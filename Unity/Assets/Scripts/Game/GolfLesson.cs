using System;
using System.Collections.Generic;
using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.Swing;
using UnityEngine;

namespace GolfArcade.Game
{
    /// The golf lesson (PLAN_Onboarding_Tutorial_TennisQuickStart_1121.md, 11-21: "driving, mid game, putting, emphasis on explaining
    /// putting and how sensitive it is"): four stations on a par 4: drive from the tee, a 100-yd approach, a short putt that opens on a
    /// card saying how little the putter moves, then a long putt that only has to finish close. A station that passes moves on; a miss
    /// puts the ball back and says the one fix; the phone offers Skip after three misses. Reports go to the phone through
    /// NativeSportsSession.LessonReport. The phone shows the title and one line (ask, then the attempt text, then the hint after two
    /// misses); the game's HUD already shows the grade, carry and distances, so the text never repeats them.
    public sealed class GolfLesson : MonoBehaviour
    {
        public enum Kind { Drive, Approach, Putt, LongPutt }
        public readonly struct Station
        {
            public readonly Kind Kind;
            public readonly string Key, Name, Title, Ask, Hint;
            public readonly string[] Tips;
            /// A card shown first (the phone's explain card), or null.
            public readonly string ExplainTitle, ExplainBody;
            public Station(Kind kind, string key, string name, string title, string ask, string hint, string explainTitle = null, string explainBody = null)
            { Kind = kind; Key = key; Name = name; Title = title; Ask = ask; Hint = hint; Tips = new string[0]; ExplainTitle = explainTitle; ExplainBody = explainBody; }
        }
        /// The drive must carry this far (a full backswing does it easily; a half swing does not).
        public const double DriveCarry = 100;
        /// The approach starts this far from the pin, and passes within ApproachSlack yards of carry (or ApproachRest of the pin).
        public const double ApproachYards = 100, ApproachSlack = 12, ApproachRest = 10;
        /// The short putt (6 ft) must drop; the long one (20 ft) has to stop within LongPuttRest (3 ft).
        public const double PuttYards = 2, LongPuttYards = 20.0 / 3, LongPuttRest = 1;
        public static readonly Station[] Stations =
        {
            new(Kind.Drive, "drive", "Drive", "Tee off",
                "Tap SWING, take the phone back high and swing through hard.",
                "A full backswing gives a full drive. Swing back further, then through faster."),
            new(Kind.Approach, "approach", "Approach", "Backswing sets distance",
                "Take the phone back about shoulder-high to reach the flag.",
                "Stop your backswing when the meter reaches the gold mark."),
            new(Kind.Putt, "putt", "Putt", "Putting is sensitive",
                "Rock the phone back only a few inches to roll it in.",
                "Smaller still. Rock back only to the first mark on the map.",
                "Putting is sensitive",
                "The putter moves only a few inches. Rock the phone back just a little. A full swing would roll the ball off the green."),
            new(Kind.LongPutt, "longputt", "Long putt", "Long putt",
                "Three times as far needs only a slightly bigger rock. Stop it close.",
                "Rock back a little more than the short putt, not a lot more."),
        };

        /// For tests: each judged attempt (station index, passed).
        public static event Action<int, bool> Attempted;

        GolfGame game;
        int index, misses;
        bool pending = true, waiting, reset, finished, judgedThisShot;
        float nextAt;
        CoursePoint start;
        public int Index => index;
        public bool Finished => finished;
        public Station Current => Stations[Mathf.Clamp(index, 0, Stations.Length - 1)];

        public void Begin(GolfGame target, int station)
        {
            game = target; index = Mathf.Clamp(station, 0, Stations.Length - 1);
            GolfGame.ShotStruck -= Struck; GolfGame.ShotStruck += Struck;
            pending = true; nextAt = Time.unscaledTime + 0.4f;
        }
        void OnDestroy() => GolfGame.ShotStruck -= Struck;
        void Struck()
        {
            if (finished || pending) return;
            waiting = true; judgedThisShot = false;
        }

