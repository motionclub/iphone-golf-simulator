using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The fixed-tempo four-step approach (PLAN_Bowling.md §4.2). The character walks it on its
    /// own; the player's job is to match it. These times are the authority the release window
    /// keys off, and the Bowl_Approach4 clip will be authored to land on them (gate B3).
    ///
    /// Measured on real bowlers (work/bowling-anim/REFERENCES.md §1.2, primary clip WJmDPWQ2808,
    /// cross-checked on two more): t = 0 is the pushaway (ball leaves the chest); the slide foot
    /// plants at 1.67 s and the ball leaves the hand at the ankle 0.33 s later, at 2.0 s.
    public static class BowlingApproach
    {
        public const float HoldToStart = .4f;     // Ready held this long before the pushaway

        // The authored clips' own seconds (the keys the Blender build lands on). The game runs them through a smooth time warp (below):
        // a little quicker into the approach, a smoother pace from step to step, and a swing that is clearly faster from the top of the
        // backswing through the release (11-19: "make the walk-up smoother, the swing and release smoother and a bit faster").
        public const float ClipStep1 = .37f, ClipStep2 = .90f, ClipStep3 = 1.30f;
        public const float ClipPushawayExtended = .50f, ClipSwingBottom = .93f;
        public const float ClipBackswingTop = 1.53f;
        public const float ClipSlidePlant = 1.67f;
        public const float ClipIdealRelease = 2.00f;      // ball at the ankle, leaves the hand
        public const float ClipFollowThroughEnd = 2.33f;  // hand above the head
        public const float ClipSlideStop = ClipIdealRelease + .25f;

        /// Playback rate of the clip (clip seconds per game second) at clip times: slow steps eased up, the downswing 1.45x, then back to 1x.
        /// Linear between keys, so the rate (and with it every speed in the pose) changes without a jump.
        static readonly float[] WarpClip = { 0, .3f, .6f, .9f, 1.2f, 1.4f, 1.55f, 1.7f, 1.85f, 2.0f, 2.15f, 2.4f, 2.7f, 99 };
        static readonly float[] WarpRate = { 1.10f, 1.0f, 1.28f, 1.12f, 1.05f, 1.0f, 1.12f, 1.35f, 1.45f, 1.45f, 1.40f, 1.25f, 1.0f, 1.0f };
        const int TableMs = 8000;
        /// Game seconds at each millisecond of clip time (the integral of 1 / rate).
        static readonly float[] GameAtMs = BuildTable();

        static float RateAtClip(float c)
        {
            for (int i = 1; i < WarpClip.Length; i++)
                if (c < WarpClip[i]) return Mathf.Lerp(WarpRate[i - 1], WarpRate[i], Mathf.InverseLerp(WarpClip[i - 1], WarpClip[i], c));
            return 1;
        }

        static float[] BuildTable()
        {
            var g = new float[TableMs + 1];
            for (int i = 1; i <= TableMs; i++) g[i] = g[i - 1] + .001f / RateAtClip((i - .5f) * .001f);
            return g;
        }

        /// Game seconds since the pushaway at which the clip is at clip time `c`.
        public static float ToGame(float c)
        {
            float f = Mathf.Clamp(c * 1000, 0, TableMs - 1); int i = (int)f;
            return Mathf.Lerp(GameAtMs[i], GameAtMs[i + 1], f - i) + Mathf.Max(0, c - TableMs * .001f);
        }

        /// Clip time at game time `t` (the inverse of ToGame).
        public static float ClipAt(float t)
        {
            if (t <= 0) return t;
            if (t >= GameAtMs[TableMs]) return TableMs * .001f + (t - GameAtMs[TableMs]);
            int lo = 0, hi = TableMs;
            while (hi - lo > 1) { int mid = (lo + hi) >> 1; if (GameAtMs[mid] <= t) lo = mid; else hi = mid; }
            return (lo + Mathf.InverseLerp(GameAtMs[lo], GameAtMs[lo + 1], t)) * .001f;
        }

        /// How fast the clip plays at game time `t`.
        public static float Rate(float t) => RateAtClip(ClipAt(t));

        // The same moments in game seconds: what the release window and the swing cues key off.
        public static readonly float Step1 = ToGame(ClipStep1), Step2 = ToGame(ClipStep2), Step3 = ToGame(ClipStep3);
        public static readonly float PushawayExtended = ToGame(ClipPushawayExtended), SwingBottom = ToGame(ClipSwingBottom);
        public static readonly float BackswingTop = ToGame(ClipBackswingTop);
        public static readonly float SlidePlant = ToGame(ClipSlidePlant);    // step 4: the slide foot takes weight
        public static readonly float Step4 = SlidePlant;
        public static readonly float IdealRelease = ToGame(ClipIdealRelease);  // ball at the ankle, leaves the hand
        public static readonly float FollowThroughEnd = ToGame(ClipFollowThroughEnd); // hand above the head
        public static readonly float SlideStop = ToGame(ClipSlideStop);
        public static readonly float AbortBefore = Step2;   // (no longer a cancel: once the approach has started a thumb lift before the backswing is the goofy drop; the cancel is the Bowl_Abort clip while the stance is held)

        public const float StartZ = -4.35f;       // where the bowler stands (stance): 0.25 m further back than before, so the slide of the authored clip stops well short of the foul line (the approach is 4.57 m)
        public const float SlideLength = .4f;     // slide-foot travel, plant to stop (~0.4 m measured)
        public const float SlideZ = -.57f;        // slide foot stops short of the foul line (the authored shot clip's slide ends 0.57 m before it, with the stance 4.35 m back)
        public const float FoulSlideZ = .27f;     // holding too long carries the bowler over the line (the authored foul clip's slide foot ends 0.27 m past it)

        /// Bowler's body position along the approach at time t (seconds since the pushaway).
        public static float BodyZ(float gameT, bool foul)
        {
            float t = ClipAt(gameT);
            if (t <= 0) return StartZ;
            float plantZ = SlideZ - SlideLength;
            if (t < ClipSlidePlant)
            {
                // Steps get longer and faster toward the slide: ease-in over the approach.
                float u = t / ClipSlidePlant;
                return Mathf.Lerp(StartZ, plantZ, u * u * (1.6f - .6f * u));
            }
            // The slide: still gliding at the release, stopping a quarter second later
            // (or, held too long, carried over the foul line).
            float stop = foul ? ClipSlideStop + .2f : ClipSlideStop, end = foul ? FoulSlideZ : SlideZ;
            float s = Mathf.Clamp01((t - ClipSlidePlant) / (stop - ClipSlidePlant));
            return Mathf.Lerp(plantZ, end, 1 - (1 - s) * (1 - s));
        }

        /// The bowling arm's pendulum angle in degrees (0 = straight down, + forward, - back) for the
        /// ideal swing at time t. The phone swing pulls the on-screen arm toward the player's own.
        public static float ArmAngle(float gameT)
        {
            float t = ClipAt(gameT);
            if (t <= 0) return 70;                                                         // stance: ball at the chest
            if (t < ClipPushawayExtended) return Mathf.Lerp(70, 35, Smooth(t / ClipPushawayExtended));
            if (t < ClipSwingBottom) return Mathf.Lerp(35, 0, Smooth((t - ClipPushawayExtended) / (ClipSwingBottom - ClipPushawayExtended)));
            if (t < ClipBackswingTop) return Mathf.Lerp(0, -95, Smooth((t - ClipSwingBottom) / (ClipBackswingTop - ClipSwingBottom)));
            if (t < ClipIdealRelease) return Mathf.Lerp(-95, 0, Smooth((t - ClipBackswingTop) / (ClipIdealRelease - ClipBackswingTop)));
            return Mathf.Lerp(0, 150, Smooth((t - ClipIdealRelease) / (ClipFollowThroughEnd - ClipIdealRelease)));
        }

        static float Smooth(float x) { x = Mathf.Clamp01(x); return x * x * (3 - 2 * x); }

    }
}
