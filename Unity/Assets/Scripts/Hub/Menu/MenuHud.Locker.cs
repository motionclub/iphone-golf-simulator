using System;
using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// LOCKER on the TV (Adnan 11-19: "clubs, mirror and emotes should not be phone only … all locker stuff should look the same … top,
    /// bottom, shoes, accessories … sport subsections"). Left: the sections as a word rail (TOP · BOTTOM · SHOES · ACCESSORIES · BODY ·
    /// EMOTES). Right: a SPORT row (tennis · golf · bowling) and then the section's picks, every one drawn the same way: a block with a small
    /// label over swatches (colours, skin tones) or word tiles (the rest). The phone describes the picks (menuLockerState, LockerTV.swift)
    /// and applies each one (menuLockerSet "key|value"), then the look reaches the hero (hubLook). Nothing opens on the phone.
    public sealed partial class MenuHud
    {
        [Serializable] public sealed class LockerChoice { public string id, label, hex; public bool on; }
        [Serializable] public sealed class LockerBlock { public string key, label, kind; public LockerChoice[] choices; }
        [Serializable] public sealed class LockerRef { public string id, label; }
        [Serializable] public sealed class LockerState { public string sport, section, title; public LockerRef[] sports, sections; public LockerBlock[] blocks; }

        static readonly (string id, string label)[] LockerSections =
        {
            ("top", "TOP"), ("bottom", "BOTTOM"), ("shoes", "SHOES"), ("accessories", "ACCESSORIES"), ("body", "BODY"), ("emotes", "EMOTES"),
        };
        static readonly (string id, string label)[] LockerSports = { ("tennis", "TENNIS"), ("golf", "GOLF"), ("bowling", "BOWLING") };

        string lockerSport = "tennis", lockerSection = "top", lockerBuiltFor;
        LockerState locker;
        RectTransform lockerPanel, lockerBlocks; Text lockerWait;
        readonly List<(MenuItem item, Word word, string id)> lockerRail = new List<(MenuItem, Word, string)>();
        readonly List<(Segment seg, string id)> lockerSportTabs = new List<(Segment, string)>();
        readonly List<MenuItem> lockerTiles = new List<MenuItem>();
        readonly List<(string block, string choice, Action<bool> paint)> lockerViews = new List<(string, string, Action<bool>)>();

        sealed class LockerSwatch { public RectTransform art; public GameObject ring; public bool on; public float k;
            public void Size() { float s = Mathf.Max(on ? 1.08f : 1, 1 + .1f * k); art.localScale = new Vector3(s, s, 1); } }

        const float LockerX = 1336, LockerW = 520, LockerTop = 262;

        void BuildLocker(RectTransform r)
        {
            Heading(r, "Locker", 720);
            // the sections as a word rail (mock .rail)
            var group = new List<MenuItem>(); float y = ListTop;
            foreach (var (id, label) in LockerSections)
            {
                string section = id;
                y += WordItem(r, "lk-" + id, label, Title(label), null, Left, y, RailSize, () => SelectLockerSection(section), group) + 4;
                lockerRail.Add((group[group.Count - 1], (Word)group[group.Count - 1].view, id));
            }
            // the right panel: the sport row on top, the section's blocks under it
            lockerPanel = BrandUi.Box(r, "Panel", LockerX, 0, LockerW, 1080);
            BrandUi.Word(BrandUi.Box(lockerPanel, "Sport label", 4, LockerTop, LockerW, 28), "Text", "SPORT", BrandUi.SemiBold, 22, BrandColors.N300);
            float cw = (LockerW - (LockerSports.Length - 1) * 10f) / LockerSports.Length;
            for (int i = 0; i < LockerSports.Length; i++)
            {
                string sport = LockerSports[i].id;
                var seg = MakeSegment(lockerPanel, "lk-sport-" + sport, LockerSports[i].label, 6 + i * (cw + 10), LockerTop + 36, cw, 56, 26, () => SelectLockerSport(sport));
                lockerSportTabs.Add((seg, sport));
            }
            lockerBlocks = BrandUi.Box(lockerPanel, "Blocks", 0, 0, LockerW, 1080);
            lockerWait = BrandUi.Word(BrandUi.Box(lockerPanel, "Wait", 6, LockerTop + 130, LockerW, 40), "Text", "Opening your locker...", BrandUi.MediumItalic, 28, BrandColors.White);
            PaintLockerNav();
        }

        /// A word tile in the setup screen's skewed-segment look (the picked one white on a gold edge). Registered as a menu item of the screen being built.
        Segment MakeSegment(RectTransform parent, string id, string text, float x, float y, float w, float h, int size, Action activate)
        {
            var box = BrandUi.Box(parent, text, x, y, w, h);
            var face = BrandUi.Fill(box, "Face");
            var seg = new Segment();
            seg.fill = BrandUi.Slant(face, "Fill", BrandUi.Ink(.58f));
            seg.on = BrandUi.Slant(face, "On", BrandColors.White);
            seg.edge = BrandUi.Slant(face, "Edge", BrandUi.WhiteA(.16f)); float lean = -(h / 2 - 2) * Mathf.Tan(14 * Mathf.Deg2Rad);
            seg.edge.rectTransform.offsetMin = new Vector2(lean, 0); seg.edge.rectTransform.offsetMax = new Vector2(lean, -(h - 4));
            seg.label = BrandUi.Word(face, "Text", text, BrandUi.BoldItalic, size, BrandColors.White, TextAnchor.MiddleCenter);
            string prev = buildingFor; buildingFor = Locker;
            var it = Item(box, face, id, text, activate, 0);
            buildingFor = prev;
            it.glow = g => { bool on = g > .35f; if (seg.lit != on) { seg.lit = on; seg.Paint(); } };
            return seg;
        }

        void PaintLockerNav()
        {
            foreach (var (item, word, id) in lockerRail) { bool on = id == lockerSection; if (word.picked != on) { word.picked = on; word.Paint(); } }
            foreach (var (seg, id) in lockerSportTabs) { bool on = id == lockerSport; if (seg.picked != on) { seg.picked = on; seg.Paint(); } }
        }
        /// The locker screen opened: ask the phone what is on show.
        void OpenLocker() { PaintLockerNav(); Send("menuLocker", lockerSport + "|" + lockerSection); }
        void SelectLockerSection(string id) { if (!Leader || id == lockerSection) return; lockerSection = id; PaintLockerNav(); Send("menuLocker", lockerSport + "|" + lockerSection); }
        void SelectLockerSport(string id) { if (!Leader || id == lockerSport) return; lockerSport = id; PaintLockerNav(); Send("menuLocker", lockerSport + "|" + lockerSection); }

        /// The phone's description of the picks on show (menuLockerState): rebuilt when the shape changes, otherwise only the lit picks move.
        public void SetLocker(string json)
        {
            LockerState s;
            try { s = JsonUtility.FromJson<LockerState>(json); } catch (Exception) { return; }
            if (s == null || s.blocks == null || s.sport != lockerSport || s.section != lockerSection) return;   // (an answer to a pick since changed)
            locker = s;
            string shape = s.sport + "|" + s.section;
            foreach (var b in s.blocks) shape += "|" + b.key + ":" + (b.choices?.Length ?? 0);
            if (shape != lockerBuiltFor) { lockerBuiltFor = shape; BuildLockerBlocks(s); }
            RefreshLocker();
        }

        const float BlockLabelH = 28, BlockGap = 22;
        void BuildLockerBlocks(LockerState s)
        {
            // the old picks go (their items too); the new ones are built as the Locker screen's
            if (screenItems.TryGetValue(Locker, out var items)) items.RemoveAll(lockerTiles.Contains);
            if (hovered != null && lockerTiles.Contains(hovered)) SetHovered(null);
            lockerTiles.Clear(); lockerViews.Clear();
            for (int c = lockerBlocks.childCount - 1; c >= 0; c--) Destroy(lockerBlocks.GetChild(c).gameObject);
            lockerWait.gameObject.SetActive(false);
            string prev = buildingFor; buildingFor = Locker;
            float y = LockerTop + 128;
            foreach (var block in s.blocks)
            {
                BrandUi.Word(BrandUi.Box(lockerBlocks, block.label + " label", 4, y, LockerW, BlockLabelH), "Text", block.label ?? "", BrandUi.SemiBold, 22, BrandColors.Gold);
                y += BlockLabelH + 8;
                int n = block.choices?.Length ?? 0;
                if (block.kind == "colour")
                {
                    const float Cell = 90, Gap = 17;
                    for (int i = 0; i < n; i++)
                    {
                        var choice = block.choices[i];
                        int col = i % 5, row = i / 5;
                        var box = BrandUi.Box(lockerBlocks, choice.label, 6 + col * (Cell + Gap), y + row * (Cell + Gap), Cell, Cell);
                        var face = BrandUi.Fill(box, "Face");
                        var sw = new LockerSwatch();
                        var ring = BrandUi.Fill(face, "Ring"); sw.ring = ring.gameObject;
                        BrandUi.Slant(ring, "Gold", BrandColors.Gold, 10, -10); BrandUi.Slant(ring, "Gap", BrandUi.Ink(.85f), 10, -5);
                        sw.art = BrandUi.Fill(face, "Art");
                        BrandUi.Skewed(BrandUi.DropShadow(sw.art, 0), 10).color = BrandUi.Ink(.35f);
                        BrandUi.Slant(sw.art, "Edge", BrandUi.WhiteA(.4f), 10);
                        bool kit = string.IsNullOrEmpty(choice.hex);
                        BrandUi.Slant(sw.art, "Colour", kit ? BrandUi.Ink(.75f) : BrandColors.FromHex("#" + choice.hex), 10, 3);
                        if (kit) BrandUi.Word(sw.art, "Kit", "KIT", BrandUi.ExtraBold, 24, BrandColors.White, TextAnchor.MiddleCenter);
                        string key = block.key, id = choice.id;
                        var it = Item(box, face, "lk-" + key + "-" + id, choice.label, () => PickLocker(key, id), 0);
                        it.glow = k => { sw.k = k; sw.Size(); };
                        lockerTiles.Add(it);
                        lockerViews.Add((key, id, on => { sw.on = on; sw.ring.SetActive(on); sw.Size(); }));
                    }
                    int rows = (n + 4) / 5;
                    y += rows * (Cell + Gap) + BlockGap - Gap;
                }
                else
                {
                    // word tiles: up to three across (a long list wraps onto more rows)
                    int across = Mathf.Min(3, Mathf.Max(1, n));
                    float cw = (LockerW - (across - 1) * 10f) / across, h = n > 6 ? 52 : 56;
                    for (int i = 0; i < n; i++)
                    {
                        var choice = block.choices[i];
                        int col = i % across, row = i / across;
                        string key = block.key, id = choice.id;
                        var seg = MakeSegment(lockerBlocks, "lk-" + key + "-" + id, choice.label, 6 + col * (cw + 10), y + row * (h + 10), cw, h, n > 6 ? 22 : 26, () => PickLocker(key, id));
                        lockerTiles.Add(screenItems[Locker][screenItems[Locker].Count - 1]);
                        lockerViews.Add((key, id, on => { if (seg.picked != on) { seg.picked = on; seg.Paint(); } }));
                    }
                    int rows = (n + across - 1) / across;
                    y += rows * (h + 10) + BlockGap - 10;
                }
            }
            buildingFor = prev;
        }

        void RefreshLocker()
        {
            if (locker?.blocks == null) return;
            foreach (var (block, choice, paint) in lockerViews)
                foreach (var b in locker.blocks)
                    if (b.key == block) foreach (var c in b.choices) if (c.id == choice) paint(c.on);
        }

        void PickLocker(string key, string id)
        {
            if (!Leader || locker?.blocks == null) return;
            // lit at once; the phone's answer (menuLockerState) confirms it
            foreach (var b in locker.blocks)
                if (b.key == key) foreach (var c in b.choices) c.on = c.id == id;
            RefreshLocker();
            Send("menuLockerSet", key + "|" + id);
        }

        /// The player's look as the phone has it (start / hubLook). The locker's own picks come with menuLockerState, so nothing is kept here.
        public void SetLook(string shirt, string shorts, string accent, string racket) { }
    }
}