        void Update()
        {
            if (finished || !game) return;
            // a lesson plays no hole intros or flyovers
            if (game.Current == GolfGame.State.Intro) { game.SkipPresentation(); return; }
            if (pending)
            {
                if (game.Current == GolfGame.State.Aim && Time.unscaledTime >= nextAt) StartStation();
                return;
            }
            if (waiting && !judgedThisShot && game.Current is GolfGame.State.Result or GolfGame.State.HoleDone or GolfGame.State.RoundDone or GolfGame.State.Aim)
            {
                judgedThisShot = true;
                Judge(game.LastShot != null && game.LastShot.IsHoled);
            }
            if (waiting && judgedThisShot && game.Current == GolfGame.State.Aim)
            {
                waiting = false;
                if (reset) { reset = false; game.DropBall(start); }
            }
            // the round ended under the lesson (a hole-out on the last practice hole): the lesson is over too
            if (game.Current == GolfGame.State.RoundDone && !finished && !pending) Finish();
        }

        void StartStation()
        {
            pending = false; waiting = false; reset = false; misses = 0;
            var hole = game.CurrentHole;
            start = Current.Kind switch
            {
                Kind.Approach => Toward(hole.Pin, hole.Tee, ApproachYards),
                Kind.Putt => Toward(hole.Pin, hole.Tee, PuttYards),
                Kind.LongPutt => Toward(hole.Pin, hole.Tee, LongPuttYards),
                _ => hole.Tee,
            };
            game.DropBall(start);
            var s = Current;
            Report(LessonJson.Station("golf", index, Stations.Length, s.Key, s.Name, s.Title, s.Ask, s.Hint, s.Tips, s.ExplainTitle, s.ExplainBody));
        }
        static CoursePoint Toward(CoursePoint from, CoursePoint to, double yards)
        {
            double d = from.DistanceTo(to);
            if (d < 1e-6) return from;
            return new CoursePoint(from.X + (to.X - from.X) * yards / d, from.D + (to.D - from.D) * yards / d);
        }

        /// The phone's Skip this step.
        public void SkipStation()
        {
            if (finished || pending) return;
            Next();
        }

        void Next()
        {
            index++;
            if (index >= Stations.Length) { Finish(); return; }
            pending = true; nextAt = Time.unscaledTime + 2.6f; waiting = false;
            // a passed practice shot is still in the air or rolling: the next station puts the ball where it wants it
        }
        void Finish()
        {
            if (finished) return;
            finished = true;
            Report(LessonJson.Done("golf"));
        }

        void Judge(bool holed)
        {
            var shot = game.LastShot; var rep = game.LastStrike;
            var pin = game.CurrentHole.Pin;
            bool putt = shot != null && shot.Club == GolfClub.Putter;
            string grade = putt ? (holed ? "IN!" : "PUTT") : rep.GradeWord;
            bool pass;
            string text;
            double carry = shot != null ? Math.Round(shot.Carry) : 0;
            double toPin = shot != null ? shot.Rest.DistanceTo(pin) : 0;
            bool past = shot != null && shot.Rest.DistanceTo(start) > start.DistanceTo(pin);
            pass = Passes(Current.Kind, holed, carry, start.DistanceTo(pin), toPin);
            text = Current.Kind switch
            {
                Kind.Drive => pass ? "Great drive." : "Swing back further, then through faster.",
                Kind.Approach => pass ? "Right on it." : carry > start.DistanceTo(pin) ? "Take the phone back less." : "Take the phone back further.",
                Kind.Putt => pass ? "In." : past ? "Softer. Only a few inches back." : "A touch firmer.",
                _ => pass ? (holed ? "In." : "Close enough. That's a good long putt.") : past ? "Too firm. Only a little more than the short putt." : "A little firmer.",
            };
            if (!pass) misses++;
            Attempted?.Invoke(index, pass);
            Report(LessonJson.Attempt(pass, grade, text, misses, null));
            // (a pass may have holed out: the game is on to the next hole, and the next station starts there; a miss is never holed)
            if (pass) Next();
            else reset = true;
        }

        /// The pass rule for each station (EditMode tests use it directly).
        public static bool Passes(Kind kind, bool holed, double carry, double target, double toPin) => kind switch
        {
            Kind.Drive => carry >= DriveCarry,
            Kind.Approach => holed || Math.Abs(carry - target) <= ApproachSlack || toPin <= ApproachRest,
            Kind.Putt => holed,
            _ => holed || toPin <= LongPuttRest,
        };

        static void Report(string json) => NativeSportsSession.LessonReport?.Invoke(json);
    }
}
