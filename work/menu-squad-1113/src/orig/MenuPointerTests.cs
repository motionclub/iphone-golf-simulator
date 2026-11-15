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
    /// The pointer menu (PLAN_PointerMenu.md): boots the plaza in menu mode through the same bridge message the phone sends, then
    /// drives the TV menu with the pointer (the HUD's PointAt hook = a pointer sample at that spot) and checks the screens, the
    /// line-up and the phone-bound events. With ML_OUT set, also films every screen at 1920×1080 with the HUD drawn (proof).
    public class MenuPointerTests
    {
        GameObject host; NativeSportsSession bridge; HubWorld hub; MenuHud hud;
        readonly List<string> events = new List<string>();
        int presses;

        [UnitySetUp] public IEnumerator Boot()
        {
            AudioListener.volume = 0; LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-test", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1200 && !bridge.Ready; i++) yield return null;
            hub = HubWorld.Find(); hud = hub ? hub.Hud : null;
            Assert.IsNotNull(hud, "menu mode builds the HUD");
            hud.Event += (t, m) => events.Add(t + " " + m);
            hub.StartArrival();
            for (float t = 0; t < 1.8f; t += Time.unscaledDeltaTime) yield return null;
        }
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        IEnumerator Click(string id)
        {
            Assert.IsTrue(hud.TryCentre(id, out var at), "visible: " + id + " on " + hud.Screen);
            hud.PointAt(at, false, presses); yield return null;
            hud.PointAt(at, true, ++presses); yield return null;
            hud.PointAt(at, false, presses); yield return null;
        }
        IEnumerator Settle(float s = .9f) { for (float t = 0; t < s; t += Time.unscaledDeltaTime) yield return null; }

        [UnityTest, Timeout(300000)] public IEnumerator MenuModeBuildsOnlyThePlazaAndStandsTheHeroOnTheLineUp()
        {
            Assert.IsNotNull(hub.Menu); Assert.AreEqual(MenuHud.Home, hud.Screen);
            Assert.IsTrue(hub.Player.locked, "nobody walks in the menu");
            Assert.Less(Vector3.Distance(hub.Player.transform.position, MenuShots.Slots[0]), .05f);
            Assert.Less(Mathf.Abs(Mathf.DeltaAngle(hub.Player.Yaw, MenuShots.FacingYaw(MenuShots.Slots[0]))), 5f, "faces the camera");
            Assert.Less(Vector3.Distance(hub.Camera.transform.position, MenuShots.For(MenuShots.Low).position), .1f, "home: the low shot (the centred one with a backdrop)");
            Assert.IsNull(GameObject.Find("Locker Room"), "no rooms in menu mode");
            yield break;
        }

        [UnityTest, Timeout(300000)] public IEnumerator PlayNowThenTennisThenExhibitionSetsUpOnTheTv()
        {
            yield return Click("play"); yield return Settle();
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
            yield return Click("sport-tennis"); yield return Settle();
            Assert.AreEqual(MenuHud.TennisModes, hud.Screen);
            Assert.Less(Vector3.Distance(hub.Camera.transform.position, MenuShots.For(MenuShots.Close).position), .1f, "modes: the close shot (the centred one with a backdrop)");
            // since 10-26 Exhibition sets up on the TV (court strip, options, START) and asks the phone for its options
            yield return Click("bay-tennis-exhibition"); yield return null;
            Assert.Contains("menuSetup bay-tennis-exhibition", events);
            Assert.AreEqual(MenuHud.Setup, hud.Screen);
            yield return Click("back"); yield return Settle();
            Assert.AreEqual(MenuHud.TennisModes, hud.Screen);
            yield return Click("back"); yield return Settle();
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
            yield return Click("back"); yield return Settle();
            Assert.AreEqual(MenuHud.Home, hud.Screen);
        }

        [UnityTest, Timeout(300000)] public IEnumerator HoverHasHysteresisAndADroppedReleaseStillClicksOnce()
        {
            Assert.IsTrue(hud.TryCentre("play", out var at));
            hud.PointAt(at, false, presses); yield return null;
            Assert.AreEqual("play", hud.Hovered);
            hud.PointAt(at + new Vector2(260, 0), false, presses); yield return null;   // 30 px past the right edge: still lit
            Assert.AreEqual("play", hud.Hovered, "kept within 40 px");
            hud.PointAt(at + new Vector2(400, 0), false, presses); yield return null;
            Assert.AreNotEqual("play", hud.Hovered);
            // press and release inside one sample (the release sample was dropped): one click
            hud.PointAt(at, false, presses); yield return null;
            int before = hud.Activated.Count;
            hud.PointAt(at, false, ++presses); yield return null;
            Assert.AreEqual(before + 1, hud.Activated.Count);
            yield return Settle(.3f);
            Assert.AreEqual(MenuHud.Sport, hud.Screen);
        }

        [UnityTest, Timeout(300000)] public IEnumerator LockerSwatchColoursTheHeroAndTellsThePhone()
        {
            yield return Click("tab-" + MenuHud.Locker); yield return Settle();
            Assert.AreEqual(MenuHud.Locker, hud.Screen);
            Assert.Less(Vector3.Distance(hub.Camera.transform.position, MenuShots.For(MenuShots.Solo).position), .1f, "locker: the solo shot (the centred one with a backdrop)");
            yield return Click("swatch-sky"); yield return null;
            Assert.Contains("menuLook shirt|3FA9F5", events);
            yield return Click("lk-shorts"); yield return Click("swatch-navy"); yield return null;
            Assert.Contains("menuLook shorts|1E2A6E", events);
            yield return Click("look-mirror"); yield return null;
            Assert.Contains("menuOpen look-mirror", events);
        }

        [UnityTest, Timeout(300000)] public IEnumerator FriendsFillTheLineUpAndAGuestCannotDrive()
        {
            Receive("hubRemote", remote: JsonUtility.ToJson(new RemoteState { id = "sam", name = "Sam", place = HubLayout.Plaza, female = true, shirt = "FF6B4A", shorts = "1E2A6E", colour = 1, x = 0, z = -7 }));
            yield return Settle(.5f);
            Assert.AreEqual(2, hub.Menu.Heroes);
            Assert.IsTrue(HubRemotes.For(hub).TryGetShown("sam", out var at));
            Assert.Less(Vector3.Distance(at, MenuShots.Slots[1]), .05f, "a friend stands on slot 1");
            Receive("menuParty", leader: false, soloLocked: true);
            yield return null;
            Assert.IsTrue(hud.TryCentre("play", out var play));
            int before = hud.Activated.Count;
            hud.PointAt(play, false, ++presses); yield return null;
            Assert.AreEqual(before, hud.Activated.Count, "a guest's pointer does nothing");
            Receive("menuMirror", mode: "sport||0.1|0.2|1"); yield return Settle(.5f);
            Assert.AreEqual(MenuHud.Sport, hud.Screen, "a guest's TV follows the leader");
            Receive("menuParty", leader: true, soloLocked: true); yield return null;
            hud.Go(MenuHud.TennisModes); yield return Settle();
            Assert.IsTrue(hud.TryCentre("bay-tennis-online", out _));
            Assert.IsTrue(hud.TryCentre("bay-tennis-exhibition", out var ex));
            hud.PointAt(ex, false, ++presses); yield return null;
            Assert.IsFalse(events.Contains("menuOpen bay-tennis-exhibition"), "solo modes lock while the party is here");
        }

        void Receive(string action, string mode = null, string remote = null, bool leader = true, bool soloLocked = false)
            => bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-test", action = action, mode = mode, remote = remote, leader = leader, soloLocked = soloLocked }));

        // ---------------------------------------------------------------- proof stills (ML_OUT)
        static string Out => Environment.GetEnvironmentVariable("ML_OUT");
        [UnityTest, Timeout(600000)] public IEnumerator FilmEveryScreen()
        {
            if (string.IsNullOrEmpty(Out)) { Assert.Ignore("ML_OUT not set"); yield break; }
            Directory.CreateDirectory(Out);
            Receive("hubRemote", remote: JsonUtility.ToJson(new RemoteState { id = "sam", name = "Sam", place = HubLayout.Plaza, female = true, shirt = "FF6B4A", shorts = "1E2A6E", colour = 1, x = 0, z = -7 }));
            yield return Settle(.6f);
            yield return Shot("01_home");
            Assert.IsTrue(hud.TryCentre("play", out var play)); hud.PointAt(play, false, presses); yield return Settle(.3f);
            yield return Shot("02_home_hover_play");
            foreach (var (screen, name) in new[] { (MenuHud.Sport, "03_sport"), (MenuHud.TennisModes, "04_tennis_modes"), (MenuHud.GolfModes, "05_golf_modes"), (MenuHud.Locker, "06_locker"), (MenuHud.Clubhouse, "07_clubhouse") })
            {
                hud.Go(screen); hud.Pointer(-1, -1, false, false, presses); yield return Settle(1.0f);
                yield return Shot(name);
            }
            hud.Go(MenuHud.Locker); yield return Settle(.8f);
            Assert.IsTrue(hud.TryCentre("swatch-sky", out var sky)); yield return Click("swatch-sky"); yield return Settle(.5f);
            yield return Shot("08_locker_sky");
            hud.Go(MenuHud.TennisModes); yield return Settle(.8f);
            hud.BeginLoading("tennis", "Exhibition", true); hud.SetRows("Adnan|READY;Sam|CHOOSING…"); hud.SetLoading(.55f); yield return Settle(1.0f);
            yield return Shot("09_loading");
            hud.SetRows("Adnan|READY;Sam|READY"); hud.MatchBuilt(); yield return Settle(.4f);
            Assert.IsTrue(hud.TryCentre("start", out var start)); hud.PointAt(start, false, presses); yield return Settle(.3f);
            yield return Shot("10_loading_start");
            hud.ShowReady(); yield return Settle(.6f);
            yield return Shot("11_ready");
            hud.SetLoading(-1); hud.Go(MenuHud.Home); yield return Settle(.8f);
            hud.SetPhonePanel(true, "Exhibition"); yield return Settle(.3f);
            yield return Shot("12_finish_on_phone");
            hud.SetPhonePanel(false);
        }

        IEnumerator Shot(string name)
        {
            yield return new WaitForEndOfFrame();
            const int W = 1920, H = 1080;
            var cam = hub.Camera; var canvas = hud.Canvas;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            float aspect = cam.aspect; cam.aspect = (float)W / H; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = aspect;
            // the HUD: its canvas drawn by a plain camera (no post) on top
            var ui = new GameObject("Proof UI camera").AddComponent<Camera>();
            ui.clearFlags = CameraClearFlags.Nothing; ui.cullingMask = 1 << 5; ui.orthographic = true; ui.targetTexture = rt; ui.aspect = (float)W / H;
            var mode = canvas.renderMode; int layer = canvas.gameObject.layer;
            SetLayer(canvas.transform, 5);
            canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = ui; canvas.planeDistance = 1;
            Canvas.ForceUpdateCanvases();
            ui.Render();
            canvas.renderMode = mode; canvas.worldCamera = null; SetLayer(canvas.transform, layer);
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(Out, name + ".png"), tex.EncodeToPNG());
            Object.DestroyImmediate(ui.gameObject); rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
        }
        static void SetLayer(Transform t, int layer) { foreach (var c in t.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = layer; }
    }
}
