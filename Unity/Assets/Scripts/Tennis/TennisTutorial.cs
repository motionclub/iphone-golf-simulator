using System;
using System.Collections.Generic;
using GolfArcade.Game;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// The tennis lesson on the Practice Court (PLAN_Onboarding_GolfLesson.md). The phone runs the court setup first (station 1:
    /// point at the TV, sync); these are stations 2–3: hit two of Coach Ray's feeds back (a forehand, then a backhand: the
    /// player picks the wing from the ball, so there is nothing new to learn for it), then land a serve. Misses retry; the phone
    /// offers a skip. The phone shows the title and one line (ask, then the attempt text, then the hint after two misses); the
    /// game's HUD already shows the timing grade, so the text never repeats it. (2026-11-16, Adnan: "tutorial length should be
    /// 1-2 mins per sport max": Pace, Aim, Wide and the played point were cut.)
    public sealed class TutorialLesson
    {
        public enum Kind { Hit, Serve }
        public struct Step { public Kind Kind; public string Key, Name, Title, Say, Hint; public string[] Tips; public int Goal; }
        public static readonly Step[] Steps =
        {
            new Step { Kind = Kind.Hit, Goal = 2, Key = "hit", Name = "Hit", Title = "Hit it back",
                Say = "Swing as the rings close on the ball.",
                Hint = "Swing early rather than late.",
                Tips = new string[0] },
            new Step { Kind = Kind.Serve, Goal = 1, Key = "serve", Name = "Serve", Title = "Serve",
                Say = "Tap TOSS, then swing overhead at the top.",
                Hint = "Tap TOSS on the green, then swing as the ball peaks.",
                Tips = new string[0] },
        };
        public const int HintAfter = 2;
        /// The phone's own stations before these (court setup), so the TV counts 1–3.
        public const int PhoneStations = 1;
        public int Index { get; private set; }
        public TutorialLesson(int start = 0) { Index = Mathf.Clamp(start, 0, Steps.Length - 1); }
        public int Progress { get; private set; }
        public int Misses { get; private set; }
        public bool Done => Index >= Steps.Length;
        public Step Current => Steps[Mathf.Min(Index, Steps.Length - 1)];
        public string Instruction => Current.Say;
        public bool Success()
        {
            if (Done) return false;
            if (++Progress < Current.Goal) return false;
            Next(); return true;
        }
        public bool Miss() { if (!Done) Misses++; return false; }
        public bool HintDue => Misses >= HintAfter;
        public void Skip() { if (!Done) Next(); }
        void Next() { Index++; Progress = 0; Misses = 0; }
    }

    public sealed class TennisTutorial : MonoBehaviour
    {
        public static event Action<int, int, string> StepChanged;
        public static event Action Finished;
        public static event Action<int, int, bool> StepResolved;
        public static int StartIndex;
        public TutorialLesson Lesson { get; private set; } = new TutorialLesson();
        TennisGame game;
        TennisCoach coach;
        float feedAt = -1, serveAt = -1, watchdog = -1;
        bool resolved, active, tipsBefore, pendingStep;

        public void Begin(TennisGame g, TennisCoach c)
        {
            Stop(); game = g; coach = c; Lesson = new TutorialLesson(StartIndex); StartIndex = 0; active = true;
            tipsBefore = TennisCoach.TipsEnabled; TennisCoach.TipsEnabled = false;
            TennisGame.Landed += OnLanded; TennisGame.DrillPoint += OnDrillPoint;
            StartStep();
        }
        public void Stop()
        {
            if (!active) return;
            active = false;
            TennisGame.Landed -= OnLanded; TennisGame.DrillPoint -= OnDrillPoint;
            TennisCoach.TipsEnabled = tipsBefore;
            if (game) game.Drill = false;
        }
        void OnDestroy() => Stop();
        /// The phone's "Skip this step" (offered after three misses); missing balls never silently passes a station.
        public void SkipStep()
        {
            if (!active || pendingStep) return;
            StepResolved?.Invoke(Lesson.Index, Lesson.Misses, true);
            Lesson.Skip(); Advance(true);
        }
        static bool Reporting => NativeSportsSession.LessonReport != null;
        static void Report(string json) => NativeSportsSession.LessonReport?.Invoke(json);
        void ShowInstruction()
        {
            string text = Lesson.HintDue ? Lesson.Current.Hint : Lesson.Instruction;
            StepChanged?.Invoke(Lesson.Index, TutorialLesson.Steps.Length, text);
            // the phone draws the lesson over the TV; the coach's own bubble is for runs without it (the editor)
            if (coach && !Reporting) coach.Say(text, 1e6f);
        }
        void StartStep()
        {
            pendingStep = false; feedAt = serveAt = watchdog = -1; resolved = true;
            if (Lesson.Done) { Finish(); return; }
            var s = Lesson.Current;
            Report(LessonJson.Station("tennis", Lesson.Index + TutorialLesson.PhoneStations, TutorialLesson.Steps.Length + TutorialLesson.PhoneStations,
                s.Key, s.Name, s.Title, s.Say, s.Hint, s.Tips));
            ShowInstruction();
            game.Drill = true;
            game.PrepareLesson();
            if (s.Kind == TutorialLesson.Kind.Serve) serveAt = Time.time + 1.2f;
            else feedAt = Time.time + 1.8f;
        }
        void Finish()
        {
            if (!active) return;
            if (coach && !Reporting) coach.Say("You're ready.", 10);
            game.Drill = false;
            Report(LessonJson.Done("tennis"));
            Finished?.Invoke(); Stop();
        }
        void Update()
        {
            if (!active || !game || !game.Player || Time.timeScale == 0 || game.CheckingTiming) return;
            if (pendingStep) { StartStep(); return; }
            if (feedAt >= 0 && Time.time >= feedAt)
            {
                // the first ball to the forehand, the second to the backhand: the player picks the wing from the ball
                feedAt = -1; resolved = false; watchdog = Time.time + 6f;
                game.Feed(Lesson.Progress % 2 == 1);
            }
            if (serveAt >= 0 && Time.time >= serveAt) { serveAt = -1; resolved = false; game.StartPlayerServe(); }
            if (watchdog >= 0 && Time.time >= watchdog)
            {
                watchdog = -1;
                if (!resolved) { resolved = true; Missed(LateText, "MISSED"); }
                NextBall();
            }
        }
        void Advance(bool stepEnded)
        {
            if (stepEnded)
            {
                // Landed callbacks run inside physics. Let the old point finish first.
                pendingStep = true; feedAt = serveAt = watchdog = -1; return;
            }
            ShowInstruction();
        }
        void NextBall()
        {
            if (Lesson.Done || pendingStep) return;
            if (Lesson.Current.Kind == TutorialLesson.Kind.Serve) { if (serveAt < 0) serveAt = Time.time + 1.4f; }
            else if (feedAt < 0) feedAt = Time.time + 1.6f;
        }

        // MARK: Judging

        const string LateText = "Swing a little sooner.";
        /// A fault's one fix: a loose toss first (the HUD's LOOSE / WILD TOSS), otherwise the swing's timing.
        string FaultText => game.TossAccuracy <= .6f ? "Tap TOSS as the marker crosses the green." : "Swing as the ball reaches the top.";

        void Passed(string text, string grade)
        {
            int index = Lesson.Index, misses = Lesson.Misses;
            bool ended = Lesson.Success();
            Report(LessonJson.Attempt(ended, grade, ended ? text : "Next one comes to your backhand.", misses, null));
            if (ended) StepResolved?.Invoke(index, misses, false);
            Advance(ended);
        }
        void Missed(string text, string grade)
        {
            Lesson.Miss();
            Report(LessonJson.Attempt(false, grade, text, Lesson.Misses, null));
            Advance(false);
        }

        void OnLanded(bool byPlayer, bool landedIn, Vector3 where, bool serve)
        {
            if (!active || pendingStep || !byPlayer || resolved) return;
            var kind = Lesson.Current.Kind;
            if (kind == TutorialLesson.Kind.Serve && !serve) return;
            resolved = true;
            if (kind == TutorialLesson.Kind.Serve)
            {
                if (landedIn) Passed("In.", "IN");
                else Missed(FaultText, "FAULT");
            }
            else Passed("Nice.", TennisRules.GradeLabel(game.LastGrade));
            if (serve) NextBall();
        }
        void OnDrillPoint(bool toPlayer, string why)
        {
            if (!active || pendingStep) return;
            if (!resolved)
            {
                resolved = true;
                if (Lesson.Current.Kind == TutorialLesson.Kind.Serve) Missed(FaultText, "FAULT");
                else Missed(LateText, "LATE");
            }
            watchdog = -1; NextBall();
        }
    }
}
