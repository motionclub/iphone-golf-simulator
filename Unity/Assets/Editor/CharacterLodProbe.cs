#if UNITY_EDITOR
// CHARACTER LOD (character-lod chat, 2026-10-17): golf measurements, LOD0 identity, pop A/B, film frames, perf proxy, cache bake.
// Clone only:  CLOD_OUT=<dir> CLOD_CAMS=<dir with hNN_cameras.json> [CLOD_HOLES=7,12] [CLOD_STEPS=measure,identity,pop,film,perf,bake]
//              GOLF_MUTE=1 Unity -projectPath <clone> -executeMethod GolfArcade.EditorTools.CharacterLodProbe.Run
// Output: report.json, parts.tsv, views.tsv (hole x view x level: frame tris, character tris), PNG proofs, film/ frames,
// HeroLodCache.bytes (every LOD computed this session, for Resources/CharacterLOD/).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using GolfArcade.CharacterLod;
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
    public static class CharacterLodProbe
    {
        const string Key = "CharacterLodProbe";
        const int W = 1920, H = 1080;
        static IEnumerator<object> job; static int lastFrame = -1;
        static readonly CultureInfo IC = CultureInfo.InvariantCulture;
        static CharacterLodProbe() { EditorApplication.update += Tick; }

        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("CLOD_OUT"); if (string.IsNullOrEmpty(o)) throw new ArgumentException("CLOD_OUT");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", Path.GetFullPath(o)); SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true;
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DREAM_WEATHER"))) Environment.SetEnvironmentVariable("DREAM_WEATHER", "Clear");
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DREAM_UTC"))) Environment.SetEnvironmentVariable("DREAM_UTC", "1792263600");
            PlayerSettings.enableFrameTimingStats = true;   // clone only: GPU frame times for the perf step
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
            catch (Exception e) { Debug.LogException(e); File.AppendAllText(Path.Combine(Out, "errors.txt"), e + "\n"); SessionState.SetBool(Key, false); EditorApplication.Exit(1); }
        }

        static string Out => SessionState.GetString(Key + "out", "/tmp/clod");
        static IEnumerable<object> Wait(int n) { for (int i = 0; i < n; i++) yield return null; }
        static bool Step(string s) { var e = Environment.GetEnvironmentVariable("CLOD_STEPS"); return string.IsNullOrEmpty(e) || e.Split(',').Contains(s); }
        static void Log(string s) { Debug.Log("[CharacterLod] " + s); File.AppendAllText(Path.Combine(Out, "log.txt"), s + "\n"); }

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

        struct Count { public long tri, draw, casters; public double ms; }
        static Count last;
        static IEnumerable<object> Measure(Camera cam, RenderTexture rt, bool timed = false)
        {
            // per-frame published counters, then the MODE: single frames read 0 or a doubled frame now and then
            var cat = Unity.Profiling.ProfilerCategory.Render;
            var tri = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Triangles Count");
            var draw = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Draw Calls Count");
            var cast = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Shadow Casters Count");
            var reads = new List<(long t, long d, long c)>();
            for (int i = 0; i < 20; i++) { yield return null; if (draw.LastValue > 0) reads.Add((tri.LastValue, draw.LastValue, cast.LastValue)); }
            tri.Dispose(); draw.Dispose(); cast.Dispose();
            var c = new Count();
            if (reads.Count > 0)
            {
                var mode = reads.GroupBy(r => r).OrderByDescending(g => g.Count()).ThenBy(g => g.Key.t).First().Key;
                c.tri = mode.t; c.draw = mode.d; c.casters = mode.c;
            }
            if (timed)
            {
                var px = new Texture2D(1, 1, TextureFormat.RGBA32, false); var times = new List<double>();
                for (int i = 0; i < 14; i++)
                {
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    cam.targetTexture = rt; cam.Render(); var a = RenderTexture.active; RenderTexture.active = rt;
                    px.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); px.Apply(); RenderTexture.active = a;
                    sw.Stop(); if (i >= 4) times.Add(sw.Elapsed.TotalMilliseconds);
                }
                Object.DestroyImmediate(px); times.Sort(); c.ms = times[times.Count / 2];
            }
            last = c;
        }

        static List<Renderer> HeroRenderers() =>
            Object.FindObjectsByType<Tennis.MatchHeroLook>(FindObjectsSortMode.None).SelectMany(l => l.GetComponentsInChildren<Renderer>()).Where(r => r.enabled).ToList();

        /// Frame tris with the heroes, and without them (every renderer under a MatchHeroLook switched off).
        static IEnumerable<object> CharacterCost(Camera cam, RenderTexture rt, Action<long, long, long, long> done)
        {
            foreach (var o in Measure(cam, rt)) yield return o; var full = last;
            var rs = HeroRenderers(); foreach (var r in rs) r.enabled = false;
            foreach (var o in Wait(2)) yield return o;
            foreach (var o in Measure(cam, rt)) yield return o; var none = last;
            foreach (var r in rs) r.enabled = true;
            foreach (var o in Wait(2)) yield return o;
            done(full.tri, full.tri - none.tri, full.draw - none.draw, full.casters - none.casters);
        }

        static Texture2D Grab(Camera cam, RenderTexture rt)
        {
            cam.targetTexture = rt; cam.Render();
            var a = RenderTexture.active; RenderTexture.active = rt;
            var t = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false); t.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); t.Apply();
            RenderTexture.active = a; return t;
        }
        static (int differ, int maxd, double mean) Diff(Texture2D a, Texture2D b, int threshold = 0)
        {
            var pa = a.GetPixels32(); var pb = b.GetPixels32(); int n = 0, mx = 0; double sum = 0;
            for (int i = 0; i < pa.Length; i++)
            {
                int d = Math.Max(Math.Abs(pa[i].r - pb[i].r), Math.Max(Math.Abs(pa[i].g - pb[i].g), Math.Abs(pa[i].b - pb[i].b)));
                if (d > threshold) n++; if (d > mx) mx = d; sum += d;
            }
            return (n, mx, sum / pa.Length);
        }
        static void Save(Texture2D t, string name) => File.WriteAllBytes(Path.Combine(Out, name), name.EndsWith(".jpg") ? t.EncodeToJPG(88) : t.EncodeToPNG());

        static IEnumerator<object> Main()
        {
            GolfGame golf = null; CameraRig rig = null;
            while (!golf || !rig || !HoleView.Current) { golf = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>(); yield return null; }
            golf.ChooseHoles(0); golf.Play();
            foreach (var o in Wait(30)) yield return o;
            var cam = rig.Camera;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; rt.Create();
            var camsDir = Environment.GetEnvironmentVariable("CLOD_CAMS");
            var env = Environment.GetEnvironmentVariable("CLOD_HOLES");
            var holes = string.IsNullOrEmpty(env) ? new[] { 7, 8, 9, 12, 15, 13, 14, 17, 18, 19, 20, 10, 16, 21, 22, 23 } : env.Split(',').Select(int.Parse).ToArray();
            var report = new StringBuilder("{\n");

            // ---- the hero at hole 7's tee, its LODs ready ----
            golf.JumpToHole(holes[0]); golf.DropBall(golf.CurrentHole.Tee);
            float t0 = Time.realtimeSinceStartup; HeroLod lod = null;
            while (Time.realtimeSinceStartup - t0 < 120)
            {
                lod = Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).FirstOrDefault();
                if (lod && lod.Ready) break; yield return null;
            }
            if (!lod) throw new Exception("no HeroLod attached to the golfer");
            Log($"HeroLod ready={lod.Ready} after {Time.realtimeSinceStartup - t0:F1}s  cacheHits={HeroLodLibrary.CacheHits} misses={HeroLodLibrary.CacheMisses}");
            var parts = new StringBuilder("renderer\ttype\tmesh\tenabled\tactive\tshadow\tsubmeshes\tmaterials\ttris_by_level\tready\n");
            foreach (var r in lod.GetComponentsInChildren<Renderer>(true))
            {
                var p = lod.Parts.FirstOrDefault(x => x.renderer == r);
                Mesh m = r is SkinnedMeshRenderer s ? s.sharedMesh : r.GetComponent<MeshFilter>()?.sharedMesh;
                long tris = 0; if (m) for (int i = 0; i < m.subMeshCount; i++) tris += m.GetIndexCount(i) / 3;
                parts.Append(string.Join("\t", r.name, r.GetType().Name, m ? m.name : "-", r.enabled, r.gameObject.activeInHierarchy, r.shadowCastingMode, m ? m.subMeshCount : 0,
                    string.Join("|", r.sharedMaterials.Select(x => x ? x.shader.name + ":" + x.passCount : "null")),
                    p.renderer ? string.Join("/", p.tris) : tris.ToString(), p.renderer ? p.ready : false)).Append('\n');
            }
            File.WriteAllText(Path.Combine(Out, "parts.tsv"), parts.ToString());
            int VisibleTris(HeroLod h, int l) => h.Parts.Where(p => p.renderer && p.renderer.enabled && p.renderer.gameObject.activeInHierarchy).Sum(p => p.ready ? p.tris[l] : p.tris[0]);
            report.Append("  \"hero_visible_tris\": [").Append(string.Join(", ", Enumerable.Range(0, HeroLod.Levels).Select(l => VisibleTris(lod, l)))).Append("],\n");
            report.Append("  \"bands\": [").Append(string.Join(", ", HeroLod.Bands.Select(b => b.ToString(IC)))).Append(string.Format(IC, "], \"hysteresis\": {0},\n", HeroLod.Hysteresis));

            // ---- mesh API facts we rely on ----
            {
                var any = lod.Parts.First(p => p.ready);
                Mesh l0 = any.renderer is SkinnedMeshRenderer s0 ? s0.sharedMesh : null;
                Log($"probe part {any.renderer.name}: {string.Join("/", any.tris)}");
            }

            golf.enabled = false; rig.enabled = false;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            cam.targetTexture = rt; cam.aspect = W / (float)H;

            // ---- measure: every view of every hole, distance LOD vs LOD0 everywhere ----
            if (Step("measure"))
            {
                var tsv = new StringBuilder("hole\tview\tscreen_h\tlevel\tframe_tris_lod0\tchar_tris_lod0\tchar_draws_lod0\tchar_casters_lod0\tframe_tris\tchar_tris\tchar_draws\tchar_casters\n");
                foreach (var number in holes)
                {
                    golf.enabled = true; rig.enabled = true;
                    golf.JumpToHole(number); golf.DropBall(golf.CurrentHole.Tee);
                    foreach (var o in Wait(40)) yield return o;
                    golf.enabled = false; rig.enabled = false;
                    foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
                    // the golfer's LODs for this hole's build (a new hole may rebuild the figure)
                    t0 = Time.realtimeSinceStartup;
                    while (Time.realtimeSinceStartup - t0 < 60 && Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).Any(l => !l.Ready)) yield return null;
                    var file = Path.Combine(camsDir, $"h{number:00}_cameras.json"); if (!File.Exists(file)) continue;
                    cam.targetTexture = rt; cam.aspect = W / (float)H;
                    var only = Environment.GetEnvironmentVariable("CLOD_VIEWS");
                    foreach (var v in ReadViews(file).Where(v => string.IsNullOrEmpty(only) || only.Split(',').Any(p => v.name.StartsWith(p))))
                    {
                        cam.transform.SetPositionAndRotation(v.pos, Quaternion.LookRotation(v.fwd)); cam.fieldOfView = v.fov;
                        long[] a = new long[4], b = new long[4]; float sh = 0; int lv = 0;
                        HeroLod.ForceLevel = 0; foreach (var o in Wait(3)) yield return o;
                        foreach (var o in CharacterCost(cam, rt, (f, t, d, c) => { a[0] = f; a[1] = t; a[2] = d; a[3] = c; })) yield return o;
                        HeroLod.ForceLevel = -1; foreach (var o in Wait(3)) yield return o;
                        var l = Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).FirstOrDefault(); if (l) { sh = l.ScreenHeight; lv = l.Level; }
                        foreach (var o in CharacterCost(cam, rt, (f, t, d, c) => { b[0] = f; b[1] = t; b[2] = d; b[3] = c; })) yield return o;
                        tsv.Append(string.Format(IC, "{0}\t{1}\t{2:F3}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\n", number, v.name, sh, lv, a[0], a[1], a[2], a[3], b[0], b[1], b[2], b[3]));
                    }
                    File.WriteAllText(Path.Combine(Out, "views.tsv"), tsv.ToString());
                    Log($"measured hole {number}");
                }
                HeroLod.ForceLevel = -1;
            }

            // a fixed frame for the image steps: hole 7 tee, time frozen so only the hero LOD can change pixels
            golf.enabled = true; rig.enabled = true;
            golf.JumpToHole(holes[0]); golf.DropBall(golf.CurrentHole.Tee);
            foreach (var o in Wait(40)) yield return o;
            golf.enabled = false; rig.enabled = false;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            t0 = Time.realtimeSinceStartup;
            while (Time.realtimeSinceStartup - t0 < 60 && Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).Any(l => !l.Ready)) yield return null;
            lod = Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).First();
            var views7 = ReadViews(Path.Combine(camsDir, $"h{holes[0]:00}_cameras.json"));
            var tee = views7.First(v => v.name == "tee");
            var heroAt = lod.transform.position; var headT = lod.GetComponentsInChildren<Transform>().First(t => t.name == "Head");
            var aim = (heroAt + headT.position) * .5f;
            float timeScale = Time.timeScale; Time.timeScale = 0;
            foreach (var o in Wait(5)) yield return o;

            // ---- identity: CHARACTER_LOD off vs on at LOD0 views (close-ups, locker-like framing) ----
            if (Step("identity"))
            {
                var closeViews = new List<(string, Vector3, Vector3, float)>
                {
                    ("closeup_front", aim + lod.transform.forward * 2.1f + Vector3.up * .2f, -lod.transform.forward, 40f),
                    ("closeup_face", headT.position + lod.transform.forward * .9f, -lod.transform.forward, 35f),
                    ("closeup_side", aim + lod.transform.right * 2.4f, -lod.transform.right, 45f),
                };
                var sb = new StringBuilder();
                foreach (var (name, pos, fwd, fov) in closeViews)
                {
                    cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(fwd)); cam.fieldOfView = fov;
                    // off / on / off, three times: the noise floor (off vs off) catches what the frozen clock does not stop (blinks)
                    int best = int.MaxValue, floor = int.MaxValue, mxBest = 0; int level = 0; float sh = 0; bool originals = true;
                    Texture2D keep = null;
                    for (int rep = 0; rep < 3; rep++)
                    {
                        HeroLod.Enabled = false; foreach (var o in Wait(4)) yield return o; var off1 = Grab(cam, rt);
                        HeroLod.Enabled = true; HeroLod.ForceLevel = -1; foreach (var o in Wait(4)) yield return o;
                        var on = Grab(cam, rt); level = lod.Level; sh = lod.ScreenHeight; originals &= lod.OriginalsOnly;
                        HeroLod.Enabled = false; foreach (var o in Wait(4)) yield return o; var off2 = Grab(cam, rt); HeroLod.Enabled = true;
                        var d = Diff(off1, on); var f = Diff(off1, off2);
                        if (d.differ < best) { best = d.differ; mxBest = d.maxd; } floor = Math.Min(floor, f.differ);
                        if (keep) Object.DestroyImmediate(keep); keep = on; Object.DestroyImmediate(off1); Object.DestroyImmediate(off2);
                    }
                    Save(keep, $"identity_{name}.png"); Object.DestroyImmediate(keep);
                    sb.Append(string.Format(IC, "    {{\"view\": \"{0}\", \"screen_h\": {1:F3}, \"level\": {2}, \"originals_only\": {3}, \"pixels_differ_min_of_3\": {4}, \"max_diff\": {5}, \"noise_floor_off_vs_off\": {6} }},\n",
                        name, sh, level, originals ? "true" : "false", best, mxBest, floor));
                }
                report.Append("  \"identity\": [\n").Append(sb.ToString().TrimEnd(',', '\n')).Append("\n  ],\n");
            }

            // ---- pop: the same frozen frame at both levels of each swap, right at the swap distance ----
            if (Step("pop"))
            {
                var sb = new StringBuilder();
                float tanHalf = Mathf.Tan(tee.fov * .5f * Mathf.Deg2Rad); float height = 1.75f * lod.transform.lossyScale.y;
                var dir = (tee.pos - aim); dir.y = 0; dir = dir.normalized;   // the tee camera's side of the hero
                var swaps = HeroLod.Bands.Select((b, i) => ($"swap{i}{i + 1}", b, i, i + 1)).ToList();
                swaps.Add(("tee_0_vs_chosen", -1f, 0, -1));   // B = the level the distance rule picks at the tee
                foreach (var (name, frac, la, lb) in swaps)
                {
                    if (frac > 0)
                    {
                        float dist = height / (2 * frac * tanHalf);
                        cam.transform.SetPositionAndRotation(aim + dir * dist + Vector3.up * dist * .12f, Quaternion.LookRotation(-dir - Vector3.up * .12f)); cam.fieldOfView = tee.fov;
                    }
                    else { cam.transform.SetPositionAndRotation(tee.pos, Quaternion.LookRotation(tee.fwd)); cam.fieldOfView = tee.fov; }
                    HeroLod.ForceLevel = la; foreach (var o in Wait(4)) yield return o; var A = Grab(cam, rt);
                    HeroLod.ForceLevel = lb; foreach (var o in Wait(4)) yield return o; var B = Grab(cam, rt);
                    int shown = lod.Level;
                    // hero pixels: where the frame changes when the hero is switched off
                    var rs = HeroRenderers(); foreach (var r in rs) r.enabled = false; foreach (var o in Wait(3)) yield return o;
                    var E = Grab(cam, rt); foreach (var r in rs) r.enabled = true;
                    var pa = A.GetPixels32(); var pb = B.GetPixels32(); var pe = E.GetPixels32();
                    int hero = 0, differ = 0, strong = 0, mx = 0; int x0 = W, y0 = H, x1 = 0, y1 = 0;
                    for (int i = 0; i < pa.Length; i++)
                    {
                        int de = Math.Max(Math.Abs(pa[i].r - pe[i].r), Math.Max(Math.Abs(pa[i].g - pe[i].g), Math.Abs(pa[i].b - pe[i].b)));
                        if (de <= 2) continue; hero++;
                        int x = i % W, y = i / W; x0 = Math.Min(x0, x); x1 = Math.Max(x1, x); y0 = Math.Min(y0, y); y1 = Math.Max(y1, y);
                        int d = Math.Max(Math.Abs(pa[i].r - pb[i].r), Math.Max(Math.Abs(pa[i].g - pb[i].g), Math.Abs(pa[i].b - pb[i].b)));
                        if (d > 8) differ++; if (d > 32) strong++; if (d > mx) mx = d;
                    }
                    // side-by-side crop around the hero: A | B | 4x |A-B|
                    int pad = 20; x0 = Math.Max(0, x0 - pad); y0 = Math.Max(0, y0 - pad); x1 = Math.Min(W - 1, x1 + pad); y1 = Math.Min(H - 1, y1 + pad);
                    int cw = Math.Max(1, x1 - x0 + 1), ch = Math.Max(1, y1 - y0 + 1);
                    var sheet = new Texture2D(cw * 3, ch, TextureFormat.RGB24, false);
                    for (int y = 0; y < ch; y++) for (int x = 0; x < cw; x++)
                    {
                        int i = (y0 + y) * W + x0 + x; sheet.SetPixel(x, y, pa[i]); sheet.SetPixel(cw + x, y, pb[i]);
                        int d = Math.Min(255, 4 * Math.Max(Math.Abs(pa[i].r - pb[i].r), Math.Max(Math.Abs(pa[i].g - pb[i].g), Math.Abs(pa[i].b - pb[i].b))));
                        sheet.SetPixel(2 * cw + x, y, new Color32((byte)d, (byte)d, (byte)d, 255));
                    }
                    sheet.Apply(); Save(sheet, $"pop_{name}.png"); Object.DestroyImmediate(sheet);
                    sb.Append(string.Format(IC, "    {{\"swap\": \"{0}\", \"levels\": [{1}, {2}], \"hero_px\": {3}, \"differ_gt8\": {4}, \"differ_gt32\": {5}, \"max_diff\": {6}, \"share_gt8\": {7:F4} }},\n",
                        name, la, shown, hero, differ, strong, mx, hero > 0 ? differ / (double)hero : 0));
                    Object.DestroyImmediate(A); Object.DestroyImmediate(B); Object.DestroyImmediate(E);
                }
                HeroLod.ForceLevel = -1;
                report.Append("  \"pop\": [\n").Append(sb.ToString().TrimEnd(',', '\n')).Append("\n  ],\n");
            }
            Time.timeScale = timeScale;

            // ---- film: a dolly from a close-up out past both swaps and back, animation running, distance LOD live ----
            if (Step("film"))
            {
                var dir = (tee.pos - aim); dir.y = 0; dir = dir.normalized;
                var side = Vector3.Cross(Vector3.up, dir).normalized;
                Directory.CreateDirectory(Path.Combine(Out, "film"));
                var frt = new RenderTexture(1280, 720, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; frt.Create();
                var levels = new StringBuilder("frame\tdist\tscreen_h\tlevel\n");
                int frames = 900;   // 15 s at 60 fps
                for (int f = 0; f < frames; f++)
                {
                    float u = f / (float)(frames - 1); float k = u < .5f ? u * 2 : (1 - u) * 2;   // out and back
                    float dist = 1.6f * Mathf.Pow(60f / 1.6f, k * k * (3 - 2 * k));   // log dolly 1.6 -> 60 m: every band, the last at ~47 m
                    var pos = aim + (dir * Mathf.Cos(u * 1.2f) + side * Mathf.Sin(u * 1.2f)) * dist + Vector3.up * (.15f + dist * .1f);
                    cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(aim - pos)); cam.fieldOfView = 50;
                    yield return null;   // LateUpdate picks the level for this camera
                    var t = Grab(cam, frt); Save(t, $"film/f{f:0000}.jpg"); Object.DestroyImmediate(t);
                    levels.Append(string.Format(IC, "{0}\t{1:F2}\t{2:F3}\t{3}\n", f, dist, lod.ScreenHeight, lod.Level));
                }
                File.WriteAllText(Path.Combine(Out, "film_levels.tsv"), levels.ToString());
                frt.Release(); Object.DestroyImmediate(frt);
                cam.targetTexture = rt;
            }

            // ---- perf proxy: synchronous 1080p render of the tee views, CHARACTER_LOD off vs on (interleaved rounds) ----
            if (Step("perf"))
            {
                var sb = new StringBuilder();
                var perfViews = views7.Where(v => v.name == "tee" || v.name.StartsWith("driveGood_0") || v.name == "greenBack").ToList();
                var sums = new Dictionary<string, List<double>>();
                for (int round = 0; round < 4; round++)
                    foreach (var on in new[] { false, true })
                        foreach (var v in perfViews)
                        {
                            HeroLod.Enabled = on; cam.transform.SetPositionAndRotation(v.pos, Quaternion.LookRotation(v.fwd)); cam.fieldOfView = v.fov;
                            foreach (var o in Wait(3)) yield return o;
                            foreach (var o in Measure(cam, rt, true)) yield return o;
                            var key = v.name + (on ? "_on" : "_off"); if (!sums.TryGetValue(key, out var lst)) sums[key] = lst = new List<double>();
                            lst.Add(last.ms); sb.Append(string.Format(IC, "{0}\t{1}\t{2}\t{3}\t{4:F2}\n", round, v.name, on ? "on" : "off", last.tri, last.ms));
                        }
                HeroLod.Enabled = true;
                File.WriteAllText(Path.Combine(Out, "perf.tsv"), "round\tview\tlod\ttris\tsync_ms\n" + sb);
                report.Append("  \"perf_median_ms\": {").Append(string.Join(", ", sums.Select(kv => string.Format(IC, "\"{0}\": {1:F2}", kv.Key, kv.Value.OrderBy(x => x).ElementAt(kv.Value.Count / 2))))).Append("},\n");
            }

            // ---- GPU/CPU frame time (FrameTimingManager), automatic 1080p frames of the tee view: LOD off vs on, solo and a 4-golfer party ----
            if (Step("gpu"))
            {
                var tim = new FrameTiming[1]; var sb = new StringBuilder(); var med = new List<string>();
                cam.transform.SetPositionAndRotation(tee.pos, Quaternion.LookRotation(tee.fwd)); cam.fieldOfView = tee.fov; cam.targetTexture = rt;
                var party = new List<GolferView>();
                foreach (var crowd in new[] { 1, 4 })
                {
                    while (party.Count < crowd - 1)
                    {
                        var st = GolferView.Look.Player; var hl = GolferStyle.Hero; hl.Female = party.Count % 2 == 0; st.Hero = hl;
                        var g = GolferView.CreateSpectator(golf.transform, st); g.transform.position = heroAt - lod.transform.forward * (1.5f + party.Count) + lod.transform.right * (1.2f * party.Count - 1);
                        party.Add(g);
                    }
                    t0 = Time.realtimeSinceStartup;
                    while (Time.realtimeSinceStartup - t0 < 120 && Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).Any(l => !l.Ready)) yield return null;
                    var gpu = new Dictionary<bool, List<double>> { [false] = new(), [true] = new() }; var cpu = new Dictionary<bool, List<double>> { [false] = new(), [true] = new() };
                    for (int round = 0; round < 6; round++)
                        foreach (var on in new[] { false, true })
                        {
                            HeroLod.Enabled = on; foreach (var o in Wait(10)) yield return o;
                            for (int i = 0; i < 40; i++)
                            {
                                FrameTimingManager.CaptureFrameTimings(); yield return null;
                                if (FrameTimingManager.GetLatestTimings(1, tim) > 0 && tim[0].gpuFrameTime > 0) { gpu[on].Add(tim[0].gpuFrameTime); cpu[on].Add(tim[0].cpuFrameTime); }
                            }
                        }
                    double M(List<double> l) => l.Count == 0 ? -1 : l.OrderBy(x => x).ElementAt(l.Count / 2);
                    med.Add(string.Format(IC, "\"golfers_{0}\": {{\"gpu_ms_off\": {1:F2}, \"gpu_ms_on\": {2:F2}, \"cpu_ms_off\": {3:F2}, \"cpu_ms_on\": {4:F2}, \"samples\": {5}}}",
                        crowd, M(gpu[false]), M(gpu[true]), M(cpu[false]), M(cpu[true]), gpu[true].Count));
                }
                HeroLod.Enabled = true;
                foreach (var g in party) Object.Destroy(g.gameObject);
                report.Append("  \"frame_timing_tee_1080p\": {").Append(string.Join(", ", med)).Append("},\n");
            }

            // ---- the female golfer too (a party golfer beside the tee), then bake every LOD computed this session ----
            if (Step("bake"))
            {
                var style = GolferView.Look.Player; var hl = GolferStyle.Hero; hl.Female = !hl.Female; style.Hero = hl;
                var other = GolferView.CreatePlayer(golf.transform, style); other.transform.position = heroAt + lod.transform.right * 2f;
                t0 = Time.realtimeSinceStartup;
                while (Time.realtimeSinceStartup - t0 < 120 && (Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).Length < 2 || Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).Any(l => !l.Ready))) yield return null;
                foreach (var l in Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None))
                    Log($"hero {l.name} ready={l.Ready} visible tris by level {string.Join("/", Enumerable.Range(0, HeroLod.Levels).Select(x => VisibleTris(l, x)))}");
                File.WriteAllBytes(Path.Combine(Out, "HeroLodCache.bytes"), HeroLodCache.Write(HeroLodLibrary.Computed));
                Log($"baked {HeroLodLibrary.Computed.Count} meshes");
            }
            report.Append(string.Format(IC, "  \"cache\": {{\"hits\": {0}, \"misses\": {1}}}\n}}\n", HeroLodLibrary.CacheHits, HeroLodLibrary.CacheMisses));
            File.WriteAllText(Path.Combine(Out, "report.json"), report.ToString());
            rt.Release(); Object.DestroyImmediate(rt);
            Log("all done");
        }
    }
}
#endif

