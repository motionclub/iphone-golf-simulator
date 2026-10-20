#if UNITY_EDITOR
// Chat B (golf-mannerisms) capture harness, copied into ~/unity-clones/golf-mannerisms/Assets/Editor/GMLocal by film.sh.
// Plays the phone's own flow on cliffside: address (the waggle), a drive (the post-shot watch), then on each hole a holing
// putt with the stroke count set so the hole-out reaction is, in turn, Victory, JumpJoy, FistPump, Slump, Stomp. Frames are
// saved only in those windows, from the gameplay camera, with the golfer's screen box in the trace for close crops.
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
    public static class GolfMannerismFilm
    {
        const string Flag = "GolfMannerismFilm.Active";
        static GolfMannerismFilm() { EditorApplication.update += Boot; }
        public static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;
        public static void Run()
        {
            GolferStyle.Body = Env("FILM_SEX", "Male") == "Female" ? GolferStyle.BodyKind.Female : GolferStyle.BodyKind.Male;
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity"); SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<GolfMannerismRecorder>()) return;
            var g = Object.FindFirstObjectByType<GolfGame>(); if (!g || !HoleView.Current) return;
            try { new GameObject("Golf mannerism film").AddComponent<GolfMannerismRecorder>().Begin(g); } catch (Exception e) { Debug.LogException(e); End(1); }
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    [DefaultExecutionOrder(10000)]
    public sealed class GolfMannerismRecorder : MonoBehaviour
    {
        static readonly string[] Reactions = { "Emote_Victory", "Emote_JumpJoy", "Emote_FistPump", "Emote_Slump", "Emote_Stomp" };
        GolfGame game; string dir; StreamWriter trace; int frame, saved, stage, wait, reaction; bool done, record; string window = "";
        static readonly BindingFlags Any = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
        GolferView Golfer => (GolferView)typeof(GolfGame).GetField("golfer", Any).GetValue(game);
        string Club => typeof(GolfGame).GetField("club", Any).GetValue(game).ToString();
        public void Begin(GolfGame g)
        {
            game = g;
            dir = Path.GetFullPath(GolfMannerismFilm.Env("FILM_OUT", "../work/golf-mannerisms/proof/film")); Directory.CreateDirectory(dir);
            foreach (var f in Directory.GetFiles(dir, "f_*.jpg")) File.Delete(f);
            PresentationPolicy.Configure("full", false, true, false);
            Time.captureFramerate = 30; UnityEngine.Random.InitState(1019);
            game.Demo = true; game.InstantReplays = false;
            GolferView.MannerismsOff = GolfMannerismFilm.Env("FILM_OFF", "0") == "1";
            Golfer.ApplyStyle();
            game.PrepareNativeAddress(GolfMannerismFilm.Env("FILM_COURSE", "cliffside"));
            game.SetWind(new Wind(0, 0));
            game.NativeReady(); game.TryNativePresentation();
            trace = new StreamWriter(Path.Combine(dir, "trace.csv"));
            trace.WriteLine("frame,saved,time,stage,window,state,performing,gx0,gy0,gx1,gy1,watching,waggle,fitShown,fitWanted,capsules,volumes");
            Debug.Log("[GolfMannerismFilm] begin " + dir + " sex " + GolferStyle.Body);
        }
        void Next() { stage++; wait = 0; Debug.Log($"[GolfMannerismFilm] stage {stage} at {Time.time:F2} state {game.Current}"); }
        void LateUpdate() { if (done || !game) return; try { Step(); } catch (Exception e) { Debug.LogException(e); Finish(1); } }
        bool SkipIntro(GolfGame.State s)
        {
            if (s == GolfGame.State.Intro && game.PresentationBeatIndex == 0 && wait > 20) game.NativeContinue();
            return s == GolfGame.State.Aim;
        }
        void Step()
        {
            var cam = Camera.main; if (cam) { cam.aspect = 16f / 9f; cam.rect = new Rect(0, 0, 1, 1); }
            frame++; wait++;
            var s = game.Current;
            switch (stage)
            {
                case 0: if (SkipIntro(s)) Next(); if (wait > 1500) throw new TimeoutException("intro"); break;
                case 1: // address: 3 s for the waggle, then a 0.9 s backswing and the drive
                    record = true; window = "address";
                    if (wait > 90 && wait <= 117) game.ShowBackswing(.9 * Mathf.SmoothStep(0, 1, (wait - 90) / 27f));
                    if (wait == 124)
                    {
                        var target = game.GreenTarget(5, 18, 7);
                        if (!target.HasValue) { var h = game.CurrentHole; double a = h.Tee.HeadingTo(h.Pin) * Math.PI / 180, d = Math.Min(h.Length * .7, 195); target = new CoursePoint(h.Tee.X + Math.Sin(a) * d, h.Tee.D + Math.Cos(a) * d); }
                        game.StrikeToward(target.Value); Next();
                    }
                    break;
                case 2: // contact and the post-shot watch (until the camera leaves the golfer), then wait for the next address
                    window = "watch"; record = wait < 90;
                    if (wait > 40 && s == GolfGame.State.Aim) Next();
                    if (wait > 1800) throw new TimeoutException("drive");
                    break;
                case 3: // a holing putt with the strokes set for this reaction
                    record = false;
                    if (s != GolfGame.State.Aim && wait < 20) { wait = 0; break; }
                    if (wait == 1)
                    {
                        var h = game.CurrentHole; double dx = h.Tee.X - h.Pin.X, dd = h.Tee.D - h.Pin.D, len = Math.Sqrt(dx * dx + dd * dd);
                        game.DropBall(new CoursePoint(h.Pin.X + dx / len * 2.5, h.Pin.D + dd / len * 2.5));
                    }
                    if (wait == 20)
                    {
                        int par = game.CurrentHole.Par;
                        int strokes = reaction switch { 0 => 1, 1 => par - 2, 2 => par - 1, 3 => par + 1, _ => par + 2 };
                        typeof(GolfGame).GetField("holeStrokes", Any).SetValue(game, strokes - 1);
                    }
                    if (wait > 30 && wait <= 45) game.ShowBackswing(.3 * Mathf.SmoothStep(0, 1, (wait - 30) / 15f));
                    if (wait == 50) { if (!game.StrikeHolingPutt()) game.StrikeToward(game.CurrentHole.Pin); Next(); }
                    break;
                case 4: // the hole-out, from the ball dropping to the next hole's opening
                    window = "holeout_" + Reactions[reaction];
                    record = s == GolfGame.State.Result && !string.IsNullOrEmpty(Golfer.Performing);
                    if (s is GolfGame.State.Intro or GolfGame.State.RoundDone && wait > 30)
                    {
                        record = false; reaction++;
                        if (reaction >= Reactions.Length || reaction >= int.Parse(GolfMannerismFilm.Env("FILM_REACTIONS", "5"))) { Finish(0); return; }
                        if (s == GolfGame.State.RoundDone)
                        {   // the native round is one hole: start another for the next reaction
                            game.PrepareNativeAddress(GolfMannerismFilm.Env("FILM_COURSE", "cliffside"));
                            game.NativeReady(); game.TryNativePresentation();
                        }
                        stage = 5; wait = 0;
                    }
                    if (s == GolfGame.State.Aim && wait > 60) { Debug.LogWarning("[GolfMannerismFilm] putt missed, again"); stage = 3; wait = 0; }
                    if (wait > 1500) throw new TimeoutException("holeout");
                    break;
                case 5: if (SkipIntro(s)) { stage = 3; wait = 0; } if (wait > 1500) throw new TimeoutException("intro2"); break;
            }
            Save();
        }
        void Save()
        {
            var g = Golfer;
            Vector4 box = new Vector4(-1, -1, -1, -1);
            var bounds = GolferBounds(g);
            if (bounds.HasValue && Camera.main)
            {
                var b = bounds.Value; float x0 = 1, y0 = 1, x1 = 0, y1 = 0;
                for (int i = 0; i < 8; i++)
                {
                    var p = Camera.main.WorldToViewportPoint(b.center + Vector3.Scale(b.extents, new Vector3(i & 1, (i >> 1) & 1, (i >> 2) & 1) * 2 - Vector3.one));
                    x0 = Mathf.Min(x0, p.x); x1 = Mathf.Max(x1, p.x); y0 = Mathf.Min(y0, p.y); y1 = Mathf.Max(y1, p.y);
                }
                box = new Vector4(x0, y0, x1, y1);
            }
            int idx = -1;
            if (record && frame % 2 == 0)
            {
                GameCapture.Save(Path.Combine(dir, $"f_{saved:D5}.jpg"), 1600, 900);
                if (bounds.HasValue) Zoom(Path.Combine(dir, $"z_{saved:D5}.jpg"), bounds.Value);
                idx = saved++;
            }
            string F(float v) => v.ToString("F3", CultureInfo.InvariantCulture);
            trace.WriteLine(string.Join(",", frame, idx, F(Time.time), stage, window, game.Current, g ? g.Performing ?? "" : "", F(box.x), F(box.y), F(box.z), F(box.w), g && g.Watching, g ? F(g.WaggleShare) : "0", g ? F(g.FitShown) : "0", g ? F(g.FitWanted) : "0", g ? g.FitCapsules : -1, g && g.Hero != null ? 0 : -1));
        }
        /// The golfer's visible parts (body, kit, hair; not a hidden club).
        static Bounds? GolferBounds(GolferView g)
        {
            if (!g) return null; Bounds? all = null;
            foreach (var r in g.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                if (!r.enabled || r.name.StartsWith("CLUB_") && !r.gameObject.activeInHierarchy) continue;
                if (all is Bounds a) { a.Encapsulate(r.bounds); all = a; } else all = r.bounds;
            }
            return all;
        }
        /// The same gameplay camera position, turned and narrowed onto the golfer (no HUD): the close look at hands, arms and shirt.
        static void Zoom(string path, Bounds b)
        {
            var cam = Camera.main; var t = cam.transform;
            var pos = t.position; var rot = t.rotation; float fov = cam.fieldOfView, aspect = cam.aspect; var target = cam.targetTexture;
            float dist = Vector3.Distance(pos, b.center);
            var rt = RenderTexture.GetTemporary(900, 1200, 24);
            try
            {
                t.LookAt(b.center); cam.aspect = .75f; cam.fieldOfView = 2 * Mathf.Atan(b.extents.magnitude * .8f / dist) * Mathf.Rad2Deg;
                cam.targetTexture = rt; cam.Render();
                var prev = RenderTexture.active; RenderTexture.active = rt;
                var tex = new Texture2D(900, 1200, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 900, 1200), 0, 0); tex.Apply();
                RenderTexture.active = prev;
                File.WriteAllBytes(path, tex.EncodeToJPG(88)); Object.DestroyImmediate(tex);
            }
            finally { cam.targetTexture = target; t.SetPositionAndRotation(pos, rot); cam.fieldOfView = fov; cam.aspect = aspect; RenderTexture.ReleaseTemporary(rt); }
        }
        void Finish(int code)
        {
            if (done) return; done = true; trace?.Dispose();
            Debug.Log($"[GolfMannerismFilm] done code {code} frames {frame} saved {saved} state {game.Current}");
            GolfMannerismFilm.End(code);
        }
    }
}
#endif
