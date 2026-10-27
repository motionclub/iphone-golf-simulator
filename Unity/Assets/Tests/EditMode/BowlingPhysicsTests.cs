using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// Gates P1, P2 and a quick P4 (PLAN_Bowling.md §12): the lane integrator and the pin deck.
    public class BowlingPhysicsTests
    {
        static BallState Roll(float board, float speed, float rpm, float axis)
        {
            var t = new BowlingThrow { Board = board, Speed = speed, RevRpm = rpm, AxisDeg = axis };
            return BowlingBall.Roll(t.Launch(), OilPattern.House);
        }

        [Test]
        public void SeventeenMphReachesThePinsInTwoAndAHalfSeconds()
        {
            var s = Roll(20, 7.6f, 150, 0);
            Assert.AreEqual(BallPhase.Deck, s.Phase);
            float atPin = s.Time + (BowlingLane.FoulToHeadPin - s.Position.z) / s.Velocity.z;
            Assert.That(atPin, Is.InRange(2.4f, 2.8f));
        }

        [Test]
        public void StraightBallStaysOnItsBoard()
        {
            var s = Roll(20, 7.6f, 150, 0);
            Assert.That(Mathf.Abs(BowlingLane.XBoard(s.Position.x) - 20), Is.LessThan(1f));
        }

        [Test]
        public void HookBallHooksLateIntoThePocket()
        {
            var start = new BowlingThrow { Board = 10, Speed = 7.6f, RevRpm = 300, AxisDeg = 45 }.Launch();
            var s = start; float boardAtTen = 0;
            while (s.Phase != BallPhase.Deck && s.Time < 10)
            {
                BowlingBall.Integrate(ref s, OilPattern.House, BowlingBall.Step);
                if (boardAtTen == 0 && s.Position.z >= 10) boardAtTen = BowlingLane.XBoard(s.Position.x);
            }
            float hook = BowlingLane.XBoard(s.Position.x) - 10;
            Assert.That(hook, Is.GreaterThan(8), "max-rev ball hooks at least 8 boards");
            Assert.That(boardAtTen - 10, Is.LessThan(hook * .4f), "most of the hook comes after the oil (skid → hook → roll)");
            float entry = Mathf.Atan2(-s.Velocity.x, s.Velocity.z) * Mathf.Rad2Deg;
            Assert.That(entry, Is.InRange(3f, 8f));
        }

        [Test]
        public void BackupBallHooksRight()
        {
            var s = Roll(25, 7.6f, 300, -40);
            Assert.That(BowlingLane.XBoard(s.Position.x), Is.LessThan(15));
        }

        [Test]
        public void BallOffTheEdgeIsAGutterBall()
        {
            var t = new BowlingThrow { Board = 2, Speed = 7, RevRpm = 0, AxisDeg = 0, LaunchDeg = 3 };
            var s = BowlingBall.Roll(t.Launch(), OilPattern.House);
            Assert.AreEqual(BallPhase.Pit, s.Phase);
        }

        [Test]
        public void ReleaseWindowGrades()
        {
            Assert.AreEqual(ReleaseGrade.Perfect, BowlingRelease.Grade(.03f));
            Assert.AreEqual(ReleaseGrade.Good, BowlingRelease.Grade(-.08f));
            Assert.AreEqual(ReleaseGrade.Early, BowlingRelease.Grade(-.2f));
            Assert.AreEqual(ReleaseGrade.Drop, BowlingRelease.Grade(-.3f));
            Assert.AreEqual(ReleaseGrade.Late, BowlingRelease.Grade(.2f));
            Assert.AreEqual(ReleaseGrade.Foul, BowlingRelease.Grade(.3f));
            var late = BowlingRelease.Resolve(new BowlingSwing { Board = 10, Speed = 7.6f, RevRpm = 300, AxisDeg = 45, TimingError = .2f, Seed = 3 });
            var perfect = BowlingRelease.Resolve(new BowlingSwing { Board = 10, Speed = 7.6f, RevRpm = 300, AxisDeg = 45, TimingError = 0, Seed = 3 });
            Assert.That(late.LoftHeight, Is.GreaterThan(perfect.LoftHeight));
            Assert.That(late.Speed, Is.LessThan(perfect.Speed));
            Assert.AreEqual(0, perfect.LaunchDeg, 1e-5f);
        }

        [Test]
        public void PinDeckSmoke()
        {
            var scene = EditorSceneManager.NewPreviewScene();
            try
            {
                using (var deck = new BowlingPinDeck(scene))
                {
                    // A rack with no ball must stay standing (pins are stable on their bases).
                    var idle = deck.Simulate(new BallState { Phase = BallPhase.Pit, Position = new Vector3(0, -1, 0) }, BowlingLeave.All);
                    Assert.AreEqual(BowlingLeave.All, idle.StandingAfter, "untouched rack stays up");

                    int strikes = 0, escaped = 0;
                    for (int i = 0; i < 20; i++)
                    {
                        var act = deck.Simulate(BowlingPinDeck.Arrival(17.5f + (i % 5 - 2) * .3f, 5 + (i % 3 - 1) * .5f, 6.4f), BowlingLeave.All);
                        if (act.StandingAfter == 0) strikes++;
                        escaped += act.Escaped;
                        Assert.That(act.SettleTime, Is.LessThanOrEqualTo(BowlingPinDeck.MaxTime + .01f));
                        Assert.That(act.Knocked, Is.GreaterThanOrEqualTo(5), "a pocket hit knocks most of the rack");
                    }
                    Assert.AreEqual(0, escaped, "no pin tunnels through the walls");
                    Assert.That(strikes, Is.GreaterThanOrEqualTo(10), "good pocket hits mostly strike");
                }
            }
            finally { EditorSceneManager.ClosePreviewScene(scene); }
        }
    }
}
