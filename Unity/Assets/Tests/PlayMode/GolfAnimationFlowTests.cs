using System.Collections;
using System.Reflection;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    public class GolfAnimationFlowTests
    {
        [UnityTest, Timeout(240000)]
        public IEnumerator RoutineResultsAdvancePromptlyButChosenEmotesFinish()
        {
            int captureRate = Time.captureFramerate;
            Time.captureFramerate = 60;
            try
            {
                yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
                var game = Object.FindFirstObjectByType<GolfGame>(); game.InstantReplays = false;
                game.PrepareNativeAddress(); game.JumpToHole(7); game.DropBall(game.CurrentHole.Tee);
                yield return null; yield return null;
                game.NativeReady(); Random.InitState(902); game.NativeSwing(.78f);
                for (int frame = 0; game.Current == GolfGame.State.Flight && frame < 2400; frame++) yield return null;
                Assert.That(game.ShowingShotResult, Is.True);
                Assert.That(game.LastShot.IsHoled, Is.False);
                Assert.That(game.ResultWaitSeconds, Is.LessThan(1));
                var golfer = (GolferView)typeof(GolfGame).GetField("golfer", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(game);
                game.EquipResultEmotes(new[] { "pushups", "scuba", "spike" });
                for (int choice = 0; choice < 3; choice++)
                {
                    Assert.That(game.PlayResultEmote(choice), Is.True);
                    float length = golfer.PerformanceDuration;
                    Assert.That(length, Is.InRange(2f, 3.6f));
                    for (int frame = 0; frame < Mathf.CeilToInt((length + .2f) * 60); frame++)
                    {
                        yield return null;
                        Assert.That(game.ShowingShotResult, Is.True, "The result must hold for a voluntary emote.");
                    }
                    Assert.That(golfer.Performing, Is.EqualTo("Idle"));
                }
                for (int i = 0; i < 90 && game.ShowingShotResult; i++) yield return null;
                Assert.That(game.ShowingShotResult, Is.False);
                Assert.That(game.Current, Is.EqualTo(GolfGame.State.Aim));
            }
            finally { Time.captureFramerate = captureRate; }
        }
    }
}
