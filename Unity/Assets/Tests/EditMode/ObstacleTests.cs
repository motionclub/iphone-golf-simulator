using System;
using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.Swing;
using NUnit.Framework;

namespace GolfArcade.Tests
{
    /// The ball against what stands on the course: into a tree's branches and down short of it,
    /// back off a wall, a putt off a trunk, caught in a bush, and stopped by soft sand.
    public class ObstacleTests
    {
        /// A long straight flat hole down +D, a bunker where one is wanted.
        static Hole Straight(params Obstacle[] obstacles) => new()
        {
            Number = 99, Par = 4,
            Centerline = new[] { new CoursePoint(0, 0), new CoursePoint(0, 400) },
            FairwayWidth = 60, GreenRadius = 12, RoughWidth = 30,
            Obstacles = obstacles,
        };

        static SwingImpact Full(double power = 1) => new() { Power = power };

        [Test]
        public void IntoTheBranchesAndDownShortOfTheTree()
        {
            var clear = new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), Straight());
            // a tall pine 30 yards out, on the line, the ball still climbing through it
            var pine = Obstacle.Tree(0, 30, 0, 22, 4, 3);
            var blocked = new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), Straight(pine));
            Assert.Greater(clear.Rest.D, 140, "unblocked it goes its distance");
            Assert.Less(blocked.Rest.D, 60, "the branches take its pace");
            Assert.Less(blocked.Rest.DistanceTo(new CoursePoint(0, 30)), 25, "and it drops near the tree");
            Assert.Less(blocked.Carry, 45);
            Assert.GreaterOrEqual(blocked.Knocks.Count, 1, "the hit is on record for the picture and the sound");
            Assert.IsFalse(blocked.Knocks[0].Hard, "into the leaves");
            Assert.AreEqual(0, clear.Knocks.Count);
        }

        [Test]
        public void AClippedCrownKeepsMostOfItsPace()
        {
            var clear = new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), Straight());
            // the ball just grazes the edge of a round crown
            var at = clear.PositionAt(0.6); double y = at.h;
            var edge = Obstacle.Tree(4.0 + 0.2, at.d, 0, y + 5, 4.2, y - 5, 0.2, false);
            var clipped = new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), Straight(edge));
            Assert.Less(clipped.Rest.D, clear.Rest.D - 5, "it lost something");
            Assert.Greater(clipped.Rest.D, 60, "but not the shot");
        }

        [Test]
        public void BackOffAWall()
        {
            // a low punch into a wall 25 yards out comes back off it
            var wall = Obstacle.Round(ObstacleKind.Wall, 0, 25, 0, 40, 3);
            var shot = new CourseShot(GolfClub.Iron, Full(0.8), 0, new CoursePoint(0, 0), Straight(wall));
            Assert.Less(shot.Rest.D, 22, "it stays this side of the wall");
            Assert.Greater(shot.Rest.D, -30);
        }

        [Test]
        public void APuttComesBackOffATrunk()
        {
            var tree = Obstacle.Tree(0, 8, 0, 10, 3, 3, 0.3);
            var shot = new CourseShot(GolfClub.Putter, Full(1), 0, new CoursePoint(0, 0), Straight(tree));
            Assert.Less(shot.Rest.D, 7.7, "it never gets past the trunk");
            Assert.IsTrue(shot.Knocks.Count >= 1 && shot.Knocks[0].Hard && double.IsNaN(shot.Knocks[0].Y), "a knock on the ground");
            var clear = new CourseShot(GolfClub.Putter, Full(1), 0, new CoursePoint(0, 0), Straight());
            Assert.Greater(clear.Rest.D, 9, "(without it, it would have)");
        }

        [Test]
        public void ARockBuriedUnderTheGreenNeverBlocksAPutt()
        {
            // Needle's green sits on a sea stack: the model's rock mass under it reads as a rock a dozen yards across
            // whose top (6.28) is below the green it holds up (6.85). A putt rolls over the grass, not into the stone.
            var stack = Obstacle.Round(ObstacleKind.Rock, 0, 6, -1.8, 6.28, 12.5);
            var hole = Straight(stack);
            hole.Ground = _ => 6.85;
            var shot = new CourseShot(GolfClub.Putter, Full(1), 0, new CoursePoint(0, 0), hole);
            var clear = new CourseShot(GolfClub.Putter, Full(1), 0, new CoursePoint(0, 0), Straight());
            Assert.AreEqual(clear.Rest.D, shot.Rest.D, 1e-9, "the ball runs exactly as it would with nothing there");
            Assert.AreEqual(0, shot.Knocks.Count, "and meets nothing");
        }

        [Test]
        public void ARockStandingAboveTheGroundStillStopsAPutt()
        {
            // the same rock with its top above the ground it stands on is a rock in the way
            var stone = Obstacle.Round(ObstacleKind.Rock, 0, 6, 6.85, 8.0, 1.2);
            var hole = Straight(stone);
            hole.Ground = _ => 6.85;
            var shot = new CourseShot(GolfClub.Putter, Full(1), 0, new CoursePoint(0, 0), hole);
            Assert.Less(shot.Rest.D, 6, "it never gets past the stone");
            Assert.GreaterOrEqual(shot.Knocks.Count, 1);
        }

        [Test]
        public void ABushCatchesARollingBall()
        {
            var bush = Obstacle.Round(ObstacleKind.Bush, 0, 6, 0, 1.2, 1.0);
            var shot = new CourseShot(GolfClub.Putter, Full(0.8), 0, new CoursePoint(0, 0), Straight(bush));
            Assert.Less(shot.Rest.D, 6.2, "it stops at the bush");
            Assert.Greater(shot.Rest.D, 3.5);
        }

        [Test]
        public void SandStopsARollingBallInAYardOrTwo()
        {
            var hole = Straight();
            hole.Hazards = new[] { new CourseHazard(HazardKind.Bunker, 0, 40, 30, 10) };   // 35 to 45 down the hole
            var shot = new CourseShot(GolfClub.Putter, Full(1), 0, new CoursePoint(0, 28), hole);
            Assert.AreEqual(CourseLie.Bunker, shot.Lie, "it ran into the sand");
            Assert.Less(shot.Rest.D, 37.5, "and stopped just inside it");
            Assert.Greater(CourseShot.RollingDeceleration(CourseLie.Bunker), 5 * CourseShot.RollingDeceleration(CourseLie.Fairway));
        }

        [Test]
        public void ClearOfEverythingTheShotIsUnchanged()
        {
            var off = Obstacle.Tree(40, 60, 0, 12, 3, 3);   // well wide of the line
            var clear = new CourseShot(GolfClub.Driver, Full(), 0, new CoursePoint(0, 0), Straight());
            var shot = new CourseShot(GolfClub.Driver, Full(), 0, new CoursePoint(0, 0), Straight(off));
            Assert.AreEqual(clear.Rest.D, shot.Rest.D, 1e-9);
            Assert.AreEqual(clear.Rest.X, shot.Rest.X, 1e-9);
        }

        // ----- The quirky movers (10-19): a timed launchpad and a sliding bullseye -----

        /// A pad on the straight hole right where a full iron comes down, its clock set so the ball arrives `cycle` of
        /// the way round (charged below Mover.ChargedShare).
        static (CourseShot clear, CourseShot shot) OnThePad(double cycle)
        {
            var clear = new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), Straight());
            double t = clear.LandingTime, period = 4;
            double phase = ((cycle - t / period) % 1 + 1) % 1;
            var hole = Straight();
            hole.Movers = new CourseMovers(new[] { Mover.Launchpad(new CoursePoint(0, clear.Landing.D), 0, new CoursePoint(0, 330), 0, period, phase) });
            return (clear, new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), hole));
        }

        [Test]
        public void AChargedPadLobsTheBallOnToTheGreen()
        {
            var (clear, shot) = OnThePad(.25);
            Assert.IsTrue(shot.Knocks.Count > 0 && shot.Knocks[0].Kind == ObstacleKind.Launchpad, "it came down on the pad");
            Assert.IsFalse(shot.Knocks[0].Hard, "a pad is a boing, not a knock");
            Assert.Greater(shot.Rest.D, clear.Rest.D + 100, "fired on, far past where it would have stopped");
            Assert.Less(shot.Rest.DistanceTo(new CoursePoint(0, 330)), 30, "to rest near the spot it was aimed at, short of the green");
            Assert.Greater(shot.Apex, 0);
        }

        [Test]
        public void ASpentPadOnlyPopsItAside()
        {
            var (clear, shot) = OnThePad(.75);
            Assert.IsTrue(shot.Knocks.Count > 0 && shot.Knocks[0].Kind == ObstacleKind.Launchpad, "it came down on the pad");
            Assert.Less(shot.Rest.D, clear.Rest.D + 12, "no lob: the timing was wrong");
            Assert.Greater(Math.Abs(shot.Rest.X - clear.Landing.X), 0.5, "it pops off to one side");
            var again = OnThePad(.75).shot;
            Assert.AreEqual(shot.Rest.X, again.Rest.X, 1e-9, "the same strike at the same time does the same thing");
            Assert.AreEqual(shot.Rest.D, again.Rest.D, 1e-9);
        }

        /// A bullseye sliding across the line 60 yards out at the height the iron passes there, placed by `cycle`
        /// (.25: in the middle of its rail as the ball gets there; 0: at the far end, 10 yards off the line).
        static (CourseShot clear, CourseShot shot) PastTheTarget(double cycle)
        {
            var clear = new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), Straight());
            double t = 0; while (clear.PositionAt(t).d < 60) t += 0.005;
            double period = 6, phase = ((cycle - t / period) % 1 + 1) % 1;
            var hole = Straight();
            hole.Movers = new CourseMovers(new[] { Mover.Target(new CoursePoint(-10, 60), new CoursePoint(10, 60), clear.PositionAt(t).h, period, phase, new CoursePoint(0, 330), 0) });
            return (clear, new CourseShot(GolfClub.Iron, Full(), 0, new CoursePoint(0, 0), hole));
        }

        [Test]
        public void HittingTheBullseyeSendsItOn()
        {
            var (clear, shot) = PastTheTarget(.25);
            Assert.IsTrue(shot.Knocks.Count > 0 && shot.Knocks[0].Kind == ObstacleKind.Target && shot.Knocks[0].Hard, "it hit the board");
            Assert.Less(shot.Rest.DistanceTo(new CoursePoint(0, 330)), 30, "and was sent on toward the green");
            Assert.Greater(shot.Rest.D, clear.Rest.D + 100, "a reward, not a block");
        }

        [Test]
        public void MissingTheTargetChangesNothing()
        {
            var (clear, shot) = PastTheTarget(0);
            Assert.AreEqual(0, shot.Knocks.Count, "the board was off at the end of its rail");
            Assert.AreEqual(clear.Rest.D, shot.Rest.D, 1e-9);
        }

        [Test]
        public void PadsAndTargetsStandOffTheLine()
        {
            int placed = 0;
            foreach (var course in Course.Course.All())
                foreach (var hole in course.Holes)
                    for (int seed = 1; seed <= 6; seed++)
                        foreach (var m in QuirkyObstacles.For(hole, seed, null, null))
                        {
                            placed++;
                            Assert.IsTrue(QuirkyObstacles.Has(hole.Number));
                            for (double t = 0; t < m.Period; t += m.Period / 12)
                            {
                                var p = m.At(t);
                                Assert.GreaterOrEqual(DreamCourseLayout.CorridorDistance(new CoursePoint(p.x, p.d), hole.Centerline), QuirkyObstacles.Clear - 1e-6, $"hole {hole.Number} {m.Kind}");
                            }
                            Assert.AreEqual(0, hole.LieAt(m.Goal).PenaltyStrokes(), "it sends the ball somewhere playable");
                            Assert.AreNotEqual(CourseLie.Water, hole.LieAt(new CoursePoint(m.RailFrom.X, m.RailFrom.D)));
                        }
            Assert.GreaterOrEqual(placed, 2 * 6, "on at least two holes");
        }

        [Test]
        public void ShapesAreTheirOwn()
        {
            var pine = Obstacle.Tree(0, 0, 0, 10, 3, 2, 0.2, cone: true);
            Assert.IsTrue(pine.Touches(0.1, 1, 0, 0.05, out bool trunk, out _)); Assert.IsTrue(trunk, "low down it's the trunk");
            Assert.IsTrue(pine.Touches(2.5, 2.5, 0, 0.05, out trunk, out _)); Assert.IsFalse(trunk, "wide low branches");
            Assert.IsFalse(pine.Touches(2.5, 9, 0, 0.05, out _, out _), "the pine narrows to its tip");
            var round = Obstacle.Tree(0, 0, 0, 10, 3, 2, 0.2, cone: false);
            Assert.IsTrue(round.Touches(2.5, 6, 0, 0.05, out _, out _), "a round crown is widest in the middle");
            var rock = Obstacle.Round(ObstacleKind.Rock, 0, 0, 0, 2, 1.5);
            Assert.IsTrue(rock.Touches(0, 1, 1.2, 0.05, out _, out _));
            Assert.IsFalse(rock.Touches(0, 2.5, 0, 0.05, out _, out _));
        }
    }
}
