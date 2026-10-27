using GolfArcade.Bowling;
using NUnit.Framework;

namespace GolfArcade.Tests
{
    /// Gate S1 (PLAN_Bowling.md §12): the tenpin score sheet and leave names.
    public class BowlingScoreTests
    {
        static BowlingScore Play(params int[] rolls)
        {
            var s = new BowlingScore();
            foreach (int r in rolls) s.Roll(r);
            return s;
        }

        static int[] Repeat(int value, int count) { var a = new int[count]; for (int i = 0; i < count; i++) a[i] = value; return a; }

        [Test] public void PerfectGameIs300() { var s = Play(Repeat(10, 12)); Assert.IsTrue(s.Complete); Assert.AreEqual(300, s.Total); Assert.AreEqual(12, s.StrikeStreak); }
        [Test] public void GutterGameIs0() { var s = Play(Repeat(0, 20)); Assert.IsTrue(s.Complete); Assert.AreEqual(0, s.Total); Assert.AreEqual("-", s.Mark(0, 0)); }
        [Test] public void AllNinesAndSparesThenNineIs190() { var s = Play(9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9); Assert.IsTrue(s.Complete); Assert.AreEqual(190, s.Total); }
        [Test] public void AllFivesIs150() { var s = Play(Repeat(5, 21)); Assert.IsTrue(s.Complete); Assert.AreEqual(150, s.Total); Assert.AreEqual("/", s.Mark(3, 1)); }
        [Test] public void DutchTwoHundred() { var s = Play(10, 5, 5, 10, 5, 5, 10, 5, 5, 10, 5, 5, 10, 5, 5, 10); Assert.IsTrue(s.Complete); Assert.AreEqual(200, s.Total); }
        [Test] public void AllNinesOpenIs90() { var s = Play(9, 0, 9, 0, 9, 0, 9, 0, 9, 0, 9, 0, 9, 0, 9, 0, 9, 0, 9, 0); Assert.IsTrue(s.Complete); Assert.AreEqual(90, s.Total); }

        [Test]
        public void StrikeWaitsForTwoBalls()
        {
            var s = Play(10);
            Assert.IsNull(s.FramePoints(0));
            s.Roll(3);
            Assert.IsNull(s.FramePoints(0));
            s.Roll(4);
            Assert.AreEqual(17, s.FramePoints(0));
            Assert.AreEqual(24, s.Cumulative(1));
        }

        [Test]
        public void SpareWaitsForOneBall()
        {
            var s = Play(7, 3);
            Assert.IsNull(s.FramePoints(0));
            Assert.AreEqual("/", s.Mark(0, 1));
            s.Roll(6);
            Assert.AreEqual(16, s.FramePoints(0));
        }

        [Test]
        public void TenthFrameStrikeStrikeStrike()
        {
            var s = Play(Repeat(0, 18));
            s.Roll(10); Assert.AreEqual(10, s.PinsStanding);
            s.Roll(10); Assert.AreEqual(10, s.PinsStanding);
            s.Roll(10);
            Assert.IsTrue(s.Complete); Assert.AreEqual(30, s.Total);
            Assert.AreEqual("X", s.Mark(9, 0)); Assert.AreEqual("X", s.Mark(9, 1)); Assert.AreEqual("X", s.Mark(9, 2));
        }

        [Test]
        public void TenthFrameStrikeThenSpare()
        {
            var s = Play(Repeat(0, 18));
            s.Roll(10); s.Roll(6); Assert.AreEqual(4, s.PinsStanding); s.Roll(4);
            Assert.IsTrue(s.Complete); Assert.AreEqual(20, s.Total);
            Assert.AreEqual("X", s.Mark(9, 0)); Assert.AreEqual("6", s.Mark(9, 1)); Assert.AreEqual("/", s.Mark(9, 2));
        }

        [Test]
        public void TenthFrameSpareThenStrike()
        {
            var s = Play(Repeat(0, 18));
            s.Roll(9); s.Roll(1); Assert.IsFalse(s.Complete); Assert.AreEqual(10, s.PinsStanding); s.Roll(10);
            Assert.IsTrue(s.Complete); Assert.AreEqual(20, s.Total); Assert.AreEqual("X", s.Mark(9, 2));
        }

