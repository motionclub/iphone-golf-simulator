using System.Collections.Generic;
using System.Globalization;
using GolfArcade.Game;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// DAILY CHALLENGES (Adnan 2026-11-15: "make it under the daily challenges tab (new) and make sure it's under play"): PLAY → the
    /// sports list's new DAILY CHALLENGES entry → this screen, whose first challenge is the Daily Hole in One (DailyHoleInOne.cs).
    /// Not played today: Select starts it (the phone launches it: menuDaily). Played: it opens the world board, which shows the day's
    /// score out of 3000, where it ranks (top X %, better than Y % of everyone who played), the three shots, and the world's top
    /// scores. The phone sends everything it shows as menuDailyState (DailyHoleInOne.swift boardJSON) whenever it changes, and the
    /// TV asks for a fresh board each time one of these screens opens (menuDailyLoad).
    public sealed partial class MenuHud
    {
        public const string Daily = "daily", DailyBoard = "dailyboard";
        const int BoardRows = 7;
        const float BoardRowH = 48, BoardRowsY = 618, BoardW = 700;

        HoleInOneBoard daily;
        MenuItem dailyPlay, boardPlay;
        Text dailyCountdown, dailyCardKicker, dailyCardStatus;
        Text boardScore, boardOutOf, boardStanding, boardDetail, boardNote;
        RectTransform boardScoreBox;
        readonly List<(RectTransform box, Image slash, Text rank, Text name, Text score)> boardRows = new List<(RectTransform, Image, Text, Text, Text)>();
        readonly List<(Text kicker, Text words, Text points)> boardShots = new List<(Text, Text, Text)>();

        /// The phone's description of today's challenge and the world board.
        public void SetDaily(string json)
        {
            var b = HoleInOneBoard.Parse(json);
            if (b == null) return;
            daily = b;
            PaintDaily();
        }

        // ---- the sports list's entry: DAILY CHALLENGES, in two looks. Not played yet: gold, a TODAY tag and the time left to play it (the
        // day ends at 12 midnight Eastern). Played: plain, a DONE tag and the time until the next one.
        MenuItem dailyEntry; Image dailyTagFill; Text dailyTagText; int dailyTick = -1; bool dailyEntryDone;
        float DailyEntry(RectTransform r, float y, List<MenuItem> group)
        {
            float h = WordItem(r, "sport-daily", "DAILY CHALLENGES", "Daily challenges", "Ends in 0h 00m 00s", Left, y, PlaySize, () => Go(Daily), group);
            dailyEntry = group[group.Count - 1];
            if (!(dailyEntry.view is Word w)) return h;
            float x = w.label.preferredWidth + 34, th = 38;
            var tag = BrandUi.Box(w.face, "Tag", x, 6 + (PlaySize * 1.1f - th) / 2, 120, th);
            dailyTagFill = BrandUi.Slant(tag, "Fill", BrandColors.Gold, 12);
            dailyTagText = BrandUi.Word(tag, "Text", "TODAY", BrandUi.ExtraBoldItalic, 24, BrandColors.NavyInk, TextAnchor.MiddleCenter);
            foreach (var sh in dailyTagText.GetComponents<Shadow>()) sh.enabled = false;
            dailyEntry.hit.sizeDelta = new Vector2(Mathf.Max(dailyEntry.hit.sizeDelta.x, x + 120 + 40), dailyEntry.hit.sizeDelta.y);
            PaintDailyEntry();
            return h;
        }

        // ---- the day's end: 12 midnight US Eastern (EST UTC-5, EDT UTC-4 from the second Sunday of March to the first of November)
        static bool IsUsDst(System.DateTime utc)
        {
            static System.DateTime NthSunday(int year, int month, int n)
            {
                var d = new System.DateTime(year, month, 1, 0, 0, 0, System.DateTimeKind.Utc);
                return d.AddDays(((int)System.DayOfWeek.Sunday - (int)d.DayOfWeek + 7) % 7 + 7 * (n - 1));
            }
            var start = NthSunday(utc.Year, 3, 2).AddHours(7);   // 2:00 am EST
            var end = NthSunday(utc.Year, 11, 1).AddHours(6);    // 2:00 am EDT
            return utc >= start && utc < end;
        }
        static System.TimeSpan UntilEasternMidnight(System.DateTime utcNow)
        {
            var et = utcNow.AddHours(IsUsDst(utcNow) ? -4 : -5);
            return et.Date.AddDays(1) - et;
        }
        /// "5h 12m 09s" (under an hour "12m 09s").
        static string Countdown(System.TimeSpan t)
        {
            int s = Mathf.Max(0, (int)t.TotalSeconds);
            return s >= 3600 ? $"{s / 3600}h {s / 60 % 60:00}m {s % 60:00}s" : $"{s / 60}m {s % 60:00}s";
        }
        public static string EasternCountdownNow() => Countdown(UntilEasternMidnight(System.DateTime.UtcNow));

        /// Once a second while a screen that shows the countdown is up.
        void TickDaily()
        {
            if (Screen != Sport && Screen != Daily && Screen != DailyBoard) return;
            int tick = (int)UntilEasternMidnight(System.DateTime.UtcNow).TotalSeconds;
            if (tick == dailyTick) return;
            dailyTick = tick;
            PaintDailyEntry();
            PaintDailyCountdown();
        }
        void PaintDailyEntry()
        {
            if (dailyEntry == null || !(dailyEntry.view is Word w)) return;
            bool done = daily != null && daily.played;
            string left = EasternCountdownNow();
            if (w.sub) { string sub = done ? "Done · next one in " + left : "Ends in " + left; if (w.sub.text != sub) { w.sub.text = sub; FitWord(dailyEntry); } }
            if (done != dailyEntryDone || w.picked == done)
            {
                dailyEntryDone = done;
                w.picked = !done; w.subRest = done ? SubRest : BrandColors.Gold;
                dailyTagFill.color = done ? BrandColors.Success : BrandColors.Gold; dailyTagText.text = done ? "DONE" : "TODAY";
                w.Paint();
            }
        }
        void PaintDailyCountdown()
        {
            if (daily == null && dailyCountdown) { dailyCountdown.text = ""; return; }
            bool played = daily != null && daily.played;
            if (dailyCountdown) dailyCountdown.text = played ? "Done for today · next challenge in " + EasternCountdownNow() : "Ends in " + EasternCountdownNow() + " · 12 midnight Eastern";
        }

        // ---- Daily Challenges: the day's challenges left, today's card right
        void BuildDaily(RectTransform r)
        {
            Heading(r, "Daily Challenges", 760);
            var group = new List<MenuItem>(); float y = ListTop;
            y += WordItem(r, "daily-holeinone", "DAILY HOLE IN ONE", "Daily Hole in One", "3 shots · 125–175 ft · out of 3,000", Left, y, WordSize, PressHoleInOne, group) + 6;
            dailyPlay = group[group.Count - 1];
            y += WordItem(r, "daily-board", "WORLD LEADERBOARD", "World leaderboard", "Today's top scores, worldwide", Left, y, WordSize, () => Go(DailyBoard), group) + 6;
            dailyCountdown = BrandUi.Word(BrandUi.Box(r, "Countdown", Left + 10, y + 18, 760, 40), "Text", "", BrandUi.MediumItalic, 28, BrandColors.Gold);

            // today's card, right of the hero (the preview card's place and size): a course still, the rules, your score once played
            const float W = PreviewW, H = PreviewH + 40;
            var card = BrandUi.Box(r, "Today", RightX, PreviewModesY, W, H);
            BrandUi.Skewed(BrandUi.DropShadow(card, 0), 4.2f, true).color = BrandUi.Ink(.45f);
            var (mask, pic) = PictureCard(card, 4.2f, true, .25f);
            pic.texture = Resources.Load<Texture2D>("Menu/Maps/golf-cliffside"); Cover(pic, W, H);
            // the words sit over the sky as well as the turf: the whole picture a shade darker under them
            var dim = BrandUi.Layer(mask, "Dim", BrandUi.Ink(.42f)); dim.raycastTarget = false; dim.transform.SetSiblingIndex(1);
            dailyCardKicker = BrandUi.Word(BrandUi.Box(mask, "Kicker", 50, 132, 560, 34), "Text", "TODAY'S CHALLENGE", BrandUi.SemiBold, 24, BrandColors.Gold);
            BrandUi.Word(BrandUi.Box(mask, "Title", 46, 166, 600, 66), "Text", "Daily Hole in One", BrandUi.ExtraBoldItalic, 56, BrandColors.White);
            BrandUi.Label(BrandUi.Box(mask, "Line", 50, 236, 570, 96), "Text",
                "Three shots from 125–175 ft. Hole it for 1,000; a miss scores up to 800, more the closer it stops. Everyone in the world plays the same three shots today.",
                BrandUi.Medium, 24, new Color(.863f, .89f, .949f), TextAnchor.UpperLeft);
            dailyCardStatus = BrandUi.Word(BrandUi.Box(mask, "Status", 50, H - 62, 570, 40), "Text", "", BrandUi.ExtraBoldItalic, 30, BrandColors.Gold);
        }

        void PressHoleInOne()
        {
            if (!Leader) return;
            if (daily != null && daily.played && daily.day > 0) { Go(DailyBoard); return; }   // one go a day: the board instead
            Send("menuDaily", "holeinone");
        }

        // ---- the world board: your day left (score, rank, the board), your three shots right
        void BuildDailyBoard(RectTransform r)
        {
            Heading(r, "Hole in One", 760);
            var group = new List<MenuItem>();
            WordItem(r, "board-play", "PLAY TODAY'S SHOTS", "Play today's shots", "You haven't played today's challenge yet", Left, ListTop, WordSize, PressHoleInOne, group);
            boardPlay = group[group.Count - 1];
            boardScoreBox = BrandUi.Box(r, "Score", Left, ListTop - 12, BoardW, 230);
            boardScore = BrandUi.Word(BrandUi.Box(boardScoreBox, "Total", 0, 0, 420, 124), "Text", "", BrandUi.ExtraBoldItalic, 112, BrandColors.Gold);
            boardOutOf = BrandUi.Word(BrandUi.Box(boardScoreBox, "Out of", 0, 52, 300, 60), "Text", "/ 3,000", BrandUi.ExtraBoldItalic, 40, BrandUi.WhiteA(.85f));
            boardStanding = BrandUi.Word(BrandUi.Box(boardScoreBox, "Standing", 2, 124, BoardW, 54), "Text", "", BrandUi.ExtraBoldItalic, 44, BrandColors.White);
            boardDetail = BrandUi.Word(BrandUi.Box(boardScoreBox, "Detail", 4, 180, BoardW, 38), "Text", "", BrandUi.Medium, 26, BrandUi.WhiteA(.8f));
            for (int i = 0; i < BoardRows; i++)
            {
                var box = BrandUi.Box(r, "Row " + i, Left, BoardRowsY + i * BoardRowH, BoardW, BoardRowH - 6);
                var slash = BrandUi.Slant(box, "Me", BrandColors.Gold, 12);
                var rank = BrandUi.Word(BrandUi.Box(box, "Rank", 16, 0, 90, BoardRowH - 6), "Text", "", BrandUi.ExtraBoldItalic, 28, BrandColors.Gold);
                var name = BrandUi.Word(BrandUi.Box(box, "Name", 110, 0, 430, BoardRowH - 6), "Text", "", BrandUi.SemiBold, 28, BrandColors.White);
                var score = BrandUi.Word(BrandUi.Box(box, "Score", BoardW - 190, 0, 170, BoardRowH - 6), "Text", "", BrandUi.ExtraBoldItalic, 30, BrandColors.White, TextAnchor.MiddleRight);
                boardRows.Add((box, slash, rank, name, score));
            }
            boardNote = BrandUi.Word(BrandUi.Box(r, "Note", Left + 6, BoardRowsY + 6, BoardW, 40), "Text", "", BrandUi.MediumItalic, 28, BrandUi.WhiteA(.8f));

            // your three shots, right of the hero
            var card = BrandUi.Box(r, "Shots", RightX, PreviewSetupY + 40, PreviewW, 420);
            BrandUi.Skewed(BrandUi.Layer(card, "Fill", BrandUi.Ink(.62f)), 4.2f, true);
            BrandUi.Word(BrandUi.Box(card, "Kicker", 52, 24, 560, 34), "Text", "YOUR SHOTS TODAY", BrandUi.SemiBold, 24, BrandColors.Gold);
            for (int i = 0; i < DailyHoleInOne.Shots; i++)
            {
                float y = 76 + i * 112;
                var k = BrandUi.Word(BrandUi.Box(card, "Shot " + i, 52, y, 300, 30), "Text", $"SHOT {i + 1}", BrandUi.SemiBold, 22, BrandUi.WhiteA(.7f));
                var words = BrandUi.Word(BrandUi.Box(card, "Words " + i, 50, y + 30, 400, 60), "Text", "", BrandUi.ExtraBoldItalic, 48, BrandColors.White);
                var points = BrandUi.Word(BrandUi.Box(card, "Points " + i, PreviewW - 250, y + 30, 200, 60), "Text", "", BrandUi.ExtraBoldItalic, 48, BrandColors.Gold, TextAnchor.MiddleRight);
                boardShots.Add((k, words, points));
            }
        }

        /// Both screens' words from the latest board (nothing yet: the plain rules and "loading").
        void PaintDaily()
        {
            if (dailyPlay == null) return;
            var b = daily; var inv = CultureInfo.InvariantCulture;
            bool played = b != null && b.played;
            string standing = b != null && b.Ranked ? $"Top {b.top}% in the world" : null;
            // Daily Challenges
            SetSub(dailyPlay, played ? $"Done · {b.total.ToString("N0", inv)} pts{(standing != null ? " · Top " + b.top + "%" : "")}" : "3 shots · 125–175 ft · out of 3,000");
            PaintDailyCountdown(); PaintDailyEntry();
            // two looks: not played yet, the card is gold ("PLAY NOW", time left); played, it says DONE with your score and the time to the next
            if (dailyCardStatus)
            {
                dailyCardStatus.text = played ? $"DONE  ·  {b.total.ToString("N0", inv)} / 3,000  ·  NEXT IN {EasternCountdownNow()}" : $"PLAY NOW  ·  ENDS IN {EasternCountdownNow()}";
                dailyCardStatus.color = played ? BrandColors.White : BrandColors.Gold;
            }
            if (dailyCardKicker) dailyCardKicker.text = b != null && b.day > 0 ? "TODAY'S CHALLENGE  ·  " + DayWords(b.day) : "TODAY'S CHALLENGE";
            // the board
            if (!boardScoreBox) return;
            boardPlay.hit.gameObject.SetActive(!played);
            boardScoreBox.gameObject.SetActive(played);
            if (played)
            {
                boardScore.text = b.total.ToString("N0", inv);
                var outOf = (RectTransform)boardOutOf.transform.parent; outOf.anchoredPosition = new Vector2(boardScore.preferredWidth + 18, outOf.anchoredPosition.y);
                boardStanding.text = standing ?? (b.state == "live" ? "Ranking you…" : "World ranking");
                boardDetail.text = b.Ranked
                    ? $"Better than {b.percentile}% of {b.players.ToString("N0", inv)} player{(b.players == 1 ? "" : "s")}  ·  #{b.rank.ToString("N0", inv)}"
                    : b.note ?? "";
            }
            var entries = b?.entries ?? new HoleInOneBoardEntry[0];
            // the top rows, and your own row last when you are below them
            var shown = new List<HoleInOneBoardEntry>();
            bool meShown = false;
            foreach (var e in entries) { if (shown.Count >= BoardRows) break; shown.Add(e); meShown |= e.me; }
            if (!meShown && b != null && b.Ranked && played)
            {
                if (shown.Count >= BoardRows) shown.RemoveAt(shown.Count - 1);
                shown.Add(new HoleInOneBoardEntry { rank = b.rank, name = "You", score = b.total, me = true });
            }
            for (int i = 0; i < boardRows.Count; i++)
            {
                var (box, slash, rank, name, score) = boardRows[i];
                bool on = i < shown.Count; box.gameObject.SetActive(on);
                if (!on) continue;
                var e = shown[i];
                slash.gameObject.SetActive(e.me);
                rank.text = "#" + e.rank.ToString("N0", inv); name.text = string.IsNullOrEmpty(e.name) ? "Player" : e.name; score.text = e.score.ToString("N0", inv);
                var ink = e.me ? BrandColors.NavyInk : BrandColors.White;
                rank.color = e.me ? BrandColors.NavyInk : BrandColors.Gold; name.color = ink; score.color = ink;
                foreach (var t in new[] { rank, name, score }) foreach (var s in t.GetComponents<Shadow>()) s.enabled = !e.me;
            }
            boardNote.gameObject.SetActive(shown.Count == 0);
            boardNote.text = b == null ? "Loading the world leaderboard…" : !string.IsNullOrEmpty(b.note) ? b.note : "No scores yet today. Be the first!";
            for (int i = 0; i < boardShots.Count; i++)
            {
                var (k, words, points) = boardShots[i];
                bool has = played && b.shots != null && i < b.shots.Length;
                float feet = has && b.feet != null && i < b.feet.Length ? b.feet[i] : -1;
                bool holed = has && b.shots[i] >= DailyHoleInOne.Holed;
                words.text = has ? DailyHoleInOne.Words(feet, holed) : "—";
                points.text = has ? b.shots[i].ToString("N0", inv) : "";
            }
        }

        static void SetSub(MenuItem it, string text)
        {
            if (it == null || !(it.view is Word w) || !w.sub || w.sub.text == text) return;
            w.sub.text = text; FitWord(it); w.Paint();
        }

        static string DayWords(int day)
        {
            int y = day / 10000, m = day / 100 % 100, d = day % 100;
            if (m < 1 || m > 12 || d < 1) return "";
            return CultureInfo.InvariantCulture.DateTimeFormat.GetAbbreviatedMonthName(m).ToUpperInvariant() + " " + d + ", " + y;
        }

        /// One of the daily screens opened: draw what we have and ask the phone for a fresh board.
        void EnterDaily()
        {
            PaintDaily();
            Send("menuDailyLoad", "");
        }
    }
}
