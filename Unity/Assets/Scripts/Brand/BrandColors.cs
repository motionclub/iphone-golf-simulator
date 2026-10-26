// MotionSports brand tokens - generated from motionsports_tokens.json (2026-10-24).
// Drop into Assets/Scripts/Brand/. Colors are sRGB; Unity's Color constructor takes 0-1 floats.
// Source: MotionSports_Brand_Guide.pdf v1.0, Appendix A (copied verbatim).
using UnityEngine;

namespace MotionSports.Brand
{
    public static class BrandColors
    {
        /// <summary>Navy Ink #061A4B - Deepest UI ink: HUD bar tracks, text on gold buttons, modal scrims</summary>
        public static readonly Color NavyInk = new Color(0.0235f, 0.102f, 0.2941f, 1f);
        /// <summary>Deep Navy #0B2878 - Top of every background gradient; HUD plates; panel fill</summary>
        public static readonly Color NavyDeep = new Color(0.0431f, 0.1569f, 0.4706f, 1f);
        /// <summary>Royal Blue #003EB8 - Primary brand field: screen backgrounds, store screenshots</summary>
        public static readonly Color Royal = new Color(0.0f, 0.2431f, 0.7216f, 1f);
        /// <summary>Icon Blue #0044BF - App icon field only; alt primary</summary>
        public static readonly Color IconBlue = new Color(0.0f, 0.2667f, 0.749f, 1f);
        /// <summary>Bright Blue #1F62D6 - Gradient end of headline band; hover/selected surfaces</summary>
        public static readonly Color Bright = new Color(0.1216f, 0.3843f, 0.8392f, 1f);
        /// <summary>Lift Blue #286EE6 - Radial spotlight behind the hero object</summary>
        public static readonly Color Lift = new Color(0.1569f, 0.4314f, 0.902f, 1f);
        /// <summary>Glow Blue #78BEFF - Soft outer glow around TV frames, focus rings, info</summary>
        public static readonly Color Glow = new Color(0.4706f, 0.7451f, 1.0f, 1f);
        /// <summary>Headline Gold #F5C542 - Accent: 2nd headline line, primary buttons, rewards, PERFECT!</summary>
        public static readonly Color Gold = new Color(0.9608f, 0.7725f, 0.2588f, 1f);
        /// <summary>Wordmark Gold #F1B120 - 'Sports' in the wordmark only</summary>
        public static readonly Color GoldWordmark = new Color(0.9451f, 0.6941f, 0.1255f, 1f);
        /// <summary>Gold Deep #C48812 - Pressed/bottom edge of gold buttons, gold text on light</summary>
        public static readonly Color GoldDeep = new Color(0.7686f, 0.5333f, 0.0706f, 1f);
        /// <summary>Arc Warm #EDB15D - Warm fringe of the swing arc</summary>
        public static readonly Color ArcWarm = new Color(0.9294f, 0.6941f, 0.3647f, 1f);
        /// <summary>White #FFFFFF - 1st headline line, card borders, arc core, body text</summary>
        public static readonly Color White = new Color(1.0f, 1.0f, 1.0f, 1f);
        /// <summary>Shadow Ink #000A32 - Color of all drop shadows (never pure black)</summary>
        public static readonly Color ShadowInk = new Color(0.0f, 0.0392f, 0.1961f, 1f);
        /// <summary>Text Shadow #00082D - TMP underlay under headlines/wordmark</summary>
        public static readonly Color TextShadow = new Color(0.0f, 0.0314f, 0.1765f, 1f);
        /// <summary>TV Bezel #10121A - Device/TV frames in marketing + replays</summary>
        public static readonly Color Bezel = new Color(0.0627f, 0.0706f, 0.102f, 1f);
        /// <summary>Bezel Rim #40485E - Inner rim line on frames</summary>
        public static readonly Color BezelRim = new Color(0.251f, 0.2824f, 0.3686f, 1f);
        /// <summary>Success Green #34C77B - Wins, IN calls, unlocked, connected</summary>
        public static readonly Color Success = new Color(0.2039f, 0.7804f, 0.4824f, 1f);
        /// <summary>Error Coral #FF5A5F - Fault, OUT, disconnected, errors</summary>
        public static readonly Color Error = new Color(1.0f, 0.3529f, 0.3725f, 1f);
        /// <summary>Warning Amber #FF9F1C - Low battery, weak connection</summary>
        public static readonly Color Warning = new Color(1.0f, 0.6235f, 0.1098f, 1f);
        /// <summary>Neutral 900 #0A1230 - Darkest neutral (blue-tinted)</summary>
        public static readonly Color N900 = new Color(0.0392f, 0.0706f, 0.1882f, 1f);
        /// <summary>Neutral 700 #2A3558 - Disabled fill on dark</summary>
        public static readonly Color N700 = new Color(0.1647f, 0.2078f, 0.3451f, 1f);
        /// <summary>Neutral 500 #6B7A9E - Secondary text on dark, dividers</summary>
        public static readonly Color N500 = new Color(0.4196f, 0.4784f, 0.6196f, 1f);
        /// <summary>Neutral 300 #B7C2DC - Muted text on blue, Common rarity</summary>
        public static readonly Color N300 = new Color(0.7176f, 0.7608f, 0.8627f, 1f);
        /// <summary>Neutral 100 #E8EEF9 - Light panels (rare), on-light background</summary>
        public static readonly Color N100 = new Color(0.9098f, 0.9333f, 0.9765f, 1f);
        /// <summary>Common #B7C2DC - Rarity tier 1</summary>
        public static readonly Color RarityCommon = new Color(0.7176f, 0.7608f, 0.8627f, 1f);
        /// <summary>Rare #3FA9FF - Rarity tier 2</summary>
        public static readonly Color RarityRare = new Color(0.2471f, 0.6627f, 1.0f, 1f);
        /// <summary>Epic #9B5CFF - Rarity tier 3</summary>
        public static readonly Color RarityEpic = new Color(0.6078f, 0.3608f, 1.0f, 1f);
        /// <summary>Legendary #F5C542 - Rarity tier 4 (= Headline Gold)</summary>
        public static readonly Color RarityLegendary = new Color(0.9608f, 0.7725f, 0.2588f, 1f);

