#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Hole-out pick-up film (APFS clone ONLY, never the shared project): the real game plays a hole's tee shot, the ball is dropped JF_DIST yards from the
    /// pin and a holing putt is struck; the game's own hole-out flow then runs and is filmed at 30 fps (game camera, and a side camera that follows the golfer).
    ///   JF_OUT=<dir> JF_FEMALE=0|1 JF_DIST=8 JF_PAR=0 (JF_PAR=1: skip the tee shot, ace-like)
    ///   Unity -projectPath <clone> -executeMethod GolfArcade.EditorTools.PickFilm.Run   (graphics on, no -quit)
    [InitializeOnLoad]
    public static class PickFilm
    {
        const string Flag = "PickFilm";
        static IEnumerator script; static int lastFrame = -1;
        static PickFilm() { EditorApplication.update += Tick; }
        static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;
        public static void Run()
        {
            script = null; lastFrame = -1;
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            if (script == null) { var g = Object.FindFirstObjectByType<GolfGame>(); if (!g) return; script = Film(g); }
            try { if (!script.MoveNext()) Done(0); } catch (Exception e) { Debug.LogException(e); Done(1); }
        }
        static void Done(int c)
        {
            SessionState.SetBool(Flag, false); Time.captureFramerate = 0; Time.timeScale = 1;
            if (Application.isBatchMode) EditorApplication.Exit(c); else EditorApplication.isPlaying = false;
        }
        static IEnumerator WaitFor(Func<bool> done, int frames, string what)
        {
            for (int i = 0; !done(); i++) { if (i > frames) throw new TimeoutException("waiting for " + what); yield return null; }
        }
        static void Plain(Camera cam, string path, int w, int h)
        {
            var hidden = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.enabled && c.renderMode != RenderMode.WorldSpace).ToList();
            var a = cam.aspect; var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 4);
            var prev = cam.targetTexture; cam.targetTexture = rt; cam.aspect = w / (float)h; cam.Render(); cam.targetTexture = prev; cam.aspect = a;
            var tex = new Texture2D(w, h, TextureFormat.RGB24, false); var act = RenderTexture.active;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, w, h), 0, 0); tex.Apply(); RenderTexture.active = act; RenderTexture.ReleaseTemporary(rt);
            File.WriteAllBytes(path, tex.EncodeToJPG(92)); Object.DestroyImmediate(tex);
        }
        static void Side(Camera cam, string path, Vector3 from, Vector3 look, float fov, int w, int h)
        {
            var p = cam.transform.position; var r = cam.transform.rotation; var f = cam.fieldOfView;
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(look - from)); cam.fieldOfView = fov;
            Plain(cam, path, w, h);
            cam.transform.SetPositionAndRotation(p, r); cam.fieldOfView = f;
        }

        static IEnumerator Film(GolfGame game)
        {
            string dir = Path.GetFullPath(Env("JF_OUT", "pk_out")); Directory.CreateDirectory(dir);
            bool female = Env("JF_FEMALE", "0") == "1"; double dist = double.Parse(Env("JF_DIST", "8"));
            var savedBody = GolferStyle.Body; int savedHoles = PlayerPrefs.GetInt("holes", 0); string savedCourse = PlayerPrefs.GetString("course", "cliffside");
            var log = new System.Collections.Generic.List<string>();
            try
            {
                Time.captureFramerate = 60; Time.timeScale = 1; UnityEngine.Random.InitState(3108);
                GolfGame.LoadCoverMinimum = 0.5f; game.InstantReplays = false;
                for (int i = 0; i < 10; i++) yield return null;
                GolferStyle.Body = female ? GolferStyle.BodyKind.Female : GolferStyle.BodyKind.Male;
                var golfer = game.GetComponentInChildren<GolferView>(true); golfer.ApplyStyle();
                game.ChooseHoles(0, "cliffside"); game.Play();
                var e1 = WaitFor(() => game.Current == GolfGame.State.Aim, 60 * 60, "the first tee"); while (e1.MoveNext()) yield return null;
                golfer = game.GetComponentInChildren<GolferView>(true);
                var cam = game.GameplayCamera ? game.GameplayCamera : Camera.main;
                foreach (var smr in golfer.GetComponentsInChildren<SkinnedMeshRenderer>(true)) smr.updateWhenOffscreen = true;
                var hole = game.CurrentHole;
                for (int i = 0; i < 24; i++) { cam.aspect = 16f / 9f; yield return null; }
                game.StrikeToward(hole.RecommendedTarget(hole.Tee));
                var e2 = WaitFor(() => game.Current is GolfGame.State.Aim or GolfGame.State.Result or GolfGame.State.HoleDone, 60 * 60, "the tee shot"); while (e2.MoveNext()) { cam.aspect = 16f / 9f; yield return null; }
                if (game.Current == GolfGame.State.Result)
                {
                    var e3 = WaitFor(() => game.Current is GolfGame.State.Aim or GolfGame.State.HoleDone, 60 * 60, "the result to pass"); while (e3.MoveNext()) { cam.aspect = 16f / 9f; yield return null; }
                }
                golfer = game.GetComponentInChildren<GolferView>(true);
                foreach (var smr in golfer.GetComponentsInChildren<SkinnedMeshRenderer>(true)) smr.updateWhenOffscreen = true;
                var pin = hole.Pin; double d = pin.DistanceTo(hole.Tee);
                // strokes so that the putt is a birdie (an eagle or ace keeps the big celebration): par-3 more approach shots
                int extra = int.Parse(Env("JF_EXTRA", Math.Max(0, hole.Par - 3).ToString()));
                for (int x = 0; x < extra; x++)
                {
                    game.DropBall(new CoursePoint(pin.X + (hole.Tee.X - pin.X) * 30 / d, pin.D + (hole.Tee.D - pin.D) * 30 / d));
                    for (int i = 0; i < 30; i++) { cam.aspect = 16f / 9f; yield return null; }
                    game.StrikeToward(pin);
                    var ex = WaitFor(() => game.Current is GolfGame.State.Aim or GolfGame.State.Result or GolfGame.State.HoleDone, 60 * 60, "an approach"); while (ex.MoveNext()) { cam.aspect = 16f / 9f; yield return null; }
                    if (game.Current == GolfGame.State.Result)
                    {
                        var ex2 = WaitFor(() => game.Current is GolfGame.State.Aim or GolfGame.State.HoleDone, 60 * 60, "the result to pass"); while (ex2.MoveNext()) { cam.aspect = 16f / 9f; yield return null; }
                    }
                }
                game.DropBall(new CoursePoint(pin.X + (hole.Tee.X - pin.X) * dist / d, pin.D + (hole.Tee.D - pin.D) * dist / d));
                for (int i = 0; i < 30; i++) { cam.aspect = 16f / 9f; yield return null; }
                bool struck = game.StrikeHolingPutt();
                log.Add($"holing putt struck={struck} from {dist} yd");
                var e4 = WaitFor(() => game.Current == GolfGame.State.Result, 60 * 60, "the hole's result"); while (e4.MoveNext()) { cam.aspect = 16f / 9f; yield return null; }
                int n = 0, guard = 0; bool seen = false; float maxHeld = 0;
                while (guard++ < 60 * 16 && game.Current == GolfGame.State.Result)
                {
                    cam.aspect = 16f / 9f; yield return null;
                    if (golfer.PickingUp) seen = true;
                    if (guard % 2 == 0)
                    {
                        string fid = (n++).ToString("00000");
                        GolfArcade.Game.GameCapture.Save($"{dir}/game_{fid}.jpg", 1280, 720);
                        var gp = golfer.transform.position; var right = Vector3.Cross(Vector3.up, golfer.transform.forward);
                        Side(cam, $"{dir}/side_{fid}.jpg", gp + right * -4.5f + Vector3.up * 1.0f + golfer.transform.forward * 0.8f, gp + Vector3.up * .75f + golfer.transform.forward * .5f, 38, 720, 720);
                    }
                    if (!golfer.PickingUp && seen && guard > 60 * 3 && n > 30 && golfer.Performing != "Emote_PickUp") { if (++maxHeld > 40) break; }
                }
                log.Add($"pickup seen={seen} frames={n} seconds={golfer.PickUpSeconds:0.0} performing={golfer.Performing}");
                Debug.Log("[PickFilm] " + log.Last());
            }
            finally { GolferStyle.Body = savedBody; PlayerPrefs.SetInt("holes", savedHoles); PlayerPrefs.SetString("course", savedCourse); PlayerPrefs.Save(); File.WriteAllText(dir + "/summary.txt", string.Join("\n", log) + "\n"); }
        }
    }
}
#endif
