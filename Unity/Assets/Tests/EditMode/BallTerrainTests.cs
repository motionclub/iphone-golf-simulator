using System;
using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.Swing;
using NUnit.Framework;

namespace GolfArcade.Tests
{
    /// The ball on a modelled hole's own ground, off the green's sampled grid (11-24: "the ball sometimes dies or goes
    /// straight up"). Before, everything past the green's grid read as dead flat to the bounce and the roll: a ball that
    /// hopped or rolled into a bank or a terrace's riser was drawn riding straight up its face — up to 30 yards in a frame on
    /// the Steps (hole 15), a few yards on Wild Isles' banks (18, 19) — and dropped back at gravity, which looked like a
    /// launch straight up; and a slope never slowed or turned a roll.
    public class BallTerrainTests
    {
        static Hole HoleOn(Func<CoursePoint, double> ground)
        {
            var hole = new Hole
            {
                Number = 97, Par = 4,
                Centerline = new[] { new CoursePoint(0, 0), new CoursePoint(0, 420) },
                FairwayWidth = 80, GreenRadius = 10, RoughWidth = 60,
            };
            hole.Ground = ground;
            return hole;
        }

        static CourseShot Hit(Hole hole, GolfClub club, double power, double heading = 0) =>
            new(club, new SwingImpact { Power = power }, heading, new CoursePoint(0, 0), hole);

        /// The steepest the drawn ball climbs in any one frame after it first comes down, yards, counting only frames in which
        /// it goes up more than twice as far as it goes across (a hop climbs as it travels; riding a face only goes up).
        static double WorstClimb(CourseShot shot, Func<CoursePoint, double> ground)
        {
            double worst = 0;
            var prev = shot.WorldAt(shot.LandingTime, ground);
            for (double t = shot.LandingTime + 1.0 / 60; t <= shot.Duration + 1e-9; t += 1.0 / 60)
            {
                var w = shot.WorldAt(t, ground);
                double across = Math.Sqrt((w.x - prev.x) * (w.x - prev.x) + (w.d - prev.d) * (w.d - prev.d)), up = w.y - prev.y;
                if (up > 2 * across) worst = Math.Max(worst, up);
                prev = w;
            }
            return worst;
        }

        [Test]
        public void ABallRunningIntoATerraceRiserComesOffItInsteadOfUpIt()
        {
            // The Steps: a 4-yard riser across the fairway at 135 yards. Drivers of every pace land short of it and run in.
            Func<CoursePoint, double> ground = p => p.D > 135 ? 4.0 : 0;
            var hole = HoleOn(ground);
            int reached = 0;
            for (double power = 0.45; power <= 0.56; power += 0.01)
            {
                var shot = Hit(hole, GolfClub.Driver, power);
                if (shot.Landing.D > 135) continue;   // flew onto the top
                reached++;
                Assert.That(WorstClimb(shot, ground), Is.LessThan(0.3), $"p{power:0.00}: the ball is drawn going straight up the riser");
                Assert.That(shot.Rest.D, Is.LessThan(135), $"p{power:0.00}: it ended on top of the riser ({shot.Rest.D:0.0})");
            }
            Assert.That(reached, Is.GreaterThan(3), "some of the drives must land short and run into the riser");
        }

        [Test]
        public void AHopIntoASteepBankIsNotThrownUpItsFace()
        {
            // a 60° bank, 6 yards high, across a fairway: a ball skipping into it is turned back, not launched up it
            Func<CoursePoint, double> ground = p => p.D < 130 ? 0 : p.D < 133.5 ? (p.D - 130) * 1.73 : 6.06;
            var hole = HoleOn(ground);
            foreach (var club in new[] { GolfClub.Driver, GolfClub.Hybrid, GolfClub.Iron5 })
                for (double power = 0.3; power <= 1.001; power += 0.05)
                {
                    var shot = Hit(hole, club, power);
                    Assert.That(WorstClimb(shot, ground), Is.LessThan(0.3), $"{club} p{power:0.00}: drawn straight up the bank");
                    // after its first touchdown it never gets much higher than it came down (a drive may arrive on the bank
                    // itself, part way up)
                    double landedAt = shot.WorldAt(shot.LandingTime, ground).y, highest = landedAt;
                    for (double t = shot.LandingTime; t <= shot.Duration; t += 1.0 / 60) highest = Math.Max(highest, shot.WorldAt(t, ground).y);
                    Assert.That(highest - landedAt, Is.LessThan(2.0), $"{club} p{power:0.00}: thrown {highest - landedAt:0.0} yd up the bank from where it came down");
                }
        }

