using System.Collections;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.PlayTests
{
    /// 2026-10-12 brief: a hole's flyover shows what matters on it and ends on the green; each character gets three seconds
    /// in which their player may tap an emote — nobody emotes unless they do — and a picked emote is played out; a skip ends
    /// the flyover only; online the flyover is skipped only when everyone asks.
    public class IntroRulesPlayTests
    {
        const int FPS = 30;
        static void ClearSeen()
        {
            foreach (var key in new[] { "tennis.venue." + TennisVenue.Selected, "tennis.walkon", "tennis.start", "golf.walkon", "golf.start" })
                PlayerPrefs.DeleteKey("presentation.v" + PresentationPolicy.Revision + "." + key);
            foreach (var c in new[] { "cliffside", "wildisles", "magma" })
                for (int i = 1; i <= 30; i++) PlayerPrefs.DeleteKey("presentation.v" + PresentationPolicy.Revision + ".golf.venue." + c + "." + i);
        }
        static GolferView Golfer(GolfGame golf) => (GolferView)typeof(GolfGame).GetField("golfer", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(golf);

        [UnityTest, Timeout(240000)]
        public IEnumerator GolfSkipLandsOnTheGolferWhoEmotesOnlyWhenTheirPlayerPicks()
        {
            Time.timeScale = 1; Time.captureFramerate = FPS; ClearSeen();
            PresentationPolicy.Configure("full", false, true, false);
            try
            {
                yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
                var golf = Object.FindFirstObjectByType<GolfGame>();
                golf.EquipResultEmotes(new[] { "wave", "pushups", "bringIt" });

                // no pick: the golfer stands through their three seconds, no emote
                golf.PrepareNativeAddress(); golf.NativeReady(); golf.TryNativePresentation();
                Assert.AreEqual(0, golf.PresentationBeatIndex, "the opening starts on the flyover");
                Assert.AreEqual(HoleIntro.Length(true), golf.PresentationDuration, .01f, "the full flyover: the opening and three highlights");
                Assert.AreEqual("0|1|0", golf.IntroSkipState, "the flyover can be skipped");
                for (int f = 0; f < FPS; f++) yield return null;
                golf.NativeContinue(); yield return null;
                Assert.AreEqual(1, golf.PresentationBeatIndex, "skip lands on the golfer's introduction, not past it");
                Assert.AreEqual("", golf.IntroSkipState, "nothing more to skip: the introduction always plays");
                var view = Golfer(golf); float intro = 0;
                for (int f = 0; f < 12 * FPS && golf.PresentationBeatIndex == 1; f++)
                {
                    yield return null; intro += 1f / FPS;
                    Assert.False(view.Performing != null && (view.Performing.StartsWith("Intro_") || view.Performing.StartsWith("Emote_")), "no emote unless one is picked: " + view.Performing);
                }
                Assert.AreEqual(PresentationDirector.GolfOverShoulder + PresentationDirector.IntroWindow, intro, .1f, "over the shoulder, then three seconds");

                // a pick during the flyover: played as the golfer turns to the camera, and played out
                ClearSeen(); golf.PrepareNativeAddress(); golf.NativeReady(); golf.TryNativePresentation();
                for (int f = 0; f < FPS; f++) yield return null;
                Assert.AreEqual("intro", golf.IntroEmoteWindow, "the emote can be picked during the flyover");
                Assert.True(golf.PlayResultEmote(1), "the phone's emote button picks the intro emote");
                Assert.AreEqual("", golf.IntroEmoteWindow, "once a hole");
                golf.NativeContinue(); yield return null;
                bool played = false; intro = 0;
                for (int f = 0; f < 12 * FPS && golf.PresentationBeatIndex == 1; f++)
                {
                    if (f == FPS * 2) golf.NativeContinue();   // another skip during the introduction changes nothing
                    yield return null; intro += 1f / FPS;
                    played |= view.Performing == "Intro_Pushups" || !view.HasMove("Intro_Pushups") && view.Performing == "Wave";
                }
                Assert.True(played, "the picked emote plays on the tee");
                float pushups = view.MoveLength("Intro_Pushups");
                Assert.GreaterOrEqual(intro + .05f, Mathf.Max(PresentationDirector.GolfOverShoulder + PresentationDirector.IntroWindow, PresentationDirector.GolfOverShoulder + pushups), "the emote is played out");
            }
            finally { Time.captureFramerate = 0; PresentationPolicy.Configure("full", false, true, false); }
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator GolfFlyoverShowsWhatMattersAndEndsOnTheGreen()
        {
            Time.timeScale = 1; Time.captureFramerate = FPS;
            PresentationPolicy.Configure("full", false, true, false);
            try
            {
                yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
                var golf = Object.FindFirstObjectByType<GolfGame>();
                foreach (var course in new[] { "cliffside", "wildisles", "magma" })
                {
                    ClearSeen();
                    golf.PrepareNativeAddress(course); golf.NativeReady(); golf.TryNativePresentation();
                    var highlights = golf.IntroHighlights;
                    Assert.AreEqual(3, highlights.Count, course + ": two highlights and the green");
                    Assert.AreEqual("green", highlights[2].Kind, course + ": the green last");
                    Assert.AreNotEqual("green", highlights[0].Kind); Assert.AreNotEqual("green", highlights[1].Kind);
                    var camera = Camera.main; float seconds = 0, nearestPin = float.MaxValue;
                    var pin = GolfArcade.Course.HoleView.ToWorld(golf.CurrentHole.Pin);
                    for (int f = 0; f < 20 * FPS && golf.PresentationBeatIndex == 0; f++)
                    {
                        yield return null; seconds += 1f / FPS;
                        var at = camera.transform.position;
                        Assert.True(float.IsFinite(at.x) && float.IsFinite(at.y) && float.IsFinite(at.z), course + " camera position");
                        double ground = GolfArcade.Course.HoleView.GroundHeight(GolfArcade.Course.HoleView.ToCourse(at));
                        Assert.Greater(at.y, ground + .8f, $"{course}: the camera stays above the ground at {seconds:F2} s");
                        nearestPin = Mathf.Min(nearestPin, Vector3.Distance(at, pin));
                    }
                    Assert.AreEqual(HoleIntro.Length(true), seconds, .1f, course + ": the flyover runs its time");
                    Assert.Less(nearestPin, 25f, course + ": and ends at the green");
                    Debug.Log($"[IntroRules] {course}: {highlights[0].Label}, {highlights[1].Label}, {highlights[2].Label}");
                    for (int f = 0; f < 15 * FPS && golf.Current == GolfGame.State.Intro; f++) yield return null;
                }
            }
            finally { Time.captureFramerate = 0; PresentationPolicy.Configure("full", false, true, false); }
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator TennisShowRunsSixSecondsAndOnePlayersSkipEndsIt()
        {
            Time.timeScale = 1; Time.captureFramerate = FPS; ClearSeen();
            PresentationPolicy.Configure("full", false, true, false);
            try
            {
                yield return SceneManager.LoadSceneAsync("Tennis");
                var game = Object.FindFirstObjectByType<TennisGame>();
                for (int i = 0; i < 120 && !game.Initialized; i++) yield return null;
                game.NativeControlled = true; game.AutoPlay = false; game.ManualSimulation = false; game.Drill = false;
                var intro = game.GetComponent<TennisPresentation>();
                var mine = game.Player.GetComponentInChildren<HeroTennisDriver>(); var theirs = game.Opponent.GetComponentInChildren<HeroTennisDriver>();

                // left alone, no picks: the whole show in six seconds (12.9 s until 2026-11-11), nobody emotes
                intro.Restart();
                int mineBefore = mine.EmotesPlayed, theirsBefore = theirs.EmotesPlayed;
                float shown = 0; bool sawIntroductions = false;
                for (int f = 0; f < 25 * FPS && game.IntroPlaying; f++) { yield return null; shown += 1f / FPS; sawIntroductions |= intro.Skippable && !intro.InFlyover; }
                Assert.AreEqual(mineBefore, mine.EmotesPlayed, "you did not pick: you do not emote");
                Assert.AreEqual(theirsBefore, theirs.EmotesPlayed, "nobody picked for the rival: they do not emote");
                Assert.True(sawIntroductions, "the players are still introduced");
                Assert.LessOrEqual(shown, 6.3f, "the show runs six seconds");
                Assert.GreaterOrEqual(shown, TennisPresentation.FullLength - .3f, "and is not cut short");

                // a pick during the flyover: played in your introduction (it gets its time on top)
                ClearSeen(); intro.Restart(); mineBefore = mine.EmotesPlayed;
                for (int f = 0; f < FPS / 2; f++) yield return null;
                Assert.AreEqual("intro", game.EmoteWindow, "the intro emote can be picked during the flyover");
                Assert.True(game.RequestEquippedEmote(2), "the phone's emote button picks the intro emote");
                for (int f = 0; f < 30 * FPS && game.IntroPlaying; f++) yield return null;
                Assert.AreEqual(mineBefore + 1, mine.EmotesPlayed, "the picked emote played");

                // alone: a swing skips straight to the call of play (before, it ended the flyover only)
                ClearSeen(); intro.Restart();
                for (int f = 0; f < FPS / 2; f++) yield return null;
                Assert.AreEqual("0|1|0", game.IntroSkipState, "the phone offers the skip");
                game.RequestSwing(.8f); yield return null;
                Assert.False(intro.Skippable, "one swing ends the flyover and the introductions");
                Assert.AreEqual("", game.IntroSkipState);
                shown = 0;
                for (int f = 0; f < 5 * FPS && game.IntroPlaying; f++) { yield return null; shown += 1f / FPS; }
                Assert.LessOrEqual(shown, PresentationDirector.TennisSwoop + .3f, "only the swoop into play is left");

                // versus: this phone's skip alone ends it here ...
                typeof(TennisGame).GetProperty("Versus").GetSetMethod(true).Invoke(game, new object[] { true });
                ClearSeen(); intro.Restart();
                for (int f = 0; f < FPS / 2; f++) yield return null;
                Assert.AreEqual("0|1|0", game.IntroSkipState, "one ask is enough in versus too");
                game.RequestSwing(.8f); yield return null;
                Assert.False(intro.Skippable, "this phone asked: the show ends (both had to ask until 2026-11-11)");
                // ... and the other phone's skip ends it here without a swing (a stale one from an earlier intro does not)
                for (int f = 0; f < 3 * FPS && game.IntroPlaying; f++) yield return null;
                ClearSeen(); intro.Restart();
                for (int f = 0; f < FPS / 2; f++) yield return null;
                int round = (int)typeof(TennisPresentation).GetField("introRound", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(intro);
                intro.RemoteSkip(round - 1); yield return null;
                Assert.True(intro.Skippable, "a skip left over from the last intro changes nothing");
                intro.RemoteSkip(round); yield return null;
                Assert.False(intro.Skippable, "the other phone asked: the show ends here too");
            }
            finally
            {
                var game = Object.FindFirstObjectByType<TennisGame>();
                if (game) typeof(TennisGame).GetProperty("Versus").GetSetMethod(true).Invoke(game, new object[] { false });
                Time.captureFramerate = 0; PresentationPolicy.Configure("full", false, true, false);
            }
        }
    }
}
