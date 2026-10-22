using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.PlayTests
{
    /// FRAME_RATE_60B (work/frame-rate-60b): does each scene ask for and hold 60, and does anything on screen move in 1/30 s steps.
    /// Run windowed (graphics on), muted: Unity -projectPath <clone> -runTests -testPlatform PlayMode -testFilter FrameRate60bTests
    /// FR60B_DIR = where the numbers (and, with FR60B_FRAMES=1, a few rendered frames) go.
    public class FrameRate60bTests
    {
        static string Dir => Environment.GetEnvironmentVariable("FR60B_DIR") ?? Path.GetFullPath("Library/fr60b");
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        GameObject host;

        [TearDown] public void Clean()
        {
            HubWorld.EditorDriven = false;
            if (host) Object.DestroyImmediate(host);
            Time.captureFramerate = 0; Time.timeScale = 1;
        }

        // ------------------------------------------------------------------ RUNTIME: real frame times, nothing fixed

        /// Wall-clock frame times over `seconds` of the scene as it runs: median fps, the 5th percentile, and the share of
        /// frames that took a 30 fps slot (31-36 ms). A 30 fps lock shows as most frames in that band.
        static IEnumerator Frames(string label, float seconds, List<string> rows, Action<int> each = null)
        {
            var dts = new List<float>(); float t = 0; int i = 0;
            while (t < seconds) { yield return null; float dt = Time.unscaledDeltaTime; dts.Add(dt); t += dt; each?.Invoke(i++); }
            var s = dts.OrderBy(x => x).ToList();
            float median = s[s.Count / 2], p95 = s[(int)(s.Count * .95f)];
            float slot30 = dts.Count(d => d > .031f && d < .036f) / (float)dts.Count;
            var cam = Main(); var urp = TennisQuality.Pipeline;
            string row = string.Format(Inv, "{{\"scene\":\"{0}\",\"frames\":{1},\"medianFps\":{2:0.0},\"p05Fps\":{3:0.0},\"share30fpsSlot\":{4:0.000},\"target\":{5},\"vSync\":{6},\"renderInterval\":{7},\"seconds\":{8:0.0},\"screen\":\"{9}x{10}\",\"camera\":\"{11}x{12}\",\"renderScale\":{13:0.00}}}",
                label, dts.Count, 1 / median, 1 / p95, slot30, Application.targetFrameRate, QualitySettings.vSyncCount, OnDemandRendering.renderFrameInterval, t,
                Screen.width, Screen.height, cam ? cam.pixelWidth : 0, cam ? cam.pixelHeight : 0, urp ? urp.renderScale : 1f);
            rows.Add(row); Debug.Log("[FR60B] RUNTIME " + row);
            // RES_1080 proof: the frame as drawn, at the size it was drawn
            Directory.CreateDirectory(Path.Combine(Dir, "res1080"));
            ScreenCapture.CaptureScreenshot(Path.Combine(Dir, "res1080", label + ".png"));
            yield return null; yield return null;
        }

        [UnityTest, Explicit, Timeout(1800000)]
        public IEnumerator RuntimeHoldsSixty()
        {
            Time.captureFramerate = 0; Time.timeScale = 1;
            GameView(1920, 1080);
            yield return null; yield return null;
            Debug.Log($"[FR60B] game view {Screen.width}x{Screen.height}");
            var rows = new List<string>();
            // tennis: the opening presentation (drone + intros), then an autoplayed rally
            PresentationPolicy.Configure("full", false, true, false);
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var tennis = Object.FindFirstObjectByType<TennisGame>();
            for (int k = 0; k < 30; k++) yield return null;
            yield return Frames("tennis_intro", Mathf.Min(8f, TennisPresentation.Length - 1f), rows);
            for (float w = 0; w < TennisPresentation.Length; w += Time.unscaledDeltaTime) yield return null;
            tennis.ConfigureMatch(TennisGame.Mode.Exhibition, null, "Rival", "CASUAL MATCH"); tennis.AutoPlay = true; tennis.AutoPlayLean = true;
            for (int k = 0; k < 120; k++) yield return null;
            yield return Frames("tennis_match", 15f, rows);
            tennis.AutoPlay = false;
            // golf: the hole presentation (intro), then aim + swing + flight
            yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
            var golf = Object.FindFirstObjectByType<GolfGame>();
            for (int k = 0; k < 30; k++) yield return null;
            golf.PrepareNativeAddress(); golf.NativeReady(); golf.TryNativePresentation();
            yield return Frames("golf_intro", 6f, rows);
            golf.PrepareNativeAddress(); golf.JumpToHole(7); golf.DropBall(golf.CurrentHole.Tee);
            for (int k = 0; k < 30; k++) yield return null;
            golf.NativeReady(); UnityEngine.Random.InitState(902); golf.NativeSwing(.78f);
            yield return Frames("golf_hole", 10f, rows);
            // plaza: booted the way the phone boots it
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "fr60b", action = "start", sport = "hub", touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF" }));
            for (int i = 0; i < 1200 && !bridge.Ready; i++) yield return null;
            for (int k = 0; k < 120; k++) yield return null;
            yield return Frames("plaza", 10f, rows);
            Directory.CreateDirectory(Dir);
            File.WriteAllText(Path.Combine(Dir, "runtime.jsonl"), string.Join("\n", rows) + "\n");
        }

        /// The Editor's Game view at a fixed w x h (the TV's 1080p), so the frame times are for a 1080p render target.
        static void GameView(int w, int h)
        {
#if UNITY_EDITOR
            try
            {
                var asm = typeof(UnityEditor.Editor).Assembly;
                var sizesType = asm.GetType("UnityEditor.GameViewSizes");
                var instance = typeof(UnityEditor.ScriptableSingleton<>).MakeGenericType(sizesType).GetProperty("instance").GetValue(null);
                var group = sizesType.GetProperty("currentGroup").GetValue(instance);
                var groupType = group.GetType();
                int count = (int)groupType.GetMethod("GetTotalCount").Invoke(group, null), index = -1;
                for (int i = 0; i < count && index < 0; i++)
                {
                    var size = groupType.GetMethod("GetGameViewSize").Invoke(group, new object[] { i });
                    var st = size.GetType();
                    if ((int)st.GetProperty("width").GetValue(size) == w && (int)st.GetProperty("height").GetValue(size) == h && st.GetProperty("sizeType").GetValue(size).ToString() == "FixedResolution") index = i;
                }
                if (index < 0)
                {
                    var sizeType = asm.GetType("UnityEditor.GameViewSize"); var kind = asm.GetType("UnityEditor.GameViewSizeType");
                    var made = Activator.CreateInstance(sizeType, Enum.Parse(kind, "FixedResolution"), w, h, "FR60B 1080p");
                    groupType.GetMethod("AddCustomSize").Invoke(group, new[] { made });
                    index = (int)groupType.GetMethod("GetTotalCount").Invoke(group, null) - 1;
                }
                var gvType = asm.GetType("UnityEditor.GameView");
                var gv = UnityEditor.EditorWindow.GetWindow(gvType);
                const System.Reflection.BindingFlags any = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
                gvType.GetProperty("lowResolutionForAspectRatios", any)?.SetValue(gv, false);
                var select = gvType.GetMethod("SizeSelectionCallback", any);
                if (select != null) select.Invoke(gv, new object[] { index, null });
                else gvType.GetProperty("selectedSizeIndex", any)?.SetValue(gv, index);
                gv.Repaint();
            }
            catch (Exception e) { Debug.LogWarning("[FR60B] could not set the Game view size: " + e.Message); }
#endif
        }

        // ------------------------------------------------------------------ NO_STEP: positions on a fixed 60 Hz clock

        /// Every visible mover, once per drawn frame, with the game clock fixed at 1/60 s (Time.captureFramerate): a thing that only
        /// changes every other frame, or that moves in straight lines between 1/30 s keys, shows in these tracks (analysed by
        /// work/frame-rate-60b/scripts/no_step.py).
        sealed class Tracks
        {
            readonly Dictionary<string, List<Vector3>> data = new();
            public void Add(string key, Vector3 v) { if (!data.TryGetValue(key, out var l)) data[key] = l = new List<Vector3>(); l.Add(v); }
            public void Save(string path)
            {
                using var w = new StreamWriter(path);
                foreach (var kv in data) w.WriteLine(kv.Key + "\t" + string.Join(";", kv.Value.Select(v => string.Format(Inv, "{0:0.#####},{1:0.#####},{2:0.#####}", v.x, v.y, v.z))));
            }
        }

        static Transform Named(Transform root, Func<string, bool> match) =>
            root ? root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => match(t.name) && t.gameObject.activeInHierarchy) : null;

        /// A point fixed to the transform 1 m out along a skew axis: its motion is the transform's whole rigid motion (turn and travel).
        static Vector3 Rigid(Transform t) => t.position + t.rotation * new Vector3(.577f, .577f, .577f);

        static void Frame(Camera cam, string path)
        {
            if (!cam) return;
            var rt = RenderTexture.GetTemporary(480, 270, 24, RenderTextureFormat.ARGB32);
            var prevT = cam.targetTexture; var prevA = cam.aspect;
            cam.targetTexture = rt; cam.aspect = 480 / 270f; cam.Render(); cam.targetTexture = prevT; cam.aspect = prevA;
            var prev = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(480, 270, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 480, 270), 0, 0); tex.Apply();
            RenderTexture.active = prev; RenderTexture.ReleaseTemporary(rt);
            File.WriteAllBytes(path, tex.EncodeToJPG(92)); Object.Destroy(tex);
        }

        static IEnumerator Record(string label, int frames, Func<Camera> camera, Action<Tracks> probe)
        {
            var tracks = new Tracks();
            bool images = Environment.GetEnvironmentVariable("FR60B_FRAMES") == "1";
            string imageDir = Path.Combine(Dir, "frames", label);
            if (images) { Directory.CreateDirectory(imageDir); foreach (var f in Directory.GetFiles(imageDir)) File.Delete(f); }
            for (int i = 0; i < frames; i++)
            {
                yield return new WaitForEndOfFrame();
                var cam = camera();
                if (cam) { tracks.Add("camera", cam.transform.position); tracks.Add("camera_aim", cam.transform.position + cam.transform.forward * 10); }
                probe(tracks);
                if (images && i < 150) Frame(cam, Path.Combine(imageDir, $"f{i:000}.jpg"));
                yield return null;
            }
            Directory.CreateDirectory(Dir);
            tracks.Save(Path.Combine(Dir, "tracks_" + label + ".tsv"));
            Debug.Log("[FR60B] NO_STEP recorded " + label);
        }

        static Camera Main() => Camera.main ? Camera.main : Camera.allCameras.Where(c => c.enabled && !c.targetTexture).OrderByDescending(c => c.depth).FirstOrDefault();

        [UnityTest, Explicit, Timeout(1800000)]
        public IEnumerator NothingStepsAtThirty()
        {
            Time.captureFramerate = 60; Time.timeScale = 1;
            GameView(1920, 1080);
            PresentationPolicy.Configure("full", false, true, false);
            // tennis intro + rally: ball, racket, the player's hands and head, camera
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var tennis = Object.FindFirstObjectByType<TennisGame>();
            Transform heroRoot() => tennis.Player ? tennis.Player.transform.root : null;
            Transform racket = null, handR = null, head = null, ballT = GameObject.Find("Tennis ball")?.transform;
            void TennisProbe(Tracks t)
            {
                if (!racket) racket = Object.FindObjectsByType<Transform>(FindObjectsSortMode.None).FirstOrDefault(x => x.name.StartsWith("Racket") && x.gameObject.activeInHierarchy && x.GetComponentInChildren<Renderer>() && x.GetComponentInChildren<Renderer>().enabled);
                if (!handR) handR = Object.FindObjectsByType<Transform>(FindObjectsSortMode.None).FirstOrDefault(x => x.name == "RightHand" && x.gameObject.activeInHierarchy);
                if (!head && handR) head = Named(handR.root, n => n == "Head");
                if (ballT) t.Add("ball", ballT.position);
                if (racket) t.Add("racket", Rigid(racket));
                if (handR) t.Add("hand_r", handR.position);
                if (head) t.Add("head", head.position);
            }
            yield return Record("tennis_intro", 360, Main, TennisProbe);
            for (int k = 0; k < (int)(TennisPresentation.Length * 60); k++) yield return null;
            tennis.ConfigureMatch(TennisGame.Mode.Exhibition, null, "Rival", "CASUAL MATCH"); tennis.AutoPlay = true; tennis.AutoPlayLean = true;
            for (int k = 0; k < 120; k++) yield return null;
            racket = handR = head = null;
            yield return Record("tennis_rally", 600, Main, TennisProbe);
            tennis.AutoPlay = false;
            // golf: presentation (flyover + the golfer), then a drive: club, hands, ball, camera
            yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
            var golf = Object.FindFirstObjectByType<GolfGame>();
            Transform club = null, gHand = null, gHead = null;
            void GolfProbe(Tracks t)
            {
                if (!club) club = Object.FindObjectsByType<Transform>(FindObjectsSortMode.None).FirstOrDefault(x => x.name == "Club" && x.gameObject.activeInHierarchy);
                if (!gHand && club) gHand = Named(club.root, n => n == "RightHand");
                if (!gHead && club) gHead = Named(club.root, n => n == "Head");
                t.Add("ball", golf.BallPosition);
                if (club) t.Add("club", Rigid(club));
                if (gHand) t.Add("hand_r", gHand.position);
                if (gHead) t.Add("head", gHead.position);
            }
            for (int k = 0; k < 30; k++) yield return null;
            golf.PrepareNativeAddress(); golf.NativeReady(); golf.TryNativePresentation();
            yield return Record("golf_intro", 420, Main, GolfProbe);
            golf.PrepareNativeAddress(); golf.JumpToHole(7); golf.DropBall(golf.CurrentHole.Tee);
            for (int k = 0; k < 30; k++) yield return null;
            golf.NativeReady(); UnityEngine.Random.InitState(902); golf.NativeSwing(.78f);
            club = gHand = gHead = null;
            yield return Record("golf_swing", 420, Main, GolfProbe);
            // the golf signature shot (hole 12: the 30 fps camera + ball file)
            golf.PrepareNativeAddress(); golf.JumpToHole(12); golf.DropBall(golf.CurrentHole.Tee);
            for (int k = 0; k < 10; k++) yield return null;
            golf.NativeReady(); golf.TryNativePresentation();
            club = gHand = gHead = null;
            yield return Record("golf_hole12_intro", 600, Main, GolfProbe);
            // plaza: the hero walks a circle (Free Walk / Run) under the follow camera
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "fr60b", action = "start", sport = "hub", touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF" }));
            for (int i = 0; i < 1200 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find();
            for (int k = 0; k < 240; k++) yield return null;
            Transform pHand = null, pHead = null;
            yield return Record("plaza", 420, () => hub ? hub.Camera : Main(), t =>
            {
                if (hub && hub.Player) hub.Player.SetStick(Mathf.Sin(Time.time * .8f), Mathf.Cos(Time.time * .8f), .8f);
                if (!pHand && hub && hub.Player) { pHand = Named(hub.Player.transform, n => n == "RightHand"); pHead = Named(hub.Player.transform, n => n == "Head"); }
                if (hub && hub.Player) t.Add("hero", hub.Player.transform.position);
                if (pHand) t.Add("hand_r", pHand.position);
                if (pHead) t.Add("head", pHead.position);
            });
        }
    }
}
