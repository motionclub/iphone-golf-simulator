using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using NUnit.Framework;

namespace GolfArcade.Tests
{
    /// The Daily Hole in One's generator (Game/DailyHoleInOne.cs): the same holes, cups and spawns for everyone on a day (the date is
    /// the only input), new ones the next day, every spawn 125–175 ft from the cup on a fair lie, every cup on its green, the score
    /// curve the phone also uses, and ordinary rounds' pins untouched.
    public class DailyHoleInOneTests
    {
        static readonly int[] Days = Enumerable.Range(0, 365).Select(i => System.DateTime.SpecifyKind(new System.DateTime(2026, 11, 1).AddDays(i), System.DateTimeKind.Utc))
            .Select(d => DailyHoleInOne.Today(d)).ToArray();

        [Test]
        public void ScoreCurve()
        {
            Assert.AreEqual(1000, DailyHoleInOne.Score(0, true));
            Assert.AreEqual(800, DailyHoleInOne.Score(0, false), "the best miss is 800");
            Assert.AreEqual(758, DailyHoleInOne.Score(5, false));   // = DailyHoleInOneTests.swift
            Assert.AreEqual(741, DailyHoleInOne.Score(7, false));
            Assert.AreEqual(717, DailyHoleInOne.Score(10, false));
            Assert.AreEqual(280, DailyHoleInOne.Score(75, false));
            Assert.AreEqual(2, DailyHoleInOne.Score(149, false));
            Assert.AreEqual(0, DailyHoleInOne.Score(150, false));
            Assert.AreEqual(0, DailyHoleInOne.Score(-1, false), "in a hazard");
            // every foot counts: each foot closer is worth at least 2 more, all the way out
            for (int f = 0; f < 150; f++) Assert.GreaterOrEqual(DailyHoleInOne.Score(f, false) - DailyHoleInOne.Score(f + 1, false), 2, $"{f} ft vs {f + 1} ft");
            for (double f = 0; f < 150; f += .1) Assert.GreaterOrEqual(DailyHoleInOne.Score(f, false), DailyHoleInOne.Score(f + .1, false));
        }

        [Test]
        public void TheDayIsTheOnlyInput()
        {
            foreach (int day in Days)
            {
                var a = DailyHoleInOne.CourseFor(day); var b = DailyHoleInOne.CourseFor(day);
                Assert.AreEqual(DailyHoleInOne.Shots, a.Holes.Length);
                for (int i = 0; i < a.Holes.Length; i++)
                {
                    Assert.AreEqual(a.Holes[i].Number, b.Holes[i].Number, $"{day}: hole {i}");
                    Assert.AreEqual(a.Holes[i].Pin.X, b.Holes[i].Pin.X, 0, $"{day}: cup {i}");
                    Assert.AreEqual(a.Holes[i].Pin.D, b.Holes[i].Pin.D, 0, $"{day}: cup {i}");
                    var sa = DailyHoleInOne.StartFor(day, i, a.Holes[i]); var sb = DailyHoleInOne.StartFor(day, i, b.Holes[i]);
                    Assert.AreEqual(sa.X, sb.X, 0, $"{day}: spawn {i}"); Assert.AreEqual(sa.D, sb.D, 0, $"{day}: spawn {i}");
                }
                Assert.AreEqual(a.Holes.Length, a.Holes.Select(h => h.Number).Distinct().Count(), $"{day}: three different holes");
            }
        }

        [Test]
        public void EachDayIsNew()
        {
            var lineups = Days.Select(d => string.Join(",", DailyHoleInOne.CourseFor(d).Holes.Select(h => h.Number))).ToArray();
            Assert.Greater(lineups.Distinct().Count(), Days.Length * 3 / 4, "the holes change from day to day");
            // the same hole on two days gets its cup cut in different places
            var cups = Days.SelectMany(d => DailyHoleInOne.CourseFor(d).Holes).GroupBy(h => h.Number)
                .Where(g => g.Count() > 1).Select(g => g.Select(h => $"{h.CupOffset.X:F2},{h.CupOffset.D:F2}").Distinct().Count());
            Assert.IsTrue(cups.All(n => n > 1), "pins move about the green");
        }

