using GolfArcade.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Tests
{
    /// UI THEME (golf aim HUD, phase 0): the theme follows the sport, never the map, and what is themed recolors with it.
    public sealed class UiThemeTests
    {
        static readonly Color Gold = new(0xF5 / 255f, 0xC5 / 255f, 0x42 / 255f), SoftGold = new(1f, 0xD1 / 255f, 0x66 / 255f);

        [TearDown] public void Reset() => ThemeService.Apply("golf");

        [Test]
        public void SportsPickTheirOwnTheme()
        {
            var golf = ThemeService.Apply("golf");
            Assert.AreEqual("Theme_Golf_EmeraldGold", golf.name);
            AssertColour(Gold, golf.Get(ThemeRole.SweetSpot));
            AssertColour(new Color(0x10 / 255f, 0x93 / 255f, 0x6B / 255f), golf.panelTop, ignoreAlpha: true);
            var tennis = ThemeService.Apply("tennis");
            Assert.AreEqual("Theme_Tennis_RoyalBlue", tennis.name);
            AssertColour(SoftGold, tennis.Get(ThemeRole.MeterFill));
            AssertColour(new Color(0x34 / 255f, 0x78 / 255f, 0xEC / 255f), tennis.panelTop, ignoreAlpha: true);
            Assert.AreSame(tennis, ThemeService.Current);
        }

        [Test]
        public void UnknownSportsAndScenesTakeTheDefault()
        {
            var golf = ThemeService.Apply("golf");
            Assert.AreSame(golf, ThemeService.Apply("padel"), "an unknown sport falls back to the default (golf)");
            Assert.AreSame(golf, ThemeService.Apply(null));
            Assert.AreEqual("golf", ThemeService.SportOf("Golf"));
            Assert.AreEqual("tennis", ThemeService.SportOf("Tennis"));
            Assert.IsNull(ThemeService.SportOf("Hub"), "the hub and menus use the default");
        }

        [Test]
        public void ThemedGraphicsRecolorWhenTheThemeChanges()
        {
            ThemeService.Apply("golf");
            var go = new GameObject("themed", typeof(Image));
            try
            {
                var themed = go.AddComponent<ThemedGraphic>();
                themed.role = ThemeRole.Accent; themed.Refresh();
                var image = go.GetComponent<Image>();
                AssertColour(Gold, image.color);
                ThemeService.Apply("tennis");   // fires Changed
                AssertColour(SoftGold, image.color);
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void SmallTextNeverFadesBelowTheThemesMinimum()
        {
            var golf = ThemeService.Apply("golf");
            Assert.GreaterOrEqual(golf.Get(ThemeRole.PanelTextMuted, 0.3f).a, golf.minTextOpacity - 1e-4f);
            Assert.AreEqual(.13f, golf.Get(ThemeRole.MeterRail).a, 1e-4f);
        }

        static void AssertColour(Color want, Color got, bool ignoreAlpha = false)
        {
            Assert.AreEqual(want.r, got.r, .004f); Assert.AreEqual(want.g, got.g, .004f); Assert.AreEqual(want.b, got.b, .004f);
            if (!ignoreAlpha) Assert.AreEqual(want.a, got.a, .004f);
        }
    }
}