        /// <summary>Drop-shadow color with brand alpha (0.43).</summary>
        public static readonly Color Shadow = new Color(0f, 0.0392f, 0.1961f, 0.43f);
        /// <summary>TMP underlay color for headlines (alpha 0.55).</summary>
        public static readonly Color TextUnderlay = new Color(0f, 0.0314f, 0.1765f, 0.55f);

        public enum Rarity { Common, Rare, Epic, Legendary }
        public static Color ForRarity(Rarity r)
        {
            switch (r)
            {
                case Rarity.Rare: return RarityRare;
                case Rarity.Epic: return RarityEpic;
                case Rarity.Legendary: return RarityLegendary;
                default: return RarityCommon;
            }
        }

        /// <summary>Background gradient: navyDeep at top -> royal at 24% of height, then flat (smoothstep).</summary>
        public static Gradient Background()
        {
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(NavyDeep, 0f), new GradientColorKey(Royal, 0.24f), new GradientColorKey(Royal, 1f) },
                new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(1f, 1f) });
            return g;
        }

        /// <summary>Hex helper for runtime-loaded skins, e.g. FromHex("#F5C542").</summary>
        public static Color FromHex(string hex) { Color c; return ColorUtility.TryParseHtmlString(hex, out c) ? c : Color.magenta; }
    }

    public static class BrandType
    {
        // Sizes at CanvasScaler reference 1920x1080. Create TMP SDF assets for each weight.
        public const float Display = 132f;   // Kanit ExtraBold Italic, UPPER - PERFECT!
        public const float Title = 84f;      // Kanit ExtraBold Italic - two-line headline
        public const float Heading = 52f;    // Kanit Bold Italic
        public const float Button = 40f;     // Kanit ExtraBold Italic, UPPER, +2 spacing
        public const float HudNumber = 72f;  // Kanit ExtraBold (upright)
        public const float HudLabel = 24f;   // Kanit SemiBold, UPPER, +6 spacing
        public const float Subline = 40f;    // Kanit Medium Italic
        public const float Body = 30f;       // Kanit Medium
        public const float Caption = 24f;    // Kanit Medium - never smaller on TV
    }

    public static class BrandMotion
    {
        public const float Fast = 0.12f, Base = 0.22f, Slow = 0.36f, Banner = 0.45f;
        public const float PressScale = 0.94f;
        // Ease-out cubic-bezier(0.22,1,0.36,1); overshoot cubic-bezier(0.34,1.56,0.64,1).
        public static float EaseOut(float t) => 1f - Mathf.Pow(1f - Mathf.Clamp01(t), 4f);
        public static float Overshoot(float t) { t = Mathf.Clamp01(t) - 1f; const float c1 = 1.70158f, c3 = c1 + 1f; return 1f + c3 * t * t * t + c1 * t * t; }
    }
}
