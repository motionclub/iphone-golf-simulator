using System;
using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The phone swing detector on synthetic swings (gate I1 runs the same on recorded phones).
    /// A pendulum about world x (CoreMotion z-up frame) with a wrist turn about the arm just
    /// before the thumb lifts; the arm hangs vertical at the release.
    public class BowlingSwingTests
    {
        struct Q
        {
            public double x, y, z, w;
            public Q(double x, double y, double z, double w) { this.x = x; this.y = y; this.z = z; this.w = w; }
            public static Q Axis(double ax, double ay, double az, double a) { double s = Math.Sin(a / 2); return new Q(ax * s, ay * s, az * s, Math.Cos(a / 2)); }
            public static Q operator *(Q a, Q b) => new Q(a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y, a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
                a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w, a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z);
            public Q Conj => new Q(-x, -y, -z, w);
        }

        static double S(double x) { x = Math.Max(0, Math.Min(1, x)); return x * x * (3 - 2 * x); }

        // stance (ball at the chest) 0 → pushaway → top of the backswing → release at the bottom
        static double Theta(double t)
        {
            if (t < .45) return .2 * t / .45;
            if (t < 1.25) return .2 + (-2.6 - .2) * S((t - .45) / .8);
            return -2.6 + 1.5 * S((t - 1.25) / .47);
        }

        static BowlingSwingDetector.Reading Swing(double twistDeg, double scale = 1)
        {
            const double dt = .01, lift = 1.72;
            var d = new BowlingSwingDetector();
            d.Begin(0);
            Q At(double t) => Q.Axis(1, 0, 0, (Theta(t) - Theta(lift)) * scale) * Q.Axis(0, 0, 1, twistDeg * Math.PI / 180 * S((t - (lift - .15)) / .15));
            var prev = At(0);
            for (double t = dt; t <= lift + 1e-6; t += dt)
            {
                var q = At(t);
                var dq = prev.Conj * q;
                if (dq.w < 0) dq = new Q(-dq.x, -dq.y, -dq.z, -dq.w);
                double angle = 2 * Math.Acos(Math.Min(1, dq.w)), sn = Math.Sqrt(Math.Max(0, 1 - dq.w * dq.w));
                var rate = sn < 1e-9 ? Vector3.zero : new Vector3((float)(dq.x / sn), (float)(dq.y / sn), (float)(dq.z / sn)) * (float)(angle / dt);
                d.Ingest(t, (float)q.x, (float)q.y, (float)q.z, (float)q.w, rate.x, rate.y, rate.z);
                prev = q;
            }
            return d.Measure(lift);
        }

        [Test]
        public void StraightSwingIsAStraightBall()
        {
            var r = Swing(0);
            Assert.AreEqual(0, r.AxisDeg, .5f);
            Assert.That(r.RevRpm, Is.LessThanOrEqualTo(160));
            Assert.That(r.Load, Is.GreaterThan(.9f));
            Assert.That(r.BallSpeed, Is.InRange(8f, 9.5f));   // 10-27: a full swing is ~19-20 mph
            Assert.That(r.DriftDeg, Is.LessThan(3));
        }

        [Test]
        public void HandshakeTurnHooks()
        {
            var r = Swing(50);
            Assert.AreEqual(50, r.AxisDeg, 4);
            Assert.That(r.RevRpm, Is.GreaterThan(250));
        }

        [Test]
        public void OppositeTurnBacksUp()
        {
            var r = Swing(-40);
            Assert.AreEqual(-40, r.AxisDeg, 4);
        }

        [Test]
        public void HalfSwingIsSlower()
        {
            var full = Swing(0); var half = Swing(0, .5);
            Assert.That(half.Load, Is.LessThan(.6f));
            // 10-27 feel pass: the curve flattens toward the top so any real swing makes most of the speed; half a swing is still
            // ~2 mph slower (was "more than 1 m/s")
            Assert.That(half.BallSpeed, Is.LessThan(full.BallSpeed - .6f));
        }

        [Test]
        public void SideRollIsCappedForPositionOnlyAiming()
        {
            var t = BowlingRelease.Resolve(new BowlingSwing { Board = 4, Speed = 7.6f, RevRpm = 450, AxisDeg = 75, Seed = 1 });
            float side = t.RevRpm * 2 * Mathf.PI / 60 * Mathf.Sin(t.AxisDeg * Mathf.Deg2Rad);
            Assert.That(side, Is.LessThanOrEqualTo(BowlingRelease.MaxSideRoll + .01f));
        }
    }
}
