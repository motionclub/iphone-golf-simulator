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
        [TearDown] public void Clean()
        {
            HubWorld.EditorDriven = false; HubWorld.MenuMode = false; HubWorld.PhoneOnly = false; HubWorld.PhoneScreenForTests = null;
            if (host) Object.DestroyImmediate(host);
            var hub = HubWorld.Find(); if (hub) Object.DestroyImmediate(hub.gameObject);   // the next capture builds its own
        }

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
        /// Each hand in the hero's own space (x right, y up, z forward): the mapped bone names, the knuckles, the thumb, and which
        /// way the palm faces (the side of the hand away from the back of the fingers' curl).
        static void HandReport(HubHeroAnimator hero, string label)
        {
            var look = hero ? hero.GetComponentInChildren<GolfArcade.Tennis.MatchHeroLook>() ?? hero.GetComponentInParent<GolfArcade.Tennis.MatchHeroLook>() : null;
            if (!look) { Debug.Log($"[HandDiag] {label}: no MatchHeroLook"); return; }
            var root = look.transform;
            string L(Vector3 p) => root.InverseTransformPoint(p).ToString("F3");
            string D(Vector3 d) => root.InverseTransformDirection(d).normalized.ToString("F2");
            foreach (bool left in new[] { true, false })
            {
                Transform B(string n) => look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), (left ? "Left" : "Right") + n));
                var lower = B("LowerArm"); var hand = B("Hand"); var index = B("IndexProximal"); var middle = B("MiddleProximal"); var little = B("LittleProximal");
                var thumb = B("ThumbProximal"); var thumbTip = B("ThumbDistal"); var midTip = B("MiddleDistal");
                if (!hand || !index || !little || !middle) { Debug.Log($"[HandDiag] {label} {(left ? "L" : "R")}: missing bones"); continue; }
                var axis = (middle.position - hand.position).normalized;
                var knuckles = little.position - index.position;   // index -> little
                // palm side: the fingertips curl toward it, so it is where the middle tip sits off the hand axis
                var palm = midTip ? Vector3.ProjectOnPlane(midTip.position - middle.position, axis) : Vector3.zero;
                Debug.Log($"[HandDiag] {label} {(left ? "L" : "R")}: names lower={lower?.name} hand={hand.name} index={index.name} little={little.name} thumb={thumb?.name} | " +
                          $"hand {L(hand.position)} index {L(index.position)} little {L(little.position)} thumb {(thumb ? L(thumb.position) : "-")} thumbTip {(thumbTip ? L(thumbTip.position) : "-")} | " +
                          $"axis {D(axis)} index->little {D(knuckles)} palmSide {D(palm)} forearmUp {(lower ? D(lower.up) : "-")} handUp {D(hand.up)} handFwd {D(hand.forward)}");
            }
        }
        /// Every right-hand finger joint in the hero's own space, and each bone's local rotation and bind-relative rotation.
        static void FingerReport(GolfArcade.Tennis.MatchHeroLook look, string label)
        {
            var root = look.transform;
            foreach (var f in new[] { "Thumb", "Index", "Middle", "Ring", "Little" })
            {
                var line = new System.Text.StringBuilder($"[FingerDiag] {label} R {f}:");
                foreach (var j in new[] { "Proximal", "Intermediate", "Distal" })
                {
                    var b = look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), "Right" + f + j)); if (!b) { line.Append(" -"); continue; }
                    line.Append($" {j[0]}{root.InverseTransformPoint(b.position).ToString("F3")} rot{b.localRotation.eulerAngles.ToString("F0")}");
                }
                Debug.Log(line.ToString());
            }
            // in the bind pose: how far off the finger's own line (intermediate -> distal head) the fingertip HubHeroAnimator aims at lies
            var body = look.body; var mesh = body ? body.sharedMesh : null;
            if (!mesh || !mesh.isReadable) { Debug.Log($"[TipDiag] {label}: body mesh not readable"); return; }
            var pal = body.bones; var bp = mesh.bindposes; var v = mesh.vertices; var w = mesh.boneWeights;
            foreach (var side in new[] { "Left", "Right" })
                foreach (var f in new[] { "Thumb", "Index", "Middle", "Ring", "Little" })
                {
                    var mid = look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), side + f + "Intermediate"));
                    var dis = look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), side + f + "Distal"));
                    int di = System.Array.IndexOf(pal, dis), ii = System.Array.IndexOf(pal, mid);
                    if (di < 0 || ii < 0) { Debug.Log($"[TipDiag] {label} {side} {f}: not in palette"); continue; }
                    Vector3 head = bp[di].inverse.GetColumn(3), prev = bp[ii].inverse.GetColumn(3);
                    float best = -1; Vector3 far = head, sum = Vector3.zero; int count = 0;
                    for (int k = 0; k < v.Length; k++)
                    {
                        float amt = (w[k].boneIndex0 == di ? w[k].weight0 : 0) + (w[k].boneIndex1 == di ? w[k].weight1 : 0) + (w[k].boneIndex2 == di ? w[k].weight2 : 0) + (w[k].boneIndex3 == di ? w[k].weight3 : 0);
                        if (amt < .5f) continue; count++; sum += v[k]; float d = (v[k] - head).sqrMagnitude; if (d > best) { best = d; far = v[k]; }
                    }
                    // the hand's frame in the bind pose (as CurlFingers builds it from the bones)
                    Vector3 H(string n) => bp[System.Array.IndexOf(pal, look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), side + n)))].inverse.GetColumn(3);
                    var axis = (H("MiddleProximal") - H("Hand")).normalized;
                    var across = Vector3.ProjectOnPlane(H("IndexProximal") - H("LittleProximal"), axis).normalized;
                    var palm = side == "Left" ? Vector3.Cross(across, axis) : Vector3.Cross(axis, across);
                    var line = (head - prev).normalized; var toPalm = Vector3.ProjectOnPlane(palm, line).normalized; var sideways = Vector3.Cross(line, toPalm);
                    string Split(Vector3 p) { var d = (p - head).normalized; return $"curl {Mathf.Atan2(Vector3.Dot(d, toPalm), Vector3.Dot(d, line)) * Mathf.Rad2Deg:F0} side {Mathf.Atan2(Vector3.Dot(d, sideways), Vector3.Dot(d, line)) * Mathf.Rad2Deg:F0}"; }
                    var centre = count > 0 ? sum / count : head;
                    Debug.Log($"[TipDiag] {label} {side} {f}: verts {count} farthest {Mathf.Sqrt(best) * 100:F1} cm ({Split(far)}), centre ({Split(centre)}); segment {(head - prev).magnitude * 100:F1} cm");
                    // the two segments with a child: the mesh's own direction (centre of the vertices on the bone) against the bone line
                    foreach (var (j, c) in new[] { ("Proximal", "Intermediate"), ("Intermediate", "Distal") })
                    {
                        var seg = look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), side + f + j));
                        var child = look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), side + f + c));
                        int si = System.Array.IndexOf(pal, seg), ci = System.Array.IndexOf(pal, child); if (si < 0 || ci < 0) continue;
                        Vector3 sh = bp[si].inverse.GetColumn(3), ch = bp[ci].inverse.GetColumn(3); Vector3 ssum = Vector3.zero; int sn = 0;
                        for (int k = 0; k < v.Length; k++)
                        {
                            float amt = (w[k].boneIndex0 == si ? w[k].weight0 : 0) + (w[k].boneIndex1 == si ? w[k].weight1 : 0) + (w[k].boneIndex2 == si ? w[k].weight2 : 0) + (w[k].boneIndex3 == si ? w[k].weight3 : 0);
                            if (amt >= .5f) { ssum += v[k]; sn++; }
                        }
                        var sline = (ch - sh).normalized; var stoPalm = Vector3.ProjectOnPlane(palm, sline).normalized; var sside = Vector3.Cross(sline, stoPalm);
                        var sd = sn > 0 ? (ssum / sn - sh).normalized : sline;
                        Debug.Log($"[TipDiag] {label} {side} {f} {j}: verts {sn} centre curl {Mathf.Atan2(Vector3.Dot(sd, stoPalm), Vector3.Dot(sd, sline)) * Mathf.Rad2Deg:F0} side {Mathf.Atan2(Vector3.Dot(sd, sside), Vector3.Dot(sd, sline)) * Mathf.Rad2Deg:F0}");
                    }
                }
        }
        static void Film(Camera cam, int w, int h, string name)
        {
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var keep = cam.rect; cam.rect = new Rect(0, 0, 1, 1); cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.rect = keep;
            var t = Read(rt, w, h); File.WriteAllBytes(Path.Combine(Dir, name + ".jpg"), t.EncodeToJPG(85));
            Object.DestroyImmediate(t); rt.Release(); Object.DestroyImmediate(rt);
        }

        /// The menu hero, female and male, as the TV shows them and close up on the arms from the front, the side and behind
        /// (2026-11-08: "female arm anatomy messed up, her arms are inverted").
        [UnityTest, Timeout(300000)] public IEnumerator HeroArmsFemale() { yield return HeroArms(true); }
        [UnityTest, Timeout(300000)] public IEnumerator HeroArmsMale() { yield return HeroArms(false); }
        IEnumerator HeroArms(bool female)
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("PM_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "hero-arms", action = "start", sport = "hub", menu = true, leader = true, playerName = "Ana", female = female, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Player, "menu hero");
            hub.StartArrival(); yield return Wait(3f);
            string sex = female ? "female" : "male";
            HandReport(hub.Player.hero, sex + " menu");
            var cam = hub.Camera;
            Film(cam, 1080, 1350, $"20_{sex}_menu");
            var t = hub.Player.transform; Vector3 chest = t.position + Vector3.up * 1.2f;
            float fov = cam.fieldOfView; cam.fieldOfView = 34;
            foreach (var (view, name) in new[] { (t.forward, "front"), (t.right, "side"), (-t.forward, "back") })
            {
                cam.transform.SetPositionAndRotation(chest + view * 2.3f, Quaternion.LookRotation(-view, Vector3.up));
                Film(cam, 1080, 1350, $"21_{sex}_arms_{name}");
            }
            cam.fieldOfView = fov;
            hub.Hud.Go(MenuHud.Locker); yield return Wait(2f);   // the locker's plain stand
            HandReport(hub.Player.hero, sex + " locker");
            // the right hand up close: outside, front, inside (the thigh side seen past the hip)
            var look = hub.Player.hero.GetComponentInChildren<GolfArcade.Tennis.MatchHeroLook>() ?? hub.Player.hero.GetComponentInParent<GolfArcade.Tennis.MatchHeroLook>();
            var hand = look.Bone(HumanBodyBones.RightHand); var mid = look.Bone(HumanBodyBones.RightMiddleIntermediate);
            Vector3 at = (hand.position + mid.position) / 2; cam.fieldOfView = 30;
            foreach (var (view, name) in new[] { (t.right, "outside"), (t.forward, "front"), (-t.forward, "back") })
            {
                cam.transform.SetPositionAndRotation(at + view * .45f, Quaternion.LookRotation(-view, Vector3.up));
                Film(cam, 900, 900, $"24_{sex}_hand_{name}");
            }
            cam.fieldOfView = fov;
            FingerReport(look, sex + " locker");
            cam.transform.SetPositionAndRotation(chest + t.forward * 2.3f, Quaternion.LookRotation(-t.forward, Vector3.up)); cam.fieldOfView = 34;
            Film(cam, 1080, 1350, $"22_{sex}_locker_front");
            cam.fieldOfView = fov;
        }

        /// A bowling game started as the phone starts it, with the female bowler: resumed before the motion sensors speak, it waits for them
        /// (2026-11-08: "starting up bowling it's just frozen"; the half-second input watchdog paused it while they were still starting), then
        /// pauses once the grace is over with none. With PM_OUT, her hands are filmed up close (one on the ball, one empty).
        [UnityTest, Timeout(300000)] public IEnumerator BowlingWaitsForTheSensorsAndHerHandsAreHers()
        {
            AudioListener.volume = 0; LogAssert.ignoreFailingMessages = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            const string id = "bowling-start-check";
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = id, action = "start", sport = "bowling", female = true, playerName = "Ana", token = 7, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF" }));
            // batch mode has no screen to draw on: the gameplay camera is drawn by hand, as a display would, until the game has seen a frame
            var cameraField = typeof(NativeSportsSession).GetField("gameplayCamera", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
            var target = new RenderTexture(640, 360, 24);
            for (int i = 0; i < 3000 && !bridge.Ready; i++)
            {
                yield return null;
                if (cameraField?.GetValue(bridge) is Camera game && game) { var keep = game.targetTexture; game.targetTexture = target; game.Render(); game.targetTexture = keep; }
            }
            target.Release(); Object.DestroyImmediate(target);
            Assert.IsTrue(bridge.Ready, "the bowling game loaded and drew");
            var pausedField = typeof(NativeSportsSession).GetField("paused", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = id, action = "resume" }));
            float resumed = Time.realtimeSinceStartup;
            while (Time.realtimeSinceStartup - resumed < 1.2f) yield return null;
            Assert.IsFalse((bool)pausedField.GetValue(bridge), "a second after Ready, with the sensors not yet sending, the game still waits for them");
            while (Time.realtimeSinceStartup - resumed < 2.8f) yield return null;
            Assert.IsTrue((bool)pausedField.GetValue(bridge), "with nothing from the sensors past the grace, it pauses for missing input");
            if (string.IsNullOrEmpty(Dir)) yield break;
            Directory.CreateDirectory(Dir);
            var look = System.Linq.Enumerable.FirstOrDefault(Object.FindObjectsByType<GolfArcade.Tennis.MatchHeroLook>(FindObjectsSortMode.None), l => l.female && l.isActiveAndEnabled);
            Assert.IsNotNull(look, "the female bowler");
            var cam = new GameObject("Hand camera").AddComponent<Camera>(); cam.fieldOfView = 32; cam.nearClipPlane = .05f;
            var root = look.transform;
            foreach (var (bone, name) in new[] { (HumanBodyBones.RightHand, "right"), (HumanBodyBones.LeftHand, "left") })
            {
                var hand = look.Bone(bone); if (!hand) continue;
                foreach (var (view, side) in new[] { (root.forward, "front"), (bone == HumanBodyBones.RightHand ? root.right : -root.right, "outside") })
                {
                    cam.transform.SetPositionAndRotation(hand.position + view * .55f, Quaternion.LookRotation(-view, Vector3.up));
                    Film(cam, 900, 900, $"30_bowling_female_{name}_{side}");
                }
            }
            cam.transform.SetPositionAndRotation(root.position + Vector3.up * 1.1f + root.forward * 3.2f, Quaternion.LookRotation(-root.forward, Vector3.up));
            Film(cam, 1080, 1350, "31_bowling_female_full");
            Object.DestroyImmediate(cam.gameObject);
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
