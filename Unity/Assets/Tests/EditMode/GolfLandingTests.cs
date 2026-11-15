using System;
using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.Swing;
using NUnit.Framework;

namespace GolfArcade.Tests
{
    /// How a golf ball lands (PLAN_FinalLook_Gameplay_2026-11-11, Phase 1 "Golf: a landing that depends on the shot").
    ///
    /// The flight was always a real one; the landing was not. From 10-28 every full shot, wedges included, got 30-46% of
    /// its fall back, hopped 1-2.4 m and skipped two or three times whatever the club or the ground
    /// (ShotModelTests.AFullShotKicksUpThenSkipsAndRuns required it). These tests replace that one with the plan's table:
    /// what the ball does now depends on how steeply and how fast it comes down, the spin it has, the ground it lands on
    /// and the slope under it. The same arithmetic outside Unity: work/final-plan-1111/phase1/golf_model.py.
    public class GolfLandingTests
    {
        const double Yd = BallFlight.MetersPerYard;

        struct Landed { public int Hops; public double FirstHopMetres, RunYards; }

        static Landed Land(GolfClub club, CourseLie onto, double power = 1, double spinScale = 1)
        {
            var launch = club.Launch(power, 0, 0);
            launch.SpinRPM *= spinScale;
            launch.Ground = onto.Ground();
            var f = BallFlight.Simulate(launch);
            var r = new Landed { RunYards = f.Landing.DistanceYards - f.CarryPoint.DistanceYards };
            // a hop is a top in the sampled path after the first touchdown (the samples straddle each bounce, so the
            // heights never quite reach the ground between hops: count the tops, not the ground contacts)
            var s = f.Samples;
            int first = (int)Math.Ceiling(f.CarryTime / BallFlight.SampleInterval) + 1, last = Math.Min(s.Count - 2, (int)Math.Ceiling(f.RollStartTime / BallFlight.SampleInterval) + 1);
            for (int i = first; i <= last; i++)
            {
                double h = s[i].HeightYards;
                if (h > 0.02 && h > s[i - 1].HeightYards && h >= s[i + 1].HeightYards)
                {
                    r.Hops++;
                    if (r.Hops == 1) r.FirstHopMetres = h * Yd;
                }
            }
            return r;
        }

        [Test]
        public void AFullWedgeOntoAGreenStopsByItsPitchMark()
        {
            foreach (var club in new[] { GolfClub.PitchingWedge, GolfClub.Wedge, GolfClub.LobWedge })
            {
                var l = Land(club, CourseLie.Green);
                Assert.That(l.FirstHopMetres, Is.LessThanOrEqualTo(0.5), $"{club}: first hop {l.FirstHopMetres:0.00} m (1.4-1.7 m before 11-11)");
                Assert.That(l.RunYards, Is.LessThanOrEqualTo(3.0), $"{club}: finished {l.RunYards:0.0} yd past its pitch mark");
                Assert.That(l.RunYards, Is.GreaterThan(-6.0), $"{club}: drew back {-l.RunYards:0.0} yd, further than a wedge does");
            }
        }

        [Test]
        public void MoreSpinChecksHarderAndAPureLobWedgeDrawsBack()
        {
            // The strike's spin wanders by up to 10% (StrikeGrade.SpinScatter): the pure end of it bites more.
            double usual = Land(GolfClub.LobWedge, CourseLie.Green).RunYards, pure = Land(GolfClub.LobWedge, CourseLie.Green, 1, 1.1).RunYards,
                   thin = Land(GolfClub.LobWedge, CourseLie.Green, 1, 0.5).RunYards;
            Assert.That(pure, Is.LessThan(usual), "more backspin finishes shorter");
            Assert.That(pure, Is.LessThan(0), $"a pure lob wedge comes back off its pitch mark ({pure:0.00} yd)");
            Assert.That(thin, Is.GreaterThan(usual + 0.5), "one with half the spin releases");
            // the same ball out of the rough, where the grass gives the spin nothing to hold, does not draw back
            Assert.That(Land(GolfClub.LobWedge, CourseLie.Rough, 1, 1.1).RunYards, Is.GreaterThanOrEqualTo(-0.05));
        }

