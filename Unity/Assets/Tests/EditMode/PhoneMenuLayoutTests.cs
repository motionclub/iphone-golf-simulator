using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The pointer menu on a phone with no TV (HubWorld.PhoneMenuView): the hero on top, the menu's 16:9 frame under him (never over
    /// him), the app's controls under that; and the phone's own lens on the menu pose (MenuShots.PhoneShot).
    public class PhoneMenuLayoutTests
    {
        [TearDown] public void Clear() { HubWorld.PhoneOnly = false; }

        static void Stacked(Vector2 screen, Rect safe)
        {
            var v = HubWorld.PhoneMenuView(screen, safe);
            Assert.IsTrue(v.stacked, $"{screen}: hero above the menu");
            Assert.AreEqual(screen.x, v.hud.width, .01f, "the frame spans the phone");
            Assert.AreEqual(screen.x * 9 / 16, v.hud.height, .01f, "16:9");
            Assert.AreEqual(screen.y * HubWorld.PhoneMenuFooter, v.hud.y, .01f, "the app's controls keep the footer");
            Assert.AreEqual(v.hud.yMax / screen.y, v.camera.y, 1e-4f, "the hero starts where the frame ends: no overlap");
            Assert.AreEqual(1, v.camera.yMax, 1e-4f, "and has the top of the screen");
            float heroPoints = v.camera.height * screen.y;
            Assert.Greater(heroPoints, screen.y - safe.yMax + screen.x * .8f, "room for him below the status bar");
        }

        [Test] public void EveryUprightIPhoneStacksTheHeroAboveTheMenu()
        {
            Stacked(new Vector2(1179, 2556), new Rect(0, 102, 1179, 2556 - 279));   // iPhone 15 / 16 Pro
            Stacked(new Vector2(1290, 2796), new Rect(0, 102, 1290, 2796 - 279));   // Pro Max
            Stacked(new Vector2(750, 1334), new Rect(0, 0, 750, 1334 - 40));        // iPhone SE
        }

        [Test] public void AScreenTooShortKeepsTheBandUnderTheStatusBar()
        {
            var screen = new Vector2(1334, 750); var safe = new Rect(0, 0, 1334, 750);
            var v = HubWorld.PhoneMenuView(screen, safe);
            Assert.IsFalse(v.stacked);
            Assert.AreEqual(v.hud.y / screen.y, v.camera.y, 1e-4f, "the hero in the band, as on the TV");
            Assert.AreEqual(v.hud.height / screen.y, v.camera.height, 1e-4f);
            Assert.LessOrEqual(v.hud.yMax, safe.yMax + .01f, "never under the status bar");
        }

        [Test] public void ThePhoneHoldsOneWiderLensOnTheCentredPose()
        {
            HubWorld.PhoneOnly = true;
            foreach (var id in new[] { MenuShots.Low, MenuShots.Close, MenuShots.Mid, MenuShots.Solo })
            {
                var s = MenuShots.For(id, 3);
                Assert.AreEqual(MenuShots.CentreShot.position, s.position, id);
                Assert.AreEqual(MenuShots.CentreShot.look, s.look, id);
                Assert.Greater(s.fov, MenuShots.CentreShot.fov, "zoomed out a little from the TV's");
            }
        }
    }
}
