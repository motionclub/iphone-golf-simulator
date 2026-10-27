using UnityEngine;

namespace GolfArcade.Bowling
{
    public enum ReleaseGrade { Perfect, Good, Early, Late, Drop, Foul }

    /// One delivery as the game resolved it: the unit that multiplayer sends to the host.
    public struct BowlingThrow
    {
        public float Board;        // board under the ball's centre at release (position only: no angle turn)
        public float Speed;        // m/s at release
        public float RevRpm;
        public float AxisDeg;      // axis rotation: + hooks left (right-hander's hook), - backs up right
        public float LaunchDeg;    // direction error from the release: + = toward the bowler's right
        public float LoftHeight;   // how far above the lane the ball leaves the hand
        public ReleaseGrade Grade;

        public bool Foul => Grade == ReleaseGrade.Foul;
        public bool Dropped => Grade == ReleaseGrade.Drop;

        /// The ball just after it leaves the hand.
        public BallState Launch()
        {
            float a = LaunchDeg * Mathf.Deg2Rad, axis = AxisDeg * Mathf.Deg2Rad;
            float w = RevRpm * 2 * Mathf.PI / 60;
            return new BallState
            {
                Position = new Vector3(BowlingLane.BoardX(Board), BowlingLane.BallRadius + Mathf.Max(0, LoftHeight), .10f),
                Velocity = new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a)) * Speed,
                // Pure forward roll is spin about +x. Turning the axis toward +z adds side roll,
                // and friction then pulls the ball left: the hook.
                Spin = new Vector3(Mathf.Cos(axis), 0, Mathf.Sin(axis)) * w,
                Phase = LoftHeight > .005f ? BallPhase.Air : BallPhase.Skid,
            };
        }
    }

    /// What the bowler did, before the release grade is applied (PLAN_Bowling.md §4.3–4.5).
    public struct BowlingSwing
    {
        public float Board;
        public float Speed;          // m/s the swing would give with a clean release
        public float RevRpm;
        public float AxisDeg;
        public float TimingError;    // seconds, thumb lift minus the ideal release (already latency-corrected)
        public float SwingDrift;     // degrees the forward swing wandered sideways
        public int Seed;
    }

    /// The release window: power comes from the swing, control from the release timing.
    public static class BowlingRelease
    {
        public const float PerfectWindow = .045f, GoodWindow = .100f, MissWindow = .250f;
        public const float MaxSpeed = 9.5f, MinSpeed = 3f;
        /// Most side roll (rad/s) a release can put on the ball: about 300 rpm at 45° of axis
        /// rotation, a strong rec hook (~15 boards, ~5.5° entry). More than that could not be
        /// aimed from the approach with position only, so a bigger flick turns the axis less.
        public const float MaxSideRoll = 22.5f;

        public static ReleaseGrade Grade(float timingError)
        {
            float e = Mathf.Abs(timingError);
            if (e <= PerfectWindow) return ReleaseGrade.Perfect;
            if (e <= GoodWindow) return ReleaseGrade.Good;
            if (timingError < 0) return timingError < -MissWindow ? ReleaseGrade.Drop : ReleaseGrade.Early;
            return timingError > MissWindow ? ReleaseGrade.Foul : ReleaseGrade.Late;
        }

        struct Effect
        {
            public float speed, revs, scatter, pull, loft;
            public Effect(float speed, float revs, float scatter, float pull, float loft) { this.speed = speed; this.revs = revs; this.scatter = scatter; this.pull = pull; this.loft = loft; }
        }

        static Effect For(ReleaseGrade g)
        {
            switch (g)
            {
                case ReleaseGrade.Perfect: return new Effect(1.02f, 1.00f, 0.0f, 0, .03f);
                case ReleaseGrade.Good:    return new Effect(0.95f, 0.95f, 0.4f, 0, .05f);
                case ReleaseGrade.Early:   return new Effect(0.80f, 0.90f, 1.2f, 0, .12f);   // dumped from behind the slide: lands short, bounces
                case ReleaseGrade.Late:    return new Effect(0.90f, 0.75f, 1.0f, -.6f, .30f); // lofted, pulled inward, skids longer
                case ReleaseGrade.Foul:    return new Effect(0.85f, 0.60f, 2.0f, -.8f, .45f); // over the line; the big loft still knocks pins (score 0)
                default:                   return new Effect(0.30f, 0.30f, 0.0f, 0, 0);
            }
        }

        public static BowlingThrow Resolve(in BowlingSwing s)
        {
            var grade = Grade(s.TimingError);
            var e = For(grade);
            var rng = new System.Random(s.Seed);
            float scatter = e.scatter + Mathf.Max(0, s.SwingDrift - 15) * .05f;
            float revs = Mathf.Max(0, s.RevRpm) * e.revs, axis = Mathf.Clamp(s.AxisDeg, -75, 75);
            float w = revs * 2 * Mathf.PI / 60, side = w * Mathf.Sin(Mathf.Abs(axis) * Mathf.Deg2Rad);
            if (side > MaxSideRoll) axis = Mathf.Sign(axis) * Mathf.Asin(MaxSideRoll / w) * Mathf.Rad2Deg;
            return new BowlingThrow
            {
                Board = Mathf.Clamp(s.Board, 1, BowlingLane.Boards),
                Speed = Mathf.Clamp(s.Speed * e.speed, MinSpeed, MaxSpeed),
                RevRpm = revs,
                AxisDeg = axis,
                LaunchDeg = e.pull + scatter * Gaussian(rng),
                LoftHeight = e.loft,
                Grade = grade,
            };
        }

        static float Gaussian(System.Random rng)
        {
            double u = 1 - rng.NextDouble(), v = rng.NextDouble();
            return (float)(System.Math.Sqrt(-2 * System.Math.Log(u)) * System.Math.Cos(2 * System.Math.PI * v));
        }
    }
}