        [Test]
        public void TheFairwaysOwnSlopeSlowsARunUphillAndCarriesItDownhill()
        {
            // An 8% slope rising (or falling) down the fairway from 100 yards, nowhere near the green's grid: the roll used to
            // read it as flat and run the same either way.
            Func<CoursePoint, double> up = p => Math.Max(0, p.D - 100) * 0.08, down = p => -Math.Max(0, p.D - 100) * 0.08;
            Func<CoursePoint, double> flat = _ => 0;
            for (double power = 0.5; power <= 0.81; power += 0.1)
            {
                var onFlat = Hit(HoleOn(flat), GolfClub.Driver, power);
                var uphill = Hit(HoleOn(up), GolfClub.Driver, power);
                var downhill = Hit(HoleOn(down), GolfClub.Driver, power);
                double runFlat = onFlat.Touchdown.DistanceTo(onFlat.Rest), runUp = uphill.Touchdown.DistanceTo(uphill.Rest),
                       runDown = downhill.Touchdown.DistanceTo(downhill.Rest);
                Assert.That(runUp, Is.LessThan(runFlat * 0.9), $"p{power:0.0}: uphill ran {runUp:0.0} yd, flat {runFlat:0.0}");
                Assert.That(runDown, Is.GreaterThan(runFlat * 1.1), $"p{power:0.0}: downhill ran {runDown:0.0} yd, flat {runFlat:0.0}");
                Assert.That(WorstClimb(uphill, up), Is.LessThan(0.3));
            }
        }

        [Test]
        public void ASlopesPullIsGravitysShareAndNeverMore()
        {
            // a green's gentle tilt pulls as before (g × gradient, to a part in a thousand); a mesh's crease or a cliff's edge,
            // whose gradient reads 5 or 50, pulls no harder than gravity itself
            var (gx, gd) = CourseShot.Pull((0.03, -0.02));
            Assert.That(gx, Is.EqualTo(-CourseShot.GravityYards * 0.03).Within(CourseShot.GravityYards * 0.03 * 1e-3));
            Assert.That(gd, Is.EqualTo(CourseShot.GravityYards * 0.02).Within(CourseShot.GravityYards * 0.02 * 1e-3));
            foreach (var s in new[] { 1.0, 5.0, 50.0 })
            {
                var (ax, ad) = CourseShot.Pull((s, 0));
                Assert.That(Math.Sqrt(ax * ax + ad * ad), Is.LessThanOrEqualTo(CourseShot.GravityYards), $"gradient {s}");
                Assert.That(ax, Is.LessThan(0), "downhill");
            }
        }

        [Test]
        public void ARollOverGroundTheMeshesMissStaysFinite()
        {
            // a hole of islands: off the land the ground reads 0 (the raycast found nothing) while the land stands 30 yards up
            Func<CoursePoint, double> ground = p => Math.Abs(p.X) < 30 && p.D < 300 ? 30 : 0;
            var hole = HoleOn(ground);
            for (double heading = -14; heading <= 14; heading += 2)
                foreach (var club in new[] { GolfClub.Driver, GolfClub.Iron, GolfClub.Wedge })
                {
                    var shot = new CourseShot(club, new SwingImpact { Power = 0.8 }, heading, new CoursePoint(0, 0), hole);
                    Assert.That(double.IsFinite(shot.Rest.X) && double.IsFinite(shot.Rest.D) && double.IsFinite(shot.Duration), $"{club} {heading}");
                    Assert.That(WorstClimb(shot, ground), Is.LessThan(0.3), $"{club} {heading}: climbed the island's side");
                }
        }
    }
}
