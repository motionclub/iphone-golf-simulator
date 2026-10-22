using System;
using UnityEngine;

namespace GolfArcade.Game
{
    /// Opt-in development diagnostics. Engine request time is not physical display/audio latency.
    /// Enable from a development capture or with -experienceTrace; never logs sensor samples.
    public static class ExperienceTrace
    {
        public static bool Enabled = Array.IndexOf(Environment.GetCommandLineArgs(), "-experienceTrace") >= 0;
        static int sequence, tennisStroke, golfStroke;
        static bool golfOpen;
        public static void GolfImpact() {
            if (golfOpen) Mark("golf", "impact-request"); else Begin("golf", "impact-request");
        }
        public static void NativeEvent(string sport, string stage, int nativeEventId, double sourceTime) {
            if (!Enabled) return;
            var stamp = NewStamp(sport, stage);
            stamp.nativeEventId = nativeEventId; stamp.sourceTime = sourceTime;
            stamp.sourceAge = stamp.bridgeTime - sourceTime;
            Write(stamp);
        }
        [Serializable] public struct Stamp
        {
            public string sport, stage;
            public int stroke, sequence, frame, nativeEventId;
            public double realtime, gameTime, sourceAge, bridgeTime, sourceTime;
        }
        public static event Action<Stamp> Recorded;
        public static void Begin(string sport, string stage, double sourceAge = -1)
        {
            if (!Enabled) return;
            if (sport == "tennis") tennisStroke++; else { golfStroke++; golfOpen = true; }
            Mark(sport, stage, sourceAge);
        }
        public static void Mark(string sport, string stage, double sourceAge = -1)
        {
            if (!Enabled) return;
            var stamp = NewStamp(sport, stage); stamp.sourceAge = sourceAge;
            Write(stamp);
            if (sport == "golf" && (stage == "contact-channels-requested" || stage == "cancel")) golfOpen = false;
        }
        static Stamp NewStamp(string sport, string stage) => new Stamp {
            sport = sport, stage = stage, stroke = sport == "tennis" ? tennisStroke : golfStroke,
            sequence = ++sequence, frame = Time.frameCount, realtime = Time.realtimeSinceStartupAsDouble,
            gameTime = Time.timeAsDouble, bridgeTime = NativeSportsSession.DiagnosticClock, sourceTime = -1, sourceAge = -1
        };
        static void Write(Stamp stamp) {
            Recorded?.Invoke(stamp);
            Debug.Log("[Experience] " + JsonUtility.ToJson(stamp));
        }
    }
}
