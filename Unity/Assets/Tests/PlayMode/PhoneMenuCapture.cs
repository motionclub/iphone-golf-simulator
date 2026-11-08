using System;
using System.Collections;
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
    /// The menu on a phone with no TV (HubWorld.PhoneOnly), filmed as the phone shows it: an iPhone 15 Pro screen (1179 x 2556) with the
    /// Dynamic Island drawn in, Unity's camera and menu HUD where HubWorld.PhoneMenuView puts them, and the app's own part of the screen
    /// left dark. PM_OUT = output folder (skipped without it).
    public class PhoneMenuCapture
    {
        static string Dir => Environment.GetEnvironmentVariable("PM_OUT");
        const int PW = 1179, PH = 2556;
        /// The phone's safe area in pixels (Unity's bottom-left origin): 59 pt under the top edge and 34 pt over the bottom at 3x.
        static readonly Rect Safe = new Rect(0, 34 * 3, PW, PH - (59 + 34) * 3);
        GameObject host;
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; HubWorld.MenuMode = false; HubWorld.PhoneOnly = false; HubWorld.PhoneScreenForTests = null; if (host) Object.DestroyImmediate(host); }

        static IEnumerator Shot(HubWorld hub, string name)
        {
            // (not WaitForEndOfFrame: batch mode has no Game view, so it never comes; the cameras are rendered by hand below)
            yield return null;
            var view = HubWorld.PhoneMenuView(new Vector2(PW, PH), Safe);
            var cam = hub.Camera; var canvas = hub.Hud.Canvas;
            // the app's part of the screen: the menu's navy
            var outPx = new Color32[PW * PH]; var bg = new Color32(16, 30, 74, 255); for (int i = 0; i < outPx.Length; i++) outPx[i] = bg;
            // the 3D at the size of Unity's part of the screen (a viewport rect inside a bigger target does not render in batch mode)
            var r = view.camera; int x0 = Mathf.RoundToInt(r.x * PW), y0 = Mathf.RoundToInt(r.y * PH), w = Mathf.RoundToInt(r.width * PW), h = Mathf.RoundToInt(r.height * PH);
            var keep = cam.rect; float aspect = cam.aspect;
            var rt3 = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.rect = new Rect(0, 0, 1, 1); cam.targetTexture = rt3; cam.aspect = (float)w / h; cam.Render(); cam.targetTexture = null; cam.rect = keep; cam.aspect = aspect;
            var world = Read(rt3, w, h).GetPixels32();
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) outPx[(y0 + y) * PW + x0 + x] = world[y * w + x];
            rt3.Release(); Object.DestroyImmediate(rt3);
            // the HUD over it, laid out for the phone (MenuHud.LayOutPhone), drawn by a plain camera into a phone-sized target
            var rt = new RenderTexture(PW, PH, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var ui = new GameObject("Proof UI camera").AddComponent<Camera>();
            ui.clearFlags = CameraClearFlags.SolidColor; ui.backgroundColor = new Color(0, 0, 0, 0); ui.cullingMask = 1 << 5; ui.orthographic = true; ui.targetTexture = rt;
            var mode = canvas.renderMode; int layer = canvas.gameObject.layer;
            SetLayer(canvas.transform, 5);
            canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = ui; canvas.planeDistance = 1;
            hub.Hud.LayOutPhone(new Vector2(PW, PH), Safe);
            Canvas.ForceUpdateCanvases(); ui.Render();
            canvas.renderMode = mode; canvas.worldCamera = null; SetLayer(canvas.transform, layer);
            var hud = Read(rt, PW, PH).GetPixels32();
            Object.DestroyImmediate(ui.gameObject); rt.Release(); Object.DestroyImmediate(rt);
            // the HUD was blended onto clear black: its colour is already weighted by its alpha
            for (int i = 0; i < outPx.Length; i++)
            {
                float a = hud[i].a / 255f; var b = outPx[i];
                outPx[i] = new Color32((byte)Mathf.Min(255, hud[i].r + b.r * (1 - a)), (byte)Mathf.Min(255, hud[i].g + b.g * (1 - a)), (byte)Mathf.Min(255, hud[i].b + b.b * (1 - a)), 255);
            }
            // the Dynamic Island and the status bar's clock, which the phone draws over everything
            Box(outPx, PW / 2 - 189, PH - 33 - 111, 378, 111, new Color32(0, 0, 0, 255));
            Box(outPx, 150, PH - 66 - 50, 150, 50, new Color32(255, 255, 255, 200));
            // the app's Back button in its footer (MenuTouchPad), where the phone draws it
            if (view.stacked) Box(outPx, PW / 2 - 150, (int)(view.hud.y - 30 * 3 - 132), 300, 132, new Color32(60, 90, 160, 255));
            var page = new Texture2D(PW, PH, TextureFormat.RGBA32, false); page.SetPixels32(outPx); page.Apply();
            File.WriteAllBytes(Path.Combine(Dir, name + ".jpg"), page.EncodeToJPG(88));
            Object.DestroyImmediate(page);
            yield return null;
        }
        static Texture2D Read(RenderTexture rt, int w, int h)
        {
            RenderTexture.active = rt; var t = new Texture2D(w, h, TextureFormat.RGBA32, false); t.ReadPixels(new Rect(0, 0, w, h), 0, 0); t.Apply(); RenderTexture.active = null;
            return t;
        }
        static void Box(Color32[] px, int x, int y, int w, int h, Color32 c)
        {
            for (int j = Mathf.Max(0, y); j < Mathf.Min(PH, y + h); j++) for (int i = Mathf.Max(0, x); i < Mathf.Min(PW, x + w); i++) px[j * PW + i] = c;
        }
        static void SetLayer(Transform t, int layer) { foreach (var c in t.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = layer; }
        static IEnumerator Wait(float s) { for (float t = 0; t < s; t += Time.unscaledDeltaTime) yield return null; }

        /// Handheld golf (no TV): the game's part of the upright phone (the top three quarters) at address, then with the aim pad
        /// pushed up (golfStick 0,1): the camera flies up the hole to show where the shot goes, as the TV's stick does.
        [UnityTest, Timeout(300000)] public IEnumerator HandheldGolfLooksUpTheHole()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("PM_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            yield return UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Golf");
            yield return null;
            var game = Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            host = new GameObject("NativeSportsSession");
            var bridge = host.AddComponent<NativeSportsSession>(); bridge.enabled = false;
            const string id = "handheld-look";
            var fields = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            typeof(NativeSportsSession).GetField("session", fields).SetValue(bridge, id);
            typeof(NativeSportsSession).GetField("golf", fields).SetValue(bridge, game);
            typeof(NativeSportsSession).GetProperty("Active").GetSetMethod(true).Invoke(null, new object[] { true });
            typeof(GolfGame).GetField("pendingNativeIntro", fields).SetValue(game, false);
            void Command(string action, float value = 0, float value2 = 0) => bridge.Receive(JsonUtility.ToJson(
                new NativeSportsSession.Message { version = 1, session = id, action = action, value = value, value2 = value2 }));
            int w = PW, h = Mathf.RoundToInt(PH * (1 - NativeSportsSession.HandheldDeck));
            var cam = game.GameplayCamera; cam.aspect = (float)w / h;   // the upright game view: FrameAddress picks its portrait framing
            try
            {
                Command("recalibrate"); Command("resume");
                for (int i = 0; i < 180 && game.Current != GolfGame.State.Aim; i++) yield return null;
                Command("golfStick", .3f, 0); yield return null; Command("golfStick", 0, 0);   // re-frame for the portrait lens
                yield return Wait(1.5f);
                Film(cam, w, h, "10_handheld_address");
                Command("golfStick", 0, 1); yield return Wait(1.6f);
                Film(cam, w, h, "11_handheld_looking_up");
                Command("golfStick", 0, 0); yield return Wait(1.6f);
                Film(cam, w, h, "12_handheld_let_go");
            }
            finally { Object.DestroyImmediate(host); Time.timeScale = 1; cam.ResetAspect(); }
        }
        static void Film(Camera cam, int w, int h, string name)
        {
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var keep = cam.rect; cam.rect = new Rect(0, 0, 1, 1); cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.rect = keep;
            var t = Read(rt, w, h); File.WriteAllBytes(Path.Combine(Dir, name + ".jpg"), t.EncodeToJPG(85));
            Object.DestroyImmediate(t); rt.Release(); Object.DestroyImmediate(rt);
        }

        [UnityTest, Timeout(600000)] public IEnumerator Capture()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("PM_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            // the phone's screen, not the editor's Game view, for the band and the HUD's layout
            HubWorld.PhoneScreenForTests = (new Vector2(PW, PH), Safe);
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "phone-menu", action = "start", sport = "hub", menu = true, leader = true, phoneOnly = true, playerName = "Adnan", female = false, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Hud, "menu mode");
            Assert.IsTrue(HubWorld.PhoneOnly, "phone only");
            var hud = hub.Hud;
            hub.StartArrival(); yield return Wait(2.5f);
            yield return Shot(hub, "01_home");
            hud.Go(MenuHud.Sport); yield return Wait(1.2f);
            yield return Shot(hub, "02_sport");
            hud.Go(MenuHud.GolfModes); yield return Wait(1.2f);
            yield return Shot(hub, "03_golf_modes");
            hud.Go(MenuHud.Locker); yield return Wait(1.6f);
            yield return Shot(hub, "04_locker");
            hud.Go(MenuHud.Clubhouse); yield return Wait(1.4f);
            yield return Shot(hub, "05_clubhouse");
            hud.Go(MenuHud.Home); yield return Wait(1.2f);
            yield return Shot(hub, "06_home_again");
        }
    }
}
