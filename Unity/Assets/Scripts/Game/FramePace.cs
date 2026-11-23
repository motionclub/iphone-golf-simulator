using UnityEngine;
using UnityEngine.Rendering;
using GolfArcade.Tennis;

namespace GolfArcade.Game
{
    /// One judging window: drawn frames, how many reached the screen late, and how many were heavy (their own work overran the slot).
    public struct FrameWindowResult
    {
        public int Frames, Late, Heavy, DrawRate;
        public bool TimingKnown;
        public float Seconds;
    }

    /// Counts drawn frames over `Seconds`. Late: the gap since the last drawn frame overran its slot by a quarter. Heavy: the frame's own work
    /// (the main thread less its wait for the present, or the GPU) took longer than the slot (FrameTimingManager; Player Settings → Frame
    /// Timing Stats). On a TV a frame can be late without being heavy: AirPlay took the picture late. A lower picture cannot cure that, so on a
    /// TV only heavy frames count against the picture (PacePolicy).
    public sealed class FrameWindow
    {
        public const float Seconds = 2f, LateFactor = 1.25f;
        /// Seconds of drawn frames still to pass before counting (loading, and after a change, when frame times are not representative).
        public float Settle;
        float sinceDrawn, elapsed; int frames, late, heavy; ulong lastStamp; bool timingSeen;
        readonly FrameTiming[] timing = new FrameTiming[1];

        public FrameWindow(float settle) { Settle = settle; }

        public void Reset() { sinceDrawn = elapsed = 0; frames = late = heavy = 0; }

        /// A pause (timeScale 0) or a loop-rate change: the window starts again, after `settle` seconds of grace.
        public void Restart(float settle) { Reset(); Settle = Mathf.Max(Settle, settle); }

        /// Every Update. True, with `result`, when a window is complete.
        public bool Tick(float unscaledDelta, int drawRate, out FrameWindowResult result)
        {
            result = default;
            sinceDrawn += unscaledDelta;
            if (!OnDemandRendering.willCurrentFrameRender) return false;
            float dt = sinceDrawn; sinceDrawn = 0;
            float slot = 1f / Mathf.Max(1, drawRate);
            bool isHeavy = Heavy(slot * 1000.0);
            if (Settle > 0) { Settle -= dt; return false; }
            frames++; if (dt > slot * LateFactor) late++;
            if (isHeavy) heavy++;
            elapsed += dt;
            if (elapsed < Seconds) return false;
            result = new FrameWindowResult { Frames = frames, Late = late, Heavy = heavy, DrawRate = drawRate, TimingKnown = timingSeen, Seconds = elapsed };
            Reset();
            return true;
        }

        /// The newest finished frame's own work against `slotMs` (frame timings arrive a few frames late; each frame is judged once).
        bool Heavy(double slotMs)
        {
            if (!FrameTimingManager.IsFeatureEnabled()) return false;
            FrameTimingManager.CaptureFrameTimings();
            if (FrameTimingManager.GetLatestTimings(1, timing) == 0) return false;
            var t = timing[0];
            if (t.frameStartTimestamp == lastStamp || t.cpuMainThreadFrameTime <= 0) return false;
            lastStamp = t.frameStartTimestamp; timingSeen = true;
            double work = System.Math.Max(t.cpuMainThreadFrameTime - t.cpuMainThreadPresentWaitTime, t.gpuFrameTime);
            return work > slotMs;
        }
    }

    /// When to act on late frames (2026-11-22, "a smooth gaming experience consistent for everyone"). A window is bad when 2 % of its frames
    /// are late (was 10 %, which let about six judders a second through for good); two bad windows in a row act, so one hitch (a load, a
    /// first-time effect) never lowers the picture. On a TV with frame timings, late frames count only when the phone's own work was heavy
    /// too; without timings a TV keeps the old 10 % rule (a late TV frame may be AirPlay's, not ours). Above 60 (a ProMotion phone at 120)
    /// the first action is the drop to 60, then the picture steps.
    public sealed class PacePolicy
    {
        public const int BadPercent = 2, BlindTvPercent = 10, WindowsToAct = 2;
        public enum Decision { Hold, DropRate, StepDown }
        int badWindows;
        /// Windows whose late frames were not the phone's doing (TV: the picture reached AirPlay late).
        public int Stalls { get; private set; }

        public static bool Bad(in FrameWindowResult w, bool tv)
        {
            if (w.Frames <= 0) return false;
            bool late = w.Late * 100 >= w.Frames * BadPercent;
            if (!tv) return late;
            if (!w.TimingKnown) return w.Late * 100 >= w.Frames * BlindTvPercent;
            return late && w.Heavy * 100 >= w.Frames * BadPercent;
        }