        [Test]
        public void TenthFrameOpenEndsAfterTwo()
        {
            var s = Play(Repeat(0, 18));
            s.Roll(7); s.Roll(2);
            Assert.IsTrue(s.Complete); Assert.AreEqual(9, s.Total);
        }

        [Test]
        public void FoulOnFirstBallScoresZeroAndResetsTheRack()
        {
            var s = new BowlingScore();
            s.Roll(9, foul: true);
            Assert.AreEqual("F", s.Mark(0, 0));
            Assert.AreEqual(10, s.PinsStanding);
            s.Roll(10);
            Assert.AreEqual("/", s.Mark(0, 1));
            s.Roll(5);
            Assert.AreEqual(15, s.FramePoints(0));
        }

        [Test]
        public void FoulOnSecondBallKeepsFirstCount()
        {
            var s = new BowlingScore();
            s.Roll(7); s.Roll(3, foul: true);
            Assert.AreEqual("F", s.Mark(0, 1));
            Assert.AreEqual(7, s.FramePoints(0));
            Assert.AreEqual(1, s.Frame);
        }

        [Test]
        public void FoulInTenthBonusBall()
        {
            var s = Play(Repeat(0, 18));
            s.Roll(10); s.Roll(10); s.Roll(10, foul: true);
            Assert.IsTrue(s.Complete); Assert.AreEqual(20, s.Total);
        }

        [Test]
        public void TooManyPinsIsRejected()
        {
            var s = Play(6);
            Assert.Throws<System.ArgumentOutOfRangeException>(() => s.Roll(5));
        }

        [Test] public void Turkey() { var s = Play(10, 10, 10); Assert.AreEqual(3, s.StrikeStreak); Assert.AreEqual("Turkey", BowlingLeave.Streak(3)); }

        [TestCase(new[] { 7, 10 }, true, "Bedposts")]
        [TestCase(new[] { 4, 6, 7, 10 }, true, "Big Four")]
        [TestCase(new[] { 4, 6, 7, 9, 10 }, true, "Greek Church")]
        [TestCase(new[] { 2, 7 }, true, "Baby Split")]
        [TestCase(new[] { 3, 10 }, true, "Baby Split")]
        [TestCase(new[] { 5, 6 }, true, "Split")]
        [TestCase(new[] { 4, 5 }, true, "Split")]
        [TestCase(new[] { 7, 9 }, true, "Split")]
        [TestCase(new[] { 2, 4, 5, 8 }, false, "Bucket")]
        [TestCase(new[] { 1, 2, 10 }, false, "Washout")]
        [TestCase(new[] { 2, 8 }, false, null)]
        [TestCase(new[] { 6, 10 }, false, null)]
        [TestCase(new[] { 10 }, false, "10 Pin")]
        public void Leaves(int[] pins, bool split, string name)
        {
            int mask = BowlingLeave.Mask(pins);
            Assert.AreEqual(split, BowlingLeave.IsSplit(mask), BowlingLeave.Numbers(mask));
            Assert.AreEqual(name, BowlingLeave.Name(mask), BowlingLeave.Numbers(mask));
        }

        [Test]
        public void PinSpotsAreRegulation()
        {
            Assert.AreEqual(BowlingLane.FoulToHeadPin, BowlingLane.PinSpot(1).z, 1e-4f);
            Assert.AreEqual(-BowlingLane.PinSpacing * 1.5f, BowlingLane.PinSpot(7).x, 1e-4f);
            Assert.AreEqual(BowlingLane.PinSpacing * 1.5f, BowlingLane.PinSpot(10).x, 1e-4f);
            Assert.AreEqual(BowlingLane.PinSpacing, (BowlingLane.PinSpot(2) - BowlingLane.PinSpot(3)).magnitude, 1e-4f);
            Assert.AreEqual(BowlingLane.PinSpacing, (BowlingLane.PinSpot(1) - BowlingLane.PinSpot(3)).magnitude, 1e-4f);
            Assert.AreEqual(0, BowlingLane.BoardX(20), 1e-4f);
        }
    }
}
