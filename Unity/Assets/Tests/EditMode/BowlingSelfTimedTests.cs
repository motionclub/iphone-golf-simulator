using System;
using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// Bowling V2's self-timed release (PLAN_PhonePlay_NoTV_GolfBowling.md §5, gate G6): the thumb lift is graded against the
    /// player's own arm passing the bottom, at any tempo. The phone swings as a pendulum about world x: the pushaway from the
    /// chest, the drop through the bottom into the backswing, the forward swing back through the bottom into the follow-through.
    public class BowlingSelfTimedTests
    {
        const double Dt = .01;

        /// Arm angle from hanging straight down, degrees (+ forward). `q` = the forward swing's top-to-bottom quarter period.
        static double Phi(double t, double q, out double bottom)
        {
            double q1 = q * .62, a = 80, q2 = q1 * a / 35, q4 = q * 90 / a;
            double tDrop = .45, tBack = tDrop + q1, tTop = tBack + q2; bottom = tTop + q;
            if (t < tDrop) { double u = t / tDrop; return 70 - 35 * u * u * (3 - 2 * u); }
            if (t < tBack) return 35 * Math.Cos(Math.PI / 2 * (t - tDrop) / q1);
            if (t < tTop) return -a * Math.Sin(Math.PI / 2 * (t - tBack) / q2);
            if (t < bottom) return -a * Math.Cos(Math.PI / 2 * (t - tTop) / q);
            return 90 * Math.Sin(Math.PI / 2 * Math.Min(1, (t - bottom) / q4));
        }

        /// Swings at tempo `q` and lifts the thumb `afterBottom` seconds after the true bottom: the graded timing error.
        static float ReleaseError(double q, double afterBottom)
        {
            Phi(0, q, out double bottom);
            double lift = bottom + afterBottom;
            var d = new BowlingSwingDetector(); d.Begin(0);
            float prevPhi = (float)Phi(0, q, out _);
            for (double t = Dt; t <= lift + 1e-6; t += Dt)
            {
                float phi = (float)Phi(t, q, out _);
                var rel = Quaternion.AngleAxis(phi - 70, Vector3.right);   // the phone's attitude, relative to the stance
                float rate = (phi - prevPhi) * Mathf.Deg2Rad / (float)Dt;
                var deviceRate = Quaternion.Inverse(rel) * (Vector3.right * rate);   // rotation rate in the device frame
                d.Ingest(t, rel.x, rel.y, rel.z, rel.w, deviceRate.x, deviceRate.y, deviceRate.z);
                prevPhi = phi;
            }
            Assert.IsTrue(d.ForwardSwing, "the forward swing was seen");
            return d.SinceBottom(lift) - BowlingGame.ReleaseAfterBottom;
        }

        [TestCase(.26)] [TestCase(.33)] [TestCase(.42)]   // fast, normal, slow tempo
        public void ReleaseJustPastTheBottomIsPerfectAtAnyTempo(double q)
        {
            float e = ReleaseError(q, BowlingGame.ReleaseAfterBottom);
            Assert.AreEqual(ReleaseGrade.Perfect, BowlingRelease.Grade(e), $"error {e * 1000:0} ms at tempo {q}");
        }

        [TestCase(.26)] [TestCase(.33)] [TestCase(.42)]
        public void LettingGoOnTheWayDownIsEarly(double q)
        {
            float e = ReleaseError(q, -.12);
            Assert.AreEqual(ReleaseGrade.Early, BowlingRelease.Grade(e), $"error {e * 1000:0} ms at tempo {q}");
        }

        [TestCase(.26)] [TestCase(.33)] [TestCase(.42)]
        public void HangingOnAsTheArmRisesIsLate(double q)
        {
            float e = ReleaseError(q, .22);
            Assert.AreEqual(ReleaseGrade.Late, BowlingRelease.Grade(e), $"error {e * 1000:0} ms at tempo {q}");
        }

        [Test]
        public void HoldingThroughTheFollowThroughFouls()
        {
            float e = ReleaseError(.33, .45);
            Assert.AreEqual(ReleaseGrade.Foul, BowlingRelease.Grade(e), $"error {e * 1000:0} ms");
        }
    }
}
