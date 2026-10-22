#if UNITY_EDITOR
// Chat A (golf-flow-camera) capture harness: copied into ~/unity-clones/golf-flow-camera/Assets/Editor/GFCLocal by film.sh.
// Plays the phone's own flow (PrepareNativeAddress -> NativeReady -> TryNativePresentation): the hole's opening, the first
// drive, a putt from off the hole (usually missed) and a holing putt, saving frames and a per-frame trace.
using System;
using System.Globalization;
using System.IO;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class GolfFlowFilm
    {
        const string Flag = "GolfFlowFilm.Active";
        static GolfFlowFilm() { EditorApplication.update += Boot; }
        public static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;
        public static void Run() { EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity"); SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true; }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<GolfFlowRecorder>()) return;
            var g = Object.FindFirstObjectByType<GolfGame>(); if (!g || !HoleView.Current) return;
            try { new GameObject("Golf flow film").AddComponent<GolfFlowRecorder>().Begin(g); } catch (Exception e) { Debug.LogException(e); End(1); }
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    [DefaultExecutionOrder(10000)]
    public sealed class GolfFlowRecorder : MonoBehaviour
    {
        GolfGame game; string dir; StreamWriter trace; int frame, saved, stage, wait; bool done; float stageAt;
        static readonly BindingFlags Any = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
        GolferView Golfer => (GolferView)typeof(GolfGame).GetField("golfer", Any).GetValue(game);
        string Club => typeof(GolfGame).GetField("club", Any).GetValue(game).ToString();
        public void Begin(GolfGame g)
        {
            game = g;
            dir = Path.GetFullPath(GolfFlowFilm.Env("FILM_OUT", "../work/golf-flow-camera/proof/film")); Directory.CreateDirectory(dir);
            foreach (var f in Directory.GetFiles(dir, "f_*.jpg")) File.Delete(f);
            PresentationPolicy.Configure("full", false, true, false);
            foreach (var key in new[] { "golf.walkon", "golf.start" }) PlayerPrefs.DeleteKey("presentation.v" + PresentationPolicy.Revision + "." + key);
            foreach (var c in new[] { "cliffside", "wildisles", "magma" })
                for (int i = 1; i <= 30; i++) PlayerPrefs.DeleteKey("presentation.v" + PresentationPolicy.Revision + ".golf.venue." + c + "." + i);
            Time.captureFramerate = 30; UnityEngine.Random.InitState(1019);
            game.Demo = true; game.InstantReplays = false;
            game.PrepareNativeAddress(GolfFlowFilm.Env("FILM_COURSE", "cliffside"));
            game.SetWind(new Wind(0, 0));
            game.NativeReady(); game.TryNativePresentation();
            trace = new StreamWriter(Path.Combine(dir, "trace.csv"));
            trace.WriteLine("frame,saved,time,stage,state,beat,performing,modelYawToStance,golferActive,golferAlpha,camX,camY,camZ,camYaw,camPitch,ballX,ballY,ballZ,club");
            Debug.Log("[GolfFlowFilm] begin " + dir);
        }
        void Next() { stage++; wait = 0; stageAt = Time.time; Debug.Log($"[GolfFlowFilm] stage {stage} at {Time.time:F2} state {game.Current}"); }
        void LateUpdate() { if (done || !game) return; try { Step(); } catch (Exception e) { Debug.LogException(e); Finish(1); } }
        void Step()
        {
            var cam = Camera.main; if (cam) { cam.aspect = 16f / 9f; cam.rect = new Rect(0, 0, 1, 1); }
            frame++; wait++;
            var s = game.Current;
            switch (stage)
            {
                case 0: // the opening: let the flyover run 6 s (its tags would show from ~2.8 s), then skip it as the phone's button does
                    if (s == GolfGame.State.Intro && game.PresentationBeatIndex == 0 && wait > 180) game.NativeContinue();
                    if (s == GolfGame.State.Aim) Next();
                    if (wait > 1500) throw new TimeoutException("intro");
                    break;
                case 1: // a second at address, a 0.9 s backswing, the drive
                    if (wait > 30 && wait <= 57) game.ShowBackswing(.9 * Mathf.SmoothStep(0, 1, (wait - 30) / 27f));
                    if (wait == 64)
                    {
                        var target = game.GreenTarget(5, 18, 7);
                        if (!target.HasValue) { var h = game.CurrentHole; double a = h.Tee.HeadingTo(h.Pin) * Math.PI / 180, d = Math.Min(h.Length * .7, 195); target = new CoursePoint(h.Tee.X + Math.Sin(a) * d, h.Tee.D + Math.Cos(a) * d); }
                        game.StrikeToward(target.Value); Next();
                    }
                    break;
                case 2: // the flight and its result, until the next address
                    if (wait > 40 && s == GolfGame.State.Aim) Next();
                    if (wait > 1800) throw new TimeoutException("drive");
                    break;
                case 3: // a long putt (from 12 yd back down the line, unless the ball is already on the green)
                    if (wait == 1 && Club != "Putter")
                    {
                        var h = game.CurrentHole; double dx = h.Tee.X - h.Pin.X, dd = h.Tee.D - h.Pin.D, len = Math.Sqrt(dx * dx + dd * dd);
                        game.DropBall(new CoursePoint(h.Pin.X + dx / len * 9 + dd / len * 2, h.Pin.D + dd / len * 9 - dx / len * 2));
                    }
                    if (wait > 30 && wait <= 50) game.ShowBackswing(.5 * Mathf.SmoothStep(0, 1, (wait - 30) / 20f));
                    if (wait == 56) { game.StrikeToward(game.CurrentHole.Pin); Next(); }
                    break;
                case 4: // that putt's roll and result: holed (the round goes on) or the next address
                    if (wait > 40 && s == GolfGame.State.Aim) Next();
                    else if (wait > 40 && s is GolfGame.State.HoleDone or GolfGame.State.Intro or GolfGame.State.RoundDone) { stage = 6; wait = 0; }
                    if (wait > 1500) throw new TimeoutException("putt");
                    break;
                case 5: // the holing putt
                    if (wait > 30 && wait <= 50) game.ShowBackswing(.4 * Mathf.SmoothStep(0, 1, (wait - 30) / 20f));
                    if (wait == 56) { if (!game.StrikeHolingPutt()) game.StrikeToward(game.CurrentHole.Pin); Next(); }
                    break;
                case 6: // the hole-out through to the next hole's opening
                    if (s is GolfGame.State.Intro or GolfGame.State.RoundDone && wait > 30 || wait > 900) { Finish(0); return; }
                    break;
            }
            Save();
        }
        void Save()
        {
            var g = Golfer; var cam = Camera.main.transform; var ball = GameObject.Find("Ball");
            var model = g ? (GameObject)typeof(GolferView).GetField("modelGo", Any).GetValue(g) : null;
            float yaw = model ? Mathf.DeltaAngle(0, model.transform.localEulerAngles.y) : float.NaN;
            var fade = g ? g.GetComponent<GolferFade>() : null; float alpha = fade ? fade.Opacity : 1f;
            var e = cam.eulerAngles; var b = ball ? ball.transform.position : Vector3.zero;
            if (frame % 2 == 0) { GameCapture.Save(Path.Combine(dir, $"f_{saved:D5}.jpg"), 960, 540); saved++; }
            trace.WriteLine(string.Join(",", frame, saved, Time.time.ToString("F3", CultureInfo.InvariantCulture), stage, game.Current, game.PresentationBeatIndex,
                g ? g.Performing ?? "" : "", yaw.ToString("F1", CultureInfo.InvariantCulture), g && g.gameObject.activeInHierarchy, alpha.ToString("F2", CultureInfo.InvariantCulture),
                cam.position.x.ToString("F2", CultureInfo.InvariantCulture), cam.position.y.ToString("F2", CultureInfo.InvariantCulture), cam.position.z.ToString("F2", CultureInfo.InvariantCulture),
                e.y.ToString("F1", CultureInfo.InvariantCulture), e.x.ToString("F1", CultureInfo.InvariantCulture),
                b.x.ToString("F2", CultureInfo.InvariantCulture), b.y.ToString("F2", CultureInfo.InvariantCulture), b.z.ToString("F2", CultureInfo.InvariantCulture), Club));
        }
        void Finish(int code)
        {
            if (done) return; done = true; trace?.Dispose();
            Debug.Log($"[GolfFlowFilm] done code {code} frames {frame} saved {saved} state {game.Current}");
            GolfFlowFilm.End(code);
        }
    }
}
#endif