#if UNITY_EDITOR
namespace GolfArcade.EditorTools
{
    using System;
    using System.Collections.Generic;
    using System.Globalization;
    using System.IO;
    using System.Linq;
    using System.Text;
    using GolfArcade.CharacterLod;
    using GolfArcade.Tennis;
    using UnityEditor;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using Object = UnityEngine.Object;

    /// Tennis: the two match heroes from the production gameplay camera (near player, far opponent), CHARACTER_LOD off vs on,
    /// plus a close-up identity check. CLOD_OUT=<dir> ... -executeMethod GolfArcade.EditorTools.CharacterLodTennisProbe.Run
    [InitializeOnLoad]
    public static class CharacterLodTennisProbe
    {
        const string Key = "CharacterLodTennisProbe";
        static IEnumerator<object> job; static int lastFrame = -1;
        static readonly CultureInfo IC = CultureInfo.InvariantCulture;
        static CharacterLodTennisProbe() { EditorApplication.update += Tick; }
        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("CLOD_OUT"); if (string.IsNullOrEmpty(o)) throw new ArgumentException("CLOD_OUT");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", Path.GetFullPath(o)); SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true;
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity"); EditorApplication.isPlaying = true;
        }
        static string Out => SessionState.GetString(Key + "out", "/tmp/clod");
        static void Tick()
        {
            if (!SessionState.GetBool(Key, false)) return;
            if (!EditorUtility.audioMasterMute) EditorUtility.audioMasterMute = true;
            if (!EditorApplication.isPlaying) return;
            if (AudioListener.volume != 0) AudioListener.volume = 0;
            if (Time.frameCount == lastFrame) return; lastFrame = Time.frameCount;
            try { job ??= Main(); if (!job.MoveNext()) { SessionState.SetBool(Key, false); EditorApplication.Exit(0); } }
            catch (Exception e) { Debug.LogException(e); File.AppendAllText(Path.Combine(Out, "tennis_errors.txt"), e + "\n"); SessionState.SetBool(Key, false); EditorApplication.Exit(1); }
        }
        static void Log(string s) { Debug.Log("[CharacterLod] " + s); File.AppendAllText(Path.Combine(Out, "tennis_log.txt"), s + "\n"); }
        static IEnumerable<object> Wait(int n) { for (int i = 0; i < n; i++) yield return null; }
        static long tris, draws;
        static IEnumerable<object> Measure()
        {
            var cat = Unity.Profiling.ProfilerCategory.Render;
            var t = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Triangles Count"); var d = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Draw Calls Count");
            tris = 0; draws = 0;
            for (int i = 0; i < 8; i++) { yield return null; if (d.LastValue > 0 && (draws == 0 || d.LastValue < draws)) { tris = t.LastValue; draws = d.LastValue; } }
            t.Dispose(); d.Dispose();
        }
        static IEnumerator<object> Main()
        {
            TennisGame game = null;
            while (!game || !game.Initialized) { game = Object.FindFirstObjectByType<TennisGame>(); yield return null; }
            game.SelectCharacter(false); game.ConfigureMatch(TennisGame.Mode.Campaign, "Nadia", "Nadia", "CHARACTER LOD PROOF");
            var pres = game.GetComponent<TennisPresentation>(); if (pres) pres.Finish(); game.AutoPlay = false;
            float t0 = Time.realtimeSinceStartup;
            while (Time.realtimeSinceStartup - t0 < 120 && (Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).Length < 2 || Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None).Any(l => !l.Ready))) yield return null;
            foreach (var o in Wait(60)) yield return o;
            var cam = game.GameplayCamera;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; rt.Create();
            cam.targetTexture = rt; cam.aspect = 1920f / 1080f;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            var sb = new StringBuilder("{\n");
            var heroes = Object.FindObjectsByType<HeroLod>(FindObjectsSortMode.None);
            foreach (var h in heroes)
                Log($"hero {h.transform.root.name}/{h.name} level={h.Level} screen_h={h.ScreenHeight:F3} visible tris by level {string.Join("/", Enumerable.Range(0, HeroLod.Levels).Select(l => h.Parts.Where(p => p.renderer && p.renderer.enabled && p.renderer.gameObject.activeInHierarchy).Sum(p => p.ready ? p.tris[l] : p.tris[0])))}");
            var rows = new List<string>();
            for (int round = 0; round < 3; round++)
                foreach (var on in new[] { false, true })
                {
                    HeroLod.Enabled = on; foreach (var o in Wait(4)) yield return o;
                    foreach (var o in Measure()) yield return o; long full = tris, fullD = draws;
                    var rs = heroes.SelectMany(h => h.GetComponentsInChildren<Renderer>()).Where(r => r.enabled).ToList();
                    foreach (var r in rs) r.enabled = false;
                    foreach (var o in Measure()) yield return o; long none = tris, noneD = draws;
                    foreach (var r in rs) r.enabled = true;
                    rows.Add(string.Format(IC, "    {{\"round\": {0}, \"lod\": {1}, \"frame_tris\": {2}, \"char_tris\": {3}, \"char_draws\": {4}, \"levels\": \"{5}\"}}",
                        round, on ? "true" : "false", full, full - none, fullD - noneD, string.Join(",", heroes.Select(h => h.Level))));
                }
            HeroLod.Enabled = true;
            sb.Append("  \"gameplay\": [\n").Append(string.Join(",\n", rows)).Append("\n  ],\n");
            // close-up identity on the near hero
            var near = heroes.OrderByDescending(h => h.ScreenHeight).First();
            var head = near.GetComponentsInChildren<Transform>().First(t => t.name == "Head");
            float ts = Time.timeScale; Time.timeScale = 0; foreach (var o in Wait(4)) yield return o;
            var behaviours = Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None).Where(b => b.enabled && b.GetType().Namespace != null && b.GetType().Namespace.Contains("Camera")).ToArray();
            game.enabled = false; foreach (var o in Wait(2)) yield return o;
            cam.transform.SetPositionAndRotation(head.position + near.transform.forward * 1.6f - Vector3.up * .3f, Quaternion.LookRotation(-near.transform.forward)); cam.fieldOfView = 40;
            Texture2D Grab() { cam.Render(); var a = RenderTexture.active; RenderTexture.active = rt; var t = new Texture2D(1920, 1080, TextureFormat.RGB24, false); t.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); t.Apply(); RenderTexture.active = a; return t; }
            HeroLod.Enabled = false; foreach (var o in Wait(4)) yield return o; var A = Grab();
            HeroLod.Enabled = true; foreach (var o in Wait(4)) yield return o; var B = Grab();
            HeroLod.Enabled = false; foreach (var o in Wait(4)) yield return o; var C = Grab(); HeroLod.Enabled = true;
            // hero pixels: where the frame changes with the near hero switched off
            var nr = near.GetComponentsInChildren<Renderer>().Where(r => r.enabled).ToList(); foreach (var r in nr) r.enabled = false; foreach (var o in Wait(3)) yield return o;
            var E = Grab(); foreach (var r in nr) r.enabled = true;
            var pa = A.GetPixels32(); var pb = B.GetPixels32(); var pc = C.GetPixels32(); var pe = E.GetPixels32();
            int differ = 0, noise = 0, heroDiffer = 0, heroPx = 0;
            bool Same(Color32 x, Color32 y) => x.r == y.r && x.g == y.g && x.b == y.b;
            for (int i = 0; i < pa.Length; i++)
            {
                bool hero = !Same(pa[i], pe[i]); if (hero) heroPx++;
                if (!Same(pa[i], pb[i])) { differ++; if (hero) heroDiffer++; }
                if (!Same(pa[i], pc[i])) noise++;
            }
            File.WriteAllBytes(Path.Combine(Out, "tennis_identity_closeup.png"), B.EncodeToPNG());
            sb.Append(string.Format(IC, "  \"identity_closeup\": {{\"screen_h\": {0:F3}, \"level\": {1}, \"pixels_differ\": {2}, \"noise_floor_off_vs_off\": {3}, \"hero_px\": {4}, \"hero_pixels_differ\": {5}}},\n",
                near.ScreenHeight, near.Level, differ, noise, heroPx, heroDiffer));
            File.WriteAllBytes(Path.Combine(Out, "HeroLodCache_tennis.bytes"), HeroLodCache.Write(HeroLodLibrary.Computed));
            sb.Append(string.Format(IC, "  \"baked\": {0}\n}}\n", HeroLodLibrary.Computed.Count));
            Time.timeScale = ts;
            File.WriteAllText(Path.Combine(Out, "tennis_report.json"), sb.ToString());
            Log("tennis done");
        }
    }
}
#endif
