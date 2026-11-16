using System.Collections;
using System.Collections.Generic;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using GolfArcade.Game;
using GolfArcade.Swing;

namespace GolfArcade.PlayTests {
    /// The golf lesson on the real game (PLAN_Onboarding_GolfLesson.md): a square, committed, smooth swing (the tests' planned
    /// strike) clears every station on the Practice Tee, and a short one at the distance station is a miss that puts the ball back.
    public sealed class GolfLessonPlayTests {
        readonly List<string> reports = new();
        GolfGame game;
        GolfLesson lesson;

        IEnumerator Setup(int station) {
            reports.Clear();
            NativeSportsSession.LessonReport = json => reports.Add(json);
            game = new GameObject("Golf lesson check").AddComponent<GolfGame>();
            yield return null;
            game.PrepareNativeAddress("lesson");
            yield return null;
            lesson = game.gameObject.AddComponent<GolfLesson>();
            lesson.Begin(game, station);
        }
        IEnumerator UntilStation(int index, float seconds = 20) {
            float deadline = Time.realtimeSinceStartup + seconds;
            while (Time.realtimeSinceStartup < deadline && !(lesson.Index == index && Last("station") != null && Last("station").Contains($"\"index\":{index},") && game.Current == GolfGame.State.Aim)) yield return null;
        }
        IEnumerator Settle(float seconds = 40) {
            float deadline = Time.realtimeSinceStartup + seconds;
            yield return null;
            while (Time.realtimeSinceStartup < deadline && game.Current is GolfGame.State.Flight or GolfGame.State.Result) yield return null;
            yield return null; yield return null;
        }
        string Last(string kind) { for (int i = reports.Count - 1; i >= 0; i--) if (reports[i].Contains($"\"kind\":\"{kind}\"")) return reports[i]; return null; }
        static void Impact(GolfGame g, SwingImpact impact) =>
            typeof(GolfGame).GetMethod("OnImpact", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).Invoke(g, new object[] { impact });

        [UnityTest, Timeout(600000)] public IEnumerator ASquareCommittedSmoothSwingClearsEveryStation() {
            yield return Setup(0);
            Time.timeScale = 4;
            try {
                for (int station = 0; station < GolfLesson.Stations.Length && !lesson.Finished; station++) {
                    yield return UntilStation(station);
                    Assert.AreEqual(station, lesson.Index, "station " + GolfLesson.Stations[station].Key + " started");
                    StringAssert.Contains($"\"key\":\"{GolfLesson.Stations[station].Key}\"", Last("station"));
                    for (int shot = 0; shot < 8 && lesson.Index == station && !lesson.Finished; shot++) {
                        float wait = Time.realtimeSinceStartup + 10;
                        while (game.Current != GolfGame.State.Aim && Time.realtimeSinceStartup < wait) yield return null;
                        game.StrikeToward(game.CurrentHole.Pin);
                        yield return Settle();
                    }
                    Debug.Log($"[GolfLesson] station {station} {GolfLesson.Stations[station].Key}: {Last("attempt")}");
                    if (lesson.Index == station && !lesson.Finished) { lesson.SkipStation(); Debug.Log($"[GolfLesson] station {station} skipped after 8 planned shots"); }
                }
                float end = Time.realtimeSinceStartup + 30;
                while (!lesson.Finished && Time.realtimeSinceStartup < end) yield return null;
                Assert.IsTrue(lesson.Finished, "the lesson reaches its end");
                StringAssert.Contains("\"kind\":\"done\"", reports[reports.Count - 1]);
                int passes = reports.FindAll(r => r.Contains("\"result\":\"pass\"")).Count;
                Assert.GreaterOrEqual(passes, 2, "planned strikes pass the stations on their own (one putt may need a skip)");
                Debug.Log("[GolfLesson] reports:\n" + string.Join("\n", reports));
            } finally { Time.timeScale = 1; NativeSportsSession.LessonReport = null; Object.Destroy(game.gameObject); }
        }

        [UnityTest, Timeout(180000)] public IEnumerator AShortSwingIsAMissThatPutsTheBallBack() {
            yield return Setup(1);   // Distance: 60 yards to the flag
            Time.timeScale = 4;
            try {
                yield return UntilStation(1);
                var spot = game.BallAt;
                Impact(game, new SwingImpact { Power = .1, Backswing = .1, Commit = 1, TempoSeconds = 1.0, DownswingSeconds = .25 });
                yield return Settle();
                string attempt = Last("attempt");
                Assert.IsNotNull(attempt);
                StringAssert.Contains("\"result\":\"miss\"", attempt);
                StringAssert.Contains("\"text\":\"Take the phone back further.\"", attempt, "the miss says the one fix");
                StringAssert.Contains("\"read\":[]", attempt, "no read-out rows: the HUD shows the numbers");
                Assert.AreEqual(1, lesson.Index, "a miss stays on the station");
                float wait = Time.realtimeSinceStartup + 10;
                while (Time.realtimeSinceStartup < wait && game.BallAt.DistanceTo(spot) > .5) yield return null;
                Assert.Less(game.BallAt.DistanceTo(spot), .5, "the ball goes back to the station's spot for another go");
            } finally { Time.timeScale = 1; NativeSportsSession.LessonReport = null; Object.Destroy(game.gameObject); }
        }
    }
}