        [Test]
        public void ASevenIronOntoAFairwayTakesAHopOrTwoAndRunsAFewYards()
        {
            var l = Land(GolfClub.Iron, CourseLie.Fairway);
            Assert.That(l.Hops, Is.InRange(1, 2), "7 iron hops");
            Assert.That(l.RunYards, Is.InRange(5.0, 10.0), $"7 iron ran {l.RunYards:0.0} yd");
            Assert.That(l.FirstHopMetres, Is.LessThanOrEqualTo(0.9), $"7 iron's first hop {l.FirstHopMetres:0.00} m (1.8 m before 11-11)");
        }

        [Test]
        public void ADriveSkipsForwardAndRuns()
        {
            var l = Land(GolfClub.Driver, CourseLie.Fairway);
            Assert.That(l.Hops, Is.InRange(1, 3), "a drive skips");
            Assert.That(l.RunYards, Is.InRange(15.0, 30.0), $"a drive ran {l.RunYards:0.0} yd");
            Assert.That(l.FirstHopMetres, Is.InRange(0.2, 1.2), $"a low skip, not a head-high kick ({l.FirstHopMetres:0.00} m; 1.9 m before 11-11)");
        }

        [Test]
        public void TheLongerTheClubTheFurtherItRuns()
        {
            double last = double.MaxValue;
            foreach (var club in new[] { GolfClub.Driver, GolfClub.Hybrid, GolfClub.Iron5, GolfClub.Iron, GolfClub.Iron9, GolfClub.PitchingWedge, GolfClub.Wedge, GolfClub.LobWedge })
            {
                double run = Land(club, CourseLie.Fairway).RunYards;
                Assert.That(run, Is.LessThan(last), $"{club} runs {run:0.0} yd, less than the club above it");
                last = run;
            }
        }

        [Test]
        public void SandTakesEverythingAndRoughAllowsOneDeadHop()
        {
            foreach (var club in new[] { GolfClub.Driver, GolfClub.Iron5, GolfClub.Iron, GolfClub.PitchingWedge, GolfClub.LobWedge })
            {
                var sand = Land(club, CourseLie.Bunker);
                Assert.That(sand.Hops, Is.EqualTo(0), $"{club} into a bunker: no hop");
                Assert.That(Math.Abs(sand.RunYards), Is.LessThan(1.5), $"{club} into a bunker moved {sand.RunYards:0.0} yd");
                var rough = Land(club, CourseLie.Rough);
                Assert.That(rough.Hops, Is.LessThanOrEqualTo(1), $"{club} into rough: one hop at most");
                Assert.That(rough.FirstHopMetres, Is.LessThanOrEqualTo(0.35), $"{club} into rough: a dead hop ({rough.FirstHopMetres:0.00} m)");
                // (a lob wedge checks on fairway by its spin and has no run to lose; the rough only has to stop it too)
                double fairway = Land(club, CourseLie.Fairway).RunYards;
                if (fairway > 2) Assert.That(rough.RunYards, Is.LessThan(fairway), $"{club}: rough holds it shorter than fairway");
                else Assert.That(rough.RunYards, Is.LessThan(2.0), $"{club}: stopped in the rough");
            }
        }

        [Test]
        public void EveryLieIsItsOwnGround()
        {
            var lies = new[] { CourseLie.Tee, CourseLie.Fairway, CourseLie.Fringe, CourseLie.Green, CourseLie.Rough, CourseLie.Bunker, CourseLie.OutOfBounds, CourseLie.Ice };
            for (int i = 0; i < lies.Length; i++)
                for (int j = i + 1; j < lies.Length; j++)
                {
                    Turf a = lies[i].Ground(), b = lies[j].Ground();
                    bool same = a.Firm == b.Firm && a.Give == b.Give && a.Friction == b.Friction && a.Take == b.Take && a.Dead == b.Dead && a.Bite == b.Bite;
                    Assert.IsFalse(same, $"{lies[i]} and {lies[j]} bounce alike");
                }
            // ice gives the spin nothing to hold: even a wedge skids on
            Assert.That(Land(GolfClub.PitchingWedge, CourseLie.Ice).RunYards, Is.GreaterThan(Land(GolfClub.PitchingWedge, CourseLie.Fairway).RunYards + 10));
        }

