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
        public const float Step1 = .37f, Step2 = .90f, Step3 = 1.30f;
        public const float PushawayExtended = .50f, SwingBottom = .93f;
        public const float BackswingTop = 1.53f;
        public const float SlidePlant = 1.67f;    // step 4: the slide foot takes weight
        public const float Step4 = SlidePlant;
        public const float IdealRelease = 2.00f;  // ball at the ankle, leaves the hand (0.2–0.35 s after the plant)
        public const float FollowThroughEnd = 2.33f; // hand above the head
        public const float SlideStop = IdealRelease + .25f;
        public const float AbortBefore = Step2;   // (no longer a cancel: once the approach has started a thumb lift before the backswing is the goofy drop; the cancel is the Bowl_Abort clip while the stance is held)

        public const float StartZ = -4.35f;       // where the bowler stands (stance): 0.25 m further back than before, so the slide of the authored clip stops well short of the foul line (the approach is 4.57 m)
        public const float SlideLength = .4f;     // slide-foot travel, plant to stop (~0.4 m measured)
        public const float SlideZ = -.57f;        // slide foot stops short of the foul line (the authored shot clip's slide ends 0.57 m before it, with the stance 4.35 m back)
        public const float FoulSlideZ = .27f;     // holding too long carries the bowler over the line (the authored foul clip's slide foot ends 0.27 m past it)

        /// Bowler's body position along the approach at time t (seconds since the pushaway).
        public static float BodyZ(float t, bool foul)
        {
            if (t <= 0) return StartZ;
            float plantZ = SlideZ - SlideLength;
            if (t < SlidePlant)
            {
                // Steps get longer and faster toward the slide: ease-in over the approach.
                float u = t / SlidePlant;
                return Mathf.Lerp(StartZ, plantZ, u * u * (1.6f - .6f * u));
            }
            // The slide: still gliding at the release, stopping a quarter second later
            // (or, held too long, carried over the foul line).
            float stop = foul ? SlideStop + .2f : SlideStop, end = foul ? FoulSlideZ : SlideZ;
            float s = Mathf.Clamp01((t - SlidePlant) / (stop - SlidePlant));
            return Mathf.Lerp(plantZ, end, 1 - (1 - s) * (1 - s));
        }

        /// The bowling arm's pendulum angle in degrees (0 = straight down, + forward, - back) for the
        /// ideal swing at time t. The phone swing pulls the on-screen arm toward the player's own.
        public static float ArmAngle(float t)
        {
            if (t <= 0) return 70;                                                         // stance: ball at the chest
            if (t < PushawayExtended) return Mathf.Lerp(70, 35, Smooth(t / PushawayExtended));
            if (t < SwingBottom) return Mathf.Lerp(35, 0, Smooth((t - PushawayExtended) / (SwingBottom - PushawayExtended)));
            if (t < BackswingTop) return Mathf.Lerp(0, -95, Smooth((t - SwingBottom) / (BackswingTop - SwingBottom)));
            if (t < IdealRelease) return Mathf.Lerp(-95, 0, Smooth((t - BackswingTop) / (IdealRelease - BackswingTop)));
            return Mathf.Lerp(0, 150, Smooth((t - IdealRelease) / (FollowThroughEnd - IdealRelease)));
        }

        static float Smooth(float x) { x = Mathf.Clamp01(x); return x * x * (3 - 2 * x); }

        /// 0 = pushaway, 1..3 = steps 1–3 planted, 4 = sliding.
        public static int StepIndex(float t) => t < Step1 ? 0 : t < Step2 ? 1 : t < Step3 ? 2 : t < SlidePlant ? 3 : 4;
    }
}
