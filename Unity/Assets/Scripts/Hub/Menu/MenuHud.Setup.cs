using System;
using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Video;

namespace GolfArcade.Hub.Menu
{
    /// The TV menu's mode previews and match setup (Adnan 10-26: "after clicking a sport, show previews of game modes, maps, etc.
    /// instead of just the character in the lobby; map selection on the external display, not the phone"). The modes screen plays a
    /// gameplay clip of the hovered mode on the right; Exhibition, Training and Golf Round set up on the TV (court / course strip,
    /// option rows, START); Local golf asks how many players first. The phone keeps the options and starts the match (MenuSetup.swift):
    /// the TV sends menuSetup (mode), menuSet (key|value) and menuSetupStart, the phone answers with menuSetupState (the JSON below).
    public sealed partial class MenuHud
    {
        // ------------------------------------------------------------------ the phone's description of a setup screen
        [Serializable] public sealed class SetupState { public string mode, sport, title, line2, start; public string map; public SetupMap[] maps; public SetupRow[] rows; }
        [Serializable] public sealed class SetupMap { public string id, title, detail, tag, tagHex; }
        [Serializable] public sealed class SetupRow { public string key, label; public string[] choices; public int value; }

        string setupSport = "tennis", setupMode, builtFor;
        SetupState setup;

        // what each mode is, in plain words (Adnan: "just say what the tab does"), with its chips
        // (10-28: each mode previews its own venue, and bowling has a preview too: the four lanes' stills)
        static readonly Dictionary<string, (string title, string line, string[] chips, string map)> ModeInfo = new Dictionary<string, (string, string, string[], string)>
        {
            { "bay-tennis-exhibition", ("Exhibition", "Play the CPU on any court, at any difficulty, for as long as you like.", new[] { "1 PLAYER", "VS CPU", "3 COURTS" }, null) },
            { "bay-tennis-training", ("Training", "Rally with the coach and work on your timing. No score.", new[] { "1 PLAYER", "COACH" }, "skyscraper") },
            { "bay-tennis-nearby", ("Local play", "Friends in the same room: two phones, one TV.", new[] { "2 PLAYERS", "SAME ROOM" }, "volcano") },
            { "bay-tennis-online", ("Online", "Play your friends wherever they are.", new[] { "2 PLAYERS", "ONLINE" }, "resort") },
            { "bay-golf-round", ("Round", "Play a course on your own: its own holes, 9 or 18.", new[] { "1 PLAYER", "3 COURSES" }, null) },
            { "bay-golf-pass", ("Local play", "One phone, passed around: swing, then hand it on.", new[] { "2-4 PLAYERS", "ONE PHONE" }, "wildisles") },
            { "bay-golf-online", ("Online", "Play a round with friends online.", new[] { "2-4 PLAYERS", "ONLINE" }, "magma") },
            { "bay-bowling-play", ("Play", "Ten frames on any of four lanes: Club, Neon, Tiki or Magma.", new[] { "1 PLAYER", "4 VENUES" }, null) },
            { "bay-bowling-exhibition", ("Exhibition", "Bowl a full game against a CPU bowler.", new[] { "1 PLAYER", "VS CPU" }, "neon") },
            { "bay-bowling-pass", ("Local play", "One phone, passed around between up to four bowlers.", new[] { "2-4 PLAYERS", "ONE PHONE" }, "tiki") },
            { "bay-bowling-online", ("Online", "Bowl with friends wherever they are.", new[] { "2-4 PLAYERS", "ONLINE" }, "magma") },
        };
        static readonly Dictionary<string, string> LastMap = new Dictionary<string, string> { { "tennis", "resort" }, { "golf", "cliffside" }, { "bowling", "club" } };
        static readonly Dictionary<string, (string title, string line)> Venues = new Dictionary<string, (string, string)>
        {
            { "tennis-resort", ("Tropical Resort", "A bright tropical bay, lush gardens and stands full of fans.") }, { "tennis-skyscraper", ("Sky Tower", "A rooftop above the clouds. Hit it wide and the ball falls forever.") },
            { "tennis-volcano", ("Magma Crater", "A court floating over a lava lake. Don't miss long.") }, { "golf-cliffside", ("Cliffside", "Cliffs, sea stacks and island carries.") },
            { "golf-wildisles", ("Wild Isles", "A world tour: pine, ice, mesa, jungle.") }, { "golf-magma", ("Magma Open", "Lava crater holes and volcanic greens.") },
            { "bowling-club", ("Club Lanes", "The clubhouse alley: wood, brass and a full crowd.") }, { "bowling-neon", ("Neon", "Black-light lanes and a glowing pit.") },
            { "bowling-tiki", ("Tiki", "Bamboo, torches and a lagoon behind the pins.") }, { "bowling-magma", ("Magma", "Lanes over a lava lake.") },
        };

