using GolfArcade.Game;
using GolfArcade.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace GolfArcade.Tests
{
    /// Handheld play (golf and bowling on a phone with no TV): the game keeps to the top three quarters, above the app's deck,
    /// and the golf HUD leaves the club and the hole map to the app.
    public class HandheldLayoutTests
    {
        Camera view; RenderTexture target; GolfShotHud hud;
        [TearDown] public void Clear()
        {
            GolfShotHud.Handheld = false; Hud.ReservedBottom = 0;
            if (hud) Object.DestroyImmediate(hud.gameObject);
            if (view) Object.DestroyImmediate(view.gameObject);
            if (target) Object.DestroyImmediate(target);
        }

        static bool Shown(GolfShotHud hud, string name)
        {
            foreach (var t in hud.GetComponentsInChildren<RectTransform>(true))
                if (t.name == name) return t.gameObject.activeSelf;
            Assert.Fail($"no {name} in the golf HUD"); return false;
        }

        void MakeHud(bool handheld)
        {
            // (building the HUD clears a placeholder with Destroy, which edit mode only logs)
            LogAssert.ignoreFailingMessages = true;
            GolfShotHud.Handheld = handheld;
            target = new RenderTexture(1320, 2868, 16);
            view = new GameObject("Handheld view").AddComponent<Camera>();
            view.targetTexture = target;
            view.rect = new Rect(0, NativeSportsSession.HandheldDeck, 1, 1 - NativeSportsSession.HandheldDeck);
            hud = GolfShotHud.Create(view);
            hud.RefreshLayout();
        }

        [Test]
        public void HandheldGolfHudLeavesTheClubAndTheMapToTheApp()
        {
            MakeHud(true);
            Assert.IsFalse(Shown(hud, "Hole map"), "the app draws the hole map (tap to open it)");
            Assert.IsFalse(Shown(hud, "Club selection"), "the deck has the club");
        }

        [Test]
        public void OnATvTheGolfHudKeepsTheClubAndTheMap()
        {
            MakeHud(false);
            Assert.IsTrue(Shown(hud, "Hole map"));
            Assert.IsTrue(Shown(hud, "Club selection"));
        }

        [Test]
        public void TheCameraKeepsToTheTopThreeQuarters()
        {
            MakeHud(true);
            Assert.AreEqual(.25f, NativeSportsSession.HandheldDeck, 1e-6f, "the app's deck (SportsSession.handheldDeck) is the bottom quarter");
            Assert.AreEqual(Mathf.RoundToInt(2868 * .75f), Mathf.RoundToInt(view.pixelHeight), 1);
            Assert.AreEqual(Mathf.RoundToInt(2868 * .25f), Mathf.RoundToInt(view.pixelRect.yMin), 1);
        }
    }
}
