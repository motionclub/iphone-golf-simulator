using System;
using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// One thing the pointer can press: its hit area, the face that scales when hovered / pressed, and what it does.
    public sealed class MenuItem
    {
        public string id, label; public RectTransform hit, face; public Action activate; public bool enabled = true; public float radius;
        public bool Visible => hit && hit.gameObject.activeInHierarchy;
        /// The hover look (menu mock 10-28): called with the eased hover amount 0..1 while it changes; null = the old focus ring.
        public Action<float> glow; public float lit;
        /// Its stack: when one entry is lit the others dim (`dim`).
        public List<MenuItem> group; public Action<bool> dim; internal object view;
    }

    /// The pointer menu's TV half (PLAN_PointerMenu.md, Brand Guide v1.0): one overlay canvas at 1920×1080 drawn over the plaza
    /// line-up. Screens: Home, Sport, Modes (tennis / golf / bowling), Locker, Clubhouse and Loading; tabs PLAZA · LOCKER · CLUBHOUSE are the
    /// roots and Back pops toward them. The phone's pointer (or a finger on a phone with no TV) drives a cursor; hovering lights an item,
    /// Select presses it. Detail screens that live on the phone (mode options, the course picker, the full locker, settings, invites)
    /// open there: the TV shows "Finish on your phone" until the phone closes them. Only the party leader drives; guests' TVs follow.
    public sealed partial class MenuHud : MonoBehaviour
    {
        public const string Home = "home", Sport = "sport", TennisModes = "modes:tennis", GolfModes = "modes:golf", BowlingModes = "modes:bowling", Locker = "locker", Clubhouse = "clubhouse", Loading = "loading",
            Setup = "setup", Players = "players";
        public const float WipeSeconds = .36f;
        /// Phone-bound events: (type, message) — the session emits them on the bridge.
        public event Action<string, string> Event;

        HubWorld world; MenuStage stage;
        Canvas canvas; CanvasScaler scaler; RectTransform canvasRT, chrome, screensRoot, plates, fx, scrims;
        readonly Dictionary<string, RectTransform> screens = new Dictionary<string, RectTransform>();
        readonly Dictionary<string, List<MenuItem>> screenItems = new Dictionary<string, List<MenuItem>>();
        readonly List<MenuItem> chromeItems = new List<MenuItem>();
        RectTransform tabBar, backButton, phoneModal, joinSeat, nameChip, hint; MenuItem joinItem; Text phoneModalTitle, nameChipText; Image phoneScreen;
        readonly List<(MenuItem item, string screen, Text label, RectTransform underline)> tabs = new List<(MenuItem, string, Text, RectTransform)>();

        /// A nested canvas: what moves every frame (plates, the cursor, the focus ring) re-batches only itself, not every screen.
        static void SubCanvas(RectTransform r, int order)
        {
            var c = r.gameObject.AddComponent<Canvas>(); c.overrideSorting = true; c.sortingOrder = 29990 + order;
        }

        /// The screen up now.
        public string Screen { get; private set; } = Home;
        public string Hovered => hovered != null ? hovered.id : "";
        /// This TV's phone drives the menu (no party, or the party's leader). Guests' TVs follow the leader (Mirror).
        public bool Leader { get; private set; } = true;
        public bool SoloLocked { get; private set; }
        public bool PhonePanelOpen => phoneOpen;
        public int ScreenChanges { get; private set; }
        /// The menu's canvas (proof captures draw it with their own camera).
        public Canvas Canvas => canvas;

        public static MenuHud Attach(HubWorld world, MenuStage stage)
        {
            var h = world.gameObject.GetComponent<MenuHud>(); if (!h) h = world.gameObject.AddComponent<MenuHud>();
            h.world = world; h.stage = stage; h.Build();
            return h;
        }

        // ================================================================== build
        void Build()
        {
            if (canvas) return;
            var go = new GameObject("Menu HUD", typeof(RectTransform)); go.transform.SetParent(transform, false);
            canvas = go.AddComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay; canvas.sortingOrder = 29990;
            scaler = go.AddComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080); scaler.matchWidthOrHeight = .5f;
            // everything sits in one 16:9 frame: the whole TV, or (no TV) the band at the top of the phone the plaza draws in
            canvasRT = BrandUi.Fill(go.transform, "Frame");
            scrims = BrandUi.Fill(canvasRT, "Scrims"); BuildScrims();
            screensRoot = BrandUi.Fill(canvasRT, "Screens");
            plates = BrandUi.Fill(canvasRT, "Name plates"); SubCanvas(plates, 1);
            chrome = BrandUi.Fill(canvasRT, "Chrome");
            fx = BrandUi.Fill(canvasRT, "FX"); SubCanvas(fx, 3);
            BuildChrome();
            BuildScreen(Home, BuildHome); BuildScreen(Sport, BuildSport); BuildScreen(TennisModes, r => BuildModes(r, "tennis"));
            BuildScreen(GolfModes, r => BuildModes(r, "golf")); BuildScreen(BowlingModes, r => BuildModes(r, "bowling")); BuildScreen(Locker, BuildLocker); BuildScreen(Clubhouse, BuildClubhouse);
            BuildScreen(Loading, BuildLoading); BuildScreen(Setup, BuildSetup); BuildScreen(Players, BuildPlayers);
            BuildPhoneModal(); BuildPlates(); BuildCursor(); BuildWipe();
            StyleModes();   // the mode cards exist before the first visit (building them on entry was a 27 ms frame)
            PrewarmGlyphs();
            Show(Home, snap: true);
        }

        void BuildScreen(string id, Action<RectTransform> build)
        {
            var root = BrandUi.Fill(screensRoot, "Screen " + id); screens[id] = root; screenItems[id] = new List<MenuItem>();
            var group = root.gameObject.AddComponent<CanvasGroup>(); group.interactable = false; group.blocksRaycasts = false; groups[id] = group;
            buildingFor = id; build(root); buildingFor = null;
            root.gameObject.SetActive(false);
        }
        string buildingFor;
        readonly Dictionary<string, CanvasGroup> groups = new Dictionary<string, CanvasGroup>();

        MenuItem Item(RectTransform hit, RectTransform face, string id, string label, Action activate, float radius)
        {
            var it = new MenuItem { id = id, label = label, hit = hit, face = face, activate = activate, radius = radius };
            if (buildingFor != null) screenItems[buildingFor].Add(it); else chromeItems.Add(it);
            return it;
        }

        // the left / right scrims (mock .scrim): ink .86 → .6 → clear over the left 40 %, clear → .55 → .8 over the right 40 %;
        // the words left and the pop-ups right read over any venue, the hero in the middle is untouched
        void BuildScrims()
        {
            BrandUi.Ramp(scrims, "Left", 0, 500, BrandUi.Ink(.86f), BrandUi.Ink(.6f));
            BrandUi.Ramp(scrims, "Left fade", 500, 268, BrandUi.Ink(.6f), BrandUi.Ink(0));
            BrandUi.Ramp(scrims, "Right fade", 1152, 307, BrandUi.Ink(0), BrandUi.Ink(.55f));
            BrandUi.Ramp(scrims, "Right", 1459, 461, BrandUi.Ink(.55f), BrandUi.Ink(.8f));
            // and a soft band under the top bar
            var top = BrandUi.Box(scrims, "Top", 0, 0, 1920, 150).gameObject.AddComponent<Image>(); top.raycastTarget = false;
            top.rectTransform.anchorMax = new Vector2(1, 1); top.rectTransform.offsetMin = new Vector2(0, -150); top.rectTransform.offsetMax = Vector2.zero;
            GolfArcade.Tennis.UiGradient.On(top, BrandUi.Ink(.5f), BrandUi.Ink(0));
        }

        void BuildChrome()
        {
            // the bar (mock .bar, 5.6cqw): wordmark, PLAZA · LOCKER · CLUBHOUSE as words (the active one white on a gold skewed underline),
            // the player's name and settings as small skewed chips top right
            var mark = BrandUi.Wordmark(chrome, Left, 26, 46);
            tabBar = BrandUi.Box(chrome, "Tabs", 0, 0, 1920, 108);
            string[] names = { "PLAZA", "LOCKER", "CLUBHOUSE" }; string[] go = { Home, Locker, Clubhouse };
            float x = Left + mark.preferredWidth + 50;
            for (int i = 0; i < 3; i++)
            {
                var box = BrandUi.Box(tabBar, names[i], x, 22, 10, 64);
                var face = BrandUi.Fill(box, "Face");
                var label = BrandUi.Word(BrandUi.Box(face, "Label", 12, 0, 10, 64), "Text", names[i], BrandUi.BoldItalic, 28, BrandUi.WhiteA(.62f));
                float w = label.preferredWidth + 24; box.sizeDelta = new Vector2(w, 64);
                var ul = BrandUi.Box(face, "Underline", 4, 50, w - 8, 6); BrandUi.Slant(ul, "Gold", BrandColors.Gold, 20); ul.pivot = new Vector2(0, .5f);
                ul.anchoredPosition = new Vector2(4, -53); ul.localScale = new Vector3(0, 1, 1);
                string target = go[i];
                var item = Item(box, face, "tab-" + target, names[i], () => Go(target), 0);
                item.glow = k => { if (Active(target)) return; ul.localScale = new Vector3(k, 1, 1); label.color = BrandUi.WhiteA(Mathf.Lerp(.62f, 1, k)); };
                tabs.Add((item, target, label, ul));
                x += w + 22;
            }
            var gear = BrandUi.Chip(chrome, "Settings", RightEdge - 66, 30, 66, 50);
            var gearFace = BrandUi.Fill(gear, "Face");
            var glyph = BrandUi.Layer(BrandUi.Box(gearFace, "Gear", 19, 10, 30, 30), "Glyph", BrandColors.White, 0, -1, BrandUi.Gear); glyph.preserveAspect = true;
            var gearItem = Item(gear, gearFace, "desk-settings", "Settings", () => OpenPhone("desk-settings", "Settings"), 0);
            gearItem.glow = k => glyph.color = Color.Lerp(BrandColors.White, BrandColors.Gold, k);
            nameChip = BrandUi.Chip(chrome, "Name", RightEdge - 66 - 18 - 160, 30, 160, 50);
            nameChipText = BrandUi.Word(BrandUi.Box(nameChip, "Name", 22, 0, 10, 50), "Text", "", BrandUi.SemiBold, 24, BrandColors.White);
            SetChipName(localName);

            // the hint (mock .hint) in place of the BACK pill: Ⓐ SELECT  Ⓑ BACK; the B half is still the pointer's back item
            hint = BrandUi.Box(chrome, "Hint", Left, 990, 600, 64);
            BrandUi.FaceButton(hint, "A", 0, 14, 36, BrandColors.White, BrandColors.NavyInk);
            var select = BrandUi.Word(BrandUi.Box(hint, "Select", 46, 0, 10, 64), "Text", "SELECT", BrandUi.SemiBold, 24, BrandUi.WhiteA(.8f));
            backButton = BrandUi.Box(hint, "Back", 46 + select.preferredWidth + 22, 0, 10, 64);
            var backFace = BrandUi.Fill(backButton, "Face");
            BrandUi.FaceButton(backFace, "B", 10, 14, 36, BrandColors.White, BrandColors.NavyInk);
            var backLabel = BrandUi.Word(BrandUi.Box(backFace, "Label", 56, 0, 10, 64), "Text", "BACK", BrandUi.SemiBold, 24, BrandUi.WhiteA(.8f));
            backButton.sizeDelta = new Vector2(56 + backLabel.preferredWidth + 14, 64);
            var backItem = Item(backButton, backFace, "back", "Back", () => Back(), 0);
            backItem.glow = k => backLabel.color = Color.Lerp(BrandUi.WhiteA(.8f), BrandColors.Gold, k);

            // the empty seat: "+ JOIN" beside the line-up (a dark skewed tile, white edge; gold when lit)
            joinSeat = BrandUi.Box(chrome, "Join", 0, 0, 104, 140);
            var joinFace = BrandUi.Box(joinSeat, "Face", 0, 0, 104, 104);
            var joinEdge = BrandUi.Slant(joinFace, "Edge", BrandUi.WhiteA(.7f), 10);
            BrandUi.Slant(joinFace, "Fill", BrandUi.Ink(.62f), 10, 4);
            BrandUi.Layer(joinFace, "Plus", BrandColors.White, 30, -1, BrandUi.Plus).preserveAspect = true;
            BrandUi.Word(BrandUi.Box(joinSeat, "Label", -40, 110, 184, 32), "Text", "JOIN", BrandUi.SemiBold, BrandType.Caption, BrandColors.White, TextAnchor.MiddleCenter);
            joinItem = Item(joinSeat, joinFace, "board-invite", "Invite friends", () => OpenPhone("board-invite", "Invite friends"), 0);
            joinItem.glow = k => joinEdge.color = Color.Lerp(BrandUi.WhiteA(.7f), BrandColors.Gold, k);
        }
        bool Active(string tab) => tab == (Screen == Locker ? Locker : Screen == Clubhouse ? Clubhouse : Home);
        void SetChipName(string name)
        {
            if (!nameChipText) return;
            name = (name ?? "").ToUpperInvariant();
            if (nameChipText.text == name) return;
            nameChipText.text = name;
            float w = nameChipText.preferredWidth + 44;
            nameChip.sizeDelta = new Vector2(w, 50); nameChip.anchoredPosition = new Vector2(RightEdge - 66 - 18 - w, -30);
        }

        void BuildHome(RectTransform r)
        {
            // one big stack (mock home): PLAY with its sports under it, then Invite friends — words, no boxes
            var group = new List<MenuItem>();
            float h = WordItem(r, "play", "PLAY", "PLAY NOW", "TENNIS · GOLF · BOWLING", Left, 250, BigSize, () => Go(Sport), group, minW: 480, big: true);
            WordItem(r, "board-invite", "INVITE FRIENDS", "INVITE FRIENDS", "Game Center or a party code", Left, 250 + h + 8, WordSize, () => OpenPhone("board-invite", "Invite friends"), group);
        }

        // ---- Sport: no flat field over the plaza any more (10-28): a dim, and three tall skewed lanes with each sport's venue art; the
        // hovered lane widens (flex 1 → 2.1), lights its picture and shows its modes
        const float LaneTop = 340, LaneH = 613, LaneGap = 25, LaneSkew = 8;
        sealed class SportLane { public MenuItem item; public RectTransform box, name, maps; public RawImage pic; public Image frame; public ChipRow chips; public RectTransform chipsRoot; public float k; }
        readonly List<SportLane> lanes = new List<SportLane>();
        void BuildSport(RectTransform r)
        {
            BrandUi.Layer(r, "Dim", BrandUi.Ink(.45f));
            BrandUi.Headline(r, Left, 118, "Play", "Pick a sport", 900, TextAnchor.UpperLeft, 80);
            AddLane(r, "sport-tennis", "Tennis", "RESORT · SKY TOWER · MAGMA CRATER", new[] { "EXHIBITION", "TRAINING", "LOCAL", "ONLINE" }, "tennis-resort", () => Go(TennisModes));
            AddLane(r, "sport-golf", "Golf", "CLIFFSIDE · WILD ISLES · MAGMA OPEN", new[] { "ROUND", "LOCAL", "ONLINE" }, "golf-cliffside", () => Go(GolfModes));
            AddLane(r, "sport-bowling", "Bowling", "CLUB · NEON · TIKI · MAGMA", new[] { "PLAY", "EXHIBITION", "LOCAL", "ONLINE" }, "bowling-neon", () => Go(BowlingModes));
            LayoutLanes();
        }
        void AddLane(RectTransform r, string id, string title, string maps, string[] modes, string art, Action go)
        {
            var l = new SportLane();
            l.box = BrandUi.Box(r, title, Left, LaneTop, 580, LaneH);
            var face = BrandUi.Fill(l.box, "Face");
            var shadow = BrandUi.Skewed(BrandUi.DropShadow(face, 0), LaneSkew); shadow.color = BrandUi.Ink(.5f);
            l.frame = BrandUi.Slant(face, "Frame", BrandUi.WhiteA(.22f), LaneSkew, -4);
            var (mask, pic) = PictureCard(face, LaneSkew, false, .35f);
            l.pic = pic; pic.texture = Resources.Load<Texture2D>("Menu/Maps/" + art);
            // words bottom-left, upright (the mock counter-skews them): the venues, the sport (scaled, not re-sized: no new glyph sizes), the modes
            l.chipsRoot = BrandUi.Box(mask, "Modes", 64, LaneH - 36 - 34, 900, 34);
            l.chips = Chips(l.chipsRoot, 0, 0, 34, modes.Length); l.chips.Set(modes);
            l.name = BrandUi.Word(BrandUi.Box(mask, "Sport", 0, 0, 800, 120), "Text", title, BrandUi.ExtraBoldItalic, 116, BrandColors.White, TextAnchor.LowerLeft).rectTransform.parent as RectTransform;
            l.name.anchorMin = l.name.anchorMax = Vector2.zero; l.name.pivot = Vector2.zero;
            l.maps = BrandUi.Word(BrandUi.Box(mask, "Venues", 0, 0, 900, 28), "Text", maps, BrandUi.SemiBold, 22, BrandColors.Gold).rectTransform.parent as RectTransform;
            l.maps.anchorMin = l.maps.anchorMax = Vector2.zero; l.maps.pivot = Vector2.zero;
            l.item = Item(l.box, face, id, title, go, 0);
            l.item.glow = k => { l.k = k; LayoutLanes(); };
            lanes.Add(l);
        }
        void LayoutLanes()
        {
            float sum = 0; foreach (var l in lanes) sum += 1 + 1.1f * l.k;
            float total = RightEdge - Left - (lanes.Count - 1) * LaneGap, x = Left;
            foreach (var l in lanes)
            {
                float w = total * (1 + 1.1f * l.k) / sum;
                l.box.anchoredPosition = new Vector2(x, -LaneTop); l.box.sizeDelta = new Vector2(w, LaneH);
                x += w + LaneGap;
                Cover(l.pic, w + 2 * (Mathf.Tan(LaneSkew * Mathf.Deg2Rad) * LaneH / 2 + 4), LaneH);
                var tint = Color.Lerp(new Color(.66f, .66f, .7f), Color.white, l.k); if (l.pic.color != tint) l.pic.color = tint;
                var edge = l.k > .35f ? BrandColors.Gold : BrandUi.WhiteA(.22f); if (l.frame.color != edge) l.frame.color = edge;
                // the sport's name grows 4.2cqw → 6cqw as it widens (by scale), the venues ride on top of it
                float s = Mathf.Lerp(.7f, 1f, l.k), bottom = 36 + 34 + 14;
                l.name.localScale = new Vector3(s, s, 1); l.name.anchoredPosition = new Vector2(52, bottom);
                l.maps.anchoredPosition = new Vector2(60, bottom + 120 * s + 10);
                bool modes = l.k > .5f; if (l.chipsRoot.gameObject.activeSelf != modes) l.chipsRoot.gameObject.SetActive(modes);
            }
        }

        readonly Dictionary<string, (MenuItem item, string label, string sub, bool solo)> modeRows = new Dictionary<string, (MenuItem, string, string, bool)>();
        void BuildModes(RectTransform r, string sport)
        {
            bool tennis = sport == "tennis", bowling = sport == "bowling";
            BrandUi.Headline(r, Left, 132, tennis ? "Tennis" : bowling ? "Bowling" : "Golf", "Pick a mode", 720);
            var rows = bowling
                ? new[] { ("bay-bowling-play", "PLAY", "Four venues · 10 frames", true), ("bay-bowling-exhibition", "EXHIBITION", "Bowl against the computer", true), ("bay-bowling-pass", "LOCAL PLAY", "Same room · one phone, up to 4 players", true), ("bay-bowling-online", "ONLINE", "Play friends online", false) }
                : tennis
                ? new[] { ("bay-tennis-exhibition", "EXHIBITION", "Custom match vs the CPU", true), ("bay-tennis-training", "TRAINING", "Rally with the coach", true), ("bay-tennis-nearby", "LOCAL PLAY", "Same room · two phones, one TV", true), ("bay-tennis-online", "ONLINE", "Play friends online", false) }
                : new[] { ("bay-golf-round", "ROUND", "Play a course, 9 or 18 holes", true), ("bay-golf-pass", "LOCAL PLAY", "Same room · one phone, passed around", true), ("bay-golf-online", "ONLINE", "Play friends online", false) };
            var group = new List<MenuItem>(); float y = ListTop;
            for (int i = 0; i < rows.Length; i++)
            {
                var (id, label, sub, solo) = rows[i];
                string key = id, name = label;
                y += WordItem(r, id, label, label, sub, Left, y, WordSize, () => OpenMode(key, Title(name)), group) + 6;
                modeRows[id] = (group[group.Count - 1], label, sub, solo);
            }
            BuildPreview(r, sport);
        }
        /// (Re)words the mode list: with the party here the solo modes lock (dim, "play online") and Online is the way on.
        void StyleModes()
        {
            foreach (var kv in modeRows)
            {
                var (item, label, sub, solo) = kv.Value;
                bool locked = SoloLocked && solo;
                if (!(item.view is Word w)) continue;
                string want = locked ? "Your party is here: play online" : sub;
                if (w.off == locked && w.sub.text == want) continue;
                w.off = locked; w.sub.text = want; item.enabled = !locked;
                FitWord(item); w.Paint();
            }
        }
        static string Title(string upper) => upper.Length == 0 ? upper : upper.Substring(0, 1) + upper.Substring(1).ToLowerInvariant();

        // ---- Locker: the camera closes on your hero; colours on the TV (live), the rest on the phone
        static readonly (string name, string hex)[] Palette =
        {
            ("Kit", ""), ("White", "F2F2F0"), ("Sky", "3FA9F5"), ("Navy", "1E2A6E"), ("Lime", "9EE63A"), ("Sun", "FFC233"), ("Coral", "FF6B4A"),
            ("Crimson", "E0243C"), ("Violet", "8A4FFF"), ("Teal", "1FB5A8"), ("Pink", "FF5FA2"), ("Charcoal", "2E3138"), ("Sand", "E3CFA4"),
        };   // = Outfit.palette (SportProgress.swift), plus the kit's own colour
        static readonly (string id, string label, string slot, string route, string title)[] LockerRail =
        {
            ("lk-shirt", "SHIRT", "shirt", null, "Shirt colour"), ("lk-shorts", "SHORTS", "shorts", null, "Shorts colour"), ("lk-shoes", "SHOES", "accent", null, "Shoe colour"),
            ("lk-racket", "RACKET", "racket", null, "Racket colour"), ("rack-club", "CLUBS", null, "rack-club", "Golf gear"), ("look-mirror", "MIRROR", null, "look-mirror", "Skin, body and hand"),
            ("emote-mirror", "EMOTES", null, "emote-mirror", "Emotes"),
        };
        string lockerSlot = "shirt"; Text swatchKicker, swatchTitle; readonly Dictionary<string, string> look = new Dictionary<string, string> { { "shirt", "" }, { "shorts", "" }, { "accent", "" }, { "racket", "" } };
        sealed class Swatch { public MenuItem item; public RectTransform art; public GameObject ring; public string hex; public bool on; public float k; public void Size() { float s = Mathf.Max(on ? 1.08f : 1, 1 + .1f * k); art.localScale = new Vector3(s, s, 1); } }
        readonly List<Swatch> swatches = new List<Swatch>();
        readonly List<(MenuItem item, Word word, string slot)> rail = new List<(MenuItem, Word, string)>();
        void BuildLocker(RectTransform r)
        {
            BrandUi.Headline(r, Left, 132, "Locker", "Your look", 720);
            // the slots as a word rail (mock .rail, 2.3cqw); the ones that open on the phone say so
            var group = new List<MenuItem>(); float y = ListTop;
            for (int i = 0; i < LockerRail.Length; i++)
            {
                var (id, label, slot, route, title) = LockerRail[i];
                string s = slot, rt = route, t = Title(label);
                y += WordItem(r, id, label, t, null, Left, y, RailSize, () => { if (s != null) SelectSlot(s); else OpenPhone(rt, t); }, group, phone: route != null) + 4;
                rail.Add((group[group.Count - 1], (Word)group[group.Count - 1].view, slot));
            }
            // big skewed swatches right of the hero (mock .swatches: 5 across, the picked one gold-ringed and up 8 %)
            const float X = 1336, W = 520, Cell = 90, Gap = 17;
            swatchKicker = BrandUi.Word(BrandUi.Box(r, "Kicker", X, 326, W, 30), "Text", "SHIRT", BrandUi.SemiBold, 24, BrandColors.Gold);
            swatchTitle = BrandUi.Word(BrandUi.Box(r, "Title", X, 358, W, 64), "Text", "Shirt colour", BrandUi.ExtraBoldItalic, 54, BrandColors.White);
            for (int i = 0; i < Palette.Length; i++)
            {
                var (name, hex) = Palette[i];
                int col = i % 5, row = i / 5;
                var box = BrandUi.Box(r, name, X + 6 + col * (Cell + Gap), 446 + row * (Cell + Gap), Cell, Cell);
                var face = BrandUi.Fill(box, "Face");
                var sw = new Swatch { hex = hex };
                var ring = BrandUi.Fill(face, "Ring"); sw.ring = ring.gameObject;
                BrandUi.Slant(ring, "Gold", BrandColors.Gold, 10, -10); BrandUi.Slant(ring, "Gap", BrandUi.Ink(.85f), 10, -5);
                sw.art = BrandUi.Fill(face, "Art");
                BrandUi.Skewed(BrandUi.DropShadow(sw.art, 0), 10).color = BrandUi.Ink(.35f);
                BrandUi.Slant(sw.art, "Edge", BrandUi.WhiteA(.4f), 10);
                BrandUi.Slant(sw.art, "Colour", hex.Length == 0 ? BrandUi.Ink(.75f) : BrandColors.FromHex("#" + hex), 10, 3);
                if (hex.Length == 0) BrandUi.Word(sw.art, "Kit", "KIT", BrandUi.ExtraBold, 24, BrandColors.White, TextAnchor.MiddleCenter);
                string h = hex;
                sw.item = Item(box, face, "swatch-" + name.ToLowerInvariant(), name, () => PickColour(h), 0);
                sw.item.glow = k => { sw.k = k; sw.Size(); };
                swatches.Add(sw);
            }
            SelectSlot("shirt");
        }
        void SelectSlot(string slot)
        {
            lockerSlot = slot;
            foreach (var (item, word, s) in rail) { bool on = s == slot && s != null; if (word.picked != on) { word.picked = on; word.Paint(); } }
            foreach (var (id, label, s, _, title) in LockerRail) if (s == slot) { swatchKicker.text = label; swatchTitle.text = title; }
            RefreshSwatches();
        }
        void RefreshSwatches()
        {
            look.TryGetValue(lockerSlot, out var cur); cur = (cur ?? "").TrimStart('#').ToUpperInvariant();
            foreach (var sw in swatches) { sw.on = sw.hex == cur; sw.ring.SetActive(sw.on); sw.Size(); }
        }
        void PickColour(string hex)
        {
            if (!Leader) return;
            look[lockerSlot] = hex; RefreshSwatches();
            // live on the TV hero now; the phone saves it to the player and sends the look back (hubLook)
            var p = world ? world.Player : null;
            if (p && p.look)
            {
                if (lockerSlot == "racket") p.look.SetRacketColour(hex.Length > 0 ? GolfArcade.Tennis.HeroKit.Hex(hex) : new Color(0, 0, 0, 0));
                else p.look.SetKit(look["shirt"], look["shorts"], look["accent"]);
            }
            Send("menuLook", lockerSlot + "|" + hex);
        }
        /// The player's look as the phone has it (start / hubLook): the swatches show what is on.
        public void SetLook(string shirt, string shorts, string accent, string racket)
        {
            look["shirt"] = shirt ?? ""; look["shorts"] = shorts ?? ""; look["accent"] = accent ?? ""; look["racket"] = racket ?? "";
            if (swatchTitle) RefreshSwatches();
        }

        void BuildClubhouse(RectTransform r)
        {
            BrandUi.Headline(r, Left, 132, "Clubhouse", "Friends & help", 720);
            var rows = new[] { ("board-invite", "INVITE FRIENDS", "Game Center or a party code"), ("screen-howto", "HOW TO PLAY", "Tennis, golf and bowling basics"),
                               ("shelf-trophies", "TROPHIES", "Your records and trophies"), ("mailbox-feedback", "FEEDBACK", "Send the team a note") };
            var group = new List<MenuItem>(); float y = ListTop;
            foreach (var (id, label, sub) in rows)
            {
                string key = id, t = Title(label);
                y += WordItem(r, id, label, label, sub, Left, y, WordSize, () => OpenPhone(key, t), group) + 6;
            }
        }

        // ---- Loading: the match builds behind the line-up. Left: who is in, SPORT · LOADING, the mode's name big, what you picked, a
        // skewed gold bar (START under it when it waits for you); right: the venue you are about to play. Built: READY! pops in its place.
        Text loadTitle, loadSub, loadKicker, holdNote, tipTitle, tipLine; RawImage tipPic; RectTransform loadBlock, loadBar, loadFill, startBox, rowsRoot, banner;
        MenuItem startItem; float barShown = -1;
        readonly List<(Text name, Text state, Image dot)> partyRows = new List<(Text, Text, Image)>();
        void BuildLoading(RectTransform r)
        {
            rowsRoot = BrandUi.Box(r, "Players", Left, 420, 640, 4 * 46f);
            for (int i = 0; i < 4; i++)
            {
                var row = BrandUi.Box(rowsRoot, "Player " + i, 0, i * 46f, 640, 40);
                BrandUi.Slant(row, "Fill", BrandUi.Ink(.5f)).rectTransform.offsetMax = new Vector2(-180, 0);
                var dotBox = BrandUi.Box(row, "Dot", 14, 9, 22, 22); var dot = BrandUi.Layer(dotBox, "Fill", BrandColors.Glow, 0, 11);
                var name = BrandUi.Word(BrandUi.Box(row, "Name", 48, 0, 300, 40), "Text", "", BrandUi.SemiBold, 26, BrandColors.White);
                var state = BrandUi.Word(BrandUi.Box(row, "State", 300, 0, 140, 40), "Text", "", BrandUi.SemiBold, 22, BrandColors.Success, TextAnchor.MiddleRight);
                partyRows.Add((name, state, dot)); row.gameObject.SetActive(false);
            }
            loadBlock = BrandUi.Box(r, "Title block", 0, 0, 1920, 1080);
            loadKicker = BrandUi.Word(BrandUi.Box(loadBlock, "Kicker", Left + 4, 612, 900, 32), "Text", "", BrandUi.SemiBold, 26, BrandColors.Gold);
            loadTitle = BrandUi.Ink(BrandUi.Word(BrandUi.Box(loadBlock, "Title", Left, 640, 1000, 124), "Text", "", BrandUi.ExtraBoldItalic, 108, BrandColors.White));
            loadSub = BrandUi.Word(BrandUi.Box(r, "Sub", Left + 4, 770, 700, 40), "Text", "", BrandUi.Medium, 30, new Color(.863f, .89f, .949f));
            // the centred hero stands from x ~800: a long line shrinks to stay left of it rather than run across the legs
            loadSub.horizontalOverflow = HorizontalWrapMode.Wrap; loadSub.resizeTextForBestFit = true; loadSub.resizeTextMinSize = 20; loadSub.resizeTextMaxSize = 30;
            // the bar (mock .arcbar, 30cqw × .7cqw, skewed 20°): a white track, the gold fill grows from its left
            loadBar = BrandUi.Box(r, "Bar", Left + 6, 826, 576, 14);
            BrandUi.Slant(loadBar, "Track", BrandUi.WhiteA(.2f), 20);
            loadFill = BrandUi.Box(loadBar, "Fill", 0, 0, 0, 14);
            HGradient.On(BrandUi.Slant(loadFill, "Gold", Color.white, 20), BrandColors.Gold, new Color(1, .906f, .627f));
            startBox = BrandUi.Box(r, "Start", Left, 862, 400, 84);
            holdNote = BrandUi.Word(BrandUi.Box(r, "Note", Left + 4, 870, 900, 60), "Text", "Starting when everyone is in", BrandUi.MediumItalic, 30, BrandUi.WhiteA(.78f));
            startItem = Item(startBox, null, "start", "Start match", PressStart, 0);
            startItem.glow = k => { if (startItem.face) startItem.face.anchoredPosition = new Vector2(Nudge * .6f * k, 0); };
            StyleStart(false);
            // READY! (mock .ready, 11cqw gold, a navy drop): pops where the title was
            banner = BrandUi.Box(r, "Ready banner", Left, 520, 1000, 250); banner.pivot = new Vector2(0, .5f); banner.anchoredPosition = new Vector2(Left, -645);
            var word = BrandUi.Word(banner, "Word", "READY!", BrandUi.ExtraBoldItalic, 168, BrandColors.Gold);
            foreach (var sh in word.GetComponents<Shadow>()) sh.enabled = false;
            var drop = word.gameObject.AddComponent<Shadow>(); drop.effectColor = BrandColors.NavyDeep; drop.effectDistance = new Vector2(0, -10);
            var o = word.gameObject.AddComponent<Outline>(); o.effectColor = BrandColors.ShadowInk; o.effectDistance = new Vector2(3, -3);
            banner.gameObject.SetActive(false);
            // the venue card right of the hero (mock .tipcard, 30cqw × 16.9cqw)
            var tip = BrandUi.Box(r, "Venue", RightEdge - 576, 192, 576, 324);
            BrandUi.Skewed(BrandUi.DropShadow(tip, 0), 7, true).color = BrandUi.Ink(.45f);
            var (mask, pic) = PictureCard(tip, 7.4f, true, .45f); tipPic = pic;
            tipTitle = BrandUi.Word(BrandUi.Box(mask, "Title", 50, 220, 500, 50), "Text", "", BrandUi.ExtraBoldItalic, 44, BrandColors.White);
            tipLine = BrandUi.Label(BrandUi.Box(mask, "Line", 52, 270, 470, 40), "Text", "", BrandUi.Medium, 24, new Color(.863f, .89f, .949f), TextAnchor.UpperLeft);
        }
        bool startReady; string startStyle;
        void StyleStart(bool ready)
        {
            startReady = ready;
            string want = holding ? (ready ? "go" : "wait") : "none";
            startBox.gameObject.SetActive(holding); holdNote.gameObject.SetActive(!holding);
            if (startStyle == want) return; startStyle = want;
            for (int c = startBox.childCount - 1; c >= 0; c--) DestroyImmediate(startBox.GetChild(c).gameObject);
            startBox.sizeDelta = new Vector2(400, 84);
            if (!holding) return;
            var (face, _) = BrandUi.GoButton(startBox, ready ? "START MATCH" : "WAITING FOR PLAYERS", ready);
            startItem.face = face; startItem.enabled = ready;
        }

        // ---- phone modal: a detail screen is open on the leader's phone — the whole scene dims, a big phone pulses, its title, gold caption
        void BuildPhoneModal()
        {
            phoneModal = BrandUi.Fill(fx, "Phone modal");
            BrandUi.Layer(phoneModal, "Dim", BrandUi.Ink(.66f));
            var phone = BrandUi.Box(phoneModal, "Phone", 960 - 67, 330, 134, 230);
            BrandUi.Layer(phone, "Body", BrandColors.White, 0, 26);
            BrandUi.Layer(phone, "Glass", BrandColors.NavyInk, 8, 19);
            phoneScreen = BrandUi.Layer(BrandUi.Box(phone, "Screen", 22, 30, 90, 142), "Gold", BrandColors.Gold, 0, 8);
            BrandUi.Layer(BrandUi.Box(phone, "Home", 59, 192, 16, 16), "Dot", BrandColors.White, 0, 8);
            phoneModalTitle = BrandUi.Ink(BrandUi.Word(BrandUi.Box(phoneModal, "Title", 160, 586, 1600, 96), "Text", "", BrandUi.ExtraBoldItalic, 80, BrandColors.White, TextAnchor.MiddleCenter));
            BrandUi.Word(BrandUi.Box(phoneModal, "Body", 160, 690, 1600, 40), "Text", "FINISH ON YOUR PHONE", BrandUi.SemiBold, 30, BrandColors.Gold, TextAnchor.MiddleCenter);
            phoneModal.gameObject.SetActive(false);
        }

        // ---- name plates over the heroes (screen space, so they stay crisp)
        readonly List<(RectTransform root, Text name, Text tag, Image dot)> plateViews = new List<(RectTransform, Text, Text, Image)>();
        string localName = "You"; Color localColour = GolfArcade.Hub.HubRemotes.PartyColours[0]; string localTag = "";
        readonly Dictionary<string, string> friendTags = new Dictionary<string, string>();
        void BuildPlates()
        {
            for (int i = 0; i < 4; i++)
            {
                var root = BrandUi.Box(plates, "Plate " + i, 0, 0, 300, 56);
                // the mock's plate: a dark skewed chip on a gold underline
                var pill = BrandUi.Fill(root, "Pill");
                BrandUi.Slant(pill, "Fill", BrandUi.Ink(.74f));
                var ul = BrandUi.Slant(pill, "Gold", BrandColors.Gold); ul.rectTransform.offsetMin = new Vector2(-6.5f, 0); ul.rectTransform.offsetMax = new Vector2(-6.5f, -51);
                var dotBox = BrandUi.Box(pill, "Dot", 8, 8, 40, 40); var dot = BrandUi.Layer(dotBox, "Fill", Color.white, 0, 20);
                var num = BrandUi.Label(dotBox, "Num", (i + 1).ToString(), BrandUi.ExtraBold, 24, BrandColors.NavyInk, TextAnchor.MiddleCenter);
                var name = BrandUi.Label(BrandUi.Box(pill, "Name", 58, 0, 160, 56), "Text", "", BrandUi.SemiBold, 26, BrandColors.White, TextAnchor.MiddleLeft);
                var tag = BrandUi.Label(BrandUi.Box(pill, "Tag", 200, 0, 84, 56), "Text", "", BrandUi.ExtraBold, 18, BrandColors.Gold, TextAnchor.MiddleRight);
                plateViews.Add((root, name, tag, dot)); root.gameObject.SetActive(false);
            }
        }
        /// Your name, party colour and tag on your plate (the phone sends them; "HOST" for a party's leader).
        public void SetIdentity(string name, int colour, string tag)
        {
            localName = string.IsNullOrEmpty(name) ? "You" : name; localColour = GolfArcade.Hub.HubRemotes.PartyColours[Mathf.Abs(colour) % 4]; localTag = tag ?? "";
            SetChipName(localName);
        }
        public void SetFriendTag(string id, string tag) { if (string.IsNullOrEmpty(tag)) friendTags.Remove(id); else friendTags[id] = tag; }
        void UpdatePlates()
        {
            bool show = (Screen == Home || Screen == TennisModes || Screen == GolfModes || Screen == BowlingModes || Screen == Clubhouse || (Screen == Loading && !bannerUp)) && !phoneOpen && world && world.Camera;
            var remotes = world ? HubRemotes.For(world) : null;
            float w = canvasRT.rect.width, h = canvasRT.rect.height;
            for (int i = 0; i < plateViews.Count; i++)
            {
                var (root, name, tag, dot) = plateViews[i];
                if (!show || !stage.TryHead(i, out var head)) { root.gameObject.SetActive(false); continue; }
                var vp = world.Camera.WorldToViewportPoint(head);
                if (vp.z <= 0) { root.gameObject.SetActive(false); continue; }
                if (!root.gameObject.activeSelf) root.gameObject.SetActive(true);
                root.anchorMin = root.anchorMax = Vector2.zero; root.pivot = new Vector2(.5f, 0);
                var at = new Vector2(vp.x * w, vp.y * h + 8);
                if ((root.anchoredPosition - at).sqrMagnitude > .01f) root.anchoredPosition = at;
                string wantName = name.text, wantTag = tag.text; Color wantDot = dot.color;
                if (i == 0) { wantName = localName; wantTag = localTag; wantDot = localColour; }
                else if (remotes && i - 1 < stage.Friends.Count && remotes.TryGetIdentity(stage.Friends[i - 1], out var n, out var c))
                { wantName = n; wantDot = c; wantTag = friendTags.TryGetValue(stage.Friends[i - 1], out var t) ? t : ""; }
                if (dot.color != wantDot) dot.color = wantDot;
                // text layout (preferredWidth) only when the words change: it ran a layout pass per plate every frame
                if (name.text != wantName || tag.text != wantTag || root.sizeDelta.y != 56)
                {
                    name.text = wantName; tag.text = wantTag;
                    float nw = name.preferredWidth, tw = tag.preferredWidth;
                    root.sizeDelta = new Vector2(58 + nw + (wantTag.Length > 0 ? tw + 14 : 0) + 24, 56);
                    ((RectTransform)name.transform.parent).sizeDelta = new Vector2(nw + 4, 56);
                    var tr = (RectTransform)tag.transform.parent; tr.anchoredPosition = new Vector2(58 + nw + 12, 0); tr.sizeDelta = new Vector2(tw + 4, 56);
                }
            }
            // the empty seat: "+ JOIN" (the leader's TV only; a guest cannot invite for the party)
            bool join = (Screen == Home || Screen == Clubhouse) && !phoneOpen && world && world.Camera && stage.TryJoinSeat(out var seat) && Leader;
            joinSeat.gameObject.SetActive(join);
            if (join)
            {
                stage.TryJoinSeat(out var at); var vp = world.Camera.WorldToViewportPoint(at);
                bool onScreen = vp.z > 0 && vp.x < .94f;
                if (!onScreen) at = MenuShots.Slots[Mathf.Min(stage.Heroes - 1, 3)] + new Vector3(.9f, 1.1f, 0);
                vp = world.Camera.WorldToViewportPoint(at);
                float x = Mathf.Min(vp.x * w, w - 124), y = vp.y * h;
                joinSeat.anchorMin = joinSeat.anchorMax = Vector2.zero; joinSeat.pivot = new Vector2(.5f, .5f);
                joinSeat.anchoredPosition = new Vector2(x, y);
            }
        }

        // ================================================================== screens
        static string ShotOf(string screen) => screen == Home ? MenuShots.Low : screen == Locker ? MenuShots.Solo : screen == Loading ? MenuShots.Mid : MenuShots.Close;
        string ParentOf(string screen) => screen == Sport ? Home : screen == TennisModes || screen == GolfModes || screen == BowlingModes ? Sport
            : screen == Setup || screen == Players ? (setupSport == "golf" ? GolfModes : TennisModes) : screen == Loading ? null : Home;

        /// Go to a screen (the pointer, the phone's menuGo, or the session).
        public void Go(string screen)
        {
            if (!screens.ContainsKey(screen) || screen == Screen) return;
            Show(screen, snap: false);
        }
        void Show(string screen, bool snap)
        {
            Screen = screen; ScreenChanges++;
            foreach (var kv in screens) kv.Value.gameObject.SetActive(kv.Key == screen);
            // the bar stays on every screen (the active tab underlined: Plaza for everything under Play); Back on all but Home; the
            // tabs do nothing while a match loads (only Back = cancel leaves it)
            backButton.gameObject.SetActive(screen != Home);
            foreach (var (item, target, label, ul) in tabs)
            {
                bool on = Active(target);
                label.color = on ? BrandColors.White : BrandUi.WhiteA(.62f); ul.localScale = new Vector3(on ? 1 : 0, 1, 1);
                item.enabled = screen != Loading;
            }
            scrims.gameObject.SetActive(screen != Sport);   // the sport lanes have their own dim
            bool modes = screen == TennisModes || screen == GolfModes || screen == BowlingModes;
            if (modes) { StyleModes(); PreviewFor(screen == GolfModes ? "golf" : screen == BowlingModes ? "bowling" : "tennis", null); }
            ShowPreview(modes || screen == Setup, screen == Setup);
            if (screen == Locker) SelectSlot(lockerSlot);
            if (stage) stage.GoTo(ShotOf(screen), snap);
            var r = screens[screen];
            entered = Time.unscaledTime; enterRoot = r; enterGroup = groups[screen];
            if (!snap) Wipe();
            SetHovered(null); GlowsOff();
            Send("menuScreen", screen);
            FocusAfterShow();
        }

        /// Back: the phone's Back button, the TV's BACK, Esc in the editor.
        public void Back()
        {
            if (!Leader) return;
            if (phoneOpen) return;   // the phone closes its own panel
            if (Screen == Loading) { Send("menuCancel", ""); return; }
            var parent = ParentOf(Screen);
            if (parent != null && Screen != Home) Go(parent);
        }

        void OpenPhone(string route, string title)
        {
            if (!Leader) return;
            Send("menuOpen", route);
            SetPhonePanel(true, title);
        }
        bool phoneOpen;
        /// A detail screen is open on the leader's phone (true) or closed (false): the TV dims and says so.
        public void SetPhonePanel(bool open, string title = null)
        {
            phoneOpen = open; phoneModal.gameObject.SetActive(open);
            if (!string.IsNullOrEmpty(title)) phoneModalTitle.text = title;
            if (open) SetHovered(null); else if (hovered == null) FocusAfterShow();
        }

        // ---- the party
        /// Leader (drives) or guest (follows); with friends here the solo modes lock and Online is the way on.
        public void SetParty(bool leader, bool soloLocked)
        {
            Leader = leader; SoloLocked = soloLocked;
            if (Screen == TennisModes || Screen == GolfModes || Screen == BowlingModes) StyleModes();
            if (!leader) SetHovered(null);
        }
        /// A guest's TV: the leader's screen and cursor.
        public void Mirror(string screen, string hover, float x, float y, bool shown)
        {
            if (Leader) return;
            if (!string.IsNullOrEmpty(screen) && screens.ContainsKey(screen) && screen != Screen) Show(screen, false);
            mirrorShown = shown; mirrorAt = new Vector2(x, y);
            MenuItem found = null;
            foreach (var it in Visible()) if (it.id == hover) { found = it; break; }
            SetHovered(found);
        }
        bool mirrorShown; Vector2 mirrorAt;

        // ---- loading
        float loadingShown = -1; bool holding, built, bannerUp; float bannerAt;
        /// A match is loading behind the menu: 0..1 (-1: none). Shows the Loading screen.
        public void SetLoading(float progress)
        {
            if (progress < 0) { loadingShown = -1; built = false; bannerUp = false; if (banner) banner.gameObject.SetActive(false); if (loadBlock) { loadBlock.gameObject.SetActive(true); loadBar.gameObject.SetActive(true); } return; }
            if (Screen != Loading && loadingShown < 0) Show(Loading, false);
            loadingShown = Mathf.Max(loadingShown, Mathf.Clamp01(progress));
            string sport = sportLoading == "golf" ? "GOLF" : sportLoading == "bowling" ? "BOWLING" : "TENNIS";
            string kicker = sport + " · " + (loadingShown >= 1 ? "READY TO PLAY" : sportLoading == "golf" ? "LOADING THE COURSE" : sportLoading == "bowling" ? "LOADING THE LANES" : "LOADING THE COURT");
            if (loadKicker.text != kicker) loadKicker.text = kicker;
            // the bar: only when it moved a pixel (the fill re-shears its mesh)
            float w = Mathf.Round(576 * loadingShown);
            if (w != barShown) { barShown = w; loadFill.sizeDelta = new Vector2(w, 14); }
            bool ready = loadingShown >= 1;
            if (banner.gameObject.activeSelf != ready) { banner.gameObject.SetActive(ready); loadBlock.gameObject.SetActive(!ready); loadBar.gameObject.SetActive(!ready); if (ready) bannerAt = Time.unscaledTime; }
        }
        string sportLoading = "tennis";
        /// The match being loaded: its sport and mode (for the loader's words), and whether START waits for the player (solo / local).
        public void BeginLoading(string sport, string mode, bool hold)
        {
            sportLoading = string.IsNullOrEmpty(sport) ? "tennis" : sport; holding = hold; built = false; bannerUp = false; startStyle = null;
            // words, not ids (10-28: the loader said "bay-tennis-exhibition"): the mode's name big, what was picked under it, the venue right
            var (title, line, map, mapTitle, mapLine) = LoadWords(sportLoading, mode);
            loadTitle.text = title; loadSub.text = line;
            tipPic.texture = Resources.Load<Texture2D>("Menu/Maps/" + sportLoading + "-" + map); Cover(tipPic, 576, 324);
            tipPic.transform.parent.parent.gameObject.SetActive(tipPic.texture);
            tipTitle.text = mapTitle; tipLine.text = mapLine;
            StyleStart(false); SetPhonePanel(false);
            if (banner) banner.gameObject.SetActive(false);
            loadBlock.gameObject.SetActive(true); loadBar.gameObject.SetActive(true); barShown = -1;
            loadingShown = -1; SetLoading(0);
        }
        /// The match is built: START lights up (held) — or the hand-off starts at once.
        public void MatchBuilt() { built = true; SetLoading(1); StyleStart(true); }
        public bool StartPressed { get; private set; }
        void PressStart()
        {
            if (!built || !Leader) return;
            StartPressed = true; Send("menuStart", "");
        }
        /// READY! (Brand Guide result banner: pops 0.6 → 1.12 → 1.0 in 0.45 s) just before the hand-off.
        public void ShowReady() { bannerUp = true; bannerAt = Time.unscaledTime; banner.gameObject.SetActive(true); loadBlock.gameObject.SetActive(false); loadBar.gameObject.SetActive(false); }
        /// The party's rows on the loader: "name|STATE;name|STATE".
        public void SetRows(string rows)
        {
            var parts = string.IsNullOrEmpty(rows) ? new string[0] : rows.Split(';');
            for (int i = 0; i < partyRows.Count; i++)
            {
                var (name, state, dot) = partyRows[i];
                bool on = i < parts.Length && parts[i].Length > 0; name.transform.parent.parent.gameObject.SetActive(on);
                if (!on) continue;
                var f = parts[i].Split('|');
                name.text = f[0]; state.text = f.Length > 1 ? f[1] : "";
                ((RectTransform)state.transform.parent).anchoredPosition = new Vector2(48 + Mathf.Max(170, name.preferredWidth + 24), 0);
                state.alignment = TextAnchor.MiddleLeft;
                state.color = state.text == "READY" ? BrandColors.Success : BrandColors.N300;
                dot.color = HubRemotes.PartyColours[i % 4];
            }
        }
        public void ResetStart() { StartPressed = false; }

        // ================================================================== pointer
        RectTransform cursor, cursorArcRT; Image cursorCore; ArcGraphic cursorArc; RectTransform focusRing; Image focusOuter, focusInner;
        Vector2 cursorRaw, cursorShown; bool pointerShown; float lastPointer = -9; int lastPresses = int.MinValue; bool held, touchMode;
        MenuItem hovered, pressedItem, ringFor; float hoverChanged;
        /// Proof: activations so far (id), newest last.
        public readonly List<string> Activated = new List<string>();

        void BuildCursor()
        {
            focusRing = BrandUi.Box(fx, "Focus", 0, 0, 10, 10);
            focusOuter = BrandUi.Layer(focusRing, "Glow", BrandColors.Glow, -6, 30, BrandUi.Ring);
            focusInner = BrandUi.Layer(focusRing, "White", BrandColors.White, 2, 26, BrandUi.Ring);
            focusRing.gameObject.SetActive(false);
            cursor = BrandUi.Box(fx, "Cursor", 0, 0, 64, 64); cursor.anchorMin = cursor.anchorMax = Vector2.zero; cursor.pivot = new Vector2(.5f, .5f);
            var halo = BrandUi.Layer(cursor, "Halo", new Color(BrandColors.Glow.r, BrandColors.Glow.g, BrandColors.Glow.b, .5f), -18, -1, BrandUi.Glow);
            BrandUi.Layer(cursor, "Edge", BrandColors.White, 14, 18);
            cursorCore = BrandUi.Layer(cursor, "Core", BrandColors.NavyDeep, 18, 14);
            cursorArcRT = BrandUi.Fill(cursor, "Arc");
            cursorArc = ArcGraphic.Add(cursorArcRT, 110, 290, 7, new Color(BrandColors.ArcWarm.r, BrandColors.ArcWarm.g, BrandColors.ArcWarm.b, 0), BrandColors.Gold, .2f);
            cursorArc.radius = new Vector2(.86f, .86f);
            cursor.gameObject.SetActive(false);
        }

        /// The phone's pointer: x, y in -1..1 (y up), shown, Select held, Select press count, from a finger (no TV) rather than aiming.
        public void Pointer(float x, float y, bool shown, bool selectHeld, int presses, bool touch = false)
        {
            if (!Leader) return;
            if (float.IsNaN(x) || float.IsNaN(y)) return;
            lastPointer = Time.unscaledTime; touchMode = touch;
            float w = canvasRT.rect.width, h = canvasRT.rect.height;
            var raw = new Vector2((Mathf.Clamp(x, -1, 1) + 1) * .5f * w, (Mathf.Clamp(y, -1, 1) + 1) * .5f * h);
            if (!pointerShown && shown) cursorShown = raw;
            cursorRaw = raw; pointerShown = shown;
            bool newPress = lastPresses != int.MinValue && presses != lastPresses;
            if (lastPresses == int.MinValue) lastPresses = presses;
            if (shown) Hover(raw);
            if (newPress)
            {
                lastPresses = presses;
                pressedItem = hovered;
                // a press and its release inside one sample (or a dropped release): click now
                if (!selectHeld) { Click(pressedItem); pressedItem = null; }
            }
            else if (held && !selectHeld && pressedItem != null)
            {
                if (pressedItem == hovered) Click(pressedItem);
                pressedItem = null;
            }
            held = selectHeld;
        }
        /// A test / editor hook: the cursor straight to a canvas position (bottom-left origin) with Select's state.
        public void PointAt(Vector2 canvasPos, bool selectHeld, int presses)
        {
            float w = canvasRT.rect.width, h = canvasRT.rect.height;
            Pointer(canvasPos.x / w * 2 - 1, canvasPos.y / h * 2 - 1, true, selectHeld, presses);
        }
        /// The canvas position (bottom-left origin) of an item's centre, for tests and the editor.
        public bool TryCentre(string id, out Vector2 at)
        {
            at = default;
            foreach (var it in Visible()) if (it.id == id) { var r = RectOf(it); at = r.center; return true; }
            return false;
        }

        void Click(MenuItem item)
        {
            if (item == null || !item.enabled || phoneOpen) return;
            Activated.Add(item.id); clickPulse = Time.unscaledTime;
            item.activate?.Invoke();
        }

        readonly List<MenuItem> visible = new List<MenuItem>();
        List<MenuItem> Visible()
        {
            visible.Clear();
            if (phoneOpen) return visible;
            foreach (var it in chromeItems) if (it.Visible) visible.Add(it);
            if (screenItems.TryGetValue(Screen, out var list)) foreach (var it in list) if (it.Visible) visible.Add(it);
            return visible;
        }
        readonly Vector3[] corners = new Vector3[4];
        Rect RectOf(MenuItem it)
        {
            it.hit.GetWorldCorners(corners);
            float w = canvasRT.rect.width, h = canvasRT.rect.height;
            Vector2 min = new Vector2(float.MaxValue, float.MaxValue), max = new Vector2(float.MinValue, float.MinValue);
            for (int i = 0; i < 4; i++)
            {
                var p = (Vector2)canvasRT.InverseTransformPoint(corners[i]) + new Vector2(w * canvasRT.pivot.x, h * canvasRT.pivot.y);
                min = Vector2.Min(min, p); max = Vector2.Max(max, p);
            }
            return Rect.MinMaxRect(min.x, min.y, max.x, max.y);
        }
        void Hover(Vector2 p)
        {
            // hysteresis: an item is entered 16 px outside its edge and kept until 40 px outside it
            if (hovered != null && hovered.Visible && hovered.enabled && Grow(RectOf(hovered), 40).Contains(p)) return;
            MenuItem best = null; float bestD = float.MaxValue;
            foreach (var it in Visible())
            {
                if (!it.enabled) continue;
                var r = Grow(RectOf(it), 16); if (!r.Contains(p)) continue;
                float d = (r.center - p).sqrMagnitude; if (d < bestD) { bestD = d; best = it; }
            }
            SetHovered(best);
        }
        static Rect Grow(Rect r, float by) => Rect.MinMaxRect(r.xMin - by, r.yMin - by, r.xMax + by, r.yMax + by);
        void SetHovered(MenuItem it)
        {
            if (it == hovered) return;
            if (hovered != null && hovered.face) hovered.face.localScale = Vector3.one;
            var was = hovered;
            hovered = it; hoverChanged = Time.unscaledTime;
            HoverLook(was, it);
            HoverPreview(it);
            if (Leader) Send("menuHover", it == null ? "" : it.id + "|" + it.label);
        }

        // ================================================================== per frame
        float entered; RectTransform enterRoot; CanvasGroup enterGroup; float clickPulse = -9; float nextState;
        RectTransform wipe; float wipeAt = -9;
        void BuildWipe()
        {
            wipe = BrandUi.Box(fx, "Wipe", 0, 0, 1180, 1080);
            var band = BrandUi.Layer(wipe, "Band", new Color(BrandColors.Royal.r, BrandColors.Royal.g, BrandColors.Royal.b, .92f));
            band.rectTransform.offsetMax = new Vector2(-180, 0);
            var edge = BrandUi.Box(wipe, "Edge", 640, -160, 540, 1400);
            ArcGraphic.Add(edge, -62, 124, 34, new Color(BrandColors.ArcWarm.r, BrandColors.ArcWarm.g, BrandColors.ArcWarm.b, .2f), BrandColors.White, .4f).radius = new Vector2(1, 1);
            wipe.gameObject.SetActive(false);
        }
        void Wipe() { wipeAt = Time.unscaledTime; wipe.gameObject.SetActive(true); }

        void LateUpdate()
        {
            if (!canvas) return;
            if (world && world.Camera) canvas.targetDisplay = world.Camera.targetDisplay;   // the TV (Present retargets only canvases that existed then)
            if (HubWorld.PhoneOnly && UnityEngine.Screen.width > 0)
            {
                // no TV: the 16:9 frame across the top of the upright phone, over the plaza's band (HubWorld sets the camera's)
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize; scaler.scaleFactor = UnityEngine.Screen.width / 1920f;
                canvasRT.anchorMin = canvasRT.anchorMax = new Vector2(.5f, 1); canvasRT.pivot = new Vector2(.5f, 1);
                canvasRT.sizeDelta = new Vector2(1920, 1080); canvasRT.anchoredPosition = Vector2.zero;
            }
            float now = Time.unscaledTime, dt = Time.unscaledDeltaTime;
            EditorInput();
            // entrance: the screen's content rises 24 px and fades in (Brand Guide §10, panel open, 0.22 s ease-out)
            if (enterRoot)
            {
                float k = BrandMotion.EaseOut((now - entered) / BrandMotion.Base);
                enterRoot.anchoredPosition = new Vector2(0, -24 * (1 - k));
                enterGroup.alpha = k;
                if (k >= 1) enterRoot = null;
            }
            // the swing-arc wipe: left to right in 0.36 s
            if (wipe.gameObject.activeSelf)
            {
                float k = (now - wipeAt) / WipeSeconds;
                if (k >= 1) wipe.gameObject.SetActive(false);
                else wipe.anchoredPosition = new Vector2(Mathf.Lerp(-1180, 1920 + 40, BrandMotion.EaseOut(k)), 0);
            }
            Glows(dt);
            if (phoneOpen) { var c = phoneScreen.color; c.a = .55f + .45f * (.5f + .5f * Mathf.Sin(now * 3.9f)); phoneScreen.color = c; }   // the phone's screen breathes
            if (banner && banner.gameObject.activeSelf && now - bannerAt < BrandMotion.Banner + .05f)
            {
                float k = Mathf.Clamp01((now - bannerAt) / BrandMotion.Banner);
                banner.localScale = Vector3.one * Mathf.LerpUnclamped(.6f, 1f, BrandMotion.Overshoot(k));
            }
            // the pointer: hidden when the phone stops sending (backgrounded) or says so
            bool live = Leader ? pointerShown && now - lastPointer < .6f : mirrorShown;
            if (!Leader) { float w = canvasRT.rect.width, h = canvasRT.rect.height; cursorRaw = new Vector2((mirrorAt.x + 1) * .5f * w, (mirrorAt.y + 1) * .5f * h); }
            cursor.gameObject.SetActive(live && !touchMode && !phoneOpen);
            if (live)
            {
                var target = cursorRaw;
                if (hovered != null && hovered.Visible) target = Vector2.Lerp(cursorRaw, RectOf(hovered).center, .12f);   // a light magnet
                cursorShown = Vector2.Lerp(cursorShown, target, 1 - Mathf.Exp(-dt / .028f));
                cursor.anchoredPosition = cursorShown;
                cursorArcRT.localRotation = Quaternion.Euler(0, 0, -(now * 90f % 360));
                float pulse = Mathf.Clamp01(1 - (now - clickPulse) / .18f);
                cursor.localScale = Vector3.one * (held ? .86f : 1f + .15f * pulse);
            }
            // hover: the face grows 4 %, a white + glow ring settles round it; pressed: scales to 0.94 (Brand Guide button press)
            bool ring = hovered != null && hovered.Visible && !phoneOpen && hovered.glow == null;   // the slash look has no ring
            if (hovered != null && hovered.glow != null && hovered.face)
            {
                var press = Vector3.one * (held && pressedItem == hovered ? BrandMotion.PressScale : 1);
                if (hovered.face.localScale != press) hovered.face.localScale = press;
            }
            focusRing.gameObject.SetActive(ring);
            if (ring)
            {
                var r = RectOf(hovered);
                float pad = 10;
                focusRing.anchorMin = focusRing.anchorMax = Vector2.zero; focusRing.pivot = new Vector2(.5f, .5f);
                focusRing.anchoredPosition = r.center; focusRing.sizeDelta = new Vector2(r.width + pad * 2, r.height + pad * 2);
                focusRing.localRotation = hovered.hit.localRotation;
                if (ringFor != hovered)
                {
                    ringFor = hovered;
                    float rad = hovered.radius > 0 ? hovered.radius + pad : 8;
                    BrandUi.Round(focusOuter, rad + 6); BrandUi.Round(focusInner, rad - 2);
                }
                float k = BrandMotion.EaseOut((now - hoverChanged) / BrandMotion.Fast);
                var scale = Vector3.one * (held && pressedItem == hovered ? BrandMotion.PressScale : Mathf.Lerp(1, 1.04f, k));
                if (hovered.face && hovered.face.localScale != scale) hovered.face.localScale = scale;
            }
            UpdatePlates();
            // the leader's screen + cursor for the party's TVs (≤15 Hz)
            if (Leader && now >= nextState && (live || hovered != null))
            {
                nextState = now + 1f / 15f;
                float w = canvasRT.rect.width, h = canvasRT.rect.height;
                Send("menuState", string.Format(System.Globalization.CultureInfo.InvariantCulture, "{0}|{1}|{2:0.000}|{3:0.000}|{4}", Screen, Hovered, cursorRaw.x / w * 2 - 1, cursorRaw.y / h * 2 - 1, live ? 1 : 0));
            }
        }

        void EditorInput()
        {
#if UNITY_EDITOR && ENABLE_LEGACY_INPUT_MANAGER
            if (GolfArcade.Game.NativeSportsSession.Active || HubWorld.EditorDriven || !Application.isEditor) return;
            var m = Input.mousePosition;
            if (Input.GetMouseButtonDown(0)) editorPresses++;
            Pointer(m.x / UnityEngine.Screen.width * 2 - 1, m.y / UnityEngine.Screen.height * 2 - 1, true, Input.GetMouseButton(0), editorPresses);
            if (Input.GetKeyDown(KeyCode.Escape)) Back();
#endif
        }