        /// A mode row pressed: the TV's own setup where there is one, the phone otherwise (local tennis hosting, online).
        void OpenMode(string id, string title)
        {
            if (!Leader) return;
            setupSport = id.Contains("golf") ? "golf" : "tennis";
            if (id == "bay-golf-pass") { setupMode = id; ResetSetup(); Go(Players); return; }
            if (id == "bay-tennis-exhibition" || id == "bay-tennis-training" || id == "bay-golf-round")
            {
                setupMode = id; ResetSetup(); Send("menuSetup", id); Go(Setup); return;
            }
            OpenPhone(id, title);
        }

        // ------------------------------------------------------------------ the preview card (modes + setup): a gameplay clip and what it is
        // right of the hero (mock .pv.sm, 34.6cqw × 19.5cqw): a borderless skewed card, the clip upright inside it, its words bottom-left
        const float PreviewW = 664, PreviewH = 374, PreviewModesY = 326, PreviewSetupY = 192;
        RectTransform previewRoot, previewCaption, previewTagBox; RawImage previewImage; Text previewTitle, previewLine, previewTag; Image previewTagFill; ChipRow previewChips;
        VideoPlayer video; RenderTexture videoTexture; string playing;

        void BuildPreview(RectTransform screen, string sport)
        {
            if (previewRoot) return;   // one card, shared by the three modes screens and the setup screen
            previewRoot = BrandUi.Box(screensRoot, "Preview", RightX, PreviewModesY, PreviewW, PreviewH);
            previewRoot.SetAsFirstSibling();
            BrandUi.Skewed(BrandUi.DropShadow(previewRoot, 0), 4.2f, true).color = BrandUi.Ink(.45f);
            var (mask, pic) = PictureCard(previewRoot, 4.2f, true, .4f);
            previewImage = pic;
            previewTagBox = BrandUi.Box(mask, "Tag", 58, 28, 200, 40);
            previewTagFill = BrandUi.Slant(previewTagBox, "Fill", BrandColors.Royal);
            previewTag = BrandUi.Word(previewTagBox, "Text", "", BrandUi.ExtraBoldItalic, 22, BrandColors.White, TextAnchor.MiddleCenter);
            previewCaption = BrandUi.Box(mask, "Caption", 46, 0, 580, PreviewH);
            previewTitle = BrandUi.Word(BrandUi.Box(previewCaption, "Title", 0, 0, 580, 66), "Text", "", BrandUi.ExtraBoldItalic, 56, BrandColors.White);
            previewLine = BrandUi.Label(BrandUi.Box(previewCaption, "Line", 2, 0, 560, 66), "Text", "", BrandUi.Medium, 26, new Color(.863f, .89f, .949f), TextAnchor.UpperLeft);
            previewChips = Chips(previewCaption, 2, 0, 34, 4);
            videoTexture = new RenderTexture(1280, 720, 0) { name = "Menu preview" };
            video = previewRoot.gameObject.AddComponent<VideoPlayer>();
            video.playOnAwake = false; video.isLooping = true; video.audioOutputMode = VideoAudioOutputMode.None; video.skipOnDrop = true;
            video.renderMode = VideoRenderMode.RenderTexture; video.targetTexture = videoTexture;
            previewRoot.gameObject.SetActive(false);
        }
        void ShowPreview(bool on, bool setupScreen = false)
        {
            if (!previewRoot) return;
            previewRoot.gameObject.SetActive(on);
            if (!on && video && video.isPlaying) video.Stop();
            // the setup screen puts its court strip under the card, so the card rides higher there
            if (on) { previewRoot.anchoredPosition = new Vector2(RightX, -(setupScreen ? PreviewSetupY : PreviewModesY)); previewRoot.SetSiblingIndex(0); }
        }
        /// The caption's words bottom-up: chips (when there are any), the line (1–2 lines), the title.
        void PlaceCaption(bool chips)
        {
            float bottom = PreviewH - 26, chipsY = bottom - 34, lineH = Mathf.Min(66, previewLine.preferredHeight + 4);
            float lineY = (chips ? chipsY - 12 : bottom) - lineH, titleY = lineY - 64;
            ((RectTransform)previewChips.chips[0].box.parent).anchoredPosition = new Vector2(2, -chipsY);
            ((RectTransform)previewLine.transform.parent).anchoredPosition = new Vector2(2, -lineY);
            ((RectTransform)previewTitle.transform.parent).anchoredPosition = new Vector2(0, -titleY);
        }

