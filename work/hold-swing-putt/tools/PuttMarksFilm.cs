#if UNITY_EDITOR
// Chat C (hold-swing-putt) capture harness: copied into ~/unity-clones/hold-swing-putt/Assets/Editor/HSPLocal by film.sh.
// Lines up a putt (the phone's flow: PrepareNativeAddress -> NativeReady), stills at the address (the ruler on the green),
// then the putter comes back to 30/55/85 % (the live amber bar and the lit marks), then a struck putt (the ruler gone).
using System;
using System.IO;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class PuttMarksFilm
    {
        const string Flag = "PuttMarksFilm.Active";
        static PuttMarksFilm() { EditorApplication.update += Boot; }
        public static void Run() { EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity"); SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true; }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<PuttMarksRecorder>()) return;
            var g = Object.FindFirstObjectByType<GolfGame>(); if (!g || !HoleView.Current) return;
            try { new GameObject("Putt marks film").AddComponent<PuttMarksRecorder>().Begin(g); } catch (Exception e) { Debug.LogException(e); End(1); }
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    [DefaultExecutionOrder(10000)]
    public sealed class PuttMarksRecorder : MonoBehaviour
    {
        GolfGame game; string dir; int wait, stage, hole; bool done;
        static readonly double[] Loads = { 0, .3, .55, .85 };
        public void Begin(GolfGame g)
        {
            game = g;
            dir = Path.GetFullPath(Environment.GetEnvironmentVariable("FILM_OUT") ?? "../work/hold-swing-putt/proof/film"); Directory.CreateDirectory(dir);
            Time.captureFramerate = 30; UnityEngine.Random.InitState(1019);
            game.Demo = true; game.InstantReplays = false;
            game.PrepareNativeAddress(Environment.GetEnvironmentVariable("FILM_COURSE") ?? "cliffside");
            game.SetWind(new Wind(0, 0));
            Debug.Log("[PuttMarksFilm] begin " + dir);
        }
        void LateUpdate() { if (done || !game) return; try { Step(); } catch (Exception e) { Debug.LogException(e); Finish(1); } }
        void Step()
        {
            var cam = Camera.main; if (cam) { cam.aspect = 16f / 9f; cam.rect = new Rect(0, 0, 1, 1); }
            wait++;
            if (game.Current == GolfGame.State.Intro) { if (wait % 30 == 0) game.NativeContinue(); return; }
            if (game.Current != GolfGame.State.Aim && stage < 10) return;
            switch (stage)
            {
                case 0: // a putt from back down the line: 9 yd (27 ft) on hole 1, 4 yd on the second shot
                {
                    var h = game.CurrentHole; double back = hole == 0 ? 9 : 4;
                    double dx = h.Tee.X - h.Pin.X, dd = h.Tee.D - h.Pin.D, len = Math.Sqrt(dx * dx + dd * dd);
                    game.DropBall(new CoursePoint(h.Pin.X + dx / len * back + dd / len * 1.2, h.Pin.D + dd / len * back - dx / len * 1.2));
                    game.NativeReady();
                    stage = 1; wait = 0; break;
                }
                default:
                    if (stage >= 1 && stage <= Loads.Length)
                    {
                        double load = Loads[stage - 1];
                        if (load > 0) game.ShowBackswing(load * Mathf.SmoothStep(0, 1, Mathf.Min(1, wait / 20f)));
                        if (wait == 45)
                        {
                            GameCapture.Save(Path.Combine(dir, $"putt{hole}_{stage}_load{load * 100:F0}.jpg"), 1600, 900);
                            Debug.Log($"[PuttMarksFilm] still hole {hole} load {load:F2} club {game.ClubInHand}");
                            stage++; wait = 0;
                        }
                    }
                    else if (stage == Loads.Length + 1) { game.StrikeToward(game.CurrentHole.Pin); stage = 10; wait = 0; }
                    else if (stage == 10 && wait == 20) { GameCapture.Save(Path.Combine(dir, $"putt{hole}_rolling.jpg"), 1600, 900); stage = 11; }
                    else if (stage == 11 && wait > 60) { if (++hole >= 2) { Finish(0); return; } stage = 12; wait = 0; }
                    else if (stage == 12 && game.Current == GolfGame.State.Aim && wait > 20) { stage = 0; wait = 0; }
                    else if (stage == 12 && wait > 1200) { Finish(0); return; }
                    break;
            }
            if (wait > 2400) throw new TimeoutException("stage " + stage);
        }
        void Finish(int code) { if (done) return; done = true; Debug.Log($"[PuttMarksFilm] done code {code}"); PuttMarksFilm.End(code); }
    }
}
#endif
