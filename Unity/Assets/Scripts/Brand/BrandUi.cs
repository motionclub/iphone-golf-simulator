using System.Collections.Generic;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.UI;

namespace MotionSports.Brand
{
    /// Code-built uGUI pieces in the MotionSports brand (Brand Guide v1.0 §4–§8), at the 1920×1080 reference: Kanit text, the gold
    /// primary pill with its Gold Deep lip, the Deep Navy secondary with a white border, navy panels with a white border and a Shadow
    /// Ink drop shadow, the two-line white + gold headline and the wordmark. Legacy Text (no TextMeshPro in this project yet).
    public static class BrandUi
    {
        // ---- Kanit (Resources/Fonts/Kanit, OFL)
        static readonly Dictionary<string, Font> fonts = new Dictionary<string, Font>();
        static Font Face(string weight)
        {
            if (fonts.TryGetValue(weight, out var f) && f) return f;
            f = Resources.Load<Font>("Fonts/Kanit/Kanit-" + weight);
            if (!f) { Debug.LogWarning("[Brand] Kanit-" + weight + " missing: the built-in font stands in"); f = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); }
            fonts[weight] = f; return f;
        }
        /// Headlines, buttons, banners, the wordmark.
        public static Font ExtraBoldItalic => Face("ExtraBoldItalic");
        /// Panel titles, mode names.
        public static Font BoldItalic => Face("BoldItalic");
        public static Font MediumItalic => Face("MediumItalic");
        /// HUD numbers (upright).
        public static Font ExtraBold => Face("ExtraBold");
        /// HUD labels.
        public static Font SemiBold => Face("SemiBold");
        /// Body, captions.
        public static Font Medium => Face("Medium");
        public static IEnumerable<Font> All { get { yield return ExtraBoldItalic; yield return BoldItalic; yield return MediumItalic; yield return ExtraBold; yield return SemiBold; yield return Medium; } }

        // ---- sprites, drawn once
        const int R = 80;
        static Sprite rounded, ring, soft, glow, gear, plus, chevron;
        /// A big-radius rounded rectangle, 9-sliced; `Round` sets the corner radius in canvas units.
        public static Sprite Rounded => rounded ? rounded : (rounded = MakeRounded(192, R, 0, 0));
        /// The same as an outline (a focus ring).
        public static Sprite Ring => ring ? ring : (ring = MakeRounded(192, R, 10, 0));
        /// A blurred rounded rectangle for the brand drop shadow (blur 28 at the 32 px radius).
        public static Sprite Soft => soft ? soft : (soft = MakeRounded(256, 112, 0, 40));
        /// A round soft glow (the hero spotlight, the swing arc's sparkle halo).
        public static Sprite Glow => glow ? glow : (glow = MakeGlow(128));
        public static Sprite Gear => gear ? gear : (gear = MakeGlyph(128, Gear01));
        public static Sprite Plus => plus ? plus : (plus = MakeGlyph(128, Plus01));
        public static Sprite Chevron => chevron ? chevron : (chevron = MakeGlyph(128, Chevron01));