        // ---- on the course: slope, and each hop on its own ground -------------------------------------------------------

        static Hole Straight(double tiltD = 0, double tiltX = 0, double greenRadius = 60, double fairwayWidth = 80) => new()
        {
            Number = 1, Par = 4, Centerline = new[] { new CoursePoint(0, -400), new CoursePoint(0, 0) },
            FairwayWidth = fairwayWidth, GreenRadius = greenRadius, Surface = new Contours { TiltD = tiltD, TiltX = tiltX },
        };

        static SwingImpact Planned(double power = 1) => new() { Power = power, StartLineDegrees = 0, CurveDegrees = 0 };

        static double RunAfterPitching(CourseShot s) => (s.Rest.D - s.Landing.D);

        [Test]
        public void AnUpslopeStopsWhatADownslopeSendsOn()
        {
            foreach (var club in new[] { GolfClub.Driver, GolfClub.Iron })
            {
                // from the fairway 300 yd out, so it pitches on fairway well short of the green
                var from = new CoursePoint(0, -330);
                double up = RunAfterPitching(new CourseShot(club, Planned(), 0, from, Straight(0.06)));
                double level = RunAfterPitching(new CourseShot(club, Planned(), 0, from, Straight(0)));
                double down = RunAfterPitching(new CourseShot(club, Planned(), 0, from, Straight(-0.06)));
                Assert.That(up, Is.LessThan(level), $"{club}: into a 6% upslope {up:0.0} yd, level {level:0.0} yd");
                Assert.That(down, Is.GreaterThan(level), $"{club}: down a 6% slope {down:0.0} yd, level {level:0.0} yd");
                Assert.That(up, Is.LessThan(down * 0.75), $"{club}: the upslope finishes clearly shorter ({up:0.0} against {down:0.0} yd)");
            }
        }

        [Test]
        public void ASideSlopeKicksTheBallDownhill()
        {
            var from = new CoursePoint(0, -330);
            var flat = new CourseShot(GolfClub.Iron, Planned(), 0, from, Straight(0, 0));
            var tilted = new CourseShot(GolfClub.Iron, Planned(), 0, from, Straight(0, 0.06));   // ground rises to the right
            Assert.That(Math.Abs(flat.Rest.X), Is.LessThan(0.5));
            Assert.That(tilted.Rest.X, Is.LessThan(tilted.Landing.X - 0.5), $"kicked and ran left, down the slope ({tilted.Rest.X - tilted.Landing.X:0.0} yd)");
        }

        [Test]
        public void EachHopLandsOnItsOwnGround()
        {
            // A 5 iron pitching on the back of a small green: its first hop carries it off the back, into the rough.
            // Before 11-11 the whole landing was judged where it first touched down, so it bounced and ran as if on green.
            double carry = GolfClub.Iron5.ReferenceDistanceYards();
            var small = Straight(0, 0, greenRadius: 9, fairwayWidth: 6);
            var open = Straight(0, 0, greenRadius: 60);
            var from = new CoursePoint(0, 6 - carry);   // pitches about 6 yd past the pin
            var held = new CourseShot(GolfClub.Iron5, Planned(), 0, from, small);
            var ran = new CourseShot(GolfClub.Iron5, Planned(), 0, from, open);
            Assert.AreEqual(CourseLie.Green, small.LieAt(held.Landing), "it pitched on the green");
            Assert.AreEqual(CourseLie.Rough, small.LieAt(held.Rest), $"and finished in the rough behind it, at {held.Rest}");
            Assert.That(RunAfterPitching(held), Is.LessThan(RunAfterPitching(ran) * 0.75),
                $"the rough held it: {RunAfterPitching(held):0.0} yd against {RunAfterPitching(ran):0.0} yd on an open green");
        }

