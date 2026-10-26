using System;
using System.Collections.Generic;
using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.Swing;
using UnityEngine;

namespace GolfArcade.Game
{
    /// The golf lesson on the Practice Tee (PLAN_Onboarding_GolfLesson.md, Course.Lesson): eight stations, each teaching one
    /// thing the game really measures, judged on the swing the player just made. A station that passes moves on; a miss puts
    /// the ball back and says why (the Shot Read); the phone offers Skip after three misses. Reports go to the phone through
    /// NativeSportsSession.LessonReport, which draws them over the TV.
    public sealed class GolfLesson : MonoBehaviour
    {
        public enum Kind { Swing, Distance, Commit, Face, Tempo, Aim, Putt, Hole }
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
            new(Kind.Swing, "grip", "Grip", "Take your grip and swing",
                "Hold the phone like a club handle, tap SWING, settle for a moment, then swing back and through.",
                "Tap SWING with the phone already in your stance and keep still for a beat: the game reads your grip from that pause.",
                "Hold the phone like the end of a club, screen facing your target.", "Tap SWING on your phone, then stay still for a beat.", "Swing back and through. That's it."),
            new(Kind.Distance, "distance", "Distance", "Backswing = distance",
                "The flag is 60 yards away. Land the ball near it: a shoulder-high backswing is about right.",
                "Stop when your hands reach your shoulder. On the TV, stop the power meter at the gold mark.",
                "How far back you take the phone is how far the ball flies.", "Hip high is about half; up behind you is full power.", "The map's dots match the meter's marks."),
            new(Kind.Commit, "commit", "Commit", "Swing through the ball",
                "Hit two in a row that fly their full distance: don't slow down at the ball.",
                "Don't swing harder, just don't stop. Finish with the phone up over your front shoulder.",
                "Easing off at the ball is graded THIN: it flies low and short.", "Past committed, more effort adds almost nothing.", "Smooth and through beats hard."),
            new(Kind.Face, "face", "Square face", "Square face, straight ball",
                "Hit one straight. Keep the phone's screen facing the same way through impact.",
                "If it curves right, your wrist rolled open: turn the screen slightly toward the target as you come through.",
                "Twist the phone open through impact and the ball slices right.", "Twist it closed and it hooks left.", "Inside about 10° it flies straight."),
            new(Kind.Tempo, "tempo", "Tempo", "Slow back, quick through",
                "Earn one PERFECT: committed, square, and a smooth rhythm.",
                "Count \"one… two…\" on the way back, then go. The backswing takes about three times as long as the downswing.",
                "PERFECT is all three at once: commit, a square face and a smooth tempo.", "Miss one and it's GREAT!, two and it's GOOD.", "A PERFECT strike flies a little further."),
            new(Kind.Aim, "aim", "Aim & map", "Aim, clubs and the map",
                "Hit the green. Line up with the aim stick on your phone first; the club is already chosen for you.",
                "Move the aim with the stick before you tap SWING, and match the map's dot on the green to your backswing.",
                "The phone's stick moves your aim line.", "The arrows change club; the game starts you on one that reaches.", "Check the wind arrow: a strong wind moves the ball."),
            new(Kind.Putt, "putt", "Putting", "Tiny strokes on the green",
                "Hole the 8-foot putt. Putting strokes are tiny: a short rock of the phone.",
                "Rock the phone back only to the first mark on the map, keep the face quiet, and stroke through.",
                "On the green the map zooms in and reads in feet.", "An 8-foot putt is about a quarter of a full putting stroke.", "The chevrons drift the way the ball will break."),
            new(Kind.Hole, "hole", "Play a hole", "Play a real hole",
                "Everything together now: tee to green, as few strokes as you can. The coach stays quiet.",
                "Pick the club the game offers, aim at the flag and swing smooth.",
                "Par is 3 here.", "After 6 strokes we pick the ball up.", "No score is kept."),
        };
        public const int HoleCap = 6;

        /// For tests: each judged attempt (station index, passed).
        public static event Action<int, bool> Attempted;

