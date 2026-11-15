using System;
using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// The menu's widgets in the slash language (approved mock 10-28, ba_template2.html; 1cqw = 19.2 canvas px): menu items are words,
    /// not boxes — a stack of upper-case ExtraBold Italic words with an optional subline; the hovered one draws a gold skewed slash in
    /// behind itself, nudges right and turns ink, the rest of its stack dims. Pictures sit in skewed cards (a Mask on a sheared graphic,
    /// so the picture itself stays upright). Every widget hangs its hover look on MenuItem.glow, which the HUD eases 0..1 (Glows), so a
    /// hover costs a transform or two per frame and a text re-colour only when it crosses the half-way mark.
    public sealed partial class MenuHud
    {
        // the type (mock .mi 3cqw, .mi.big 7.2cqw, .rail 2.3cqw; sublines 1.1cqw raised to 26 so they read from the sofa)
        const float WordSize = 58, BigSize = 138, RailSize = 44, SubSize = 26, Nudge = 15, GlowSeconds = .2f;
        const float Left = 64, ListTop = 392, RightX = 1190, RightEdge = 1856;   // lists left of the hero, pop-ups right of it (x 800–1120 stays clear)
        static readonly Color WordRest = BrandUi.WhiteA(.88f), WordDim = BrandUi.WhiteA(.55f), WordOff = BrandUi.WhiteA(.35f), SubRest = BrandUi.WhiteA(.72f);

        /// One stack entry's look: the slash, the word, its subline; lit (hovered), dim (a sibling is), off (locked), picked (the
        /// selected slot: gold word on a faint slash).
        sealed class Word
        {
            public RectTransform face, slash; public Image pick; public Text label, sub, tag; public Image tagArrow; public Color subRest = SubRest;
            public bool lit, dim, off, picked;
            public void Glow(float k)
            {
                var s = new Vector3(k, 1, 1); if (slash.localScale != s) slash.localScale = s;
                face.anchoredPosition = new Vector2(Nudge * k, 0);
                bool on = k > .35f; if (on != lit) { lit = on; Paint(); }
            }
            public void Paint()
            {
                label.color = lit ? BrandColors.NavyInk : off ? WordOff : picked ? BrandColors.Gold : dim ? WordDim : WordRest;
                foreach (var s in label.GetComponents<Shadow>()) s.enabled = !lit;
                if (sub)
                {
                    var c = subRest; if (dim || off) c.a *= .6f;
                    sub.color = lit ? BrandColors.NavyDeep : c;
                    foreach (var s in sub.GetComponents<Shadow>()) s.enabled = !lit;
                }
                if (tag) { tag.color = lit ? BrandColors.NavyDeep : BrandColors.Glow; tagArrow.color = tag.color; }
                if (pick) pick.gameObject.SetActive(picked && !lit);
            }
        }

        /// A stack entry at (x, y): `text` shown (upper case), `label` for the phone (menuHover), `sub` under it. Returns its height.
        float WordItem(Transform parent, string id, string text, string label, string sub, float x, float y, float size, Action activate, List<MenuItem> group,
            float minW = 0, bool big = false, bool phone = false)
        {
            float textH = size * 1.1f, subSize = big ? 30 : SubSize, subH = string.IsNullOrEmpty(sub) ? 0 : subSize * 1.5f;
            float h = 6 + textH + subH + (subH > 0 ? 10 : 6);
            var box = BrandUi.Box(parent, text, x, y, 10, h);
            var face = BrandUi.Fill(box, "Face");
            var w = new Word { face = face };
            var pick = BrandUi.Slant(face, "Picked", BrandUi.WhiteA(.13f)); pick.rectTransform.offsetMin = new Vector2(-19, 0); pick.rectTransform.offsetMax = new Vector2(4, 0);
            pick.gameObject.SetActive(false); w.pick = pick;
            var slash = BrandUi.GoldSlash(face).rectTransform;
            slash.pivot = new Vector2(0, .5f); slash.offsetMin = new Vector2(-19, 0); slash.offsetMax = new Vector2(4, 0); slash.localScale = new Vector3(0, 1, 1);
            w.slash = slash;
            w.label = BrandUi.Word(BrandUi.Box(face, "Label", 6, 6, 10, textH), "Text", text, BrandUi.ExtraBoldItalic, size, WordRest);
            float width = w.label.preferredWidth + 6;
            if (phone)
            {
                // a slot that opens on the phone says so: ↗ PHONE after the word
                float tx = width + 22;
                w.tagArrow = BrandUi.Layer(BrandUi.Box(face, "Arrow", tx, 6 + (textH - 22) / 2, 22, 22), "Glyph", BrandColors.Glow, 0, -1, BrandUi.ArrowOut);
                w.tag = BrandUi.Word(BrandUi.Box(face, "Tag", tx + 26, 6, 10, textH), "Text", "PHONE", BrandUi.SemiBold, 20, BrandColors.Glow);
                width = tx + 26 + w.tag.preferredWidth;
            }
            if (subH > 0)
            {
                w.subRest = big ? BrandColors.Gold : SubRest;
                w.sub = BrandUi.Word(BrandUi.Box(face, "Sub", 10, 6 + textH, 10, subH), "Text", sub, big ? BrandUi.BoldItalic : BrandUi.MediumItalic, subSize, w.subRest);
                width = Mathf.Max(width, w.sub.preferredWidth + 10);
            }
            box.sizeDelta = new Vector2(Mathf.Max(minW, width + 40), h);
            var item = Item(box, face, id, label, activate, 0);
            item.glow = w.Glow; item.view = w; item.group = group; group?.Add(item);
            item.dim = d => { if (w.dim != d) { w.dim = d; w.Paint(); } };
            w.Paint();
            return h;
        }
        /// Re-fits an entry's slash to its words (a subline that changed, e.g. a locked mode's).
        static void FitWord(MenuItem it)
        {
            if (!(it.view is Word w)) return;
            float width = Mathf.Max(w.label.preferredWidth + 6, w.sub ? w.sub.preferredWidth + 10 : 0);
            var size = new Vector2(width + 40, it.hit.sizeDelta.y);
            if (it.hit.sizeDelta != size) it.hit.sizeDelta = size;
        }

        /// A skewed picture card: the clip (RawImage, upright) inside a Mask on a sheared graphic, a dark ramp over its lower part.
        /// `inside`: the slant stays in the rect (the mock's clip-path cards); otherwise it overhangs (its skewX cards, lanes, thumbs).
        static (RectTransform mask, RawImage pic) PictureCard(Transform parent, float angle, bool inside, float shadeFrom = .4f)
        {
            var mask = BrandUi.Skewed(BrandUi.Layer(parent, "Mask", Color.white), angle, inside);
            mask.gameObject.AddComponent<Mask>().showMaskGraphic = false;
            var pic = BrandUi.Fill(mask.transform, "Picture").gameObject.AddComponent<RawImage>(); pic.raycastTarget = false;
            if (!inside) { float over = Mathf.Tan(angle * Mathf.Deg2Rad) * ((RectTransform)parent).rect.height / 2 + 4; pic.rectTransform.offsetMin = new Vector2(-over, 0); pic.rectTransform.offsetMax = new Vector2(over, 0); }
            var shade = BrandUi.Fill(mask.transform, "Shade").gameObject.AddComponent<Image>(); shade.raycastTarget = false;
            shade.rectTransform.anchorMax = new Vector2(1, 1 - shadeFrom); shade.rectTransform.offsetMin = new Vector2(-60, 0); shade.rectTransform.offsetMax = new Vector2(60, 0);
            GolfArcade.Tennis.UiGradient.On(shade, BrandUi.Ink(0), BrandUi.Ink(.92f));
            return (mask.rectTransform, pic);
        }
        /// A picture fills its card without stretching (CSS background-size: cover).
        static void Cover(RawImage pic, float w, float h)
        {
            var tex = pic.texture; if (!tex || w <= 0 || h <= 0) return;
            float a = w / h, t = (float)tex.width / tex.height;
            var uv = a < t ? new Rect(.5f - a / t / 2, 0, a / t, 1) : new Rect(0, .5f - t / a / 2, 1, t / a);
            if (pic.uvRect != uv) pic.uvRect = uv;
        }

        /// Skewed tag chips (the mode's facts under the preview, a lane's modes): a fixed pool, only their words change.
        sealed class ChipRow
        {
            public readonly List<(RectTransform box, Image fill, Text text)> chips = new List<(RectTransform, Image, Text)>();
            public void Set(IList<string> words)
            {
                float x = 0;
                for (int i = 0; i < chips.Count; i++)
                {
                    var (box, fill, text) = chips[i];
                    bool on = words != null && i < words.Count;
                    if (box.gameObject.activeSelf != on) box.gameObject.SetActive(on);
                    if (!on) continue;
                    if (text.text != words[i]) text.text = words[i];
                    float w = text.preferredWidth + 30;
                    box.anchoredPosition = new Vector2(x, 0); box.sizeDelta = new Vector2(w, box.sizeDelta.y);
                    x += w + 12;
                }
            }
        }
        static ChipRow Chips(Transform parent, float x, float y, float h, int count, float size = 20)
        {
            var row = new ChipRow(); var root = BrandUi.Box(parent, "Chips", x, y, 900, h);
            for (int i = 0; i < count; i++)
            {
                var box = BrandUi.Box(root, "Chip " + i, 0, 0, 100, h);
                var fill = BrandUi.Slant(box, "Fill", i == 0 ? BrandColors.Gold : BrandUi.WhiteA(.18f), 12);
                var text = BrandUi.Word(box, "Text", "", BrandUi.BoldItalic, size, i == 0 ? BrandColors.NavyInk : BrandColors.White, TextAnchor.MiddleCenter);
                if (i == 0) foreach (var s in text.GetComponents<Shadow>()) s.enabled = false;
                row.chips.Add((box, fill, text)); box.gameObject.SetActive(false);
            }
            return row;
        }

        // ---- the hover glow: eased 0..1 per item, in and out
        readonly List<MenuItem> glowing = new List<MenuItem>();
        void Glows(float dt)
        {
            for (int i = glowing.Count - 1; i >= 0; i--)
            {
                var it = glowing[i];
                float want = it == hovered && !phoneOpen ? 1 : 0;
                if (it.lit == want) { if (want == 0) glowing.RemoveAt(i); continue; }
                it.lit = Mathf.MoveTowards(it.lit, want, dt / GlowSeconds);
                it.glow(BrandMotion.EaseOut(it.lit));
            }
        }
        /// A new screen starts unlit (no slash sliding out of a screen that is gone).
        void GlowsOff()
        {
            foreach (var it in glowing) { it.lit = 0; it.glow(0); }
            glowing.Clear();
        }
        void HoverLook(MenuItem was, MenuItem now)
        {
            if (was?.group != null) foreach (var g in was.group) g.dim?.Invoke(false);
            if (now?.group != null) foreach (var g in now.group) g.dim?.Invoke(g != now);
            if (now?.glow != null && !glowing.Contains(now)) glowing.Add(now);
        }
    }
}
