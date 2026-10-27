using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The computer bowler (exhibition mode): plans each delivery the way a bowler does. On a full rack it hooks into the pocket,
    /// on a spare it throws straighter at the leave's key pin. The line comes from the real lane: the planner rolls the ball with
    /// the game's own integrator from every board and keeps the one that arrives where it wants. Skill (0..1) sets the ball's
    /// revs and how far the CPU misses its board, its speed and its release timing, so a rookie sprays it and a pro repeats.
    public static class BowlingCpu
    {
        /// The opponents on offer: name, skill (they average about 110, 150, 175 and 200 on the house pattern: BowlingGameHarness).
        public static readonly (string name, float skill)[] Opponents = { ("Rookie Ray", .2f), ("Steady Sam", .5f), ("Lucky Lou", .8f), ("Pro Pia", 1f) };

        /// The head-pin line x the ball is aimed at: the 1-3 pocket on a full rack, the leave's key pin (nudged toward the rest) on a spare.
        public static float TargetX(int standing)
        {
            if (standing == BowlingLeave.All || standing == 0) return BowlingLane.BoardX(17.5f);
            float keyZ = float.MaxValue, keyX = 0, sumX = 0; int keyN = 0, n = 0;
            for (int p = 1; p <= 10; p++)
            {
                if (!BowlingLeave.Standing(standing, p)) continue;
                var at = BowlingLane.PinSpot(p); sumX += at.x; n++;
                if (at.z < keyZ - .01f) { keyZ = at.z; keyX = at.x; keyN = 1; }
                else if (Mathf.Abs(at.z - keyZ) < .01f) { keyX += at.x; keyN++; }
            }
            if (n == 0) return BowlingLane.BoardX(17.5f);
            return Mathf.Lerp(keyX / keyN, sumX / n, .35f);
        }

        /// Where a clean release from `board` crosses the head-pin line (NaN if it never reaches the pins).
        public static float ArrivalX(float board, float speed, float rpm, float axis, OilPattern oil)
        {
            var th = BowlingRelease.Resolve(new BowlingSwing { Board = board, Speed = speed, RevRpm = rpm, AxisDeg = axis, TimingError = 0, Seed = 1 });
            th.LaunchDeg = 0; th.LoftHeight = .03f;
            var end = BowlingBall.Roll(th.Launch(), oil);
            if (end.Phase != BallPhase.Deck || end.Velocity.z < .1f) return float.NaN;
            return end.Position.x + end.Velocity.x / end.Velocity.z * (BowlingLane.FoulToHeadPin - end.Position.z);
        }

        /// The ball the CPU means to throw at this leave: revs, axis, speed and the board whose clean release arrives on target.
        public static BowlingGame.Shot Line(float skill, int standing, OilPattern oil)
        {
            skill = Mathf.Clamp01(skill);
            bool spare = standing != BowlingLeave.All;
            // a full rack: a hook into the pocket (more revs the better the bowler); a spare: nearly straight, it is about accuracy
            float rpm = spare ? 150 : Mathf.Lerp(180, 330, skill), axis = spare ? 5 : Mathf.Lerp(18, 42, skill);
            float speed = Mathf.Lerp(6.8f, 7.8f, skill);
            float target = TargetX(standing), best = 20, bestAxis = axis, err = float.MaxValue;
            // the bowler's natural hand first; when even the outside board hooks past the pocket, turn the hand less (as a bowler does)
            foreach (float k in new[] { 1f, .8f, .6f, .4f, .25f })
            {
                float a = Mathf.Max(5, axis * k);
                for (float b = 3; b <= 37; b += .25f)
                {
                    float x = ArrivalX(b, speed, rpm, a, oil);
                    if (float.IsNaN(x)) continue;
                    float e = Mathf.Abs(x - target);
                    if (e < err) { err = e; best = b; bestAxis = a; }
                }
                if (err < .3f * BowlingLane.BoardWidth) break;
            }
            return new BowlingGame.Shot(best, speed, rpm, bestAxis, 0);
        }

        /// How far a bowler misses (standard deviations): a base every bowler has, plus a share that grows as skill falls.
        /// Tuned with BowlingGameHarness so the opponents average what the menu says.
        public static class Noise
        {
            public static float BoardBase = 1f, BoardMiss = 4f, TimingBase = .03f, TimingMiss = .12f, SpeedBase = .1f, SpeedMiss = .4f;
        }

        /// The line, as thrown: the board, speed and release timing wander by how unskilled the bowler is.
        public static BowlingGame.Shot Plan(float skill, int standing, OilPattern oil, System.Random rng)
        {
            var line = Line(skill, standing, oil);
            float miss = 1 - Mathf.Clamp01(skill);
            float board = Mathf.Clamp(line.Board + Gaussian(rng) * (Noise.BoardBase + Noise.BoardMiss * miss), 3, 37);
            float timing = Gaussian(rng) * (Noise.TimingBase + Noise.TimingMiss * miss);
            float speed = Mathf.Clamp(line.Speed + Gaussian(rng) * (Noise.SpeedBase + Noise.SpeedMiss * miss), BowlingRelease.MinSpeed, BowlingRelease.MaxSpeed);
            return new BowlingGame.Shot(Mathf.Round(board * 2) / 2, speed, line.Rpm, line.Axis, timing);
        }

        static float Gaussian(System.Random rng)
        {
            double u = 1 - rng.NextDouble(), v = rng.NextDouble();
            return (float)(System.Math.Sqrt(-2 * System.Math.Log(u)) * System.Math.Cos(2 * System.Math.PI * v));
        }
    }
}
