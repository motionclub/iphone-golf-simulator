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
    }

    /// The pointer menu's TV half (PLAN_PointerMenu.md, Brand Guide v1.0): one overlay canvas at 1920×1080 drawn over the plaza
    /// line-up. Screens: Home, Sport, Modes (tennis / golf), Locker, Clubhouse and Loading; tabs PLAZA · LOCKER · CLUBHOUSE are the
    /// roots and Back pops toward them. The phone's pointer (or a finger on a phone with no TV) drives a cursor; hovering lights an item,
    /// Select presses it. Detail screens that live on the phone (mode options, the course picker, the full locker, settings, invites)
    /// open there: the TV shows "Finish on your phone" until the phone closes them. Only the party leader drives; guests' TVs follow.
    public sealed class MenuHud : MonoBehaviour
    {
        public const string Home = "home", Sport = "sport", TennisModes = "modes:tennis", GolfModes = "modes:golf", Locker = "locker", Clubhouse = "clubhouse", Loading = "loading";
        public const float WipeSeconds = .36f;
        /// Phone-bound events: (type, message) — the session emits them on the bridge.
        public event Action<string, string> Event;

        HubWorld world; MenuStage stage;
        Canvas canvas; CanvasScaler scaler; RectTransform canvasRT, chrome, screensRoot, plates, fx;
        readonly Dictionary<string, RectTransform> screens = new Dictionary<string, RectTransform>();
        readonly Dictionary<string, List<MenuItem>> screenItems = new Dictionary<string, List<MenuItem>>();
        readonly List<MenuItem> chromeItems = new List<MenuItem>();
        RectTransform tabBar, backButton, phoneModal, joinSeat; MenuItem joinItem; Text phoneModalTitle;
        readonly List<(MenuItem item, string screen, Image pill, Text label, ArcGraphic underline)> tabs = new List<(MenuItem, string, Image, Text, ArcGraphic)>();

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
            screensRoot = BrandUi.Fill(canvasRT, "Screens");
            plates = BrandUi.Fill(canvasRT, "Name plates");
            chrome = BrandUi.Fill(canvasRT, "Chrome");
            fx = BrandUi.Fill(canvasRT, "FX");
            BuildChrome();
            BuildScreen(Home, BuildHome); BuildScreen(Sport, BuildSport); BuildScreen(TennisModes, r => BuildModes(r, "tennis"));
            BuildScreen(GolfModes, r => BuildModes(r, "golf")); BuildScreen(Locker, BuildLocker); BuildScreen(Clubhouse, BuildClubhouse);
            BuildScreen(Loading, BuildLoading);
            BuildPhoneModal(); BuildPlates(); BuildCursor(); BuildWipe();
            PrewarmGlyphs();
            Show(Home, snap: true);
        }

        void BuildScreen(string id, Action<RectTransform> build)
        {
            var root = BrandUi.Fill(screensRoot, "Screen " + id); screens[id] = root; screenItems[id] = new List<MenuItem>();
            buildingFor = id; build(root); buildingFor = null;
            root.gameObject.SetActive(false);
        }
        string buildingFor;

        MenuItem Item(RectTransform hit, RectTransform face, string id, string label, Action activate, float radius)
        {
            var it = new MenuItem { id = id, label = label, hit = hit, face = face, activate = activate, radius = radius };
            if (buildingFor != null) screenItems[buildingFor].Add(it); else chromeItems.Add(it);
            return it;
        }
        MenuItem Button(Transform parent, string id, string label, float x, float y, float w, float h, BrandUi.Style style, Action activate, string sub = null)
        {
            var box = BrandUi.Box(parent, label, x, y, w, h);
            var (face, _, _) = BrandUi.Button(box, style, label, sub);
            return Item(box, face, id, label, activate, h / 2);
        }

        void BuildChrome()
        {
            BrandUi.Wordmark(chrome, 72, 36);
            // the tab bar: PLAZA · LOCKER · CLUBHOUSE (Deep Navy, radius 40, white border; the active tab a Bright pill, gold label, a small arc)
            tabBar = BrandUi.Box(chrome, "Tab bar", 600, 36, 720, 96);
            BrandUi.DropShadow(tabBar, 40);
            BrandUi.Layer(tabBar, "Border", BrandColors.White, 0, 40);
            BrandUi.Layer(tabBar, "Fill", BrandColors.NavyDeep, 5, 35);
            string[] names = { "PLAZA", "LOCKER", "CLUBHOUSE" }; string[] go = { Home, Locker, Clubhouse };
            for (int i = 0; i < 3; i++)
            {
                var box = BrandUi.Box(tabBar, names[i], 16 + i * 230f, 16, 228, 64);
                var face = BrandUi.Fill(box, "Face");
                var pill = BrandUi.Layer(face, "Pill", BrandColors.Bright, 0, 32);
                var label = BrandUi.Label(face, "Label", names[i], BrandUi.ExtraBoldItalic, 30, BrandColors.White, TextAnchor.MiddleCenter);
                var ul = BrandUi.Box(face, "Arc", 54, 52, 120, 26); var arc = ArcGraphic.Add(ul, 205, 130, 6, new Color(1, .77f, .26f, 0), BrandColors.Gold, .3f);
                string target = go[i];
                var item = Item(box, face, "tab-" + target, names[i], () => Go(target), 32);
                tabs.Add((item, target, pill, label, arc));
            }
            var gear = BrandUi.Box(chrome, "Settings", 1760, 40, 88, 88);
            var gearFace = BrandUi.Fill(gear, "Face"); BrandUi.DropShadow(gearFace, 28);
            BrandUi.Layer(gearFace, "Tile", BrandColors.NavyDeep, 0, 28);
            var glyph = BrandUi.Layer(gearFace, "Gear", BrandColors.White, 20, -1, BrandUi.Gear); glyph.preserveAspect = true;
            Item(gear, gearFace, "desk-settings", "Settings", () => OpenPhone("desk-settings", "Settings"), 28);
            backButton = BrandUi.Box(chrome, "Back", 72, 964, 230, 80);
            var (backFace, backLabel, _) = BrandUi.Button(backButton, BrandUi.Style.Secondary, "BACK");
            backLabel.fontSize = 32;
            Item(backButton, backFace, "back", "Back", () => Back(), 40);
            joinSeat = BrandUi.Box(chrome, "Join", 0, 0, 104, 140);
            var joinFace = BrandUi.Box(joinSeat, "Face", 0, 0, 104, 104);
            BrandUi.DropShadow(joinFace, 52);
            BrandUi.Layer(joinFace, "Glow", new Color(BrandColors.Glow.r, BrandColors.Glow.g, BrandColors.Glow.b, .43f), -22, -1, BrandUi.Glow);
            BrandUi.Layer(joinFace, "Border", BrandColors.White, 0, 52);
            BrandUi.Layer(joinFace, "Fill", new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, .92f), 4, 48);
            BrandUi.Layer(joinFace, "Plus", BrandColors.White, 26, -1, BrandUi.Plus).preserveAspect = true;
            var joinLabel = BrandUi.Underlay(BrandUi.Label(BrandUi.Box(joinSeat, "Label", -40, 110, 184, 32), "Text", "JOIN", BrandUi.SemiBold, BrandType.Caption, BrandColors.White, TextAnchor.MiddleCenter));
            joinItem = Item(joinSeat, joinFace, "board-invite", "Invite friends", () => OpenPhone("board-invite", "Invite friends"), 52);
        }

        void BuildHome(RectTransform r)
        {
            BrandUi.Headline(r, 72, 196, "Welcome", "to the club.");
            Button(r, "play", "PLAY NOW", 72, 560, 460, 96, BrandUi.Style.Primary, () => Go(Sport));
            Button(r, "board-invite", "INVITE FRIENDS", 72, 684, 460, 88, BrandUi.Style.Secondary, () => OpenPhone("board-invite", "Invite friends"));
        }

        void BuildSport(RectTransform r)
        {
            // flat brand blue (cutouts sit on the brand field, Brand Guide §9): navyDeep -> royal by 24 %, the Lift spotlight, three echo arcs
            var field = BrandUi.Layer(r, "Brand field", Color.white); UiGradientFlat(field);
            var spot = BrandUi.Box(r, "Spotlight", 960 - 900, 626 - 560, 1800, 1120);
            var s = spot.gameObject.AddComponent<Image>(); s.sprite = BrandUi.Glow; s.color = new Color(BrandColors.Lift.r, BrandColors.Lift.g, BrandColors.Lift.b, .55f); s.raycastTarget = false;
            Echo(r, 1320, 960, 700, 480, 10, new Color(1, 1, 1, .08f));
            Echo(r, 1460, 1080, 760, 540, 6, new Color(BrandColors.Gold.r, BrandColors.Gold.g, BrandColors.Gold.b, .10f));
            Echo(r, 1600, 1200, 830, 600, 16, new Color(1, 1, 1, .05f));
            BrandUi.Headline(r, 360, 130, "Game night", "just got loud.", 1200, TextAnchor.UpperCenter);
            SportCard(r, "sport-tennis", "Tennis", "Exhibition · Campaign · Training · Online", "tennis", 330, -2.5f, () => Go(TennisModes));
            SportCard(r, "sport-golf", "Golf", "Round · Pass the phone · Online", "golf", 1010, 2f, () => Go(GolfModes));
        }
        static void UiGradientFlat(Image img)
        {
            // the background: Deep Navy at the top to Royal at 24 % of the height, then flat Royal
            img.color = BrandColors.Royal;
            var band = BrandUi.Box(img.transform, "Top band", 0, 0, 1920, 260).gameObject.AddComponent<Image>(); band.raycastTarget = false;
            band.rectTransform.anchorMin = new Vector2(0, 1); band.rectTransform.anchorMax = new Vector2(1, 1); band.rectTransform.sizeDelta = new Vector2(0, 260);
            GolfArcade.Tennis.UiGradient.On(band, BrandColors.NavyDeep, BrandColors.Royal);
        }
        static void Echo(RectTransform r, float w, float h, float _, float __, float width, Color c)
        {
            var box = BrandUi.Box(r, "Echo", 960 - w / 2, 1060 - h / 2, w, h);
            var a = ArcGraphic.Add(box, 18, 144, width, c, c, 1); a.radius = Vector2.one;
        }
        void SportCard(RectTransform r, string id, string title, string sub, string art, float x, float tilt, Action go)
        {
            var box = BrandUi.Box(r, title, x, 350, 580, 580);
            var face = BrandUi.Fill(box, "Face");
            BrandUi.DropShadow(face, 0);
            BrandUi.Layer(face, "Frame", BrandColors.White);
            var inner = BrandUi.Layer(face, "Field", BrandColors.Royal, 10);
            GolfArcade.Tennis.UiGradient.On(inner, BrandColors.NavyDeep, BrandColors.Royal);
            var glow = BrandUi.Box(face, "Spot", 40, 140, 500, 420).gameObject.AddComponent<Image>(); glow.sprite = BrandUi.Glow; glow.color = new Color(BrandColors.Lift.r, BrandColors.Lift.g, BrandColors.Lift.b, .7f); glow.raycastTarget = false;
            var pic = BrandUi.Box(face, "Art", 110, 150, 360, 360).gameObject.AddComponent<Image>(); pic.sprite = GolfArcade.UI.Club.Art(art); pic.preserveAspect = true; pic.raycastTarget = false;
            BrandUi.Underlay(BrandUi.Label(BrandUi.Box(face, "Title", 36, 26, 520, 86), "Text", title, BrandUi.ExtraBoldItalic, 72, BrandColors.White, TextAnchor.UpperLeft));
            BrandUi.Underlay(BrandUi.Label(BrandUi.Box(face, "Sub", 36, 106, 520, 36), "Text", sub, BrandUi.MediumItalic, 26, BrandColors.N300, TextAnchor.UpperLeft));
            box.localRotation = Quaternion.Euler(0, 0, -tilt);   // the guide's tilt (+ counter-clockwise on screen)
            Item(box, face, id, title, go, 0);
        }

        readonly Dictionary<string, (MenuItem item, RectTransform box, string label, string sub, bool solo)> modeRows = new Dictionary<string, (MenuItem, RectTransform, string, string, bool)>();
        void BuildModes(RectTransform r, string sport)
        {
            bool tennis = sport == "tennis";
            BrandUi.Headline(r, 72, 196, tennis ? "Grip it." : "Tee it up.", tennis ? "Rip it." : "Send it.");
            var rows = tennis
                ? new[] { ("bay-tennis-exhibition", "EXHIBITION", "Quick match on any court", true), ("bay-tennis-campaign", "CAMPAIGN", "The Island Circuit", true), ("bay-tennis-training", "TRAINING", "Rally with the coach", true), ("bay-tennis-online", "ONLINE", "Play friends online", false) }
                : new[] { ("bay-golf-round", "ROUND", "Play a course, 9 or 18 holes", true), ("bay-golf-pass", "PASS THE PHONE", "Local party golf", true), ("bay-golf-online", "ONLINE", "Play friends online", false) };
            for (int i = 0; i < rows.Length; i++)
            {
                var (id, label, sub, solo) = rows[i];
                var box = BrandUi.Box(r, label, 72, 500 + i * 112f, 600, 96);
                string key = id, name = label;
                var item = Item(box, null, id, label, () => OpenPhone(key, Title(name)), 48);
                modeRows[id] = (item, box, label, sub, solo);
            }
        }
        /// (Re)draws the mode rows: the first solo mode is the gold primary, unless the party is here (then Online, and solo is locked).
        void StyleModes()
        {
            foreach (var kv in modeRows)
            {
                var (item, box, label, sub, solo) = kv.Value;
                bool first = kv.Key == "bay-tennis-exhibition" || kv.Key == "bay-golf-round";
                bool locked = SoloLocked && solo;
                var style = locked ? BrandUi.Style.RowDisabled : (SoloLocked ? !solo : first) ? BrandUi.Style.RowPrimary : BrandUi.Style.Row;
                string want = style.ToString();
                if (box.name == label + "|" + want) continue;
                for (int c = box.childCount - 1; c >= 0; c--) DestroyImmediate(box.GetChild(c).gameObject);
                var (face, _, _) = BrandUi.Button(box, style, label, locked ? "Your party is here: play online" : sub);
                box.name = label + "|" + want; item.face = face; item.enabled = !locked;
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
        readonly List<(MenuItem item, Image ring, string hex)> swatches = new List<(MenuItem, Image, string)>();
        readonly List<(MenuItem item, Image pill, Text label, string slot)> rail = new List<(MenuItem, Image, Text, string)>();
        void BuildLocker(RectTransform r)
        {
            BrandUi.Headline(r, 72, 196, "Look the part.", "Play the part.");
            var panel = BrandUi.Panel(r, "Rail", 72, 450, 420, 16 * 2 + 7 * 64 + 6 * 8);
            for (int i = 0; i < LockerRail.Length; i++)
            {
                var (id, label, slot, route, title) = LockerRail[i];
                var box = BrandUi.Box(panel, label, 16, 16 + i * 72f, 388, 64);
                var face = BrandUi.Fill(box, "Face");
                var pill = BrandUi.Layer(face, "Pill", BrandColors.Bright, 0, 32);
                var text = BrandUi.Label(face, "Label", label, BrandUi.ExtraBoldItalic, 30, BrandColors.White, TextAnchor.MiddleLeft);
                text.rectTransform.offsetMin = new Vector2(24, 0);
                string s = slot, rt = route, t = Title(label);
                var item = Item(box, face, id, t, () => { if (s != null) SelectSlot(s); else OpenPhone(rt, t); }, 32);
                rail.Add((item, pill, text, slot));
            }
            var sw = BrandUi.Panel(r, "Swatches", 1440, 300, 410, 30 * 2 + 92 + 22 + 4 * 72 + 3 * 18 + 6);
            swatchKicker = BrandUi.Label(BrandUi.Box(sw, "Kicker", 30, 26, 350, 30), "Text", "SHIRT", BrandUi.SemiBold, BrandType.HudLabel, BrandColors.N300, TextAnchor.MiddleLeft);
            swatchTitle = BrandUi.Label(BrandUi.Box(sw, "Title", 30, 58, 350, 60), "Text", "Shirt colour", BrandUi.BoldItalic, BrandType.Heading, BrandColors.White, TextAnchor.MiddleLeft);
            for (int i = 0; i < Palette.Length; i++)
            {
                var (name, hex) = Palette[i];
                int col = i % 4, row = i / 4;
                var box = BrandUi.Box(sw, name, 30 + col * 90f, 140 + row * 90f, 72, 72);
                var face = BrandUi.Fill(box, "Face");
                var ring = BrandUi.Layer(face, "Ring", BrandColors.Gold, -10, 46); ring.gameObject.SetActive(false);
                BrandUi.Layer(face, "Gap", BrandColors.NavyDeep, -4, 40);
                BrandUi.Layer(face, "Edge", BrandColors.White, 0, 36);
                var fill = BrandUi.Layer(face, "Colour", hex.Length == 0 ? BrandColors.N700 : BrandColors.FromHex("#" + hex), 4, 32);
                if (hex.Length == 0) BrandUi.Label(fill.transform, "Kit", "KIT", BrandUi.SemiBold, 22, BrandColors.White, TextAnchor.MiddleCenter);
                string h = hex;
                var item = Item(box, face, "swatch-" + name.ToLowerInvariant(), name, () => PickColour(h), 36);
                swatches.Add((item, ring, hex));
            }
            SelectSlot("shirt");
        }
        void SelectSlot(string slot)
        {
            lockerSlot = slot;
            foreach (var (item, pill, label, s) in rail) { bool on = s == slot; pill.gameObject.SetActive(on); label.color = on ? BrandColors.Gold : BrandColors.White; }
            foreach (var (id, label, s, _, title) in LockerRail) if (s == slot) { swatchKicker.text = label; swatchTitle.text = title; }
            RefreshSwatches();
        }
        void RefreshSwatches()
        {
            look.TryGetValue(lockerSlot, out var cur); cur = (cur ?? "").TrimStart('#').ToUpperInvariant();
            foreach (var (item, ring, hex) in swatches) ring.gameObject.SetActive(hex == cur);
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
            BrandUi.Headline(r, 72, 196, "Talk trash.", "Back it up.");
            var rows = new[] { ("board-invite", "INVITE FRIENDS", "Game Center or a party code", BrandUi.Style.RowPrimary), ("screen-howto", "HOW TO PLAY", "Tennis and golf basics", BrandUi.Style.Row),
                               ("shelf-trophies", "TROPHIES", "Campaign progress and records", BrandUi.Style.Row), ("mailbox-feedback", "FEEDBACK", "Send the team a note", BrandUi.Style.Row) };
            for (int i = 0; i < rows.Length; i++)
            {
                var (id, label, sub, style) = rows[i];
                string key = id, t = Title(label);
                Button(r, id, label, 72, 500 + i * 112f, 600, 96, style, () => OpenPhone(key, t), sub);
            }
        }

        // ---- Loading: the match builds behind the line-up; the arc loader, who is ready, START when it is built (solo / local)
        RectTransform loaderSpin; Text loadTitle, loadSub, holdNote; RectTransform startBox; MenuItem startItem; RectTransform rowsRoot; RectTransform banner;
        readonly List<(Text name, Text state, Image dot)> partyRows = new List<(Text, Text, Image)>();
        void BuildLoading(RectTransform r)
        {
            BrandUi.Headline(r, 72, 196, "One swing.", "Make it count.");
            var panel = BrandUi.Panel(r, "Loading", 72, 500, 640, 450);
            var ringBox = BrandUi.Box(panel, "Ring", 34, 34, 84, 84);
            ArcGraphic.Add(BrandUi.Fill(ringBox, "Track"), 0, 360, 6, new Color(1, 1, 1, .18f), new Color(1, 1, 1, .18f), 1).radius = new Vector2(.82f, .82f);
            loaderSpin = BrandUi.Fill(ringBox, "Spin");
            ArcGraphic.Add(loaderSpin, 0, 140, 8, new Color(1, 1, 1, 0), BrandColors.White, .15f).radius = new Vector2(.82f, .82f);
            loadTitle = BrandUi.Label(BrandUi.Box(panel, "Title", 140, 30, 470, 60), "Text", "Loading the court", BrandUi.BoldItalic, BrandType.Heading, BrandColors.White, TextAnchor.MiddleLeft);
            loadSub = BrandUi.Label(BrandUi.Box(panel, "Sub", 140, 88, 470, 34), "Text", "", BrandUi.Medium, BrandType.Caption, BrandColors.N300, TextAnchor.MiddleLeft);
            BrandUi.Layer(BrandUi.Box(panel, "Rule", 34, 140, 572, 3), "Line", new Color(1, 1, 1, .18f));
            rowsRoot = BrandUi.Box(panel, "Players", 34, 156, 572, 160);
            for (int i = 0; i < 4; i++)
            {
                var row = BrandUi.Box(rowsRoot, "Player " + i, 0, i * 52f, 572, 48);
                var dotBox = BrandUi.Box(row, "Dot", 0, 2, 44, 44); var dot = BrandUi.Layer(dotBox, "Fill", BrandColors.Glow, 0, 22);
                var name = BrandUi.Label(BrandUi.Box(row, "Name", 60, 0, 340, 48), "Text", "", BrandUi.Medium, BrandType.Body, BrandColors.White, TextAnchor.MiddleLeft);
                var state = BrandUi.Label(BrandUi.Box(row, "State", 330, 0, 242, 48), "Text", "", BrandUi.SemiBold, BrandType.HudLabel, BrandColors.Success, TextAnchor.MiddleRight);
                partyRows.Add((name, state, dot)); row.gameObject.SetActive(false);
            }
            startBox = BrandUi.Box(panel, "Start", 34, 330, 572, 96);
            holdNote = BrandUi.Label(BrandUi.Box(panel, "Note", 34, 330, 572, 96), "Text", "Starting when everyone is in", BrandUi.MediumItalic, BrandType.Body, BrandColors.N300, TextAnchor.MiddleCenter);
            startItem = Item(startBox, null, "start", "Start match", PressStart, 48);
            StyleStart(false);
            banner = BrandUi.Box(r, "Ready banner", 1010, 30, 860, 210); banner.gameObject.SetActive(false);
            var arcBox = BrandUi.Box(banner, "Arc", 120, 0, 620, 110); ArcGraphic.Add(arcBox, 205, 115, 14, new Color(1, 1, 1, 0), BrandColors.White, .15f).radius = new Vector2(1, 1.6f);
            var word = BrandUi.Label(BrandUi.Box(banner, "Word", 0, 40, 860, 170), "Text", "READY!", BrandUi.ExtraBoldItalic, BrandType.Display, BrandColors.Gold, TextAnchor.MiddleCenter);
            var o = word.gameObject.AddComponent<Outline>(); o.effectColor = BrandColors.NavyDeep; o.effectDistance = new Vector2(3, -3);
            for (int i = 1; i <= 5; i++) { var sh = word.gameObject.AddComponent<Shadow>(); sh.effectColor = BrandColors.NavyDeep; sh.effectDistance = new Vector2(0, -2 * i); }
        }
        bool startReady; string startStyle;
        void StyleStart(bool ready)
        {
            startReady = ready;
            string want = holding ? (ready ? "go" : "wait") : "none";
            startBox.gameObject.SetActive(holding); holdNote.gameObject.SetActive(!holding);
            if (startStyle == want) return; startStyle = want;
            for (int c = startBox.childCount - 1; c >= 0; c--) DestroyImmediate(startBox.GetChild(c).gameObject);
            if (!holding) return;
            var (face, _, _) = BrandUi.Button(startBox, ready ? BrandUi.Style.Primary : BrandUi.Style.Disabled, ready ? "START MATCH" : "WAITING FOR PLAYERS");
            startItem.face = face; startItem.enabled = ready;
        }

        // ---- phone modal: a detail screen is open on the leader's phone
        void BuildPhoneModal()
        {
            phoneModal = BrandUi.Fill(fx, "Phone modal");
            BrandUi.Layer(phoneModal, "Scrim", new Color(BrandColors.NavyInk.r, BrandColors.NavyInk.g, BrandColors.NavyInk.b, .6f));
            var panel = BrandUi.Panel(phoneModal, "Panel", 610, 380, 700, 260);
            phoneModalTitle = BrandUi.Label(BrandUi.Box(panel, "Title", 40, 50, 620, 70), "Text", "", BrandUi.BoldItalic, BrandType.Heading, BrandColors.White, TextAnchor.MiddleCenter);
            BrandUi.Label(BrandUi.Box(panel, "Body", 40, 140, 620, 50), "Text", "Finish on your phone", BrandUi.Medium, BrandType.Body, BrandColors.N300, TextAnchor.MiddleCenter);
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
                var pill = BrandUi.Fill(root, "Pill");
                BrandUi.DropShadow(pill, 28);
                BrandUi.Layer(pill, "Border", BrandColors.White, 0, 28);
                BrandUi.Layer(pill, "Fill", new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, .92f), 4, 24);
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
        }
        public void SetFriendTag(string id, string tag) { if (string.IsNullOrEmpty(tag)) friendTags.Remove(id); else friendTags[id] = tag; }
        void UpdatePlates()
        {
            bool show = (Screen == Home || Screen == TennisModes || Screen == GolfModes || Screen == Clubhouse || (Screen == Loading && !bannerUp)) && !phoneOpen && world && world.Camera;
            var remotes = world ? HubRemotes.For(world) : null;
            float w = canvasRT.rect.width, h = canvasRT.rect.height;
            for (int i = 0; i < plateViews.Count; i++)
            {
                var (root, name, tag, dot) = plateViews[i];
                if (!show || !stage.TryHead(i, out var head)) { root.gameObject.SetActive(false); continue; }
                var vp = world.Camera.WorldToViewportPoint(head);
                if (vp.z <= 0) { root.gameObject.SetActive(false); continue; }
                root.gameObject.SetActive(true);
                root.anchorMin = root.anchorMax = Vector2.zero; root.pivot = new Vector2(.5f, 0);
                root.anchoredPosition = new Vector2(vp.x * w, vp.y * h + 8);
                if (i == 0) { name.text = localName; tag.text = localTag; dot.color = localColour; }
                else if (remotes && i - 1 < stage.Friends.Count && remotes.TryGetIdentity(stage.Friends[i - 1], out var n, out var c))
                { name.text = n; dot.color = c; tag.text = friendTags.TryGetValue(stage.Friends[i - 1], out var t) ? t : ""; }
                float width = 58 + name.preferredWidth + (tag.text.Length > 0 ? tag.preferredWidth + 14 : 0) + 24;
                root.sizeDelta = new Vector2(width, 56);
                ((RectTransform)name.transform.parent).sizeDelta = new Vector2(name.preferredWidth + 4, 56);
                var tr = (RectTransform)tag.transform.parent; tr.anchoredPosition = new Vector2(58 + name.preferredWidth + 12, 0); tr.sizeDelta = new Vector2(tag.preferredWidth + 4, 56);
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
        static string ParentOf(string screen) => screen == Sport ? Home : screen == TennisModes || screen == GolfModes ? Sport : screen == Loading ? null : Home;

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
            bool root = screen == Home || screen == Locker || screen == Clubhouse;
            tabBar.gameObject.SetActive(root);
            backButton.gameObject.SetActive(!root);
            foreach (var (item, target, pill, label, arc) in tabs) { bool on = target == screen; pill.gameObject.SetActive(on); label.color = on ? BrandColors.Gold : BrandColors.White; arc.gameObject.SetActive(on); }
            if (screen == TennisModes || screen == GolfModes) StyleModes();
            if (screen == Locker) SelectSlot(lockerSlot);
            if (stage) stage.GoTo(ShotOf(screen), snap);
            var r = screens[screen];
            entered = Time.unscaledTime; enterRoot = r;
            if (!snap) Wipe();
            SetHovered(null);
            Send("menuScreen", screen);
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
            if (open) SetHovered(null);
        }

        // ---- the party
        /// Leader (drives) or guest (follows); with friends here the solo modes lock and Online is the way on.
        public void SetParty(bool leader, bool soloLocked)
        {
            Leader = leader; SoloLocked = soloLocked;
            if (Screen == TennisModes || Screen == GolfModes) StyleModes();
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
            if (progress < 0) { loadingShown = -1; built = false; bannerUp = false; if (banner) banner.gameObject.SetActive(false); return; }
            if (Screen != Loading && loadingShown < 0) Show(Loading, false);
            loadingShown = Mathf.Max(loadingShown, Mathf.Clamp01(progress));
            loadTitle.text = loadingShown >= 1 ? "Ready to play" : sportLoading == "golf" ? "Loading the course" : "Loading the court";
        }
        string sportLoading = "tennis";
        /// The match being loaded: its sport and mode (for the loader's words), and whether START waits for the player (solo / local).
        public void BeginLoading(string sport, string mode, bool hold)
        {
            sportLoading = sport; holding = hold; built = false; bannerUp = false; startStyle = null;
            loadSub.text = (string.IsNullOrEmpty(mode) ? "" : mode + " · ") + (sport == "golf" ? "Golf" : "Tennis");
            StyleStart(false); SetPhonePanel(false);
            if (banner) banner.gameObject.SetActive(false);
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
        public void ShowReady() { bannerUp = true; bannerAt = Time.unscaledTime; banner.gameObject.SetActive(true); }
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
                state.color = state.text == "READY" ? BrandColors.Success : BrandColors.N300;
                dot.color = HubRemotes.PartyColours[i % 4];
            }
        }
        public void ResetStart() { StartPressed = false; }

        // ================================================================== pointer
        RectTransform cursor; Image cursorCore; ArcGraphic cursorArc; RectTransform focusRing; Image focusOuter, focusInner;
        Vector2 cursorRaw, cursorShown; bool pointerShown; float lastPointer = -9; int lastPresses = int.MinValue; bool held, touchMode;
        MenuItem hovered, pressedItem; float hoverChanged;
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
            cursorArc = ArcGraphic.Add(BrandUi.Fill(cursor, "Arc"), 110, 290, 7, new Color(BrandColors.ArcWarm.r, BrandColors.ArcWarm.g, BrandColors.ArcWarm.b, 0), BrandColors.Gold, .2f);
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

        IEnumerable<MenuItem> Visible()
        {
            if (phoneOpen) yield break;
            foreach (var it in chromeItems) if (it.Visible) yield return it;
            if (screenItems.TryGetValue(Screen, out var list)) foreach (var it in list) if (it.Visible) yield return it;
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
            hovered = it; hoverChanged = Time.unscaledTime;
            if (Leader) Send("menuHover", it == null ? "" : it.id + "|" + it.label);
        }

        // ================================================================== per frame
        float entered; RectTransform enterRoot; float clickPulse = -9; float nextState;
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
                var g = enterRoot.GetComponent<CanvasGroup>(); if (!g) g = enterRoot.gameObject.AddComponent<CanvasGroup>();
                g.alpha = k; g.interactable = false; g.blocksRaycasts = false;
                if (k >= 1) enterRoot = null;
            }
            // the swing-arc wipe: left to right in 0.36 s
            if (wipe.gameObject.activeSelf)
            {
                float k = (now - wipeAt) / WipeSeconds;
                if (k >= 1) wipe.gameObject.SetActive(false);
                else wipe.anchoredPosition = new Vector2(Mathf.Lerp(-1180, 1920 + 40, BrandMotion.EaseOut(k)), 0);
            }
            if (loaderSpin) loaderSpin.localRotation = Quaternion.Euler(0, 0, -now * 330f);
            if (bannerUp && banner)
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
                cursorArc.Set(110 - now * 90f % 360, 290);
                float pulse = Mathf.Clamp01(1 - (now - clickPulse) / .18f);
                cursor.localScale = Vector3.one * (held ? .86f : 1f + .15f * pulse);
            }
            // hover: the face grows 4 %, a white + glow ring settles round it; pressed: scales to 0.94 (Brand Guide button press)
            bool ring = hovered != null && hovered.Visible && !phoneOpen;
            focusRing.gameObject.SetActive(ring);
            if (ring)
            {
                var r = RectOf(hovered);
                float pad = 10;
                focusRing.anchorMin = focusRing.anchorMax = Vector2.zero; focusRing.pivot = new Vector2(.5f, .5f);
                focusRing.anchoredPosition = r.center; focusRing.sizeDelta = new Vector2(r.width + pad * 2, r.height + pad * 2);
                focusRing.localRotation = hovered.hit.localRotation;
                float rad = hovered.radius > 0 ? hovered.radius + pad : 8;
                BrandUi.Round(focusOuter, rad + 6); BrandUi.Round(focusInner, rad - 2);
                float k = BrandMotion.EaseOut((now - hoverChanged) / BrandMotion.Fast);
                if (hovered.face) hovered.face.localScale = Vector3.one * (held && pressedItem == hovered ? BrandMotion.PressScale : Mathf.Lerp(1, 1.04f, k));
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
            BrandUi.Prewarm(new (Font, int, string)[]
            {
                (BrandUi.ExtraBoldItalic, 84, upper + lower), (BrandUi.ExtraBoldItalic, 64, "MotionSports"), (BrandUi.ExtraBoldItalic, 40, upper), (BrandUi.ExtraBoldItalic, 36, upper),
                (BrandUi.ExtraBoldItalic, 32, upper), (BrandUi.ExtraBoldItalic, 30, upper), (BrandUi.ExtraBoldItalic, 72, "TennisGolf"), (BrandUi.ExtraBoldItalic, 132, "READY!"),
                (BrandUi.BoldItalic, 52, upper + lower), (BrandUi.MediumItalic, 26, upper + lower), (BrandUi.MediumItalic, 30, upper + lower), (BrandUi.Medium, 24, upper + lower),
                (BrandUi.Medium, 30, upper + lower), (BrandUi.SemiBold, 24, upper), (BrandUi.SemiBold, 26, upper + lower), (BrandUi.ExtraBold, 18, upper), (BrandUi.ExtraBold, 24, "1234"),
            });
        }
    }
}
