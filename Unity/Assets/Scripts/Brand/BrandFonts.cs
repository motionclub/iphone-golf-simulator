using UnityEngine;

namespace MotionSports.Brand
{
    /// The brand's Kanit weights (brand guide §5), as dynamic fonts for the uGUI Text the game
    /// uses. Expected at Resources/Fonts/Kanit/Kanit-<Weight>.ttf from the brand kit (OFL 1.1).
    /// When a weight is missing, `Missing` names it and the caller's fallback font is used;
    /// the guide asks us to say what is missing rather than quietly substitute.
    public static class BrandFonts
    {
        static Font extraBoldItalic, boldItalic, mediumItalic, extraBold, semiBold, medium;
        static bool warned;

        static Font Load(ref Font cache, string weight, Font fallback)
        {
            if (!cache) cache = Resources.Load<Font>("Fonts/Kanit/Kanit-" + weight);
            if (cache) return cache;
            if (!warned) { warned = true; Debug.LogWarning("[Brand] Kanit fonts are missing (Resources/Fonts/Kanit/Kanit-*.ttf from the brand kit); using stand-in fonts."); }
            return fallback;
        }

        public static bool Missing => !Resources.Load<Font>("Fonts/Kanit/Kanit-ExtraBoldItalic");

        /// Display, Title, Button: banners, headlines, buttons (italic).
        public static Font ExtraBoldItalic(Font fallback) => Load(ref extraBoldItalic, "ExtraBoldItalic", fallback);
        /// Heading (italic).
        public static Font BoldItalic(Font fallback) => Load(ref boldItalic, "BoldItalic", fallback);
        /// Subline (italic).
        public static Font MediumItalic(Font fallback) => Load(ref mediumItalic, "MediumItalic", fallback);
        /// HUD numbers (upright).
        public static Font ExtraBold(Font fallback) => Load(ref extraBold, "ExtraBold", fallback);
        /// HUD labels (upright).
        public static Font SemiBold(Font fallback) => Load(ref semiBold, "SemiBold", fallback);
        /// Body, captions.
        public static Font Medium(Font fallback) => Load(ref medium, "Medium", fallback);
    }
}
