using System;
using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// PLAY → TUTORIAL (PLAN_Onboarding_v3_IntroTutorial.md, Adnan 2026-11-15: "once they do, everything is locked except a section called
    /// tutorial … golf first, then tennis, then bowling … once they are completely done they are free to play everything else").
    /// The sports list gets a TUTORIAL entry on top. Until the phone says the lessons are done (menuTutorialState), Tennis, Golf, Bowling
    /// and Daily Challenges are dimmed and say so, and TUTORIAL is lit first. The Tutorial screen lists the three lessons in order: done
    /// ones are ticked and replayable, the next one is lit, later ones wait. Pressing one opens its how-to-play and safety card on the
    /// phone (menuOpen bay-tutorial-<sport>); the phone also refuses locked bays, so the TV's styling is never the only lock.
    public sealed partial class MenuHud
    {
        public const string Tutorial = "tutorial";
        static readonly string[] Lessons = { "golf", "tennis", "bowling" };
        static readonly string[] LessonWords = { "Swing, distance, aim and putting · about 6 min", "Calibrate to your TV, then rally · about 6 min", "Roll, aim and spin · about 3 min" };
        static readonly string[] Locked = { "sport-tennis", "sport-golf", "sport-bowling", "sport-daily" };

        /// The phone's state: {"locked":bool,"next":"golf","done":["golf"],"deferred":["tennis"]}.
        [Serializable] public sealed class TutorialState { public bool locked; public string next = ""; public string[] done = new string[0]; public string[] deferred = new string[0]; }
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
        float TutorialEntry(RectTransform r, float y, List<MenuItem> group)
        {
            float h = WordItem(r, "sport-tutorial", "TUTORIAL", "Tutorial", "Replay a lesson", Left, y, WordSize, () => Go(Tutorial), group);
            tutorialEntry = group[group.Count - 1];
            return h;
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
            BrandUi.Label(BrandUi.Box(mask, "Line", 50, 236, 570, 96), "Text",
                "Each lesson starts on your phone: how to stand and swing, then a quick safety check. Then the coach takes you through it, one step at a time.",
                BrandUi.Medium, 24, new Color(.863f, .89f, .949f), TextAnchor.UpperLeft);
            PaintTutorial();
        }

        bool Done(string sport) => Array.IndexOf(LessonState.done ?? new string[0], sport) >= 0;
        bool Deferred(string sport) => Array.IndexOf(LessonState.deferred ?? new string[0], sport) >= 0;

        /// Lock or free the sports list; tick, light or wait the lessons; aim the card at the next one.
        void PaintTutorial()
        {
            bool locked = LessonState.locked;
            if (screenItems.TryGetValue(Sport, out var sportItems))
                foreach (var it in sportItems)
                {
                    if (Array.IndexOf(Locked, it.id) < 0 || !(it.view is Word w)) continue;
                    if (w.off == locked && it.enabled == !locked) continue;
                    w.off = locked; it.enabled = !locked;
                    if (w.sub)
                    {
                        if (locked) { if (!w.sub.text.StartsWith("Finish the tutorial")) { lockedSubs[it.id] = w.sub.text; w.sub.text = "Finish the tutorial to unlock"; } }
                        else if (lockedSubs.TryGetValue(it.id, out var was)) w.sub.text = was;
                    }
                    FitWord(it); w.Paint();
                }
            SetSub(tutorialEntry, locked ? "Start here · golf, tennis, bowling" : "Replay a lesson");
            if (locked) Primary[Sport] = "sport-tutorial"; else Primary.Remove(Sport);
            Primary[Tutorial] = string.IsNullOrEmpty(LessonState.next) ? "bay-tutorial-golf" : "bay-tutorial-" + LessonState.next;

            for (int i = 0; i < lessonRows.Count; i++)
            {
                var it = lessonRows[i]; string sport = Lessons[i];
                bool done = Done(sport), next = LessonState.next == sport, later = !done && !next && !Deferred(sport);
                it.enabled = !later;
                if (it.view is Word w)
                {
                    w.off = later; w.picked = done && !next;
                    string sub = done ? "Done · play it again any time" : Deferred(sport) ? "Waiting for a TV · " + LessonWords[i] : later ? "Finish " + Lessons[Mathf.Max(0, i - 1)] + " first" : LessonWords[i];
                    if (w.sub) w.sub.text = sub;
                    FitWord(it); w.Paint();
                }
            }
            if (tutorialCardTitle)
            {
                string next = string.IsNullOrEmpty(LessonState.next) ? "golf" : LessonState.next;
                int n = Array.IndexOf(Lessons, next);
                tutorialCardKicker.text = string.IsNullOrEmpty(LessonState.next) ? "ALL LESSONS DONE" : "LESSON " + (n + 1) + " OF 3  ·  UP NEXT";
                tutorialCardTitle.text = Title(next.ToUpperInvariant());
                var tex = Resources.Load<Texture2D>(next == "golf" ? "Menu/Maps/golf-cliffside" : next == "tennis" ? "Menu/Maps/tennis-resort" : "Menu/Maps/bowling-club");
                if (tex && tutorialCardPic.texture != tex) { tutorialCardPic.texture = tex; Cover(tutorialCardPic, PreviewW, PreviewH + 40); }
            }
            // a list on screen whose lit entry just locked: light the first one that can be used
            if ((Screen == Sport || Screen == Tutorial) && hovered != null && !hovered.enabled) FocusAfterShow();
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
