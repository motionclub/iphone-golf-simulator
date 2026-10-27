using System.Collections.Generic;
using GolfArcade.UI;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Bowling
{
    /// The bowling TV HUD in the MotionSports brand (MotionSports_Brand_Guide.pdf §3–§10):
    ///   * the score sheet as the brand HUD score plate: Deep Navy at 92 % with a 5 px white
    ///     border, a gold pill title tab, Navy Ink wells for the frames, HUD labels in Neutral 300,
    ///     the leader's total in Gold, the bowler marked with a gold dot;
    ///   * result banners in the praise tiers: STRIKE!/TURKEY! gold Display with a Deep Navy
    ///     outline, 5-step chunk shadow, a swing arc drawing on over the word and two sparkles,
    ///     popping 0.6 → 1.12 → 1.0 in 0.45 s; SPARE! gold with a small arc; counts white; FOUL red;
    ///   * the ball speed as a HUD number on a small plate.
    /// Kanit comes from BrandFonts (the club fonts stand in until the brand kit's TTFs are added).
    /// Rendered by the game camera (screen-space camera) so captures include it.
    public sealed class BowlingHud
    {
        public enum Praise { Good, Nice, Big, Bad }

        static readonly Vector2 Reference = new Vector2(1920, 1080);
        const float RowHeight = 92, Left = 40, Top = 30, PlateWidth = 1840, CellWidth = 132, TenthWidth = 186;
        readonly RectTransform root;
        readonly List<Row> rows = new List<Row>();
        readonly RectTransform banner;
        readonly Text bannerText, sub, status, speedNumber;
        readonly Text[] chunk = new Text[5];
        readonly Image arc;
        readonly RectTransform[] sparkles = new RectTransform[2];
        readonly GameObject speedPlate;
        float bannerAt = -10, bannerUntil = -10;
        Praise tier;

        static Font Display => BrandFonts.ExtraBoldItalic(UiKit.Display);
        static Font HudNumber => BrandFonts.ExtraBold(UiKit.Display);
        static Font HudLabel => BrandFonts.SemiBold(UiKit.Ui);
        static Font Body => BrandFonts.Medium(UiKit.Body);
        static Font Subline => BrandFonts.MediumItalic(UiKit.Strong);
        static Font Heading => BrandFonts.BoldItalic(UiKit.Strong);

        sealed class Row
        {
            public Text name, total;
            public Image dot;
            public Text[,] marks = new Text[10, 3];
            public Text[] cumulative = new Text[10];
        }

        static readonly Vector2 TopLeft = new Vector2(0, 1);

        Text Label(Transform parent, string name, Font font, float size, Color color, TextAnchor anchor, Vector2 anchorAt, Vector2 pos, Vector2 box, bool shadow = true)
        {
            var t = UiKit.Label(parent, name, Mathf.RoundToInt(size), anchor, anchorAt, anchorAt, pos, box, font, false);
            t.color = color;
            if (shadow) { var s = t.gameObject.AddComponent<Shadow>(); s.effectColor = BrandColors.TextUnderlay; s.effectDistance = new Vector2(0, -Mathf.Max(1, size / 40)); }
            return t;
        }

        /// A brand panel: the Shadow Ink drop shadow, a white border, the fill inset by the border.
        /// `pos` is the corner given by the anchor (UiKit pivots on its anchor). Returns all three.
        static GameObject[] Plate(Transform parent, string name, Vector2 anchorAt, Vector2 pos, Vector2 size, Color fill, float border = 5)
        {
            var shadow = UiKit.Panel(parent, name + "Shadow", BrandColors.Shadow, anchorAt, anchorAt, pos + new Vector2(0, -12), size);
            var edge = UiKit.Panel(parent, name + "Border", BrandColors.White, anchorAt, anchorAt, pos, size);
            var inset = new Vector2(anchorAt.x > .5f ? -border : border, anchorAt.y > .5f ? -border : border);
            var inner = UiKit.Panel(parent, name, fill, anchorAt, anchorAt, pos + inset, size - Vector2.one * border * 2);
            return new[] { shadow.gameObject, edge.gameObject, inner.gameObject };
        }

        readonly CanvasScaler scaler; readonly Camera hudCamera;

        public BowlingHud(Camera camera, IList<string> players)
        {
            var go = new GameObject("BowlingHud");
            var canvas = go.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = camera; canvas.planeDistance = .5f;
            scaler = go.AddComponent<CanvasScaler>(); hudCamera = camera;
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = Reference; scaler.matchWidthOrHeight = .5f;
            root = (RectTransform)go.transform;

            // --- the score plate
            float plateHeight = 52 + players.Count * RowHeight + 14;
            Plate(root, "ScorePlate", TopLeft, new Vector2(Left, -Top), new Vector2(PlateWidth, plateHeight), new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, .92f));            // gold pill title tab on the top-left edge
            UiKit.Panel(root, "TitleTab", BrandColors.Gold, TopLeft, TopLeft, new Vector2(Left + 28, -Top + 20), new Vector2(230, 40));
            Label(root, "TitleTabText", Display, 26, BrandColors.NavyInk, TextAnchor.MiddleCenter, TopLeft, new Vector2(Left + 28, -Top + 20), new Vector2(230, 40), false).text = BowlingVenue.Title;
            for (int f = 0; f < 10; f++)
                Label(root, "FrameNo", HudLabel, BrandType.HudLabel, BrandColors.N300, TextAnchor.MiddleCenter, TopLeft, new Vector2(CellX(f), -Top - 16), new Vector2(f == 9 ? TenthWidth : CellWidth, 30), false).text = (f + 1).ToString();
            Label(root, "TotalLabel", HudLabel, BrandType.HudLabel, BrandColors.N300, TextAnchor.MiddleRight, TopLeft, new Vector2(Left + PlateWidth - 180, -Top - 16), new Vector2(150, 30), false).text = "TOTAL";
            for (int p = 0; p < players.Count; p++) rows.Add(BuildRow(players[p], p));

            // --- status line and the speed plate
            status = Label(root, "Status", Body, BrandType.Body, BrandColors.White, TextAnchor.LowerLeft, Vector2.zero, new Vector2(48, 40), new Vector2(1300, 50));
            var speedAt = new Vector2(1, 0);
            speedPlate = new GameObject("SpeedGroup", typeof(RectTransform));
            var group = (RectTransform)speedPlate.transform;
            group.SetParent(root, false); group.anchorMin = Vector2.zero; group.anchorMax = Vector2.one; group.offsetMin = group.offsetMax = Vector2.zero;
            Plate(group, "SpeedPlate", speedAt, new Vector2(-40, 34), new Vector2(300, 110), new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, .92f));
            speedNumber = Label(group, "SpeedNumber", HudNumber, BrandType.HudNumber, BrandColors.Gold, TextAnchor.MiddleRight, speedAt, new Vector2(-148, 44), new Vector2(190, 92));
            Label(group, "SpeedLabel", HudLabel, BrandType.HudLabel, BrandColors.N300, TextAnchor.MiddleLeft, speedAt, new Vector2(-58, 52), new Vector2(80, 40), false).text = "MPH";
            Speed(0);

            // --- the result banner: arc + chunk-shadowed gold word + sparkles, and a subline
            var center = new Vector2(.5f, .5f);
            banner = new GameObject("Banner", typeof(RectTransform)).GetComponent<RectTransform>();
            banner.SetParent(root, false); banner.anchorMin = banner.anchorMax = center; banner.anchoredPosition = new Vector2(0, 70); banner.sizeDelta = new Vector2(1400, 360);
            arc = new GameObject("Arc", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            arc.rectTransform.SetParent(banner, false); arc.rectTransform.sizeDelta = new Vector2(1000, 330); arc.rectTransform.anchoredPosition = new Vector2(0, 40);
            var arcTex = BowlingClubLanes.ArcTexture(1024, 340, Color.clear, 200, 345, .028f, false);
            arc.sprite = Sprite.Create(arcTex, new Rect(0, 0, arcTex.width, arcTex.height), new Vector2(.5f, .5f));
            arc.type = Image.Type.Filled; arc.fillMethod = Image.FillMethod.Horizontal; arc.fillOrigin = 0;
            for (int i = chunk.Length - 1; i >= 0; i--)
            {
                // 5-step Deep Navy chunk shadow, down and to the right
                chunk[i] = Label(banner, "Chunk" + i, Display, BrandType.Display, BrandColors.NavyDeep, TextAnchor.MiddleCenter, center, new Vector2((i + 1) * 2.5f, -(i + 1) * 2.5f), new Vector2(1400, 180), false);
            }
            bannerText = Label(banner, "Word", Display, BrandType.Display, BrandColors.Gold, TextAnchor.MiddleCenter, center, Vector2.zero, new Vector2(1400, 180), false);
            var outline = bannerText.gameObject.AddComponent<Outline>(); outline.effectColor = BrandColors.NavyDeep; outline.effectDistance = new Vector2(3, -3);
            var drop = chunk[chunk.Length - 1].gameObject.AddComponent<Shadow>(); drop.effectColor = BrandColors.Shadow; drop.effectDistance = new Vector2(0, -16);
            var sparkle = Sparkle();
            for (int i = 0; i < 2; i++)
            {
                var s = new GameObject("Sparkle" + i, typeof(RectTransform), typeof(Image)).GetComponent<Image>();
                s.rectTransform.SetParent(banner, false); s.sprite = sparkle;
                s.rectTransform.sizeDelta = Vector2.one * (i == 0 ? 90 : 56);
                s.rectTransform.anchoredPosition = i == 0 ? new Vector2(470, 150) : new Vector2(-520, -40);
                sparkles[i] = s.rectTransform;
            }
            sub = Label(root, "Subline", Subline, 48, BrandColors.White, TextAnchor.MiddleCenter, center, new Vector2(0, -60), new Vector2(1400, 70));
            var subPlate = sub.gameObject.AddComponent<Outline>(); subPlate.effectColor = BrandColors.TextUnderlay; subPlate.effectDistance = new Vector2(2, -2);
            Banner(null, null, 0, Praise.Good);
        }

        static float CellX(int f) => Left + 300 + f * (CellWidth + 8);

        /// A 4-point white sparkle with a soft glow (brand guide §7: the head of the arc on contact).
        static Sprite Sparkle()
        {
            const int n = 128;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, true) { name = "Sparkle" };
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float u = (x + .5f) / n * 2 - 1, v = (y + .5f) / n * 2 - 1;
                    float star = Mathf.Max(Mathf.Clamp01(1 - Mathf.Abs(u) * 14) * Mathf.Clamp01(1 - Mathf.Abs(v)), Mathf.Clamp01(1 - Mathf.Abs(v) * 14) * Mathf.Clamp01(1 - Mathf.Abs(u)));
                    float glow = Mathf.Pow(Mathf.Clamp01(1 - Mathf.Sqrt(u * u + v * v)), 3) * .6f;
                    float a = Mathf.Clamp01(Mathf.Pow(star, .7f) + glow);
                    px[y * n + x] = new Color(1, 1, 1, a);
                }
            tex.SetPixels(px); tex.Apply(true);
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f));
        }

        Row BuildRow(string player, int index)
        {
            var r = new Row();
            float top = -Top - 40 - index * RowHeight;
            r.dot = UiKit.Panel(root, "BowlerDot", BrandColors.Gold, TopLeft, TopLeft, new Vector2(Left + 26, top - 36), new Vector2(16, 16));
            r.name = Label(root, "Name", Heading, 40, BrandColors.White, TextAnchor.MiddleLeft, TopLeft, new Vector2(Left + 52, top - 4), new Vector2(240, RowHeight - 8));
            r.name.text = player;
            for (int f = 0; f < 10; f++)
            {
                float x = CellX(f), w = f == 9 ? TenthWidth : CellWidth;
                UiKit.Panel(root, "Well", BrandColors.NavyInk, TopLeft, TopLeft, new Vector2(x, top - 4), new Vector2(w, RowHeight - 12));
                int balls = f == 9 ? 3 : 2;
                for (int b = 0; b < balls; b++)
                    r.marks[f, b] = Label(root, "Mark", HudNumber, 36, BrandColors.White, TextAnchor.MiddleCenter, TopLeft, new Vector2(x + w - (balls - b) * 42 - 4, top - 6), new Vector2(40, 36), false);
                r.cumulative[f] = Label(root, "Cum", HudNumber, 34, BrandColors.White, TextAnchor.MiddleCenter, TopLeft, new Vector2(x, top - 40), new Vector2(w, 42), false);
            }
            r.total = Label(root, "Total", HudNumber, 56, BrandColors.White, TextAnchor.MiddleRight, TopLeft, new Vector2(Left + PlateWidth - 180, top - 2), new Vector2(150, RowHeight - 8));
            return r;
        }

        public void Score(int player, BowlingScore s, bool current)
        {
            var r = rows[player];
            r.dot.enabled = current;
            for (int f = 0; f < 10; f++)
            {
                for (int b = 0; b < (f == 9 ? 3 : 2); b++)
                {
                    string m = s.Mark(f, b);
                    r.marks[f, b].text = m;
                    r.marks[f, b].color = m == "F" ? BrandColors.Error : m == "X" ? BrandColors.Gold : BrandColors.White;
                }
                var c = s.Cumulative(f);
                r.cumulative[f].text = c.HasValue ? c.Value.ToString() : "";
            }
            r.total.text = s.Total.ToString();
        }

        /// The leader's total is gold, the rest white (brand HUD score plate).
        public void Leader(int player)
        {
            for (int i = 0; i < rows.Count; i++) rows[i].total.color = i == player ? BrandColors.Gold : BrandColors.White;
        }

        /// A result banner. Big: STRIKE!-class (gold, arc, sparkles). Nice: SPARE! (gold, small arc).
        /// Good: counts and misses (white, no arc). Bad: FOUL/OOPS (Error Coral, no arc).
        public void Banner(string word, string subline, float seconds, Praise praise)
        {
            tier = praise;
            bannerText.text = word ?? "";
            foreach (var c in chunk) c.text = word ?? "";
            bannerText.color = praise == Praise.Good ? BrandColors.White : praise == Praise.Bad ? BrandColors.Error : BrandColors.Gold;
            sub.text = subline ?? "";
            bannerAt = Time.unscaledTime; bannerUntil = Time.unscaledTime + seconds;
            banner.gameObject.SetActive(!string.IsNullOrEmpty(word));
            sub.gameObject.SetActive(!string.IsNullOrEmpty(subline));
            arc.gameObject.SetActive(praise == Praise.Big || praise == Praise.Nice);
            arc.rectTransform.localScale = praise == Praise.Nice ? new Vector3(.62f, .62f, 1) : Vector3.one;
            foreach (var s in sparkles) s.gameObject.SetActive(praise == Praise.Big);
            Tick();
        }

        public void Dispose() { if (root) Object.Destroy(root.gameObject); }

        public void Status(string text) => status.text = text;

        /// Ball speed in mph (0 hides the plate).
        public void Speed(float mph)
        {
            speedPlate.SetActive(mph > 0);
            speedNumber.text = mph.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture);
        }

        public void Tick()
        {
            // a phone held upright (bowling with no TV): fit the TV layout's width, so the score sheet spans the top of the screen
            if (hudCamera) scaler.matchWidthOrHeight = hudCamera.aspect < 1 ? 0 : .5f;
            float now = Time.unscaledTime;
            if (now > bannerUntil) { banner.gameObject.SetActive(false); sub.gameObject.SetActive(false); return; }
            // pop 0.6 → 1.12 → 1.0 in 0.45 s (overshoot); the arc draws on over the same time
            float t = (now - bannerAt) / BrandMotion.Banner;
            banner.localScale = Vector3.one * Mathf.LerpUnclamped(.6f, 1f, BrandMotion.Overshoot(t));
            arc.fillAmount = BrandMotion.EaseOut(t);
            for (int i = 0; i < sparkles.Length; i++)
            {
                float tw = Mathf.Clamp01((t - .6f - i * .25f) * 2.5f);
                float pulse = tw * (.75f + .25f * Mathf.Sin((now - bannerAt) * 9 + i * 2));
                sparkles[i].localScale = Vector3.one * pulse;
                sparkles[i].localRotation = Quaternion.Euler(0, 0, (now - bannerAt) * 40 * (i == 0 ? 1 : -1));
            }
            float fade = Mathf.Clamp01((bannerUntil - now) / .2f);
            sub.color = new Color(1, 1, 1, fade);
        }
    }
}
