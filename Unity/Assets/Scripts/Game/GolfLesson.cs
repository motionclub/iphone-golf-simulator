using System;
using System.Collections.Generic;
using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.Swing;
using UnityEngine;

namespace GolfArcade.Game
{
    /// The golf lesson on the Practice Tee (PLAN_Onboarding_GolfLesson.md, Course.Lesson): three stations, about a minute
    /// and a half: swing, backswing = distance, hole a short putt. A station that passes moves on; a miss puts the ball back
    /// and says the one fix; the phone offers Skip after three misses. Reports go to the phone through
    /// NativeSportsSession.LessonReport. The phone shows the title and one line (ask, then the attempt text, then the hint
    /// after two misses); the game's HUD already shows the grade, carry and distances, so the text never repeats them.
    /// (2026-11-16, Adnan: "lessons are too long and redundant": Commit, Face, Tempo, Aim and the played hole were cut.)
    public sealed class GolfLesson : MonoBehaviour
    {
        public enum Kind { Swing, Distance, Putt }
        public readonly struct Station
        {
            public readonly Kind Kind;
            public readonly string Key, Name, Title, Ask, Hint;
            public readonly string[] Tips;
            public Station(Kind kind, string key, string name, string title, string ask, string hint, params string[] tips)
            { Kind = kind; Key = key; Name = name; Title = title; Ask = ask; Hint = hint; Tips = tips; }
        }
        public static readonly Station[] Stations =
        {
            new(Kind.Swing, "swing", "Swing", "Swing",
                "Tap SWING, then swing the phone like a club.",
                "Tap SWING first, then swing back and through."),
            new(Kind.Distance, "distance", "Distance", "Backswing sets distance",
                "Take the phone back shoulder-high to reach the flag.",
                "Stop your backswing when the meter reaches the gold mark."),
            new(Kind.Putt, "putt", "Putt", "Sink the putt",
                "Rock the phone gently to roll it in.",
                "Rock back only to the first mark on the map."),
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
                Kind.Distance => Toward(hole.Pin, hole.Tee, 60),
                Kind.Putt => Toward(hole.Pin, hole.Tee, 8.0 / 3),
                _ => hole.Tee,
            };
            game.DropBall(start);
            var s = Current;
            Report(LessonJson.Station("golf", index, Stations.Length, s.Key, s.Name, s.Title, s.Ask, s.Hint, s.Tips));
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
            switch (Current.Kind)
            {
                case Kind.Distance:
                {
                    double target = start.DistanceTo(pin);
                    double carry = shot != null ? Math.Round(shot.Carry) : 0;
                    double toPin = shot != null ? shot.Rest.DistanceTo(pin) : 0;
                    pass = holed || Math.Abs(carry - target) <= 10 || toPin <= 8;
                    text = pass ? "Right on it." : carry > target ? "Take the phone back less." : "Take the phone back further.";
                    break;
                }
                case Kind.Putt:
                {
                    pass = holed;
                    bool past = shot != null && shot.Rest.DistanceTo(start) > start.DistanceTo(pin);
                    text = pass ? "In!" : past ? "Softer stroke." : "Firmer stroke.";
                    break;
                }
                default:   // Kind.Swing: any swing
                    pass = true;
                    text = "Nice.";
                    break;
            }
            if (!pass) misses++;
            Attempted?.Invoke(index, pass);
            Report(LessonJson.Attempt(pass, grade, text, misses, null));
            // (a pass may have holed out: the game is on to the next hole, and the next station starts there; a miss is never holed)
            if (pass) Next();
            else reset = true;
        }

        static void Report(string json) => NativeSportsSession.LessonReport?.Invoke(json);
    }
}
