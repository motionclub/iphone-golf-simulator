using System;
using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// PLAY → TRAINING → TUTORIAL, and the sport gate (PLAN_Onboarding_Tutorial_TennisQuickStart_1121.md). The first PLAY starts the whole
    /// tutorial on the phone (golf, tennis, bowling). Until a sport's lesson is done or skipped (menuTutorialState `gate`), its row says
    /// "Lesson first, or skip it", and opening it asks on the phone: play the lesson or skip it (menuOpen bay-gate-<sport>). The
    /// Tutorial screen lists the three lessons in order: done ones are ticked and replayable, the next one is lit. The phone also
    /// refuses gated bays, so the TV's styling is never the only lock.
    public sealed partial class MenuHud
    {
        public const string Tutorial = "tutorial";
        static readonly string[] Lessons = { "golf", "tennis", "bowling" };
        static readonly string[] LessonWords = { "About 2 min", "About 2 min", "About 1 min" };
        static readonly string[] Locked = { "sport-tennis", "sport-golf", "sport-bowling", "sport-daily" };

        /// The phone's state: {"locked":bool,"next":"golf","done":["golf"],"deferred":["tennis"],"gate":["tennis","bowling"]}.
        /// 11-16 (Adnan: "only force them to do one tutorial at a time"): `gate` lists the sports whose own lesson comes first; opening one
        /// of them (its modes, or golf's Daily Challenge) opens its lesson instead. `locked` is no longer sent true.
        [Serializable] public sealed class TutorialState { public bool locked; public string next = ""; public string[] done = new string[0]; public string[] deferred = new string[0]; public string[] gate = new string[0]; }
        public TutorialState LessonState { get; private set; } = new TutorialState();
        public bool TutorialLocked => LessonState.locked;

        readonly List<MenuItem> lessonRows = new List<MenuItem>();
        MenuItem tutorialEntry;
        Text tutorialCardKicker, tutorialCardTitle;
        RawImage tutorialCardPic;

        public void SetTutorial(string json)
        {
            TutorialState s = null;
            try { s = JsonUtility.FromJson<TutorialState>(json); } catch (Exception) { }
            if (s == null) return;
            LessonState = s;
            PaintTutorial();
        }

        // ---- the sports list's entry (built first in BuildSport)
        // PLAY → TRAINING (Adnan 11-19: "create a tab called training, and in there include the tutorial", under Bowling): the Tutorial lives in
        // here, with the tennis coach (the old Tennis → Training). The list's entry, then its screen.
        float TrainingEntry(RectTransform r, float y, List<MenuItem> group)
        {
            float h = WordItem(r, "sport-training", "TRAINING", "Training", "Lessons first, then a coach", Left, y, PlaySize, () => Go(Training), group);
            return h;
        }
        void BuildTraining(RectTransform r)
        {
            Heading(r, "Training", 720);
            var group = new List<MenuItem>(); float y = ListTop;
            y += WordItem(r, "sport-tutorial", "TUTORIAL", "Tutorial", "Replay a lesson", Left, y, WordSize, () => Go(Tutorial), group) + 6;
            tutorialEntry = group[group.Count - 1];
            y += WordItem(r, "bay-tennis-training", "TENNIS COACH", "Tennis coach", "Rally with no score, no pressure", Left, y, WordSize, () => OpenMode("bay-tennis-training", "Tennis coach"), group) + 6;
            BuildPreview(r, "tennis");
        }

        // ---- the Tutorial screen: the three lessons left, the next one's picture right
        void BuildTutorial(RectTransform r)
        {
            Heading(r, "Tutorial", 720);
            var group = new List<MenuItem>(); float y = ListTop;
            for (int i = 0; i < Lessons.Length; i++)
            {
                string sport = Lessons[i], word = (i + 1) + " · " + sport.ToUpperInvariant(), title = Title(sport.ToUpperInvariant()) + " lesson";
                y += WordItem(r, "bay-tutorial-" + sport, word, title, LessonWords[i], Left, y, WordSize, () => OpenPhone("bay-tutorial-" + sport, title), group) + 6;
                lessonRows.Add(group[group.Count - 1]);
            }
            BrandUi.Word(BrandUi.Box(r, "Note", Left + 10, y + 16, 720, 40), "Text", "Stand 2 m (6 ft) back from the TV.", BrandUi.MediumItalic, 28, BrandUi.WhiteA(.78f));

            const float W = PreviewW, H = PreviewH + 40;
            var card = BrandUi.Box(r, "Next", RightX, PreviewModesY, W, H);
            BrandUi.Skewed(BrandUi.DropShadow(card, 0), 4.2f, true).color = BrandUi.Ink(.45f);
            var (mask, pic) = PictureCard(card, 4.2f, true, .25f); tutorialCardPic = pic;
            var dim = BrandUi.Layer(mask, "Dim", BrandUi.Ink(.35f)); dim.raycastTarget = false; dim.transform.SetSiblingIndex(1);
            tutorialCardKicker = BrandUi.Word(BrandUi.Box(mask, "Kicker", 50, 132, 560, 34), "Text", "LESSON 1 OF 3", BrandUi.SemiBold, 24, BrandColors.Gold);
            tutorialCardTitle = BrandUi.Word(BrandUi.Box(mask, "Title", 46, 166, 600, 66), "Text", "Golf", BrandUi.ExtraBoldItalic, 56, BrandColors.White);
            PaintTutorial();
        }

        bool Done(string sport) => Array.IndexOf(LessonState.done ?? new string[0], sport) >= 0;
        /// This sport's own lesson comes first (LessonState.gate).
        public bool Gated(string sport) => Array.IndexOf(LessonState.gate ?? new string[0], sport) >= 0;
        /// A sport's screen (its modes, golf's Daily Challenge) while its lesson comes first: the phone asks, lesson or skip (true).
        bool LessonFirst(string screen)
        {
            string sport = screen == GolfModes || screen == Daily ? "golf" : screen == TennisModes ? "tennis" : screen == BowlingModes ? "bowling" : null;
            if (sport == null || !Gated(sport)) return false;
            OpenPhone("bay-gate-" + sport, Title(sport.ToUpperInvariant()) + " lesson");
            return true;
        }
        bool Deferred(string sport) => Array.IndexOf(LessonState.deferred ?? new string[0], sport) >= 0;

        /// Lock or free the sports list; tick, light or wait the lessons; aim the card at the next one.
        void PaintTutorial()
        {
            bool locked = LessonState.locked;
            if (screenItems.TryGetValue(Sport, out var sportItems))
                foreach (var it in sportItems)
                {
                    if (Array.IndexOf(Locked, it.id) < 0 || !(it.view is Word w)) continue;
                    bool first = Gated(it.id == "sport-daily" ? "golf" : it.id.Substring("sport-".Length));
                    w.off = locked; it.enabled = !locked;
                    if (w.sub)
                    {
                        const string lessonSub = "Lesson first, or skip it";
                        if (first) { if (w.sub.text != lessonSub) { lockedSubs[it.id] = w.sub.text; w.sub.text = lessonSub; } }
                        else if (lockedSubs.TryGetValue(it.id, out var was)) { w.sub.text = was; lockedSubs.Remove(it.id); }
                    }
                    FitWord(it); w.Paint();
                }
            SetSub(tutorialEntry, "Replay a lesson");
            if (locked) Primary[Sport] = "sport-training"; else Primary.Remove(Sport);
            Primary[Training] = "sport-tutorial";
            Primary[Tutorial] = string.IsNullOrEmpty(LessonState.next) ? "bay-tutorial-golf" : "bay-tutorial-" + LessonState.next;

            for (int i = 0; i < lessonRows.Count; i++)
            {
                var it = lessonRows[i]; string sport = Lessons[i];
                bool done = Done(sport);
                it.enabled = true;
                if (it.view is Word w)
                {
                    w.off = false; w.picked = done;
                    string sub = done ? "Done" : LessonWords[i];
                    if (w.sub) w.sub.text = sub;
                    FitWord(it); w.Paint();
                }
            }
            if (tutorialCardTitle)
            {
                string next = string.IsNullOrEmpty(LessonState.next) ? "golf" : LessonState.next;
                tutorialCardKicker.text = "";
                tutorialCardTitle.text = Title(next.ToUpperInvariant());
                var tex = Resources.Load<Texture2D>(next == "golf" ? "Menu/Maps/golf-cliffside" : next == "tennis" ? "Menu/Maps/tennis-resort" : "Menu/Maps/bowling-beachcourt");
                if (tex && tutorialCardPic.texture != tex) { tutorialCardPic.texture = tex; Cover(tutorialCardPic, PreviewW, PreviewH + 40); }
            }
            // a list on screen whose lit entry just locked: light the first one that can be used
            if ((Screen == Sport || Screen == Training || Screen == Tutorial) && hovered != null && !hovered.enabled) FocusAfterShow();
        }
        readonly Dictionary<string, string> lockedSubs = new Dictionary<string, string>();
        /// Tests: an item on any screen can be used (not locked).
        public bool IsEnabled(string id)
        {
            foreach (var kv in screenItems) foreach (var it in kv.Value) if (it.id == id) return it.enabled;
            return false;
        }
    }
}
