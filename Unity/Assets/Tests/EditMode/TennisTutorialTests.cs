using NUnit.Framework;
using GolfArcade.Tennis;

/// The first-time tennis lesson: every step, in order, and nobody gets stuck.
public class TennisTutorialTests
{
    [Test] public void CalibrationCountsEverySwingOnADelayedDisplay()
    {
        var calibration = new TennisBeatCalibration(0);
        for (int beat = 0; beat < TennisBeatCalibration.Beats; beat++)
        {
            float time = calibration.BeatTime(beat) + .48f;
            Assert.AreEqual(beat, calibration.Swing(time));
            Assert.AreEqual(-1, calibration.Swing(time + .02f), "one count per bounce");
        }
        Assert.AreEqual(TennisBeatCalibration.Beats - TennisBeatCalibration.WarmUp, calibration.Scored);
        Assert.IsTrue(calibration.TryResult(out _));
    }

    [Test] public void TheLessonTeachesEachSkillInOrder()
    {
        var kinds = System.Array.ConvertAll(TutorialLesson.Steps, s => s.Kind);
        Assert.AreEqual(new[] { TutorialLesson.Kind.Forehand, TutorialLesson.Kind.Pace, TutorialLesson.Kind.Backhand, TutorialLesson.Kind.Aim,
            TutorialLesson.Kind.Serve, TutorialLesson.Kind.Dive, TutorialLesson.Kind.Point }, kinds);
        Assert.AreEqual(2, TutorialLesson.Steps[0].Goal, "two forehands back");
        Assert.AreEqual(2, TutorialLesson.Steps[3].Goal, "aim: the left ring, then the right");
        Assert.AreEqual(8, TutorialLesson.Steps.Length + TutorialLesson.PhoneStations, "the phone's court setup makes eight stations");
        foreach (var s in TutorialLesson.Steps)
        {
            Assert.IsNotEmpty(s.Say); Assert.IsNotEmpty(s.Hint); Assert.IsNotEmpty(s.Title); Assert.IsNotEmpty(s.Key);
            Assert.AreEqual(3, s.Tips.Length, s.Key); Assert.Greater(s.Goal, 0);
            Assert.That(s.Say + s.Hint, Does.Not.Contain("touch control").IgnoreCase.And.Not.Contain("aim pad").IgnoreCase, "there is no touch play");
        }
    }

    [Test] public void SuccessesCompleteAStepAndTheLesson()
    {
        var lesson = new TutorialLesson();
        int successes = 0;
        while (!lesson.Done) { lesson.Success(); successes++; Assert.Less(successes, 100); }
        int goal = 0; foreach (var s in TutorialLesson.Steps) goal += s.Goal;
        Assert.AreEqual(goal, successes);
    }

    [Test] public void MissesCoachAndRetryInsteadOfSilentlyPassing()
    {
        var lesson = new TutorialLesson();
        lesson.Miss(); Assert.IsFalse(lesson.HintDue);
        for (int i = 0; i < 20; i++) Assert.IsFalse(lesson.Miss());
        Assert.IsTrue(lesson.HintDue, "the hint comes after two misses");
        Assert.AreEqual(TutorialLesson.Kind.Forehand, lesson.Current.Kind);
        Assert.AreEqual(0, lesson.Progress);
        lesson.Success(); Assert.AreEqual(TutorialLesson.Kind.Forehand, lesson.Current.Kind, "one of two");
        lesson.Success(); Assert.AreEqual(TutorialLesson.Kind.Pace, lesson.Current.Kind);
        Assert.AreEqual(0, lesson.Misses);
    }

    [Test] public void SkipAdvancesExactlyOneStationAndResumeClamps()
    {
        var lesson = new TutorialLesson(3);
        Assert.AreEqual(TutorialLesson.Kind.Aim, lesson.Current.Kind);
        lesson.Skip(); Assert.AreEqual(4, lesson.Index); Assert.AreEqual(TutorialLesson.Kind.Serve, lesson.Current.Kind);
        Assert.AreEqual(0, new TutorialLesson(-100).Index);
        Assert.AreEqual(TutorialLesson.Steps.Length - 1, new TutorialLesson(100).Index);
    }

    [Test] public void LessonReportsAreValidJson()
    {
        var s = TutorialLesson.Steps[1];
        string station = GolfArcade.Game.LessonJson.Station("tennis", 2, 8, s.Key, s.Name, s.Title, s.Say, "He said \"go\"", s.Tips);
        Assert.That(station, Does.StartWith("{\"kind\":\"station\"")); Assert.That(station, Does.Contain("\\\"go\\\""));
        string attempt = GolfArcade.Game.LessonJson.Attempt(false, "OK", "EARLY.", 2, new System.Collections.Generic.List<(string, string, int)> { ("TIMING", "EARLY 220 ms", 0) });
        Assert.AreEqual("{\"kind\":\"attempt\",\"result\":\"miss\",\"grade\":\"OK\",\"text\":\"EARLY.\",\"misses\":2,\"read\":[[\"TIMING\",\"EARLY 220 ms\",0]]}", attempt);
        Assert.AreEqual("{\"kind\":\"done\",\"sport\":\"tennis\"}", GolfArcade.Game.LessonJson.Done("tennis"));
    }

    [Test] public void KitColoursParseFromTheLaunchMessage()
    {
        var kit = TennisLook.Kit.From("FF0000", "", null, "1E2A6E", 2);
        Assert.AreEqual(1f, kit.Shirt.r, 1e-3); Assert.AreEqual(1f, kit.Shirt.a);
        Assert.AreEqual(0f, kit.Shorts.a, "empty keeps the kit's own colour");
        Assert.IsTrue(kit.Any);
        Assert.IsFalse(new TennisLook.Kit { Skin = 2 }.Any, "no skin or kit override keeps the authored look");
        var defaultSkin = TennisLook.Kit.From("", "", "", "", 2);
        Assert.IsTrue(defaultSkin.HasSkin);
        Assert.IsTrue(defaultSkin.Any, "an explicit default skin tone still overrides another player\'s skin");
        Assert.IsTrue(TennisLook.Kit.From("", "", "", "", 4).Any, "a different skin tone recolours");
    }
}
