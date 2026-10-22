#if UNITY_EDITOR
// Research-only measurement harness (chat 9, majestic maps). Lives in work/majestic-maps-research/tools
// and is copied into the measurement clone's Assets/Editor only. Never install into the real project.
//
// For every golf hole / tennis venue / the hub: frames the production gameplay camera, renders it
// automatically into a 1920x1080 target with the pipeline's MSAA, and samples per variant
// (full, no shadows, no post, no MSAA, no heroes, sky only, empty):
//   - FrameTimingManager gpuFrameTime / cpuFrameTime (Metal command-buffer timestamps)
//   - per-pass GPU time from Recorder.gpuElapsedNanoseconds where SystemInfo.supportsGpuRecorder
//   - published render counters (triangles, draw calls, SetPass, batches, shadow casters)
//   - a synchronous wall-clock proxy (Render + 1px readback) as an upper bound
// Env: MAJ_OUT (required), MAJ_HOLES (golf list), MAJ_GOLF_WEATHER ("8:Storm,16:Rain,..."),
//      MAJ_VENUES (resort,skyscraper,volcano), MAJ_TENNIS_WEATHER (Clear,Storm,...), MAJ_HUB=1,
//      MAJ_VARIANTS (comma list), MAJ_SAMPLES (default 90).
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Profiling;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class MajesticCost
    {
        const string Key = "MajesticCost";
        const int W = 1920, H = 1080;
        static IEnumerator<object> job;
        static int lastFrame = -1;

        static MajesticCost() { EditorApplication.update += Tick; }

        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("MAJ_OUT");
            if (string.IsNullOrEmpty(o)) throw new ArgumentException("MAJ_OUT");
            Directory.CreateDirectory(o);
            SessionState.SetString(Key + "out", Path.GetFullPath(o));
            SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true; // Adnan: every Unity run muted (plus GOLF_MUTE=1 in run.sh)
            bool golf = !string.IsNullOrEmpty(Environment.GetEnvironmentVariable("MAJ_HOLES"));
            bool tennis = !string.IsNullOrEmpty(Environment.GetEnvironmentVariable("MAJ_VENUES"));
            EditorSceneManager.OpenScene(golf ? "Assets/Scenes/Golf.unity" : tennis ? "Assets/Scenes/Tennis.unity" : "Assets/Scenes/Hub.unity");
            EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false)) return;
            if (!EditorUtility.audioMasterMute) EditorUtility.audioMasterMute = true;
            if (!EditorApplication.isPlaying) return;
            if (AudioListener.volume != 0) AudioListener.volume = 0;
            if (Time.frameCount == lastFrame) return;
            lastFrame = Time.frameCount;
            try
            {
                job ??= Main();
                if (!job.MoveNext()) Finish(0);
            }
            catch (Exception e) { Debug.LogException(e); Finish(1); }
        }

        static void Finish(int code)
        {
            SessionState.SetBool(Key, false);
            Log("done code=" + code);
            EditorApplication.Exit(code);
        }

        static string Out => SessionState.GetString(Key + "out", "/tmp/majestic");
        static readonly StringBuilder log = new();
        static void Log(string s)
        {
            Debug.Log("[Majestic] " + s);
            log.AppendLine(s);
            File.WriteAllText(Path.Combine(Out, "run.log"), log.ToString());
        }

        static IEnumerable<object> Wait(int frames) { for (int i = 0; i < frames; i++) yield return null; }
        static IEnumerable<object> WaitSeconds(float s) { float until = Time.realtimeSinceStartup + s; while (Time.realtimeSinceStartup < until) yield return null; }

        static IEnumerator<object> Main()
        {
            Log($"unity={Application.unityVersion} gfx={SystemInfo.graphicsDeviceType} gpu={SystemInfo.graphicsDeviceName} gpuRecorder={SystemInfo.supportsGpuRecorder} pipeline={GraphicsSettings.currentRenderPipeline?.name} quality={QualitySettings.names[QualitySettings.GetQualityLevel()]}");
            string holes = Environment.GetEnvironmentVariable("MAJ_HOLES");
            string venues = Environment.GetEnvironmentVariable("MAJ_VENUES");
            bool hub = Environment.GetEnvironmentVariable("MAJ_HUB") == "1";

            if (!string.IsNullOrEmpty(holes))
            {
                GolfGame golf = null; CameraRig rig = null;
                while (!golf || !rig || !HoleView.Current) { golf = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>(); yield return null; }
                golf.ChooseHoles(0); golf.Play();
                foreach (var o in Wait(30)) yield return o;
                var extra = (Environment.GetEnvironmentVariable("MAJ_GOLF_WEATHER") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries)
                    .Select(x => x.Split(':')).Select(p => (int.Parse(p[0]), p[1])).ToList();
                var slots = holes.Split(',').Select(h => (int.Parse(h), "Clear")).Concat(extra).ToList();
                WeatherView view = null;
                foreach (var (number, weather) in slots)
                {
                    Environment.SetEnvironmentVariable("DREAM_WEATHER", weather);
                    Environment.SetEnvironmentVariable("DREAM_UTC", "1792263600"); // 14:00 EST clear-day sun, same as chat 2's captures
                    golf.enabled = true; rig.enabled = true;
                    if (view) view.Restore();
                    golf.JumpToHole(number);
                    golf.DropBall(golf.CurrentHole.Tee);
                    foreach (var o in Wait(40)) yield return o;
                    var h = golf.CurrentHole;
                    var cam = rig.Camera;
                    if (weather != "Clear" && Enum.TryParse<Weather>(weather, out var w))
                    {
                        if (!view) view = WeatherView.Create(golf.transform, EventSounds.Create(golf.transform));
                        view.Begin(cam, h, w, new Wind(w == Weather.Storm ? 10 : 4, 45), true);
                    }
                    rig.FrameAddress(HoleView.ToWorld(h.Tee, .06), HoleView.ToWorld(h.Pin) - HoleView.ToWorld(h.Tee), false);
                    rig.SnapNext(); rig.ApplyFrame();
                    golf.enabled = false; rig.enabled = false;
                    var heroes = Object.FindObjectsByType<Animator>(FindObjectsSortMode.None).Select(a => a.transform).ToArray();
                    foreach (var o in Measure($"golf_h{number:00}_{weather.ToLowerInvariant()}", cam, heroes)) yield return o;
                }
            }

            if (!string.IsNullOrEmpty(venues))
            {
                var weathers = (Environment.GetEnvironmentVariable("MAJ_TENNIS_WEATHER") ?? "Clear").Split(',');
                foreach (var vname in venues.Split(','))
                {
                    var venue = (TennisVenueKind)Enum.Parse(typeof(TennisVenueKind), vname, true);
                    TennisVenue.Selected = venue;
                    var load = UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Tennis");
                    while (!load.isDone) yield return null;
                    TennisGame tennis = null;
                    while (!tennis || !tennis.Initialized) { tennis = Object.FindFirstObjectByType<TennisGame>(); yield return null; }
                    foreach (var o in Wait(60)) yield return o;
                    foreach (var weather in weathers)
                    {
                        Environment.SetEnvironmentVariable("DREAM_WEATHER", weather);
                        Environment.SetEnvironmentVariable("DREAM_UTC", "1792263600");
                        tennis.enabled = true;
                        var conditions = tennis.GetComponent<TennisConditions>();
                        if (conditions) typeof(TennisConditions).GetField("lastGame", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).SetValue(conditions, -1);
                        TennisConditions.Boundary(tennis);
                        foreach (var o in Wait(30)) yield return o;
                        foreach (var o in WaitSeconds(weather == "Clear" ? 1 : 6)) yield return o; // weather eases in
                        var presentation = tennis.GetComponent<TennisPresentation>(); if (presentation) presentation.Finish();
                        tennis.enabled = false;
                        var cam = tennis.GameplayCamera;
                        cam.aspect = W / (float)H;
                        TennisShoulderCamera.Frame(tennis.Player.transform.position, false, Vector3.zero, false, cam.aspect, out var position, out var look, out var fov);
                        cam.transform.position = position; cam.transform.LookAt(look); cam.fieldOfView = fov;
                        var heroes = new[] { tennis.Player.transform, tennis.Opponent.transform };
                        foreach (var o in Measure($"tennis_{vname}_{weather.ToLowerInvariant()}", cam, heroes)) yield return o;
                    }
                }
            }

            if (hub)
            {
                var load = UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Hub");
                while (!load.isDone) yield return null;
                GolfArcade.Hub.HubWorld world = null;
                while (!world || !world.Camera) { world = Object.FindFirstObjectByType<GolfArcade.Hub.HubWorld>(); yield return null; }
                foreach (var o in WaitSeconds(3)) yield return o;
                world.HurryArrival();
                foreach (var o in WaitSeconds(6)) yield return o;
                var heroes = Object.FindObjectsByType<Animator>(FindObjectsSortMode.None).Select(a => a.transform).ToArray();
                foreach (var o in Measure("hub_plaza_clear", world.Camera, heroes)) yield return o;
            }
        }

        // ---- measurement -------------------------------------------------------------------

        [Serializable] class PassTime { public string name; public float gpuMs; public float cpuMs; }
        [Serializable] class Variant
        {
            public string name;
            public float gpuMedianMs, gpuP90Ms, gpuP10Ms, cpuMedianMs, syncWallMedianMs, syncWallP10Ms, syncQuarterP25Ms, sync1xP25Ms, sync2xP25Ms, pixelGpuMs1080;
            public int gpuSamples;
            public long triangles, vertices, drawCalls, setPass, batches, shadowCasters;
            public PassTime[] passes;
        }
        [Serializable] class Report
        {
            public string slot, gpu, api, pipeline, note = "Editor play mode on the Mac GPU; gameplay camera rendered automatically into a 1920x1080 target (pipeline MSAA). Not device timing.";
            public int width = W, height = H, msaa, renderers, meshRenderers, skinned, particleSystems, lodGroups, lights, shadowLights, transparentMaterials, uniqueMaterials, uniqueShaders;
            public long sceneTriangles; public float cameraFov, farClip;
            public Variant[] variants;
        }

        static readonly string[] PassKeys = { "Shadow", "Opaque", "Transparent", "Skybox", "Post", "Bloom", "Uber", "Depth", "Copy", "Final", "Resolve", "Blit", "Draw" };

        static IEnumerable<object> Measure(string slot, Camera cam, Transform[] heroes)
        {
            var asset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            int msaa = asset ? asset.msaaSampleCount : 1;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = msaa };
            rt.Create();
            var prevTarget = cam.targetTexture; var prevAspect = cam.aspect;
            var data = cam.GetUniversalAdditionalCameraData();
            bool prevPost = data && data.renderPostProcessing;
            var otherCams = Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).Where(c => c != cam && c.enabled).ToArray();
            foreach (var c in otherCams) c.enabled = false;
            var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.enabled).ToArray();
            foreach (var c in canvases) c.enabled = false;
            cam.targetTexture = rt; cam.aspect = W / (float)H; cam.enabled = true;

            var report = Inventory(slot, cam, msaa);
            var wanted = (Environment.GetEnvironmentVariable("MAJ_VARIANTS") ?? "full,noShadows,noPost,noMSAA,noHeroes,skyOnly,empty").Split(',');
            int rounds = int.TryParse(Environment.GetEnvironmentVariable("MAJ_ROUNDS"), out var rr) ? rr : 5;
            var acc = wanted.ToDictionary(v => v, v => new Acc { name = v });
            // Interleaved A/B rounds: every variant is sampled once per round, so drift and other
            // processes' GPU load (other chats' editors share this GPU) hit all variants alike.
            for (int round = 0; round < rounds; round++)
                foreach (var v in wanted)
                {
                    var undo = Apply(v, cam, heroes, data, prevPost);
                    foreach (var o in Sample(cam, acc[v])) yield return o;
                    if (v == "full" && round == 0) Save(cam, Path.Combine(Out, slot + ".jpg"));
                    undo();
                    yield return null;
                }
            var variants = wanted.Select(v => acc[v].Result()).ToList();
            report.variants = variants.ToArray();
            File.WriteAllText(Path.Combine(Out, slot + ".json"), JsonUtility.ToJson(report, true));
            var f = variants[0];
            Log($"{slot}: pixelGPU1080={f.pixelGpuMs1080:F2}ms sync q/1/2={f.syncQuarterP25Ms:F2}/{f.sync1xP25Ms:F2}/{f.sync2xP25Ms:F2} ftmGpu p10={f.gpuP10Ms:F2} tris={f.triangles} draws={f.drawCalls} setpass={f.setPass} casters={f.shadowCasters} | " +
                string.Join(" ", variants.Skip(1).Select(x => $"{x.name}=px{x.pixelGpuMs1080:F2}/1x{x.sync1xP25Ms:F2}/q{x.syncQuarterP25Ms:F2}")));

            cam.targetTexture = prevTarget; cam.aspect = prevAspect;
            foreach (var c in otherCams) if (c) c.enabled = true;
            foreach (var c in canvases) if (c) c.enabled = true;
            rt.Release(); Object.DestroyImmediate(rt);
        }

        static Action Apply(string v, Camera cam, Transform[] heroes, UniversalAdditionalCameraData data, bool prevPost)
        {
            switch (v)
            {
                case "noShadows":
                {
                    var lights = Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Where(l => l.shadows != LightShadows.None).ToArray();
                    var prev = lights.Select(l => l.shadows).ToArray();
                    foreach (var l in lights) l.shadows = LightShadows.None;
                    return () => { for (int i = 0; i < lights.Length; i++) if (lights[i]) lights[i].shadows = prev[i]; };
                }
                case "noPost":
                    if (data) data.renderPostProcessing = false;
                    return () => { if (data) data.renderPostProcessing = prevPost; };
                case "noMSAA":
                {
                    bool prev = cam.allowMSAA; cam.allowMSAA = false;
                    var t = cam.targetTexture; var flat = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 }; flat.Create(); cam.targetTexture = flat;
                    return () => { cam.allowMSAA = prev; cam.targetTexture = t; flat.Release(); Object.DestroyImmediate(flat); };
                }
                case "noHeroes":
                {
                    var rs = heroes.Where(h => h).SelectMany(h => h.GetComponentsInChildren<Renderer>()).Where(r => r.enabled).ToArray();
                    foreach (var r in rs) r.enabled = false;
                    return () => { foreach (var r in rs) if (r) r.enabled = true; };
                }
                case "majOff":
                {
                    var t = System.Type.GetType("GolfArcade.Majestic.MajesticVenue, GolfArcade");
                    var m = t?.GetMethod("SetEnabled");
                    m?.Invoke(null, new object[] { false });
                    return () => m?.Invoke(null, new object[] { true });
                }
                case "skyOnly":
                {
                    int mask = cam.cullingMask; cam.cullingMask = 0;
                    return () => cam.cullingMask = mask;
                }
                case "empty":
                {
                    int mask = cam.cullingMask; var flags = cam.clearFlags; cam.cullingMask = 0; cam.clearFlags = CameraClearFlags.SolidColor;
                    if (data) data.renderPostProcessing = false;
                    return () => { cam.cullingMask = mask; cam.clearFlags = flags; if (data) data.renderPostProcessing = prevPost; };
                }
                default: return () => { };
            }
        }

        sealed class Acc
        {
            public string name; public readonly List<double> gpu = new(), cpu = new(), sync = new(), syncQ = new(), sync2 = new();
            public long tri, vert, draw, pass, batch, casters;
            public readonly Dictionary<string, (double gpu, double cpu, int n)> passes = new();
            public Variant Result() => new Variant
            {
                name = name, gpuSamples = gpu.Count,
                gpuMedianMs = (float)Pct(gpu, .5), gpuP90Ms = (float)Pct(gpu, .9), gpuP10Ms = (float)Pct(gpu, .1), cpuMedianMs = (float)Pct(cpu, .5),
                syncWallMedianMs = (float)Pct(sync, .5), syncWallP10Ms = (float)Pct(sync, .1),
                syncQuarterP25Ms = (float)Pct(syncQ, .25), sync1xP25Ms = (float)Pct(sync, .25), sync2xP25Ms = (float)Pct(sync2, .25),
                pixelGpuMs1080 = (float)((Pct(sync2, .25) - Pct(sync, .25)) / 3),
                triangles = tri, vertices = vert, drawCalls = draw, setPass = pass, batches = batch, shadowCasters = casters,
                passes = passes.Where(p => p.Value.n > 0 && p.Value.cpu / p.Value.n > .05)
                    .Select(p => new PassTime { name = p.Key, gpuMs = (float)(p.Value.gpu / p.Value.n), cpuMs = (float)(p.Value.cpu / p.Value.n) })
                    .OrderByDescending(p => p.cpuMs).Take(30).ToArray()
            };
        }

        static IEnumerable<object> Sample(Camera cam, Acc acc)
        {
            int n = int.TryParse(Environment.GetEnvironmentVariable("MAJ_SAMPLES"), out var s) ? s : 40;
            foreach (var o in Wait(6)) yield return o;
            var names = new List<string>(); Sampler.GetNames(names);
            var recorders = names.Distinct().Where(x => !x.StartsWith("Physics") && !x.StartsWith("Gfx.WaitFor") && PassKeys.Any(k => x.IndexOf(k, StringComparison.OrdinalIgnoreCase) >= 0)).Take(400)
                .Select(x => (x, Sampler.Get(x).GetRecorder())).Where(p => p.Item2 != null && p.Item2.isValid).ToList();
            foreach (var (_, r) in recorders) r.enabled = true;
            var cat = Unity.Profiling.ProfilerCategory.Render;
            var tri = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Triangles Count");
            var vert = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Vertices Count");
            var draw = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Draw Calls Count");
            var pass = Unity.Profiling.ProfilerRecorder.StartNew(cat, "SetPass Calls Count");
            var batch = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Batches Count");
            var casters = Unity.Profiling.ProfilerRecorder.StartNew(cat, "Shadow Casters Count");
            var timings = new FrameTiming[1];
            foreach (var o in Wait(3)) yield return o;
            for (int i = 0; i < n; i++)
            {
                FrameTimingManager.CaptureFrameTimings();
                if (FrameTimingManager.GetLatestTimings(1, timings) > 0)
                {
                    if (timings[0].gpuFrameTime > 0) acc.gpu.Add(timings[0].gpuFrameTime);
                    if (timings[0].cpuFrameTime > 0) acc.cpu.Add(timings[0].cpuFrameTime);
                }
                // counters: largest published value (frames where the editor skipped the camera report 0)
                // Counters: smallest non-zero published value. Frames where the editor skipped the camera read 0,
                // and on a loaded machine one profiler frame can hold two camera renders (doubled counts).
                if (draw.LastValue > 0 && (acc.draw == 0 || draw.LastValue < acc.draw))
                { acc.tri = tri.LastValue; acc.vert = vert.LastValue; acc.draw = draw.LastValue; acc.pass = pass.LastValue; acc.batch = batch.LastValue; acc.casters = casters.LastValue; }
                foreach (var (k, r) in recorders)
                {
                    acc.passes.TryGetValue(k, out var a);
                    acc.passes[k] = (a.gpu + r.gpuElapsedNanoseconds / 1e6, a.cpu + r.elapsedNanoseconds / 1e6, a.n + 1);
                }
                yield return null;
            }
            foreach (var (_, r) in recorders) r.enabled = false;
            tri.Dispose(); vert.Dispose(); draw.Dispose(); pass.Dispose(); batch.Dispose(); casters.Dispose();

            // Synchronous proxy, CPU submit + GPU, forced complete by a 1px readback, at 1/4x, 1x and 2x of
            // 1080p (pixel counts 1/16 : 1 : 4). CPU work is resolution independent, so
            // (T2x - T1x)/3 = the per-pixel GPU cost of one 1080p frame, free of editor/CPU overhead.
            cam.enabled = false;
            var px = new Texture2D(1, 1, TextureFormat.RGBA32, false);
            var keep = cam.targetTexture; int aa = keep ? keep.antiAliasing : 1;
            foreach (var (scale, list) in new[] { (.25f, acc.syncQ), (1f, acc.sync), (2f, acc.sync2) })
            {
                var t = scale == 1f ? keep : new RenderTexture((int)(W * scale), (int)(H * scale), 24, RenderTextureFormat.ARGB32) { antiAliasing = aa };
                if (t != keep) t.Create();
                cam.targetTexture = t;
                for (int i = 0; i < 12; i++)
                {
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    cam.Render(); var a = RenderTexture.active; RenderTexture.active = t;
                    px.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); px.Apply(); RenderTexture.active = a;
                    sw.Stop(); if (i >= 3) list.Add(sw.Elapsed.TotalMilliseconds);
                }
                cam.targetTexture = keep;
                if (t != keep) { t.Release(); Object.DestroyImmediate(t); }
            }
            Object.DestroyImmediate(px);
            cam.enabled = true;
        }

        static double Pct(List<double> xs, double p) { if (xs.Count == 0) return -1; var s = xs.OrderBy(x => x).ToList(); return s[Mathf.Clamp((int)(p * s.Count), 0, s.Count - 1)]; }

        static Report Inventory(string slot, Camera cam, int msaa)
        {
            var renderers = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.enabled && r.gameObject.activeInHierarchy).ToArray();
            var mats = renderers.SelectMany(r => r.sharedMaterials).Where(m => m).Distinct().ToArray();
            long tris = 0; var seen = new HashSet<Mesh>();
            foreach (var mf in renderers.OfType<MeshRenderer>().Select(r => r.GetComponent<MeshFilter>()).Where(f => f && f.sharedMesh))
                if (seen.Add(mf.sharedMesh)) for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) tris += mf.sharedMesh.GetIndexCount(s) / 3;
            var lights = Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Where(l => l.enabled).ToArray();
            return new Report
            {
                slot = slot, gpu = SystemInfo.graphicsDeviceName, api = SystemInfo.graphicsDeviceType.ToString(), pipeline = GraphicsSettings.currentRenderPipeline?.name, msaa = msaa,
                renderers = renderers.Length, meshRenderers = renderers.Count(r => r is MeshRenderer), skinned = renderers.Count(r => r is SkinnedMeshRenderer),
                particleSystems = Object.FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None).Count(p => p.isPlaying),
                lodGroups = Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None).Length, lights = lights.Length, shadowLights = lights.Count(l => l.shadows != LightShadows.None),
                transparentMaterials = mats.Count(m => m.renderQueue >= 2500), uniqueMaterials = mats.Length, uniqueShaders = mats.Select(m => m.shader).Distinct().Count(),
                sceneTriangles = tris, cameraFov = cam.fieldOfView, farClip = cam.farClipPlane
            };
        }

        static void Save(Camera cam, string path)
        {
            var big = cam.targetTexture; var small = RenderTexture.GetTemporary(1280, 720, 24); var a = RenderTexture.active;
            Graphics.Blit(big, small); RenderTexture.active = small;
            var tex = new Texture2D(1280, 720, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, 1280, 720), 0, 0); tex.Apply();
            File.WriteAllBytes(path, tex.EncodeToJPG(85)); RenderTexture.active = a; RenderTexture.ReleaseTemporary(small); Object.DestroyImmediate(tex);
        }
    }
}
#endif
