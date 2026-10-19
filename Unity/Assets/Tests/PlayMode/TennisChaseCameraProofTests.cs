using System.Collections;
using System.IO;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    public class TennisChaseCameraProofTests
    {
        const BindingFlags Flags = BindingFlags.Instance | BindingFlags.NonPublic;
        static string Out => System.Environment.GetEnvironmentVariable("CHASE_CAMERA_OUT") ?? "Library/Captures/chase-camera";
        [UnityTest, Timeout(600000)] public IEnumerator ServeRallyLobAndVolley()
        {
            TennisVenue.Selected = TennisVenueKind.Resort;
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.ManualSimulation = true; game.NativeControlled = true; TennisGame.InstantReplayEnabled = false;
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            game.ElevatedCamera = false;
            int oldRate = Time.captureFramerate; Time.captureFramerate = 60;
            var log = new System.Text.StringBuilder("Real Unity gameplay rendering; deterministic shot fixtures; unchanged animation sources.\n");
            Directory.CreateDirectory(Out);
            try {
                game.StartPlayerServe();
                for (int i=0; i<360; i++) game.Step(1f/120);
                for (int i=0; i<45; i++) yield return null;
                game.Toss(1);
                for(int i=0; i<200 && game.Flow != TennisGame.Phase.PlayerServeToss; i++) { game.Step(1f/120); yield return null; }
                Assert.AreEqual(TennisGame.Phase.PlayerServeToss, game.Flow);
                for(int i=0; i<60; i++) { game.Step(1f/120); yield return null; }
                Capture("serve", game, log);

                game.PrepareLesson();
                game.Player.transform.position = new Vector3(0, .035f, -11.2f);
                game.Player.Prepare(.6f, false);
                var rallyFrom = new Vector3(.95f, 1.35f, -5f);
                game.InjectBall(rallyFrom, TennisRules.RallyVelocity(rallyFrom, new Vector3(.95f, TennisRules.BallRadius, -9f), 12f, 0, .75f));
                game.Player.Tick(.2f, 0);
                for(int i=0; i<60; i++) yield return null;
                Capture("baseline-rally", game, log);
                AssertLandingClear(game);

                game.PrepareLesson();
                game.Player.transform.position = new Vector3(0, .035f, -11.2f);
                game.Player.Prepare(.35f, false);
                var from = new Vector3(.95f, 1.2f, 10);
                game.InjectBall(from, TennisAbilities.LobVelocity(from, new Vector3(.95f, TennisRules.BallRadius, -10), 8));
                // Advance real ball physics to the high part of the lob; the match camera tracks every sample.
                float maxCameraStep = 0;
                for(int i=0; i<145; i++) {
                    var before = game.GameplayCamera.transform.position;
                    game.Step(1f/120); yield return null;
                    maxCameraStep = Mathf.Max(maxCameraStep, Vector3.Distance(before, game.GameplayCamera.transform.position));
                    var visible = game.GameplayCamera.WorldToViewportPoint(game.BallPosition);
                    Assert.That(visible.y, Is.InRange(.025f,.98f), "Moving lob stays on screen while camera eases");
                }
                Assert.Less(maxCameraStep, .4f, "Chase camera eases without a cut during the lob");
                log.AppendLine($"Moving lob maximum camera step at 60 fps: {maxCameraStep:F4} m");
                Assert.Greater(game.BallPosition.y, 6);
                Capture("lob", game, log);
                AssertLandingClear(game);

                game.PrepareLesson();
                game.Player.transform.position = new Vector3(0, .035f, -2.2f);
                var volleyFrom = new Vector3(.95f, 1.3f, -1f);
                game.InjectBall(volleyFrom, TennisRules.RallyVelocity(volleyFrom, new Vector3(.95f, TennisRules.BallRadius, -3f), 10f, 0, .75f));
                game.Player.Swing(.45f, false, TennisActor.Stroke.Volley);
                game.Player.Tick(.12f, 0);
                for(int i=0; i<60; i++) yield return null;
                Capture("net-volley", game, log);
                AssertLandingClear(game);
                // All ordinary phases retain the same lens; no receiver/result camera cut.
                var flow = typeof(TennisGame).GetProperty("Flow");
                foreach (TennisGame.Phase phase in System.Enum.GetValues(typeof(TennisGame.Phase))) {
                    flow.SetValue(game, phase);
                    typeof(TennisGame).GetMethod("UpdateCamera", Flags).Invoke(game, new object[]{true});
                    Assert.AreEqual(46, game.GameplayCamera.fieldOfView, phase.ToString());
                    Assert.Less(game.GameplayCamera.transform.position.z, game.Player.transform.position.z-3.4f);
                }
                // Settings fallback restores the former court height and distance in the actual game.
                game.ElevatedCamera = true;
                typeof(TennisGame).GetMethod("UpdateCamera", Flags).Invoke(game, new object[]{true});
                Assert.AreEqual(7, game.GameplayCamera.transform.position.y);
                Assert.That(game.Player.transform.position.z-game.GameplayCamera.transform.position.z, Is.EqualTo(7.8f).Within(.001f));
                File.WriteAllText(Path.Combine(Out,"camera-proof.txt"), log.ToString());
            } finally { Time.captureFramerate = oldRate; }
        }

        [UnityTest, Timeout(180000)] public IEnumerator BothSplitLayoutsChaseFromEachPlayersEnd()
        {
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.ManualSimulation = true; game.NativeControlled = true;
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            game.Player.transform.position = new Vector3(0,.035f,-11.2f);
            game.Opponent.transform.position = new Vector3(0,.035f,11.2f);
            game.InjectBall(new Vector3(1,1.3f,0), new Vector3(0,0,-10));
            typeof(TennisGame).GetMethod("BuildSplit", Flags).Invoke(game,new object[]{"A","B"});
            typeof(TennisGame).GetMethod("UpdateSplit", Flags).Invoke(game,null);
            Assert.AreEqual(46,game.SplitCamera.fieldOfView);
            Assert.Greater(game.SplitCamera.transform.position.z,game.Opponent.transform.position.z+3.4f);
            Assert.Less(game.SplitCamera.transform.position.y,3f);
            game.SplitCamera.enabled=false;
            typeof(TennisGame).GetMethod("BuildVersusSplit", Flags).Invoke(game,new object[]{"B"});
            game.RightCamera.enabled=true;
            typeof(TennisGame).GetMethod("UpdateVersusSplit", Flags).Invoke(game,null);
            Assert.AreEqual(46,game.RightCamera.fieldOfView);
            Assert.Greater(game.RightCamera.transform.position.z,game.Opponent.transform.position.z+3.4f);
            game.ElevatedCamera=true;
            // Snap the other player's selectable elevated view for the assertion.
            typeof(TennisGame).GetField("rightFramed",Flags).SetValue(game,false);
            typeof(TennisGame).GetMethod("UpdateVersusSplit", Flags).Invoke(game,null);
            Assert.AreEqual(7,game.RightCamera.transform.position.y);
        }

        static void AssertLandingClear(TennisGame game)
        {
            var ring = (LineRenderer)typeof(TennisGame).GetField("landingRing", Flags).GetValue(game);
            Assert.IsTrue(ring.enabled);
            for(int i=0; i<ring.positionCount; i++) {
                var v=game.GameplayCamera.WorldToViewportPoint(ring.GetPosition(i));
                Assert.That(v.y, Is.InRange(.12f,.98f), "Landing ring clears the timing HUD");
                Assert.That(v.x, Is.InRange(.02f,.98f)); Assert.Greater(v.z,0);
            }
        }

        static void Capture(string name, TennisGame game, System.Text.StringBuilder log)
        {
            var cam=game.GameplayCamera;
            cam.aspect=16f/9;
            var v=cam.WorldToViewportPoint(game.BallPosition);
            Assert.That(v.y, Is.InRange(.025f,.975f), name+" ball height"); Assert.Greater(v.z,0);
            GameCapture.Save(Path.Combine(Out,name+".png"),1920,1080);
            log.AppendLine($"{name}: phase={game.Flow}; player={game.Player.transform.position}; ball={game.BallPosition}; eye={cam.transform.position}; pitch={cam.transform.eulerAngles.x}; fov={cam.fieldOfView}; ballViewport={v}");
        }
    }
}
