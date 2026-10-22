#if UNITY_EDITOR
// Chat 10 (majestic-all-maps, G0 make-room): what each golf view costs and where the triangles come from. Clone only.
//   MAM_OUT=<dir> MAM_CAMS=<dir with hNN_cameras.json> [MAM_HOLES=7,8,...] [DREAM_WEATHER] GOLF_MUTE=1 Unity -projectPath <clone>
//     -executeMethod GolfArcade.EditorTools.MajesticGolfBudget.Run
// Per hole it re-poses every camera of hNN_cameras.json (the player's real views) at 1920x1080 and records the published render
// counters (triangles, draw calls, shadow casters; smallest non-zero over a few frames, chat 9's doubled-read rule) and a
// synchronous render+readback time. At the worst view it then breaks the frame down: counters with each instancer type,
// the characters and the shadows switched off in turn, plus the visible mesh-renderer triangles grouped by object family.
// Output: hNN_budget.json + budget.tsv (one row per hole x view).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class MajesticGolfBudget
    {
        const string Key = "MajesticGolfBudget";
        const int W = 1920, H = 1080;
        static IEnumerator<object> job; static int lastFrame = -1;
        static MajesticGolfBudget() { EditorApplication.update += Tick; }
        static readonly CultureInfo IC = CultureInfo.InvariantCulture;

        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("MAM_OUT"); if (string.IsNullOrEmpty(o)) throw new ArgumentException("MAM_OUT");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", Path.GetFullPath(o)); SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true;
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DREAM_WEATHER"))) Environment.SetEnvironmentVariable("DREAM_WEATHER", "Clear");
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DREAM_UTC"))) Environment.SetEnvironmentVariable("DREAM_UTC", "1792263600");
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity"); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false)) return;
            if (!EditorUtility.audioMasterMute) EditorUtility.audioMasterMute = true;
            if (!EditorApplication.isPlaying) return;
            if (AudioListener.volume != 0) AudioListener.volume = 0;
            if (Time.frameCount == lastFrame) return; lastFrame = Time.frameCount;
            try { job ??= Main(); if (!job.MoveNext()) { SessionState.SetBool(Key, false); EditorApplication.Exit(0); } }
            catch (Exception e) { Debug.LogException(e); SessionState.SetBool(Key, false); EditorApplication.Exit(1); }
        }

        static string Out => SessionState.GetString(Key + "out", "/tmp/mam_budget");
        static IEnumerable<object> Wait(int n) { for (int i = 0; i < n; i++) yield return null; }

        sealed class View { public string name; public Vector3 pos, fwd; public float fov; }
        static List<View> ReadViews(string file)
        {
            var list = new List<View>();
            foreach (System.Text.RegularExpressions.Match m in Regex.Matches(File.ReadAllText(file), "\"(\\w+)\": \\{\"pos\": \\[([^\\]]+)\\], \"fwd\": \\[([^\\]]+)\\], \"fov\": ([\\d.]+)"))
            {
                float[] P(string s) => s.Split(',').Select(x => float.Parse(x.Trim(), IC)).ToArray();
                var p = P(m.Groups[2].Value); var f = P(m.Groups[3].Value);
                list.Add(new View { name = m.Groups[1].Value, pos = new Vector3(p[0], p[1], p[2]), fwd = new Vector3(f[0], f[1], f[2]), fov = float.Parse(m.Groups[4].Value, IC) });
            }
            return list;
        }

        struct Count { public long tri, draw, casters, setpass; public double ms; }
        static Count last;
        static IEnumerable<object> Measure(Camera cam, RenderTexture rt)
        {
            var cat = Unity.Profiling.ProfilerCategory.Render;
            var tri = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Triangles Count");
            var draw = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Draw Calls Count");
            var pass = Unity.Profiling.ProfilerRecorder.StartNew(cat, "SetPass Calls Count");
            var cast = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Shadow Casters Count");
            var c = new Count();
            for (int i = 0; i < 8; i++)
            {
                yield return null;
                if (draw.LastValue > 0 && (c.draw == 0 || draw.LastValue < c.draw)) { c.tri = tri.LastValue; c.draw = draw.LastValue; c.setpass = pass.LastValue; c.casters = cast.LastValue; }
            }
            tri.Dispose(); draw.Dispose(); pass.Dispose(); cast.Dispose();
            var px = new Texture2D(1, 1, TextureFormat.RGBA32, false); var times = new List<double>();
            for (int i = 0; i < 10; i++)
            {
                var sw = System.Diagnostics.Stopwatch.StartNew();
                cam.targetTexture = rt; cam.Render(); var a = RenderTexture.active; RenderTexture.active = rt;
                px.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); px.Apply(); RenderTexture.active = a;
                sw.Stop(); if (i >= 2) times.Add(sw.Elapsed.TotalMilliseconds);
            }
            cam.targetTexture = rt; Object.DestroyImmediate(px);
            times.Sort(); c.ms = times[times.Count / 2]; last = c;
        }

        static IEnumerator<object> Main()
        {
            GolfGame golf = null; CameraRig rig = null;
            while (!golf || !rig || !HoleView.Current) { golf = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>(); yield return null; }
            golf.ChooseHoles(0); golf.Play();
            foreach (var o in Wait(30)) yield return o;
            var cam = rig.Camera;
            // the game camera renders into a 1080p target so the published counters are the 1080p frame
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; rt.Create();
            var camsDir = Environment.GetEnvironmentVariable("MAM_CAMS");
            var env = Environment.GetEnvironmentVariable("MAM_HOLES");
            var holes = string.IsNullOrEmpty(env) ? new[] { 7, 8, 9, 12, 15, 13, 14, 17, 18, 19, 20, 10, 16, 21, 22, 23 } : env.Split(',').Select(int.Parse).ToArray();
            var tsv = new StringBuilder("hole\tview\ttris\tdraws\tsetpass\tcasters\tsync_ms\n");
            foreach (var number in holes)
            {
                golf.enabled = true; rig.enabled = true;
                golf.JumpToHole(number); golf.DropBall(golf.CurrentHole.Tee);
                foreach (var o in Wait(40)) yield return o;
                golf.enabled = false; rig.enabled = false;
                foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
                var file = Path.Combine(camsDir, $"h{number:00}_cameras.json"); if (!File.Exists(file)) continue;
                var views = ReadViews(file);
                var results = new List<(View v, Count c)>();
                cam.targetTexture = rt; cam.aspect = W / (float)H;
                foreach (var v in views)
                {
                    cam.transform.SetPositionAndRotation(v.pos, Quaternion.LookRotation(v.fwd)); cam.fieldOfView = v.fov;
                    foreach (var o in Wait(3)) yield return o;
                    foreach (var o in Measure(cam, rt)) yield return o;
                    results.Add((v, last));
                    tsv.Append(string.Format(IC, "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6:F2}\n", number, v.name, last.tri, last.draw, last.setpass, last.casters, last.ms));
                }
                var worst = results.OrderByDescending(r => r.c.tri).First();
                var json = new StringBuilder();
                json.Append("{\n  \"hole\": ").Append(number).Append(",\n  \"views\": [\n");
                json.Append(string.Join(",\n", results.Select(r => string.Format(IC, "    {{\"view\": \"{0}\", \"tris\": {1}, \"draws\": {2}, \"setpass\": {3}, \"casters\": {4}, \"sync_ms\": {5:F2} }}", r.v.name, r.c.tri, r.c.draw, r.c.setpass, r.c.casters, r.c.ms))));
                json.Append("\n  ],\n  \"worst\": \"").Append(worst.v.name).Append("\",\n  \"breakdown\": [\n");

                // ---- breakdown at the worst view
                cam.transform.SetPositionAndRotation(worst.v.pos, Quaternion.LookRotation(worst.v.fwd)); cam.fieldOfView = worst.v.fov;
                foreach (var o in Wait(3)) yield return o;
                foreach (var o in Measure(cam, rt)) yield return o;
                var full = last; var parts = new List<string>();
                void Part(string what, Count c) => parts.Add(string.Format(IC, "    {{\"off\": \"{0}\", \"d_tris\": {1}, \"d_draws\": {2}, \"d_casters\": {3}, \"d_ms\": {4:F2} }}", what, full.tri - c.tri, full.draw - c.draw, full.casters - c.casters, full.ms - c.ms));
                // instancers and other drawing behaviours, by type
                var drawers = Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
                    .Where(b => b && b.enabled && Regex.IsMatch(b.GetType().Name, "Instances|Turf|Crowd|Grass|Plant|Botan|Scatter|Fringe|Majestic"))
                    .GroupBy(b => b.GetType().Name).ToList();
                foreach (var g in drawers)
                {
                    foreach (var b in g) b.enabled = false;
                    foreach (var o in Wait(3)) yield return o;
                    foreach (var o in Measure(cam, rt)) yield return o;
                    Part("behaviour:" + g.Key, last);
                    foreach (var b in g) b.enabled = true;
                }
                // characters
                var skinned = Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None).Where(r => r.enabled).ToList();
                foreach (var r in skinned) r.enabled = false;
                foreach (var o in Wait(3)) yield return o; foreach (var o in Measure(cam, rt)) yield return o; Part("characters", last);
                foreach (var r in skinned) r.enabled = true;
                // shadows
                var sun = RenderSettings.sun; var keep = sun ? sun.shadows : LightShadows.None;
                if (sun) sun.shadows = LightShadows.None;
                foreach (var o in Wait(3)) yield return o; foreach (var o in Measure(cam, rt)) yield return o; Part("shadows", last);
                if (sun) sun.shadows = keep;
                // visible mesh renderers by family (analytic: mesh triangles of renderers whose bounds are in the frustum)
                var planes = GeometryUtility.CalculateFrustumPlanes(cam);
                var fam = new Dictionary<string, (long tris, int n, long casterTris)>();
                foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
                {
                    if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                    var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh) continue;
                    bool vis = GeometryUtility.TestPlanesAABB(planes, r.bounds);
                    long t = 0; for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) t += mf.sharedMesh.GetIndexCount(s) / 3;
                    var key = Regex.Replace(r.transform.root.name + "/" + r.name, "[0-9_() ]+$", "");
                    key = Regex.Replace(key, "\\d+", "#");
                    fam.TryGetValue(key, out var a);
                    fam[key] = (a.tris + (vis ? t : 0), a.n + (vis ? 1 : 0), a.casterTris + (r.shadowCastingMode != ShadowCastingMode.Off ? t : 0));
                }
                foreach (var kv in fam.Where(k => k.Value.tris > 0 || k.Value.casterTris > 20000).OrderByDescending(k => k.Value.tris).Take(40))
                    parts.Add(string.Format(IC, "    {{\"family\": \"{0}\", \"visible_tris\": {1}, \"visible_renderers\": {2}, \"caster_tris_all\": {3}}}", kv.Key.Replace("\"", "'"), kv.Value.tris, kv.Value.n, kv.Value.casterTris));
                json.Append(string.Join(",\n", parts)).Append("\n  ],\n");
                json.Append(string.Format(IC, "  \"full_at_worst\": {{\"tris\": {0}, \"draws\": {1}, \"casters\": {2}, \"sync_ms\": {3:F2} }}\n}}\n", full.tri, full.draw, full.casters, full.ms));
                File.WriteAllText(Path.Combine(Out, $"h{number:00}_budget.json"), json.ToString());
                File.WriteAllText(Path.Combine(Out, "budget.tsv"), tsv.ToString());
                foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = true;
                cam.targetTexture = null;
                Debug.Log($"[MajesticGolfBudget] h{number:00} done worst={worst.v.name} tris={worst.c.tri}");
            }
            rt.Release(); Object.DestroyImmediate(rt);
            Debug.Log("[MajesticGolfBudget] all done");
        }
    }
}
#endif