#if UNITY_EDITOR
        int editorPresses;
#endif

        void Send(string type, string message) => Event?.Invoke(type, message ?? "");

        void PrewarmGlyphs()
        {
            const string upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ!·' ", lower = "abcdefghijklmnopqrstuvwxyz.,·':!0123456789 ";
            // every (weight, size) the slash screens draw at; headlines best-fit, so theirs are the likely sizes
            BrandUi.Prewarm(new (Font, int, string)[]
            {
                (BrandUi.ExtraBoldItalic, 96, upper + lower), (BrandUi.ExtraBoldItalic, 80, upper + lower), (BrandUi.ExtraBoldItalic, 46, "MotionSports"), (BrandUi.ExtraBoldItalic, 138, "PLAY"),
                (BrandUi.ExtraBoldItalic, 58, upper), (BrandUi.ExtraBoldItalic, 44, upper), (BrandUi.ExtraBoldItalic, 116, "TennisGolfBowling"), (BrandUi.ExtraBoldItalic, 168, "READY!"),
                (BrandUi.ExtraBoldItalic, 108, upper + lower), (BrandUi.ExtraBoldItalic, 56, upper + lower), (BrandUi.ExtraBoldItalic, 54, upper + lower), (BrandUi.ExtraBoldItalic, 44, upper + lower),
                (BrandUi.ExtraBoldItalic, 42, upper), (BrandUi.ExtraBoldItalic, 36, upper + lower), (BrandUi.ExtraBoldItalic, 22, upper), (BrandUi.ExtraBoldItalic, 20, upper),
                (BrandUi.ExtraBoldItalic, 124, "234"), (BrandUi.ExtraBoldItalic, 80, upper + lower),
                (BrandUi.BoldItalic, 28, upper + lower), (BrandUi.BoldItalic, 30, upper), (BrandUi.BoldItalic, 20, upper), (BrandUi.MediumItalic, 26, upper + lower), (BrandUi.MediumItalic, 30, upper + lower),
                (BrandUi.Medium, 24, upper + lower), (BrandUi.Medium, 26, upper + lower), (BrandUi.Medium, 30, upper + lower), (BrandUi.Medium, 22, upper + lower),
                (BrandUi.SemiBold, 20, upper), (BrandUi.SemiBold, 22, upper), (BrandUi.SemiBold, 24, upper + lower), (BrandUi.SemiBold, 26, upper + lower), (BrandUi.SemiBold, 30, upper + lower),
                (BrandUi.ExtraBold, 18, upper), (BrandUi.ExtraBold, 19, "AB"), (BrandUi.ExtraBold, 24, "1234KIT"),
            });
        }
    }
}
