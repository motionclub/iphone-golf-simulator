using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using Unity.Profiling;
using UnityEngine;

/// Clone-only (work/menu-background SMOOTH gate): a standalone player started with `-menuprofile <out dir>` boots the plaza
/// menu with the phone's own start message (menu = true), walks the menu (arrival swoop, Home, Sport, Tennis modes, Locker,
/// Home, the camera moves between them) with the pointer drifting, uncapped (vSync 0, no target frame rate) so each frame's
/// time is its cost, and writes per-phase p50/p95/max of the frame interval, the CPU main/render thread and the GPU
/// (FrameTimingManager) and GC bytes per frame to <out dir>/player_frametime.txt, then quits.
public class MenuProfileBoot : MonoBehaviour
{
    string dir;
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        var args = Environment.GetCommandLineArgs(); int i = Array.IndexOf(args, "-menuprofile");
        if (i < 0 || i + 1 >= args.Length) return;
        var go = new GameObject("MenuProfileBoot"); DontDestroyOnLoad(go);
        go.AddComponent<MenuProfileBoot>().dir = args[i + 1];
    }

    class Phase { public string name; public List<double> dt = new(), main = new(), render = new(), gpu = new(); public List<long> gc = new(); }
    readonly FrameTiming[] ft = new FrameTiming[1];
    ProfilerRecorder gcR;

    IEnumerator Start()
    {
        Directory.CreateDirectory(dir); AudioListener.volume = 0;
        Screen.SetResolution(1920, 1080, FullScreenMode.Windowed);
        yield return null;
        var host = new GameObject("NativeSportsSession"); DontDestroyOnLoad(host);
        var bridge = host.AddComponent<NativeSportsSession>();
        bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-player", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
        float t0 = Time.realtimeSinceStartup;
        while (!bridge.Ready && Time.realtimeSinceStartup - t0 < 120) yield return null;
        var hub = HubWorld.Find(); var hud = hub ? hub.Hud : null; var stage = hub ? hub.Menu : null;
        if (!hud) { File.WriteAllText(Path.Combine(dir, "player_frametime.txt"), "menu did not boot"); Application.Quit(); yield break; }
        gcR = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame", 4);
        var phases = new List<Phase>(); string pass = "";
        Phase P(string n) { var p = new Phase { name = pass + n }; phases.Add(p); return p; }
        float wig = 0;
        IEnumerator Hold(Phase p, float seconds, Func<bool> until = null)
        {
            for (float t = 0; t < seconds && (until == null || !until()); t += Time.unscaledDeltaTime)
            {
                wig += Time.unscaledDeltaTime;
                hud.PointAt(new Vector2(1920 * (.3f + .22f * Mathf.Sin(wig * 1.3f)), 1080 * (.5f + .3f * Mathf.Sin(wig * 2.1f))), false, 0);
                yield return null;
                p.dt.Add(Time.unscaledDeltaTime * 1000);
                FrameTimingManager.CaptureFrameTimings();
                if (FrameTimingManager.GetLatestTimings(1, ft) > 0)
                {
                    p.main.Add(ft[0].cpuMainThreadFrameTime - ft[0].cpuMainThreadPresentWaitTime); p.render.Add(ft[0].cpuRenderThreadFrameTime);
                    if (ft[0].gpuFrameTime > 0) p.gpu.Add(ft[0].gpuFrameTime);
                }
                p.gc.Add(gcR.LastValue);
            }
        }
        // two walks: uncapped (each frame's interval = its cost), then capped at 60 like the game on the TV (late frames = hitches)
        foreach (var cap in new[] { -1, 60 })
        {
            QualitySettings.vSyncCount = 0; Application.targetFrameRate = cap; pass = cap < 0 ? "[uncapped] " : "[60 fps] ";
            for (int k = 0; k < 120; k++) yield return null;   // warm up
            if (cap < 0) { hub.StartArrival(); yield return Hold(P("arrival swoop"), 3f, () => !stage.Arriving); }
            else { hud.Go(MenuHud.Home); yield return Hold(P("settle"), 1f); }
            yield return Hold(P("home (still)"), 5f);
            foreach (var (screen, name) in new[] { (MenuHud.Sport, "sport"), (MenuHud.TennisModes, "tennis modes"), (MenuHud.Locker, "locker"), (MenuHud.Home, "home again") })
            {
                hud.Go(screen);
                yield return Hold(P("move to " + name), 2f, () => !stage.Moving);
                yield return Hold(P(name + " (still)"), 4f);
            }
        }
        string Q(List<double> v, double q) { if (v.Count == 0) return "n/a"; var s = v.OrderBy(x => x).ToList(); return s[Mathf.Clamp(Mathf.CeilToInt((float)(q * s.Count)) - 1, 0, s.Count - 1)].ToString("F2"); }
        var lines = new List<string> { $"MenuProfileBoot player {Application.unityVersion} {SystemInfo.deviceModel} {SystemInfo.graphicsDeviceName} {Screen.width}x{Screen.height} quality {QualitySettings.names[QualitySettings.GetQualityLevel()]} tier {GolfArcade.Tennis.TennisQuality.Current} msaa {QualitySettings.antiAliasing} uncapped",
            "phase | frames | frame interval ms p50/p95/max | late (> 17.5 ms) | CPU main (work) p50/p95 | CPU render p95 | GPU p50/p95/max | GC KB/frame mean/max" };
        var csv = new List<string> { "phase,frame,interval_ms,cpu_main_ms,cpu_render_ms,gpu_ms" };
        foreach (var p in phases) for (int k = 0; k < p.dt.Count; k++) csv.Add($"{p.name},{k},{p.dt[k]:F2},{(k < p.main.Count ? p.main[k] : 0):F2},{(k < p.render.Count ? p.render[k] : 0):F2},{(k < p.gpu.Count ? p.gpu[k] : 0):F2}");
        File.WriteAllLines(Path.Combine(dir, "player_frames.csv"), csv);
        foreach (var p in phases)
            lines.Add($"{p.name} | {p.dt.Count} | {Q(p.dt, .5)}/{Q(p.dt, .95)}/{(p.dt.Count > 0 ? p.dt.Max() : 0):F2} | {(p.dt.Count > 0 ? 100.0 * p.dt.Count(x => x > 17.5) / p.dt.Count : 0):F1}% | {Q(p.main, .5)}/{Q(p.main, .95)} | {Q(p.render, .95)} | {Q(p.gpu, .5)}/{Q(p.gpu, .95)}/{(p.gpu.Count > 0 ? p.gpu.Max() : 0):F2} | {(p.gc.Count > 0 ? p.gc.Average() / 1024 : 0):F1}/{(p.gc.Count > 0 ? p.gc.Max() / 1024f : 0):F1}");
        File.WriteAllLines(Path.Combine(dir, "player_frametime.txt"), lines);
        gcR.Dispose();
        Application.Quit();
    }
}
