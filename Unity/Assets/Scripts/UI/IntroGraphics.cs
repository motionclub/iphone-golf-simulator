using System.Collections.Generic;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// The graphics of a round's opening (golf and tennis): playful, not corporate, and never in the way.
    ///  · Plate: a chunky sticker — white rim, candy gradient fill, a tilt of a couple of degrees — that pops in with a
    ///    springy overshoot, bobs gently while it is up and drops away; a small coloured tab over it, a detail chip under it.
    ///  · Tag: a bubble pinned to a place in the picture by a little tail and a pulsing dot (what a hole's highlight is).
    /// Everything is drawn in 1920-wide design units scaled to the parent (the HUD's own canvas), each piece anchored to the
    /// parent's own corners, so it sits on whichever screen the HUD is on, landscape or portrait, and stays on it when the
    /// canvas changes shape between layout and drawing (a resize, a capture at another aspect). Animation runs on the time the caller passes in, so it
    /// holds still while the game is paused.
    public sealed class IntroGraphics : MonoBehaviour
    {
        RectTransform parent, space;
        readonly List<Plate> plates = new();
        readonly List<Tag> tags = new();

        public static IntroGraphics On(RectTransform parent)
        {
            var go = new GameObject("Intro graphics", typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var g = go.AddComponent<IntroGraphics>();
            g.parent = parent; g.space = (RectTransform)go.transform;
            g.space.anchorMin = Vector2.zero; g.space.anchorMax = Vector2.one; g.space.pivot = new Vector2(.5f, .5f);
            g.space.offsetMin = g.space.offsetMax = Vector2.zero;
            g.Fit();
            return g;
        }
        /// Canvas units per design unit (the parent fits 1920 x 1080 of them), and the parent's size in design units.
        float k = 1;
        public Vector2 Size => space.rect.size / k;
        /// Drawn on an upright screen (handheld play on a phone with no TV).
        public bool Portrait => space && space.rect.width < space.rect.height;
        void Fit()
        {
            var r = space.rect.size; if (r.x <= 1 || r.y <= 1) return;
            // (an upright screen, a phone in handheld play, is laid out 1440 wide: a third bigger, still clear of each other)
            k = Mathf.Min(r.x / (Portrait ? 1440f : 1920f), r.y / 1080f);
            foreach (var t in tags) if (t.root) t.root.localScale = Vector3.one * k;
        }
        void LateUpdate() => Fit();

        public void Clear()
        {
            // (hidden first: a destroyed object still draws in a capture taken later the same frame)
            foreach (var p in plates) if (p.root) { p.root.gameObject.SetActive(false); Destroy(p.root.gameObject); }
            foreach (var t in tags) if (t.root) { t.root.gameObject.SetActive(false); Destroy(t.root.gameObject); }
            plates.Clear(); tags.Clear();
        }
        void OnDestroy() => Clear();

        // ---------------------------------------------------------------- palette
        public static readonly Color Ink = UiKit.Hex("10243D"), Lime = UiKit.Hex("C8F03C"), Sky = UiKit.Hex("38B6FF"), Coral = UiKit.Hex("FF6B8B"),
            Sun = UiKit.Hex("FFC83D"), Lava = UiKit.Hex("FF7A2B"), Grape = UiKit.Hex("9C7CFF"), Grass = UiKit.Hex("5ED34E"), Cream = UiKit.Hex("FFF9EE");
        static Color Lighter(Color c, float k) => Color.Lerp(c, Color.white, k);
        static Color Darker(Color c, float k) => Color.Lerp(c, Ink, k);

        // ---------------------------------------------------------------- pieces
        Image Shape(RectTransform to, string name, Color c, Sprite sprite, Vector2 offMin, Vector2 offMax)
        {
            var img = new GameObject(name).AddComponent<Image>(); img.transform.SetParent(to, false);
            img.sprite = sprite; img.type = Image.Type.Sliced; img.color = c; img.raycastTarget = false;
            var rt = img.rectTransform; rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = offMin; rt.offsetMax = offMax;
            return img;
        }
        static RectTransform Holder(RectTransform to, string name, Vector2 anchor, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>(); rt.SetParent(to, false);
            rt.anchorMin = rt.anchorMax = anchor; rt.pivot = pivot; rt.anchoredPosition = pos; rt.sizeDelta = size;
            return rt;
        }
        static Text Words(RectTransform to, string s, int size, Color c, Font f, TextAnchor a, float outline = 0, Color? outlineColor = null)
        {
            var t = new GameObject("Text").AddComponent<Text>(); t.transform.SetParent(to, false);
            t.font = f; t.fontSize = size; t.color = c; t.alignment = a; t.text = s; t.raycastTarget = false;
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow;
            var rt = t.rectTransform; rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
            if (outline > 0)
            {
                var oc = outlineColor ?? Ink;
                var o1 = t.gameObject.AddComponent<Outline>(); o1.effectColor = oc; o1.effectDistance = new Vector2(outline, -outline);
                var o2 = t.gameObject.AddComponent<Outline>(); o2.effectColor = oc; o2.effectDistance = new Vector2(-outline, outline);
                var d = t.gameObject.AddComponent<Shadow>(); d.effectColor = new Color(oc.r, oc.g, oc.b, .6f); d.effectDistance = new Vector2(0, -outline * 1.8f);
            }
            return t;
        }
        /// A rimmed candy pill: drop shadow, white rim, gradient fill (lighter at the top), a gloss along the top.
        RectTransform Sticker(RectTransform to, string name, Color fill, Vector2 anchor, Vector2 pivot, Vector2 pos, Vector2 size, float rim = 7)
        {
            var root = Holder(to, name, anchor, pivot, pos, size);
            Shape(root, "Shadow", new Color(.04f, .1f, .25f, .32f), UiKit.RoundedLarge, new Vector2(0, -12), new Vector2(0, -12));
            Shape(root, "Rim", Color.white, UiKit.RoundedLarge, Vector2.zero, Vector2.zero);
            var body = Shape(root, "Fill", fill, UiKit.RoundedLarge, new Vector2(rim, rim), new Vector2(-rim, -rim));
            UiGradient.On(body, Lighter(fill, .22f), Darker(fill, .12f));
            var gloss = Shape(root, "Gloss", new Color(1, 1, 1, .2f), UiKit.RoundedLarge, new Vector2(rim + 12, size.y * .52f), new Vector2(-rim - 12, -rim - 6));
            return root;
        }

        // ---------------------------------------------------------------- the plate
        public sealed class Plate
        {
            public RectTransform root; internal RectTransform main, tab, chip; internal CanvasGroup group; internal float tilt, born, side, baseY = 34;
            internal Vector2 at;   // from its corner of the screen (design units)
            internal bool hiding; internal float hiddenAt;
        }
        /// A name plate low in a corner: `kicker` on a tab over it, `title` big, `detail` on a chip under it.
        public Plate ShowPlate(string kicker, string title, string detail, Color fill, bool right, float time, float bottom = 92)
        {
            var p = new Plate { side = right ? 1 : -1, tilt = right ? 2.4f : -2.4f, born = time };
            int titleSize = 92; float w = Mathf.Clamp(title.Length * titleSize * .66f + 120, 380, 1100), h = 150;
            p.at = new Vector2(right ? -90 : 90, bottom);
            p.root = Holder(space, "Plate", new Vector2(right ? 1 : 0, 0), new Vector2(right ? 1 : 0, 0), p.at * k, new Vector2(w, h + 120));
            p.group = p.root.gameObject.AddComponent<CanvasGroup>();
            p.main = Sticker(p.root, "Title", fill, new Vector2(right ? 1 : 0, 0), new Vector2(right ? 1 : 0, 0), new Vector2(0, 34), new Vector2(w, h), 8);
            var tt = Words(Holder(p.main, "Title text", new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, 4), new Vector2(w - 40, h)), title, titleSize, Color.white, UiKit.Display, TextAnchor.MiddleCenter, 4, Darker(fill, .55f));
            if (!string.IsNullOrEmpty(kicker))
            {
                float kw = kicker.Length * 19 + 64;
                p.tab = Sticker(p.root, "Kicker", Sun, new Vector2(right ? 1 : 0, 0), new Vector2(right ? 1 : 0, 0), new Vector2(right ? -34 : 34, 34 + h - 16), new Vector2(kw, 58), 5);
                Words(Holder(p.tab, "Kicker text", new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, 1), new Vector2(kw, 58)), kicker, 30, Ink, UiKit.Display, TextAnchor.MiddleCenter);
                p.tab.localRotation = Quaternion.Euler(0, 0, -p.tilt * 1.6f);
            }
            if (!string.IsNullOrEmpty(detail))
            {
                float dw = detail.Length * 15.5f + 56;
                p.chip = Sticker(p.root, "Detail", Cream, new Vector2(right ? 1 : 0, 0), new Vector2(right ? 1 : 0, 0), new Vector2(right ? -70 : 70, -8), new Vector2(dw, 54), 4);
                Words(Holder(p.chip, "Detail text", new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, 1), new Vector2(dw, 54)), detail, 26, Ink, UiKit.Strong, TextAnchor.MiddleCenter);
            }
            p.root.localRotation = Quaternion.Euler(0, 0, p.tilt);
            plates.Add(p); TickPlate(p, time);
            return p;
        }
        public void HidePlate(Plate p, float time) { if (p != null && !p.hiding) { p.hiding = true; p.hiddenAt = time; } }

        // ---------------------------------------------------------------- map pieces (UI OVERHAUL 11-15)

        /// The map's arrival: its sculpted title (boards 01-10 ARRIVAL) low in a corner, popping in like a plate, and a small
        /// "Skip intro ›" pill in the far corner (the phone's button skips; this says so on the TV).
        public Plate ShowMapTitle(MapSkin skin, bool right, float time, float height = 330, bool skipHint = true, string detail = null)
        {
            var sprite = skin.TitleSprite;
            if (!sprite) return ShowPlate("", skin.Title, detail ?? "", Sky, right, time);
            float w = height * sprite.rect.width / Mathf.Max(1, sprite.rect.height);
            var p = TitleShell("Map title", right, time, w, height, skipHint, detail);
            var img = new GameObject("Sculpted title").AddComponent<Image>(); img.transform.SetParent(p.main, false);
            img.sprite = sprite; img.preserveAspect = true; img.raycastTarget = false;
            var rt = img.rectTransform; rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
            var drop = img.gameObject.AddComponent<Shadow>(); drop.effectColor = new Color(0, 0, 0, .35f); drop.effectDistance = new Vector2(0, -10);
            return p;
        }

        /// A mode's own name where the map's title stands (the Daily Challenge: "DAILY CHALLENGE"), lettered into the map's sculpted
        /// plate, with the same pop, bob and cream fact tab as the map's title (2026-11-16, Adnan: the same UI as the game, named for
        /// the mode).
        public Plate ShowWordTitle(MapSkin skin, string words, bool right, float time, float height = 230, bool skipHint = false, string detail = null, float bottom = -1)
        {
            if (!skin.PlateSprite) return ShowPlate("", words, detail ?? "", right ? Grape : Coral, right, time);
            float w = height * skin.PlateSprite.rect.width / Mathf.Max(1, skin.PlateSprite.rect.height);
            var p = TitleShell("Mode title", right, time, w, height, skipHint, detail, bottom);
            skin.Plate("Plate art", p.main, MapSkin.Piece.Plate, (words ?? "").ToUpperInvariant(), height, new Vector2(.5f, .5f), Vector2.zero);
            return p;
        }

        /// The frame a title stands in: low in its corner, tilted a touch, the facts on a cream tab under it (centred under the
        /// title, or held to the screen's edge side when wider than it, so it never runs off a narrow screen), the Skip chip.
        Plate TitleShell(string name, bool right, float time, float w, float height, bool skipHint, string detail, float bottom = -1)
        {
            var p = new Plate { side = right ? 1 : -1, tilt = right ? 1.6f : -1.6f, born = time, baseY = 20 };
            p.at = new Vector2(right ? -70 : 70, bottom >= 0 ? bottom : string.IsNullOrEmpty(detail) ? 70 : 118);
            p.root = Holder(space, name, new Vector2(right ? 1 : 0, 0), new Vector2(right ? 1 : 0, 0), p.at * k, new Vector2(w, height));
            p.group = p.root.gameObject.AddComponent<CanvasGroup>();
            p.main = Holder(p.root, "Title art", new Vector2(.5f, 0), new Vector2(.5f, 0), Vector2.zero, new Vector2(w, height));
            if (!string.IsNullOrEmpty(detail))
            {
                float dw = Mathf.Min(60 + detail.Length * 19, Size.x - 2 * 70 - 40);
                bool centred = dw <= w;
                float x = centred ? .5f : right ? 1 : 0;
                p.tab = Holder(p.root, "Detail", new Vector2(x, 0), new Vector2(x, 1), new Vector2(0, -2), new Vector2(dw, 62));
                Shape(p.tab, "Pill", Cream, UiKit.RoundedLarge, Vector2.zero, Vector2.zero);
                var t = Words(Holder(p.tab, "Detail text", new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(dw - 30, 62)), detail, 30, Ink, MapSkin.Bold, TextAnchor.MiddleCenter);
                t.horizontalOverflow = HorizontalWrapMode.Wrap; t.resizeTextForBestFit = true; t.resizeTextMinSize = 18; t.resizeTextMaxSize = 30;
            }
            if (skipHint)
            {
                p.chip = Holder(p.root, "Skip intro", new Vector2(right ? 0 : 1, 0), new Vector2(.5f, .5f), Vector2.zero, new Vector2(200, 92));
                p.chip.SetParent(space, true);
                p.chip.anchorMin = p.chip.anchorMax = new Vector2(right ? 0 : 1, 0); p.chip.anchoredPosition = new Vector2((right ? 1 : -1) * 170 * k, 110 * k);
                p.chip.localScale = Vector3.one * k;
                Shape(p.chip, "Pill", Cream, UiKit.RoundedLarge, Vector2.zero, Vector2.zero);
                Words(Holder(p.chip, "Skip text", new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(200, 92)), "Skip intro ›", 34, Ink, MapSkin.Bold, TextAnchor.MiddleCenter);
                p.chip.SetParent(p.root, true);
            }
            p.root.localRotation = Quaternion.Euler(0, 0, p.tilt);
            plates.Add(p); TickPlate(p, time);
            return p;
        }

        /// A player's username on the map's sculpted plate (board 12 intros: no role words, no YOU).
        public Plate ShowNamePlate(MapSkin skin, string name, bool right, float time, float bottom = 92, float height = 190)
        {
            if (!skin.PlateSprite) return ShowPlate("", name, "", right ? Grape : Coral, right, time, bottom);
            var p = new Plate { side = right ? 1 : -1, tilt = right ? 2f : -2f, born = time };
            p.at = new Vector2(right ? -90 : 90, bottom);
            float w = height * skin.PlateSprite.rect.width / Mathf.Max(1, skin.PlateSprite.rect.height);
            p.root = Holder(space, "Name plate", new Vector2(right ? 1 : 0, 0), new Vector2(right ? 1 : 0, 0), p.at * k, new Vector2(w, height + 40));
            p.group = p.root.gameObject.AddComponent<CanvasGroup>();
            p.main = Holder(p.root, "Plate", new Vector2(.5f, 0), new Vector2(.5f, 0), new Vector2(0, 34), new Vector2(w, height));
            skin.Plate("Plate art", p.main, MapSkin.Piece.Plate, (name ?? "").ToUpperInvariant(), height, new Vector2(.5f, .5f), Vector2.zero);
            p.root.localRotation = Quaternion.Euler(0, 0, p.tilt);
            plates.Add(p); TickPlate(p, time);
            return p;
        }
        static float Spring(float x) { x = Mathf.Clamp01(x); return 1 - Mathf.Exp(-x * 6.5f) * Mathf.Cos(x * 10.5f); }
        static float Ease(float x) { x = Mathf.Clamp01(x); return x * x * (3 - 2 * x); }
        void TickPlate(Plate p, float time)
        {
            if (!p.root) return;
            float s = time - p.born;
            // pops in (the plate, then its tab, then its chip), wobbles a breath, bobs while it is up, drops away
            float pop = Spring(s / .55f), tab = Spring((s - .12f) / .5f), chip = Spring((s - .22f) / .5f);
            float bob = Mathf.Sin(s * 2.4f) * 5, sway = Mathf.Sin(s * 1.7f + .6f) * .7f;
            float gone = p.hiding ? Ease((time - p.hiddenAt) / .28f) : 0;
            float scale = Mathf.LerpUnclamped(.35f, 1, pop) * (1 - .2f * gone);
            var lift = new Vector2(0, p.baseY + bob - 60 * gone);
            if (p.main == p.root) { p.root.localScale = Vector3.one * scale * k; p.root.anchoredPosition = (p.at + lift) * k; }
            else { p.root.localScale = Vector3.one * k; p.root.anchoredPosition = p.at * k; p.main.localScale = Vector3.one * scale; p.main.anchoredPosition = lift; }
            if (p.tab) p.tab.localScale = Vector3.one * Mathf.LerpUnclamped(.2f, 1, tab);
            if (p.chip) p.chip.localScale = Vector3.one * Mathf.LerpUnclamped(.2f, 1, chip);
            p.root.localRotation = Quaternion.Euler(0, 0, p.tilt + sway + (1 - Mathf.Clamp01(pop)) * p.side * -9);
            p.group.alpha = Mathf.Clamp01(s / .12f) * (1 - gone);
            if (p.hiding && gone >= 1) { Destroy(p.root.gameObject); p.root = null; }
        }

        // ---------------------------------------------------------------- the tag
        public sealed class Tag
        {
            public RectTransform root; internal RectTransform bubble, tail, dot, ring; internal CanvasGroup group; internal float born; internal Color fill;
            internal bool hiding; internal float hiddenAt; internal Vector2 offset; internal float width;
        }
        public void HideTag(Tag t, float time) { if (t != null && !t.hiding) { t.hiding = true; t.hiddenAt = time; } }
        /// Pin the tag on a viewport point of `camera`'s picture (hidden behind the lens or off the screen).
        public void Pin(Tag t, Camera camera, Vector3 world, float time)
        {
            if (t == null || !t.root) return;
            var v = camera.WorldToViewportPoint(world);
            var size = Size; var at = new Vector2((v.x - .5f) * size.x, (v.y - .5f) * size.y);
            float s = time - t.born, gone = t.hiding ? Ease((time - t.hiddenAt) / .25f) : 0;
            // the bubble above the spot (below it when the spot is high), kept on the screen
            bool below = at.y > size.y * .5f - 330;
            float up = below ? -230 : 120;
            float x = Mathf.Clamp(at.x, -size.x / 2 + t.width / 2 + 50, size.x / 2 - t.width / 2 - 50);
            var bubbleAt = new Vector2(x, at.y + up + (below ? -132 : 0));
            float pop = Spring((s - .1f) / .5f), dotPop = Spring(s / .4f);
            t.bubble.anchoredPosition = bubbleAt + new Vector2(0, Mathf.Sin(s * 2.6f) * 5);
            t.bubble.localScale = Vector3.one * Mathf.LerpUnclamped(.3f, 1, pop) * (1 - .25f * gone);
            t.bubble.localRotation = Quaternion.Euler(0, 0, Mathf.Sin(s * 1.9f) * 1.2f + (1 - Mathf.Clamp01(pop)) * 8);
            t.tail.anchoredPosition = new Vector2(Mathf.Lerp(x, at.x, .35f), at.y + (below ? -64 : 64) * 1f);
            t.tail.localRotation = Quaternion.Euler(0, 0, 45); t.tail.localScale = Vector3.one * Mathf.Clamp01(pop);
            t.dot.anchoredPosition = at; t.dot.localScale = Vector3.one * Mathf.LerpUnclamped(.2f, 1, dotPop);
            float pulse = Mathf.Repeat(s * .9f, 1);
            t.ring.anchoredPosition = at; t.ring.localScale = Vector3.one * Mathf.Lerp(.6f, 2.1f, pulse);
            t.ring.GetComponentInChildren<Image>().color = new Color(1, 1, 1, (1 - pulse) * .85f);
            t.group.alpha = v.z <= 0 ? 0 : Mathf.Clamp01(s / .12f) * (1 - gone);
            if (t.hiding && gone >= 1) { Destroy(t.root.gameObject); t.root = null; }
        }

        /// Animate every plate (tags are placed by Pin, which needs the camera), and fade out the tags let go, pinned or not.
        public void Tick(float time)
        {
            foreach (var p in plates) TickPlate(p, time);
            foreach (var t in tags)
            {
                if (!t.root || !t.hiding) continue;
                float gone = Ease((time - t.hiddenAt) / .25f);
                t.group.alpha = Mathf.Min(t.group.alpha, 1 - gone);
                if (gone >= 1) { Destroy(t.root.gameObject); t.root = null; }
            }
            plates.RemoveAll(p => !p.root); tags.RemoveAll(t => !t.root);
        }

        /// A small "VS" sticker between two plates.
        public RectTransform ShowVs(float time)
        {
            // (board 12: a cream VS pill with the plates' navy ink)
            var r = Sticker(space, "VS", Cream, new Vector2(.5f, 0), new Vector2(.5f, 0), Vector2.zero, new Vector2(170, 110), 7);
            Words(Holder(r, "VS text", new Vector2(.5f, .5f), new Vector2(.5f, .5f), new Vector2(0, 3), new Vector2(170, 110)), "VS", 64, Ink, MapSkin.Bold, TextAnchor.MiddleCenter);
            var plate = new Plate { root = r, main = r, group = r.gameObject.AddComponent<CanvasGroup>(), born = time, tilt = -4, side = 1, baseY = 150 };
            plates.Add(plate); TickPlate(plate, time);
            return r;
        }
    }
}
