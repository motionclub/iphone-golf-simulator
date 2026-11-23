using System.Collections;
using System.IO;
using GolfArcade.Bowling;
using GolfArcade.Game;
using GolfArcade.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace GolfArcade.PlayTests
{
    /// UI OVERHAUL 11-16: the new in-game UI on a phone with no TV (handheld play: the game in the top three quarters of an upright
    /// phone, the app's deck over the bottom quarter, NativeSportsSession.Handheld) and the Daily Challenge's opening in the game's
    /// own UI. Each piece is built on a camera with the handheld viewport and drawn over the map's picture; the deck's quarter is
    /// painted navy in the PNG (the app draws it). Asserts every piece stays inside the game's part of the screen.
    public sealed class UiOverhaulHandheldCaptureTests
    {
        static string Out => System.Environment.GetEnvironmentVariable("UO_UNITY_OUT");
        static string Repo => System.Environment.GetEnvironmentVariable("UO_REPO") ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
        const int PhoneW = 1206, PhoneH = 2622;

        Camera camera; RenderTexture rt; GameObject backdrop;

        void Make(bool handheld)
        {
            rt = handheld ? new RenderTexture(PhoneW, PhoneH, 24, RenderTextureFormat.ARGB32) : new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            camera = new GameObject("Capture camera").AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.1f, .14f, .22f); camera.targetTexture = rt;
            if (handheld) camera.rect = new Rect(0, NativeSportsSession.HandheldDeck, 1, 1 - NativeSportsSession.HandheldDeck);
            MapSkin.LocalName = "Adnan";
            GolfShotHud.Handheld = handheld;
        }
        [TearDown] public void TearDown()
        {
            foreach (var g in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (g) Object.Destroy(g.gameObject);
            if (camera) Object.Destroy(camera.gameObject);
            if (rt) rt.Release();
            BowlingVenue.Selected = BowlingVenueKind.RooftopLanes; MapSkin.LocalName = ""; GolfShotHud.Handheld = false;
        }

        Canvas NewCanvas(string name, float plane, Vector2 reference)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var c = go.AddComponent<Canvas>(); c.renderMode = RenderMode.ScreenSpaceCamera; c.worldCamera = camera; c.planeDistance = plane;
            var s = go.AddComponent<CanvasScaler>(); s.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; s.referenceResolution = reference; s.matchWidthOrHeight = .5f;
            return c;
        }
        /// The map's picture filling the game's part of the screen (cropped, not stretched).
        void Backdrop(string map)
        {
            if (backdrop) Object.Destroy(backdrop);
            var c = NewCanvas("Backdrop", 5, new Vector2(1920, 1080)); backdrop = c.gameObject;
            var img = new GameObject("Map", typeof(RectTransform)).AddComponent<RawImage>(); img.transform.SetParent(c.transform, false);
            var r = img.rectTransform; r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one; r.offsetMin = r.offsetMax = Vector2.zero;
            var path = Path.Combine(Repo, "GolfArcade/Unity/MenuArt", map + ".jpg");
            if (!File.Exists(path)) { img.color = new Color(.2f, .35f, .5f); return; }
            var t = new Texture2D(2, 2); t.LoadImage(File.ReadAllBytes(path)); img.texture = t;
            float view = camera.pixelWidth / (float)camera.pixelHeight, art = t.width / (float)t.height;
            img.uvRect = view < art ? new Rect((1 - view / art) / 2, 0, view / art, 1) : new Rect(0, (1 - art / view) / 2, 1, art / view);
        }
        IEnumerator Save(string name)
        {
            // (a frame, then an explicit render: WaitForEndOfFrame never comes in a batchmode run)
            yield return null;
            Canvas.ForceUpdateCanvases(); camera.Render();
            if (string.IsNullOrEmpty(Out)) yield break;
            Directory.CreateDirectory(Out);
            var prev = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            RenderTexture.active = prev;
            if (camera.rect.y > 0)
            {
                // the app's deck over the bottom quarter
                int deck = Mathf.RoundToInt(rt.height * camera.rect.y);
                var navy = new Color32(14, 26, 46, 255); var px = new Color32[rt.width * deck];
                for (int i = 0; i < px.Length; i++) px[i] = navy;
                tex.SetPixels32(0, 0, rt.width, deck, px);
            }
            tex.Apply();
            File.WriteAllBytes(Path.Combine(Out, name + ".png"), tex.EncodeToPNG());
            Object.Destroy(tex);
        }
        static void Clear() { foreach (var g in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (g && g.name != "Backdrop") Object.Destroy(g.gameObject); }

        /// Every visible graphic under `root` lies inside the camera's part of the screen (a small margin for drop shadows and tilt).
        void AssertInView(Transform root, string what)
        {
            var view = camera.pixelRect; view.xMin -= 12; view.xMax += 12; view.yMin -= 12; view.yMax += 12;
            var corners = new Vector3[4];
            foreach (var g in root.GetComponentsInChildren<Graphic>())
            {
                if (!g.isActiveAndEnabled || g.color.a < .05f || g is Text tx && string.IsNullOrEmpty(tx.text)) continue;
                var cg = g.GetComponentInParent<CanvasGroup>(); if (cg && cg.alpha < .05f) continue;
                g.rectTransform.GetWorldCorners(corners);
                foreach (var c in corners)
                {
                    var p = RectTransformUtility.WorldToScreenPoint(camera, c);
                    Assert.IsTrue(view.Contains(p), $"{what}: {g.name} ({g.transform.parent?.name}) at {p} is outside the game's view {camera.pixelRect}");
                }
            }
        }

        [UnityTest] public IEnumerator HandheldGolfHudAndIntro()
        {
            Make(true);
            foreach (var key in new[] { "cliffside", "wildisles", "magma" })
            {
                Backdrop("map-golf-" + key);
                var skin = MapSkin.Golf(key);
                var hud = GolfShotHud.Create(camera);
                hud.ApplySkin(skin);
                hud.SetHole(1, 4); hud.SetDistance(416, "yd"); hud.SetPower(.72f, "204 yd");
                for (int i = 0; i < 20; i++) yield return null;
                AssertInView(hud.transform, key + " shot HUD");
                yield return Save("handheld-golf-" + key + "-live");
                Object.Destroy(hud.gameObject); yield return null;

                // the flyover's map title with the hole's facts, then the golfer's name plate
                var intro = NewCanvas("Intro", 1, new Vector2(1920, 1080));
                var g = IntroGraphics.On((RectTransform)intro.transform);
                // (one after the other, as the game shows them: the title drops away before the tee's name plate comes up)
                var title = g.ShowMapTitle(skin, true, Time.time, 280, false, "HOLE 1  ·  PAR 4  ·  416 YD  ·  7 MPH LEFT TO RIGHT");
                for (int i = 0; i < 50; i++) { g.Tick(Time.time); yield return null; }
                AssertInView(intro.transform, key + " intro");
                yield return Save("handheld-golf-" + key + "-intro");
                g.Clear(); yield return null;
                g.ShowNamePlate(skin, "Adnan", false, Time.time);
                for (int i = 0; i < 50; i++) { g.Tick(Time.time); yield return null; }
                AssertInView(intro.transform, key + " name plate");
                yield return Save("handheld-golf-" + key + "-name");
                Clear(); yield return null;
            }
        }

        [UnityTest] public IEnumerator HandheldDailyChallengeOpening()
        {
            Make(true);
            Backdrop("map-golf-cliffside");
            var skin = MapSkin.Golf("cliffside");
            var intro = NewCanvas("Intro", 1, new Vector2(1920, 1080));
            var g = IntroGraphics.On((RectTransform)intro.transform);
            g.ShowWordTitle(skin, "DAILY CHALLENGE", false, Time.time, 250, false, "SHOT 1 OF 3  ·  31 YD OUT  ·  7 MPH LEFT TO RIGHT");
            Assert.IsTrue(g.Portrait, "the handheld view is upright");
            g.ShowWordTitle(skin, "3,000 PTS", true, Time.time, 170, false, "UP FOR GRABS  ·  ACE 1,000", g.Portrait ? 440 : -1);
            for (int i = 0; i < 50; i++) { g.Tick(Time.time); yield return null; }
            AssertInView(intro.transform, "daily opening");
            yield return Save("handheld-golf-daily-intro");
        }

        [UnityTest] public IEnumerator TvDailyChallengeOpening()
        {
            Make(false);
            foreach (var key in new[] { "cliffside", "magma" })
            {
                Backdrop("map-golf-" + key);
                var skin = MapSkin.Golf(key);
                var intro = NewCanvas("Intro", 1, new Vector2(1920, 1080));
                var g = IntroGraphics.On((RectTransform)intro.transform);
                var title = g.ShowWordTitle(skin, "DAILY CHALLENGE", false, Time.time, 250, false, "SHOT 2 OF 3  ·  104 YD OUT  ·  CALM");
                g.ShowWordTitle(skin, "1,240 PTS", true, Time.time, 170, false, "YOUR SCORE SO FAR");
                for (int i = 0; i < 50; i++) { g.Tick(Time.time); yield return null; }
                var words = title.root.GetComponentsInChildren<Text>();
                Assert.IsTrue(System.Array.Exists(words, t => t.text == "DAILY CHALLENGE"), "the plate reads DAILY CHALLENGE");
                Assert.IsNotNull(title.root.GetComponentInChildren<Image>().sprite, "on the course's sculpted plate");
                AssertInView(intro.transform, key + " daily opening");
                yield return Save("tv-golf-" + key + "-daily");
                Clear(); yield return null;
            }
        }

        [UnityTest] public IEnumerator HandheldBowlingHud()
        {
            Make(true);
            foreach (var (kind, map) in new[] { (BowlingVenueKind.RooftopLanes, "map-bowling-rooftop"), (BowlingVenueKind.BeachCourtLanes, "map-bowling-beachcourt"), (BowlingVenueKind.CraterLanes, "map-bowling-crater") })
            {
                BowlingVenue.Selected = kind; Backdrop(map);
                var hud = new BowlingHud(camera, new[] { "Adnan", "Milo" });
                var s = new BowlingScore(); foreach (var p in new[] { 9, 1, 5, 5, 6, 0 }) s.Roll(p);
                hud.Score(0, s, true); hud.Score(1, new BowlingScore(), false); hud.Speed(17.2f);
                hud.Banner("STRIKE!", null, 5, BowlingHud.Praise.Big);
                for (int i = 0; i < 30; i++) { hud.Tick(); yield return null; }
                yield return Save("handheld-bowling-" + kind.ToString().ToLowerInvariant() + "-live");
                hud.Dispose(); yield return null;
            }
        }
    }
}
