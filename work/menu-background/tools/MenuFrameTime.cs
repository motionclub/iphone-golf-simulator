using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using NUnit.Framework;
using Unity.Profiling;
using Unity.Profiling.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// Menu frame time (clone only, work/menu-background SMOOTH gate): boots the pointer menu like the phone does, then samples every
    /// frame of the arrival swoop, each screen held still (Home, Sport, Tennis modes, Locker) with the pointer moving over it, and
    /// each camera move between them. Per phase: PlayerLoop ms (the game's own CPU frame, editor excluded), GPU ms when the
    /// platform reports it, GC bytes allocated per frame, the top script / UI markers; plus an A/B of Home with the HUD disabled.
    /// MB_OUT = output folder (frametime.txt, frametime.csv).
    public class MenuFrameTime
    {
        static string Dir => Environment.GetEnvironmentVariable("MB_OUT");
        GameObject host;
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        sealed class Phase { public string name; public List<float> loop = new(), gpu = new(), cpuMain = new(); public List<long> gc = new(); public Dictionary<string, double> markers = new(); public int frames; }

        ProfilerRecorder loopR, mainR, gcR, gcCountR;
        List<(string name, ProfilerRecorder r)> markerRs = new();
        readonly FrameTiming[] timing = new FrameTiming[1];

        void StartRecorders()
        {
            loopR = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "PlayerLoop", 4);
            mainR = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 4);
            gcR = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame", 4);
            gcCountR = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocation In Frame Count", 4);
            var handles = new List<ProfilerRecorderHandle>(); ProfilerRecorderHandle.GetAvailable(handles);
            string[] keep = { "Canvas.SendWillRenderCanvases", "Canvas.BuildBatch", "UGUI.Rendering.UpdateBatches", "UGUI.Rendering.EmitWorldScreenspaceCameraGeometry",
                "Layout.Rebuild", "Graphic.Rebuild", "Canvas.UpdateLayout", "PostLateUpdate.PlayerUpdateCanvases", "Update.ScriptRunBehaviourUpdate",
                "PreLateUpdate.ScriptRunBehaviourLateUpdate", "PostLateUpdate.FinishFrameRendering", "Inl_UniversalRenderPipeline.RenderSingleCameraInternal",
                "Shadows.RenderShadowmap", "MeshSkinning.Update", "Animators.Update", "Director.ProcessFrame", "GC.Collect", "TextGenerator.Populate" };
            foreach (var h in handles)
            {
                var d = ProfilerRecorderHandle.GetDescription(h);
                bool script = d.Category == ProfilerCategory.Scripts || d.Name.EndsWith("[Invoke]") || d.Name.EndsWith("()");
                if (!script && Array.IndexOf(keep, d.Name) < 0) continue;
                if (d.Name.Contains("TestRunner") || d.Name.Contains("UnityTest") || d.Name.Contains("Editor")) continue;
                markerRs.Add((d.Name, ProfilerRecorder.StartNew(d.Category, d.Name, 4)));
            }
        }
        void StopRecorders() { loopR.Dispose(); mainR.Dispose(); gcR.Dispose(); gcCountR.Dispose(); foreach (var (_, r) in markerRs) r.Dispose(); markerRs.Clear(); }

        void Sample(Phase p)
        {
            p.frames++;
            p.loop.Add(loopR.LastValue / 1e6f); p.cpuMain.Add(mainR.LastValue / 1e6f); p.gc.Add(gcR.LastValue);
            FrameTimingManager.CaptureFrameTimings();
            if (FrameTimingManager.GetLatestTimings(1, timing) > 0 && timing[0].gpuFrameTime > 0) p.gpu.Add((float)timing[0].gpuFrameTime);
            foreach (var (n, r) in markerRs) { var v = r.LastValue; if (v > 0) { p.markers.TryGetValue(n, out var t); p.markers[n] = t + v / 1e6; } }
        }

        Canvas hudCanvas; float pointerT;
        void Wiggle(MenuHud hud)
        {
            // the pointer drifts over the menu (hover, plates and the cursor all live), Select up
            if (!hudCanvas) hudCanvas = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).FirstOrDefault(c => c.renderMode == RenderMode.ScreenSpaceOverlay && c.GetComponentInParent<MenuHud>());
            pointerT += Time.unscaledDeltaTime;
            var rt = hudCanvas ? (RectTransform)hudCanvas.transform : null; var size = rt ? rt.rect.size : new Vector2(1920, 1080);
            hud.PointAt(new Vector2(size.x * (.3f + .22f * Mathf.Sin(pointerT * 1.3f)), size.y * (.5f + .3f * Mathf.Sin(pointerT * 2.1f))), false, 0);
        }

        IEnumerator Hold(MenuHud hud, Phase p, float seconds, Func<bool> until = null)
        {
            for (float t = 0; t < seconds && (until == null || !until()); t += Time.unscaledDeltaTime) { Wiggle(hud); yield return null; Sample(p); }
        }

        static string Pct(List<float> v, float q) { if (v.Count == 0) return "n/a"; var s = v.OrderBy(x => x).ToList(); return s[Mathf.Clamp(Mathf.CeilToInt(q * s.Count) - 1, 0, s.Count - 1)].ToString("F2"); }

        [UnityTest, Timeout(900000)] public IEnumerator Profile()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("MB_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0; LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-ft", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); var hud = hub.Hud; var stage = hub.Menu;
            Assert.IsNotNull(hud, "menu mode");
            UnityEngine.Profiling.Profiler.enabled = true;   // script markers (Type.Method() [Invoke]) only exist while the profiler runs
            for (int i = 0; i < 10; i++) yield return null;
            StartRecorders();
            for (int i = 0; i < 60; i++) yield return null;   // warm up (first-use shader / mesh uploads)
            var phases = new List<Phase>();
            Phase P(string n) { var p = new Phase { name = n }; phases.Add(p); return p; }

            // the arrival swoop (held, then released)
            var arrival = P("arrival swoop");
            hub.StartArrival();
            yield return Hold(hud, arrival, 3f, () => !stage.Arriving);
            yield return Hold(hud, P("home (still)"), 4f);
            foreach (var (screen, name) in new[] { (MenuHud.Sport, "sport"), (MenuHud.TennisModes, "tennis modes"), (MenuHud.Locker, "locker"), (MenuHud.Home, "home again") })
            {
                hud.Go(screen);
                var move = P("move to " + name); yield return null; Sample(move);
                yield return Hold(hud, move, 2f, () => !stage.Moving);
                yield return Hold(hud, P(name + " (still)"), 3f);
            }
            StopRecorders();
            // A/B per script type on Home: each type's instances off for 45 frames next to 45 frames on; the difference in GC
            // bytes and PlayerLoop ms is what that script costs per frame (no deep profiling needed)
            var ab = new List<string> { "", "A/B on Home, per script type (45 frames off vs 45 on; GC KB/frame and PlayerLoop ms, mean): type | instances | GC on | GC off | delta KB | ms on | ms off | delta ms" };
            loopR = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "PlayerLoop", 4); gcR = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame", 4);
            var types = Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None).Where(m => m && m.enabled && m.gameObject.activeInHierarchy && !(m is NativeSportsSession) && m.GetType().Namespace != null && m.GetType().Namespace.StartsWith("GolfArcade"))
                .GroupBy(m => m.GetType()).ToList();
            foreach (var g in types)
            {
                var list = g.ToList(); double gcOn = 0, gcOff = 0, msOn = 0, msOff = 0; int nOn = 0, nOff = 0;
                for (int pass = 0; pass < 2; pass++)
                {
                    bool disable = pass == 0;
                    foreach (var m in list) if (m) m.enabled = !disable;
                    for (int i = 0; i < 50; i++)
                    {
                        Wiggle(hud); yield return null;
                        if (i < 5) continue;
                        if (disable) { gcOff += gcR.LastValue; msOff += loopR.LastValue / 1e6; nOff++; } else { gcOn += gcR.LastValue; msOn += loopR.LastValue / 1e6; nOn++; }
                    }
                }
                foreach (var m in list) if (m) m.enabled = true;
                gcOn /= Math.Max(1, nOn); gcOff /= Math.Max(1, nOff); msOn /= Math.Max(1, nOn); msOff /= Math.Max(1, nOff);
                ab.Add($"{g.Key.Name} | {list.Count} | {gcOn / 1024:F1} | {gcOff / 1024:F1} | {(gcOn - gcOff) / 1024:F1} | {msOn:F2} | {msOff:F2} | {msOn - msOff:F2}");
            }
            loopR.Dispose(); gcR.Dispose();

            var lines = new List<string> { $"MenuFrameTime  {DateTime.Now:yyyy-MM-dd HH:mm}  editor {Application.unityVersion}  quality {QualitySettings.names[QualitySettings.GetQualityLevel()]}  tier {GolfArcade.Tennis.TennisQuality.Current}  screen {Screen.width}x{Screen.height}",
                "phase | frames | PlayerLoop ms p50/p95/max | MainThread(incl. editor) p95 | GPU ms p50/p95 | GC KB/frame mean/max" };
            var csv = new List<string> { "phase,frames,loop_p50,loop_p95,loop_max,gpu_p95,gc_mean_bytes,gc_max_bytes" };
            foreach (var p in phases)
            {
                double gcMean = p.gc.Count > 0 ? p.gc.Average() : 0; long gcMax = p.gc.Count > 0 ? p.gc.Max() : 0;
                lines.Add($"{p.name} | {p.frames} | {Pct(p.loop, .5f)}/{Pct(p.loop, .95f)}/{(p.loop.Count > 0 ? p.loop.Max() : 0):F2} | {Pct(p.cpuMain, .95f)} | {Pct(p.gpu, .5f)}/{Pct(p.gpu, .95f)} | {gcMean / 1024:F1}/{gcMax / 1024f:F1}");
                csv.Add($"{p.name},{p.frames},{Pct(p.loop, .5f)},{Pct(p.loop, .95f)},{(p.loop.Count > 0 ? p.loop.Max() : 0):F2},{Pct(p.gpu, .95f)},{gcMean:F0},{gcMax}");
                foreach (var kv in p.markers.OrderByDescending(k => k.Value).Take(14))
                    lines.Add($"      {kv.Value / Math.Max(1, p.frames):F3} ms/frame  {kv.Key}");
            }
            lines.AddRange(ab);
            File.WriteAllLines(Path.Combine(Dir, "frametime.txt"), lines); File.WriteAllLines(Path.Combine(Dir, "frametime.csv"), csv);
            Debug.Log("MenuFrameTime done: " + Dir);
        }
    }
}
