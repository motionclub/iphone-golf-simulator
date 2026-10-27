using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The computer bowler (exhibition): its planned line, read through the real lane integrator, arrives where it aims; skill
    /// sets how far it misses.
    public class BowlingCpuTests
    {
        static float Arrival(BowlingGame.Shot s) => BowlingCpu.ArrivalX(s.Board, s.Speed, s.Rpm, s.Axis, OilPattern.House);

        [TestCase(.2f)] [TestCase(.5f)] [TestCase(.95f)]
        public void TheLineArrivesInThePocket(float skill)
        {
            float miss = Mathf.Abs(Arrival(BowlingCpu.Line(skill, BowlingLeave.All, OilPattern.House)) - BowlingCpu.TargetX(BowlingLeave.All));
            Assert.Less(miss, .5f * BowlingLane.BoardWidth, $"the planned line misses by {miss / BowlingLane.BoardWidth:0.0} boards");
        }

        [Test]
        public void AProUsuallyFindsThePocket()
        {
            // the pocket is ~4 boards wide: most of a pro's balls arrive within 2 boards of its middle
            var rng = new System.Random(3); int inside = 0;
            for (int i = 0; i < 40; i++)
                if (Mathf.Abs(Arrival(BowlingCpu.Plan(.95f, BowlingLeave.All, OilPattern.House, rng)) - BowlingCpu.TargetX(BowlingLeave.All)) < 2 * BowlingLane.BoardWidth) inside++;
            Assert.GreaterOrEqual(inside, 28, $"{inside}/40 in the pocket");
        }

        [Test]
        public void ASpareShotGoesAtTheLeave()
        {
            int tenPin = 1 << 9;   // pin 10 standing alone (BowlingLeave masks: bit p-1)
            Assert.IsTrue(BowlingLeave.Standing(tenPin, 10) && !BowlingLeave.Standing(tenPin, 1), "the mask is the 10 pin alone");
            var shot = BowlingCpu.Plan(1, tenPin, OilPattern.House, new System.Random(5));
            float x = Arrival(shot), pin = BowlingLane.PinSpot(10).x;
            Assert.Less(Mathf.Abs(x - pin), BowlingLane.PinSpacing / 2, $"arrives {x:0.000} m, the 10 pin is at {pin:0.000} m");
        }

        [Test]
        public void RookiesMissMoreThanPros()
        {
            float Spread(float skill)
            {
                var rng = new System.Random(11); float sum = 0;
                for (int i = 0; i < 40; i++) { var s = BowlingCpu.Plan(skill, BowlingLeave.All, OilPattern.House, rng); sum += Mathf.Abs(s.Timing); }
                return sum / 40;
            }
            Assert.Greater(Spread(.1f), Spread(.95f) * 2, "a rookie's release timing wanders at least twice a pro's");
        }
    }
}
