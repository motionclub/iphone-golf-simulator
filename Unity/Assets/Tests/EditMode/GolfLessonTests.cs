using NUnit.Framework;
using GolfArcade.Course;
using GolfArcade.Game;

/// The golf lesson's hole and its four stations (PLAN_Onboarding_Tutorial_TennisQuickStart_1121.md: drive, approach, putting).
public class GolfLessonTests
{
    [Test] public void FourStationsInTeachingOrder()
    {
        var kinds = System.Array.ConvertAll(GolfLesson.Stations, s => s.Kind);
        Assert.AreEqual(new[] { GolfLesson.Kind.Drive, GolfLesson.Kind.Approach, GolfLesson.Kind.Putt, GolfLesson.Kind.LongPutt }, kinds);
        foreach (var s in GolfLesson.Stations)
        {
            Assert.IsNotEmpty(s.Key); Assert.IsNotEmpty(s.Title); Assert.IsNotEmpty(s.Ask); Assert.IsNotEmpty(s.Hint);
            Assert.AreEqual(0, s.Tips.Length, s.Key + ": the phone shows the title and one line, no tips");
            Assert.That(s.Title.Split(' ').Length, Is.InRange(1, 4), s.Key + ": a short title");
            Assert.That(s.Ask + s.Hint, Does.Not.Contain("!").And.Not.Contain(":"), s.Key + ": one plain sentence each");
            Assert.That(s.Ask + s.Hint, Does.Not.Contain("touch control").IgnoreCase.And.Not.Contain("SWING POWER"), "there is no touch play");
        }
    }

    [Test] public void PuttingIsExplainedFirstAndOnlyPutting()
    {
        foreach (var s in GolfLesson.Stations)
        {
            bool explains = !string.IsNullOrEmpty(s.ExplainTitle);
            Assert.AreEqual(s.Kind == GolfLesson.Kind.Putt, explains, s.Key + ": only the first putt opens on the explain card");
            if (explains)
            {
                StringAssert.Contains("sensitive", s.ExplainTitle);
                StringAssert.Contains("few inches", s.ExplainBody);
                var json = LessonJson.Station("golf", 2, 4, s.Key, s.Name, s.Title, s.Ask, s.Hint, s.Tips, s.ExplainTitle, s.ExplainBody);
                StringAssert.Contains("\"explain\":{\"title\":\"Putting is sensitive\"", json);
            }
        }
        StringAssert.DoesNotContain("explain", LessonJson.Station("golf", 0, 4, "drive", "Drive", "Tee off", "a", "b", new string[0]));
    }

    [Test] public void PassRules()
    {
        Assert.IsTrue(GolfLesson.Passes(GolfLesson.Kind.Drive, false, 180, 280, 100), "a full drive");
        Assert.IsFalse(GolfLesson.Passes(GolfLesson.Kind.Drive, false, 60, 280, 220), "a half swing is not a drive");
        Assert.IsTrue(GolfLesson.Passes(GolfLesson.Kind.Approach, false, 95, 100, 14), "carry within 12 yd");
        Assert.IsTrue(GolfLesson.Passes(GolfLesson.Kind.Approach, false, 70, 100, 8), "stopped within 10 yd");
        Assert.IsFalse(GolfLesson.Passes(GolfLesson.Kind.Approach, false, 140, 100, 40), "way long");
        Assert.IsTrue(GolfLesson.Passes(GolfLesson.Kind.Putt, true, 0, 2, 0));
        Assert.IsFalse(GolfLesson.Passes(GolfLesson.Kind.Putt, false, 0, 2, .3), "the short putt has to drop");
        Assert.IsTrue(GolfLesson.Passes(GolfLesson.Kind.LongPutt, false, 0, 6.7, .8), "a long putt inside 3 ft");
        Assert.IsFalse(GolfLesson.Passes(GolfLesson.Kind.LongPutt, false, 0, 6.7, 2), "6 ft away is not close enough");
    }

    [Test] public void TheLessonHoleIsAStraightParFourTwiceByKey()
    {
        var lesson = Course.ByKey("lesson");
        Assert.IsNotNull(lesson); Assert.AreEqual("lesson", lesson.Key); Assert.AreEqual(2, lesson.Holes.Length);
        Assert.AreEqual(8, lesson.Par);
        Assert.AreEqual(1, lesson.Holes[0].PlayNumber); Assert.AreEqual(2, lesson.Holes[1].PlayNumber);
        Assert.That(lesson.Holes[0].Tee.DistanceTo(lesson.Holes[0].Pin), Is.InRange(250, 300), "a driver from the tee");
        Assert.Greater(lesson.Holes[0].Tee.DistanceTo(lesson.Holes[0].Pin), GolfLesson.ApproachYards + GolfLesson.DriveCarry, "the drive station never reaches the green");
        Assert.IsFalse(System.Array.Exists(Course.All(), c => c.Key == "lesson"), "the lesson is not a course on the course screen");
    }
}
