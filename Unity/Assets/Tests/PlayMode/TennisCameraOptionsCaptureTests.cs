using System.Collections;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// Renders the shipping chase camera next to three pulled-back candidates from identical match moments.
    public class TennisCameraOptionsCaptureTests
    {
        static string Out => System.Environment.GetEnvironmentVariable("CAMERA_OPTIONS_OUT") ?? "Library/Captures/camera-options";

        // name, eye offset from player (x follows the player by `follow`, rest is fixed), look-at offset from player, fov
        struct Option { public string name; public float follow, x, y, z, lookX, lookY, lookZ, fov; }

        static readonly Option[] Options = {
            new Option { name = "A_pulled_back_shoulder", follow = 1, x = .9f, y = 3.3f, z = -5.6f, lookX = .2f, lookY = 1.0f, lookZ = 9f, fov = 48 },
            new Option { name = "B_high_behind_centred", follow = .75f, x = 0, y = 5.0f, z = -7.4f, lookX = 0, lookY = .8f, lookZ = 5.5f, fov = 46 },
            new Option { name = "C_three_quarter_wide", follow = 1f, x = -2.4f, y = 3.8f, z = -6.0f, lookX = 1.4f, lookY = 1.0f, lookZ = 5.5f, fov = 50 },
        };

        [UnityTest, Explicit, Timeout(600000)] public IEnumerator Capture()
        {
            LogAssert.ignoreFailingMessages = true;
            TennisVenue.Selected = TennisVenueKind.Resort;
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.ManualSimulation = true; game.NativeControlled = true; TennisGame.InstantReplayEnabled = false;
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            game.ElevatedCamera = false;
            Directory.CreateDirectory(Out);
            int oldRate = Time.captureFramerate; Time.captureFramerate = 60;
            try {
                // Moment 1: ball coming across, player set up at the baseline.
                game.PrepareLesson();
                game.Player.transform.position = new Vector3(2.2f, .035f, -11.2f);
                game.Player.Prepare(.6f, false);
                var from = new Vector3(.95f, 1.35f, -5f);
                game.InjectBall(from, TennisRules.RallyVelocity(from, new Vector3(2.4f, TennisRules.BallRadius, -9.6f), 12f, 0, .75f));
                game.Player.Tick(.2f, 0);
                for (int i = 0; i < 60; i++) { game.Step(1f / 120); yield return null; }
                Shoot(game, "rally");

                // Moment 2: mid forehand.
                game.PrepareLesson();
                game.Player.transform.position = new Vector3(-1.5f, .035f, -11.2f);
                game.Player.Prepare(.6f, false);
                from = new Vector3(-1.2f, 1.35f, -5f);
                game.InjectBall(from, TennisRules.RallyVelocity(from, new Vector3(-1.5f, TennisRules.BallRadius, -10.4f), 12f, 0, .75f));
                game.Player.Tick(.2f, 0);
                for (int i = 0; i < 70; i++) { game.Step(1f / 120); yield return null; }
                game.Player.Swing(.7f, false, TennisActor.Stroke.Drive);
                for (int i = 0; i < 14; i++) { game.Step(1f / 120); yield return null; }
                Shoot(game, "swing");

                // Moment 3: stepped up near the net.
                game.PrepareLesson();
                game.Player.transform.position = new Vector3(0, .035f, -2.6f);
                var volleyFrom = new Vector3(.95f, 1.3f, -1f);
                game.InjectBall(volleyFrom, TennisRules.RallyVelocity(volleyFrom, new Vector3(.8f, TennisRules.BallRadius, -3.4f), 10f, 0, .75f));
                game.Player.Swing(.45f, false, TennisActor.Stroke.Volley);
                game.Player.Tick(.12f, 0);
                for (int i = 0; i < 50; i++) { game.Step(1f / 120); yield return null; }
                Shoot(game, "net");
            } finally { Time.captureFramerate = oldRate; }
        }

        static void Shoot(TennisGame game, string moment)
        {
            var cam = game.GameplayCamera; cam.aspect = 16f / 9;
            var p = game.Player.transform.position;
            // Current shipping camera exactly as the game framed it.
            GameCapture.Save(Path.Combine(Out, moment + "_0_current.png"), 1600, 900);
            Vector3 keepPos = cam.transform.position; Quaternion keepRot = cam.transform.rotation; float keepFov = cam.fieldOfView;
            foreach (var o in Options) {
                float cx = Mathf.Lerp(0, p.x, o.follow) + o.x;
                cam.transform.position = new Vector3(cx, o.y, p.z + o.z);
                cam.transform.LookAt(new Vector3(Mathf.Lerp(0, p.x, o.follow) + o.lookX, o.lookY, p.z + o.lookZ));
                cam.fieldOfView = o.fov;
                GameCapture.Save(Path.Combine(Out, moment + "_" + o.name + ".png"), 1600, 900);
            }
            cam.transform.SetPositionAndRotation(keepPos, keepRot); cam.fieldOfView = keepFov;
        }
    }
}
