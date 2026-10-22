using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// Recolors the Graphic next to it (an Image, a Text, a TMP_Text: all are Graphics) from the
    /// active theme's colour for `role`, when it is enabled and whenever the theme changes.
    [ExecuteAlways, DisallowMultipleComponent]
    public sealed class ThemedGraphic : MonoBehaviour
    {
        public ThemeRole role;
        [Range(0, 1)] public float alpha = 1f;
        Graphic graphic;

        /// Adds (or retunes) the component on `target`.
        public static ThemedGraphic Bind(GameObject target, ThemeRole role, float alpha = 1f)
        {
            var t = target.GetComponent<ThemedGraphic>() ?? target.AddComponent<ThemedGraphic>();
            t.role = role; t.alpha = alpha;
            t.Refresh();
            return t;
        }

        void OnEnable() { ThemeService.Changed += OnChanged; Refresh(); }
        void OnDisable() => ThemeService.Changed -= OnChanged;
        void OnChanged(UITheme _) => Refresh();
#if UNITY_EDITOR
        void OnValidate() => Refresh();
#endif

        public void Refresh()
        {
            if (!graphic) graphic = GetComponent<Graphic>();
            if (graphic) graphic.color = ThemeService.Current.Get(role, alpha);
        }
    }
}