        public Decision Observe(in FrameWindowResult w, bool tv)
        {
            bool bad = Bad(w, tv);
            if (!bad && tv && w.TimingKnown && w.Late * 100 >= w.Frames * BadPercent) Stalls++;
            badWindows = bad ? badWindows + 1 : 0;
            if (badWindows < WindowsToAct) return Decision.Hold;
            badWindows = 0;
            return w.DrawRate > 60 ? Decision.DropRate : Decision.StepDown;
        }

        public void Reset() => badWindows = 0;
    }

    /// The one frame governor at work (tennis, golf's Luminous Coast, bowling): whichever registers first acts, so two never step twice.
    public static class FramePace
    {
        static Object owner;
        static float lastStallLog = -100;

        /// Every Update of a governor. `calm` counts seconds without a bad window (a minute marks the level as one this phone holds).
        public static void Govern(Object self, FrameWindow window, PacePolicy policy, ref float calm, ref int generation, string who)
        {
            if (owner && owner != self) return;
            owner = self;
            // (only a match is judged: golf's scene also sits behind the menu at boot, and a loading stall is not the phone's level)
            if (Time.timeScale == 0 || (NativeSportsSession.Embedded && !NativeSportsSession.InMatch)) { window.Restart(1); policy.Reset(); return; }
            if (generation != InputRate.Generation) { generation = InputRate.Generation; window.Restart(1); policy.Reset(); }
            int drawRate = Mathf.Max(1, Application.targetFrameRate / Mathf.Max(1, OnDemandRendering.renderFrameInterval));
            if (!window.Tick(Time.unscaledDeltaTime, drawRate, out var w)) return;
            bool tv = NativeSportsSession.OnTV;
            int stalls = policy.Stalls;
            switch (policy.Observe(w, tv))
            {
                case PacePolicy.Decision.DropRate:
                    // the phone's own screen at 120 that cannot hold it: 60 for the rest of the match, and the next few launches of the sport
                    InputRate.Stop(); OnDemandRendering.renderFrameInterval = 1; Application.targetFrameRate = 60; PhoneRate.Dropped();
                    window.Restart(4); calm = 0;
                    Debug.Log($"[FramePace] {who}: {w.Late}/{w.Frames} late, {w.Heavy} heavy at {w.DrawRate} fps: 60 fps from now on");
                    return;
                case PacePolicy.Decision.StepDown:
                    if (TennisQuality.StepDown())
                    {
                        window.Restart(4); calm = 0;
                        Debug.Log($"[FramePace] {who}: {w.Late}/{w.Frames} late, {w.Heavy} heavy: rendering stepped down (reduction {TennisQuality.Reductions})");
                    }
                    return;
            }
            if (policy.Stalls > stalls && Time.realtimeSinceStartup - lastStallLog > 10)
            {
                lastStallLog = Time.realtimeSinceStartup;
                Debug.Log($"[FramePace] TV picture late, not the phone's work: {w.Late}/{w.Frames} late, {w.Heavy} heavy (stalls so far {policy.Stalls})");
            }
            if (!PacePolicy.Bad(w, tv) && (calm += w.Seconds) >= 60) TennisQuality.MarkHeld();
        }
    }

    /// The phone's own screen at 120 (Settings → Phone frame rate: Auto on a ProMotion phone with an A17 Pro or newer, or 120): a sport this
    /// phone could not hold at 120 starts at 60 for its next `Penalty` launches, then tries 120 again (a phone that was only hot that day).
    public static class PhoneRate
    {
        const string Key = "rate.v1.";
        public const int Penalty = 5;
        static string sport;

        /// The loop rate for a match on the phone's own screen.
        public static int Choose(string forSport, int requested, double panelHz)
        {
            sport = forSport;
            int fps = FrameRate.Target(requested, panelHz);
            if (fps <= 60 || Application.isEditor || string.IsNullOrEmpty(sport)) return fps;
            int left = PlayerPrefs.GetInt(Key + sport, 0);
            if (left <= 0) return fps;
            PlayerPrefs.SetInt(Key + sport, left - 1);
            Debug.Log($"[FramePace] {sport}: 60 fps this launch ({left - 1} more), as 120 did not hold last time");
            return 60;
        }

        public static void Dropped()
        {
            if (!Application.isEditor && !string.IsNullOrEmpty(sport)) PlayerPrefs.SetInt(Key + sport, Penalty);
        }
    }
}
