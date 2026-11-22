// DAILY SHARE (2026-11-21): the Daily Hole in One's shot frames, from Unity (ShotClips.cs) to the app (DailyShareClips.swift).
// Unity copies the course camera's picture into a 1280x720 BGRA frame 30 times a second while a shot is on and calls
// SportsShotClips_Frame on its main thread; the app registers one sink (through dlsym, like the other plugin calls) that copies
// the pixels before it returns and encodes them off this thread. Without a sink (no app, or the app is older) every call is a no-op.
#include <atomic>

typedef void (*SportsShotClipsSink)(int kind, int shot, double time, double feet, int points, int holed,
                                    const void *bgra, int width, int height, int stride);
static std::atomic<SportsShotClipsSink> sink{nullptr};

extern "C" {
__attribute__((visibility("default"))) void SportsShotClips_SetSink(SportsShotClipsSink s) { sink.store(s); }
// Whether the app wants the shots filmed (it registers a sink only when it shares a clip): without one, Unity films nothing.
__attribute__((visibility("default"))) bool SportsShotClips_Wanted() { return sink.load() != nullptr; }
// kind: 1 armed at address, 2 contact, 3 at rest (feet: 0 holed, -1 hazard; points), 4 closed (the shot's frames are done), 5 cancelled.
__attribute__((visibility("default"))) void SportsShotClips_Event(int kind, int shot, double time, double feet, int points, int holed) {
    if (SportsShotClipsSink s = sink.load()) s(kind, shot, time, feet, points, holed, nullptr, 0, 0, 0);
}
// One frame: BGRA, bottom row first (AsyncGPUReadback's layout), `time` on Unity's realtime clock.
__attribute__((visibility("default"))) void SportsShotClips_Frame(const void *bgra, int width, int height, int stride, double time) {
    if (!bgra || width <= 0 || height <= 0) return;
    if (SportsShotClipsSink s = sink.load()) s(0, -1, time, 0, 0, 0, bgra, width, height, stride);
}
}
