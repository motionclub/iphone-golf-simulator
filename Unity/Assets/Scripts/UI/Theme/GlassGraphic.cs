using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// A rounded-rectangle glass panel as one procedural Graphic: a signed-distance box with a
    /// radius, an inside stroke and a three-stop vertical gradient (Resources/UI/Glass/UIGlass).
    /// By default it wears the active theme's panel; `SetFlat` gives a plain fill instead (club
    /// tiles, chips). Radius is in canvas units: 24 at the 1920x1080 reference.
    [RequireComponent(typeof(CanvasRenderer))]
    public sealed class GlassGraphic : MaskableGraphic
    {
        public float radius = 24f;
        bool flat; Color flatFill, flatStroke; float flatStrokeWidth;
        System.Func<UITheme, (Color fill, Color stroke, float width)> flatFromTheme;
        Material instance;
        static Shader shader;
        static readonly int Top = Shader.PropertyToID("_Top"), Mid = Shader.PropertyToID("_Mid"), Bottom = Shader.PropertyToID("_Bottom"),
            StrokeColor = Shader.PropertyToID("_Stroke"), Size = Shader.PropertyToID("_Size"), Radius = Shader.PropertyToID("_Radius"),
            StrokeWidth = Shader.PropertyToID("_StrokeWidth");

        /// A glass panel in `parent`, stretched over it or placed by the caller.
        public static GlassGraphic Create(Transform parent, string name, float radius = 24f)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer));
            go.transform.SetParent(parent, false);
            var g = go.AddComponent<GlassGraphic>();
            g.radius = radius; g.raycastTarget = false;
            return g;
        }

        /// A flat fill and stroke (re-read from the theme on every change when `fromTheme` is given).
        public void SetFlat(Color fill, Color stroke, float strokeWidth, System.Func<UITheme, (Color, Color, float)> fromTheme = null)
        {
            flat = true; flatFill = fill; flatStroke = stroke; flatStrokeWidth = strokeWidth; flatFromTheme = fromTheme;
            if (fromTheme != null) { var v = fromTheme(ThemeService.Current); flatFill = v.Item1; flatStroke = v.Item2; flatStrokeWidth = v.Item3; }
            SetAllDirty();
        }

        protected override void OnEnable()
        {
            base.OnEnable();
            ThemeService.Changed += OnThemeChanged;
            if (!material || material == defaultMaterial) Bind();
        }
        protected override void OnDisable() { ThemeService.Changed -= OnThemeChanged; base.OnDisable(); }
        protected override void OnDestroy()
        {
            base.OnDestroy();
            if (instance) { if (Application.isPlaying) Destroy(instance); else DestroyImmediate(instance); }
        }

        void OnThemeChanged(UITheme _)
        {
            if (flatFromTheme != null) { var v = flatFromTheme(ThemeService.Current); flatFill = v.Item1; flatStroke = v.Item2; flatStrokeWidth = v.Item3; }
            SetAllDirty();
        }

        void Bind()
        {
            shader ??= Resources.Load<Shader>("UI/Glass/UIGlass");
            if (!shader) return;
            instance = new Material(shader) { name = "UIGlass (instance)", hideFlags = HideFlags.HideAndDontSave };
            material = instance;
        }

        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            var r = GetPixelAdjustedRect();
            if (r.width <= 0 || r.height <= 0) return;
            Push();
            var c = (Color32)color;
            vh.AddVert(new Vector3(r.xMin, r.yMin), c, new Vector2(0, 0));
            vh.AddVert(new Vector3(r.xMin, r.yMax), c, new Vector2(0, 1));
            vh.AddVert(new Vector3(r.xMax, r.yMax), c, new Vector2(1, 1));
            vh.AddVert(new Vector3(r.xMax, r.yMin), c, new Vector2(1, 0));
            vh.AddTriangle(0, 1, 2); vh.AddTriangle(2, 3, 0);
        }

        // The material's numbers: the rect (for the distance field) and the colours.
        void Push()
        {
            if (!instance) return;
            var t = ThemeService.Current;
            var rect = rectTransform.rect;
            instance.SetVector(Size, new Vector4(rect.width, rect.height, 0, 0));
            instance.SetFloat(Radius, radius);
            if (flat)
            {
                instance.SetColor(Top, flatFill); instance.SetColor(Mid, flatFill); instance.SetColor(Bottom, flatFill);
                instance.SetColor(StrokeColor, flatStroke); instance.SetFloat(StrokeWidth, flatStrokeWidth);
            }
            else
            {
                instance.SetColor(Top, t.panelTop); instance.SetColor(Mid, t.panelMid); instance.SetColor(Bottom, t.panelBottom);
                instance.SetColor(StrokeColor, t.panelStroke); instance.SetFloat(StrokeWidth, t.strokeWidth);
            }
        }

#if UNITY_EDITOR
        protected override void OnValidate() { base.OnValidate(); SetAllDirty(); }
#endif
    }
}