        [Test]
        public void SpawnsAreMakeable()
        {
            int fairway = 0, total = 0;
            foreach (int day in Days)
            {
                var course = DailyHoleInOne.CourseFor(day);
                for (int i = 0; i < course.Holes.Length; i++)
                {
                    var hole = course.Holes[i];
                    // the cup: on the green, within 9 yd of its middle, the green itself where it always was
                    Assert.AreEqual(CourseLie.Green, hole.LieAt(hole.Pin), $"{day} hole {hole.Number}: cup on the green");
                    Assert.LessOrEqual(hole.Pin.DistanceTo(hole.GreenCenter), 9.0001);
                    Assert.AreEqual(CourseLie.Green, hole.LieAt(hole.GreenCenter));
                    var start = DailyHoleInOne.StartFor(day, i, hole);
                    double feet = start.DistanceTo(hole.Pin) * 3;
                    Assert.That(feet, Is.InRange(125 - 1e-6, 175 + 1e-6), $"{day} hole {hole.Number}: {feet:F1} ft");
                    var lie = hole.LieAt(start);
                    Assert.IsTrue(lie == CourseLie.Fairway || lie == CourseLie.Rough || lie == CourseLie.Tee, $"{day} hole {hole.Number}: lie {lie}");
                    Assert.IsNull(hole.HazardAt(start));
                    total++; if (lie != CourseLie.Rough) fairway++;
                }
            }
            Assert.Greater(fairway, total * 3 / 4, "mostly from the fairway");
        }

        [Test]
        public void OrdinaryRoundsKeepTheirPin()
        {
            foreach (var c in Course.Course.All())
                foreach (var h in c.Holes)
                {
                    Assert.AreEqual(0, h.CupOffset.X); Assert.AreEqual(0, h.CupOffset.D);
                    Assert.AreEqual(h.Centerline[h.Centerline.Length - 1].X, h.Pin.X); Assert.AreEqual(h.Centerline[h.Centerline.Length - 1].D, h.Pin.D);
                }
        }

        /// The Daily Challenge's own loading tips: short enough for the card, and none said twice.
        [Test]
        public void DailyTipsFitTheirCard()
        {
            var seen = new System.Collections.Generic.HashSet<string>();
            Assert.GreaterOrEqual(GolfGame.DailyTips.Length, 4);
            foreach (var (title, text) in GolfGame.DailyTips)
            {
                Assert.That(title.Length, Is.InRange(4, 24), title);
                Assert.That(text.Length, Is.InRange(20, 130), text);
                Assert.IsTrue(seen.Add(text), "said twice: " + text);
            }
            Assert.Greater(GolfGame.DailyIntroSeconds, 2f); Assert.Less(GolfGame.DailyIntroSeconds, 4f, "an opening, not a wait");
        }

        [Test]
        public void BoardParses()
        {
            var b = HoleInOneBoard.Parse("{\"day\":20261115,\"played\":true,\"total\":2337,\"shots\":[1000,640,697],\"feet\":[0,11.6,10],\"state\":\"live\",\"note\":\"\",\"rank\":13,\"players\":100,\"percentile\":88,\"top\":13,\"hours\":5,\"minutes\":7,\"entries\":[{\"rank\":1,\"name\":\"Ann\",\"score\":2900,\"me\":false}]}");
            Assert.IsNotNull(b); Assert.IsTrue(b.Ranked); Assert.AreEqual(2337, b.total); Assert.AreEqual(3, b.shots.Length); Assert.AreEqual(11.6f, b.feet[1], 1e-4);
            Assert.AreEqual("Ann", b.entries[0].name);
            Assert.IsNull(HoleInOneBoard.Parse(""));
        }
    }
}
