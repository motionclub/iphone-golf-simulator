using System;
using System.Collections.Generic;
using GolfArcade.Game;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The bowling lesson (PLAN_Onboarding_v3_IntroTutorial.md, the Tutorial's third lesson): five stations on a normal game, each
    /// judged on the ball just bowled (BowlingGame.BallFinished). A pass moves on; a miss says why; the phone offers Skip after three
    /// misses. Reports go to the phone like the golf and tennis lessons (NativeSportsSession.LessonReport → LessonCenter).
    public static class BowlingLessonPlan
    {
        public enum Kind { Roll, Release, Line, Spin, Pins }
        public readonly struct Station
        {
            public readonly Kind Kind; public readonly string Key, Name, Title, Ask, Hint; public readonly string[] Tips;
            public Station(Kind kind, string key, string name, string title, string ask, string hint, params string[] tips)
            { Kind = kind; Key = key; Name = name; Title = title; Ask = ask; Hint = hint; Tips = tips; }
        }
        public static readonly Station[] Stations =
        {
            new(Kind.Roll, "roll", "Roll it", "Roll your first ball",
                "Hold the ball button, swing the phone back, then forward, and let go of the button.",
                "Keep holding the button all the way back; let go only as the phone swings forward past your leg.",
                "Hold the phone like the ball, screen up.", "Hold the button to grip the ball.", "Swing back, swing through, let go."),
            new(Kind.Release, "release", "Release", "Let go at the bottom",
                "Get a GOOD or PERFECT release: let go as the phone passes the bottom of the swing.",
                "Too early lofts it short, too late bounces it. Let go right as your arm points at the floor.",
                "The release is timed to your own swing.", "PERFECT gives the full speed and line.", "Smooth beats hard."),
            new(Kind.Line, "line", "Line up", "Pick your spot",
                "Slide to a new spot on the lane with the arrows, then roll from there.",
                "Tap the arrows (or drag the lane slider) before you hold the ball, then roll.",
                "Where you stand is where the ball starts.", "The middle board is 20.", "Move left or right to aim at the pins you need."),
            new(Kind.Spin, "spin", "Spin", "Put spin on it",
                "Turn your wrist as you let go, like turning a door handle, and watch the ball hook.",
                "Turn the phone a quarter turn at the release; a flat wrist rolls it straight.",
                "Turning your wrist at the release spins the ball.", "Spin makes it hook into the pins.", "More turn, more hook."),
            new(Kind.Pins, "pins", "Knock them down", "Knock 7 or more down",
                "Put it together: line up, roll smoothly and knock down 7 or more pins with one ball.",
                "Aim between the front pin and the one beside it (the pocket) and let go at the bottom.",
                "The pocket is just beside the head pin.", "A strike is all 10 with the first ball.", "Ten frames make a game."),
        };

        /// One ball's verdict at a station: pass, what to say, and the read-out rows (key, value, 1 good / 0 fault / 2 note).
        public static (bool pass, bool counts, string text, List<(string, string, int)> read) Judge(Kind kind, ReleaseGrade grade, float board, float axisDeg, int knocked, bool fullRack)
        {
            var read = new List<(string, string, int)>
            {
                ("Release", grade.ToString().ToUpperInvariant(), grade == ReleaseGrade.Perfect || grade == ReleaseGrade.Good ? 1 : 0),
                ("Pins", knocked.ToString(), knocked >= 7 ? 1 : 2),
            };
            if (grade == ReleaseGrade.Drop) return (false, true, "It slipped: keep holding the button until the forward swing.", read);
            if (grade == ReleaseGrade.Foul) return (false, true, "Over the line: you held it too long.", read);
            switch (kind)
            {
                case Kind.Roll:
                    return (true, true, "That's bowling! Now let's time the release.", read);
                case Kind.Release:
                    if (grade == ReleaseGrade.Perfect || grade == ReleaseGrade.Good) return (true, true, grade == ReleaseGrade.Perfect ? "PERFECT release!" : "Good release!", read);
                    return (false, true, grade == ReleaseGrade.Early ? "A touch early: wait until the phone passes your leg." : "A touch late: let go as your arm points at the floor.", read);
                case Kind.Line:
                    read.Add(("Board", Mathf.RoundToInt(board).ToString(), Mathf.Abs(board - 20) >= 3 ? 1 : 0));
                    if (Mathf.Abs(board - 20) >= 3) return (true, true, "Nice: you rolled from a new spot.", read);
                    return (false, true, "Move at least 3 boards left or right before you hold the ball.", read);
                case Kind.Spin:
                    read.Add(("Spin", Mathf.RoundToInt(Mathf.Abs(axisDeg)) + "°", Mathf.Abs(axisDeg) >= 12 ? 1 : 0));
                    if (Mathf.Abs(axisDeg) >= 12) return (true, true, "Look at it hook!", read);
                    return (false, true, "Turn your wrist more as you let go, a quarter turn.", read);
                default:
                    if (!fullRack) return (false, false, "Pick up the spare, then go for 7 with a full rack.", read);
                    if (knocked >= 7) return (true, true, knocked == 10 ? "STRIKE! Lesson complete." : knocked + " pins! Lesson complete.", read);
                    return (false, true, knocked + " pins. Aim for the pocket, beside the front pin.", read);
            }
        }
    }

    public sealed class BowlingLesson : MonoBehaviour
    {
        /// A lesson is running (the session keeps a finished game from ending the lesson: it racks up a new one).
        public static bool Running { get; private set; }
        /// For tests: each judged ball (station index, passed).
        public static event Action<int, bool> Attempted;

        BowlingGame game;
        int index, misses;
        bool finished, pendingStation = true;
        float stationAt;
        public int Index => index;
        public bool Finished => finished;
        BowlingLessonPlan.Station Current => BowlingLessonPlan.Stations[Mathf.Clamp(index, 0, BowlingLessonPlan.Stations.Length - 1)];

        public void Begin(BowlingGame target, int station)
        {
            game = target; index = Mathf.Clamp(station, 0, BowlingLessonPlan.Stations.Length - 1);
            game.BallFinished -= Ball; game.BallFinished += Ball;
            game.GameFinished -= Over; game.GameFinished += Over;
            Running = true; pendingStation = true; stationAt = Time.unscaledTime + 0.6f;
        }
        void OnDestroy()
        {
            if (game) { game.BallFinished -= Ball; game.GameFinished -= Over; }
            Running = false;
        }

        void Update()
        {
            if (finished || !pendingStation || Time.unscaledTime < stationAt) return;
            pendingStation = false; misses = 0;
            var s = Current;
            Report(LessonJson.Station("bowling", index, BowlingLessonPlan.Stations.Length, s.Key, s.Name, s.Title, s.Ask, s.Hint, s.Tips));
        }

        void Ball(BowlingThrow th, PinAction act)
        {
            if (finished || pendingStation) return;
            bool fullRack = act != null && act.StandingBefore == BowlingLeave.All;
            var (pass, counts, text, read) = BowlingLessonPlan.Judge(Current.Kind, th.Grade, th.Board, th.AxisDeg, act?.Knocked ?? 0, fullRack);
            if (!pass && counts) misses++;
            Attempted?.Invoke(index, pass);
            Report(LessonJson.Attempt(pass, pass ? "PASS" : "", text, misses, read));
            if (pass) Next();
        }

        void Next()
        {
            index++;
            if (index >= BowlingLessonPlan.Stations.Length) { Finish(); return; }
            pendingStation = true; stationAt = Time.unscaledTime + 2.2f;   // the pins and the banner first
        }
        /// The phone's Skip this step.
        public void SkipStation() { if (!finished) Next(); }
        void Finish()
        {
            finished = true; Running = false;
            Report(LessonJson.Done("bowling"));
        }
        /// Ten frames went by before the lesson did: a fresh game on the same lane.
        void Over(string _) { if (!finished && game) game.NewGame(game.Players); }

        static void Report(string json) => NativeSportsSession.LessonReport?.Invoke(json);
    }
}
