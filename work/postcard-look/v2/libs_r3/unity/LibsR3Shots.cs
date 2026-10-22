using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using GolfArcade.Course;
using GolfArcade.Game;

// TEMPORARY (libs repair round 3): Game-view stills of SCRATCH hole FBXs (Assets/_LibsR3Probe/hole_NN.fbx) through the real GolfGame / HoleView.BuildFromModel / CameraRig / GolfAtmosphere,
// 900x1600 RenderTexture, TennisURP (in memory). Same camera rules as PostcardLookStills (landmark pos/look/fov or address ball/aim). Copied into the project only while
// heavy.sh's lock is held and removed on exit (work/postcard-look/v2/libs_r3/unity/run_shots.sh). Never writes ProjectSettings, never touches Resources/Course.
namespace LibsR3
{
    [InitializeOnLoad]
    public static class LibsR3Shots
    {
        const string Flag = "LibsR3Shots";
        const int W = 900, H = 1600;
        const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        [System.Serializable] sealed class Cfg { public ShotCfg[] shots; }
        [System.Serializable] sealed class ShotCfg { public string name; public int hole; public string kind; public float[] pos, look, ball, aim; public float fov; public bool putting; }
        static readonly List<ShotCfg> queue = new();
        static int warm, shotIndex = -1, wait, startFrame, settleTicks, currentHole = -1;
        static string outDir, assets;
        static RenderTexture rt; static Texture2D tex; static Camera cam; static GolfGame game; static CameraRig rig;
        static readonly List<string> report = new();

        static LibsR3Shots() { EditorApplication.update += Tick; }

        public static void Run()
        {
            outDir = System.Environment.GetEnvironmentVariable("LIBS_R3_OUT");
            string cfg = System.Environment.GetEnvironmentVariable("LIBS_R3_CFG");
            assets = System.Environment.GetEnvironmentVariable("LIBS_R3_ASSETS");
            if (string.IsNullOrEmpty(outDir) || string.IsNullOrEmpty(cfg) || string.IsNullOrEmpty(assets)) { Debug.LogError("[LibsR3] LIBS_R3_OUT / _CFG / _ASSETS missing"); EditorApplication.Exit(1); return; }
            Directory.CreateDirectory(outDir);
            SessionState.SetString(Flag + "out", outDir); SessionState.SetString(Flag + "cfg", cfg); SessionState.SetString(Flag + "assets", assets);
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            SessionState.SetBool(Flag, true);
            EditorApplication.isPlaying = true;
        }

        static void Say(string s) { report.Add(s); Debug.Log("[LibsR3] " + s); }

        static void Finish(int code)
        {
            try { File.WriteAllLines(Path.Combine(outDir, "shots_report.txt"), report.ToArray()); } catch (System.Exception e) { Debug.LogWarning(e.Message); }
            SessionState.SetBool(Flag, false);
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }

