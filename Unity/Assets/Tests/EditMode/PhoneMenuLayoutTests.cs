using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The pointer menu on a phone with no TV (HubWorld.PhoneMenuView, 2026-11-08: "the menu should fit the screen"): the menu's upright
    /// frame is the whole phone under the status bar, nothing of the app's under it; the camera holds the centred pose through the
    /// plate's own lens (MenuShots.For).
    public class PhoneMenuLayoutTests
    {
        [TearDown] public void Clear() { HubWorld.PhoneOnly = false; }

        static void FillsThePhone(Vector2 screen, Rect safe)
        {
            var f = HubWorld.PhoneMenuView(screen, safe);
            Assert.AreEqual(0, f.x, .01f, $"{screen}: the whole width");
            Assert.AreEqual(screen.x, f.width, .01f, $"{screen}: the whole width");
            Assert.AreEqual(0, f.y, .01f, $"{screen}: down to the bottom edge (no app bar under the menu)");
            Assert.AreEqual(safe.yMax, f.yMax, .01f, $"{screen}: up to the status bar, never under it");
        }

        [Test] public void EveryUprightIPhoneGetsTheWholeScreenUnderTheStatusBar()
        {
            FillsThePhone(new Vector2(1179, 2556), new Rect(0, 102, 1179, 2556 - 279));   // iPhone 15 / 16 Pro
            FillsThePhone(new Vector2(1206, 2622), new Rect(0, 102, 1206, 2622 - 288));   // iPhone 17 Pro
            FillsThePhone(new Vector2(1290, 2796), new Rect(0, 102, 1290, 2796 - 279));   // Pro Max
            FillsThePhone(new Vector2(750, 1334), new Rect(0, 0, 750, 1334 - 40));        // iPhone SE
        }

        [Test] public void AMissingSafeAreaStillLeavesAMenu()
        {
            var f = HubWorld.PhoneMenuView(new Vector2(1179, 2556), new Rect(0, 0, 0, 0));
            Assert.Greater(f.height, 2556 * .49f);
        }

        [Test] public void ThePhoneHoldsTheCentredPoseThroughThePlatesLens()
        {
            HubWorld.PhoneOnly = true;
            foreach (var id in new[] { MenuShots.Low, MenuShots.Close, MenuShots.Mid, MenuShots.Solo })
            {
                var s = MenuShots.For(id, 3);
                Assert.AreEqual(MenuShots.CentreShot.position, s.position, id);
                Assert.AreEqual(MenuShots.CentreShot.look, s.look, id);
                Assert.AreEqual(MenuShots.CentreShot.fov, s.fov, 1e-4f, "the plate's lens: a wider one runs past its edges");
            }
        }
    }
}