        [Test]
        public void NoTwoStrikesLandQuiteAlikeAndEveryPhoneSeesTheSameBounce()
        {
            Assert.AreEqual(0, CourseShot.LandingLuck(Planned()), "a planned shot (the preview, the tests) lands as the average one does");
            var a = Planned(); a.SpinScatter = 0.04; a.SpeedBonus = 0.01;
            var b = Planned(); b.SpinScatter = -0.07; b.SpeedBonus = 0.02;
            Assert.That(CourseShot.LandingLuck(a), Is.InRange(-1.0, 1.0));
            Assert.AreNotEqual(CourseShot.LandingLuck(a), CourseShot.LandingLuck(b));
            Assert.AreEqual(CourseShot.LandingLuck(a), CourseShot.LandingLuck(a), "the same strike, the same bounce: nothing is rolled at landing");
            // and the luck is small: the same swing lands within a few yards of itself
            var from = new CoursePoint(0, -330); var hole = Straight();
            double plain = new CourseShot(GolfClub.Iron, Planned(), 0, from, hole).Rest.D;
            double min = double.MaxValue, max = double.MinValue;
            var rng = new Random(11);
            for (int i = 0; i < 40; i++)
            {
                var impact = Planned(); impact.SpinScatter = (rng.NextDouble() - 0.5) * 0.2; impact.SpeedBonus = 1e-9 * (i + 1);
                double d = new CourseShot(GolfClub.Iron, impact, 0, from, hole).Rest.D;
                min = Math.Min(min, d); max = Math.Max(max, d);
            }
            Assert.That(max - min, Is.GreaterThan(0.5), "identical swings do not finish on the same blade of grass");
            Assert.That(max - min, Is.LessThan(12), $"but they finish together ({min - plain:0.0} to {max - plain:+0.0} yd of the planned shot)");
        }

        [Test]
        public void TheBounceNeverAddsEnergyAndNeverLeavesTheBallUnderTheGround()
        {
            var rng = new Random(7);
            var lies = new[] { CourseLie.Fairway, CourseLie.Green, CourseLie.Rough, CourseLie.Bunker, CourseLie.Ice, CourseLie.Fringe, CourseLie.OutOfBounds };
            for (int i = 0; i < 4000; i++)
            {
                double vx = (rng.NextDouble() - 0.5) * 40, vz = (rng.NextDouble() - 0.5) * 60, vy = -rng.NextDouble() * 30 - 0.01;
                double spin = (rng.NextDouble() - 0.3) * 1200, sx = (rng.NextDouble() - 0.5) * 0.4, sz = (rng.NextDouble() - 0.5) * 0.4;
                double before = vx * vx + vy * vy + vz * vz + 0.4 * BallFlight.BallRadiusMetres * BallFlight.BallRadiusMetres * spin * spin;
                double ax = vx, ay = vy, az = vz, s = spin;
                BallFlight.BounceOff(ref ax, ref ay, ref az, ref s, lies[i % lies.Length].Ground(), sx, sz, 1, rng.NextDouble() * 2 - 1);
                Assert.IsTrue(double.IsFinite(ax) && double.IsFinite(ay) && double.IsFinite(az) && double.IsFinite(s), $"case {i}");
                double after = ax * ax + ay * ay + az * az + 0.4 * BallFlight.BallRadiusMetres * BallFlight.BallRadiusMetres * s * s;
                Assert.That(after, Is.LessThanOrEqualTo(before * 1.0001 + 1e-9), $"case {i}: the bounce added energy");
                // leaving the face, not into it (the ground's normal is (-sx, 1, -sz))
                Assert.That(-sx * ax + ay - sz * az, Is.GreaterThanOrEqualTo(-1e-9), $"case {i}: it left into the ground");
            }
        }
    }
}
