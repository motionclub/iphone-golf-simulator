using System;
using System.Collections.Generic;
using GolfArcade.Game;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// The tennis lesson on the Practice Court (PLAN_Onboarding_GolfLesson.md). The phone runs the court setup first (station 1:
    /// point at the TV, sync); these are stations 2–8, each teaching one thing the rally really measures (the 10-24 rules: the racket
    /// face picks the side, timing picks pace and depth, an early swing is held back). Misses retry; the phone offers a skip.
    public sealed class TutorialLesson
    {
        public enum Kind { Serve, Forehand, Backhand, Aim, Point, Pace, Dive }
        public struct Step { public Kind Kind; public string Key, Name, Title, Say, Hint; public string[] Tips; public int Goal; }
        public static readonly Step[] Steps =
        {
            new Step { Kind = Kind.Forehand, Goal = 2, Key = "forehand", Name = "Forehand", Title = "Forehand on the rings",
                Say = "Coach Ray feeds you a ball. Your player runs to it. Swing as the green rings close on the ball.",
                Hint = "Start the swing as the rings meet the ball. Early is fine: your player holds the racket back and still hits it.",
                Tips = new[] { "Coach Ray feeds the ball. Your player runs to it for you.", "Green rings shrink onto the ball as it comes.", "Swing when they meet the ball. A smooth swing is plenty." } },
            new Step { Kind = Kind.Pace, Goal = 1, Key = "pace", Name = "Timing", Title = "Timing sets the pace",
                Say = "Hit one GREAT or better. Swing exactly as the ball reaches you. Swinging harder barely changes the pace.",
                Hint = "Wait a beat longer. Swing as the rings meet the ball, not when you first see it bounce.",
                Tips = new[] { "Right on the ball is your fastest shot, and it lands deep.", "Early: your player holds the swing back, so it's slow and short.", "Three GREAT hits in a row charge a SUPERCHARGED shot." } },
            new Step { Kind = Kind.Backhand, Goal = 1, Key = "backhand", Name = "Backhand", Title = "Backhand",
                Say = "This ball comes to your other side. Swing across your body and get one back.",
                Hint = "Turn your shoulders while the ball is coming, then swing across your chest on the rings.",
                Tips = new[] { "The side the ball is on picks forehand or backhand.", "No need to change your grip.", "Same timing as the forehand." } },
            new Step { Kind = Kind.Aim, Goal = 2, Key = "aim", Name = "Aim", Title = "Aim with the racket face",
                Say = "Hit one into the LEFT ring, then one into the RIGHT ring. Clean timing lets the ball go closer to the lines.",
                Hint = "Finish the swing with the racket face turned toward that side of the TV, about a quarter turn.",
                Tips = new[] { "The ball goes where your racket face points at contact.", "Three lanes: left, straight, right.", "A quarter turn picks a side lane." } },
            new Step { Kind = Kind.Serve, Goal = 1, Key = "serve", Name = "Serve", Title = "Serve",
                Say = "Tap TOSS on your phone as the ticker crosses the middle, then swing overhead at the top. Land one in the box.",
                Hint = "Tap TOSS, watch the ball rise on the TV, and wait for the power bar to peak before you swing.",
                Tips = new[] { "Tap TOSS as the meter's ticker crosses the green middle.", "Swing overhead as the power bar peaks with the ball.", "Tap the box on your phone to aim; the middle is safest." } },
            new Step { Kind = Kind.Dive, Goal = 1, Key = "dive", Name = "Run and dive", Title = "Run and dive",
                Say = "Coach Ray hits one wide. Tap DIVE on your phone to reach it.",
                Hint = "Tap DIVE the moment the ball heads away from you. It only works with a ball coming.",
                Tips = new[] { "Your player runs to every ball and sprints for a hard one.", "Too wide? Tap DIVE on your phone.", "A dive costs stamina and needs about 2.5 s to recharge." } },
            new Step { Kind = Kind.Point, Goal = 1, Key = "point", Name = "Play a point", Title = "Play a real point",
                Say = "Serve, then rally with Coach Ray. Win or lose, the lesson is complete.",
                Hint = "Aim away from Coach Ray and keep your timing smooth: placement wins points.",
                Tips = new[] { "You serve first.", "Aim away from Coach Ray.", "Win or lose, the lesson is complete." } },
        };
        public const int HintAfter = 2;
        /// The phone's own stations before these (court setup), so the TV counts 1–8.
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
        LineRenderer marker;
        float feedAt = -1, serveAt = -1, watchdog = -1;
        bool resolved, active, tipsBefore, pendingStep;
        int feeds, divesAtFeed;
        static readonly Color Gold = new Color(1, .82f, .15f);
        static readonly Vector3 LeftRing = new(-2.5f, .06f, 8f), RightRing = new(2.5f, .06f, 8f);

        public void Begin(TennisGame g, TennisCoach c)
        {
            Stop(); game = g; coach = c; Lesson = new TutorialLesson(StartIndex); StartIndex = 0; active = true; feeds = 0;
            tipsBefore = TennisCoach.TipsEnabled; TennisCoach.TipsEnabled = false;
            TennisGame.Landed += OnLanded; TennisGame.DrillPoint += OnDrillPoint; TennisGame.ScoreChanged += OnScore;
            if (!marker) marker = game.MakeMarker("Tutorial target", Gold);
            StartStep();
        }
        public void Stop()
        {
            if (!active) return;
            active = false;
            TennisGame.Landed -= OnLanded; TennisGame.DrillPoint -= OnDrillPoint; TennisGame.ScoreChanged -= OnScore;
            TennisCoach.TipsEnabled = tipsBefore;
            if (game) game.Drill = false;
            if (marker) marker.enabled = false;
        }
        void OnDestroy() { Stop(); if (marker) Destroy(marker.gameObject); }
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
            game.Drill = s.Kind != TutorialLesson.Kind.Point;
            game.PrepareLesson();
            if (s.Kind == TutorialLesson.Kind.Serve || s.Kind == TutorialLesson.Kind.Point) serveAt = Time.time + 1.2f;
            else feedAt = Time.time + 1.8f;
        }
        void Finish()
        {
            if (!active) return;
            if (coach && !Reporting) coach.Say("You're ready. See you on the Island Circuit!", 10);
            if (marker) marker.enabled = false;
            game.Drill = false;
            Report(LessonJson.Done("tennis"));
            Finished?.Invoke(); Stop();
        }
        void Update()
        {
            if (!active || !game || !game.Player || Time.timeScale == 0 || game.CheckingTiming) return;
            if (pendingStep) { StartStep(); return; }
            var kind = Lesson.Current.Kind;
            marker.enabled = kind == TutorialLesson.Kind.Aim;
            if (marker.enabled) TennisGame.DrawRing(marker, Lesson.Progress == 0 ? LeftRing : RightRing, 1.1f);
            if (feedAt >= 0 && Time.time >= feedAt)
            {
                feedAt = -1; resolved = false; watchdog = Time.time + 6f; feeds++;
                if (kind == TutorialLesson.Kind.Dive) { divesAtFeed = game.Dives; game.FeedWide(feeds % 2 == 0); }
                else game.Feed(kind == TutorialLesson.Kind.Backhand);
            }
            if (serveAt >= 0 && Time.time >= serveAt) { serveAt = -1; resolved = false; game.StartPlayerServe(); }
            if (watchdog >= 0 && Time.time >= watchdog)
            {
                watchdog = -1;
                if (!resolved) { resolved = true; Missed("Too late: the ball got past the racket.", "MISSED"); }
                NextBall();
            }
        }
        void Advance(bool stepEnded)
        {
            if (stepEnded)
            {
                // Landed/Score callbacks run inside physics. Let the old point finish first.
                pendingStep = true; feedAt = serveAt = watchdog = -1; return;
            }
            ShowInstruction();
        }
        void NextBall()
        {
            if (Lesson.Done || pendingStep) return;
            if (Lesson.Current.Kind == TutorialLesson.Kind.Serve) { if (serveAt < 0) serveAt = Time.time + 1.4f; }
            else if (Lesson.Current.Kind != TutorialLesson.Kind.Point && feedAt < 0) feedAt = Time.time + 1.6f;
        }

        // MARK: Judging

        string TimingRead()
        {
            int ms = Mathf.RoundToInt(TennisGame.LastLateness * 1000);
            return ms > 35 ? $"LATE {ms} ms" : ms < -35 ? $"EARLY {-ms} ms" : "ON THE BALL";
        }
        static string SideRead(Vector3 where) => where.x < -.8f ? "LEFT" : where.x > .8f ? "RIGHT" : "STRAIGHT";
        static string DepthRead(Vector3 where)
        {
            float depth = Mathf.Abs(where.z);
            return (depth >= 9.2f ? "deep " : depth <= 7.2f ? "short " : "") + depth.ToString("0.0") + " m";
        }
        List<(string, string, int)> HitRead(Vector3 where, bool good)
        {
            bool onTime = Mathf.Abs(TennisGame.LastLateness) <= .095f;
            return new List<(string, string, int)>
            {
                ("TIMING", TimingRead(), onTime ? 1 : good ? 2 : 0),
                ("PACE", Mathf.RoundToInt(game.LastHit.Speed * 3.6f) + " km/h", good ? 1 : 2),
                ("SIDE", SideRead(where), 2),
                ("LANDS", DepthRead(where), Mathf.Abs(where.z) >= 9.2f ? 1 : 2),
            };
        }
        void Passed(string text, string grade, List<(string, string, int)> read)
        {
            int index = Lesson.Index, misses = Lesson.Misses;
            bool ended = Lesson.Success();
            Report(LessonJson.Attempt(ended, grade, ended ? text : "That's one. " + text, misses, read));
            if (ended) StepResolved?.Invoke(index, misses, false);
            Advance(ended);
        }
        void Missed(string text, string grade, List<(string, string, int)> read = null)
        {
            Lesson.Miss();
            Report(LessonJson.Attempt(false, grade, text, Lesson.Misses, read));
            Advance(false);
        }

        void OnLanded(bool byPlayer, bool landedIn, Vector3 where, bool serve)
        {
            if (!active || pendingStep || !byPlayer || resolved || Lesson.Current.Kind == TutorialLesson.Kind.Point) return;
            var kind = Lesson.Current.Kind;
            if (kind == TutorialLesson.Kind.Serve && !serve) return;
            resolved = true;
            string grade = TennisRules.GradeLabel(game.LastGrade);
            switch (kind)
            {
                case TutorialLesson.Kind.Serve:
                    if (landedIn) Passed("In! A clean toss and a swing at the top.", "ACE!", new() { ("SERVE", "in", 1), ("PACE", Mathf.RoundToInt(game.LastHit.Speed * 3.6f) + " km/h", 2) });
                    else Missed("FAULT. Toss at the middle of the meter, then swing as the ball reaches the top.", "FAULT", new() { ("SERVE", "out", 0) });
                    break;
                case TutorialLesson.Kind.Pace:
                    if (game.LastGrade >= Timing.Great) Passed("Right on the ball: your fastest shot, and it lands deep. Three GREAT in a row will SUPERCHARGE the next one.", grade, HitRead(where, true));
                    else Missed(TennisGame.LastLateness < -.035f ? "EARLY. Your player held the swing back, so the ball floated short." : "A touch LATE, so the ball came off slower.", grade, HitRead(where, false));
                    break;
                case TutorialLesson.Kind.Aim:
                {
                    bool wantLeft = Lesson.Progress == 0;
                    bool hit = wantLeft ? where.x < -.8f : where.x > .8f;
                    if (hit) Passed(wantLeft ? "Left side! Now turn the face the other way for the RIGHT ring." : "Into the corner! Square goes straight; turn the face for the corners.", grade, HitRead(where, true));
                    else Missed(where.x < -.8f || where.x > .8f ? "Wrong side: the racket face was turned the other way." : "Straight down the middle. Your racket face was square to the TV.", grade, HitRead(where, false));
                    break;
                }
                case TutorialLesson.Kind.Dive:
                    if (game.Dives > divesAtFeed) Passed("Saved! Dives cost stamina and need about 2.5 s to recharge.", "SAVED!", new() { ("DIVE", "in time", 1), ("STAMINA", Mathf.RoundToInt(game.Stamina * 100) + "%", 2) });
                    else Passed("You reached it without diving. Nice running!", grade, new() { ("DIVE", "not needed", 2) });
                    break;
                case TutorialLesson.Kind.Backhand:
                    Passed("Backhand back over. The game picks forehand or backhand from where the ball is.", grade, HitRead(where, true));
                    break;
                default:
                    Passed("Two back over. Every ball you hit lands in, so your job is to make it a good one.", grade, HitRead(where, true));
                    break;
            }
            if (serve) NextBall();
        }
        void OnDrillPoint(bool toPlayer, string why)
        {
            if (!active || pendingStep) return;
            if (!resolved)
            {
                resolved = true;
                if (Lesson.Current.Kind == TutorialLesson.Kind.Dive) Missed("Too wide: the ball got past before you dived.", "MISSED", new() { ("DIVE", "late", 0) });
                else if (Lesson.Current.Kind == TutorialLesson.Kind.Serve) Missed("FAULT. Toss at the middle of the meter, then swing as the ball reaches the top.", "FAULT", new() { ("SERVE", why ?? "fault", 0) });
                else Missed("Too late: the ball got past the racket.", "LATE", new() { ("TIMING", "missed", 0) });
            }
            watchdog = -1; NextBall();
        }
        void OnScore(string line)
        {
            if (active && !pendingStep && Lesson.Current.Kind == TutorialLesson.Kind.Point)
            {
                int index = Lesson.Index, misses = Lesson.Misses;
                bool won = game.Match.PlayerPoints > 0 || line.Contains("15–0");
                Report(LessonJson.Attempt(true, won ? "POINT!" : "15–0", won ? "Point won! You're ready for the Island Circuit." : "Point to Coach Ray. That's the lesson: you're ready for the Island Circuit.",
                    misses, new List<(string, string, int)> { ("RALLY", game.RallyShots + " shots", 1) }));
                StepResolved?.Invoke(index, misses, false);
                Advance(Lesson.Success());
            }
        }
    }
}
