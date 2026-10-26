using System.Collections.Generic;
using GolfArcade.Course;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// The screen between two holes. Building the next hole takes a few seconds of the main thread, so the game puts this
    /// up first, lets it be drawn, and only then builds. It is the MotionSports venue loading screen (picked 2026-10-25, the
    /// same design as the app's match loading): the course's key art, the hole that is coming (HOLE 3 OF 9, its name, what to
    /// do on it, par, length and what is in the way), a GOLF TIP card, and the bar with what is being done and how far, so the
    /// wait has a clear end. It covers the whole display (an overlay canvas on the display the course camera draws to, so the
    /// TV gets it as well as the phone).
    public sealed class HoleLoadingCover : MonoBehaviour
    {
        public struct Info
        {
            public Hole Hole;
            public string Course, Name, Blurb;
            /// The hole's place in its round (1 for the first), how many holes the round has, par and length in yards.
            public int Ordinal, Count, Par;
            public double Yards;
        }

        public const float FadeIn = 0.14f, FadeOut = 0.32f;
        /// Each tip stays this long before the second one comes up (seconds, unscaled).
        const float TipSeconds = 4f;
        /// Golf's colour on the bar and the percentage (the app's match loading uses the same).
        static Color Accent => BrandColors.Success;

        /// A few of the app's loading tips (GameTips.golf in HowToCards.swift, word for word), with their card headlines.
        static readonly (string title, string text)[] Tips =
        {
            ("Smooth tempo", "Smooth tempo, a square face and a committed swing together earn a PERFECT strike."),
            ("Read the wind", "Check the wind arrow and MPH badge before you pick a club, and aim off for a strong crosswind."),
            ("Backswing sets distance", "How far back you take the phone sets the distance: hip-high is about 60%, up behind you is full power."),
            ("Smooth beats hard", "You don't have to swing hard. A smooth, committed swing through the ball carries full distance."),
            ("Shape your shot", "Twisting the phone open or closed bends the ball: open slices right, closed hooks left."),
            ("Play it safe", "Water and lava cost a stroke. Play short of trouble with a safer club."),
            ("Club up in the rough", "Rough takes 10–15% off your swing. Take one more club than the yardage says."),
            ("Escape the sand", "Bunkers rob most clubs of about 40% of their speed. Take a wedge and just get out."),
            ("Read the break", "On the green, the beads on the slope grid drift the way the ball will break. Read them before you putt."),
            ("Tiny putts", "Putting uses tiny strokes. A 3-foot putt is only about a fifth of a full putting stroke."),
            ("Free do-overs", "Tap the button again, or stop short on the way through, and the swing resets with no stroke lost. Tap it and go again."),
            ("Give yourself room", "Clear a full swing's room around you, and keep the phone in a firm grip."),
        };

        Camera view;
        Canvas canvas;
        CanvasScaler scaler;
        CanvasGroup group;
        RectTransform root, artFrame, wordmark, header, holeTab, chips, card, cardTab, phoneIcon, barRoot, track, fill, sparkle, ring, ringArc;
        RawImage art;
        AspectRatioFitter artFit;
        GradientGraphic topShade, bottomShade;
        Text motion, sports, holeTabText, title, objective, tipTab, tipTitle, tipText, status, percent;
        bool portraitBuilt = true, laidOut, cardLeft = true;
        float shownAt = -1, hideAt = -1, shown, target, progress, lastWidth, lastHeight;
        int tipShown = -1;
        bool visible;
        Info info;
        static readonly Dictionary<string, Texture2D> arts = new();
        static Sprite star, ringSprite;

        /// Up on screen, or fading out.
        public bool Visible => visible || group.alpha > 0.001f;
        /// The cover is fully opaque: nothing under it can be seen, so the game may stall.
        public bool Opaque => visible && group.alpha >= 0.999f;
        /// Seconds it has been up (unscaled), 0 when it is not.
        public float ShownFor => visible && shownAt >= 0 ? Time.unscaledTime - shownAt : 0;
        public float Progress => progress;
        public string Status => status ? status.text : "";
        public string Title => title ? title.text : "";
        public string Number => info.Ordinal > 0 ? info.Ordinal.ToString() : "";

        public static HoleLoadingCover Create(Camera camera)
        {
            var go = new GameObject("Hole loading cover", typeof(RectTransform));
            var canvas = UiKit.Canvas(go);
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 500;
            canvas.targetDisplay = camera ? camera.targetDisplay : 0;
            var c = go.AddComponent<HoleLoadingCover>();
            c.view = camera; c.canvas = canvas; c.scaler = go.GetComponent<CanvasScaler>();
            c.Build();
            go.SetActive(false);
            return c;
        }

        // ---- Type (Kanit when the brand kit's TTFs are in; the club fonts slanted stand in until then)

        static Font Display => BrandFonts.ExtraBoldItalic(UiKit.Display);
        static Font Subline => BrandFonts.MediumItalic(UiKit.Strong);
        static Font Body => BrandFonts.Medium(UiKit.Body);

        static Text Words(Transform parent, string name, Font face, int size, Color color, TextAnchor anchor, bool loud, bool shadow = true)
        {
            var t = Club.Words(parent, name, "", face, size, color, anchor);
            if (loud && BrandFonts.Missing) t.fontStyle = FontStyle.Italic;
            if (shadow) { var s = t.gameObject.AddComponent<Shadow>(); s.effectColor = new Color(BrandColors.TextShadow.r, BrandColors.TextShadow.g, BrandColors.TextShadow.b, .55f); s.effectDistance = new Vector2(0, -Mathf.Max(2, size / 24f)); }
            return t;
        }

        // ---- Building

        static RectTransform Node(Transform parent, string name)
        {
            var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
            rt.SetParent(parent, false);
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
            return rt;
        }

        static Image Rounded(Transform parent, string name, Color color, float radius, bool ring = false)
        {
            var img = Club.Paint(parent, name, color, radius, ring); img.raycastTarget = false; return img;
        }

        /// A brand panel: a Shadow Ink drop shadow, a white border and the fill inset by it.
        static void Panel(RectTransform rt, Color fill, float radius, float border, float drop)
        {
            var shade = Rounded(rt, "Shadow", new Color(BrandColors.ShadowInk.r, BrandColors.ShadowInk.g, BrandColors.ShadowInk.b, .43f), radius);
            shade.rectTransform.offsetMin = new Vector2(0, -drop); shade.rectTransform.offsetMax = new Vector2(0, -drop);
            if (border > 0) Rounded(rt, "Border", Color.white, radius);
            var face = Rounded(rt, "Fill", fill, Mathf.Max(1, radius - border));
            face.rectTransform.offsetMin = Vector2.one * border; face.rectTransform.offsetMax = -Vector2.one * border;
        }

        void Build()
        {
            group = gameObject.AddComponent<CanvasGroup>();
            root = Club.Fill(transform, "Cover");
            // the brand's navy-to-royal field, the course's key art over it, darker at the top and bottom for the type
            var back = Club.Fill(root, "Back").gameObject.AddComponent<GradientGraphic>(); back.Vertical = true; back.raycastTarget = true;
            back.Stops = new[] { BrandColors.NavyInk, BrandColors.NavyDeep, UiKit.Hex("0B2C86") };
            artFrame = Club.Fill(root, "Art frame"); artFrame.gameObject.AddComponent<RectMask2D>();
            art = Club.Fill(artFrame, "Art").gameObject.AddComponent<RawImage>(); art.raycastTarget = false;
            artFit = art.gameObject.AddComponent<AspectRatioFitter>(); artFit.aspectMode = AspectRatioFitter.AspectMode.EnvelopeParent;
            topShade = Club.Fill(root, "Top shade").gameObject.AddComponent<GradientGraphic>(); topShade.Vertical = true; topShade.raycastTarget = false;
            topShade.Stops = new[] { Ink(.5f), Ink(0) };
            bottomShade = Club.Fill(root, "Bottom shade").gameObject.AddComponent<GradientGraphic>(); bottomShade.Vertical = true; bottomShade.raycastTarget = false;

            // MotionSports: white Motion, Wordmark Gold Sports
            wordmark = Node(root, "Wordmark");
            motion = Words(wordmark, "Motion", Display, 52, Color.white, TextAnchor.MiddleLeft, true);
            sports = Words(wordmark, "Sports", Display, 52, BrandColors.GoldWordmark, TextAnchor.MiddleLeft, true);
            motion.text = "Motion"; sports.text = "Sports";
            foreach (var t in new[] { motion, sports }) { t.horizontalOverflow = HorizontalWrapMode.Overflow; t.rectTransform.anchorMin = t.rectTransform.anchorMax = new Vector2(0, .5f); t.rectTransform.pivot = new Vector2(0, .5f); }

            // the hole: HOLE 3 OF 9 · CLIFFSIDE on a gold tab, its name, what to do on it, par / yards / hazards
            header = Node(root, "Hole");
            holeTab = Node(header, "Tab");
            Rounded(holeTab, "Rim", Color.white, 40);
            var tabFill = Rounded(holeTab, "Fill", BrandColors.Gold, 37); tabFill.rectTransform.offsetMin = Vector2.one * 3; tabFill.rectTransform.offsetMax = -Vector2.one * 3;
            holeTabText = Words(holeTab, "Words", Display, 26, BrandColors.NavyInk, TextAnchor.MiddleCenter, true, false);
            title = Words(header, "Name", Display, 96, Color.white, TextAnchor.UpperLeft, true);
            title.horizontalOverflow = HorizontalWrapMode.Overflow;
            objective = Words(header, "Objective", Subline, 34, BrandColors.N100, TextAnchor.UpperLeft, true);
            chips = Node(header, "Chips");

            // GOLF TIP 1/2: the phone, a headline in gold and one line of how to play
            card = Node(root, "Tip");
            Panel(card, UiKit.Hex("15389A"), 24, 6, 16);
            phoneIcon = Node(card, "Phone");
            Rounded(phoneIcon, "Tile", BrandColors.Lift, 18);
            Rounded(phoneIcon, "Rim", new Color(1, 1, 1, .35f), 18, true);
            // a phone: a white body with the tile's blue as its screen
            var handset = Node(phoneIcon, "Handset"); handset.anchorMin = handset.anchorMax = handset.pivot = new Vector2(.5f, .5f); handset.sizeDelta = new Vector2(36, 60);
            Rounded(handset, "Body", Color.white, 10);
            var screen = Rounded(handset, "Screen", BrandColors.Lift, 5);
            screen.rectTransform.offsetMin = new Vector2(5, 9); screen.rectTransform.offsetMax = new Vector2(-5, -9);
            tipTitle = Words(card, "Headline", Display, 46, BrandColors.Gold, TextAnchor.UpperLeft, true);
            tipTitle.horizontalOverflow = HorizontalWrapMode.Overflow;
            tipText = Words(card, "Tip", Body, 32, Color.white, TextAnchor.UpperLeft, false, false);
            cardTab = Node(card, "Tab");
            Rounded(cardTab, "Rim", Color.white, 30);
            var cardTabFill = Rounded(cardTab, "Fill", BrandColors.Gold, 28); cardTabFill.rectTransform.offsetMin = Vector2.one * 3; cardTabFill.rectTransform.offsetMax = -Vector2.one * 3;
            tipTab = Words(cardTab, "Words", Display, 22, BrandColors.NavyInk, TextAnchor.MiddleCenter, true, false);

            // the bar: what is being done and how far, a white-rimmed pill filled in golf green with a sparkle at its head,
            // and a short arc chasing round a faint ring (the brand's loading, never a spinner)
            barRoot = Node(root, "Loading");
            status = Words(barRoot, "Status", Display, 38, Color.white, TextAnchor.LowerLeft, true);
            status.horizontalOverflow = HorizontalWrapMode.Overflow;
            percent = Words(barRoot, "Percent", Display, 38, Accent, TextAnchor.LowerRight, true);
            track = Node(barRoot, "Track");
            Rounded(track, "Shadow", new Color(BrandColors.ShadowInk.r, BrandColors.ShadowInk.g, BrandColors.ShadowInk.b, .43f), 30).rectTransform.anchoredPosition = new Vector2(0, -8);
            Rounded(track, "Rim", Color.white, 30);
            var trackFill = Rounded(track, "Inside", BrandColors.NavyInk, 26); trackFill.rectTransform.offsetMin = Vector2.one * 4; trackFill.rectTransform.offsetMax = -Vector2.one * 4;
            fill = Node(track, "Fill");
            Rounded(fill, "Colour", Accent, 20);
            var shine = Rounded(fill, "Shine", new Color(1, 1, 1, .32f), 10);
            shine.rectTransform.anchorMin = new Vector2(0, .55f); shine.rectTransform.offsetMin = new Vector2(8, 0); shine.rectTransform.offsetMax = new Vector2(-8, -3);
            sparkle = Node(track, "Sparkle"); sparkle.anchorMin = sparkle.anchorMax = new Vector2(0, .5f); sparkle.pivot = new Vector2(.5f, .5f);
            var halo = Rounded(sparkle, "Glow", new Color(BrandColors.Gold.r, BrandColors.Gold.g, BrandColors.Gold.b, .85f), 0); halo.sprite = Club.Glow; halo.type = Image.Type.Simple;
            halo.rectTransform.offsetMin = -Vector2.one * 14; halo.rectTransform.offsetMax = Vector2.one * 14;
            var starImage = Rounded(sparkle, "Star", Color.white, 0); starImage.sprite = Star; starImage.type = Image.Type.Simple;
            ring = Node(root, "Ring"); ring.anchorMin = ring.anchorMax = ring.pivot = new Vector2(.5f, .5f);
            var faint = Rounded(ring, "Faint", new Color(1, 1, 1, .18f), 0); faint.sprite = RingSprite; faint.type = Image.Type.Simple;
            ringArc = Club.Fill(ring, "Arc");
            var arc = ringArc.gameObject.AddComponent<Image>(); arc.raycastTarget = false; arc.sprite = RingSprite;
            arc.type = Image.Type.Filled; arc.fillMethod = Image.FillMethod.Radial360; arc.fillOrigin = (int)Image.Origin360.Top; arc.fillAmount = .34f; arc.fillClockwise = false;
            arc.color = BrandColors.ArcWarm;
        }

        static Color Ink(float a) => new(BrandColors.NavyInk.r, BrandColors.NavyInk.g, BrandColors.NavyInk.b, a);

        /// The 4-point sparkle at the head of the swing arc (and of the bar).
        static Sprite Star => star ? star : (star = MakeStar(96));
        static Sprite RingSprite => ringSprite ? ringSprite : (ringSprite = MakeRing(96, 6));

        static Sprite MakeStar(int n)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float dx = Mathf.Abs((x + .5f) / n * 2 - 1), dy = Mathf.Abs((y + .5f) / n * 2 - 1);
                    // a concave diamond: |x|^.5 + |y|^.5 <= 1, with a soft edge
                    float d = Mathf.Sqrt(dx) + Mathf.Sqrt(dy);
                    float a = Mathf.Clamp01((1f - d) * n * .25f) + Mathf.Clamp01(1 - Mathf.Sqrt(dx * dx + dy * dy) * 7f);
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * Mathf.Clamp01(a)));
                }
            tex.SetPixels32(px); tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f));
        }

        static Sprite MakeRing(int n, float thickness)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[n * n];
            float r = n / 2f - 1, inner = r - thickness;
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float d = Mathf.Sqrt((x + .5f - n / 2f) * (x + .5f - n / 2f) + (y + .5f - n / 2f) * (y + .5f - n / 2f));
                    float a = Mathf.Clamp01(r - d + .5f) * Mathf.Clamp01(d - inner + .5f);
                    px[y * n + x] = new Color32(255, 255, 255, (byte)(255 * a));
                }
            tex.SetPixels32(px); tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f));
        }

        /// The course's key art (Resources/Loading/loading-golf-<course>), or nothing (the brand field shows).
        static Texture2D ArtFor(string course)
        {
            string name = (course ?? "").ToLowerInvariant();
            string key = name.Contains("magma") ? "magma" : name.Contains("wild") ? "wildisles" : "cliffside";
            if (!arts.TryGetValue(key, out var tex)) arts[key] = tex = Resources.Load<Texture2D>("Loading/loading-golf-" + key);
            return tex;
        }

        // ---- Layout

        bool Portrait => !view || (OffscreenSize.Override is Vector2Int o ? o.x < o.y * 1.2f : view.aspect < 1.2f);

        /// Lays the screen out against the surface it is being drawn to now (for the offscreen captures).
        public void RefreshLayout() { if (gameObject.activeInHierarchy) Layout(); }

        static void Put(RectTransform rt, Vector2 anchor, Vector2 pivot, float x, float y, float w, float h)
        {
            rt.anchorMin = rt.anchorMax = anchor; rt.pivot = pivot; rt.anchoredPosition = new Vector2(x, y); rt.sizeDelta = new Vector2(w, h);
        }

        static void Place(Text t, float x, float y, float w, float h)
        {
            var rt = t.rectTransform; rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = new Vector2(x, y); rt.sizeDelta = new Vector2(w, h);
        }

        /// How tall `t` is set `width` wide, in canvas units.
        static float TallAt(Text t, float width)
        {
            var settings = t.GetGenerationSettings(new Vector2(width, 0));
            return t.cachedTextGeneratorForLayout.GetPreferredHeight(t.text, settings) / Mathf.Max(.01f, t.pixelsPerUnit);
        }

        void Layout()
        {
            bool portrait = Portrait;
            float width = view ? OffscreenSize.Width(view) : Screen.width, height = view ? OffscreenSize.Height(view) : Screen.height;
            float scale = Mathf.Max(.1f, portrait ? width / 1080f : height / 1080f);
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize;
            scaler.scaleFactor = scale; canvas.scaleFactor = scale;
            canvas.targetDisplay = view ? view.targetDisplay : 0;
            lastWidth = width; lastHeight = height;
            float H = height / scale, W = width / scale;
            float safeTop = 0;
            if (view && view.targetDisplay == 0 && !view.targetTexture && OffscreenSize.Override == null) safeTop = Mathf.Max(0, Screen.height - Screen.safeArea.yMax) / scale;
            laidOut = true; portraitBuilt = portrait;
            var topLeft = new Vector2(0, 1); var topRight = new Vector2(1, 1); var bottomLeft = new Vector2(0, 0);

            // the wordmark's two halves side by side
            int markSize = portrait ? 46 : 52;
            motion.fontSize = sports.fontSize = markSize;
            float mw = motion.preferredWidth, sw = sports.preferredWidth;
            motion.rectTransform.anchoredPosition = Vector2.zero; motion.rectTransform.sizeDelta = new Vector2(mw + 4, markSize * 1.4f);
            sports.rectTransform.anchoredPosition = new Vector2(mw, 0); sports.rectTransform.sizeDelta = new Vector2(sw + 8, markSize * 1.4f);

            float headerWidth = portrait ? W - 120 : Mathf.Min(1150, W - 240);
            holeTabText.fontSize = portrait ? 26 : 26;
            float tabWidth = holeTabText.preferredWidth + 56;
            Put(holeTab, topLeft, topLeft, 0, 0, tabWidth, 54);
            title.fontSize = portrait ? 88 : 96; Icons.Fit(title, 48, title.fontSize);
            Place(title, -4, -62, headerWidth, title.fontSize * 1.25f);
            objective.fontSize = portrait ? 34 : 34;
            float objectiveTall = string.IsNullOrEmpty(objective.text) ? 0 : TallAt(objective, headerWidth);
            Place(objective, 0, -62 - title.fontSize * 1.2f, headerWidth, objectiveTall + 8);
            float chipsY = -62 - title.fontSize * 1.2f - objectiveTall - 22;
            ArrangeChips(portrait);
            Put(chips, topLeft, topLeft, 0, chipsY, headerWidth, 64);
            float headerTall = -chipsY + 64;

            if (portrait)
            {
                float artH = Mathf.Round(H * .42f);
                artFrame.anchorMin = new Vector2(0, 1); artFrame.anchorMax = new Vector2(1, 1); artFrame.pivot = new Vector2(.5f, 1);
                artFrame.anchoredPosition = Vector2.zero; artFrame.sizeDelta = new Vector2(0, artH);
                Put(topShade.rectTransform, new Vector2(.5f, 1), new Vector2(.5f, 1), 0, 0, W, 360);
                // the art fades into the navy field under it, where the hole's name sits
                Put(bottomShade.rectTransform, new Vector2(.5f, 1), new Vector2(.5f, 1), 0, -(artH - 420), W, 422);
                bottomShade.Stops = new[] { Ink(0), new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, .85f), BrandColors.NavyDeep };
                Put(wordmark, new Vector2(.5f, 1), new Vector2(.5f, 1), 0, -(safeTop + 70), mw + sw, markSize * 1.4f);
                // the name over the foot of the art, what to do and the chips under it, then the tip
                float headerTop = artH - (62 + title.fontSize * 1.2f) - 30;
                Put(header, topLeft, topLeft, 60, -headerTop, headerWidth, headerTall);
                LayoutCard(topLeft, topLeft, 60, -(headerTop + headerTall + 70), W - 120, true);
                Put(barRoot, bottomLeft, bottomLeft, 60, 130, W - 120 - 90, 120);
                Put(ring, bottomLeft, new Vector2(.5f, .5f), W - 60 - 32, 130 + 14 + 15, 60, 60);
            }
            else
            {
                artFrame.anchorMin = Vector2.zero; artFrame.anchorMax = Vector2.one; artFrame.pivot = new Vector2(.5f, .5f);
                artFrame.anchoredPosition = Vector2.zero; artFrame.sizeDelta = Vector2.zero;
                Put(topShade.rectTransform, new Vector2(.5f, 1), new Vector2(.5f, 1), 0, 0, W, 520);
                Put(bottomShade.rectTransform, new Vector2(.5f, 0), new Vector2(.5f, 0), 0, 0, W, 520);
                bottomShade.Stops = new[] { Ink(0), Ink(.8f) };
                Put(wordmark, topRight, topRight, -120, -(56 + safeTop), mw + sw, markSize * 1.4f);
                Put(header, topLeft, topLeft, 120, -(56 + safeTop), headerWidth, headerTall);
                float cardWidth = Mathf.Min(980, W * .5f);
                LayoutCard(cardLeft ? topLeft : topRight, cardLeft ? topLeft : topRight, cardLeft ? 195 : -195, -Mathf.Max(560, 56 + headerTall + 90), cardWidth, false);
                Put(barRoot, bottomLeft, bottomLeft, 195, 100, W - 195 * 2 - 30, 130);
                Put(ring, bottomLeft, new Vector2(.5f, .5f), W - 195 + 30, 100 + 14 + 16, 66, 66);
            }
            // the bar's pieces: the words over the track
            status.fontSize = percent.fontSize = portrait ? 36 : 38;
            status.rectTransform.anchorMin = new Vector2(0, 1); status.rectTransform.anchorMax = new Vector2(1, 1); status.rectTransform.pivot = new Vector2(0, 1);
            status.rectTransform.anchoredPosition = Vector2.zero; status.rectTransform.sizeDelta = new Vector2(-140, 60);
            percent.rectTransform.anchorMin = percent.rectTransform.anchorMax = percent.rectTransform.pivot = new Vector2(1, 1);
            percent.rectTransform.anchoredPosition = Vector2.zero; percent.rectTransform.sizeDelta = new Vector2(160, 60);
            track.anchorMin = new Vector2(0, 0); track.anchorMax = new Vector2(1, 0); track.pivot = new Vector2(.5f, 0);
            track.anchoredPosition = new Vector2(0, 14); track.sizeDelta = new Vector2(0, portrait ? 30 : 32);
            sparkle.sizeDelta = Vector2.one * (portrait ? 68 : 74);
            ApplyProgress(shown);
        }

        void LayoutCard(Vector2 anchor, Vector2 pivot, float x, float y, float cardWidth, bool portrait)
        {
            float icon = portrait ? 96 : 100, pad = portrait ? 34 : 36, gap = 30;
            tipTitle.fontSize = portrait ? 46 : 48; Icons.Fit(tipTitle, 30, tipTitle.fontSize);
            tipText.fontSize = portrait ? 32 : 32;
            float textWidth = cardWidth - pad * 2 - icon - gap;
            float bodyTall = TallAt(tipText, textWidth);
            float cardTall = Mathf.Max(icon + pad * 2, 42 + tipTitle.fontSize * 1.2f + 8 + bodyTall + pad);
            Put(card, anchor, pivot, x, y, cardWidth, cardTall);
            Put(phoneIcon, new Vector2(0, .5f), new Vector2(0, .5f), pad, 0, icon, icon);
            Place(tipTitle, pad + icon + gap, -42, textWidth, tipTitle.fontSize * 1.25f);
            Place(tipText, pad + icon + gap, -42 - tipTitle.fontSize * 1.2f - 8, textWidth, bodyTall + 6);
            Put(cardTab, topLeft2, new Vector2(0, .5f), 28, 0, tipTab.preferredWidth + 44, 46);
        }
        static readonly Vector2 topLeft2 = new(0, 1);

        void ArrangeChips(bool portrait)
        {
            foreach (Transform child in chips) { child.gameObject.SetActive(false); Destroy(child.gameObject); }
            float h = 64, size = 30, pad = 30, x = 0;
            void Chip(string text, Color fill)
            {
                var rt = Node(chips, "Chip"); rt.anchorMin = rt.anchorMax = new Vector2(0, .5f); rt.pivot = new Vector2(0, .5f);
                Panel(rt, fill, 32, 3, 6);
                var t = Words(rt, "Text", Display, (int)size, Color.white, TextAnchor.MiddleCenter, true, false);
                t.horizontalOverflow = HorizontalWrapMode.Overflow; t.text = text;
                float w = t.preferredWidth + 2 * pad;
                rt.sizeDelta = new Vector2(w, h); rt.anchoredPosition = new Vector2(x, 0);
                x += w + 14;
            }
            Chip($"PAR {info.Par}", BrandColors.NavyDeep);
            Chip($"{info.Yards:F0} YD", BrandColors.NavyDeep);
            if (info.Hole != null)
            {
                int wet = 0, sand = 0; bool lava = false;
                foreach (var hz in info.Hole.Hazards)
                {
                    if (hz.Kind == HazardKind.Water || hz.Kind == HazardKind.Lava) { wet++; lava |= hz.Kind == HazardKind.Lava; }
                    else if (hz.Kind == HazardKind.Bunker) sand++;
                }
                if (wet > 0) Chip($"{wet} {(lava ? "LAVA" : "WATER")}", lava ? UiKit.Hex("B5341B") : BrandColors.Bright);
                else if (sand > 0) Chip($"{sand} BUNKER{(sand > 1 ? "S" : "")}", UiKit.Hex("A07818"));
            }
        }

        // ---- Showing

        /// Up over everything, fading in over 0.14 s; progress starts again from nothing.
        public void Show(Info next)
        {
            info = next;
            gameObject.SetActive(true);
            canvas.targetDisplay = view ? view.targetDisplay : 0;
            var picture = ArtFor(info.Course);
            art.texture = picture; art.enabled = picture;
            if (picture) artFit.aspectRatio = (float)picture.width / Mathf.Max(1, picture.height);
            holeTabText.text = info.Count > 1 ? $"HOLE {info.Ordinal} OF {info.Count}  ·  {(info.Course ?? "").ToUpperInvariant()}" : $"HOLE {info.Ordinal}  ·  {(info.Course ?? "").ToUpperInvariant()}";
            title.text = info.Name ?? "";
            objective.text = ObjectiveOf(info.Blurb);
            status.text = "Packing the clubs…";
            // the card sits left on odd holes and right on even ones, so a round does not look the same every time
            cardLeft = info.Ordinal % 2 == 1;
            tipShown = -1; ShowTip(0);
            progress = target = 0; shown = 0;
            laidOut = false; Layout();
            visible = true; shownAt = Time.unscaledTime; hideAt = -1;
            group.alpha = 0; group.blocksRaycasts = true; group.interactable = true;
            SetFade(0);
        }

        /// The load's first or second tip (two per hole, a different pair every hole).
        void ShowTip(int which)
        {
            if (which == tipShown) return;
            tipShown = which;
            var tip = Tips[((Mathf.Max(1, info.Ordinal) - 1) * 2 + which) % Tips.Length];
            tipTab.text = $"GOLF TIP {which + 1}/2";
            tipTitle.text = tip.title; tipText.text = tip.text;
            if (laidOut) Layout();
        }

        /// What to do on the hole, from its blurb: "A par 4 down a clifftop: carry the inlet…" gives "Carry the inlet…".
        static string ObjectiveOf(string blurb)
        {
            if (string.IsNullOrEmpty(blurb)) return "";
            int colon = blurb.IndexOf(':');
            string s = colon > 0 && colon < blurb.Length - 12 ? blurb.Substring(colon + 1).Trim() : blurb;
            return char.ToUpperInvariant(s[0]) + s.Substring(1);
        }

        /// Where the loading has got to (0 to 1) and what is being done; the bar eases to it.
        public void SetProgress(float to, string what)
        {
            target = Mathf.Max(target, Mathf.Clamp01(to));
            if (!string.IsNullOrEmpty(what) && status.text != what) status.text = what;
        }

        /// Fades out over a third of a second (at once with `instant`), and the screen is gone.
        public void Hide(bool instant = false)
        {
            if (!visible) return;
            visible = false; hideAt = Time.unscaledTime;
            if (instant) { group.alpha = 0; gameObject.SetActive(false); }
        }

        void SetFade(float a) { group.alpha = a; group.blocksRaycasts = a > 0.01f; }

        void ApplyProgress(float p)
        {
            progress = p;
            if (!track) return;
            float inset = 6, inner = Mathf.Max(0, track.rect.width - inset * 2), h = track.rect.height - inset * 2;
            float w = Mathf.Max(h, inner * Mathf.Clamp01(p));
            fill.anchorMin = new Vector2(0, 0); fill.anchorMax = new Vector2(0, 1); fill.pivot = new Vector2(0, .5f);
            fill.anchoredPosition = new Vector2(inset, 0); fill.sizeDelta = new Vector2(w, -inset * 2);
            sparkle.anchoredPosition = new Vector2(inset + w, 0);
            percent.text = $"{Mathf.RoundToInt(Mathf.Clamp01(p) * 100)}%";
        }

        void Update()
        {
            float now = Time.unscaledTime;
            if (visible || hideAt >= 0)
            {
                float width = view ? OffscreenSize.Width(view) : Screen.width, height = view ? OffscreenSize.Height(view) : Screen.height;
                if (Portrait != portraitBuilt || !Mathf.Approximately(lastWidth, width) || !Mathf.Approximately(lastHeight, height)) Layout();
            }
            if (visible)
            {
                SetFade(Mathf.Clamp01((now - shownAt) / FadeIn));
                float ease = 1 - Mathf.Exp(-5f * Time.unscaledDeltaTime);
                shown = Mathf.Lerp(shown, target, ease);
                ApplyProgress(shown);
                ShowTip(Mathf.FloorToInt((now - shownAt) / TipSeconds) % 2);
                ringArc.localRotation = Quaternion.Euler(0, 0, -(now % 1.1f) / 1.1f * 360f);
                sparkle.localScale = Vector3.one * (.92f + .08f * Mathf.Sin(now * 6f));
            }
            else if (hideAt >= 0)
            {
                float u = Mathf.Clamp01((now - hideAt) / FadeOut);
                SetFade(1 - u * u * (3 - 2 * u));
                if (u >= 1) { hideAt = -1; gameObject.SetActive(false); }
            }
        }
    }
}