        static Sprite MakeRounded(int n, int r, float band, float blur)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp, name = "Brand rounded" };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float cx = Mathf.Clamp(x + .5f, r, n - r), cy = Mathf.Clamp(y + .5f, r, n - r);
                    float d = Mathf.Sqrt((x + .5f - cx) * (x + .5f - cx) + (y + .5f - cy) * (y + .5f - cy)) - r;
                    float a;
                    if (blur > 0) { float k = Mathf.Clamp01(.5f - d / blur); a = k * k * (3 - 2 * k); }
                    else { a = Mathf.Clamp01(.5f - d); if (band > 0) a *= Mathf.Clamp01(d + band + .5f); }
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * a));
                }
            tex.SetPixels32(px); tex.Apply(false, true);
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(r, r, r, r));
        }
        static Sprite MakeGlow(int n)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp, name = "Brand glow" };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float dx = (x + .5f) / n * 2 - 1, dy = (y + .5f) / n * 2 - 1;
                    float a = Mathf.Clamp01(1 - Mathf.Sqrt(dx * dx + dy * dy));
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * Mathf.Pow(a, 1.6f)));
                }
            tex.SetPixels32(px); tex.Apply(false, true);
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f));
        }
        // solid rounded glyphs (Brand Guide §8 iconography): coverage from a signed distance in 0..1 space, 4x supersampled
        static Sprite MakeGlyph(int n, System.Func<Vector2, float> sdf)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp, name = "Brand glyph" };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float a = 0;
                    for (int s = 0; s < 4; s++)
                    {
                        var p = new Vector2((x + .25f + .5f * (s & 1)) / n, (y + .25f + .5f * (s >> 1)) / n);
                        a += sdf(p) <= 0 ? .25f : 0;
                    }
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * a));
                }
            tex.SetPixels32(px); tex.Apply(false, true);
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f));
        }
        static float Gear01(Vector2 p)
        {
            var c = p - new Vector2(.5f, .5f); float r = c.magnitude, a = Mathf.Atan2(c.y, c.x);
            float teeth = Mathf.Cos(a * 8) > .35f ? .44f : .35f;
            return Mathf.Max(r - teeth, .14f - r);
        }
        static float Plus01(Vector2 p)
        {
            var c = new Vector2(Mathf.Abs(p.x - .5f), Mathf.Abs(p.y - .5f));
            float bar(Vector2 q, Vector2 h) { var d = new Vector2(Mathf.Max(q.x - h.x, 0), Mathf.Max(q.y - h.y, 0)); return d.magnitude - .05f; }
            return Mathf.Min(bar(c, new Vector2(.34f, .03f)), bar(c, new Vector2(.03f, .34f)));
        }
        static float Chevron01(Vector2 p)
        {
            float Seg(Vector2 q, Vector2 a, Vector2 b) { var pa = q - a; var ba = b - a; float h = Mathf.Clamp01(Vector2.Dot(pa, ba) / ba.sqrMagnitude); return (pa - ba * h).magnitude - .075f; }
            return Mathf.Min(Seg(p, new Vector2(.62f, .18f), new Vector2(.32f, .5f)), Seg(p, new Vector2(.32f, .5f), new Vector2(.62f, .82f)));
        }

        // ---- layout helpers (positions are the mock's: x right, y down from the top-left of the 1920×1080 screen)
        public static RectTransform Box(Transform parent, string name, float x, float y, float w, float h)
        {
            var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
            rt.SetParent(parent, false);
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = new Vector2(x, -y); rt.sizeDelta = new Vector2(w, h);
            return rt;
        }
        public static RectTransform Fill(Transform parent, string name)
        {
            var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
            rt.SetParent(parent, false); rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
            return rt;
        }
        /// A child image filling its parent, inset by `inset` canvas units.
        public static Image Layer(Transform parent, string name, Color color, float inset = 0, float radius = -1, Sprite sprite = null)
        {
            var img = Fill(parent, name).gameObject.AddComponent<Image>();
            ((RectTransform)img.transform).offsetMin = new Vector2(inset, inset); ((RectTransform)img.transform).offsetMax = new Vector2(-inset, -inset);
            img.color = color; img.raycastTarget = false;
            if (sprite) img.sprite = sprite;
            if (radius >= 0) Round(img, radius);
            return img;
        }
        public static Image Round(Image img, float radius)
        {
            if (!img.sprite || img.sprite == Rounded || img.sprite == Ring) { if (!img.sprite) img.sprite = Rounded; }
            img.type = Image.Type.Sliced; img.pixelsPerUnitMultiplier = R / Mathf.Max(1f, radius);
            return img;
        }
        /// The brand drop shadow under a box: Shadow Ink at 43 %, blur 28, offset y +22.
        public static Image DropShadow(RectTransform box, float radius)
        {
            var img = new GameObject("Shadow", typeof(RectTransform)).AddComponent<Image>();
            var rt = img.rectTransform; rt.SetParent(box, false); rt.SetAsFirstSibling();
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = new Vector2(-28, -28 - 22); rt.offsetMax = new Vector2(28, 28 - 22);
            img.sprite = Soft; img.type = Image.Type.Sliced; img.pixelsPerUnitMultiplier = 112f / Mathf.Max(1f, radius + 28);
            img.color = BrandColors.Shadow; img.raycastTarget = false;
            return img;
        }
        public static Text Label(Transform parent, string name, string text, Font font, float size, Color color, TextAnchor align = TextAnchor.MiddleLeft)
        {
            var t = Fill(parent, name).gameObject.AddComponent<Text>();
            t.font = font; t.fontSize = Mathf.RoundToInt(size); t.color = color; t.alignment = align; t.text = text;
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow; t.raycastTarget = false;
            t.supportRichText = true; t.lineSpacing = 1f;
            return t;
        }
        /// Text Shadow #00082D at 55 %, offset size/40 (the brand underlay; legacy Text has no blur).
        public static Text Underlay(Text t)
        {
            var s = t.gameObject.AddComponent<Shadow>();
            s.effectColor = BrandColors.TextUnderlay; s.effectDistance = new Vector2(0, -Mathf.Max(1.5f, t.fontSize / 40f) - 1);
            return t;
        }

        /// The wordmark: "Motion" white + "Sports" Wordmark Gold, Kanit ExtraBold Italic, with its shadow (required over a 3D scene).
        public static Text Wordmark(Transform parent, float x, float y, float size = 64)
        {
            var box = Box(parent, "Wordmark", x, y, size * 7f, size * 1.25f);
            var t = Label(box, "Text", "Motion<color=#F1B120>Sports</color>", ExtraBoldItalic, size, BrandColors.White);
            return Underlay(t);
        }

        /// The two-line headline: line 1 white, line 2 Headline Gold (Title style, 84 px, Kanit ExtraBold Italic).
        public static RectTransform Headline(Transform parent, float x, float y, string line1, string line2, float width = 1000, TextAnchor align = TextAnchor.UpperLeft)
        {
            var box = Box(parent, "Headline", x, y, width, 210);
            var a = Underlay(Label(box, "Line 1", line1, ExtraBoldItalic, BrandType.Title, BrandColors.White, align));
            var b = Underlay(Label(box, "Line 2", line2, ExtraBoldItalic, BrandType.Title, BrandColors.Gold, align));
            a.rectTransform.offsetMax = new Vector2(0, 0); a.rectTransform.offsetMin = new Vector2(0, 105);
            b.rectTransform.offsetMax = new Vector2(0, -102); b.rectTransform.offsetMin = new Vector2(0, 0);
            return box;
        }

        public enum Style { Primary, Secondary, Row, RowPrimary, RowDisabled, Card, Tab, Disabled }

        /// A button face for `style` filling `box` (the hit area): returns the face (what scales on press) and its label.
        public static (RectTransform face, Text label, Text sub) Button(RectTransform box, Style style, string label, string sub = null, float radius = -1)
        {
            float h = box.sizeDelta.y; if (radius < 0) radius = h / 2;
            var face = Fill(box, "Face");
            bool gold = style == Style.Primary || style == Style.RowPrimary;
            if (style != Style.Tab) DropShadow(face, radius);
            if (gold)
            {
                // gold -> wordmark gold, with a 6 px Gold Deep lip along the bottom
                Layer(face, "Lip", BrandColors.GoldDeep, 0, radius);
                var top = Layer(face, "Gold", BrandColors.White, 0, radius);
                top.rectTransform.offsetMin = new Vector2(0, 6);
                UiGradient.On(top, BrandColors.Gold, BrandColors.GoldWordmark);
            }
            else if (style == Style.Disabled || style == Style.RowDisabled) Layer(face, "Fill", BrandColors.N700, 0, radius);
            else if (style == Style.Tab) { }
            else
            {
                Layer(face, "Border", BrandColors.White, 0, radius);
                Layer(face, "Fill", BrandColors.NavyDeep, 5, Mathf.Max(0, radius - 5));
            }
            bool off = style == Style.Disabled || style == Style.RowDisabled;
            var ink = gold ? BrandColors.NavyInk : off ? BrandColors.N500 : BrandColors.White;
            bool row = style == Style.Row || style == Style.RowPrimary || style == Style.RowDisabled;
            var text = Label(face, "Label", label, ExtraBoldItalic, row ? 36 : style == Style.Tab ? 30 : BrandType.Button, ink, row ? TextAnchor.MiddleLeft : TextAnchor.MiddleCenter);
            Text subText = null;
            if (row)
            {
                text.rectTransform.offsetMin = new Vector2(34, string.IsNullOrEmpty(sub) ? 0 : 30); text.rectTransform.offsetMax = new Vector2(-30, string.IsNullOrEmpty(sub) ? 0 : -6);
                if (!string.IsNullOrEmpty(sub))
                {
                    subText = Label(face, "Sub", sub, Medium, BrandType.Caption, gold ? BrandColors.NavyDeep : BrandColors.N300, TextAnchor.MiddleLeft);
                    subText.rectTransform.offsetMin = new Vector2(34, 8); subText.rectTransform.offsetMax = new Vector2(-30, -50);
                }
            }
            else if (gold) text.rectTransform.offsetMin = new Vector2(0, 6);
            return (face, text, subText);
        }

        /// A navy panel: Deep Navy at 94 %, a 5 px white border, radius 32, the brand drop shadow.
        public static RectTransform Panel(Transform parent, string name, float x, float y, float w, float h, float radius = 32)
        {
            var box = Box(parent, name, x, y, w, h);
            DropShadow(box, radius);
            Layer(box, "Border", BrandColors.White, 0, radius);
            Layer(box, "Fill", new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, .94f), 5, radius - 5);
            return box;
        }

        /// Every glyph the menu uses at every size it uses, rasterised now (a first look at a screen must not pay for it).
        public static void Prewarm(IEnumerable<(Font font, int size, string text)> uses)
        {
            foreach (var (font, size, text) in uses) if (font && !string.IsNullOrEmpty(text)) font.RequestCharactersInTexture(text, size, FontStyle.Normal);
        }
    }
}
