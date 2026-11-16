using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// The first-launch onboarding with a TV, filmed on the real menu (PLAN_Onboarding_v3): the phone's walkthrough
    /// (OnboardingSnapshotTests.testOnboardingWalkthrough writes OF_SCRIPT: each moment's tip, Tutorial lock and what the player does) is
    /// replayed here, the TV filmed at 10 fps into OF_OUT/tv, and the golf lesson's first step played on the Practice Tee in the middle.
    /// OF_OUT/frames.txt maps every frame to its moment (and, in the lesson, which HUD layer goes over it). work/onboarding-v3/film.sh
    /// joins the TV, the phone and the HUD into one video. Run windowed (WaitForEndOfFrame hangs in batchmode), muted.
    public class OnboardingFilm
    {
        [Serializable] public sealed class Entry { public string screen, coach, tutorial, act, phone, caption; public float hold; }
        [Serializable] sealed class Script { public Entry[] entries; }

        static string Out => Environment.GetEnvironmentVariable("OF_OUT");
        static string ScriptPath => Environment.GetEnvironmentVariable("OF_SCRIPT");
        /// "tv" (1920x1080, the TV with the phone as remote) or "phone" (1080x1920, 9:16: no TV, the menu on the phone itself).
        static bool Phone => Environment.GetEnvironmentVariable("OF_FORMAT") == "phone";
        static int W => Phone ? 1080 : 1920;
        static int H => Phone ? 1920 : 1080;
        const float Fps = 10;
        GameObject host; GolfGame golf;
        readonly List<string> frames = new List<string>();
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; if (host) Object.DestroyImmediate(host); if (golf) Object.DestroyImmediate(golf.gameObject); NativeSportsSession.LessonReport = null; }

        IEnumerator Shot(Camera cam, Canvas canvas, string tag)
        {
            yield return new WaitForEndOfFrame();
            if (canvas)
            {
                // the menu: the play view exactly as drawn (OnboardingFilm sets it to W x H), its overlay canvas and all
                var screen = ScreenCapture.CaptureScreenshotAsTexture();
                if (frames.Count == 0) Debug.Log($"[OnboardingFilm] play view {screen.width}x{screen.height}, want {W}x{H}");
                File.WriteAllBytes(Path.Combine(Out, "tv", $"f{frames.Count:00000}.jpg"), screen.EncodeToJPG(86));
                frames.Add(tag); Object.Destroy(screen);
                yield break;
            }
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            float aspect = cam.aspect; cam.aspect = (float)W / H; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = aspect;
            if (canvas)
            {
                var ui = new GameObject("Film UI camera").AddComponent<Camera>();
                ui.clearFlags = CameraClearFlags.Nothing; ui.cullingMask = 1 << 5; ui.orthographic = true; ui.targetTexture = rt; ui.aspect = (float)W / H;
                var mode = canvas.renderMode; int layer = canvas.gameObject.layer;
                SetLayer(canvas.transform, 5);
                canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = ui; canvas.planeDistance = 1;
                Canvas.ForceUpdateCanvases(); ui.Render();
                canvas.renderMode = mode; canvas.worldCamera = null; SetLayer(canvas.transform, layer);
                Object.DestroyImmediate(ui.gameObject);
            }
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
            var bytes = tex.EncodeToJPG(86);
            if (Black(tex))
            {
                if (frames.Count % 50 == 0) Debug.Log($"[OnboardingFilm] black frame {frames.Count}: cam {cam.name} enabled {cam.enabled} display {cam.targetDisplay} target {(cam.targetTexture ? cam.targetTexture.name : "-")} canvas {(canvas ? canvas.renderMode.ToString() : "-")}");
                // the Game view as drawn (the editor runs windowed): what the player would see
                var screen = ScreenCapture.CaptureScreenshotAsTexture();
                if (screen && !Black(screen)) bytes = screen.EncodeToJPG(86);
                if (screen) Object.Destroy(screen);
            }
            File.WriteAllBytes(Path.Combine(Out, "tv", $"f{frames.Count:00000}.jpg"), bytes);
            frames.Add(tag);
            rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
        }
        static bool Black(Texture2D t)
        {
            for (int i = 1; i < 8; i++) { var c = t.GetPixel(t.width * i / 8, t.height * i / 8); if (c.r + c.g + c.b > .02f) return false; }
            return true;
        }
        static void SetLayer(Transform t, int layer) { foreach (var c in t.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = layer; }

        /// `seconds` of film at 10 fps (each frame waits for its slot in real time, so the menu's own motion plays at its speed).
        IEnumerator Record(float seconds, Func<(Camera, Canvas)> view, string tag)
        {
            int n = Mathf.Max(1, Mathf.RoundToInt(seconds * Fps));
            float next = Time.realtimeSinceStartup;
            for (int i = 0; i < n; i++)
            {
                while (Time.realtimeSinceStartup < next) yield return null;
                next += 1 / Fps;
                var (cam, canvas) = view();
                if (cam) yield return Shot(cam, canvas, tag);
            }
        }

        IEnumerator BootMenu()
        {
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "onboarding-film", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = true, phoneOnly = Phone, shirt = "1F5BD8", shorts = "18245A", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Hud, "menu mode");
        }
        static (Camera, Canvas) Menu() { var h = HubWorld.Find(); return h && h.Hud ? (h.Camera, h.Hud.Canvas) : (null, null); }

        [UnityTest, Timeout(900000)] public IEnumerator Film()
        {
            if (string.IsNullOrEmpty(Out) || string.IsNullOrEmpty(ScriptPath)) { Assert.Ignore("OF_OUT / OF_SCRIPT not set"); yield break; }
            Directory.CreateDirectory(Path.Combine(Out, "tv")); AudioListener.volume = 0;
#if UNITY_EDITOR
            // the play view at the film's size (a TV's 1920x1080, or a 9:16 phone): the menu lays itself out for exactly that screen
            UnityEditor.PlayModeWindow.SetCustomRenderingResolution((uint)W, (uint)H, "OnboardingFilm " + W + "x" + H);
            for (int i = 0; i < 10; i++) yield return null;
#endif
            LogAssert.ignoreFailingMessages = true;
            var script = JsonUtility.FromJson<Script>("{\"entries\":" + File.ReadAllText(ScriptPath) + "}");
            Assert.IsNotNull(script?.entries); Assert.Greater(script.entries.Length, 5);
            yield return BootMenu();
            var hud = HubWorld.Find().Hud; var sent = new List<string>();
            hud.Event += (t, m) => { if (t != "menuState") sent.Add(t + " " + m); };
            HubWorld.Find().StartArrival(); yield return new WaitForSecondsRealtime(2.5f);

            for (int i = 0; i < script.entries.Length; i++)
            {
                var e = script.entries[i]; string tag = i.ToString();
                if (e.act == "lesson") { yield return Lesson(i); hud = HubWorld.Find().Hud; continue; }
                if (!string.IsNullOrEmpty(e.screen) && hud.Screen != e.screen) { hud.Go(e.screen); yield return Record(.8f, Menu, tag); }
                hud.SetTutorial(e.tutorial); hud.SetCoach(e.coach);
                if (e.act == "safe") hud.SetPhonePanel(true, "Golf lesson");
                if (e.act == "locker")
                {
                    // pick a colour on the TV's Locker, then BACK to the Plaza
                    yield return Record(1.6f, Menu, tag); hud.Move(1, 0);
                    yield return Record(.8f, Menu, tag); hud.SelectFocused();
                    yield return Record(Mathf.Max(.5f, e.hold - 2.4f), Menu, tag); hud.Back();
                }
                else
                {
                    yield return Record(e.hold, Menu, tag);
                    if (e.act == "select") hud.SelectFocused();
                    if (e.act == "safe") hud.SetPhonePanel(false);
                }
                yield return Record(.9f, Menu, tag);
            }
            File.WriteAllLines(Path.Combine(Out, "frames.txt"), frames);
            File.WriteAllLines(Path.Combine(Out, "events.txt"), sent);
            // the tips the player pressed reached the phone, in order
            Assert.IsTrue(sent.Contains("menuCoach welcome"), string.Join(", ", sent));
            Assert.IsTrue(sent.Contains("menuOpen bay-tutorial-golf"), "the golf lesson's card opens on the phone");
        }

        /// The golf lesson's first step on the Practice Tee: its how-it-works card (Swift's HUD, composited later), then one swing.
        IEnumerator Lesson(int entry)
        {
            if (host) Object.DestroyImmediate(host);
            var world = HubWorld.Find(); if (world) Object.DestroyImmediate(world.gameObject);
            yield return null;
            var reports = new List<string>();
            NativeSportsSession.LessonReport = json => reports.Add(json);
            golf = new GameObject("Golf lesson (film)").AddComponent<GolfGame>();
            yield return null;
            golf.PrepareNativeAddress("lesson");
            yield return null;
            var lesson = golf.gameObject.AddComponent<GolfLesson>();
            lesson.Begin(golf, 0);
            float deadline = Time.realtimeSinceStartup + 30;
            while (Time.realtimeSinceStartup < deadline && !(reports.Exists(r => r.Contains("\"kind\":\"station\"")) && golf.Current == GolfGame.State.Aim)) yield return null;
            Func<(Camera, Canvas)> view = () => (golf ? golf.GameplayCamera : null, null);
            yield return Record(4.5f, view, entry + ":explain");
            golf.StrikeToward(golf.CurrentHole.Pin);
            yield return Record(7f, view, entry + ":ask");
            File.WriteAllLines(Path.Combine(Out, "lesson-reports.txt"), reports);
            NativeSportsSession.LessonReport = null;
            Object.DestroyImmediate(golf.gameObject); golf = null;
            yield return null;
            yield return BootMenu();
            HubWorld.Find().StartArrival(); yield return new WaitForSecondsRealtime(2f);
        }
    }
}
