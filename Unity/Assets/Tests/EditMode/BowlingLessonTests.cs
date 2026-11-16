using NUnit.Framework;
using GolfArcade.Bowling;
using GolfArcade.Hub.Menu;
using UnityEngine;

/// The bowling lesson's stations and verdicts, and the Tutorial lock's state from the phone (PLAN_Onboarding_v3_IntroTutorial.md).
public class BowlingLessonTests
{
    [Test] public void FiveStationsInTeachingOrder()
    {
        var kinds = System.Array.ConvertAll(BowlingLessonPlan.Stations, s => s.Kind);
        Assert.AreEqual(new[] { BowlingLessonPlan.Kind.Roll, BowlingLessonPlan.Kind.Release, BowlingLessonPlan.Kind.Line, BowlingLessonPlan.Kind.Spin, BowlingLessonPlan.Kind.Pins }, kinds);
        foreach (var s in BowlingLessonPlan.Stations)
        {
            Assert.IsNotEmpty(s.Key); Assert.IsNotEmpty(s.Title); Assert.IsNotEmpty(s.Ask); Assert.IsNotEmpty(s.Hint);
            Assert.AreEqual(3, s.Tips.Length, s.Key);
        }
    }

    [Test] public void EachStationPassesOnWhatItTeaches()
    {
        var k = BowlingLessonPlan.Kind.Roll;
        Assert.IsTrue(BowlingLessonPlan.Judge(k, ReleaseGrade.Late, 20, 0, 3, true).pass, "any rolled ball");
        Assert.IsFalse(BowlingLessonPlan.Judge(k, ReleaseGrade.Drop, 20, 0, 0, true).pass, "a dropped ball is not a roll");
        Assert.IsTrue(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Release, ReleaseGrade.Good, 20, 0, 4, true).pass);
        Assert.IsFalse(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Release, ReleaseGrade.Early, 20, 0, 9, true).pass, "pins don't excuse an early release");
        Assert.IsTrue(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Line, ReleaseGrade.Late, 15, 0, 2, true).pass);
        Assert.IsFalse(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Line, ReleaseGrade.Perfect, 21, 0, 10, true).pass, "the middle is not a new spot");
        Assert.IsTrue(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Spin, ReleaseGrade.Good, 20, -15, 5, true).pass, "either way counts");
        Assert.IsFalse(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Spin, ReleaseGrade.Good, 20, 4, 5, true).pass);
        Assert.IsTrue(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Pins, ReleaseGrade.Good, 20, 0, 7, true).pass);
        var spare = BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Pins, ReleaseGrade.Good, 20, 0, 3, false);
        Assert.IsFalse(spare.pass); Assert.IsFalse(spare.counts, "a spare ball is not a miss");
    }

    [Test] public void TutorialStateParsesFromThePhone()
    {
        var s = JsonUtility.FromJson<MenuHud.TutorialState>("{\"locked\":true,\"next\":\"tennis\",\"done\":[\"golf\"],\"deferred\":[]}");
        Assert.IsTrue(s.locked); Assert.AreEqual("tennis", s.next); Assert.AreEqual(new[] { "golf" }, s.done); Assert.AreEqual(0, s.deferred.Length);
    }
}
