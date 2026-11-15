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
    /// MENU SQUAD 11-13 (work/menu-squad-1113, clone only): films the TV menu at 1920x1080 (plate pinned with MENU_BACKDROP) solo and with a
    /// party of four, driven the way the phone drives it (arrow steps + Select), and counts the presses from Home to a started match.
    /// MSQ_OUT = output folder: <name>_bg.jpg (3D), <name>_ui.png (HUD with alpha), presses.json.
    public class MenuSquadCapture
    {
        static string Dir => Environment.GetEnvironmentVariable("MSQ_OUT");
        GameObject host; NativeSportsSession bridge;
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        const string Exhibition = "{\"mode\":\"bay-tennis-exhibition\",\"sport\":\"tennis\",\"title\":\"Exhibition\",\"line2\":\"Pick a court\",\"start\":\"START MATCH\",\"map\":\"resort\"," +
            "\"maps\":[{\"id\":\"resort\",\"title\":\"Tropical Resort\",\"detail\":\"A bright tropical bay, lush gardens and stands full of fans.\",\"tag\":\"CLASSIC\",\"tagHex\":\"3FA9F5\"}," +
            "{\"id\":\"skyscraper\",\"title\":\"Sky Tower\",\"detail\":\"A rooftop above the clouds.\",\"tag\":\"OPEN EDGE\",\"tagHex\":\"8A4FFF\"}," +
            "{\"id\":\"volcano\",\"title\":\"Magma Crater\",\"detail\":\"A court floating over a lava lake.\",\"tag\":\"OVER LAVA\",\"tagHex\":\"FF6B4A\"}]," +
            "\"rows\":[{\"key\":\"opponent\",\"label\":\"CPU opponent\",\"choices\":[\"Milo Reyes · The Wildcard\",\"Tama Kealoha · The Moonballer\",\"Suki Tanaka · The Needle\",\"Dex Okafor · Big Serve\",\"Five\",\"Six\"],\"value\":2}," +
            "{\"key\":\"difficulty\",\"label\":\"Difficulty\",\"choices\":[\"Relaxed\",\"Standard\",\"Tough\"],\"value\":1}," +
            "{\"key\":\"length\",\"label\":\"Match length\",\"choices\":[\"3 games\",\"1 set\",\"Best of 3\"],\"value\":1}]}";

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
            File.WriteAllBytes(Path.Combine(Dir, name + "_bg.jpg"), tex.EncodeToJPG(90));
            var ui = new GameObject("Proof UI camera").AddComponent<Camera>();
            ui.clearFlags = CameraClearFlags.SolidColor; ui.backgroundColor = new Color(0, 0, 0, 0); ui.cullingMask = 1 << 5; ui.orthographic = true; ui.targetTexture = rt; ui.aspect = (float)W / H;
            var mode = canvas.renderMode; int layer = canvas.gameObject.layer;
            SetLayer(canvas.transform, 5);
            canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = ui; canvas.planeDistance = 1;
            // name plates placed for this 16:9 frame (the editor window has its own aspect)
            Canvas.ForceUpdateCanvases(); cam.aspect = (float)W / H;
            typeof(MenuHud).GetMethod("UpdatePlates", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)?.Invoke(hub.Hud, null);
            typeof(MenuHud).GetMethod("PlaceFocus", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)?.Invoke(hub.Hud, new object[] { Time.unscaledTime });
            Canvas.ForceUpdateCanvases(); ui.Render(); cam.ResetAspect();
            canvas.renderMode = mode; canvas.worldCamera = null; SetLayer(canvas.transform, layer);
            RenderTexture.active = rt; tex4.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex4.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(Dir, name + "_ui.png"), tex4.EncodeToPNG()); Object.DestroyImmediate(tex4);
            Object.DestroyImmediate(ui.gameObject); rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
            // where each hero's body is on screen (for the "UI never covers a hero" check): renderer bounds -> screen rects
            var rects = new List<string>(); cam.aspect = (float)W / H;
            foreach (var look in Object.FindObjectsByType<GolfArcade.Tennis.MatchHeroLook>(FindObjectsSortMode.None))
            {
                if (!look.gameObject.activeInHierarchy) continue;
                Bounds b = default; bool any = false;
                foreach (var r in look.GetComponentsInChildren<SkinnedMeshRenderer>()) { if (!r.enabled || r.forceRenderingOff) continue; if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
                if (!any || b.center.y < -10) continue;
                float x0 = 1, y0 = 1, x1 = 0, y1 = 0; bool front = true;
                for (int i = 0; i < 8; i++)
                {
                    var c = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                    var vp = cam.WorldToViewportPoint(c); if (vp.z <= 0) front = false;
                    x0 = Mathf.Min(x0, vp.x); x1 = Mathf.Max(x1, vp.x); y0 = Mathf.Min(y0, vp.y); y1 = Mathf.Max(y1, vp.y);
                }
                if (front) rects.Add(string.Format(System.Globalization.CultureInfo.InvariantCulture, "[{0:0.0000},{1:0.0000},{2:0.0000},{3:0.0000}]", x0, 1 - y1, x1, 1 - y0));
            }
            cam.ResetAspect();
            File.WriteAllText(Path.Combine(Dir, name + "_heroes.json"), "[" + string.Join(",", rects) + "]");
            yield return null;
        }
        static void SetLayer(Transform t, int layer) { foreach (var c in t.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = layer; }
        static IEnumerator Wait(float s) { for (float t = 0; t < s; t += Time.unscaledDeltaTime) yield return null; }

        /// Arrow steps (down, then right, then up, left) until `id` is lit; returns the steps taken (or -1).
        static IEnumerator StepTo(MenuHud hud, string id, int[] steps)
        {
            steps[0] = -1;
            var dirs = new[] { (0, -1), (1, 0), (0, 1), (-1, 0) };
            int n = 0;
            if (hud.Hovered == id) { steps[0] = 0; yield break; }
            foreach (var (dx, dy) in dirs)
            {
                for (int i = 0; i < 12; i++)
                {
                    var was = hud.Hovered;
                    hud.Move(dx, dy); n++; yield return null; yield return null;
                    if (hud.Hovered == id) { steps[0] = n; yield break; }
                    if (hud.Hovered == was) { n--; break; }   // nothing that way
                }
            }
        }

        void Friend(string id, string name, bool female, string shirt, string shorts, int colour)
            => bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-squad", action = "hubRemote",
                remote = JsonUtility.ToJson(new RemoteState { id = id, name = name, place = HubLayout.Plaza, female = female, shirt = shirt, shorts = shorts, colour = colour, x = 0, z = -7 }) }));

        [UnityTest, Timeout(900000)] public IEnumerator Capture()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("MSQ_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-squad", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = false, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Hud, "menu mode");
            var hud = hub.Hud; var sent = new List<string>();
            hud.Event += (t, m) => sent.Add(t + " " + m);
            hub.StartArrival(); yield return Wait(2.5f);
            hud.Move(0, -1); yield return null; hud.Move(0, 1); yield return Wait(.6f);   // arrows on (the phone's first step)

            var steps = new int[1];
            // ---- solo
            yield return Shot(hub, "01_home_solo");
            yield return StepTo(hud, "board-invite", steps); yield return Wait(.4f);
            yield return Shot(hub, "01b_home_solo_invite_lit");
            yield return StepTo(hud, "play", steps); yield return Wait(.4f);
            yield return Shot(hub, "01c_home_solo_play_lit");
            // ---- the party of four
            Friend("maya", "Maya", true, "2F6FD6", "F4F0E6", 1);
            yield return Wait(2.5f); yield return StepTo(hud, "play", steps); yield return Wait(.4f);
            yield return Shot(hub, "01d_home_two");
            Friend("theo", "Theo", false, "7BC043", "23344D", 2); Friend("rio", "Rio", true, "F5C542", "FFFFFF", 3);
            yield return Wait(2.5f);
            Debug.Log("[MenuSquad] heroes " + hub.Menu.Heroes);
            yield return Shot(hub, "02_home_party");
            // lighting variants (MSQ_LIGHT=1): the backdrop reads its MENU_MIDDAY_* / HERO_LOOK_* numbers every frame
            if (Environment.GetEnvironmentVariable("MSQ_LIGHT") == "1")
            {
                var looks = new (string name, string sun, string fill, string temp, string sat, string con, string hero, string skin)[]
                    { ("A", "2.0", ".62", "3", "8", "8", ".5", "1.0"), ("B", "2.0", ".62", "2", "8", "6", ".85", "1.1"), ("C", "2.2", ".70", "1", "8", "4", "1.1", "1.15"), ("D", "2.2", ".70", "1", "6", "2", "1.4", "1.2") };
                foreach (var l in looks)
                {
                    Environment.SetEnvironmentVariable("MENU_MIDDAY_SUN", l.sun); Environment.SetEnvironmentVariable("MENU_MIDDAY_FILL", l.fill);
                    Environment.SetEnvironmentVariable("HERO_LOOK_TEMP", l.temp); Environment.SetEnvironmentVariable("HERO_LOOK_SAT", l.sat); Environment.SetEnvironmentVariable("HERO_LOOK_CONTRAST", l.con);
                    Environment.SetEnvironmentVariable("MENU_HERO_FILL", l.hero); Environment.SetEnvironmentVariable("MENU_HERO_SKIN", l.skin);
                    yield return Wait(1.0f);
                    yield return Shot(hub, "L" + l.name + "_party");
                }
                yield break;
            }

            // ---- presses from Home to a started exhibition, the phone's way (arrows + Select)
            int presses = 0; var log = new List<string>();
            void Note(string what) { log.Add("\"" + what + " @" + hud.Screen + " lit=" + hud.Hovered + "\""); }
            // to the PLAY item
            yield return StepTo(hud, "play", steps); presses += Mathf.Max(0, steps[0]); Note("to play: " + steps[0]);
            hud.SelectFocused(); presses++; yield return Wait(1.2f); Note("select");
            yield return Shot(hub, "03_sport");
            yield return StepTo(hud, "sport-tennis", steps); presses += Mathf.Max(0, steps[0]); Note("to tennis: " + steps[0]);
            hud.SelectFocused(); presses++; yield return Wait(1.2f); Note("select");
            yield return Shot(hub, "04_tennis_modes");
            yield return StepTo(hud, "bay-tennis-exhibition", steps); presses += Mathf.Max(0, steps[0]); Note("to exhibition: " + steps[0]);
            hud.SelectFocused(); presses++; yield return Wait(.6f); Note("select");
            hud.SetSetup(Exhibition); yield return Wait(1.4f);
            yield return Shot(hub, "05_setup_open");
            yield return StepTo(hud, "setup-start", steps); presses += Mathf.Max(0, steps[0]); Note("to start: " + steps[0]);
            yield return Wait(.5f);
            yield return Shot(hub, "06_setup_start_lit");
            hud.SelectFocused(); presses++; yield return null; Note("select");
            bool setupStarted = sent.Exists(s => s.StartsWith("menuSetupStart"));
            hud.BeginLoading("tennis", "bay-tennis-exhibition", true); hud.SetRows("Adnan|READY"); hud.SetLoading(.5f); yield return Wait(1.2f);
            yield return Shot(hub, "07_loading");
            hud.MatchBuilt(); yield return Wait(.6f);
            yield return StepTo(hud, "start", steps); presses += Mathf.Max(0, steps[0]); Note("to match start: " + steps[0]);
            yield return Shot(hub, "08_loading_start_lit");
            hud.SelectFocused(); presses++; yield return null; Note("select");
            bool matchStarted = sent.Exists(s => s.StartsWith("menuStart"));
            File.WriteAllText(Path.Combine(Dir, "presses.json"), "{\"presses\":" + presses + ",\"setupStarted\":" + (setupStarted ? "true" : "false") + ",\"matchStarted\":" + (matchStarted ? "true" : "false") + ",\"log\":[" + string.Join(",", log) + "]}");
            hud.SetLoading(-1); hud.ResetStart();

            // ---- the other screens
            hud.Go(MenuHud.Home); yield return Wait(1.2f);
            yield return Shot(hub, "09_home_party_play_lit");
            hud.Go(MenuHud.Locker); yield return Wait(1.6f);
            yield return Shot(hub, "10_locker");
            hud.Go(MenuHud.Clubhouse); yield return Wait(1.4f);
            yield return Shot(hub, "11_clubhouse");
            hud.Go(MenuHud.Home); yield return Wait(1.0f);
            yield return StepTo(hud, "tab-" + MenuHud.Locker, steps); yield return Wait(.4f);
            yield return Shot(hub, "12_home_tab_lit");
            Debug.Log("[MenuSquad] done: " + string.Join(" | ", sent));
        }
    }
}
