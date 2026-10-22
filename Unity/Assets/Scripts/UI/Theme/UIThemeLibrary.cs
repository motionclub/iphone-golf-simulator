using System;
using UnityEngine;

namespace GolfArcade.UI
{
    /// The themes the game ships: a default and one per sport. Themes follow the sport only, never
    /// the course or the venue. Lives in Resources/UI/Themes/UIThemeLibrary.asset.
    [CreateAssetMenu(menuName = "GolfArcade/UI Theme Library", fileName = "UIThemeLibrary")]
    public sealed class UIThemeLibrary : ScriptableObject
    {
        [Serializable] public struct SportTheme { public string sport; public UITheme theme; }

        public UITheme defaultTheme;
        public SportTheme[] sportThemes = Array.Empty<SportTheme>();

        /// The sport's theme ("golf", "tennis"), or the default for anything else.
        public UITheme Get(string sport)
        {
            if (!string.IsNullOrEmpty(sport))
                foreach (var s in sportThemes)
                    if (s.theme && string.Equals(s.sport, sport, StringComparison.OrdinalIgnoreCase)) return s.theme;
            return defaultTheme;
        }

        /// The same two themes built in memory, for when the asset is missing from a build.
        public static UIThemeLibrary BuildFallback()
        {
            var lib = CreateInstance<UIThemeLibrary>();
            lib.name = "UIThemeLibrary (built-in)";
            lib.hideFlags = HideFlags.DontSave;
            var golf = UITheme.GolfEmeraldGold(); golf.hideFlags = HideFlags.DontSave;
            var tennis = UITheme.TennisRoyalBlue(); tennis.hideFlags = HideFlags.DontSave;
            lib.defaultTheme = golf;
            lib.sportThemes = new[] { new SportTheme { sport = "golf", theme = golf }, new SportTheme { sport = "tennis", theme = tennis } };
            return lib;
        }
    }
}
