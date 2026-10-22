#if UNITY_EDITOR
// Proof + gate harness for the Majestic weather layer (chat W, work/majestic-weather). Clone only, never installed.
// Muted (Editor mute + AudioListener 0; run with GOLF_MUTE=1). Renders the game's own cameras at 1920x1080.
// Env: MW_OUT (required), MW_SLOTS (comma list of slot ids, default all: W01..W16,X10),
//      MW_JOBS (refs,read,cost,det,toggle,video,coverage; default refs,read,det),
//      MW_ROUNDS / MW_SAMPLES (cost), MW_ORIG_SURFACE (unpatched EnvironmentSurface.hlsl for the off-path proof),
//      MW_VIDEO_SECONDS (default 5).
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Course;
using GolfArcade.EnvironmentArt;
using GolfArcade.Game;
using GolfArcade.Majestic;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.Media;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class MajesticWeatherShots
    {
        const string Key = "MajesticWeatherShots";
        const int W = 1920, H = 1080;
        static IEnumerator<object> job; static int lastFrame = -1;
        static MajesticWeatherShots() { EditorApplication.update += Tick; }

        sealed class Slot { public string id, place; public bool golf; public int hole; public TennisVenueKind venue; public Weather weather; public bool clearing; public string fx; }
        static readonly Slot[] All =
        {
            G("W01", 7, Weather.Rain, "rain"), G("W02", 8, Weather.Rain, "clearing", true), G("W03", 13, Weather.Storm, "thunderstorm"), G("W04", 15, Weather.Fog, "seafog"),
            G("W05", 20, Weather.Gusty, "gusty"), G("W06", 17, Weather.Rain, "snow"), G("W07", 17, Weather.Storm, "blizzard"), G("W08", 17, Weather.Fog, "freezingfog"),
            G("W09", 22, Weather.Rain, "ashfall"), G("W10", 23, Weather.Storm, "eruption"), G("W11", 21, Weather.Fog, "smoke"),
            T("W12", TennisVenueKind.Resort, Weather.Rain, "rain"), T("W13", TennisVenueKind.Resort, Weather.Fog, "seafog"), T("W14", TennisVenueKind.Skyscraper, Weather.Storm, "thunderstorm"),
            T("W15", TennisVenueKind.Skyscraper, Weather.Gusty, "gusty"), T("W16", TennisVenueKind.Volcano, Weather.Fog, "smoke"),
            G("X10", 10, Weather.Storm, "h10_ash_family"), G("X16", 16, Weather.Rain, "h16_ash_family"),
        };
        static Slot G(string id, int hole, Weather w, string fx, bool clearing = false) => new() { id = id, golf = true, hole = hole, weather = w, fx = fx, clearing = clearing, place = $"golf h{hole:00}" };
        static Slot T(string id, TennisVenueKind v, Weather w, string fx) => new() { id = id, venue = v, weather = w, fx = fx, place = "tennis " + v.ToString().ToLowerInvariant() };

        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("MW_OUT"); if (string.IsNullOrEmpty(o)) throw new ArgumentException("MW_OUT");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", Path.GetFullPath(o)); SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true;
            Environment.SetEnvironmentVariable("DREAM_UTC", Environment.GetEnvironmentVariable("MW_UTC") ?? "1792263600");
            bool golf = Slots().Any(s => s.golf);
            EditorSceneManager.OpenScene(golf ? "Assets/Scenes/Golf.unity" : "Assets/Scenes/Tennis.unity"); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false)) return;
            if (!EditorUtility.audioMasterMute) EditorUtility.audioMasterMute = true;
            if (!EditorApplication.isPlaying) return;
            if (AudioListener.volume != 0) AudioListener.volume = 0;
            if (Time.frameCount == lastFrame) return; lastFrame = Time.frameCount;
            try { job ??= Main(); if (!job.MoveNext()) Finish(0); }
            catch (Exception e) { Debug.LogException(e); Log("EXCEPTION " + e.Message); Finish(1); }
        }

        static void Finish(int code)
        {
            Time.captureFramerate = 0; Time.timeScale = 1;
            File.WriteAllText(Path.Combine(Out, "results.json"), "{\n" + string.Join(",\n", results.Select(kv => $"  \"{kv.Key}\": {kv.Value}")) + "\n}\n");
            SessionState.SetBool(Key, false); Log("done code=" + code); EditorApplication.Exit(code);
        }

        static string Out => SessionState.GetString(Key + "out", "/tmp/mw");
        static readonly StringBuilder log = new();
        static readonly Dictionary<string, string> results = new();
        static void Log(string s) { Debug.Log("[MajesticWeather] " + s); log.AppendLine(s); File.WriteAllText(Path.Combine(Out, "run.log"), log.ToString()); }
        static void Result(string key, string json) { results[key] = json; }
        static IEnumerable<object> Wait(int n) { for (int i = 0; i < n; i++) yield return null; }
        static IEnumerable<object> WaitSeconds(float s) { float t = Time.realtimeSinceStartup + s; while (Time.realtimeSinceStartup < t) yield return null; }
        static bool Job(string j) => (Environment.GetEnvironmentVariable("MW_JOBS") ?? "refs,read,det").Split(',').Contains(j);
        static IEnumerable<Slot> Slots()
        {
            var want = (Environment.GetEnvironmentVariable("MW_SLOTS") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries);
            return want.Length == 0 ? All : All.Where(s => want.Contains(s.id));
        }

        // ================================================================== main
        static IEnumerator<object> Main()
        {
            // MW_QUALITY=<index>: render at that quality level (iPhone default = 2 "Medium": 1 cascade, 20 m shadows)
            if (int.TryParse(Environment.GetEnvironmentVariable("MW_QUALITY"), out var mq) && mq >= 0 && mq < QualitySettings.names.Length) QualitySettings.SetQualityLevel(mq, true);
            Log($"unity={Application.unityVersion} gfx={SystemInfo.graphicsDeviceType} gpu={SystemInfo.graphicsDeviceName} quality={QualitySettings.names[QualitySettings.GetQualityLevel()]} shadersReady={MajesticWeather.ShadersReady} jobs={Environment.GetEnvironmentVariable("MW_JOBS")}");
            if (Job("det")) Determinism();
            var golfSlots = Slots().Where(s => s.golf).ToList();
            if (golfSlots.Count > 0)
            {
                GolfGame golf = null; CameraRig rig = null;
                while (!golf || !rig || !HoleView.Current) { golf = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>(); yield return null; }
                golf.ChooseHoles(0); golf.Play();
                foreach (var o in Wait(30)) yield return o;
                bool first = true;
                foreach (var s in golfSlots) { foreach (var o in GolfSlot(s, golf, rig, first)) yield return o; first = false; }
            }
            bool firstTennis = true;
            foreach (var s in Slots().Where(s => !s.golf)) { foreach (var o in TennisSlot(s, firstTennis)) yield return o; firstTennis = false; }
        }

        // ================================================================== golf
        static WeatherView ownView;
        static IEnumerable<object> GolfSlot(Slot s, GolfGame golf, CameraRig rig, bool first)
        {
            Log($"--- {s.id} {s.place} {s.weather}{(s.clearing ? " -> clearing" : "")}");
            Environment.SetEnvironmentVariable("DREAM_WEATHER", s.weather.ToString());
            Time.timeScale = 1; Time.captureFramerate = 0;
            golf.enabled = true; rig.enabled = true;
            MajesticWeather.SetEnabled(true);
            golf.JumpToHole(s.hole); golf.DropBall(golf.CurrentHole.Tee);
            foreach (var o in WaitSeconds(4)) yield return o;
            var h = golf.CurrentHole; var cam = rig.Camera;
            var wind = new Wind(s.weather == Weather.Storm ? 10 : s.weather == Weather.Gusty ? 9 : 4, 45);
            var view = golf.WeatherShown;
            if (!view || view.Weather != s.weather)
            {
                if (!ownView) ownView = WeatherView.Create(golf.transform, EventSounds.Create(golf.transform));
                view = ownView;
            }
            void SetWeather(Weather w)
            {
                view.Begin(cam, h, w, wind, true);
                DreamEnvironment.Current?.SetWeather(w);
                DreamVisibility.Set(w == Weather.Fog, HoleView.ToWorld(golf.BallAt));
                MajesticWeather.Current?.Restart();
            }
            MajesticWeather.Source = view;
            SetWeather(s.weather);
            rig.FrameAddress(HoleView.ToWorld(h.Tee, .06), HoleView.ToWorld(h.Pin) - HoleView.ToWorld(h.Tee), false);
            rig.SnapNext(); rig.ApplyFrame();
            golf.enabled = false; rig.enabled = false; cam.aspect = 16f / 9;
            while (!MajesticWeather.Current) yield return null;
            var mw = MajesticWeather.Current;
            foreach (var o in Wait(3)) yield return o;
            mw.Snap();
            foreach (var o in Wait(20)) yield return o;
            if (s.clearing)
            {
                view.Change(Weather.Clear); DreamEnvironment.Current?.SetWeather(Weather.Clear);
                foreach (var o in WaitSeconds(7)) yield return o;
            }
            Log($"{s.id}: family={mw.Family} phase={mw.Phase} active={mw.Active} weather={mw.Weather} sky={Weathers.SkyOf(h)} title={s.weather.Title(Weathers.SkyOf(h))}");
            State(s, mw);
            if (Job("refs")) { foreach (var o in Refs(s, cam, mw, () => SetWeather(Weather.Clear), () => { SetWeather(s.weather); }, s.clearing ? () => { view.Change(Weather.Clear); DreamEnvironment.Current?.SetWeather(Weather.Clear); mw.ClearingNow(); } : null)) yield return o; }
            if (Job("read")) { foreach (var o in Read(s, cam, mw, BallRenderers(golf), FlagRenderers(h))) yield return o; }
            if (Job("coverage") && first) Coverage(s, cam);
            if (Job("cost")) { foreach (var o in Cost(s, cam, mw, () => SetWeather(Weather.Clear), () => SetWeather(s.weather), s.clearing ? () => { view.Change(Weather.Clear); DreamEnvironment.Current?.SetWeather(Weather.Clear); mw.ClearingNow(); } : null)) yield return o; }
            if (Job("toggle") && first) { foreach (var o in Toggle(s, cam, mw)) yield return o; }
            if (Job("offpath")) { foreach (var o in OffPath(s, cam, mw)) yield return o; }
            if (Job("video")) { foreach (var o in Video(s, cam, mw, view, () => SetWeather(s.weather), null)) yield return o; }
            if (Job("rim")) { foreach (var o in Rim(s, cam, mw, golf, h, () => SetWeather(Weather.Clear), () => SetWeather(s.weather))) yield return o; }
            MajesticWeather.Source = null;
        }

        static Renderer[] BallRenderers(GolfGame golf)
        {
            var ball = golf.transform.Find("Ball") ?? GameObject.Find("Ball")?.transform;
            var at = HoleView.ToWorld(golf.BallAt);
            var near = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.enabled && r.gameObject.activeInHierarchy && r.bounds.size.magnitude < .6f && Vector3.Distance(r.bounds.center, at) < .6f);
            // (the weather's rim behind the ball is background treatment, not the ball: excluded)
            return (ball ? ball.GetComponentsInChildren<Renderer>() : Array.Empty<Renderer>()).Concat(near).Where(r => !(r is ParticleSystemRenderer) && !r.name.StartsWith("Majestic weather ball halo")).Distinct().ToArray();
        }

        static Renderer[] FlagRenderers(Hole h)
        {
            var pin = HoleView.ToWorld(h.Pin);
            return Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)
                .Where(r => r.enabled && r.gameObject.activeInHierarchy && Vector3.Distance(r.bounds.center, pin) < 5 && (r.name.ToUpperInvariant().Contains("FLAG") || r.name.ToUpperInvariant().Contains("POLE"))).ToArray();
        }

        // ================================================================== tennis
        static IEnumerable<object> TennisSlot(Slot s, bool first)
        {
            Log($"--- {s.id} {s.place} {s.weather}");
            Time.timeScale = 1; Time.captureFramerate = 0;
            TennisVenue.Selected = s.venue;
            Environment.SetEnvironmentVariable("DREAM_WEATHER", s.weather.ToString());
            MajesticWeather.SetEnabled(true); MajesticWeather.Source = null;
            var load = UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Tennis"); while (!load.isDone) yield return null;
            TennisGame tennis = null; while (!tennis || !tennis.Initialized) { tennis = Object.FindFirstObjectByType<TennisGame>(); yield return null; }
            foreach (var o in WaitSeconds(3)) yield return o;
            var conditions = tennis.GetComponent<TennisConditions>();
            if (conditions) typeof(TennisConditions).GetField("lastGame", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).SetValue(conditions, -1);
            TennisConditions.Boundary(tennis);
            foreach (var o in WaitSeconds(3)) yield return o;
            var presentation = tennis.GetComponent<TennisPresentation>(); if (presentation) presentation.Finish();
            foreach (var o in Wait(20)) yield return o;
            tennis.enabled = false;
            var cam = tennis.GameplayCamera; cam.aspect = 16f / 9;
            TennisShoulderCamera.Frame(tennis.Player.transform.position, false, Vector3.zero, false, cam.aspect, out var pos, out var look, out var fov);
            cam.transform.position = pos; cam.transform.LookAt(look); cam.fieldOfView = fov;
            while (!MajesticWeather.Current) yield return null;
            var mw = MajesticWeather.Current;
            var view = tennis.GetComponentInChildren<WeatherView>();
            var hole = new Hole { Centerline = new[] { CoursePoint.Zero, new CoursePoint(0, 80) }, Ground = _ => 0, Theme = s.venue == TennisVenueKind.Volcano ? "magma" : "" };
            var wind = new Wind(s.weather == Weather.Storm ? 10 : s.weather == Weather.Gusty ? 7 : 2, 45);
            void SetWeather(Weather w) { view.Begin(cam, hole, w, wind, true); DreamEnvironment.Current?.SetWeather(w); mw.Restart(); }
            SetWeather(s.weather);
            foreach (var o in Wait(3)) yield return o;
            mw.Snap();
            foreach (var o in Wait(20)) yield return o;
            Log($"{s.id}: family={mw.Family} phase={mw.Phase} active={mw.Active} weather={mw.Weather} play={mw.PlayShare}");
            State(s, mw);
            if (Job("refs")) { foreach (var o in Refs(s, cam, mw, () => SetWeather(Weather.Clear), () => SetWeather(s.weather), null)) yield return o; }
            if (Job("coverage") && first) Coverage(s, cam);
            // tennis between games has no ball in play: the far player stands in for it (contrast + fog), the near player for the flag
            if (Job("read")) { foreach (var o in Read(s, cam, mw, tennis.Opponent.GetComponentsInChildren<Renderer>(), tennis.Player.GetComponentsInChildren<Renderer>())) yield return o; }
            if (Job("cost")) { foreach (var o in Cost(s, cam, mw, () => SetWeather(Weather.Clear), () => SetWeather(s.weather), null)) yield return o; }
            if (Job("toggle") && first) { foreach (var o in Toggle(s, cam, mw)) yield return o; }
            if (Job("offpath")) { foreach (var o in OffPath(s, cam, mw)) yield return o; }
            // the rule: never during a rally (a ball put in play: what falls stops, the court stays wet)
            if (s.weather == Weather.Rain || s.weather == Weather.Storm)
            {
                SetWeather(s.weather); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(10)) yield return o;
                float before = mw.Now.Precip;
                tennis.InjectBall(new Vector3(0, 1.2f, 6), new Vector3(0, 3, -14));
                foreach (var o in WaitSeconds(2.2f)) yield return o;
                float during = mw.Now.Precip; bool fallOn = mw.Fx != null && mw.Fx.Fall.enabled; int drops = mw.Fx?.Drops ? mw.Fx.Drops.particleCount : 0;
                Save(cam, Path.Combine(Out, $"{s.id}_rally_hold.png"));
                // the real tennis ball, in play: its contrast against the wet court (READABILITY, tennis)
                var tb = GameObject.Find("Tennis ball");
                if (Job("read") && tb) { foreach (var o in Read(new Slot { id = s.id + "ball", venue = s.venue, weather = s.weather, place = s.place }, cam, mw, tb.GetComponentsInChildren<Renderer>(), null)) yield return o; }
                bool pass = before > .3f && during < .01f && !fallOn && drops == 0 && mw.Now.Wet > .3f;
                Log($"{s.id} RALLY_HOLD precip before={before:F2} during={during:F3} fallLayer={fallOn} drops={drops} wet={mw.Now.Wet:F2} phase={mw.Phase} -> {(pass ? "PASS" : "FAIL")}");
                Result(s.id + "_rally_hold", $"{{\"before\":{before:F3},\"during\":{during:F3},\"fallLayer\":{(fallOn ? "true" : "false")},\"drops\":{drops},\"wet\":{mw.Now.Wet:F2},\"pass\":{(pass ? "true" : "false")}}}");
            }
            if (Job("rim"))
            {
                // the tennis ball's comet outline in play, the tennis boost off then on: a still mid-flight + the ball's
                // contrast (READ <id>ball_off / _on), then a half-speed clip with the boost on
                SetWeather(s.weather); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(10)) yield return o;
                var settings = new (string tag, bool on, float floor, float width, float inner)[] { ("off", false, 0, 0, 0), ("r1", true, 1.6f, .10f, .88f), ("r2", true, 2.2f, .12f, .9f), ("r3", true, 2.2f, .08f, .8f) };
                foreach (var st in settings)
                {
                    MajesticWeatherComet.TennisBoost = st.on; string tag = st.tag;
                    if (st.on) { MajesticWeatherComet.TennisFloor = st.floor; MajesticWeatherComet.TennisWidth = st.width; MajesticWeatherComet.TennisInner = st.inner; MajesticWeatherComet.TennisHot = new Color(1f, .82f, .45f); }
                    tennis.InjectBall(new Vector3(0, 1.2f, 6), new Vector3(0, 3, -14));
                    foreach (var o in WaitSeconds(.35f)) yield return o;
                    var tb = GameObject.Find("Tennis ball");
                    Save(cam, Path.Combine(Out, $"{s.id}_rim_tennis_{tag}.png"));
                    if (tb) { var vp = cam.WorldToViewportPoint(tb.transform.position); Log($"{s.id} RIM tennis ball ({tag}) at viewport {vp.x:F3},{vp.y:F3} z={vp.z:F1}"); }
                    // (1) as the integration chat measured (the ball's own renderers), (2) the ball with its outline as one object
                    if (tb) { foreach (var o in Read(new Slot { id = $"{s.id}ball_{tag}", venue = s.venue, weather = s.weather, place = s.place }, cam, mw, tb.GetComponentsInChildren<Renderer>(), null)) yield return o; }
                    if (tb) { foreach (var o in Read(new Slot { id = $"{s.id}ball_{tag}_withrim", venue = s.venue, weather = s.weather, place = s.place }, cam, mw, tb.GetComponentsInChildren<Renderer>().Concat(Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.name.StartsWith("Majestic weather ball comet"))).ToArray(), null)) yield return o; }
                }
                MajesticWeatherComet.TennisBoost = true;
                tennis.InjectBall(new Vector3(0, 1.2f, 6), new Vector3(0, 3, -14));
                foreach (var o in Record(cam, Path.Combine(Out, $"{s.id}_rim_tennis.mp4"), 150, f => { if (f == 40) tennis.InjectBall(new Vector3(0, 1.2f, 6), new Vector3(1.5f, 3.5f, -15)); }, 60)) yield return o;
            }
            if (Job("video")) { foreach (var o in Video(s, cam, mw, view, () => SetWeather(s.weather), tennis)) yield return o; }
        }

        // ================================================================== stills: majestic / legacy (today) / clear
        static IEnumerable<object> Refs(Slot s, Camera cam, MajesticWeather mw, Action clear, Action weather, Action clearing)
        {
            foreach (var o in WaitSeconds(2)) yield return o;   // let rain / flakes / petals fill in (they spawn over time)
            Save(cam, Path.Combine(Out, $"{s.id}_majestic.png"));
            MajesticWeather.SetEnabled(false);
            if (clearing != null) { weather(); foreach (var o in Wait(3)) yield return o; clearing(); foreach (var o in WaitSeconds(4)) yield return o; }
            foreach (var o in WaitSeconds(1.5f)) yield return o;
            Save(cam, Path.Combine(Out, $"{s.id}_legacy.png"));
            MajesticWeather.SetEnabled(true);
            clear(); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(15)) yield return o;
            Save(cam, Path.Combine(Out, $"{s.id}_clear.png"));
            weather(); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(15)) yield return o;
            if (clearing != null) { clearing(); foreach (var o in WaitSeconds(6)) yield return o; }
        }

        static void State(Slot s, MajesticWeather mw)
        {
            var g = new StringBuilder("{");
            void V(string n) { var v = Shader.GetGlobalVector(n); g.Append($"\"{n}\":[{v.x:F4},{v.y:F4},{v.z:F4},{v.w:F4}],"); }
            foreach (var n in new[] { "_MajWet", "_MajCover", "_MajCoverFx", "_MajFogColor", "_MajFog", "_MajFogGlow", "_MajObserver", "_MajSkyRefl", "_MajSunDir", "_MajWind", "_MajTime", "_MajFlash", "_MajWater", "_GolfWind", "_RSkyAerial" }) V(n);
            g.Append($"\"_MajWeatherOn\":{Shader.GetGlobalFloat("_MajWeatherOn")},\"phase\":\"{mw.Phase}\",\"family\":\"{mw.Family}\",\"weather\":\"{mw.Weather}\",");
            g.Append($"\"fog\":[{RenderSettings.fogStartDistance:F1},{RenderSettings.fogEndDistance:F1}],\"look\":{JsonUtility.ToJson(mw.Now)}}}");
            Result(s.id + "_state", g.ToString());
        }

        // ================================================================== READABILITY
        static IEnumerable<object> Read(Slot s, Camera cam, MajesticWeather mw, Renderer[] ball, Renderer[] flag)
        {
            // today's contrast at the same camera, for comparison (the layer off)
            (float c, int px, float lo, float lb) legacyBall = (-1, 0, 0, 0), legacyFlag = (-1, 0, 0, 0);
            Texture2D F = null;
            MajesticWeather.SetEnabled(false); foreach (var o in WaitSeconds(1f)) yield return o;
            F = Grab(cam); legacyBall = Contrast(ball); legacyFlag = Contrast(flag); Object.DestroyImmediate(F);
            MajesticWeather.SetEnabled(true); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(6)) yield return o;
            F = Grab(cam);
            (float c, int px, float lo, float lb) Contrast(Renderer[] rs)
            {
                if (rs == null || rs.Length == 0) return (-1, 0, 0, 0);
                // hide the surface but keep its shadow: the mask is the object's own pixels, not its shadow too
                var modes = rs.Select(r => r.shadowCastingMode).ToArray();
                foreach (var r in rs) r.shadowCastingMode = ShadowCastingMode.ShadowsOnly;
                var B = Grab(cam);
                for (int k = 0; k < rs.Length; k++) rs[k].shadowCastingMode = modes[k];
                var a = F.GetPixels32(); var b = B.GetPixels32(); double so = 0, sb = 0; int n = 0;
                for (int i = 0; i < a.Length; i++)
                {
                    int d = Math.Abs(a[i].r - b[i].r) + Math.Abs(a[i].g - b[i].g) + Math.Abs(a[i].b - b[i].b);
                    if (d < 24) continue;
                    so += Lum(a[i]); sb += Lum(b[i]); n++;
                }
                Object.DestroyImmediate(B);
                if (n < 30) return (-1, n, 0, 0);   // too few pixels to judge (a flag 400 yd away)
                float lo = (float)(so / n), lb = (float)(sb / n);
                return ((Mathf.Max(lo, lb) + .05f) / (Mathf.Min(lo, lb) + .05f), n, lo, lb);
            }
            var ballC = Contrast(ball);
            var flagC = Contrast(flag);
            // the fall layer never draws over the ball's line: the same frame without it differs nowhere in the corridor
            int corridorPx = 0, corridorHit = 0; double corridorDiff = 0;
            var fx = mw.Fx;
            if (fx != null && fx.Fall.enabled && !mw.Tennis)
            {
                fx.Fall.forceRenderingOff = true; fx.Drops.GetComponent<Renderer>().forceRenderingOff = true;
                var C = Grab(cam);
                fx.Fall.forceRenderingOff = false; fx.Drops.GetComponent<Renderer>().forceRenderingOff = false;
                var D = Grab(cam);
                var a = D.GetPixels32(); var c = C.GetPixels32();
                var pa = cam.WorldToViewportPoint(mw.CorridorA); var pb = cam.WorldToViewportPoint(Vector3.Lerp(mw.CorridorA, mw.CorridorB, .35f));
                if (pb.z <= 0) pb = pa;
                for (int y = 0; y < H; y += 2) for (int x = 0; x < W; x += 2)
                {
                    var p = new Vector2((x + .5f) / W, (y + .5f) / H);
                    var ap = (p - (Vector2)pa) * new Vector2(16f / 9, 1); var ab = ((Vector2)pb - (Vector2)pa) * new Vector2(16f / 9, 1);
                    float k = Mathf.Clamp01(Vector2.Dot(ap, ab) / Mathf.Max(ab.sqrMagnitude, 1e-5f));
                    if ((ap - ab * k).magnitude > .07f * .95f) continue;
                    int i = y * W + x; int d = Math.Abs(a[i].r - c[i].r) + Math.Abs(a[i].g - c[i].g) + Math.Abs(a[i].b - c[i].b);
                    corridorPx++; corridorDiff += d / 3.0; if (d > 24) corridorHit++;
                }
                Object.DestroyImmediate(C); Object.DestroyImmediate(D);
            }
            Object.DestroyImmediate(F);
            // near drops: none inside the corridor over 60 frames
            int inside = 0, maxCount = 0, frames = 0;
            var buf = new ParticleSystem.Particle[MajesticWeatherFx.MaxDrops + 8];
            for (int f = 0; f < 60; f++)
            {
                yield return null;
                if (fx == null || !fx.Drops) continue;
                int n = fx.Drops.GetParticles(buf); maxCount = Math.Max(maxCount, n); frames++;
                for (int i = 0; i < n; i++) if (MajesticWeatherFx.InCorridor(buf[i].position, mw, mw.Tennis ? 2.2f * .9f : 3.2f * .9f)) inside++;
            }
            // URP fog (all the ball, flag and players get): linear fog share at their distances
            float Fog(float d) => !RenderSettings.fog ? 0 : RenderSettings.fogMode != FogMode.Linear ? -1 : Mathf.Clamp01((d - RenderSettings.fogStartDistance) / Mathf.Max(.01f, RenderSettings.fogEndDistance - RenderSettings.fogStartDistance));
            var camPos = cam.transform.position;
            float dBall = ball != null && ball.Length > 0 ? Vector3.Distance(camPos, ball[0].bounds.center) : 0;
            float dFlag = flag != null && flag.Length > 0 ? Vector3.Distance(camPos, flag[0].bounds.center) : 0;
            float fogBall = Fog(dBall), fogFlag = Fog(dFlag), fogFar = Fog(dFlag * 1.25f + 1);
            bool contrastOk = (ballC.c < 0 || ballC.c >= 3) && (flagC.c < 0 || flagC.c >= 3);
            bool corridorOk = corridorPx == 0 || corridorHit <= corridorPx * .002f;
            bool fogOk = fogBall <= .15f && fogFlag <= .15f;
            Log($"{s.id} READ (today: ball {legacyBall.c:F2} flag {legacyFlag.c:F2}) ball contrast={ballC.c:F2} ({ballC.px}px L {ballC.lo:F3} vs {ballC.lb:F3}) flag={flagC.c:F2} ({flagC.px}px) corridor fall-layer px={corridorPx} hit={corridorHit} meanDiff={(corridorPx > 0 ? corridorDiff / corridorPx : 0):F2} drops in corridor={inside} (max {maxCount}/{MajesticWeatherFx.MaxDrops}, {frames} frames, rejected {fx?.Rejected}) fog ball={fogBall:F3}@{dBall:F0} flag={fogFlag:F3}@{dFlag:F0} -> contrast {(contrastOk ? "PASS" : "FAIL")} corridor {(corridorOk && inside == 0 ? "PASS" : "FAIL")} fog {(fogOk ? "PASS" : "FAIL")}");
            Result(s.id + "_read", $"{{\"ballToday\":{legacyBall.c:F3},\"flagToday\":{legacyFlag.c:F3},\"ball\":{ballC.c:F3},\"ballPx\":{ballC.px},\"flag\":{flagC.c:F3},\"flagPx\":{flagC.px},\"corridorPx\":{corridorPx},\"corridorHit\":{corridorHit},\"dropsInCorridor\":{inside},\"maxDrops\":{maxCount},\"fogBall\":{fogBall:F3},\"fogFlag\":{fogFlag:F3},\"dBall\":{dBall:F1},\"dFlag\":{dFlag:F1},\"contrastPass\":{B(contrastOk)},\"corridorPass\":{B(corridorOk && inside == 0)},\"fogPass\":{B(fogOk)}}}");
        }
        static string B(bool b) => b ? "true" : "false";
        static double Lum(Color32 c)
        {
            double L(byte v) { double x = v / 255.0; return x <= .04045 ? x / 12.92 : Math.Pow((x + .055) / 1.055, 2.4); }
            return .2126 * L(c.r) + .7152 * L(c.g) + .0722 * L(c.b);
        }

        // ================================================================== WEATHER_COST (interleaved A/B, chat 9's method)
        sealed class Acc { public string name; public readonly List<double> gpu = new(), sync = new(), sync2 = new(); public long tri, draw; }
        static IEnumerable<object> Cost(Slot s, Camera cam, MajesticWeather mw, Action clear, Action weather, Action clearing)
        {
            int rounds = int.TryParse(Environment.GetEnvironmentVariable("MW_ROUNDS"), out var r) ? r : 4;
            var variants = new (string name, Action apply)[]
            {
                ("clear", () => { MajesticWeather.SetEnabled(true); clear(); }),
                ("majestic", () => { MajesticWeather.SetEnabled(true); weather(); }),
                ("legacy", () => { weather(); MajesticWeather.SetEnabled(false); }),
            };
            var acc = variants.ToDictionary(v => v.name, v => new Acc { name = v.name });
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = (GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset)?.msaaSampleCount ?? 1 }; rt.Create();
            var prevTarget = cam.targetTexture; cam.targetTexture = rt; cam.enabled = true;
            for (int round = 0; round < rounds; round++)
                foreach (var (name, apply) in variants)
                {
                    apply(); foreach (var o in Wait(3)) yield return o;
                    if (MajesticWeather.Enabled) mw.Snap();
                    if (clearing != null && name != "clear") { clearing(); foreach (var o in Wait(3)) yield return o; mw.Snap(); }
                    foreach (var o in Sample(cam, acc[name])) yield return o;
                }
            cam.targetTexture = prevTarget;
            rt.Release(); Object.DestroyImmediate(rt);
            MajesticWeather.SetEnabled(true); weather(); foreach (var o in Wait(3)) yield return o; mw.Snap();
            double Px(Acc a) => (Pct(a.sync2, .25) - Pct(a.sync, .25)) / 3;
            var c = acc["clear"]; var m = acc["majestic"]; var l = acc["legacy"];
            double dM = Px(m) - Px(c), dL = Px(l) - Px(c), dMg = Pct(m.gpu, .5) - Pct(c.gpu, .5), dLg = Pct(l.gpu, .5) - Pct(c.gpu, .5);
            bool pass = dM <= 1.0;
            Log($"{s.id} COST pixelGPU1080 clear={Px(c):F2} majestic={Px(m):F2} legacy={Px(l):F2} | delta majestic={dM:+0.00;-0.00} legacy={dL:+0.00;-0.00} ms | ftm gpu median delta majestic={dMg:+0.00;-0.00} legacy={dLg:+0.00;-0.00} | sync1x clear/maj/leg={Pct(c.sync, .25):F2}/{Pct(m.sync, .25):F2}/{Pct(l.sync, .25):F2} | tris {c.tri}/{m.tri}/{l.tri} draws {c.draw}/{m.draw}/{l.draw} -> {(pass ? "PASS" : "FAIL")}");
            Result(s.id + "_cost", $"{{\"pixelClear\":{Px(c):F3},\"pixelMajestic\":{Px(m):F3},\"pixelLegacy\":{Px(l):F3},\"deltaMajestic\":{dM:F3},\"deltaLegacy\":{dL:F3},\"ftmDeltaMajestic\":{dMg:F3},\"ftmDeltaLegacy\":{dLg:F3},\"sync1x\":[{Pct(c.sync, .25):F3},{Pct(m.sync, .25):F3},{Pct(l.sync, .25):F3}],\"tris\":[{c.tri},{m.tri},{l.tri}],\"draws\":[{c.draw},{m.draw},{l.draw}],\"samples\":[{c.sync.Count},{m.sync.Count},{l.sync.Count}],\"pass\":{B(pass)}}}");
        }

        static IEnumerable<object> Sample(Camera cam, Acc acc)
        {
            int n = int.TryParse(Environment.GetEnvironmentVariable("MW_SAMPLES"), out var sN) ? sN : 24;
            foreach (var o in Wait(4)) yield return o;
            var draw = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Render, "Draw Calls Count");
            var tri = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Render, "Triangles Count");
            var timings = new FrameTiming[1];
            foreach (var o in Wait(2)) yield return o;
            for (int i = 0; i < n; i++)
            {
                FrameTimingManager.CaptureFrameTimings();
                if (FrameTimingManager.GetLatestTimings(1, timings) > 0 && timings[0].gpuFrameTime > 0) acc.gpu.Add(timings[0].gpuFrameTime);
                if (draw.LastValue > 0 && (acc.draw == 0 || draw.LastValue < acc.draw)) { acc.draw = draw.LastValue; acc.tri = tri.LastValue; }
                yield return null;
            }
            draw.Dispose(); tri.Dispose();
            // synchronous proxy at 1x and 2x of 1080p: (T2x - T1x) / 3 = per-pixel GPU cost of one 1080p frame
            cam.enabled = false;
            var px = new Texture2D(1, 1, TextureFormat.RGBA32, false);
            var keep = cam.targetTexture; int aa = keep ? keep.antiAliasing : 1;
            foreach (var (scale, list) in new[] { (1f, acc.sync), (2f, acc.sync2) })
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

        // ================================================================== TOGGLE_RESTORES
        static IEnumerable<object> Toggle(Slot s, Camera cam, MajesticWeather mw)
        {
            Time.timeScale = 0;   // freeze every animation (shader _Time, particles, clouds) so frames can be compared exactly
            foreach (var o in Wait(4)) yield return o;
            MajesticWeather.SetEnabled(false); foreach (var o in Wait(4)) yield return o;
            var t0 = Grab(cam);
            MajesticWeather.SetEnabled(true); foreach (var o in Wait(4)) yield return o; mw.Snap(); foreach (var o in Wait(3)) yield return o;
            var t1 = Grab(cam);
            MajesticWeather.SetEnabled(false); foreach (var o in Wait(4)) yield return o;
            var t2 = Grab(cam);
            var (max02, n02) = Diff(t0, t2); var (max01, n01) = Diff(t0, t1);
            // the shaders' off path is the original shader: the same frozen frame with EnvironmentSurface.hlsl unpatched
            // the shaders' off path is the original shaders: the same frozen frame with every patched shader file unpatched
            string origDir = Environment.GetEnvironmentVariable("MW_ORIG_DIR");
            int maxPU = -1, nPU = -1;
            if (!string.IsNullOrEmpty(origDir) && Directory.Exists(origDir))
            {
                var files = Directory.GetFiles(origDir, "*", SearchOption.AllDirectories).Select(f => f.Substring(origDir.Length + 1)).Where(f => f.StartsWith("Assets/")).ToArray();
                var patched = files.ToDictionary(f => f, f => File.ReadAllText(f));
                bool async = ShaderUtil.allowAsyncCompilation; ShaderUtil.allowAsyncCompilation = false;
                AssetDatabase.StartAssetEditing();
                foreach (var f in files) File.WriteAllText(f, File.ReadAllText(Path.Combine(origDir, f)));
                AssetDatabase.StopAssetEditing();
                foreach (var f in files) AssetDatabase.ImportAsset(f, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
                foreach (var o in Wait(12)) yield return o;
                var u = Grab(cam);
                foreach (var f in files) File.WriteAllText(f, patched[f]);
                foreach (var f in files) AssetDatabase.ImportAsset(f, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
                foreach (var o in Wait(12)) yield return o;
                var p2 = Grab(cam);
                (maxPU, nPU) = Diff(t2, u);
                var (maxRe, nRe) = Diff(t2, p2);
                Log($"{s.id} TOGGLE off-path vs unpatched shaders ({files.Length} files): maxDiff={maxPU} pixels={nPU} (re-patched vs before: max {maxRe} px {nRe})");
                File.WriteAllBytes(Path.Combine(Out, $"{s.id}_toggle_unpatched.png"), u.EncodeToPNG());
                Object.DestroyImmediate(u); Object.DestroyImmediate(p2);
                ShaderUtil.allowAsyncCompilation = async;
            }
            File.WriteAllBytes(Path.Combine(Out, $"{s.id}_toggle_off_before.png"), t0.EncodeToPNG());
            File.WriteAllBytes(Path.Combine(Out, $"{s.id}_toggle_on.png"), t1.EncodeToPNG());
            File.WriteAllBytes(Path.Combine(Out, $"{s.id}_toggle_off_after.png"), t2.EncodeToPNG());
            bool pass = max02 == 0 && n01 > 0 && maxPU <= 2;   // (a 2/255 tolerance for shader recompilation rounding)
            Log($"{s.id} TOGGLE off-before vs off-after: maxDiff={max02} pixels={n02}; on vs off pixels={n01} (max {max01}) -> {(pass ? "PASS" : "FAIL")}");
            Result(s.id + "_toggle", $"{{\"offVsOffMax\":{max02},\"offVsOffPixels\":{n02},\"onVsOffPixels\":{n01},\"offVsUnpatchedMax\":{maxPU},\"offVsUnpatchedPixels\":{nPU},\"pass\":{B(pass)}}}");
            Object.DestroyImmediate(t0); Object.DestroyImmediate(t1); Object.DestroyImmediate(t2);
            MajesticWeather.SetEnabled(true); Time.timeScale = 1;
            foreach (var o in Wait(3)) yield return o; mw.Snap();
        }

        static (int max, int n) Diff(Texture2D a, Texture2D b)
        {
            var x = a.GetPixels32(); var y = b.GetPixels32(); int max = 0, n = 0;
            for (int i = 0; i < x.Length; i++)
            {
                int d = Math.Max(Math.Abs(x[i].r - y[i].r), Math.Max(Math.Abs(x[i].g - y[i].g), Math.Abs(x[i].b - y[i].b)));
                if (d > 0) n++; if (d > max) max = d;
            }
            return (max, n);
        }

        // ================================================================== OFF PATH (patched shaders, layer off) == original shaders
        // Same frozen frame, no asset reimport: every material on a patched world shader is switched to its "<name>__orig"
        // twin (the unpatched source, compiled side by side: tools/make_orig.py), rendered, switched back. A second render
        // of the patched frame gives the noise floor (things that animate on unscaled time); only pixels stable across the
        // two patched renders are compared.
        static IEnumerable<object> OffPath(Slot s, Camera cam, MajesticWeather mw)
        {
            var only = (Environment.GetEnvironmentVariable("MW_OFFPATH_SLOTS") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries);
            if (only.Length > 0 && !only.Contains(s.id)) yield break;
            var twins = new Dictionary<Shader, Shader>(); var pats = new Dictionary<Shader, Shader>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                foreach (var m in r.sharedMaterials)
                {
                    if (!m || !m.shader || twins.ContainsKey(m.shader)) continue;
                    var t = Shader.Find(m.shader.name + "__orig"); var pt = Shader.Find(m.shader.name + "__pat");
                    if (t && pt) { twins[m.shader] = t; pats[m.shader] = pt; }
                }
            var mats = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).SelectMany(r => r.sharedMaterials).Where(m => m && m.shader && twins.ContainsKey(m.shader)).Distinct().ToArray();
            bool async = ShaderUtil.allowAsyncCompilation; ShaderUtil.allowAsyncCompilation = false;
            Time.timeScale = 0;
            MajesticWeather.SetEnabled(false);
            // MW_OFFPATH_NOAO=1: screen-space AO off for the comparison (it reads a depth-normals prepass whose draw order
            // changes with any shader swap: tie-depth speckles on objects that were never patched)
            var aoFeatures = new List<ScriptableRendererFeature>();
            if (Environment.GetEnvironmentVariable("MW_OFFPATH_NOAO") == "1" && GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp)
            {
                var list = typeof(UniversalRenderPipelineAsset).GetField("m_RendererDataList", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)?.GetValue(urp) as ScriptableRendererData[];
                if (list != null) foreach (var d in list) if (d) foreach (var f in d.rendererFeatures) if (f && f.isActive && f.GetType().Name.Contains("AmbientOcclusion")) { f.SetActive(false); aoFeatures.Add(f); }
                Log($"{s.id} OFFPATH: screen-space AO off for the comparison ({aoFeatures.Count} feature(s))");
            }
            foreach (var o in Wait(5)) yield return o;
            var p1 = Grab(cam);
            var keep = mats.Select(m => m.shader).ToArray();
            var kw = mats.Select(m => m.shaderKeywords).ToArray();
            void Swap(int to)   // 0 patched (live), 1 original twin, 2 patched twin (control)
            {
                for (int i = 0; i < mats.Length; i++)
                {
                    int q = mats[i].renderQueue;
                    mats[i].shader = to == 1 ? twins[keep[i]] : to == 2 ? pats[keep[i]] : keep[i];
                    mats[i].shaderKeywords = kw[i]; mats[i].renderQueue = q;
                }
            }
            // let every variant finish compiling (an async placeholder renders cyan), then grab
            IEnumerable<object> Settle()
            {
                for (int k = 0; k < 6; k++) { Object.DestroyImmediate(Grab(cam)); foreach (var o in Wait(2)) yield return o; }
                float until = Time.realtimeSinceStartup + 40;
                while (ShaderUtil.anythingCompiling && Time.realtimeSinceStartup < until) { Object.DestroyImmediate(Grab(cam)); yield return null; }
                foreach (var o in Wait(3)) yield return o;
            }
            Swap(1); foreach (var o in Settle()) yield return o;   // warm-up of both twin sets
            Swap(2); foreach (var o in Settle()) yield return o;
            Swap(0); foreach (var o in Settle()) yield return o;
            Object.DestroyImmediate(p1); p1 = Grab(cam);
            Swap(1); foreach (var o in Settle()) yield return o;
            var u = Grab(cam);
            Swap(2); foreach (var o in Settle()) yield return o;
            var ctl = Grab(cam);
            Swap(0); foreach (var o in Settle()) yield return o;
            var p2 = Grab(cam);
            // twin against twin: the original source vs the patched source, both through the same swap
            var (maxTT, nTT) = Diff(u, ctl);
            var (maxPC, nPC) = Diff(p1, ctl);
            Log($"{s.id} OFFPATH twin-vs-twin (original vs patched source, layer off): differing {nTT}, max {maxTT}; swap artifact (live patched vs patched twin): differing {nPC}, max {maxPC}");
            Result(s.id + "_offpath_twins", $"{{\"differing\":{nTT},\"max\":{maxTT},\"swapArtifactPx\":{nPC},\"swapArtifactMax\":{maxPC},\"pass\":{B(maxTT <= 2)}}}");
            Object.DestroyImmediate(ctl);
            var a = p1.GetPixels32(); var b = p2.GetPixels32(); var c = u.GetPixels32();
            int stable = 0, max = 0, n = 0, noise = 0;
            var diff = new Texture2D(W, H, TextureFormat.RGB24, false); var dpx = new Color32[a.Length];
            for (int i = 0; i < a.Length; i++)
            {
                int dn = Math.Max(Math.Abs(a[i].r - b[i].r), Math.Max(Math.Abs(a[i].g - b[i].g), Math.Abs(a[i].b - b[i].b)));
                if (dn > 0) { noise++; dpx[i] = new Color32(0, 0, 90, 255); continue; }
                stable++;
                int d = Math.Max(Math.Abs(a[i].r - c[i].r), Math.Max(Math.Abs(a[i].g - c[i].g), Math.Abs(a[i].b - c[i].b)));
                if (d > 0) n++; if (d > max) max = d;
                byte v = (byte)Math.Min(255, d * 20); dpx[i] = new Color32(v, v, v, 255);
            }
            diff.SetPixels32(dpx); diff.Apply();
            File.WriteAllBytes(Path.Combine(Out, $"{s.id}_offpath_diff.png"), diff.EncodeToPNG());
            File.WriteAllBytes(Path.Combine(Out, $"{s.id}_offpath_patched.jpg"), p1.EncodeToJPG(92));
            File.WriteAllBytes(Path.Combine(Out, $"{s.id}_offpath_original.jpg"), u.EncodeToJPG(92));
            Object.DestroyImmediate(p1); Object.DestroyImmediate(p2); Object.DestroyImmediate(u); Object.DestroyImmediate(diff);
            ShaderUtil.allowAsyncCompilation = async;
            foreach (var f in aoFeatures) f.SetActive(true);
            bool pass = max <= 2 && mats.Length > 0;   // rounding only (coordinator 10-18: <= 2/255)
            Log($"{s.id} OFFPATH {mats.Length} materials on {twins.Count} patched shaders: stable px {stable} (noise {noise}), differing {n}, max {max} -> {(pass ? "PASS" : "FAIL")}");
            Result(s.id + "_offpath", $"{{\"materials\":{mats.Length},\"shaders\":{twins.Count},\"stable\":{stable},\"noise\":{noise},\"differing\":{n},\"max\":{max},\"pass\":{B(pass)}}}");
            MajesticWeather.SetEnabled(true); Time.timeScale = 1;
            foreach (var o in Wait(3)) yield return o; mw.Snap();
        }

        // ================================================================== DETERMINISM
        static void Determinism()
        {
            var fails = new List<string>();
            foreach (Weather w in Enum.GetValues(typeof(Weather)))
                foreach (Sky f in Enum.GetValues(typeof(Sky)))
                    foreach (bool t in new[] { false, true })
                    {
                        var a = JsonUtility.ToJson(MajesticWeatherRules.For(w, f, t)); var b = JsonUtility.ToJson(MajesticWeatherRules.For(w, f, t));
                        if (a != b) fails.Add($"For({w},{f},{t})");
                    }
            for (int i = 0; i < 400; i++)
            {
                double utc = 1792263600 + i * .37;
                if (MajesticWeatherRules.Gust(12345, utc, 1) != MajesticWeatherRules.Gust(12345, utc, 1)) fails.Add("Gust " + i);
            }
            int differ = 0; for (int i = 0; i < 100; i++) if (Mathf.Abs(MajesticWeatherRules.Gust(12345, 1792263600 + i, 1) - MajesticWeatherRules.Gust(999, 1792263600 + i, 1)) > 1e-4f) differ++;
            if (differ < 50) fails.Add("Gust ignores the seed");
            // the play-window rule (tennis): arrival, between games and after the match only
            if (!MajesticWeatherRules.TennisWeatherShows(false, false, false, 0, -1)) fails.Add("arrival");
            if (MajesticWeatherRules.TennisWeatherShows(true, false, false, 0, 0)) fails.Add("rally");
            if (MajesticWeatherRules.TennisWeatherShows(false, false, false, 0, 0)) fails.Add("between points");
            if (!MajesticWeatherRules.TennisWeatherShows(false, false, false, 1, 0)) fails.Add("between games");
            if (!MajesticWeatherRules.TennisWeatherShows(false, true, false, 6, 5)) fails.Add("after the match");
            if (!MajesticWeatherRules.TennisWeatherShows(true, false, true, 0, -1)) fails.Add("intro");
            // gameplay visibility is the shared rule
            var p = new Vector3(40, 2, 120); var obs = new Vector3(0, 3, 10);
            if (MajesticWeatherRules.Visibility(p, obs) != DreamConditions.Visibility(p.x, p.y, p.z, obs.x, obs.y, obs.z)) fails.Add("visibility");
            // seed -> weather is the game's own (DreamConditions / RoundEvents): same seed, same sequence
            for (int s = 1; s < 40; s++) for (int h = 0; h < 18; h++) if (DreamConditions.WeatherFor(s * 7919, h) != DreamConditions.WeatherFor(s * 7919, h)) fails.Add("WeatherFor");
            Log($"DETERMINISM pure rules: {(fails.Count == 0 ? "PASS" : "FAIL " + string.Join(", ", fails))}");
            Result("determinism_rules", $"{{\"fails\":[{string.Join(",", fails.Select(f => "\"" + f + "\""))}],\"pass\":{B(fails.Count == 0)}}}");
        }

        /// The published state across quality tiers (run from a slot): every tier must publish the same globals.
        static IEnumerable<object> Tiers(Slot s, MajesticWeather mw)
        {
            int keep = QualitySettings.GetQualityLevel(); var seen = new List<string>();
            for (int q = 0; q < QualitySettings.names.Length; q++)
            {
                QualitySettings.SetQualityLevel(q, true); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(2)) yield return o;
                var sb = new StringBuilder();
                foreach (var n in new[] { "_MajWet", "_MajCover", "_MajFog", "_MajFogColor", "_MajObserver", "_MajWind" }) sb.Append(n + Shader.GetGlobalVector(n).ToString("F4") + ";");
                sb.Append("gust" + mw.GustNow.ToString("F4"));
                seen.Add(sb.ToString());
            }
            QualitySettings.SetQualityLevel(keep, true);
            bool pass = seen.Distinct().Count() == 1;
            Log($"{s.id} DETERMINISM tiers ({seen.Count}): {(pass ? "PASS" : "FAIL")} {(pass ? "" : string.Join(" | ", seen.Distinct()))}");
            Result(s.id + "_tiers", $"{{\"tiers\":{seen.Count},\"distinct\":{seen.Distinct().Count()},\"pass\":{B(pass)}}}");
        }

        // ================================================================== video (muted, H.264)
        static IEnumerable<object> Video(Slot s, Camera cam, MajesticWeather mw, WeatherView view, Action weather, TennisGame tennis)
        {
            var only = (Environment.GetEnvironmentVariable("MW_VIDEO_SLOTS") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries);
            if (only.Length > 0 && !only.Contains(s.id)) yield break;
            float seconds = float.TryParse(Environment.GetEnvironmentVariable("MW_VIDEO_SECONDS"), out var vs) ? vs : 5;
            if (s.clearing) seconds = Mathf.Max(seconds, 7);
            weather(); foreach (var o in Wait(3)) yield return o; mw.Snap();
            if (Job("det") && s.id != "W02") { foreach (var o in Tiers(s, mw)) yield return o; }
            const int vw = 1280, vh = 720;
            var attrs = new VideoTrackAttributes { frameRate = new MediaRational(30), width = vw, height = vh, includeAlpha = false, bitRateMode = VideoBitrateMode.High };
            string path = Path.Combine(Out, $"{s.id}_{s.fx}.mp4");
            Time.captureFramerate = 30;
            var rt = new RenderTexture(vw, vh, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; rt.Create();
            var flat = new RenderTexture(vw, vh, 0, RenderTextureFormat.ARGB32); flat.Create();
            var tex = new Texture2D(vw, vh, TextureFormat.RGBA32, false);
            int frames = Mathf.RoundToInt(seconds * 30);
            using (var enc = new MediaEncoder(path, attrs))
            {
                for (int f = 0; f < frames; f++)
                {
                    if (s.clearing && f == 20) { view.Change(Weather.Clear); DreamEnvironment.Current?.SetWeather(Weather.Clear); }
                    if ((s.weather == Weather.Storm) && (f == 25 || f == 95)) view.Strike();
                    if (tennis && f == frames / 2 && (s.weather == Weather.Rain || s.weather == Weather.Storm)) tennis.InjectBall(new Vector3(0, 1.2f, 6), new Vector3(0, 3, -14));
                    yield return null;
                    var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.enabled).ToArray();
                    foreach (var c in canvases) c.enabled = false;
                    var prev = cam.targetTexture; cam.targetTexture = rt; cam.Render(); cam.targetTexture = prev;
                    foreach (var c in canvases) c.enabled = true;
                    Graphics.Blit(rt, flat); var a = RenderTexture.active; RenderTexture.active = flat;
                    tex.ReadPixels(new Rect(0, 0, vw, vh), 0, 0); tex.Apply(); RenderTexture.active = a;
                    enc.AddFrame(tex);
                }
            }
            Time.captureFramerate = 0;
            rt.Release(); flat.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(flat); Object.DestroyImmediate(tex);
            Log($"{s.id} VIDEO {path} {frames} frames");
        }

        // ================================================================== RIM: the ball's comet outline, variants A/B/C
        // per variant: the weather still (+ contrast read), and on MW_RIM_MOVE slots (default W01) a clear still and a clip
        // of the ball at rest, crossing the view, and launched down the fairway.
        static IEnumerable<object> Rim(Slot s, Camera cam, MajesticWeather mw, GolfGame golf, Hole h, Action clear, Action weather)
        {
            var moveSlots = (Environment.GetEnvironmentVariable("MW_RIM_MOVE") ?? "W01").Split(',');
            var ball = golf.transform.Find("Ball") ?? GameObject.Find("Ball")?.transform;
            for (int v = 0; v < MajesticWeatherComet.Styles.Length; v++)
            {
                MajesticWeatherComet.Variant = v; string tag = "ABC"[v].ToString();
                weather(); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in WaitSeconds(1.5f)) yield return o;
                Save(cam, Path.Combine(Out, $"{s.id}_rim{tag}.png"));
                var rs = new Slot { id = $"{s.id}rim{tag}", golf = true, hole = s.hole, weather = s.weather, fx = s.fx, place = s.place };
                foreach (var o in Read(rs, cam, mw, BallRenderers(golf), FlagRenderers(h))) yield return o;
                if (!moveSlots.Contains(s.id) || !ball) continue;
                clear(); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(15)) yield return o;
                Save(cam, Path.Combine(Out, $"{s.id}_rim{tag}_clear.png"));
                weather(); foreach (var o in Wait(3)) yield return o; mw.Snap(); foreach (var o in Wait(10)) yield return o;
                // half-speed clip (60 Hz game time, 30 fps video): rest, the ball crossing ~3.5 units in front of the camera
                // at ~15 m/s, rest, then launched down the fairway
                var rest = ball.position; var ct = cam.transform; var fwd = Vector3.ProjectOnPlane(HoleView.ToWorld(h.Pin) - rest, Vector3.up).normalized;
                var cross0 = ct.position + ct.forward * 3.5f - ct.up * .35f;
                float g = 9.81f / .9144f;
                Vector3 At(int f)
                {
                    if (f < 15) return rest;
                    if (f < 51) { float u = (f - 15) / 35f; return cross0 + ct.right * (-5 + 10 * u) + ct.up * (.35f * Mathf.Sin(Mathf.PI * u)); }
                    if (f < 61) return rest;
                    float t = (f - 61) / 60f; return rest + fwd * 45 * t + Vector3.up * (12 * t - .5f * g * t * t);
                }
                foreach (var o in Record(cam, Path.Combine(Out, $"{s.id}_rim{tag}_move.mp4"), 150, f => ball.position = At(f), 60)) yield return o;
                ball.position = rest;
                foreach (var o in Wait(3)) yield return o;
            }
            MajesticWeatherComet.Variant = 0;
        }

        static IEnumerable<object> Record(Camera cam, string path, int frames, Action<int> perFrame, int captureHz = 30)
        {
            const int vw = 1280, vh = 720;
            var attrs = new VideoTrackAttributes { frameRate = new MediaRational(30), width = vw, height = vh, includeAlpha = false, bitRateMode = VideoBitrateMode.High };
            Time.captureFramerate = captureHz;
            var rt = new RenderTexture(vw, vh, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; rt.Create();
            var flat = new RenderTexture(vw, vh, 0, RenderTextureFormat.ARGB32); flat.Create();
            var tex = new Texture2D(vw, vh, TextureFormat.RGBA32, false);
            using (var enc = new MediaEncoder(path, attrs))
            {
                for (int f = 0; f < frames; f++)
                {
                    perFrame(f);
                    yield return null;
                    var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.enabled).ToArray();
                    foreach (var c in canvases) c.enabled = false;
                    var prev = cam.targetTexture; cam.targetTexture = rt; cam.Render(); cam.targetTexture = prev;
                    foreach (var c in canvases) c.enabled = true;
                    Graphics.Blit(rt, flat); var a = RenderTexture.active; RenderTexture.active = flat;
                    tex.ReadPixels(new Rect(0, 0, vw, vh), 0, 0); tex.Apply(); RenderTexture.active = a;
                    enc.AddFrame(tex);
                }
            }
            Time.captureFramerate = 0;
            rt.Release(); flat.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(flat); Object.DestroyImmediate(tex);
            Log($"RIM VIDEO {path} {frames} frames");
        }

        // ================================================================== coverage: which shaders draw the view
        static void Coverage(Slot s, Camera cam)
        {
            var planes = GeometryUtility.CalculateFrustumPlanes(cam);
            var rows = new List<(string shader, float area)>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy || !GeometryUtility.TestPlanesAABB(planes, r.bounds)) continue;
                var b = r.bounds; var mn = new Vector2(1, 1); var mx = new Vector2(0, 0);
                for (int i = 0; i < 8; i++)
                {
                    var c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) * 2 - 1, (i >> 1 & 1) * 2 - 1, (i >> 2 & 1) * 2 - 1));
                    var v = cam.WorldToViewportPoint(c); if (v.z < 0) { mn = Vector2.zero; mx = Vector2.one; break; }
                    mn = Vector2.Min(mn, v); mx = Vector2.Max(mx, v);
                }
                mn = Vector2.Max(mn, Vector2.zero); mx = Vector2.Min(mx, Vector2.one);
                float area = Mathf.Max(0, mx.x - mn.x) * Mathf.Max(0, mx.y - mn.y);
                foreach (var m in r.sharedMaterials) if (m && m.shader) rows.Add((m.shader.name, area));
            }
            var sb = new StringBuilder("shader\tboundsScreenAreaSum\trenderers\n");
            foreach (var g in rows.GroupBy(x => x.shader).OrderByDescending(g => g.Sum(x => x.area))) sb.Append($"{g.Key}\t{g.Sum(x => x.area):F3}\t{g.Count()}\n");
            File.WriteAllText(Path.Combine(Out, $"{s.id}_coverage.tsv"), sb.ToString());
            Log($"{s.id} COVERAGE written");
        }

        // ================================================================== capture
        static Texture2D Grab(Camera cam)
        {
            var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.enabled).ToArray();
            foreach (var c in canvases) c.enabled = false;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; rt.Create();
            var prev = cam.targetTexture; cam.targetTexture = rt; cam.Render(); cam.targetTexture = prev;
            var flat = RenderTexture.GetTemporary(W, H, 0); Graphics.Blit(rt, flat);
            var a = RenderTexture.active; RenderTexture.active = flat;
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply();
            RenderTexture.active = a; RenderTexture.ReleaseTemporary(flat); rt.Release(); Object.DestroyImmediate(rt);
            foreach (var c in canvases) if (c) c.enabled = true;
            return tex;
        }
        static void Save(Camera cam, string path) { var t = Grab(cam); File.WriteAllBytes(path, t.EncodeToPNG()); Object.DestroyImmediate(t); }
    }
}
#endif
