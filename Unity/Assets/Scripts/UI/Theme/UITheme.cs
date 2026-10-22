using UnityEngine;

namespace GolfArcade.UI
{
    /// One sport's colours: a colour per ThemeRole, the 3-stop glass gradient, the stroke and the
    /// shadow. Layout and type are shared by every theme, so there is nothing else to set here.
    [CreateAssetMenu(menuName = "GolfArcade/UI Theme", fileName = "Theme_New")]
    public sealed class UITheme : ScriptableObject
    {
        [Header("Glass panel (top, middle, bottom; alpha is the panel opacity)")]
        public Color panelTop = Color.white, panelMid = Color.white, panelBottom = Color.white;
        public Color panelStroke = Color.white;
        public float strokeWidth = 2f;

        [Header("Text")]
        public Color panelText = Color.white;
        public Color panelTextMuted = new(1, 1, 1, 0.85f);
        /// Small labels never fade below this over the glass.
        [Range(0, 1)] public float minTextOpacity = 0.85f;

        [Header("Accents")]
        public Color accent = Color.white;
        public Color button = Color.white;
        public Color buttonText = Color.black;
        public Color rule = Color.white;
        /// The outline round the chunky type of the clear (no panel) style: the club card's blue.
        public Color textOutline = new(0x15 / 255f, 0x57 / 255f, 0xB8 / 255f, 1f);
        public Color dot = Color.white;

        [Header("Meter")]
        public Color meterRail = new(1, 1, 1, 0.13f);
        public Color meterFill = Color.white;
        public Color sweetSpot = Color.white;
        public Color pearl = Color.white;

        [Header("Shadow under panels")]
        public Color shadowColor = Color.black;
        [Range(0, 1)] public float shadowAlpha = 0.27f;
        public float shadowBlur = 32f;
        public Vector2 shadowOffset = new(0, 12);

        /// The colour a role has in this theme. `alpha` multiplies it; text roles never drop under
        /// `minTextOpacity`.
        public Color Get(ThemeRole role, float alpha = 1f)
        {
            Color c;
            switch (role)
            {
                case ThemeRole.Panel: c = panelMid; break;
                case ThemeRole.PanelStroke: c = panelStroke; break;
                case ThemeRole.PanelText: c = panelText; break;
                case ThemeRole.PanelTextMuted: c = panelTextMuted; break;
                case ThemeRole.Accent: c = accent; break;
                case ThemeRole.Button: c = button; break;
                case ThemeRole.ButtonText: c = buttonText; break;
                case ThemeRole.Rule: c = rule; break;
                case ThemeRole.MeterRail: c = meterRail; break;
                case ThemeRole.MeterFill: c = meterFill; break;
                case ThemeRole.SweetSpot: c = sweetSpot; break;
                case ThemeRole.Pearl: c = pearl; break;
                case ThemeRole.Dot: c = dot; break;
                default: c = new Color(shadowColor.r, shadowColor.g, shadowColor.b, shadowAlpha); break;
            }
            c.a *= alpha;
            if (role == ThemeRole.PanelText || role == ThemeRole.PanelTextMuted) c.a = Mathf.Max(c.a, minTextOpacity);
            return c;
        }

        static Color Hex(string hex, float alpha = 1f)
        {
            int v = System.Convert.ToInt32(hex, 16);
            return new Color(((v >> 16) & 255) / 255f, ((v >> 8) & 255) / 255f, (v & 255) / 255f, alpha);
        }

        /// Golf: Emerald & Gold (the J variant 4 of the mock-ups). Also what the theme asset is filled from.
        public static UITheme GolfEmeraldGold()
        {
            var t = CreateInstance<UITheme>();
            t.name = "Theme_Golf_EmeraldGold";
            t.panelTop = Hex("10936B", .95f); t.panelMid = Hex("0B7556", .95f); t.panelBottom = Hex("075B44", .96f);
            t.panelStroke = Hex("3FBF94"); t.strokeWidth = 2f;
            t.panelText = Hex("FFFFFF"); t.panelTextMuted = Hex("FFFFFF", .85f); t.minTextOpacity = .85f;
            t.accent = t.button = t.sweetSpot = t.meterFill = t.pearl = t.dot = Hex("F5C542");
            t.buttonText = Hex("063D2D"); t.rule = Hex("5FC7A3"); t.textOutline = Hex("1557B8");
            t.meterRail = new Color(1, 1, 1, .13f);
            t.shadowColor = Hex("02261B"); t.shadowAlpha = .27f; t.shadowBlur = 32f; t.shadowOffset = new Vector2(0, 12);
            return t;
        }

        /// Tennis: Royal Blue & Gold, a classic true blue.
        public static UITheme TennisRoyalBlue()
        {
            var t = CreateInstance<UITheme>();
            t.name = "Theme_Tennis_RoyalBlue";
            t.panelTop = Hex("3478EC", .95f); t.panelMid = Hex("1F62D6", .95f); t.panelBottom = Hex("1950BC", .96f);
            t.panelStroke = Hex("7DA6F6"); t.strokeWidth = 2f;
            t.panelText = Hex("FFFFFF"); t.panelTextMuted = Hex("FFFFFF", .86f); t.minTextOpacity = .86f;
            t.accent = t.button = t.sweetSpot = t.meterFill = t.pearl = t.dot = Hex("FFD166");
            t.buttonText = Hex("0D2C66"); t.rule = Hex("86AEF5"); t.textOutline = Hex("0D2C66");
            t.meterRail = new Color(1, 1, 1, .13f);
            t.shadowColor = Hex("071E4D"); t.shadowAlpha = .27f; t.shadowBlur = 32f; t.shadowOffset = new Vector2(0, 12);
            return t;
        }
    }
}
