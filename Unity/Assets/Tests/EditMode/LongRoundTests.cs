using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using NUnit.Framework;

namespace GolfArcade.Tests
{
    /// Rounds longer than a course: 9 or 18 holes from any course, going on into the courses after it ("cliffside+9")
    /// or round the same course again ("cliffside*9"). The key travels as a course key does (the app's launch, a
    /// multiplayer venue), and Course.ByKey builds the round from it.
    public class LongRoundTests
    {
        [Test]
        public void ALinkedRoundGoesOnIntoTheNextCourse()
        {
            var round = Course.Course.ByKey("cliffside+9");
            Assert.IsNotNull(round);
            CollectionAssert.AreEqual(new[] { 7, 8, 9, 12, 15, 13, 14, 17, 18 }, round.Holes.Select(h => h.Number).ToArray());
            Assert.AreEqual("cliffside+9", round.Key, "the round keeps its key, so the host and every phone agree on it");
            Assert.AreEqual("Cliffside + Wild Isles", round.Name);
            Assert.AreEqual(19 + 5 + 4 + 5 + 3, round.Par);
        }

        [Test]
        public void EighteenLinkedHolesTourEveryCourseAndComeRoundAgain()
        {
            var round = Course.Course.ByKey("wildisles+18");
            CollectionAssert.AreEqual(new[] { 13, 14, 17, 18, 19, 20, 10, 16, 21, 22, 23, 7, 8, 9, 12, 15, 13, 14 },
                round.Holes.Select(h => h.Number).ToArray(), "Wild Isles, the Magma Open, Cliffside, then Wild Isles' first two again");
            Assert.AreEqual("Grand Tour", round.Name);
        }

        [Test]
        public void AnUnlinkedRoundGoesRoundTheSameCourseAgain()
        {
            var round = Course.Course.ByKey("magma*9");
            CollectionAssert.AreEqual(new[] { 10, 16, 21, 22, 23, 10, 16, 21, 22 }, round.Holes.Select(h => h.Number).ToArray());
            Assert.AreEqual("Magma Open", round.Name);
        }

        [Test]
        public void EveryHoleOfALongRoundIsItsOwnHoleNumberedInTheRound()
        {
            var round = Course.Course.ByKey("cliffside*18");
            Assert.AreEqual(18, round.Holes.Length);
            for (int i = 0; i < round.Holes.Length; i++) Assert.AreEqual(i + 1, round.Holes[i].PlayNumber, $"hole {i + 1} of the round");
            Assert.AreEqual(round.Holes.Length, round.Holes.Distinct().Count(), "a hole played twice is two holes, each read off its model when played");
            var card = new Scorecard(round);
            card.Record(0, 4); card.Record(5, 3);
            Assert.AreEqual(7, card.Total, "the second time round is scored on its own");
        }

        [Test]
        public void TheRoundKeyIsTheCourseKeyForTheCourseOwnRound()
        {
            Assert.AreEqual("cliffside", Course.Course.RoundKey("cliffside", 0, true));
            Assert.AreEqual("cliffside", Course.Course.RoundKey("cliffside", 5, false), "five holes round Cliffside is Cliffside");
            Assert.AreEqual("cliffside+9", Course.Course.RoundKey("cliffside", 9, true));
            Assert.AreEqual("wildisles*18", Course.Course.RoundKey("wildisles", 18, false));
            Assert.AreEqual("cliffside+9", Course.Course.RoundKey("postcards", 9, true), "the retired Postcards key is Cliffside");
        }

        [Test]
        public void KeysThatAreNotRoundsAreNotCourses()
        {
            Assert.IsNull(Course.Course.ByKey("cliffside+0"));
            Assert.IsNull(Course.Course.ByKey("cliffside+99"));
            Assert.IsNull(Course.Course.ByKey("nowhere+9"));
            Assert.IsNull(Course.Course.ByKey("+9"));
            Assert.AreEqual("magma", Course.Course.ByKey("magma").Key, "a plain key is still its course");
        }

        [Test]
        public void TheGameSetupPlaysTheRoundItNames()
        {
            var course = GameSetup.CourseFor("magma+9");
            CollectionAssert.AreEqual(new[] { 10, 16, 21, 22, 23, 7, 8, 9, 12 }, course.Holes.Select(h => h.Number).ToArray(), "after the Magma Open comes Cliffside");
            Assert.AreEqual(0, GameSetup.HolesFor("magma+9"), "a round, not one hole of a course");
            Assert.AreEqual(12, GameSetup.CourseFor("cliffside-12").Holes.Single().Number, "one hole of a course still works as before");
        }
    }
}
