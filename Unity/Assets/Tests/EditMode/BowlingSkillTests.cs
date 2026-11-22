using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The 11-21 skill pass (BowlingSkill): what the bowler does has to reach the ball. Each test checks the new behaviour and,
    /// where it matters, that the 10-27 feel pass really flattened it (so the test would have caught the old problem).
    public class BowlingSkillTests
    {
        bool onWas, easyWas;
        [SetUp] public void SkillOn() { onWas = BowlingSkill.On; easyWas = BowlingSkill.EasyLanes; BowlingSkill.On = true; BowlingSkill.EasyLanes = false; }
        [TearDown] public void SkillBack() { BowlingSkill.On = onWas; BowlingSkill.EasyLanes = easyWas; }

        const float Mph = 2.237f, Arm = BowlingSwingDetector.ArmLength;
        static float SwingMph(float peakRate) => BowlingSwingDetector.BallSpeed(peakRate * Arm, 1) * Mph;

        static BowlingThrow Ball(float board, float mph, float rpm, float axis, float aim = 0, float timing = 0)
            => BowlingRelease.Resolve(new BowlingSwing { Board = board, Speed = mph / Mph, RevRpm = rpm, AxisDeg = axis, AimDeg = aim, TimingError = timing, Seed = 3 });

        static BallState Roll(BowlingThrow th) => BowlingBall.Roll(th.Launch(), OilPattern.House);

        static BowlingShotRead Read(float board, float mph, float rpm, float axis, float aim = 0)
        {
            var th = Ball(board, mph, rpm, axis, aim);
            return BowlingShotRead.From(th, Roll(th));
        }

        [Test]
        public void SwingSpeedSpansTheHumanRange()
        {
            Assert.That(SwingMph(1.5f), Is.EqualTo(14f).Within(.7f), "lazy");
            Assert.That(SwingMph(4f), Is.EqualTo(18.4f).Within(.7f), "normal: still a good pace");
            Assert.That(SwingMph(9f), Is.EqualTo(22.5f).Within(.7f), "hard");
            Assert.That(SwingMph(9f) - SwingMph(1.5f), Is.GreaterThan(7.5f), "lazy to hard spans > 7.5 mph");
            float last = 0;
            for (float r = .5f; r <= 14; r += .25f) { float m = SwingMph(r); Assert.That(m, Is.GreaterThanOrEqualTo(last)); last = m; }
            Assert.That(last, Is.LessThanOrEqualTo(BowlingRelease.MaxSpeed * Mph + .01f));

            BowlingSkill.On = false;
            Assert.That(SwingMph(9f) - SwingMph(1.5f), Is.LessThan(5f), "the 10-27 curve packed it into < 5 mph");
        }

        [Test]
        public void AShortBackswingCostsPace()
        {
            float full = BowlingSwingDetector.BallSpeed(4 * Arm, 1), half = BowlingSwingDetector.BallSpeed(4 * Arm, .2f);
            Assert.That(half, Is.LessThan(full * .95f));
            Assert.That(half, Is.GreaterThanOrEqualTo(full * .9f - 1e-4f));
        }

        [Test]
        public void ASmallWristTurnIsAlreadyAHook()
        {
            Assert.AreEqual(6, BowlingSwingDetector.Spin(6, 4).axis, 1e-4f);
            Assert.AreEqual(0, BowlingSwingDetector.Spin(3, 4).axis, 1e-4f, "a still wrist is still a straight ball");
            Assert.That(BowlingSwingDetector.Spin(80, 20).rpm, Is.EqualTo(500).Within(1e-3f));
            BowlingSkill.On = false;
            Assert.AreEqual(0, BowlingSwingDetector.Spin(6, 4).axis, 1e-4f, "the 10-27 dead zone ate it");
        }

        [Test]
        public void MoreFlickKeepsHookingMore()
        {
            float SideRoll(BowlingThrow t) => t.RevRpm * 2 * Mathf.PI / 60 * Mathf.Sin(Mathf.Abs(t.AxisDeg) * Mathf.Deg2Rad);
            float a = SideRoll(Ball(10, 18.4f, 340, 45)), b = SideRoll(Ball(10, 18.4f, 450, 60)), c = SideRoll(Ball(10, 18.4f, 500, 70));
            Assert.That(b, Is.GreaterThan(a + 2)); Assert.That(c, Is.GreaterThan(b + 1));
            Assert.That(c, Is.LessThan(BowlingRelease.SideRollCeiling));
            // and that turns into entry angle: the big hook enters ~6°; under the old hard cap every flick stopped near 5°
            float bigEntry = Read(8, 18.4f, 500, 70, 1).EntryDeg;
            Assert.That(bigEntry, Is.GreaterThan(5.6f), $"{bigEntry:0.0}°");
            BowlingSkill.On = false;
            Assert.That(Read(8, 18.4f, 500, 70, 1).EntryDeg, Is.LessThan(5.3f));
        }

        [Test]
        public void SpeedMovesTheBallAtThePins()
        {
            float slow = Read(7.4f, 16, 280, 35).HeadBoard, fast = Read(7.4f, 21, 280, 35).HeadBoard;
            Assert.That(slow - fast, Is.GreaterThan(5), $"16 mph → board {slow:0.0}, 21 mph → {fast:0.0}: slower hooks more (left)");
        }

        [Test]
        public void TheLaneNoLongerErasesWhereYouStand()
        {
            float Spread() => Read(10, 19.8f, 300, 45).HeadBoard - Read(3, 19.8f, 300, 45).HeadBoard;
            Assert.That(Spread(), Is.GreaterThan(3.5f), "7 boards apart at the line, > 3.5 apart at the pins");
            BowlingSkill.EasyLanes = true;
            Assert.That(Spread(), Is.LessThan(2.5f), "easy lanes keep the old wall");
            BowlingSkill.EasyLanes = false; BowlingSkill.On = false;
            Assert.That(Spread(), Is.LessThan(2f), "the 10-27 wall pulled them together");
        }

        [Test]
        public void TheReleaseIsWorthTiming()
        {
            var perfect = Ball(10, 18, 300, 40, 0, 0); var good = Ball(10, 18, 300, 40, 0, .07f);
            var early = Ball(10, 18, 300, 40, 0, -.15f); var late = Ball(10, 18, 300, 40, 0, .15f);
            Assert.AreEqual(ReleaseGrade.Perfect, perfect.Grade); Assert.AreEqual(ReleaseGrade.Good, good.Grade);
            Assert.That(perfect.Speed, Is.GreaterThan(good.Speed * 1.02f));
            Assert.That(perfect.RevRpm, Is.GreaterThan(good.RevRpm * 1.05f));
            Assert.That(early.Speed, Is.LessThanOrEqualTo(good.Speed * .9f));
            Assert.That(late.RevRpm, Is.LessThanOrEqualTo(good.RevRpm * .8f));
        }

        [Test]
        public void TheReadoutSaysWhereItHit()
        {
            // find the board that hits the pocket with this ball, then miss it either way
            float best = 0, err = 99;
            for (float b = 3; b <= 30; b += .25f) { var r = Read(b, 18.4f, 300, 40); if (r.Valid && Mathf.Abs(r.HeadBoard - 17.5f) < err) { err = Mathf.Abs(r.HeadBoard - 17.5f); best = b; } }
            var pocket = Read(best, 18.4f, 300, 40);
            Assert.AreEqual(BowlingShotRead.Hit.Pocket, pocket.Where);
            Assert.That(pocket.EntryDeg, Is.InRange(2.5f, 7f));
            var light = Read(best - 3, 18.4f, 300, 40); var high = Read(best + 3, 18.4f, 300, 40); var cross = Read(best + 5, 18.4f, 300, 40);
            Assert.AreEqual(BowlingShotRead.Hit.Light, light.Where);
            Assert.AreEqual(BowlingShotRead.Hit.High, high.Where);
            Assert.AreEqual(BowlingShotRead.Hit.Brooklyn, cross.Where);
            StringAssert.Contains("stand left", light.Hint(false));
            StringAssert.Contains("stand right", high.Hint(false));
            StringAssert.Contains("POCKET", pocket.Line(true));
            StringAssert.Contains("MPH", pocket.Line(false));
            StringAssert.DoesNotContain("POCKET", pocket.Line(false));
            // a gutter ball has no read past its speed and revs
            var gutter = Ball(1, 18.4f, 120, 0, 3);
            var g = BowlingShotRead.From(gutter, Roll(gutter));
            Assert.IsFalse(g.Valid); Assert.IsNull(g.Hint(false));
        }
    }
}