        GolfGame game;
        int index, misses, streak, holeStrokes;
        bool pending = true, waiting, reset, finished, judgedThisShot;
        bool bunkerTold;
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
            if (Current.Kind == Kind.Hole) holeStrokes++;
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
            pending = false; waiting = false; reset = false; misses = 0; streak = 0; holeStrokes = 0; bunkerTold = false;
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
            var shot = game.LastShot; var imp = game.LastImpact; var rep = game.LastStrike;
            var pin = game.CurrentHole.Pin;
            bool putt = shot != null && shot.Club == GolfClub.Putter;
            int back = (int)Math.Round(Math.Clamp(imp.Backswing, 0, 1) * 100);
            int commit = (int)Math.Round(Math.Max(0, imp.Commit) * 100);
            double face = imp.FaceDegrees;
            string faceText = Math.Abs(face) < 1 ? "square" : $"{Math.Abs(face):0}° {(face > 0 ? "open" : "closed")}";
            int carry = shot != null ? (int)Math.Round(shot.Carry) : 0;
            double toPin = shot != null ? shot.Rest.DistanceTo(pin) : 0;
            string grade = putt ? (holed ? "IN!" : "PUTT") : rep.GradeWord;
            var read = new List<(string, string, int)>();
            bool pass = false, counts = true;
            string text;
            switch (Current.Kind)
            {
                case Kind.Swing:
                    pass = true;
                    text = $"That's a swing! A {back}% backswing carried it {carry} yards.";
                    read.Add(("BACK", back + "%", 1)); read.Add(("CARRY", carry + " yd", 1)); read.Add(("GRADE", rep.GradeWord, 1));
                    break;
                case Kind.Distance:
                {
                    double target = start.DistanceTo(pin);
                    double err = carry - target;
                    int need = (int)Math.Round(Math.Clamp(target / Math.Max(1, (shot?.Club ?? GolfClub.Wedge).ReferenceDistanceYards()), 0, 1) * 100);
                    pass = holed || Math.Abs(err) <= 10 || toPin <= 8;
                    text = pass ? "Right on the number. How far back you go is how far it flies."
                        : err > 0 ? $"Long! A {back}% backswing carried {carry} yards. About {need}% is right from here."
                        : $"Short. A {back}% backswing carried {carry} yards. About {need}% is right from here.";
                    read.Add(("BACK", back + "%", pass ? 1 : 0)); read.Add(("CARRY", carry + " yd", pass ? 1 : 0)); read.Add(("TARGET", Math.Round(target) + " yd", 2));
                    break;
                }
                case Kind.Commit:
                {
                    bool ok = imp.Commit >= 1 && rep.Grade != StrikeGrade.Thin;
                    streak = ok ? streak + 1 : 0;
                    pass = streak >= 2;
                    counts = !ok;
                    text = pass ? "Two committed swings. Full speed through the ball, full distance."
                        : ok ? "That's one, committed all the way through. Now one more just like it."
                        : rep.Grade == StrikeGrade.Thin ? "THIN. You slowed down at the ball, so it flew low and short."
                        : "You eased off a little at the ball, so it lost distance.";
                    read.Add(("COMMIT", commit + "%", ok ? 1 : 0)); read.Add(("BACK", back + "%", 2)); read.Add(("CARRY", carry + " yd", ok ? 1 : 0));
                    break;
                }
                case Kind.Face:
                {
                    var shape = rep.Shape;
                    pass = shape == ShotShape.Straight;
                    string way = shape is ShotShape.Fade or ShotShape.Slice ? "right" : "left";
                    text = pass ? "Straight! A square face sends it where you aim."
                        : $"It curved {way} ({rep.ShapeWord.ToLowerInvariant()}). The face was {faceText} at impact.";
                    read.Add(("FACE", faceText, pass ? 1 : 0)); read.Add(("SHAPE", rep.ShapeWord.ToLowerInvariant(), pass ? 1 : 0)); read.Add(("COMMIT", commit + "%", imp.Commit >= 1 ? 1 : 2));
                    break;
                }
                case Kind.Tempo:
                {
                    pass = rep.Grade == StrikeGrade.Perfect;
                    bool smooth = rep.TempoRatio >= Strikes.SmoothTempoLow && rep.TempoRatio <= Strikes.SmoothTempoHigh;
                    text = pass ? "PERFECT! Committed, square and smooth: the purest strike there is."
                        : !smooth ? (rep.TempoRatio < Strikes.SmoothTempoLow ? $"{rep.GradeWord} But you rushed the backswing." : $"{rep.GradeWord} But the backswing dragged.")
                        : imp.Commit < 1 ? $"{rep.GradeWord} But you eased off at the ball."
                        : $"{rep.GradeWord} But the face was {faceText}, so it curved.";
                    read.Add(("COMMIT", commit + "%", imp.Commit >= 1 ? 1 : 0)); read.Add(("FACE", faceText, rep.Shape == ShotShape.Straight ? 1 : 0));
                    read.Add(("TEMPO", rep.TempoRatio.ToString("0.0") + " : 1", smooth ? 1 : 0)); read.Add(("GRADE", rep.GradeWord, pass ? 1 : 2));
                    break;
                }
                case Kind.Aim:
                {
                    bool onGreen = holed || (shot != null && game.CurrentHole.LieAt(shot.Rest) == CourseLie.Green);
                    pass = onGreen;
                    var rest = shot?.Rest ?? start;
                    string side = rest.X < pin.X - 4 ? "left" : rest.X > pin.X + 4 ? "right" : rest.D < pin.D ? "short" : "long";
                    text = pass ? "On the green! Aim first, then swing." : $"Missed the green {side}, {toPin:0} yards from the flag.";
                    read.Add(("TO PIN", $"{toPin:0} yd", pass ? 1 : 0)); read.Add(("CARRY", carry + " yd", 2)); read.Add(("BACK", back + "%", 2));
                    break;
                }
                case Kind.Putt:
                {
                    pass = holed;
                    double feet = toPin * 3;
                    bool past = shot != null && shot.Rest.DistanceTo(start) > start.DistanceTo(pin);
                    text = pass ? "In the hole! On the green the map reads in feet."
                        : $"{(past ? "Past" : "Short")} by {feet:0} feet. Putting strokes are tiny.";
                    read.Add(("STROKE", back + "%", pass ? 1 : 2)); read.Add(("LEFT", $"{feet:0} ft", pass ? 1 : 0));
                    break;
                }
                default:   // Kind.Hole: quiet until it's over, but the first bunker gets a word
                {
                    if (holed || holeStrokes >= HoleCap)
                    {
                        int par = game.CurrentHole.Par, diff = holeStrokes - par;
                        string word = !holed ? "PICKED UP" : diff <= -2 ? "EAGLE!" : diff == -1 ? "BIRDIE!" : diff == 0 ? "PAR!" : diff == 1 ? "BOGEY" : $"+{diff}";
                        Attempted?.Invoke(index, true);
                        Report(LessonJson.Attempt(true, word, holed ? $"Holed in {holeStrokes}! That's the game." : "Six strokes: we pick it up there. That's the game.", misses,
                            new List<(string, string, int)> { ("STROKES", holeStrokes.ToString(), 1), ("PAR", par.ToString(), 2) }));
                        Next();
                    }
                    else if (!bunkerTold && shot != null && game.CurrentHole.LieAt(shot.Rest) == CourseLie.Bunker)
                    {
                        bunkerTold = true;
                        Report(LessonJson.Attempt(false, "", "In the sand. A bunker keeps about three quarters of the distance: swing a little further back.", 0, null));
                    }
                    return;
                }
            }
            if (!pass && counts) misses++;
            Attempted?.Invoke(index, pass);
            Report(LessonJson.Attempt(pass, grade, text, misses, read));
            if (pass)
            {
                // holed out on a practice station: the game is on to the next hole; the next station starts there
                Next();
            }
            else if (!holed) reset = true;
            else { pending = true; nextAt = Time.unscaledTime + 1.5f; }
        }

        static void Report(string json) => NativeSportsSession.LessonReport?.Invoke(json);
    }
}