        /// The clip and words for a mode (`id` null: the screen's first mode) on the modes screens.
        void PreviewFor(string sport, string id)
        {
            if (!previewRoot) return;
            id ??= sport == "golf" ? "bay-golf-round" : sport == "bowling" ? "bay-bowling-play" : "bay-tennis-exhibition";
            if (!ModeInfo.TryGetValue(id, out var info)) return;
            Clip(sport, info.map ?? LastMap[sport]);
            previewTitle.text = info.title; previewLine.text = info.line;
            previewTagBox.gameObject.SetActive(false);
            previewChips.Set(info.chips); PlaceCaption(true);
        }
        void HoverPreview(MenuItem it)
        {
            if (it == null || previewRoot == null || !previewRoot.gameObject.activeInHierarchy) return;
            if ((Screen == TennisModes || Screen == GolfModes || Screen == BowlingModes) && ModeInfo.ContainsKey(it.id))
                PreviewFor(Screen == GolfModes ? "golf" : Screen == BowlingModes ? "bowling" : "tennis", it.id);
            else if (Screen == Setup && it.id.StartsWith("map-") && setup != null) ShowMap(it.id.Substring(4));
        }
        /// Plays the gameplay clip for a court / course (Resources/Menu/Previews/<sport>-<id>, filmed from the current game 10-26), or its
        /// still (Resources/Menu/Maps/<sport>-<id>) where there is no clip (bowling's lanes, 10-28).
        void Clip(string sport, string id)
        {
            string key = sport + "-" + id;
            if (key == playing && previewImage.texture) return;
            playing = key;
            var clip = Resources.Load<VideoClip>("Menu/Previews/" + key);
            if (clip)
            {
                video.clip = clip; video.Play(); previewImage.texture = videoTexture;
            }
            else
            {
                if (video.isPlaying) video.Stop();
                previewImage.texture = Resources.Load<Texture2D>("Menu/Maps/" + key);
            }
            Cover(previewImage, PreviewW, PreviewH);
        }

        /// The loader's words for a match: the mode's name (never its id), what was picked on the setup screen, and the venue.
        (string title, string line, string map, string mapTitle, string mapLine) LoadWords(string sport, string mode)
        {
            string id = null, title;
            if (!string.IsNullOrEmpty(mode) && ModeInfo.ContainsKey(mode)) { id = mode; title = ModeInfo[mode].title; }
            else if (!string.IsNullOrEmpty(mode) && mode.StartsWith("bay-")) { id = mode; title = Title(mode.Substring(mode.LastIndexOf('-') + 1)); }
            else if (!string.IsNullOrEmpty(mode)) title = mode;
            else title = sport == "golf" ? "Golf" : sport == "bowling" ? "Bowling" : "Tennis";
            if (id == null) foreach (var kv in ModeInfo) if (kv.Key.Contains("-" + sport + "-") && kv.Value.title == title) { id = kv.Key; break; }
            string map = LastMap.TryGetValue(sport, out var m) ? m : "", line = id != null && ModeInfo.TryGetValue(id, out var info) ? info.line : "";
            string mapTitle = null, mapLine = null;
            if (setup != null && id != null && setup.mode == id)
            {
                // "Sky Tower · vs Suki Tanaka · Standard · 1 set": the court, then each option as picked
                var parts = new List<string>();
                if (setup.maps != null) foreach (var sm in setup.maps) if (sm.id == setup.map) { parts.Add(sm.title); mapTitle = sm.title; mapLine = sm.detail; map = sm.id; }
                if (setup.rows != null)
                    foreach (var row in setup.rows)
                    {
                        if (row.choices == null || row.choices.Length == 0 || parts.Count >= 4) continue;
                        string c = row.choices[Mathf.Clamp(row.value, 0, row.choices.Length - 1)];
                        int dot = c.IndexOf(" · "); if (dot > 0) c = c.Substring(0, dot);
                        parts.Add(row.key == "opponent" ? "vs " + c : c);
                    }
                line = string.Join(" · ", parts);
            }
            if (mapTitle == null && Venues.TryGetValue(sport + "-" + map, out var v)) { mapTitle = v.title; mapLine = v.line; }
            return (title, line, map, mapTitle ?? "", mapLine ?? "");
        }

