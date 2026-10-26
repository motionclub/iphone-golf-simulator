using NUnit.Framework;
using GolfArcade.Course;
using GolfArcade.Game;

/// The golf lesson's Practice Tee and its eight stations (PLAN_Onboarding_GolfLesson.md).
public class GolfLessonTests
{
    [Test] public void EightStationsInTeachingOrder()
    {
        var kinds = System.Array.ConvertAll(GolfLesson.Stations, s => s.Kind);
        Assert.AreEqual(new[] { GolfLesson.Kind.Swing, GolfLesson.Kind.Distance, GolfLesson.Kind.Commit, GolfLesson.Kind.Face,
            GolfLesson.Kind.Tempo, GolfLesson.Kind.Aim, GolfLesson.Kind.Putt, GolfLesson.Kind.Hole }, kinds);
        foreach (var s in GolfLesson.Stations)
        {
            Assert.IsNotEmpty(s.Key); Assert.IsNotEmpty(s.Title); Assert.IsNotEmpty(s.Ask); Assert.IsNotEmpty(s.Hint);
            Assert.AreEqual(3, s.Tips.Length, s.Key);
            Assert.That(s.Ask + s.Hint, Does.Not.Contain("touch control").IgnoreCase.And.Not.Contain("SWING POWER"), "there is no touch play");
        }
    }

    [Test] public void ThePracticeTeeIsTwoShortParThreesByKey()
    {
        var lesson = Course.ByKey("lesson");
        Assert.IsNotNull(lesson); Assert.AreEqual("lesson", lesson.Key); Assert.AreEqual(2, lesson.Holes.Length);
        Assert.AreEqual(6, lesson.Par);
        Assert.AreEqual(1, lesson.Holes[0].PlayNumber); Assert.AreEqual(2, lesson.Holes[1].PlayNumber);
        Assert.AreEqual(115, lesson.Holes[0].Tee.DistanceTo(lesson.Holes[0].Pin), 1);
        Assert.IsFalse(System.Array.Exists(Course.All(), c => c.Key == "lesson"), "the lesson is not a course on the course screen");
    }
}
