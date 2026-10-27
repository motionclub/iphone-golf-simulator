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
        static readonly Dictionary<string, (string title, string line, string[] chips)> ModeInfo = new Dictionary<string, (string, string, string[])>
        {
            { "bay-tennis-exhibition", ("Exhibition", "Play the CPU on any court, at any difficulty, for as long as you like.", new[] { "1 PLAYER", "VS CPU", "3 COURTS" }) },
            { "bay-tennis-training", ("Training", "Rally with the coach and work on your timing. No score.", new[] { "1 PLAYER", "COACH" }) },
            { "bay-tennis-nearby", ("Local play", "Friends in the same room: two phones, one TV.", new[] { "2 PLAYERS", "SAME ROOM" }) },
            { "bay-tennis-online", ("Online", "Play your friends wherever they are.", new[] { "2 PLAYERS", "ONLINE" }) },
            { "bay-golf-round", ("Round", "Play a course on your own: its own holes, 9 or 18.", new[] { "1 PLAYER", "3 COURSES" }) },
            { "bay-golf-pass", ("Local play", "One phone, passed around: swing, then hand it on.", new[] { "2-4 PLAYERS", "ONE PHONE" }) },
            { "bay-golf-online", ("Online", "Play a round with friends online.", new[] { "2-4 PLAYERS", "ONLINE" }) },
        };
        static readonly Dictionary<string, string> LastMap = new Dictionary<string, string> { { "tennis", "resort" }, { "golf", "cliffside" } };

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

        // ------------------------------------------------------------------ the preview panel (modes + setup): a gameplay clip and what it is
        RectTransform previewRoot, previewCaption, chipsRoot; RawImage previewImage; Text previewTitle, previewLine, previewTag; Image previewTagFill, previewFrame;
        VideoPlayer video; RenderTexture videoTexture; string playing;

        void BuildPreview(RectTransform screen, string sport)
        {
            if (previewRoot) return;   // one panel, shared by both modes screens and the setup screen
            previewRoot = BrandUi.Box(screensRoot, "Preview", 780, 160, 1068, 600);
            previewRoot.SetAsFirstSibling();
            BrandUi.DropShadow(previewRoot, 32);
            previewFrame = BrandUi.Layer(previewRoot, "Frame", BrandColors.White, 0, 32);
            var mask = BrandUi.Layer(previewRoot, "Mask", Color.white, 6, 27); mask.gameObject.AddComponent<Mask>().showMaskGraphic = false;
            previewImage = BrandUi.Fill(mask.transform, "Clip").gameObject.AddComponent<RawImage>(); previewImage.raycastTarget = false;
            var shade = BrandUi.Box(mask.transform, "Shade", 0, 330, 1056, 258).gameObject.AddComponent<Image>(); shade.raycastTarget = false;
            GolfArcade.Tennis.UiGradient.On(shade, new Color(BrandColors.NavyInk.r, BrandColors.NavyInk.g, BrandColors.NavyInk.b, 0), new Color(BrandColors.NavyInk.r, BrandColors.NavyInk.g, BrandColors.NavyInk.b, .95f));
            var tagBox = BrandUi.Box(mask.transform, "Tag", 26, 26, 260, 52);
            BrandUi.Layer(tagBox, "Edge", BrandColors.White, 0, 26); previewTagFill = BrandUi.Layer(tagBox, "Fill", BrandColors.Royal, 3, 23);
            previewTag = BrandUi.Label(tagBox, "Text", "", BrandUi.ExtraBoldItalic, 26, BrandColors.White, TextAnchor.MiddleCenter);
            previewCaption = BrandUi.Box(mask.transform, "Caption", 44, 380, 980, 200);
            previewTitle = BrandUi.Ink(BrandUi.Underlay(BrandUi.Label(BrandUi.Box(previewCaption, "Title", 0, 0, 980, 84), "Text", "", BrandUi.ExtraBoldItalic, 76, BrandColors.White, TextAnchor.UpperLeft)));
            previewLine = BrandUi.Ink(BrandUi.Underlay(BrandUi.Label(BrandUi.Box(previewCaption, "Line", 0, 86, 980, 52), "Text", "", BrandUi.SemiBold, BrandType.Body, BrandColors.White, TextAnchor.UpperLeft)));
            chipsRoot = BrandUi.Box(previewCaption, "Chips", 0, 142, 980, 48);
            videoTexture = new RenderTexture(1280, 720, 0) { name = "Menu preview" };
            video = previewRoot.gameObject.AddComponent<VideoPlayer>();
            video.playOnAwake = false; video.isLooping = true; video.audioOutputMode = VideoAudioOutputMode.None; video.skipOnDrop = true;
            video.renderMode = VideoRenderMode.RenderTexture; video.targetTexture = videoTexture;
            previewRoot.gameObject.SetActive(false);
        }
        void ShowPreview(bool on)
        {
            if (!previewRoot) return;
            previewRoot.gameObject.SetActive(on);
            if (!on && video && video.isPlaying) video.Stop();
            // the setup screen draws its own words under the big clip (the map's), the modes screens the mode's
            if (previewRoot.gameObject.activeSelf) previewRoot.SetSiblingIndex(0);
        }

        /// The clip and words for a mode (`id` null: the screen's first mode) on the modes screens.
        void PreviewFor(string sport, string id)
        {
            if (!previewRoot) return;
            id ??= sport == "golf" ? "bay-golf-round" : "bay-tennis-exhibition";
            if (!ModeInfo.TryGetValue(id, out var info)) return;
            Clip(sport, LastMap[sport]);
            previewTitle.text = info.title; previewLine.text = info.line;
            previewTag.transform.parent.gameObject.SetActive(false);
            Chips(info.chips);
        }
        void HoverPreview(MenuItem it)
        {
            if (it == null || previewRoot == null || !previewRoot.gameObject.activeInHierarchy) return;
            if ((Screen == TennisModes || Screen == GolfModes) && ModeInfo.ContainsKey(it.id)) PreviewFor(Screen == GolfModes ? "golf" : "tennis", it.id);
            else if (Screen == Setup && it.id.StartsWith("map-") && setup != null) ShowMap(it.id.Substring(4));
        }
        void Chips(string[] chips)
        {
            for (int c = chipsRoot.childCount - 1; c >= 0; c--) Destroy(chipsRoot.GetChild(c).gameObject);
            float x = 0;
            foreach (var chip in chips)
            {
                float w = 30 + chip.Length * 17f;
                var box = BrandUi.Box(chipsRoot, chip, x, 0, w, 46);
                BrandUi.Layer(box, "Edge", BrandColors.White, 0, 23); BrandUi.Layer(box, "Fill", BrandColors.NavyDeep, 3, 20);
                BrandUi.Label(box, "Text", chip, BrandUi.SemiBold, 24, BrandColors.White, TextAnchor.MiddleCenter);
                x += w + 14;
            }
        }
        /// Plays the gameplay clip for a court / course (Resources/Menu/Previews/<sport>-<id>, filmed from the current game 10-26), or its
        /// still (Resources/Menu/Maps/<sport>-<id>) where there is no clip.
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
        }

        // ------------------------------------------------------------------ setup: maps, options, START
        RectTransform setupContent; Text setupWait;
        readonly List<(Image ring, string id)> mapCards = new List<(Image, string)>();
        readonly List<(Image on, Text label, string key, int index)> choiceViews = new List<(Image, Text, string, int)>();
        readonly List<(Text label, string key)> stepViews = new List<(Text, string)>();
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
            setupWait = BrandUi.Ink(BrandUi.Label(BrandUi.Box(r, "Wait", 72, 500, 640, 60), "Text", "Getting your options...", BrandUi.SemiBold, BrandType.Body, BrandColors.White, TextAnchor.MiddleLeft));
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

        void BuildSetupContent(SetupState s)
        {
            for (int c = setupContent.childCount - 1; c >= 0; c--) Destroy(setupContent.GetChild(c).gameObject);
            screenItems[Setup].Clear(); mapCards.Clear(); choiceViews.Clear(); stepViews.Clear();
            setupWait.gameObject.SetActive(false);
            buildingFor = Setup;
            BrandUi.Headline(setupContent, 72, 170, s.title ?? "", s.line2 ?? "");
            // option rows: a label, then the choices side by side (the picked one white)
            int rows = s.rows?.Length ?? 0;
            float y = 430, rowH = 124, gap = 18;
            for (int i = 0; i < rows; i++)
            {
                var row = s.rows[i];
                var panel = BrandUi.Panel(setupContent, row.label, 72, y, 640, rowH, 28);
                BrandUi.Label(BrandUi.Box(panel, "Label", 0, 10, 640, 36), "Text", (row.label ?? "").ToUpperInvariant(), BrandUi.SemiBold, 26, BrandColors.Gold, TextAnchor.MiddleCenter);
                int n = Mathf.Max(1, row.choices?.Length ?? 0);
                if (n > 4)
                {
                    // a long list (the CPU opponents): ◀ the current one ▶, wrapping round
                    var stepLabel = BrandUi.Label(BrandUi.Box(panel, "Value", 90, 54, 460, 54), "Text", "", BrandUi.ExtraBoldItalic, 32, BrandColors.White, TextAnchor.MiddleCenter);
                    for (int side = 0; side < 2; side++)
                    {
                        var arrow = BrandUi.Box(panel, side == 0 ? "Previous" : "Next", side == 0 ? 16 : 640 - 16 - 64, 50, 64, 64);
                        var face = BrandUi.Fill(arrow, "Face");
                        BrandUi.Layer(face, "Gold", BrandColors.Gold, 0, 32);
                        var chev = BrandUi.Layer(face, "Chevron", BrandColors.NavyDeep, 16, -1, BrandUi.Chevron); chev.preserveAspect = true;
                        if (side == 0) chev.rectTransform.localScale = new Vector3(-1, 1, 1);
                        string key = row.key; int step = side == 0 ? -1 : 1, count = n;
                        Item(arrow, face, "opt-" + key + (side == 0 ? "-prev" : "-next"), row.label + (side == 0 ? ": previous" : ": next"), () => StepOption(key, step, count), 32);
                    }
                    stepViews.Add((stepLabel, row.key));
                    y += rowH + gap; continue;
                }
                float cw = (640 - 32 - (n - 1) * 10f) / n;
                for (int k = 0; k < n; k++)
                {
                    var box = BrandUi.Box(panel, row.choices[k], 16 + k * (cw + 10), 54, cw, 54);
                    var face = BrandUi.Fill(box, "Face");
                    BrandUi.Layer(face, "Edge", new Color(1, 1, 1, .6f), 0, 27);
                    BrandUi.Layer(face, "Fill", BrandColors.NavyDeep, 3, 24);
                    var on = BrandUi.Layer(face, "On", BrandColors.White, 0, 27);
                    var label = BrandUi.Label(face, "Text", row.choices[k].ToUpperInvariant(), BrandUi.ExtraBoldItalic, n > 3 ? 24 : 28, BrandColors.White, TextAnchor.MiddleCenter);
                    string key = row.key; int index = k;
                    Item(box, face, "opt-" + key + "-" + k, row.label + ": " + row.choices[k], () => PickOption(key, index), 27);
                    choiceViews.Add((on, label, key, k));
                }
                y += rowH + gap;
            }
            Button(setupContent, "setup-start", string.IsNullOrEmpty(s.start) ? "START" : s.start, 72, Mathf.Min(y + 10, 852), 640, 104, BrandUi.Style.Primary, StartSetup);
            // the court / course strip under the big clip: the picked one lifted with a gold edge
            int maps = s.maps?.Length ?? 0;
            float stripW = 1068, cardW = maps > 0 ? Mathf.Min(330, (stripW - (maps - 1) * 24f) / maps) : 0, cardH = cardW * 9 / 16;
            for (int i = 0; i < maps; i++)
            {
                var m = s.maps[i];
                var box = BrandUi.Box(setupContent, m.title, 780 + i * (cardW + 24), 800, cardW, cardH + 46);
                var face = BrandUi.Fill(box, "Face");
                var ring = BrandUi.Layer(BrandUi.Box(face, "Ring", -8, -8, cardW + 16, cardH + 16), "Gold", BrandColors.Gold, 0, 22);
                var pic = BrandUi.Box(face, "Picture", 0, 0, cardW, cardH);
                BrandUi.Layer(pic, "Edge", BrandColors.White, 0, 18);
                var still = BrandUi.Box(pic, "Still", 4, 4, cardW - 8, cardH - 8).gameObject.AddComponent<RawImage>(); still.raycastTarget = false;
                still.texture = Resources.Load<Texture2D>("Menu/Maps/" + setupSport + "-" + m.id);
                BrandUi.Ink(BrandUi.Underlay(BrandUi.Label(BrandUi.Box(face, "Name", 0, cardH + 8, cardW, 38), "Text", m.title, BrandUi.ExtraBoldItalic, 30, BrandColors.White, TextAnchor.MiddleCenter)));
                string id = m.id;
                Item(box, face, "map-" + id, m.title, () => PickMap(id), 18);
                mapCards.Add((ring, id));
            }
            buildingFor = null;
        }

        void RefreshSetup()
        {
            if (setup == null) return;
            foreach (var (ring, id) in mapCards) ring.gameObject.SetActive(id == setup.map);
            foreach (var (on, label, key, index) in choiceViews)
            {
                int value = 0; foreach (var row in setup.rows) if (row.key == key) value = row.value;
                bool picked = index == value;
                on.gameObject.SetActive(picked); label.color = picked ? BrandColors.NavyDeep : BrandColors.White;
            }
            foreach (var (label, key) in stepViews)
                foreach (var row in setup.rows) if (row.key == key && row.choices != null && row.choices.Length > 0) label.text = row.choices[Mathf.Clamp(row.value, 0, row.choices.Length - 1)];
            if (Screen == Setup) ShowMap(setup.map);
        }
        /// The big clip shows a court / course: its own clip, name, line and tag.
        void ShowMap(string id)
        {
            if (setup?.maps == null || previewRoot == null) return;
            foreach (var m in setup.maps)
            {
                if (m.id != id) continue;
                Clip(setupSport, m.id);
                previewTitle.text = m.title; previewLine.text = m.detail ?? "";
                bool tag = !string.IsNullOrEmpty(m.tag);
                previewTag.transform.parent.gameObject.SetActive(tag);
                if (tag)
                {
                    previewTag.text = m.tag;
                    previewTagFill.color = string.IsNullOrEmpty(m.tagHex) ? BrandColors.Royal : BrandColors.FromHex("#" + m.tagHex);
                    ((RectTransform)previewTag.transform.parent).sizeDelta = new Vector2(40 + m.tag.Length * 17f, 52);
                }
                Chips(Array.Empty<string>());
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

        // ------------------------------------------------------------------ local golf: how many players (big cards), then the course setup
        void BuildPlayers(RectTransform r)
        {
            BrandUi.Headline(r, 360, 150, "Local play", "How many players?", 1200, TextAnchor.UpperCenter);
            for (int i = 0; i < 3; i++)
            {
                int players = i + 2;
                var box = BrandUi.Box(r, players + " players", 230 + i * 500f, 430, 440, 400);
                var face = BrandUi.Fill(box, "Face");
                BrandUi.DropShadow(face, 36);
                BrandUi.Layer(face, "Edge", BrandColors.White, 0, 36); BrandUi.Layer(face, "Fill", BrandColors.NavyDeep, 6, 30);
                BrandUi.Ink(BrandUi.Label(BrandUi.Box(face, "Number", 0, 40, 440, 200), "Text", players.ToString(), BrandUi.ExtraBoldItalic, 180, BrandColors.White, TextAnchor.MiddleCenter));
                BrandUi.Label(BrandUi.Box(face, "Word", 0, 240, 440, 44), "Text", "PLAYERS", BrandUi.SemiBold, 30, BrandColors.White, TextAnchor.MiddleCenter);
                float dots = players * 56 + (players - 1) * 14, x = (440 - dots) / 2;
                for (int d = 0; d < players; d++)
                {
                    var dot = BrandUi.Box(face, "Seat " + d, x + d * 70, 306, 56, 56);
                    BrandUi.Layer(dot, "Edge", BrandColors.White, 0, 28); BrandUi.Layer(dot, "Fill", GolfArcade.Hub.HubRemotes.PartyColours[d], 4, 24);
                }
                Item(box, face, "players-" + players, players + " players", () => PickPlayers(players), 36);
            }
            var note = BrandUi.Panel(r, "How", 380, 880, 1160, 76, 38);
            BrandUi.Label(note, "Text", "Swing, then hand the phone on. The TV says whose turn it is.", BrandUi.SemiBold, BrandType.Body, BrandColors.White, TextAnchor.MiddleCenter);
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
