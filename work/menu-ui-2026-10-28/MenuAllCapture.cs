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
    /// The TV menu's new screens, filmed with their HUD at 1920x1080 (work/menu-tv/setup): tennis modes with the live preview, the
    /// Exhibition setup (court strip, CPU opponent stepper, options, START), local golf's players screen and the golf setup. The phone's
    /// side is stood in for: its menuSetupState JSON (MenuSetup.swift's shape) is handed to MenuHud.SetSetup. MS_OUT = output folder.
    public class MenuAllCapture
    {
        static string Dir => Environment.GetEnvironmentVariable("MS_OUT");
        GameObject host;
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        const string Exhibition = "{\"mode\":\"bay-tennis-exhibition\",\"sport\":\"tennis\",\"title\":\"Exhibition\",\"line2\":\"Pick a court\",\"start\":\"START MATCH\",\"map\":\"skyscraper\"," +
            "\"maps\":[{\"id\":\"resort\",\"title\":\"Tropical Resort\",\"detail\":\"A bright tropical bay, lush gardens and stands full of fans.\",\"tag\":\"CLASSIC\",\"tagHex\":\"3FA9F5\"}," +
            "{\"id\":\"skyscraper\",\"title\":\"Sky Tower\",\"detail\":\"A rooftop above the clouds. Hit it wide and the ball falls forever.\",\"tag\":\"OPEN EDGE\",\"tagHex\":\"8A4FFF\"}," +
            "{\"id\":\"volcano\",\"title\":\"Magma Crater\",\"detail\":\"A court floating over a lava lake. Don't miss long.\",\"tag\":\"OVER LAVA\",\"tagHex\":\"FF6B4A\"}]," +
            "\"rows\":[{\"key\":\"opponent\",\"label\":\"CPU opponent\",\"choices\":[\"Milo Reyes · The Wildcard\",\"Tama Kealoha · The Moonballer\",\"Suki Tanaka · The Needle\",\"Dex Okafor · Big Serve\",\"Five\",\"Six\"],\"value\":2}," +
            "{\"key\":\"difficulty\",\"label\":\"Difficulty\",\"choices\":[\"Relaxed\",\"Standard\",\"Tough\"],\"value\":1}," +
            "{\"key\":\"length\",\"label\":\"Match length\",\"choices\":[\"3 games\",\"1 set\",\"Best of 3\"],\"value\":1}]}";
        const string Golf = "{\"mode\":\"bay-golf-pass\",\"sport\":\"golf\",\"title\":\"Local play · 3 players\",\"line2\":\"Pick a course\",\"start\":\"TEE OFF\",\"map\":\"cliffside\"," +
            "\"maps\":[{\"id\":\"cliffside\",\"title\":\"Cliffside\",\"detail\":\"Cliffs, sea stacks and island carries · 5 holes · par 19\",\"tag\":\"OCEAN CLIFFS\",\"tagHex\":\"3FA9F5\"}," +
            "{\"id\":\"wildisles\",\"title\":\"Wild Isles\",\"detail\":\"A world tour: pine, ice, mesa, jungle · 6 holes · par 25\",\"tag\":\"WILD ISLANDS\",\"tagHex\":\"3FA9F5\"}," +
            "{\"id\":\"magma\",\"title\":\"Magma Open\",\"detail\":\"Lava crater holes and volcanic greens · 5 holes · par 20\",\"tag\":\"LAVA CRATER\",\"tagHex\":\"3FA9F5\"}]," +
            "\"rows\":[{\"key\":\"holes\",\"label\":\"Holes\",\"choices\":[\"This course\",\"9 holes\",\"18 holes\"],\"value\":0},{\"key\":\"twists\",\"label\":\"Twists\",\"choices\":[\"Off\",\"On\"],\"value\":1}]}";

        static IEnumerator Shot(HubWorld hub, string name)
        {
            yield return new WaitForEndOfFrame();
            const int W = 1920, H = 1080;
            var cam = hub.Camera; var canvas = hub.Hud.Canvas;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex4 = new Texture2D(W, H, TextureFormat.RGBA32, false);
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            float aspect = cam.aspect; cam.aspect = (float)W / H; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = aspect;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(Dir, name + "_bg.jpg"), tex.EncodeToJPG(88));
            // the HUD drawn by a plain camera on top (MenuPointerTests.Shot)
            var ui = new GameObject("Proof UI camera").AddComponent<Camera>();
            ui.clearFlags = CameraClearFlags.SolidColor; ui.backgroundColor = new Color(0, 0, 0, 0); ui.cullingMask = 1 << 5; ui.orthographic = true; ui.targetTexture = rt; ui.aspect = (float)W / H;
            var mode = canvas.renderMode; int layer = canvas.gameObject.layer;
            SetLayer(canvas.transform, 5);
            canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = ui; canvas.planeDistance = 1;
            Canvas.ForceUpdateCanvases(); ui.Render();
            canvas.renderMode = mode; canvas.worldCamera = null; SetLayer(canvas.transform, layer);
            RenderTexture.active = rt; tex4.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex4.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(Dir, name + "_ui.png"), tex4.EncodeToPNG()); Object.DestroyImmediate(tex4);
            Object.DestroyImmediate(ui.gameObject); rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
            yield return null;
        }
        static void SetLayer(Transform t, int layer) { foreach (var c in t.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = layer; }
        int presses;
        IEnumerator Press(MenuHud hud, string id)
        {
            // invoke the item's own action (the pointer path needs the phone's press timing)
            var f = typeof(MenuHud).GetField("screenItems", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            var c = typeof(MenuHud).GetField("chromeItems", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            MenuItem hit = null;
            foreach (var list in ((System.Collections.Generic.Dictionary<string, System.Collections.Generic.List<MenuItem>>)f.GetValue(hud)).Values) foreach (var it in list) if (it.id == id && it.Visible) hit = it;
            if (hit == null) foreach (var it in (System.Collections.Generic.List<MenuItem>)c.GetValue(hud)) if (it.id == id && it.Visible) hit = it;
            Assert.IsNotNull(hit, "no item " + id + " on " + hud.Screen);
            if (hud.TryCentre(id, out var at)) for (int i = 0; i < 6; i++) { hud.PointAt(at, false, presses); yield return null; }
            hit.activate?.Invoke(); yield return null;
            Debug.Log($"[MenuAllCapture] pressed {id}: screen {hud.Screen}");
        }
        IEnumerator Hover(MenuHud hud, string id)
        {
            Assert.IsTrue(hud.TryCentre(id, out var at), "no item " + id + " on " + hud.Screen);
            // re-aim every frame: right after a Shot the canvas is back from its 1920x1080 proof camera and the first centre is stale
            for (int i = 0; i < 20; i++) { hud.TryCentre(id, out at); hud.PointAt(at, false, presses); yield return null; }
            Debug.Log($"[MenuAllCapture] hover {id} at {at} -> hovered '{hud.Hovered}' screen {UnityEngine.Screen.width}x{UnityEngine.Screen.height} canvas {((RectTransform)hud.Canvas.transform).rect.size}");
        }
        static IEnumerator Wait(float s) { for (float t = 0; t < s; t += Time.unscaledDeltaTime) yield return null; }

        [UnityTest, Timeout(600000)] public IEnumerator Capture()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("MS_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-setup", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Hud, "menu mode");
            var hud = hub.Hud; var sent = new System.Collections.Generic.List<string>();
            hud.Event += (t, m) => sent.Add(t + " " + m);
            hub.StartArrival(); yield return Wait(2.5f);
            yield return Shot(hub, "01_home");
            yield return Hover(hud, "play"); yield return Wait(.5f);
            yield return Shot(hub, "01b_home_hover_play");
            yield return Press(hud, "play"); yield return Wait(1f);
            yield return Shot(hub, "02_sport");
            yield return Hover(hud, "sport-golf"); yield return Wait(.7f);
            yield return Shot(hub, "02b_sport_hover_golf");
            yield return Press(hud, "sport-tennis"); yield return Wait(1.2f);
            yield return Hover(hud, "bay-tennis-exhibition"); yield return Wait(.8f);
            yield return Shot(hub, "03_tennis_modes_exhibition");
            yield return Hover(hud, "bay-tennis-training"); yield return Wait(.8f);
            yield return Shot(hub, "04_tennis_modes_training");
            yield return Press(hud, "bay-tennis-exhibition"); yield return Wait(.6f);
            hud.SetSetup(Exhibition); yield return Wait(1.2f);
            yield return Shot(hub, "05_exhibition_setup");
            yield return Press(hud, "map-resort"); yield return Press(hud, "opt-opponent-next"); yield return Press(hud, "opt-difficulty-2"); yield return Wait(1f);
            yield return Shot(hub, "06_exhibition_changed");
            yield return Press(hud, "setup-start"); yield return null;
            hud.Back(); yield return Wait(.6f); hud.Back(); yield return Wait(.6f);
            yield return Press(hud, "sport-golf"); yield return Wait(1.2f);
            yield return Shot(hub, "07_golf_modes");
            yield return Press(hud, "bay-golf-pass"); yield return Wait(1f);
            yield return Hover(hud, "players-3"); yield return Wait(.4f);
            yield return Shot(hub, "08_local_players");
            yield return Press(hud, "players-3"); yield return null;
            hud.SetSetup(Golf); yield return Wait(1.2f);
            yield return Shot(hub, "09_golf_setup");
            hud.Back(); yield return Wait(.6f); hud.Back(); yield return Wait(.6f); hud.Back(); yield return Wait(.6f);
            hud.Go(MenuHud.BowlingModes); yield return Wait(1.2f);
            yield return Shot(hub, "10_bowling_modes");
            hud.Go(MenuHud.Locker); yield return Wait(1.6f);
            yield return Hover(hud, "swatch-sky"); yield return Wait(.5f);
            yield return Shot(hub, "11_locker");
            hud.Go(MenuHud.Clubhouse); yield return Wait(1.4f);
            yield return Shot(hub, "12_clubhouse");
            hud.Go(MenuHud.Home); yield return Wait(1.2f);
            yield return Press(hud, "desk-settings"); yield return Wait(.8f);
            yield return Shot(hub, "13_phone_modal");
            hud.Back(); yield return Wait(.6f); hud.Go(MenuHud.Home); yield return Wait(1f);
            hud.BeginLoading("tennis", "bay-tennis-exhibition", true); hud.SetLoading(.45f); yield return Wait(1.2f);
            yield return Shot(hub, "14_loading");
            hud.MatchBuilt(); yield return Wait(.6f);
            yield return Hover(hud, "start"); yield return Wait(.4f);
            yield return Shot(hub, "15_loading_ready");
            File.WriteAllLines(Path.Combine(Dir, "events.txt"), sent);
        }
    }
}
