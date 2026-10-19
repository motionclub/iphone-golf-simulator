using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Majestic;
using GolfArcade.EnvironmentArt;
using GolfArcade.Hub;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.PlayTests
{
    /// Integration 10-18 (chat 12): ONE filmed smoke playthrough of the combined project, the way FrameRate60bTests.RuntimeHoldsSixty
    /// walks the game: a tennis serve + rally (autoplay), a golf hole in rain (DREAM_WEATHER=Rain, a real swing), and a plaza walk
    /// (the phone's stick, then an emote). Game view 1920x1080; the film is 1280x720 at 30 fps (H.264, no audio) with a frame-time log.
    /// Runs only with SMOKE_OUT set; windowed (batch mode draws nothing).
    public class IntegrationSmokeFilm
    {
        static string Out => Environment.GetEnvironmentVariable("SMOKE_OUT");
        GameObject host;

        sealed class Recorder
        {
            public const int W = 1280, H = 720, Fps = 30;
#if UNITY_EDITOR
            UnityEditor.Media.MediaEncoder encoder;
#endif
            readonly RenderTexture scaled = new RenderTexture(W, H, 0, RenderTextureFormat.ARGB32); readonly Texture2D tex = new Texture2D(W, H, TextureFormat.RGBA32, false);
            double next = -1;
            public Recorder(string path)
            {
#if UNITY_EDITOR
                encoder = new UnityEditor.Media.MediaEncoder(path, new UnityEditor.Media.VideoTrackAttributes { frameRate = new UnityEditor.Media.MediaRational(Fps), width = W, height = H, includeAlpha = false, bitRateMode = UnityEditor.VideoBitrateMode.Medium });
#endif
            }
            public void Frame()
            {
                double now = Time.realtimeSinceStartupAsDouble; if (next < 0) next = now; if (now < next) return;
                var shot = ScreenCapture.CaptureScreenshotAsTexture(); if (!shot) return;
                Graphics.Blit(shot, scaled);
                var prev = RenderTexture.active; RenderTexture.active = scaled; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = prev;
                Object.Destroy(shot);
                int n = 0;
                while (next <= now && n++ < 4) {
#if UNITY_EDITOR
                    encoder.AddFrame(tex);
#endif
                    next += 1.0 / Fps; }
                if (next <= now) next = now + 1.0 / Fps;
            }
            public void Close()
            {
#if UNITY_EDITOR
                encoder?.Dispose(); encoder = null;
#endif
            }
        }

        [TearDown] public void TearDown()
        {
            Environment.SetEnvironmentVariable("DREAM_WEATHER", null);
            if (host) { try { host.GetComponent<NativeSportsSession>()?.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "smoke", action = "end" })); } catch { } Object.DestroyImmediate(host); }
            HubWorld.EditorDriven = false;
        }

        [UnityTest, Timeout(1800000)]
        public IEnumerator Playthrough()
        {
            if (string.IsNullOrEmpty(Out)) { Assert.Ignore("SMOKE_OUT not set"); yield break; }
            Directory.CreateDirectory(Out);
            var log = new List<string>(); int errors = 0, exceptions = 0;
            Application.logMessageReceived += (m, s, t) => { if (t == LogType.Exception) { exceptions++; if (exceptions < 20) log.Add("EXCEPTION " + m.Split('\n')[0]); } else if (t == LogType.Error) { errors++; if (errors < 20) log.Add("ERROR " + m.Split('\n')[0]); } };
            Time.captureFramerate = 0; Time.timeScale = 1;
#if UNITY_EDITOR
            try { UnityEditor.PlayModeWindow.SetCustomRenderingResolution(1920, 1080, "smoke 1080p"); } catch (Exception e) { Debug.LogWarning("[Smoke] game view: " + e.Message); }
#endif
            yield return null; yield return null;
            log.Add($"game view {Screen.width}x{Screen.height}");
            string only = Environment.GetEnvironmentVariable("SMOKE_ONLY") ?? "";   // "golf" etc: film one segment again
            bool Want(string seg) => only == "" || only.Contains(seg);
            var rec = new Recorder(Path.Combine(Out, only == "" ? "smoke_playthrough.mp4" : $"smoke_{only}.mp4"));
            IEnumerator Film(string label, float seconds, Action<float> each = null)
            {
                var dts = new List<float>(); float t = 0;
                while (t < seconds) { yield return new WaitForEndOfFrame(); rec.Frame(); yield return null; float dt = Time.unscaledDeltaTime; t += dt; dts.Add(dt); each?.Invoke(t); }
                dts.Sort(); float med = dts[dts.Count / 2], p95 = dts[(int)(dts.Count * .95f)];
                log.Add($"{label}: {seconds:0} s, {dts.Count} frames, median {1 / med:0.0} fps, p95 frame {p95 * 1000:0.0} ms (while recording)");
            }
            try
            {
                if (Want("tennis")) {
                // 1. tennis: the opening (drone + intros, cut short), then a serve and rallies on autoplay
                PresentationPolicy.Configure("full", false, true, false);
                yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
                var tennis = Object.FindFirstObjectByType<TennisGame>();
                for (int k = 0; k < 30; k++) yield return null;
                yield return Film("tennis intro", 6f);
                for (float w = 6; w < TennisPresentation.Length; w += Time.unscaledDeltaTime) yield return null;
                tennis.ConfigureMatch(TennisGame.Mode.Exhibition, null, "Rival", "CASUAL MATCH"); tennis.AutoPlay = true; tennis.AutoPlayLean = true;
                for (int k = 0; k < 60; k++) yield return null;
                yield return Film("tennis serve + rally", 30f);
                log.Add($"tennis: {tennis.Match.Scoreboard}, hits {tennis.Hits}, longest rally {tennis.LongestRally}");
                tennis.AutoPlay = false;
                }

                if (Want("golf")) {
                // 2. golf in rain: hole 7 (Cliffside, Majestic layer), a real swing and its flight. Started the way chat W's weather harness
                // starts a hole (MajesticWeatherShots.GolfSlot): the round first, then the hole, then the rain view itself.
                Environment.SetEnvironmentVariable("DREAM_WEATHER", "Rain");
                yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
                GolfGame golf = null; CameraRig rig = null;
                for (int k = 0; k < 600 && (!golf || !rig || !HoleView.Current); k++) { golf = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>(); yield return null; }
                golf.ChooseHoles(0); golf.Play();
                for (int k = 0; k < 60; k++) yield return null;
                MajesticWeather.SetEnabled(true);
                golf.PrepareNativeAddress(); golf.JumpToHole(7); golf.DropBall(golf.CurrentHole.Tee);
                for (int k = 0; k < 120; k++) yield return null;
                var view = golf.WeatherShown;
                if (!view || view.Weather != Weather.Rain) view = WeatherView.Create(golf.transform, EventSounds.Create(golf.transform));
                view.Begin(rig.Camera, golf.CurrentHole, Weather.Rain, new Wind(4, 45), true);
                DreamEnvironment.Current?.SetWeather(Weather.Rain);
                log.Add($"golf: course hole {golf.CurrentHole.Number}, weather view {view.Weather}");
                for (int k = 0; k < 60; k++) yield return null;
                yield return Film("golf hole 7 in rain, address", 4f);
                golf.NativeReady(); UnityEngine.Random.InitState(902); golf.NativeSwing(.78f);
                yield return Film("golf hole 7 in rain, swing + flight", 12f);
                Environment.SetEnvironmentVariable("DREAM_WEATHER", null);
                }

                if (Want("plaza")) {
                // 3. the plaza, booted the way the phone boots it: walk with the stick, turn, walk, wave
                HubWorld.EditorDriven = true;
                host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
                var bridge = host.AddComponent<NativeSportsSession>();
                bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "smoke", action = "start", sport = "hub", touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF" }));
                for (int i = 0; i < 1200 && !bridge.Ready; i++) yield return null;
                var hub = HubWorld.Find();
                for (int k = 0; k < 90; k++) yield return null;
                yield return Film("plaza walk", 14f, t => {
                    if (!hub || !hub.Player) return;
                    if (t < 5) hub.Player.SetStick(0, 1, 1);
                    else if (t < 7) hub.Player.SetStick(.9f, .4f, 1);
                    else if (t < 11) hub.Player.SetStick(0, 1, .8f);
                    else hub.Player.SetStick(0, 0, 0);
                });
                bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "smoke", action = "hubEmote", mode = "wave", sport = "hub" }));
                yield return Film("plaza emote", 4f);
                }
            }
            finally
            {
                rec.Close();
                log.Add($"errors {errors}, exceptions {exceptions}");
                File.WriteAllLines(Path.Combine(Out, only == "" ? "smoke_log.txt" : $"smoke_{only}_log.txt"), log);
            }
            Assert.AreEqual(0, exceptions, "no exceptions in the playthrough: " + string.Join(" / ", log));
        }
    }
}
