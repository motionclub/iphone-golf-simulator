using System;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// The size of the surface a capture is rendering into, while it renders (GameCapture.Save sets it): the
    /// full-screen cards lay out against it instead of against the editor window.
    public static class OffscreenSize
    {
        public static Vector2Int? Override;
        public static int Width(Camera c) => Override?.x ?? c.pixelWidth;
        public static int Height(Camera c) => Override?.y ?? c.pixelHeight;
    }

    /// The ball drops: everything that follows a hole out, in the way the party games do it. The score is stamped across the
    /// screen on a ribbon (BIRDIE!, in gold for an eagle or an ace, sky blue for par, orange for a bogey) with the hole against
    /// par under it (-1, E, +2) and confetti, and the golfer is left in the clear; along the bottom the emotes and NEXT HOLE
    /// with a countdown. No scorecard: the strokes hole by hole are for the round's card at the end. It replaces the shot's
    /// stats panel and the landing badge. The big screen and the phone share it, laid out for each.
    public sealed class HoleOutCard : MonoBehaviour
    {
        public sealed class Data
        {
            /// BIRDIE!, PAR, BOGEY …
            public string Score;
            /// HOLE 2 OF 5  ·  NEEDLE
            public string Eyebrow;
            /// PAR 4  ·  HOLED FROM 14 FT
            public string Detail;
            /// The hole against par (the ribbon's colour and the number under it), the round against par and the holes played.
            public int Strokes, Par, HoleToPar, ToPar, Thru;
            /// The button: NEXT HOLE (or SCORECARD on the last), and what comes up: 3 · THE STEPS · PAR 3 · 148 YD.
            public string NextLabel, NextDetail;
            public string[] Emotes;
        }

        static readonly Color Ink = UiKit.Hex("10243D"), Lime = UiKit.Hex("D7F044"), LimeDeep = UiKit.Hex("9FBF1C"), Cream = UiKit.Hex("FFF9EE");

        Camera view;
        Canvas canvas;
        CanvasScaler scaler;
        RectTransform root, ribbonWrap, wordRect, scoreRect, stickerWrap, bottomWrap;
        CanvasGroup stickerFade, emoteFade;
        ConfettiGraphic confetti;
        HoldButton next;
        Image countdownFill;
        Text nextLabelText;
        Data data;
        Action proceed;
        Func<int, bool> emote;
        bool portraitBuilt, confettiThrown;
        float shownAt, builtWidth, builtHeight;

        public bool Showing => gameObject.activeSelf;
        public string ScoreWord => data?.Score;
        /// The number under the word: the hole against par (-1, E, +2).
        public string ToParText => data == null ? "" : GolfArcade.Course.Scorecard.FormatToPar(data.HoleToPar);
        public string NextText => nextLabelText ? nextLabelText.text : "";

        public static HoleOutCard Create(Transform parent, Camera camera)
        {
            var go = new GameObject("Hole out card", typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var canvas = UiKit.Canvas(go);
            canvas.renderMode = RenderMode.ScreenSpaceCamera;
            canvas.worldCamera = camera; canvas.planeDistance = .5f;
            canvas.sortingOrder = 55; canvas.targetDisplay = camera.targetDisplay;
            var c = go.AddComponent<HoleOutCard>();
            c.view = camera; c.canvas = canvas; c.scaler = go.GetComponent<CanvasScaler>();
            go.SetActive(false);
            return c;
        }

        public void Show(Data card, Action onNext, Func<int, bool> onEmote)
        {
            data = card; proceed = onNext; emote = onEmote;
            shownAt = Time.unscaledTime; confettiThrown = false;
            gameObject.SetActive(true);
            Rebuild(Portrait);
            LateUpdate();
        }

        public void Hide() { gameObject.SetActive(false); }

        bool Portrait => view && (OffscreenSize.Override is Vector2Int o ? o.x < o.y * 1.2f : view.aspect < 1.2f);

        /// Lays the card out against the surface it is being drawn to now (for the offscreen captures).
        public void RefreshLayout() { if (gameObject.activeInHierarchy) LateUpdate(); }

        /// The seconds left before the game goes on by itself (of `total`), as the bar under NEXT HOLE.
        public void SetCountdown(float seconds, float total)
        {
            if (!countdownFill) return;
            countdownFill.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(seconds / Mathf.Max(0.01f, total)), 1);
        }

        // ---- Frame

        void LateUpdate()
        {
            if (!view || data == null) return;
            bool portrait = Portrait;
            float width = OffscreenSize.Width(view), height = OffscreenSize.Height(view);
            // one canvas unit is a thousandth of the phone's width (or of the big screen's height), whatever the
            // display: the sizing the golf HUD uses, so a capture into a render texture lays out like the glass
            float scale = Mathf.Max(.1f, portrait ? width / 1080f : height / 1080f);
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize;
            scaler.scaleFactor = scale; canvas.scaleFactor = scale;
            canvas.targetDisplay = view.targetDisplay;
            if (portrait != portraitBuilt || !Mathf.Approximately(width, builtWidth) || !Mathf.Approximately(height, builtHeight)) Rebuild(portrait);
            Animate(Time.unscaledTime - shownAt);
        }

        static float Back(float x) { x = Mathf.Clamp01(x) - 1; const float c = 1.70158f; return 1 + (c + 1) * x * x * x + c * x * x; }
        static float Out(float x) { x = 1 - Mathf.Clamp01(x); return 1 - x * x * x; }

        /// The reveal, in beats: the ribbon sweeps in and the word is stamped on it, the score against par pops under it,
        /// confetti flies, the hole is named, then the way on rises.
        void Animate(float t)
        {
            if (GolfArcade.Game.PresentationPolicy.Constrained) t = 10;
            float w = portraitBuilt ? 1500 : 2100;
            ribbonWrap.anchoredPosition = new Vector2(Mathf.Lerp(-w, 0, Back((t - 0.0f) / 0.42f)), 0);
            float stamp = Mathf.Clamp01((t - 0.14f) / 0.36f);
            wordRect.localScale = stamp <= 0 ? Vector3.zero : Vector3.one * Mathf.Lerp(2.4f, 1f, Back(stamp));
            scoreRect.localScale = Vector3.one * Mathf.Max(0, Back((t - 0.24f) / 0.4f));
            stickerFade.alpha = Mathf.Clamp01((t - 0.42f) / 0.25f);
            stickerWrap.anchoredPosition = new Vector2(0, Mathf.Lerp(40, 0, Out((t - 0.42f) / 0.3f)));
            bottomWrap.anchoredPosition = new Vector2(0, Mathf.Lerp(-480, 0, Out((t - 0.5f) / 0.5f)));
            if (!confettiThrown && t > 0.2f) { confettiThrown = true; confetti.Burst(portraitBuilt ? 90 : 110, (data.Score ?? "").Length * 31 + data.Strokes); }
        }

        // ---- Building (positions are in canvas units: 1080 across on the phone, 1080 high on the big screen)

        static RectTransform Node(Transform parent, string name)
        {
            var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
            rt.SetParent(parent, false);
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
            return rt;
        }

        static RectTransform Stretched(Transform parent, string name)
        {
            var rt = Node(parent, name);
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.pivot = new Vector2(.5f, .5f); rt.offsetMin = rt.offsetMax = Vector2.zero;
            return rt;
        }

        static T Add<T>(Transform parent, string name) where T : Graphic
        {
            var rt = Stretched(parent, name);
            var g = rt.gameObject.AddComponent<T>(); g.raycastTarget = false;
            return g;
        }

        static Image Rounded(Transform parent, string name, Color color, float radius, bool ring = false)
        {
            var img = Club.Paint(parent, name, color, radius, ring); img.raycastTarget = false; return img;
        }

        static void Put(RectTransform rt, Vector2 anchor, Vector2 pivot, float x, float y, float w, float h)
        {
            rt.anchorMin = rt.anchorMax = anchor; rt.pivot = pivot; rt.anchoredPosition = new Vector2(x, y); rt.sizeDelta = new Vector2(w, h);
        }

        static Text Label(Transform parent, string name, string text, Font face, int size, Color color, TextAnchor anchor = TextAnchor.MiddleCenter)
        {
            var t = Club.Words(parent, name, text, face, size, color, anchor);
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow;
            return t;
        }

        /// Ribbon colours by what the hole came to: gold for an ace or an eagle or better, lime a birdie, sky par, orange a bogey, red worse.
        Color[] RibbonColours()
        {
            if (data.Strokes == 1 || data.HoleToPar <= -2) return new[] { UiKit.Hex("ffc928"), UiKit.Hex("ffe98a"), UiKit.Hex("ffa72a") };
            if (data.HoleToPar < 0) return new[] { UiKit.Hex("bfe83a"), UiKit.Hex("e8f87a"), UiKit.Hex("9ee06b") };
            if (data.HoleToPar == 0) return new[] { UiKit.Hex("53cfe8"), UiKit.Hex("a6ecf6"), UiKit.Hex("4cb8e8") };
            if (data.HoleToPar == 1) return new[] { UiKit.Hex("ff9a5a"), UiKit.Hex("ffc08e"), UiKit.Hex("ff7a4a") };
            return new[] { UiKit.Hex("ff6a5a"), UiKit.Hex("ff9a8e"), UiKit.Hex("e8483a") };
        }

        void Rebuild(bool portrait)
        {
            portraitBuilt = portrait;
            builtWidth = OffscreenSize.Width(view); builtHeight = OffscreenSize.Height(view);
            if (root) { root.gameObject.SetActive(false); Destroy(root.gameObject); }   // (gone from view at once, not at the frame's end)
            float scale = Mathf.Max(.1f, portrait ? builtWidth / 1080f : builtHeight / 1080f);
            float W = builtWidth / scale, H = builtHeight / scale;
            float safeTop = 0, safeBottom = 0;
            if (view.targetDisplay == 0 && !view.targetTexture && OffscreenSize.Override == null)
            { var safe = Screen.safeArea; safeTop = Mathf.Max(0, Screen.height - safe.yMax) / scale; safeBottom = safe.yMin / scale; }
            root = Stretched(transform, "Card");
            var topLeft = new Vector2(0, 1); var bottomMid = new Vector2(.5f, 0); var center = new Vector2(.5f, .5f);

            // The golfer is left in the clear: on the phone between the banner and the way on (CameraRig.FrameHoleOut puts them
            // there), on the big screen in the left half while all of this sits in a column on the right.
            float colX = portrait ? 0 : 1000, colW = portrait ? W : 820, colMid = colX + colW / 2;
            confetti = Add<ConfettiGraphic>(root, "Confetti");

            // ---- the ribbon and the word stamped on it
            ribbonWrap = Stretched(root, "Ribbon sweep");
            float ribbonH = portrait ? 230 : 200, ribbonTop = portrait ? 200 + safeTop : 60;
            var ribbon = Node(ribbonWrap, "Ribbon");
            float ribbonLeft = portrait ? -80 : colX - 40, ribbonRight = W + 80;
            Put(ribbon, topLeft, center, (ribbonLeft + ribbonRight) / 2, -(ribbonTop + ribbonH / 2), ribbonRight - ribbonLeft, ribbonH);
            ribbon.localEulerAngles = new Vector3(0, 0, portrait ? -4f : -3f);
            bool clear = GlassKit.ClearStyle;
            if (!clear)
            {
            var shade = Add<Image>(ribbon, "Shadow"); shade.color = new Color(.03f, .1f, .18f, .55f); shade.rectTransform.offsetMin = new Vector2(0, -22); shade.rectTransform.offsetMax = new Vector2(0, -22);
            var fill = Add<GradientGraphic>(ribbon, "Fill"); fill.Stops = RibbonColours();
            foreach (var side in new[] { 1f, 0f })
            {
                var edge = Add<Image>(ribbon, side > 0 ? "Top edge" : "Bottom edge"); edge.color = Color.white;
                edge.rectTransform.anchorMin = new Vector2(0, side); edge.rectTransform.anchorMax = new Vector2(1, side); edge.rectTransform.pivot = new Vector2(.5f, side);
                edge.rectTransform.sizeDelta = new Vector2(0, 10); edge.rectTransform.anchoredPosition = Vector2.zero;
            }
            }
            int wordMax = portrait ? 200 : 150;
            var word = UiKit.Chunky(ribbon, "Score", wordMax, clear ? RibbonColours()[0] : Color.white, clear ? GlassKit.Ink : Ink, portrait ? 8 : 7);
            word.text = data.Score; word.horizontalOverflow = HorizontalWrapMode.Overflow;
            wordRect = word.rectTransform;
            wordRect.anchorMin = wordRect.anchorMax = center; wordRect.pivot = center;
            wordRect.anchoredPosition = new Vector2(colMid - (ribbonLeft + ribbonRight) / 2, 0);
            wordRect.sizeDelta = new Vector2(portrait ? 900 : 760, ribbonH - 30);
            Icons.Fit(word, 50, wordMax);

            // ---- under it, the hole against par: -1, E, +2 (the strokes and the round so far are for the round's card)
            float scoreH = portrait ? 280 : 300, scoreTop = ribbonTop + ribbonH + (portrait ? 24 : 16);
            scoreRect = Node(root, "To par");
            Put(scoreRect, topLeft, center, colMid, -(scoreTop + scoreH / 2), colW, scoreH);
            var toPar = UiKit.Chunky(scoreRect, "Number", portrait ? 250 : 270, RibbonColours()[0], clear ? GlassKit.Ink : Ink, portrait ? 10 : 10);
            toPar.text = ToParText; toPar.horizontalOverflow = HorizontalWrapMode.Overflow;

            // ---- the hole, on a cream sticker
            stickerWrap = Stretched(root, "Sticker"); stickerFade = stickerWrap.gameObject.AddComponent<CanvasGroup>();
            var sticker = Node(stickerWrap, "Pill");
            float stickerH = portrait ? 84 : 70;
            Text stickerText;
            if (clear) { stickerText = UiKit.Chunky(sticker, "Hole", portrait ? 40 : 36, Color.white, GlassKit.Ink, 3); stickerText.text = data.Eyebrow; stickerText.horizontalOverflow = HorizontalWrapMode.Overflow; }
            else stickerText = Label(sticker, "Hole", data.Eyebrow, UiKit.Display, portrait ? 38 : 32, Ink);
            float stickerW = Mathf.Min(colW - 60, stickerText.preferredWidth + (portrait ? 96 : 84));
            Put(sticker, topLeft, center, colMid, -(scoreTop + scoreH + (portrait ? 10 : 6) + stickerH / 2), stickerW, stickerH);
            sticker.localEulerAngles = new Vector3(0, 0, -2);
            if (!clear) { var stickerBack = Rounded(sticker, "Back", Cream, 80); stickerBack.transform.SetAsFirstSibling(); }
            stickerText.rectTransform.anchorMin = Vector2.zero; stickerText.rectTransform.anchorMax = Vector2.one; stickerText.rectTransform.offsetMin = stickerText.rectTransform.offsetMax = Vector2.zero;

            // ---- the emotes and the way on, rising together
            bottomWrap = Stretched(root, "Bottom");
            int n = data.Emotes?.Length ?? 0;
            float eh = portrait ? 76 : 64, gap = portrait ? 16 : 12, ctaH = portrait ? 156 : 136, space = portrait ? 36 : 40;
            float rowW = portrait ? W - 88 : colW;
            RectTransform emotesAt, ctaAt;
            if (portrait)
            {
                float ctaBottom = 80 + safeBottom;
                ctaAt = Node(bottomWrap, "Next place"); Put(ctaAt, bottomMid, new Vector2(.5f, 0), 0, ctaBottom, rowW, ctaH);
                emotesAt = Node(bottomWrap, "Emotes place"); Put(emotesAt, bottomMid, new Vector2(.5f, 0), 0, ctaBottom + ctaH + space, rowW, eh);
            }
            else
            {
                float bottom = 70;
                ctaAt = Node(bottomWrap, "Next place"); Put(ctaAt, new Vector2(0, 0), new Vector2(0, 0), colX, bottom, colW, ctaH);
                emotesAt = Node(bottomWrap, "Emotes place"); Put(emotesAt, new Vector2(0, 0), new Vector2(0, 0), colX, bottom + ctaH + space, colW, eh);
            }
            // NEXT HOLE: a lime slab with the hole coming up and a countdown
            Color nextInk = clear ? ThemeService.Current.buttonText : Ink;
            next = Club.Slab(ctaAt, "Next hole", clear ? GlassKit.Gold : Lime, clear ? UiKit.Hex("C99A1C") : LimeDeep, ctaH / 2, out var face, portrait ? 14 : 12);
            var nextRt = (RectTransform)next.transform; nextRt.anchorMin = Vector2.zero; nextRt.anchorMax = Vector2.one; nextRt.offsetMin = nextRt.offsetMax = Vector2.zero;
            // the label over the hole that is coming up over the countdown, each in its own band of the slab
            bool detail = !string.IsNullOrEmpty(data.NextDetail);
            float subBand = detail ? (portrait ? 46 : 38) : 0, barBand = portrait ? 34 : 28;
            nextLabelText = Label(face, "Label", data.NextLabel + "  ▸", UiKit.Display, portrait ? 62 : 50, nextInk);
            nextLabelText.rectTransform.offsetMin = new Vector2(0, subBand + barBand); nextLabelText.rectTransform.offsetMax = new Vector2(0, -4);
            if (detail)
            {
                var sub = Label(face, "Next hole", data.NextDetail, clear ? UiKit.Display : UiKit.Strong, portrait ? 32 : 26, new Color(nextInk.r, nextInk.g, nextInk.b, .78f));
                sub.rectTransform.offsetMin = new Vector2(0, barBand); sub.rectTransform.offsetMax = new Vector2(0, -(ctaH - barBand - subBand));
                Icons.Fit(sub, 14, portrait ? 32 : 26);
            }
            var track = Rounded(face, "Countdown track", new Color(0, 0, 0, .16f), 6);
            track.rectTransform.anchorMin = new Vector2(.08f, 0); track.rectTransform.anchorMax = new Vector2(.92f, 0); track.rectTransform.pivot = new Vector2(.5f, 0);
            track.rectTransform.sizeDelta = new Vector2(0, 9); track.rectTransform.anchoredPosition = new Vector2(0, portrait ? 16 : 13);
            countdownFill = Rounded(track.transform, "Time left", nextInk, 6);
            countdownFill.rectTransform.anchorMin = Vector2.zero; countdownFill.rectTransform.anchorMax = Vector2.one; countdownFill.rectTransform.offsetMin = countdownFill.rectTransform.offsetMax = Vector2.zero;
            next.Pressed = () => proceed?.Invoke();
            FocusItem.Mark(next, true);
            // the emotes: three outlined pills the golfer performs on the spot
            emoteFade = emotesAt.gameObject.AddComponent<CanvasGroup>();
            float ew = (emotesAt.rect.width - gap * (n - 1)) / Mathf.Max(1, n);
            for (int i = 0; i < n; i++)
            {
                int choice = i;
                var b = Club.Slab(emotesAt, "Emote " + (i + 1), clear ? GlassKit.Gold : new Color(.03f, .1f, .18f, .62f), clear ? UiKit.Hex("C99A1C") : new Color(0, 0, 0, .3f), eh / 2, out var ef, 8);
                var brt = (RectTransform)b.transform; Put(brt, topLeft, topLeft, i * (ew + gap), 0, ew, eh);
                Rounded(ef, "Ring", clear ? Color.white : new Color(1, 1, 1, .6f), eh / 2, true);
                Label(ef, "Name", data.Emotes[i].ToUpperInvariant(), UiKit.Display, portrait ? 32 : 26, clear ? nextInk : Color.white);
                b.Pressed = () => emote?.Invoke(choice);
                FocusItem.Mark(b, false);
            }
        }
    }
}