        // ------------------------------------------------------------------ setup: options left, the court card + strip right, START
        RectTransform setupContent; Text setupWait;
        sealed class MapCard { public RectTransform face; public GameObject ring; public RawImage still; public Text name; public string id; public bool picked; public float k;
            public void Paint() { face.anchoredPosition = new Vector2(0, picked ? 10 : 6 * k); ring.SetActive(picked); var c = picked || k > .35f ? Color.white : new Color(.72f, .72f, .76f); if (still.color != c) still.color = c; } }
        sealed class Segment { public Image fill, on, edge; public Text label; public string key; public int index; public bool picked, lit;
            public void Paint() { on.gameObject.SetActive(picked); fill.color = lit && !picked ? new Color(BrandColors.Bright.r, BrandColors.Bright.g, BrandColors.Bright.b, .85f) : BrandUi.Ink(.58f);
                edge.color = picked ? BrandColors.Gold : lit ? BrandUi.WhiteA(.6f) : BrandUi.WhiteA(.16f); label.color = picked ? BrandColors.NavyInk : BrandUi.WhiteA(lit ? 1 : .78f);
                foreach (var s in label.GetComponents<Shadow>()) s.enabled = !picked; } }
        readonly List<MapCard> mapCards = new List<MapCard>();
        readonly List<Segment> choiceViews = new List<Segment>();
        readonly List<(Text value, Text detail, string key)> stepViews = new List<(Text, Text, string)>();
        /// A new setup screen is on its way from the phone: nothing of the last mode's shows meanwhile.
        void ResetSetup()
        {
            setup = null; builtFor = null; mapCards.Clear(); choiceViews.Clear(); stepViews.Clear();
            if (setupContent) for (int c = setupContent.childCount - 1; c >= 0; c--) Destroy(setupContent.GetChild(c).gameObject);
            if (screenItems.TryGetValue(Setup, out var items)) items.Clear();
            if (setupWait) setupWait.gameObject.SetActive(true);
        }
        void BuildSetup(RectTransform r)
        {
            setupContent = BrandUi.Fill(r, "Content");
            setupWait = BrandUi.Word(BrandUi.Box(r, "Wait", Left, 500, 640, 60), "Text", "Getting your options...", BrandUi.MediumItalic, 30, BrandColors.White);
        }

        /// The phone's description of the setup screen (menuSetupState): built once per mode, then only the selection moves.
        public void SetSetup(string json)
        {
            SetupState s;
            try { s = JsonUtility.FromJson<SetupState>(json); } catch (Exception) { return; }
            if (s == null || string.IsNullOrEmpty(s.mode)) return;
            setup = s; setupSport = string.IsNullOrEmpty(s.sport) ? setupSport : s.sport;
            if (!string.IsNullOrEmpty(s.map)) LastMap[setupSport] = s.map;
            string shape = s.mode + "|" + (s.maps?.Length ?? 0) + "|" + (s.rows?.Length ?? 0);
            if (shape != builtFor) { builtFor = shape; BuildSetupContent(s); }
            RefreshSetup();
        }

