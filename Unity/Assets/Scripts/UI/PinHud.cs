using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// Where the pin is, on the course picture: a glass pill ("PIN 139 yd") standing over the pin on a thin
    /// white stem when it is in view; when it is out of frame — off to one side, or behind the camera — the
    /// pill waits at the edge of the screen nearest it with an arrow pointing the way. Placed by viewport, so it sits right on the phone and on the TV.
    public sealed class PinLocator : MonoBehaviour
    {
        RectTransform root, pill, arrow, stem;
        Image foot;
        Text caption, label;

        public static PinLocator Create(Transform canvasRoot)
        {
            var go = new GameObject("Pin locator", typeof(RectTransform));
            go.transform.SetParent(canvasRoot, false);
            var p = go.AddComponent<PinLocator>();
            p.root = (RectTransform)go.transform;
            p.root.sizeDelta = Vector2.zero;
            // the stem and its foot first, so the pill draws over them
            var stem = UiKit.Panel(p.root, "Pin stem", new Color(1, 1, 1, .9f), new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, 19), new Vector2(3, 20), false);
            stem.rectTransform.pivot = new Vector2(.5f, 1); stem.raycastTarget = false; p.stem = stem.rectTransform;
            p.foot = GlassKit.Dot(p.root, "Pin foot", new Color(1, 1, 1, .95f), Vector2.zero, 10);
            p.foot.rectTransform.anchorMin = p.foot.rectTransform.anchorMax = new Vector2(.5f, .5f); p.foot.rectTransform.anchoredPosition = Vector2.zero;
            p.pill = GlassKit.Panel(p.root, "Pill", new Vector2(.5f, .5f), Vector2.zero, new Vector2(180, 48), 24);
            Text Row(string name, int size, Font face, ThemeRole role)
            {
                var t = UiKit.Label(p.pill, name, size, TextAnchor.MiddleLeft, new Vector2(0, .5f), new Vector2(0, .5f), Vector2.zero, new Vector2(160, 48), face, false);
                t.rectTransform.pivot = new Vector2(0, .5f); t.raycastTarget = false; ThemedGraphic.Bind(t.gameObject, role);
                if (GlassKit.ClearStyle) { t.font = UiKit.Display; t.fontSize = size + 3; GlassKit.Outline(t); }
                return t;
            }
            p.caption = Row("Caption", 15, GlassKit.SemiBold, ThemeRole.PanelTextMuted);
            p.label = Row("Value", 24, GlassKit.Regular, ThemeRole.PanelText);
            var a = UiKit.Label(p.root, "Arrow", 32, TextAnchor.MiddleCenter, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(44, 44), UiKit.Display, true, ThemeRole.Accent);
            a.text = "▲"; a.raycastTarget = false;
            p.arrow = a.rectTransform;
            go.SetActive(false);
            return p;
        }

        /// `view` null hides it. `pin` is the top of the flag in the world.
        public void Set(Camera view, Vector3 pin, string text)
        {
            bool on = view && text != null;
            gameObject.SetActive(on);
            if (!on) return;
            transform.SetAsLastSibling();
            bool obscured = !GolfArcade.EnvironmentArt.DreamVisibility.Visible(pin);
            // "PIN  416 YD" reads as the caption PIN over a big 416 yd
            string value = obscured ? "Hole bearing" : text.Trim(), cap = "";
            if (!obscured && value.StartsWith("PIN")) { cap = "PIN"; value = value.Substring(3).Trim().Replace(" YD", " yd").Replace(" FT", " ft"); }
            caption.text = cap; label.text = value;
            float capW = cap.Length > 0 ? caption.preferredWidth + 18 : 0;
            caption.rectTransform.anchoredPosition = new Vector2(26, 0); label.rectTransform.anchoredPosition = new Vector2(26 + capW, 0);
            pill.sizeDelta = new Vector2(Mathf.Max(150, 52 + capW + label.preferredWidth), 48);
            var canvas = ((RectTransform)transform.parent).rect.size;
            var vp = view.WorldToViewportPoint(pin);
            bool behind = vp.z < 0;
            var d = new Vector2(vp.x - 0.5f, vp.y - 0.5f);
            if (behind) d = -d;
            if(obscured){
                var bearing=pin-GolfArcade.EnvironmentArt.DreamVisibility.Observer;bearing.y=0;
                float angle=Mathf.Round(Mathf.Atan2(bearing.x,bearing.z)*Mathf.Rad2Deg/30)*30;
                var coarse=view.transform.InverseTransformDirection(Quaternion.Euler(0,angle,0)*Vector3.forward);
                d=new Vector2(coarse.x,coarse.z*.55f);
            }
            // the frame it keeps inside: room for the pill and its arrow at the sides, clear of
            // the corners' cards at the top and the status line at the bottom
            float mx = Mathf.Min(0.45f, (pill.sizeDelta.x / 2 + 70) / Mathf.Max(1, canvas.x));
            const float bottom = 0.14f, top = 0.8f;
            bool inView = !obscured && !behind && vp.x > mx && vp.x < 1 - mx && vp.y > bottom && vp.y < top;
            Vector2 at;
            if (inView) at = new Vector2(vp.x, vp.y);
            else
            {
                if (d.sqrMagnitude < 1e-6f) d = new Vector2(0, -1);
                float tx = d.x > 0 ? (1 - mx - 0.5f) / d.x : d.x < 0 ? (mx - 0.5f) / d.x : float.MaxValue;
                float ty = d.y > 0 ? (top - 0.5f) / d.y : d.y < 0 ? (bottom - 0.5f) / d.y : float.MaxValue;
                at = new Vector2(0.5f, 0.5f) + d * Mathf.Min(tx, ty);
            }
            root.anchorMin = root.anchorMax = at;
            root.anchoredPosition = Vector2.zero;
            // over the pin, the pill stands on it; at the edge, the arrow points out past it
            pill.anchoredPosition = inView ? new Vector2(0, 44) : Vector2.zero;
            stem.gameObject.SetActive(inView); foot.gameObject.SetActive(inView);
            arrow.gameObject.SetActive(!inView);
            if (!inView)
            {
                var screenDir = new Vector2(d.x * canvas.x, d.y * canvas.y).normalized;
                arrow.anchoredPosition = new Vector2(screenDir.x * (pill.sizeDelta.x / 2 + 26), screenDir.y * 56);
                arrow.localRotation = Quaternion.Euler(0, 0, Mathf.Atan2(screenDir.y, screenDir.x) * Mathf.Rad2Deg - 90f);
            }
        }
    }

    /// The hole from above for the big screen, top right: the same live picture the controller
    /// carries on the phone (the map camera's texture), with the pin, the ball and where this
    /// swing comes down marked on it.
    public sealed class TvMap : MonoBehaviour
    {
        RawImage picture;
        RectTransform pin, ball, landing;
        static readonly Color Red = UiKit.Hex("E8352F");

        public static TvMap Create(Transform safeArea, float margin)
        {
            const float w = 460, h = w * 700f / 972f;   // the controller map's shape: the texture is shared
            var frame = UiKit.Pill(safeArea, "TV map", Color.white, new Vector2(1, 1), new Vector2(-margin - w / 2, -margin - h / 2), new Vector2(w + 16, h + 16), out var fill, 8f, false);
            foreach (var img in frame.GetComponentsInChildren<Image>()) img.sprite = UiKit.RoundedLarge;
            var m = frame.gameObject.AddComponent<TvMap>();
            var mask = UiKit.Panel(fill.transform, "Mask", Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            mask.sprite = UiKit.RoundedLarge; mask.raycastTarget = false;
            mask.gameObject.AddComponent<Mask>().showMaskGraphic = false;
            m.picture = new GameObject("Picture").AddComponent<RawImage>();
            m.picture.transform.SetParent(mask.transform, false);
            var prt = m.picture.rectTransform; prt.anchorMin = Vector2.zero; prt.anchorMax = Vector2.one; prt.offsetMin = prt.offsetMax = Vector2.zero;
            m.picture.raycastTarget = false;
            RectTransform Dot(string name, Color c, float size, Sprite sprite, bool rim)
            {
                RectTransform holder = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
                holder.SetParent(mask.transform, false); holder.sizeDelta = new Vector2(size, size);
                if (rim)
                {
                    var r = UiKit.Panel(holder, "Rim", Color.white, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(size + 8, size + 8));
                    r.sprite = UiKit.Circle; r.type = Image.Type.Simple; r.raycastTarget = false;
                }
                var dot = UiKit.Panel(holder, "Dot", c, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(size, size));
                dot.sprite = sprite; dot.type = Image.Type.Simple; dot.raycastTarget = false;
                return holder;
            }
            m.landing = Dot("Landing", Game.LandingZone.Amber, 30, UiKit.Ring, false);
            m.ball = Dot("Ball", Color.white, 20, UiKit.Circle, false);
            m.pin = Dot("Pin", Red, 24, UiKit.Circle, true);
            frame.gameObject.SetActive(false);
            return m;
        }

        public void Draw(Camera map, Texture texture, Vector3 pinAt, Vector3 ballAt, bool showBall, Vector3 landingAt, bool showLanding)
        {
            picture.texture = texture;
            GolfArcade.EnvironmentArt.DreamVisibility.Mask(picture,map);
            void Place(RectTransform mark, Vector3 world, bool show)
            {
                var vp = map ? map.WorldToViewportPoint(world) : Vector3.zero;
                bool inside = show && map && (mark==ball || GolfArcade.EnvironmentArt.DreamVisibility.Visible(world)) && vp.x >= 0 && vp.x <= 1 && vp.y >= 0 && vp.y <= 1;
                mark.gameObject.SetActive(inside);
                if (inside) { mark.anchorMin = mark.anchorMax = new Vector2(vp.x, vp.y); mark.anchoredPosition = Vector2.zero; }
            }
            Place(landing, landingAt, showLanding);
            Place(ball, ballAt, showBall);
            Place(pin, pinAt, true);
            ball.SetAsLastSibling();
        }
    }
}
