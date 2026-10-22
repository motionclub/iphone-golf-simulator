using System.Collections.Generic;
using System.Numerics;
using GolfArcade.Shot;
using GolfArcade.Swing;
using NUnit.Framework;

namespace GolfArcade.Tests
{
    /// GOLF SWING SPEED: the phone paces the golfer's downswing (GolferView.PaceDownswing), so the detector's DownswingProgress
    /// must run from the top (0) to the ball (1) without going back, and be at the ball when the shot is struck.
    public class GolfSwingPaceTests
    {
        static readonly Quaternion Flat = Quaternion.Identity;

        /// A full swing, 100 Hz: address, eased backswing to `top` rad, a pause, a downswing with even angular acceleration that
        /// reaches the ball after `down` s, then the follow-through. Returns (progress while coming down, progress when struck).
        static (List<double> coming, double struck) Swing(GolfClub club, double top, double down)
        {
            var d = new MotionSwingDetector(); d.SetReadyPose(Flat); d.Configure(club);
            var coming = new List<double>(); double struck = double.NaN, t = 0;
            void Feed(double angle, double rate)
            {
                t += .01;
                var e = d.Ingest(t, Quaternion.CreateFromAxisAngle(Vector3.UnitX, (float)angle), new Vector3((float)rate, 0, 0), Vector3.Zero);
                if (d.Phase == SwingPhase.Downswing) coming.Add(d.DownswingProgress);
                if (e?.Kind == SwingEventKind.Impact) struck = d.DownswingProgress;
            }
            for (int i = 0; i < 40; i++) Feed(0, 0);
            for (int i = 1; i <= 80; i++) { double u = i / 80.0; Feed(top * (.5 - .5 * System.Math.Cos(System.Math.PI * u)), top * .5 * System.Math.PI / .8 * System.Math.Sin(System.Math.PI * u)); }
            for (int i = 0; i < 6; i++) Feed(top, 0);
            double k = top / (down * down);
            for (double s = .01; s < down * 1.3; s += .01) Feed(top - k * s * s, -2 * k * s);
            return (coming, struck);
        }

        [TestCase(GolfClub.Driver, 2.75, .20)]
        [TestCase(GolfClub.Driver, 2.75, .32)]
        [TestCase(GolfClub.Iron, 1.6, .28)]
        [TestCase(GolfClub.Putter, .45, .35)]
        public void DownswingProgressRunsFromTheTopToTheBall(GolfClub club, double top, double down)
        {
            var (coming, struck) = Swing(club, top, down);
            Assert.IsNotEmpty(coming, "the downswing was seen");
            Assert.Less(coming[0], .15, "it starts near the top");
            for (int i = 1; i < coming.Count; i++) Assert.GreaterOrEqual(coming[i], coming[i - 1] - 1e-9, $"never back (sample {i})");
            Assert.IsFalse(double.IsNaN(struck), "the swing was struck");
            Assert.That(struck, Is.InRange(.97, 1.15), "the phone is at the ball when the shot is struck");
        }
    }
}
