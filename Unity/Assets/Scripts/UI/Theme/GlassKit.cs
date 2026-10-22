using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// The glass look's builders: a themed panel (soft shadow + glass + room for content), themed
    /// labels in Inter, capsules and dots. Sizes are canvas units at the 1920x1080 reference.
    public static class GlassKit
    {
        public const float DefaultRadius = 24f;
        /// The clear style: no panels, no borders; the club card's chunky type (white with a blue outline and a drop)
        /// straight on the picture. False gives the glass panels.
        public static bool ClearStyle = true;
        const float ShadowReach = 48f;

        // ---- Sprites, drawn once.
        static Sprite roundRect, shadow;

        /// A 9-sliced rounded rectangle: radius 32 on a 64 px sprite. Use `Round` to set a radius.
        public static Sprite RoundRect => roundRect ??= MakeRoundRect();
        static Sprite MakeRoundRect()
        {
            const int n = 64, r = 32;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp, name = "Glass round rect" };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float cx = Mathf.Clamp(x + .5f, r, n - r), cy = Mathf.Clamp(y + .5f, r, n - r);
                    float d = Mathf.Sqrt((x + .5f - cx) * (x + .5f - cx) + (y + .5f - cy) * (y + .5f - cy)) - r;
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * Mathf.Clamp01(.5f - d)));
                }
            tex.SetPixels32(px); tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(r, r, r, r));
        }

        /// A soft rounded shadow, 9-sliced: a 24-radius box inset 48 px, blurred (sigma about 14 px).
        public static Sprite ShadowSprite => shadow ??= MakeShadow();
        static Sprite MakeShadow()
        {
            const int n = 128, inset = 48; const float r = 24, sigma = 14;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp, name = "Glass shadow" };
            var px = new Color32[n * n];
            float lo = inset, hi = n - inset;
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float cx = Mathf.Clamp(x + .5f, lo + r, hi - r), cy = Mathf.Clamp(y + .5f, lo + r, hi - r);
                    float d = Mathf.Sqrt((x + .5f - cx) * (x + .5f - cx) + (y + .5f - cy) * (y + .5f - cy)) - r;
                    float a = 1f / (1f + Mathf.Exp(1.702f * d / sigma));   // a Gaussian edge
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * a));
                }
            tex.SetPixels32(px); tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(64, 64, 64, 64));
        }

        /// Gives `img` the rounded-rect sprite at `radius`.
        public static Image Round(Image img, float radius)
        {
            img.sprite = RoundRect; img.type = Image.Type.Sliced; img.pixelsPerUnitMultiplier = 32f / Mathf.Max(1f, radius);
            return img;
        }

        // ---- Fonts: Inter, for the glass look (Resources/Fonts/Inter).
        public static Font Regular => regular ??= Face("Regular");
        public static Font Medium => medium ??= Face("Medium");
        public static Font SemiBold => semiBold ??= Face("SemiBold");
        public static Font Bold => bold ??= Face("Bold");
        static Font regular, medium, semiBold, bold;
        static Font Face(string weight) => Resources.Load<Font>("Fonts/Inter/Inter-" + weight) ?? UiKit.Strong;

        // ---- Builders.

        /// A glass panel: a soft shadow under a glass body. The returned root has the panel's size and sits
        /// at `pos` from `anchor` (its pivot is the anchor, like GolfShotHud.Panel); put content in it.
        public static RectTransform Panel(Transform parent, string name, Vector2 anchor, Vector2 pos, Vector2 size, float radius = DefaultRadius, bool shadow = true)
        {
            var root = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
            root.SetParent(parent, false);
            root.anchorMin = root.anchorMax = root.pivot = anchor;
            root.anchoredPosition = pos; root.sizeDelta = size;
            if (ClearStyle) return root;   // (a place for content, nothing drawn)
            if (shadow) AddShadow(root, radius);
            var glass = GlassGraphic.Create(root, "Glass", radius);
            Stretch(glass.rectTransform);
            return root;
        }

        /// A soft shadow around a panel root (theme's colour, blur and offset).
        public static Image AddShadow(RectTransform root, float radius)
        {
            var go = new GameObject("Shadow", typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
            go.transform.SetParent(root, false);
            var img = go.GetComponent<Image>();
            img.sprite = ShadowSprite; img.type = Image.Type.Sliced; img.pixelsPerUnitMultiplier = 1f; img.raycastTarget = false;
            var rt = img.rectTransform; Stretch(rt);
            var off = ThemeService.Current.shadowOffset;
            rt.offsetMin = new Vector2(-ShadowReach + off.x, -ShadowReach - off.y);
            rt.offsetMax = new Vector2(ShadowReach + off.x, ShadowReach - off.y);
            ThemedGraphic.Bind(go, ThemeRole.Shadow);
            return img;
        }

        public static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        /// A themed label in Inter: `role` picks the colour (PanelText, PanelTextMuted, ButtonText ...). A drop shadow
        /// is added only when asked, for type straight on the picture.
        public static Text Label(Transform parent, string name, int size, Font face, ThemeRole role, TextAnchor anchor, Vector2 pos, Vector2 box, float alpha = 1f)
        {
            // pos is the top-left of `box` from the parent's top-left, like the mock-ups' layers
            var t = UiKit.Label(parent, name, size, anchor, new Vector2(0, 1), new Vector2(0, 1), new Vector2(pos.x, -pos.y), box, ClearStyle ? UiKit.Display : face, false);
            t.rectTransform.pivot = new Vector2(0, 1);
            t.raycastTarget = false; t.supportRichText = true;
            ThemedGraphic.Bind(t.gameObject, role, alpha);
            if (ClearStyle) Outline(t);
            return t;
        }

        /// The club card's lettering on `t`: a heavy outline in the theme's colour and a drop under it, sized with the type.
        public static Text Outline(Text t)
        {
            float w = Mathf.Clamp(t.fontSize * .075f, 1.6f, 4f);
            var c = ThemeService.Current.textOutline;
            foreach (var d in new[] { new Vector2(w, -w), new Vector2(-w, w) })
            { var o = t.gameObject.AddComponent<UnityEngine.UI.Outline>(); o.effectColor = c; o.effectDistance = d; }
            var drop = t.gameObject.AddComponent<UnityEngine.UI.Shadow>(); drop.effectColor = new Color(c.r, c.g, c.b, .7f); drop.effectDistance = new Vector2(0, -w * 2.2f);
            return t;
        }

        /// Makes a pill (UiKit.Pill) see-through: its rim, shadow and fill, so only what is drawn on it remains (the clear style).
        public static void Hide(RectTransform pill)
        {
            foreach (var img in pill.GetComponentsInChildren<Image>(true)) { var c = img.color; c.a = 0; img.color = c; }
        }

        /// The lettering colour of the clear style: the theme's outline, or the arcade ink when the glass is in use.
        public static Color Ink => ClearStyle ? ThemeService.Current.textOutline : UiKit.ArcadeInk;
        public static Color Gold => ThemeService.Current.accent;

        /// A rounded, themed fill (a rail, a tile, a sweet-spot block).
        public static Image Capsule(Transform parent, string name, ThemeRole role, Vector2 pos, Vector2 size, float radius, float alpha = 1f)
        {
            var img = UiKit.Panel(parent, name, Color.white, new Vector2(0, 1), new Vector2(0, 1), new Vector2(pos.x, -pos.y), size, false);
            img.rectTransform.pivot = new Vector2(0, 1);
            Round(img, radius); img.raycastTarget = false;
            ThemedGraphic.Bind(img.gameObject, role, alpha);
            return img;
        }

        /// A round dot (the circle sprite).
        public static Image Dot(Transform parent, string name, Color color, Vector2 center, float size)
        {
            var img = UiKit.Panel(parent, name, color, new Vector2(0, 1), new Vector2(0, 1), new Vector2(center.x, -center.y), new Vector2(size, size), false);
            img.sprite = UiKit.Circle; img.type = Image.Type.Simple; img.raycastTarget = false;
            img.rectTransform.pivot = new Vector2(.5f, .5f);
            return img;
        }
    }
}