        const float OptW = 656, SegH = 56, OptGap = 22;
        void BuildSetupContent(SetupState s)
        {
            for (int c = setupContent.childCount - 1; c >= 0; c--) Destroy(setupContent.GetChild(c).gameObject);
            screenItems[Setup].Clear(); mapCards.Clear(); choiceViews.Clear(); stepViews.Clear();
            setupWait.gameObject.SetActive(false);
            buildingFor = Setup;
            BrandUi.Headline(setupContent, Left, 132, s.title ?? "", s.line2 ?? "", 760);
            // option rows (mock .opts): a small label, then the choices as skewed segments (the picked one white on a gold edge), or a
            // stepper ‹ value › for a long list (the CPU opponents)
            int rows = s.rows?.Length ?? 0;
            float y = ListTop;
            for (int i = 0; i < rows; i++)
            {
                var row = s.rows[i];
                BrandUi.Word(BrandUi.Box(setupContent, row.label + " label", Left + 2, y, OptW, 28), "Text", (row.label ?? "").ToUpperInvariant(), BrandUi.SemiBold, 22, BrandColors.N300);
                float top = y + 36;
                int n = Mathf.Max(1, row.choices?.Length ?? 0);
                if (n > 4)
                {
                    var value = BrandUi.Word(BrandUi.Box(setupContent, row.label + " value", Left + 76, top - 4, OptW - 160, 42), "Text", "", BrandUi.ExtraBoldItalic, 36, BrandColors.White);
                    var detail = BrandUi.Word(BrandUi.Box(setupContent, row.label + " detail", Left + 78, top + 36, OptW - 160, 28), "Text", "", BrandUi.Medium, 22, BrandColors.N300);
                    for (int side = 0; side < 2; side++)
                    {
                        var arrow = BrandUi.Box(setupContent, side == 0 ? "Previous" : "Next", side == 0 ? Left : Left + OptW - 56, top, 56, 56);
                        var face = BrandUi.Fill(arrow, "Face");
                        var fill = BrandUi.Slant(face, "Fill", BrandUi.Ink(.62f));
                        var chev = BrandUi.Layer(face, "Chevron", BrandColors.Gold, 16, -1, BrandUi.Chevron); chev.preserveAspect = true;
                        if (side == 1) chev.rectTransform.localScale = new Vector3(-1, 1, 1);
                        string key = row.key; int step = side == 0 ? -1 : 1, count = n;
                        var it = Item(arrow, face, "opt-" + key + (side == 0 ? "-prev" : "-next"), row.label + (side == 0 ? ": previous" : ": next"), () => StepOption(key, step, count), 0);
                        it.glow = k => { bool on = k > .35f; fill.color = on ? BrandColors.Gold : BrandUi.Ink(.62f); chev.color = on ? BrandColors.NavyInk : BrandColors.Gold; };
                    }
                    stepViews.Add((value, detail, row.key));
                    y = top + 70 + OptGap; continue;
                }
                float cw = (OptW - (n - 1) * 10f) / n;
                for (int k = 0; k < n; k++)
                {
                    var box = BrandUi.Box(setupContent, row.choices[k], Left + 6 + k * (cw + 10), top, cw, SegH);
                    var face = BrandUi.Fill(box, "Face");
                    var seg = new Segment { key = row.key, index = k };
                    seg.fill = BrandUi.Slant(face, "Fill", BrandUi.Ink(.58f));
                    seg.on = BrandUi.Slant(face, "On", BrandColors.White);
                    seg.edge = BrandUi.Slant(face, "Edge", BrandUi.WhiteA(.16f)); float lean = -(SegH / 2 - 2) * Mathf.Tan(14 * Mathf.Deg2Rad);   // a bottom bar shears about its own middle: line it up with the fill's foot
                    seg.edge.rectTransform.offsetMin = new Vector2(lean, 0); seg.edge.rectTransform.offsetMax = new Vector2(lean, -(SegH - 4));
                    seg.label = BrandUi.Word(face, "Text", row.choices[k], BrandUi.BoldItalic, n > 3 ? 24 : 28, BrandColors.White, TextAnchor.MiddleCenter);
                    string key = row.key; int index = k;
                    var it = Item(box, face, "opt-" + key + "-" + k, row.label + ": " + row.choices[k], () => PickOption(key, index), 0);
                    it.glow = g => { bool on = g > .35f; if (seg.lit != on) { seg.lit = on; seg.Paint(); } };
                    choiceViews.Add(seg);
                }
                y = top + SegH + OptGap;
            }
            // one gold skewed START (mock .go, bottom-left above the hint)
            var go = BrandUi.Box(setupContent, "Start", Left, Mathf.Clamp(y + 20, 866, 900), 400, 86);
            var (goFace, _) = BrandUi.GoButton(go, string.IsNullOrEmpty(s.start) ? "START" : s.start.ToUpperInvariant());
            var start = Item(go, goFace, "setup-start", string.IsNullOrEmpty(s.start) ? "START" : s.start, StartSetup, 0);
            start.glow = k => goFace.anchoredPosition = new Vector2(Nudge * .6f * k, 0);
            // the court / course strip under the card (mock .strip.r): skewed thumbnails, the picked one gold-edged and lifted
            int maps = s.maps?.Length ?? 0;
            float cardW = maps > 0 ? Mathf.Min(204, (PreviewW - 12 - (maps - 1) * 19f) / maps) : 0, cardH = cardW * 9 / 16;
            for (int i = 0; i < maps; i++)
            {
                var m = s.maps[i];
                var box = BrandUi.Box(setupContent, m.title, RightX + 12 + i * (cardW + 19), PreviewSetupY + PreviewH + 40, cardW, cardH);
                var face = BrandUi.Fill(box, "Face");
                var card = new MapCard { face = face, id = m.id };
                var ring = BrandUi.Fill(face, "Ring"); card.ring = ring.gameObject; BrandUi.Slant(ring, "Gold", BrandColors.Gold, 10, -6);
                BrandUi.Slant(face, "Edge", BrandUi.WhiteA(.3f), 10, -3);
                var (mask, pic) = PictureCard(face, 10, false, .5f);
                card.still = pic; pic.texture = Resources.Load<Texture2D>("Menu/Maps/" + setupSport + "-" + m.id); Cover(pic, cardW + 2 * (Mathf.Tan(10 * Mathf.Deg2Rad) * cardH / 2 + 4), cardH);
                card.name = BrandUi.Word(BrandUi.Box(mask, "Name", 18, cardH - 34, cardW, 28), "Text", (m.title ?? "").ToUpperInvariant(), BrandUi.ExtraBoldItalic, 20, BrandColors.White);
                string id = m.id;
                var it = Item(box, face, "map-" + id, m.title, () => PickMap(id), 0);
                it.glow = k => { card.k = k; card.Paint(); };
                mapCards.Add(card);
            }
            buildingFor = null;
        }

