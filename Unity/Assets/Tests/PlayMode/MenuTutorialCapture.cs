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
    /// PLAY → TUTORIAL (PLAN_Onboarding_v3_IntroTutorial.md) on the TV menu at 1920x1080: the sports list locked to TUTORIAL, the
    /// Tutorial screen at each stage (golf next; golf done, tennis next; all done), a locked sport refusing a press, and a lesson
    /// row asking the phone for its how-to-play card. The phone's menuTutorialState JSON is stood in for. MT_OUT = output folder.
    public class MenuTutorialCapture
    {
        static string Dir => Environment.GetEnvironmentVariable("MT_OUT");
        GameObject host;
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; if (host) Object.DestroyImmediate(host); }

        static IEnumerator Shot(HubWorld hub, string name)
        {
            yield return new WaitForEndOfFrame();
            const int W = 1920, H = 1080;
            var cam = hub.Camera; var canvas = hub.Hud.Canvas;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            float aspect = cam.aspect; cam.aspect = (float)W / H; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = aspect;
            // the HUD drawn by a plain camera on top (MenuPointerTests.Shot)
            var ui = new GameObject("Proof UI camera").AddComponent<Camera>();
            ui.clearFlags = CameraClearFlags.Nothing; ui.cullingMask = 1 << 5; ui.orthographic = true; ui.targetTexture = rt; ui.aspect = (float)W / H;
            var mode = canvas.renderMode; int layer = canvas.gameObject.layer;
            SetLayer(canvas.transform, 5);
            canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = ui; canvas.planeDistance = 1;
            Canvas.ForceUpdateCanvases(); ui.Render();
            canvas.renderMode = mode; canvas.worldCamera = null; SetLayer(canvas.transform, layer);
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(Dir, name + ".jpg"), tex.EncodeToJPG(88));
            Object.DestroyImmediate(ui.gameObject); rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
            yield return null;
        }
        static void SetLayer(Transform t, int layer) { foreach (var c in t.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = layer; }
        int presses;
        IEnumerator Press(MenuHud hud, string id)
        {
            Assert.IsTrue(hud.TryCentre(id, out var at), "no item " + id + " on " + hud.Screen);
            hud.PointAt(at, false, presses); yield return null;
            presses++; hud.PointAt(at, true, presses); yield return null;
            hud.PointAt(at, false, presses); yield return null;
            Debug.Log($"[MenuTutorialCapture] pressed {id}: screen {hud.Screen}, last activated {(hud.Activated.Count > 0 ? hud.Activated[hud.Activated.Count - 1] : "-")}");
        }
        IEnumerator Hover(MenuHud hud, string id)
        {
            Assert.IsTrue(hud.TryCentre(id, out var at), "no item " + id + " on " + hud.Screen);
            for (int i = 0; i < 20; i++) { hud.PointAt(at, false, presses); yield return null; }
        }
        static IEnumerator Wait(float s) { for (float t = 0; t < s; t += Time.unscaledDeltaTime) yield return null; }

        [UnityTest, Timeout(600000)] public IEnumerator Capture()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("MT_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-tutorial", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = true, shirt = "1F5BD8", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Hud, "menu mode");
            var hud = hub.Hud; var sent = new System.Collections.Generic.List<string>();
            hud.Event += (t, m) => sent.Add(t + " " + m);
            // the phone's lock arrives over the bridge as on a device
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-tutorial", action = "menuTutorialState", mode = "{\"locked\":true,\"next\":\"golf\",\"done\":[],\"deferred\":[]}" }));
            hub.StartArrival(); yield return Wait(2.5f);
            Assert.AreEqual("play", hud.Hovered); hud.SelectFocused(); yield return Wait(1.2f);
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
            Assert.AreEqual("sport-tutorial", hud.Hovered, "locked: TUTORIAL is lit first");
            yield return Shot(hub, "01_play_locked");
            foreach (var id in new[] { "sport-tennis", "sport-golf", "sport-bowling", "sport-daily" }) Assert.IsFalse(hud.IsEnabled(id), id + " is locked");
            hud.SelectFocused(); yield return Wait(1.2f);   // the phone's Select on the lit TUTORIAL
            Assert.AreEqual(MenuHud.Tutorial, hud.Screen);
            yield return Shot(hub, "02_tutorial_golf_next");
            Assert.IsFalse(hud.IsEnabled("bay-tutorial-tennis"), "tennis waits for golf"); Assert.IsTrue(hud.IsEnabled("bay-tutorial-golf"));
            Assert.AreEqual("bay-tutorial-golf", hud.Hovered, "the next lesson is lit");
            hud.SelectFocused(); yield return Wait(.8f);
            Assert.IsTrue(sent.Contains("menuOpen bay-tutorial-golf"), "the golf lesson's card opens on the phone: " + string.Join(", ", sent));
            yield return Shot(hub, "03_tutorial_finish_on_phone");
            hud.SetPhonePanel(false);
            hud.SetTutorial("{\"locked\":true,\"next\":\"tennis\",\"done\":[\"golf\"],\"deferred\":[]}"); yield return Wait(1f);
            yield return Shot(hub, "04_tutorial_tennis_next");
            Assert.IsTrue(hud.IsEnabled("bay-tutorial-tennis") && hud.IsEnabled("bay-tutorial-golf") && !hud.IsEnabled("bay-tutorial-bowling"), "golf replays, tennis is next, bowling waits");
            hud.SetTutorial("{\"locked\":false,\"next\":\"\",\"done\":[\"golf\",\"tennis\",\"bowling\"],\"deferred\":[]}"); yield return Wait(.6f);
            hud.Back(); yield return Wait(1.2f);
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
            foreach (var id in new[] { "sport-tennis", "sport-golf", "sport-bowling", "sport-daily" }) Assert.IsTrue(hud.IsEnabled(id), id + " is unlocked");
            yield return Shot(hub, "05_play_unlocked");
            for (int i = 0; i < 6 && hud.Hovered != "sport-golf"; i++) { hud.Move(0, -1); yield return null; }
            Assert.AreEqual("sport-golf", hud.Hovered, "the arrows reach an unlocked sport");
            hud.SelectFocused(); yield return Wait(.8f);
            Assert.AreEqual(MenuHud.GolfModes, hud.Screen, "unlocked: golf opens");
            File.WriteAllLines(Path.Combine(Dir, "events.txt"), sent);
        }
    }
}
