using System.Collections;
using System.IO;
using GolfArcade.Bowling;
using GolfArcade.Tennis;
using GolfArcade.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace GolfArcade.PlayTests
{
    /// UI OVERHAUL 11-15: every map's TV pieces build in its skin (sculpted art loaded, usernames shown, no YOU) and render over the
    /// map's reference picture; PNGs to $UO_UNITY_OUT for the proof boards beside the design boards.
    public sealed class UiOverhaulCaptureTests
    {
        static string Out => System.Environment.GetEnvironmentVariable("UO_UNITY_OUT");
        static string Repo => System.Environment.GetEnvironmentVariable("UO_REPO") ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

        Camera camera; RenderTexture rt; GameObject backdrop;

        [SetUp] public void SetUp()
        {
            rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            camera = new GameObject("Capture camera").AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.1f, .14f, .22f); camera.targetTexture = rt;
            MapSkin.LocalName = "Adnan";
        }
        [TearDown] public void TearDown()
        {
            foreach (var g in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (g) Object.Destroy(g.gameObject);
            if (camera) Object.Destroy(camera.gameObject);
            if (rt) rt.Release();
            TennisVenue.Selected = TennisVenueKind.Resort; BowlingVenue.Selected = BowlingVenueKind.ClubLanes; MapSkin.LocalName = "";
        }

        Canvas NewCanvas(string name, float plane, Vector2 reference)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var c = go.AddComponent<Canvas>(); c.renderMode = RenderMode.ScreenSpaceCamera; c.worldCamera = camera; c.planeDistance = plane;
            var s = go.AddComponent<CanvasScaler>(); s.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; s.referenceResolution = reference; s.matchWidthOrHeight = .5f;
            return c;
        }
        void Backdrop(string map)
        {
            if (backdrop) Object.Destroy(backdrop);
            var c = NewCanvas("Backdrop", 5, new Vector2(1920, 1080)); backdrop = c.gameObject;
            var img = new GameObject("Map", typeof(RectTransform)).AddComponent<RawImage>(); img.transform.SetParent(c.transform, false);
            var r = img.rectTransform; r.anchorMin = Vector2.zero; r.anchorMax = Vector2.one; r.offsetMin = r.offsetMax = Vector2.zero;
            var path = Path.Combine(Repo, "GolfArcade/Unity/MenuArt", map + ".jpg");
            if (File.Exists(path)) { var t = new Texture2D(2, 2); t.LoadImage(File.ReadAllBytes(path)); img.texture = t; }
            else img.color = new Color(.2f, .35f, .5f);
        }
        IEnumerator Save(string name)
        {
            // (a frame, then an explicit render: WaitForEndOfFrame never comes in a batchmode run)
            yield return null;
            Canvas.ForceUpdateCanvases(); camera.Render();
            if (string.IsNullOrEmpty(Out)) yield break;
            Directory.CreateDirectory(Out);
            var prev = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false); tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); tex.Apply();
            RenderTexture.active = prev;
            File.WriteAllBytes(Path.Combine(Out, name + ".png"), tex.EncodeToPNG());
            Object.Destroy(tex);
        }
        static void Clear() { foreach (var g in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (g && g.name != "Backdrop") Object.Destroy(g.gameObject); }

        [Test] public void EveryMapSkinHasItsArt()
        {
            foreach (var s in MapSkin.All)
            {
                Assert.IsNotNull(s.TitleSprite, s.Id + " title"); Assert.IsNotNull(s.PlateSprite, s.Id + " plate");
                if (s.Id.StartsWith("tennis") || s.Id.StartsWith("bowling") || s.Id.StartsWith("golf")) Assert.IsNotNull(s.EventSprite, s.Id + " event");
                foreach (var w in new[] { "TENNIS", "GOLF", "BOWLING" }) Assert.IsFalse(s.Title.Contains(w), s.Title);
            }
            Assert.IsNotNull(MapSkin.Call("ACE")); Assert.IsNotNull(MapSkin.Call("OUT"));
            Assert.AreNotEqual(UiKit.Display, MapSkin.Bold, "Fredoka is in Resources");
            Assert.IsNotNull(MapSkin.Golf("wildisles").LoadingArt(0), "Wild Isles now has loading art");
        }

        [UnityTest] public IEnumerator TennisScoreboardPointAndArrival()
        {
            foreach (var (kind, map) in new[] { (TennisVenueKind.Resort, "map-resort"), (TennisVenueKind.Skyscraper, "map-skyscraper"), (TennisVenueKind.Volcano, "map-volcano") })
            {
                TennisVenue.Selected = kind; Backdrop(map);
                var canvas = NewCanvas("Tennis HUD", 1, new Vector2(1280, 720));
                var hud = canvas.gameObject.AddComponent<TennisHud>();
                hud.OpponentName = "MILO"; hud.Build(canvas); hud.MatchVisible = true;
                var m = TennisMatch.New(); m.PlayerGames = 3; m.OpponentGames = 2; m.PlayerPoints = 2; m.OpponentPoints = 1;
                hud.ShowPointResult(hud.ShownPlayerName, "ACE · 30-15", true);
                for (int i = 0; i < 40; i++) { hud.RefreshAs(m, false, 0, true); yield return null; }
                Assert.AreEqual("ADNAN SCORED", hud.PointResultText, "usernames, never YOU");
                yield return Save("tv-tennis-" + kind.ToString().ToLowerInvariant() + "-live");
                Clear(); yield return null;
                var intro = NewCanvas("Intro", 1, new Vector2(1920, 1080));
                var g = IntroGraphics.On((RectTransform)intro.transform);
                float t0 = Time.time;
                g.ShowMapTitle(MapSkin.Tennis, false, t0);
                for (int i = 0; i < 50; i++) { g.Tick(Time.time); yield return null; }
                yield return Save("tv-tennis-" + kind.ToString().ToLowerInvariant() + "-arrival");
                Clear(); yield return null;
                var stare = NewCanvas("Intro", 1, new Vector2(1920, 1080));
                var g2 = IntroGraphics.On((RectTransform)stare.transform);
                g2.ShowNamePlate(MapSkin.Tennis, "Adnan", false, Time.time, 70); g2.ShowNamePlate(MapSkin.Tennis, "Milo", true, Time.time, 70); g2.ShowVs(Time.time);
                for (int i = 0; i < 50; i++) { g2.Tick(Time.time); yield return null; }
                yield return Save("tv-tennis-" + kind.ToString().ToLowerInvariant() + "-players");
                Clear(); yield return null;
            }
        }

        [UnityTest] public IEnumerator GolfMeterAndCourseCard()
        {
            foreach (var key in new[] { "cliffside", "wildisles", "magma" })
            {
                Backdrop("map-golf-" + key);
                var hud = GolfShotHud.Create(camera);
                hud.ApplySkin(MapSkin.Golf(key));
                hud.SetHole(1, 4); hud.SetDistance(416, "yd"); hud.SetPower(.72f, "204 yd");
                for (int i = 0; i < 20; i++) yield return null;
                var pct = hud.GetComponentsInChildren<Text>(true);
                bool found = false; foreach (var t in pct) if (t.name == "Percent" && t.text == "72%" && t.isActiveAndEnabled) found = true;
                Assert.IsTrue(found, "the small live percentage reads 72%");
                yield return Save("tv-golf-" + key + "-live");
                Object.Destroy(hud.gameObject); yield return null;
            }
        }

        [UnityTest] public IEnumerator BowlingScorecardSpeedAndStrike()
        {
            foreach (var (kind, map) in new[] { (BowlingVenueKind.ClubLanes, "map-bowling-club"), (BowlingVenueKind.NeonNights, "map-bowling-neon"),
                                               (BowlingVenueKind.TikiShores, "map-bowling-tiki"), (BowlingVenueKind.MagmaLanes, "map-bowling-magma") })
            {
                BowlingVenue.Selected = kind; Backdrop(map);
                var hud = new BowlingHud(camera, new[] { "Adnan", "Milo" });
                var s = new BowlingScore(); foreach (var p in new[] { 9, 1, 5, 5, 6, 0 }) s.Roll(p);
                hud.Score(0, s, true); hud.Score(1, new BowlingScore(), false); hud.Speed(17.2f);
                hud.Banner("STRIKE!", null, 5, BowlingHud.Praise.Big);
                for (int i = 0; i < 30; i++) { hud.Tick(); yield return null; }
                yield return Save("tv-bowling-" + kind.ToString().ToLowerInvariant() + "-live");
                hud.Dispose(); yield return null;
            }
        }
    }
}
