#include <deque>
#include <string>
#include <mutex>
#include <cstring>
#include <cstdio>
#include <mach/mach_time.h>

// Bounded queues owned by the framework: no callbacks into released Swift objects.
static std::mutex gate;
static std::deque<std::string> inputs, events;
static std::string tennisResult;
static std::deque<std::string> networkInputs, networkOutputs;
static bool networkFault = false;
// The network queues never refuse a match's traffic (a refusal used to end the match: the guest ejected itself). Past a soft limit an
// unreliable packet (a pose or a clock update, stale a frame later) makes room by evicting the oldest unreliable one, or is dropped
// itself; reliable packets grow the queue up to a hard limit. Only past that is a packet lost, and that is reported (logged, never an
// eject): the versus ready handshake's score check re-syncs a lost call.
static const size_t networkSoftLimit = 128, networkHardLimit = 1024;
static int networkDropped = 0;
static bool unreliablePacket(const std::string& json) { return json.find("\"reliable\":false") != std::string::npos; }
static int networkPush(std::deque<std::string>& queue,const char* json) {
    if(!json || strlen(json)>60000) return 0;
    std::lock_guard<std::mutex> lock(gate);
    std::string value(json);
    if(queue.size()>=networkSoftLimit) {
        auto old=queue.begin();
        while(old!=queue.end() && !unreliablePacket(*old)) ++old;
        if(old!=queue.end()) queue.erase(old);
        else if(unreliablePacket(value)) { networkDropped++; return 1; }
        else if(queue.size()>=networkHardLimit) { networkDropped++; networkFault=true; queue.pop_front(); }
    }
    queue.emplace_back(std::move(value));return 1;
}
// Mirrors SportsSample in the host's SportsRuntime.h and NativeSportsSession.Sample in C#.
struct SportsSample {
    int32_t version, session; double time;
    float target, power, aim;
    int32_t swing, swingStart, swingAbort, flags;
    float handSide, lift, strokeFacing;
    float qx, qy, qz, qw, rx, ry, rz, gx, gy, gz;
    double onsetTime, confirmationTime, abortTime;
};
static_assert(sizeof(SportsSample) == 120, "Motion sample layout must match the host and managed bridge");
// Fixed ring: pushing and polling never allocate on either side of the bridge.
static SportsSample samples[64];
static int sampleHead = 0, sampleCount = 0;
static int pop(std::deque<std::string>& queue, char* output, int capacity) {
    std::lock_guard<std::mutex> lock(gate);
    if (!output || capacity < 2) return 0;
    output[0]='\0';
    if (queue.empty()) return 0;
    auto value = queue.front(); queue.pop_front();
    if (value.size() >= (size_t)capacity) return 0;
    memcpy(output, value.c_str(), value.size()+1); return (int)value.size();
}
extern "C" {
__attribute__((visibility("default"))) int SportsNetworkPush(const char* json) { return networkPush(networkInputs,json); }
__attribute__((visibility("default"))) int SportsNetworkPoll(char* output,int capacity) { return pop(networkInputs,output,capacity); }
__attribute__((visibility("default"))) int SportsNetworkEmit(const char* json) { return networkPush(networkOutputs,json); }
__attribute__((visibility("default"))) int SportsNetworkPollOutput(char* output,int capacity) {
    {
        std::lock_guard<std::mutex> lock(gate);
        if(networkFault) {
            // a report only: the phone logs it and plays on
            char fault[320];
            int n=snprintf(fault,sizeof(fault),"{\"version\":1,\"lobbyID\":\"\",\"matchID\":\"\",\"sender\":\"\",\"sequence\":0,\"kind\":\"bridgeError\",\"reliable\":true,\"sentAt\":0,\"payload\":\"Multiplayer message queue overflow: %d packets dropped.\"}",networkDropped);
            if(output && n>0 && capacity>n) { networkFault=false;memcpy(output,fault,n+1);return n; }
        }
    }
    return pop(networkOutputs,output,capacity);
}

__attribute__((visibility("default"))) void SportsSetTennisResult(const char* value) {
    std::lock_guard<std::mutex> lock(gate);
    tennisResult = value ? value : "";
}
__attribute__((visibility("default"))) int SportsReadTennisResult(char* output, int capacity) {
    std::lock_guard<std::mutex> lock(gate);
    if (!output || tennisResult.empty() || tennisResult.size() >= (size_t)capacity) return 0;
    memcpy(output, tennisResult.c_str(), tennisResult.size()+1);
    return (int)tennisResult.size();
}

__attribute__((visibility("default"))) double SportsClock() {
    static mach_timebase_info_data_t info = [] { mach_timebase_info_data_t i; mach_timebase_info(&i); return i; }();
    return mach_absolute_time() * (double)info.numer / info.denom / 1e9;
}
__attribute__((visibility("default"))) void SportsPushInput(const char* json) {
    if (!json || strlen(json)>4096) return;
    std::lock_guard<std::mutex> lock(gate);
    if(inputs.size()>=64) inputs.pop_front(); inputs.emplace_back(json);
}
__attribute__((visibility("default"))) void SportsPushSample(const SportsSample* sample) {
    if (!sample) return;
    std::lock_guard<std::mutex> lock(gate);
    if (sampleCount == 64) { sampleHead = (sampleHead + 1) % 64; sampleCount--; }
    samples[(sampleHead + sampleCount) % 64] = *sample; sampleCount++;
}
__attribute__((visibility("default"))) int SportsPollSample(SportsSample* output) {
    std::lock_guard<std::mutex> lock(gate);
    if (!output || sampleCount == 0) return 0;
    *output = samples[sampleHead]; sampleHead = (sampleHead + 1) % 64; sampleCount--;
    return 1;
}
__attribute__((visibility("default"))) int SportsPollInput(char* output, int capacity) { return pop(inputs,output,capacity); }
__attribute__((visibility("default"))) void SportsEmit(const char* json) {
    if(!json || strlen(json)>4096) return;
    std::lock_guard<std::mutex> lock(gate);
    if(events.size()>=64) events.pop_front(); events.emplace_back(json);
}
__attribute__((visibility("default"))) int SportsPollEvent(char* output,int capacity) { return pop(events,output,capacity); }
/// Between matches: the last match's network traffic only (a sport session's inputs and motion samples stay).
__attribute__((visibility("default"))) void SportsNetworkClear() {
    std::lock_guard<std::mutex> lock(gate); networkInputs.clear(); networkOutputs.clear(); networkFault=false; networkDropped=0;
}
__attribute__((visibility("default"))) void SportsClear() {
    std::lock_guard<std::mutex> lock(gate); inputs.clear(); events.clear(); networkInputs.clear(); networkOutputs.clear(); networkFault=false; networkDropped=0; sampleHead = sampleCount = 0;
}
}
