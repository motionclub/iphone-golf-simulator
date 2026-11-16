using System;
using System.Collections.Generic;
using GolfArcade.Game;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The bowling lesson (PLAN_Onboarding_v3_IntroTutorial.md, the Tutorial's third lesson): three stations on a normal game
    /// (roll, release, knock 7 down), each judged on the ball just bowled (BowlingGame.BallFinished). A pass moves on; a miss
    /// says the one fix; the phone offers Skip after three misses. Reports go to the phone like the golf and tennis lessons
    /// (NativeSportsSession.LessonReport → LessonCenter), which shows the title and one line; the game's HUD shows the release
    /// grade and the pins, so the text never repeats them. (2026-11-16, Adnan: "shorten them": Line and Spin were cut.)
    public static class BowlingLessonPlan
    {
        public enum Kind { Roll, Release, Pins }
        public readonly struct Station
        {
            public readonly Kind Kind; public readonly string Key, Name, Title, Ask, Hint; public readonly string[] Tips;
            public Station(Kind kind, string key, string name, string title, string ask, string hint, params string[] tips)
            { Kind = kind; Key = key; Name = name; Title = title; Ask = ask; Hint = hint; Tips = tips; }
        }
        public static readonly Station[] Stations =
        {
            new(Kind.Roll, "roll", "Roll", "Roll it",
                "Hold the button, swing through and let go.",
                "Hold the button all the way back, then let go."),
            new(Kind.Release, "release", "Release", "Time the release",
                "Let go at the bottom of your swing.",
                "Let go as your arm points at the floor."),
            new(Kind.Pins, "pins", "Pins", "Knock them down",
                "Knock down 7 or more pins.",
                "Line up with the arrows, then aim beside the front pin."),
        };

        /// One ball's verdict at a station: pass, whether a miss counts toward the hint and Skip, and the one line to say.
        public static (bool pass, bool counts, string text) Judge(Kind kind, ReleaseGrade grade, int knocked, bool fullRack)
        {
            if (grade == ReleaseGrade.Drop) return (false, true, "Keep holding the button until you swing forward.");
            if (grade == ReleaseGrade.Foul) return (false, true, "Let go a little sooner.");
            switch (kind)
            {
                case Kind.Roll:
                    return (true, true, "Nice.");
                case Kind.Release:
                    if (grade == ReleaseGrade.Perfect || grade == ReleaseGrade.Good) return (true, true, "Right on time.");
                    return (false, true, grade == ReleaseGrade.Early ? "Hold on a little longer." : "Let go a little sooner.");
                default:
                    if (!fullRack) return (false, false, "Finish the frame, then try again with all ten.");
                    if (knocked >= 7) return (true, true, "Nice bowling.");
                    return (false, true, "Aim just beside the front pin.");
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
            var (pass, counts, text) = BowlingLessonPlan.Judge(Current.Kind, th.Grade, act?.Knocked ?? 0, fullRack);
            if (!pass && counts) misses++;
            Attempted?.Invoke(index, pass);
            Report(LessonJson.Attempt(pass, pass ? "PASS" : "", text, misses, null));
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