        void RefreshSetup()
        {
            if (setup == null) return;
            foreach (var card in mapCards) { card.picked = card.id == setup.map; card.Paint(); }
            foreach (var seg in choiceViews)
            {
                int value = 0; foreach (var row in setup.rows) if (row.key == seg.key) value = row.value;
                seg.picked = seg.index == value; seg.Paint();
            }
            foreach (var (value, detail, key) in stepViews)
                foreach (var row in setup.rows)
                    if (row.key == key && row.choices != null && row.choices.Length > 0)
                    {
                        // "Suki Tanaka · The Needle": the name big, the rest under it
                        string c = row.choices[Mathf.Clamp(row.value, 0, row.choices.Length - 1)]; int dot = c.IndexOf(" · ");
                        value.text = dot > 0 ? c.Substring(0, dot) : c; detail.text = dot > 0 ? c.Substring(dot + 3) : "";
                    }
            if (Screen == Setup) ShowMap(setup.map);
        }
        /// The card shows a court / course: its own clip, name, line and tag.
        void ShowMap(string id)
        {
            if (setup?.maps == null || previewRoot == null) return;
            foreach (var m in setup.maps)
            {
                if (m.id != id) continue;
                Clip(setupSport, m.id);
                previewTitle.text = m.title; previewLine.text = m.detail ?? "";
                bool tag = !string.IsNullOrEmpty(m.tag);
                previewTagBox.gameObject.SetActive(tag);
                if (tag)
                {
                    previewTag.text = m.tag;
                    previewTagFill.color = string.IsNullOrEmpty(m.tagHex) ? BrandColors.Royal : BrandColors.FromHex("#" + m.tagHex);
                    previewTagBox.sizeDelta = new Vector2(previewTag.preferredWidth + 40, 40);
                }
                previewChips.Set(null); PlaceCaption(false);
            }
        }

