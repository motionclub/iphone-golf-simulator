using System;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GolfArcade.UI
{
    /// The active UI theme. Golf.unity uses "golf", Tennis.unity "tennis", and the hub and menus
    /// the default (golf). It follows scene loads by itself; the course or venue never matters.
    public static class ThemeService
    {
        const string LibraryPath = "UI/Themes/UIThemeLibrary";
        static UIThemeLibrary library;
        static UITheme current;

        /// The sport the active theme was picked for (null: the default).
        public static string Sport { get; private set; }

        public static UITheme Current => current ? current : current = Library.defaultTheme;

        /// Fired after the active theme was (re)picked; ThemedGraphic and GlassGraphic recolor on it.
        public static event Action<UITheme> Changed;

        static UIThemeLibrary Library => library ? library : library = Resources.Load<UIThemeLibrary>(LibraryPath) ?? UIThemeLibrary.BuildFallback();

        /// Picks `sport`'s theme (unknown or null: the default) and tells everything listening.
        public static UITheme Apply(string sport)
        {
            var theme = Library.Get(sport);
            if (!theme) theme = Library.defaultTheme;
            current = theme; Sport = string.IsNullOrEmpty(sport) ? null : sport.ToLowerInvariant();
            Debug.Log($"[Theme] {(Sport ?? "default")} -> {theme.name}");
            Changed?.Invoke(theme);
            return theme;
        }

        /// The sport a scene belongs to: Golf -> "golf", Tennis -> "tennis", the hub and anything else -> null.
        public static string SportOf(string sceneName) => sceneName switch { "Golf" => "golf", "Tennis" => "tennis", _ => null };

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Hook()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        static void OnSceneLoaded(Scene scene, LoadSceneMode mode) => Apply(SportOf(scene.name));
    }
}
