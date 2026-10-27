using System;
using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The 10-27 feel pass (Adnan: "make sure it's easy to put a good amount of power ... when someone aims right, they should
    /// bowl right, but it's a spectrum"). Phone swings as BowlingSelfTimedTests' pendulum (stance 70° forward of hanging, the drop
    /// through the bottom, the backswing to `back`°, the forward swing of quarter period `q`), the forward swing turning `aimDeg` off
    /// the backswing's line (+ = right) through its first 60 %, an optional wrist turn about the forearm over the last 0.18 s.
    public class BowlingSwingFeelTests
    {
        static double S(double x) { x = Math.Max(0, Math.Min(1, x)); return x * x * (3 - 2 * x); }

        static BowlingSwingDetector.Reading Swing(double back, double q, double aimDeg = 0, double twistDeg = 0, double noise = 0)
        {
            double q1 = q * .62, q2 = q1 * back / 35, q4 = q * 90 / back, tDrop = .45, tBack = tDrop + q1, tTop = tBack + q2, bottom = tTop + q;
            double lift = bottom + BowlingGame.ReleaseAfterBottom;
            double Phi(double t)
            {
                if (t < tDrop) { double u = t / tDrop; return 70 - 35 * u * u * (3 - 2 * u); }
                if (t < tBack) return 35 * Math.Cos(Math.PI / 2 * (t - tDrop) / q1);
                if (t < tTop) return -back * Math.Sin(Math.PI / 2 * (t - tBack) / q2);
                if (t < bottom) return -back * Math.Cos(Math.PI / 2 * (t - tTop) / q);
                return 90 * Math.Sin(Math.PI / 2 * Math.Min(1, (t - bottom) / q4));
            }
            // attitude: the plane's turn about up (+aim = clockwise from above), the arm about x (device z up the forearm when it
            // hangs), the wrist turn about the forearm; the rotation rate from the angles' own rates (as the self-timed tests do)
            double Yaw(double t) => t < tTop ? 0 : aimDeg * S((t - tTop) / (q * .6));
            double Twist(double t) => twistDeg * S((t - (lift - .18)) / .18);
            var rng = new System.Random(7);
            var d = new BowlingSwingDetector(); d.Begin(0);
            const double dt = .01;
            for (double t = dt; t <= lift + 1e-6; t += dt)
            {
                double D(Func<double, double> f) => (f(t) - f(t - dt)) / dt * Math.PI / 180;
                var plane = Quaternion.AngleAxis(-(float)Yaw(t), Vector3.forward);
                var arm = plane * Quaternion.AngleAxis((float)Phi(t), Vector3.right);
                var att = arm * Quaternion.AngleAxis((float)Twist(t), Vector3.forward);
                var world = Vector3.forward * (float)-D(Yaw) + plane * Vector3.right * (float)D(Phi) + arm * Vector3.forward * (float)D(Twist);
                var rate = Quaternion.Inverse(att) * world;
                if (noise > 0) rate += new Vector3((float)(rng.NextDouble() * 2 - 1), (float)(rng.NextDouble() * 2 - 1), (float)(rng.NextDouble() * 2 - 1)) * (float)noise;
                d.Ingest(t, att.x, att.y, att.z, att.w, rate.x, rate.y, rate.z);
            }
            Assert.IsTrue(d.ForwardSwing, "the forward swing was read");
            return d.Measure(lift);
        }

        static float Mph(BowlingSwingDetector.Reading r) => r.BallSpeed * 2.237f;

        // swing → mph (the detector's ball speed, before the release grade): nothing needs a violent swing
        [TestCase(20, .55, 15.0f, 16.5f, TestName = "Power: tiny swing (20 deg back, ~1 rad/s) ~15-16 mph")]
        [TestCase(30, .50, 16.0f, 17.8f, TestName = "Power: lazy swing (30 deg back, ~1.6 rad/s) ~16-18 mph")]
        [TestCase(45, .42, 18.0f, 19.6f, TestName = "Power: gentle swing (45 deg back, ~2.9 rad/s) high teens")]
        [TestCase(70, .36, 19.8f, 21.0f, TestName = "Power: normal swing (70 deg back, ~5.3 rad/s) ~20 mph")]
        [TestCase(95, .22, 20.8f, 21.25f, TestName = "Power: hard swing (95 deg back, ~12 rad/s) at the top")]
        public void PowerBands(double back, double q, float lo, float hi)
        {
            var r = Swing(back, q);
            Assert.That(Mph(r), Is.InRange(lo, hi), $"{Mph(r):0.0} mph");
        }

        [Test]
        public void HarderIsNeverSlower()
        {
            float last = 0;
            foreach (var (back, q) in new[] { (20.0, .55), (30.0, .5), (45.0, .42), (70.0, .36), (85.0, .3), (95.0, .22) })
            {
                float mph = Mph(Swing(back, q));
                Assert.That(mph, Is.GreaterThanOrEqualTo(last - .01f), $"{back}° back");
                last = mph;
            }
        }

        [Test]
        public void StraightSwingAimsStraight()
        {
            Assert.AreEqual(0, Swing(70, .36).AimDeg, .01f);
            Assert.AreEqual(0, Swing(45, .42).AimDeg, .01f);
        }

        [TestCase(15, 1.1f, 1.7f)]
        [TestCase(-15, -1.7f, -1.1f)]
        [TestCase(8, .35f, .8f)]
        [TestCase(-8, -.8f, -.35f)]
        public void SwingingRightBowlsRight(double swing, float lo, float hi)
        {
            var r = Swing(70, .36, swing);
            Assert.That(r.SwingAimDeg, Is.EqualTo((float)swing).Within(2f), "the swing's direction is read");
            Assert.That(r.AimDeg, Is.InRange(lo, hi), $"launch {r.AimDeg:0.00}°");
        }

        [Test]
        public void AimIsASpectrum()
        {
            float last = -99;
            for (int a = -30; a <= 30; a += 3)
            {
                float aim = Swing(70, .36, a).AimDeg;
                Assert.That(aim, Is.GreaterThanOrEqualTo(last - .02f), $"{a}° swing → {aim:0.00}° after {last:0.00}°");
                last = aim;
            }
            Assert.AreEqual(BowlingSwingDetector.MaxSwingAim, Swing(70, .36, 40).AimDeg, .01f, "capped");
            Assert.AreEqual(-BowlingSwingDetector.MaxSwingAim, Swing(70, .36, -40).AimDeg, .01f, "capped");
        }

        [TestCase(50)] [TestCase(-40)]
        public void WristTurnDoesNotAim(double twist)
        {
            // the hook's handshake (or a backup turn) about the forearm must not read as the swing turning
            var r = Swing(70, .36, 0, twist);
            Assert.That(Mathf.Abs(r.AimDeg), Is.LessThan(.15f), $"swing read {r.SwingAimDeg:0.0}°, launch {r.AimDeg:0.00}°");
            Assert.That(Mathf.Abs(r.AxisDeg), Is.GreaterThan(25), "still hooks / backs up");
            var right = Swing(70, .36, 15, twist);
            Assert.That(right.AimDeg, Is.InRange(.9f, 1.8f), "and a hook swung right still goes right");
        }

        [Test]
        public void ShakyPhoneStillAims()
        {
            // 0.3 rad/s of sensor noise on every axis, a gentle swing
            Assert.That(Mathf.Abs(Swing(45, .42, 0, 0, .3).AimDeg), Is.LessThan(.3f));
            Assert.That(Swing(45, .42, 15, 0, .3).AimDeg, Is.InRange(.9f, 2f));
        }

        [Test]
        public void AimFromSwingHasADeadZoneAndACap()
        {
            Assert.AreEqual(0, BowlingSwingDetector.AimFromSwing(0));
            Assert.AreEqual(0, BowlingSwingDetector.AimFromSwing(BowlingSwingDetector.AimDeadZone));
            Assert.AreEqual(0, BowlingSwingDetector.AimFromSwing(-BowlingSwingDetector.AimDeadZone));
            // continuous at the dead zone's edge, proportional past it, odd
            Assert.AreEqual(.012f, BowlingSwingDetector.AimFromSwing(BowlingSwingDetector.AimDeadZone + .1f), 1e-4f);
            Assert.AreEqual(2 * BowlingSwingDetector.AimFromSwing(8) - BowlingSwingDetector.AimFromSwing(3 + 0f), BowlingSwingDetector.AimFromSwing(13), 1e-4f);
            Assert.AreEqual(-BowlingSwingDetector.AimFromSwing(11), BowlingSwingDetector.AimFromSwing(-11), 1e-5f);
            Assert.AreEqual(BowlingSwingDetector.MaxSwingAim, BowlingSwingDetector.AimFromSwing(90));
            Assert.AreEqual(-BowlingSwingDetector.MaxSwingAim, BowlingSwingDetector.AimFromSwing(-90));
        }

        [Test]
        public void TheAimTurnsTheLaunch()
        {
            // a perfect release has no scatter or pull: the launch is the aim (networked throws carry LaunchDeg as is)
            var straight = BowlingRelease.Resolve(new BowlingSwing { Board = 20, Speed = 8.5f, RevRpm = 120, TimingError = 0, Seed = 3 });
            var right = BowlingRelease.Resolve(new BowlingSwing { Board = 20, Speed = 8.5f, RevRpm = 120, TimingError = 0, AimDeg = 1.4f, Seed = 3 });
            Assert.AreEqual(0, straight.LaunchDeg, 1e-5f);
            Assert.AreEqual(1.4f, right.LaunchDeg, 1e-5f);
            // the CPU plans with no aim (BowlingCpu.ArrivalX zeroes the launch; Plan never sets AimDeg): unchanged
            var good = BowlingRelease.Resolve(new BowlingSwing { Board = 20, Speed = 8.5f, RevRpm = 120, TimingError = .07f, Seed = 3 });
            var goodAimed = BowlingRelease.Resolve(new BowlingSwing { Board = 20, Speed = 8.5f, RevRpm = 120, TimingError = .07f, AimDeg = -1, Seed = 3 });
            Assert.AreEqual(good.LaunchDeg - 1, goodAimed.LaunchDeg, 1e-5f, "the aim adds to the release's own scatter");
        }

        [Test]
        public void ReleasesKeepMostOfTheSpeed()
        {
            float Speed(float timing) => BowlingRelease.Resolve(new BowlingSwing { Board = 20, Speed = 8.5f, RevRpm = 120, TimingError = timing, Seed = 1 }).Speed;
            Assert.That(Speed(0), Is.GreaterThanOrEqualTo(8.5f));
            Assert.That(Speed(.07f), Is.GreaterThanOrEqualTo(8.5f));          // good
            Assert.That(Speed(-.15f), Is.GreaterThanOrEqualTo(8.5f * .92f - 1e-4f)); // early
            Assert.That(Speed(.15f), Is.GreaterThanOrEqualTo(8.5f * .96f - 1e-4f));  // late
        }
    }
}
