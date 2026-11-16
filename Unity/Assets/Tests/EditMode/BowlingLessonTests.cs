using NUnit.Framework;
using GolfArcade.Bowling;
using GolfArcade.Hub.Menu;
using UnityEngine;

/// The bowling lesson's stations and verdicts, and the Tutorial lock's state from the phone (PLAN_Onboarding_v3_IntroTutorial.md).
public class BowlingLessonTests
{
    [Test] public void ThreeStationsInTeachingOrder()
    {
        var kinds = System.Array.ConvertAll(BowlingLessonPlan.Stations, s => s.Kind);
        Assert.AreEqual(new[] { BowlingLessonPlan.Kind.Roll, BowlingLessonPlan.Kind.Release, BowlingLessonPlan.Kind.Pins }, kinds);
        foreach (var s in BowlingLessonPlan.Stations)
        {
            Assert.IsNotEmpty(s.Key); Assert.IsNotEmpty(s.Title); Assert.IsNotEmpty(s.Ask); Assert.IsNotEmpty(s.Hint);
            Assert.AreEqual(0, s.Tips.Length, s.Key + ": the phone shows the title and one line, no tips");
            Assert.That(s.Title.Split(' ').Length, Is.InRange(1, 4), s.Key + ": a short title");
            Assert.That(s.Ask + s.Hint, Does.Not.Contain("!").And.Not.Contain(":"), s.Key + ": one plain sentence each");
        }
    }

    [Test] public void EachStationPassesOnWhatItTeaches()
    {
        var k = BowlingLessonPlan.Kind.Roll;
        Assert.IsTrue(BowlingLessonPlan.Judge(k, ReleaseGrade.Late, 3, true).pass, "any rolled ball");
        Assert.IsFalse(BowlingLessonPlan.Judge(k, ReleaseGrade.Drop, 0, true).pass, "a dropped ball is not a roll");
        Assert.IsTrue(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Release, ReleaseGrade.Good, 4, true).pass);
        Assert.IsTrue(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Release, ReleaseGrade.Perfect, 4, true).pass);
        Assert.IsFalse(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Release, ReleaseGrade.Early, 9, true).pass, "pins don't excuse an early release");
        Assert.IsTrue(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Pins, ReleaseGrade.Good, 7, true).pass);
        Assert.IsFalse(BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Pins, ReleaseGrade.Good, 6, true).pass);
        var spare = BowlingLessonPlan.Judge(BowlingLessonPlan.Kind.Pins, ReleaseGrade.Good, 3, false);
        Assert.IsFalse(spare.pass); Assert.IsFalse(spare.counts, "a spare ball is not a miss");
    }

    [Test] public void VerdictsNeverRepeatTheHudsGradeWord()
    {
        foreach (BowlingLessonPlan.Kind kind in System.Enum.GetValues(typeof(BowlingLessonPlan.Kind)))
        foreach (ReleaseGrade grade in System.Enum.GetValues(typeof(ReleaseGrade)))
        {
            string text = BowlingLessonPlan.Judge(kind, grade, 10, true).text;
            Assert.That(text, Does.Not.Contain(grade.ToString()).IgnoreCase, $"{kind} {grade}");
            Assert.That(text, Does.Not.Contain("STRIKE").IgnoreCase, $"{kind} {grade}");
        }
    }

    [Test] public void TutorialStateParsesFromThePhone()
    {
        var s = JsonUtility.FromJson<MenuHud.TutorialState>("{\"locked\":true,\"next\":\"tennis\",\"done\":[\"golf\"],\"deferred\":[]}");
        Assert.IsTrue(s.locked); Assert.AreEqual("tennis", s.next); Assert.AreEqual(new[] { "golf" }, s.done); Assert.AreEqual(0, s.deferred.Length);
    }
}