        static bool Settled()
        {
            int frames = Time.frameCount - startFrame, views = Object.FindObjectsByType<HoleView>(FindObjectsInactive.Include, FindObjectsSortMode.None).Length;
            return frames >= 5 && views == 1;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying) return;
            if (shotIndex < 0)
            {
                if (!HoleView.Current || ++warm < 90) return;
                outDir = SessionState.GetString(Flag + "out", outDir); assets = SessionState.GetString(Flag + "assets", assets);
                var c = JsonUtility.FromJson<Cfg>(File.ReadAllText(SessionState.GetString(Flag + "cfg", "")));
                queue.AddRange(c.shots.Select((s, i) => (s, i)).OrderBy(t => t.s.hole).ThenBy(t => t.i).Select(t => t.s));
                game = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>();
                cam = rig ? rig.GetComponentInChildren<Camera>() : Camera.main;
                foreach (var cv in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) cv.enabled = false;
                foreach (var guid in AssetDatabase.FindAssets("TennisURP t:UniversalRenderPipelineAsset"))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    if (Path.GetFileNameWithoutExtension(path) != "TennisURP") continue;
                    QualitySettings.renderPipeline = AssetDatabase.LoadAssetAtPath<UnityEngine.Rendering.RenderPipelineAsset>(path); Say("pipeline asset set in memory to TennisURP"); break;
                }
                rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
                tex = new Texture2D(W, H, TextureFormat.RGB24, false);
                Say($"{queue.Count} shot(s) -> {outDir}; probe assets {assets}");
                shotIndex = 0; currentHole = -1; wait = 1; return;
            }
            if (--wait > 0) return;
            if (shotIndex >= queue.Count) { Say("DONE"); Finish(0); return; }
            var s = queue[shotIndex];
            if (s.hole != currentHole) { LoadHole(s.hole); return; }
            if (!Settled() && ++settleTicks < 3000) return;
            settleTicks = 0;
            if (!swapped) { SwapModel(s.hole); wait = 10; return; }
            Take(s);
            shotIndex++; wait = 3;
        }

        static void LoadHole(int number)
        {
            int index = System.Array.FindIndex(GolfArcade.Course.Course.Postcards().Holes, h => h.Number == number);
            game.enabled = true; rig.enabled = true;
            startFrame = Time.frameCount; settleTicks = 0;
            typeof(GolfGame).GetMethod("StartHole", Private).Invoke(game, new object[] { index });
            currentHole = number; wait = 30; swapped = false;
        }

        static bool swapped;
        static void SwapModel(int n)
        {
            var probe = AssetDatabase.LoadAssetAtPath<GameObject>($"{assets}/hole_{n:00}.fbx");
            if (!probe) { Say($"hole {n}: NO probe model at {assets}/hole_{n:00}.fbx (installed model rendered)"); swapped = true; return; }
            var view = HoleView.Current;
            foreach (var extra in Object.FindObjectsByType<HoleView>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (extra != view) Object.DestroyImmediate(extra.gameObject);
            var old = view.transform.Find("Course model");
            if (old) Object.DestroyImmediate(old.gameObject);
            typeof(HoleView).GetMethod("BuildFromModel", Private).Invoke(view, new object[] { probe });
            int stale = 0;
            string installed = $"Assets/Resources/Course/hole_{n:00}.fbx";
            foreach (var mf in Object.FindObjectsByType<MeshFilter>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (mf.sharedMesh && AssetDatabase.GetAssetPath(mf.sharedMesh) == installed) stale++;
            int fromProbe = view.transform.Find("Course model") ? view.transform.Find("Course model").GetComponentsInChildren<MeshFilter>(true).Count(mf => mf.sharedMesh && AssetDatabase.GetAssetPath(mf.sharedMesh).StartsWith(assets)) : 0;
            Say($"hole {n}: swapped to the probe model {assets}/hole_{n:00}.fbx: {fromProbe} mesh(es) from the probe, {stale} MeshFilter(s) still on the installed model (must be 0)");
            swapped = true;
        }

        static void Take(ShotCfg s)
        {
            var golfer = (GolferView)typeof(GolfGame).GetField("golfer", Private).GetValue(game); if (golfer) golfer.SetVisible(false);
            var line = (LineRenderer)typeof(GolfGame).GetField("aimLine", Private).GetValue(game); if (line) line.enabled = false;
            var marker = (Transform)typeof(GolfGame).GetField("landingMarker", Private).GetValue(game); if (marker) marker.gameObject.SetActive(false);
            game.enabled = false; rig.enabled = false;
            var ballT = (Transform)typeof(GolfGame).GetField("ball", Private).GetValue(game);
            bool landmark = s.kind == "landmark" || (string.IsNullOrEmpty(s.kind) && s.pos != null);
            cam.fieldOfView = s.fov > 1 ? s.fov : 60;
            if (s.ball != null && s.ball.Length >= 2 && ballT) { ballT.gameObject.SetActive(true); ballT.position = HoleView.ToWorld(new CoursePoint(s.ball[0], s.ball[1]), 0.06); }
            if (landmark)
            {
                var pos = new Vector3(s.pos[0], s.pos[1], s.pos[2]); var look = new Vector3(s.look[0], s.look[1], s.look[2]);
                rig.transform.position = pos; rig.transform.rotation = Quaternion.LookRotation(look - pos, Vector3.up);
            }
            else
            {
                var ballAt = new CoursePoint(s.ball[0], s.ball[1]);
                var ball = HoleView.ToWorld(ballAt, 0.06);
                var aim = HoleView.ToWorld(new CoursePoint(s.aim[0], s.aim[1]), 0) - HoleView.ToWorld(ballAt, 0); aim.y = 0; aim.Normalize();
                rig.FrameAddress(ball, aim, s.putting); rig.SnapNext(); rig.ApplyFrame();
            }
            cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
            File.WriteAllBytes(Path.Combine(outDir, s.name + ".png"), tex.EncodeToPNG());
            Say($"hole {s.hole} {s.name} written");
            cam.fieldOfView = 60;
        }
    }
}