        void PickMap(string id)
        {
            if (!Leader || setup == null) return;
            setup.map = id; LastMap[setupSport] = id; RefreshSetup();
            Send("menuSet", "map|" + id);
        }
        void PickOption(string key, int index)
        {
            if (!Leader || setup == null) return;
            foreach (var row in setup.rows) if (row.key == key) row.value = index;
            RefreshSetup();
            Send("menuSet", key + "|" + index);
        }
        void StepOption(string key, int step, int count)
        {
            if (setup == null) return;
            foreach (var row in setup.rows) if (row.key == key) { PickOption(key, ((row.value + step) % count + count) % count); return; }
        }
        void StartSetup()
        {
            if (!Leader || setup == null) return;
            Send("menuSetupStart", setup.mode);
        }

        // ------------------------------------------------------------------ local golf: how many players (big skewed numerals right of the hero)
        sealed class CountCard { public RectTransform face; public Image gold; public Text num, word; public bool lit;
            public void Glow(float k)
            {
                face.anchoredPosition = new Vector2(0, 16 * k);
                bool on = k > .35f; if (on == lit) return; lit = on;
                gold.gameObject.SetActive(on); num.color = on ? BrandColors.NavyInk : BrandColors.White; word.color = on ? BrandColors.NavyDeep : BrandColors.N300;
                foreach (var s in num.GetComponents<Shadow>()) s.enabled = !on;
            } }
        void BuildPlayers(RectTransform r)
        {
            BrandUi.Headline(r, Left, 132, "Local play", "How many players?", 760);
            // the tip as a quiet line (mock .note): a gold rule, two lines of words
            BrandUi.Layer(BrandUi.Box(r, "Rule", Left, ListTop + 4, 5, 84), "Gold", BrandColors.Gold);
            BrandUi.Label(BrandUi.Box(r, "Note", Left + 26, ListTop, 600, 92), "Text", "Swing, then hand the phone on. The TV says whose turn it is.", BrandUi.Medium, 30,
                new Color(.902f, .925f, .973f), TextAnchor.UpperLeft);
            const float W = 204, H = 296, Gap = 24;
            float x0 = RightEdge - 3 * W - 2 * Gap - 6;
            for (int i = 0; i < 3; i++)
            {
                int players = i + 2;
                var box = BrandUi.Box(r, players + " players", x0 + i * (W + Gap), 308, W, H);
                var face = BrandUi.Fill(box, "Face");
                var card = new CountCard { face = face };
                BrandUi.Skewed(BrandUi.DropShadow(face, 0), 10).color = BrandUi.Ink(.45f);
                BrandUi.Slant(face, "Edge", BrandUi.WhiteA(.22f), 10, -4);
                BrandUi.Slant(face, "Fill", BrandUi.Ink(.66f), 10);
                card.gold = BrandUi.Slant(face, "Gold", Color.white, 10); HGradient.On(card.gold, BrandColors.Gold, BrandUi.GoldLight); card.gold.gameObject.SetActive(false);
                card.num = BrandUi.Ink(BrandUi.Word(BrandUi.Box(face, "Number", 0, 34, W, 140), "Text", players.ToString(), BrandUi.ExtraBoldItalic, 124, BrandColors.White, TextAnchor.MiddleCenter));
                card.word = BrandUi.Word(BrandUi.Box(face, "Word", 0, 182, W, 30), "Text", "PLAYERS", BrandUi.BoldItalic, 20, BrandColors.N300, TextAnchor.MiddleCenter);
                foreach (var s in card.word.GetComponents<Shadow>()) s.enabled = false;
                float dots = players * 24 + (players - 1) * 10, x = (W - dots) / 2;
                for (int d = 0; d < players; d++)
                {
                    var dot = BrandUi.Box(face, "Seat " + d, x + d * 34, 230, 24, 24);
                    BrandUi.Layer(dot, "Fill", GolfArcade.Hub.HubRemotes.PartyColours[d], 0, 12);
                }
                var it = Item(box, face, "players-" + players, players + " players", () => PickPlayers(players), 0);
                it.glow = card.Glow;
            }
        }
        void PickPlayers(int players)
        {
            if (!Leader) return;
            setupSport = "golf"; setupMode = "bay-golf-pass";
            ResetSetup();
            Send("menuSet", "players|" + players);
            Send("menuSetup", "bay-golf-pass");
            Go(Setup);
        }
    }
}
