using System;
using System.Collections.Generic;
using GolfArcade.Course;

namespace GolfArcade.Game
{
    /// DAILY HOLE IN ONE (Adnan 2026-11-15; PLAY → Daily Challenges): three shots a day on three of the modelled holes, each one
    /// longer than the last (Adnan 11-22: "it should not be a chip in every time"): a chip from just off the green, a pitch of about
    /// 100 yards, then a 150–175 yard iron (Bands). The cup is cut somewhere else on the green each day and drawn wider than a
    /// round's: 2.5× on every shot (CupBoost: "make the hole bigger or easier to make"). Like Wordle, the day is the only input: the
    /// UTC date (yyyymmdd) seeds a SplitMix64 stream (RoundEvents' Dice, never UnityEngine.Random or System.Random), so every phone in
    /// the world builds the same three holes, the same cups and the same spawns, and the round's wind and weather come from the same
    /// seed. A holed shot scores 1000; any other at most 800, less the farther it stops (Score); the day's total is out of 3000.
    ///
    /// The holes and cups come from the date alone, before anything is built (the cup is cut into the green as the hole is built).
    /// The spawn comes once the hole is built, because only then are its ground, trees and props known: it must be on dry fairway
    /// (or, failing that, rough), with nothing standing in the line to the pin and no hill or cliff in the way, so the shot can be made.
    /// The built hole is the same on every phone, so the spawn is too.
    public static class DailyHoleInOne
    {
        public const int Shots = 3, Holed = 1000, BestMiss = 800;
        public const int MaxTotal = Shots * Holed;
        /// Each shot's distance from the cup, yards (the course's units), shortest first. The first is the chip: not a fixed band
        /// but ChipPast–ChipPast+ChipReach yards beyond the edge of the green (fringe included) on its line, never past ChipMax.
        public static readonly (double Min, double Max)[] Bands = { (0, 0), (90, 110), (150, 175) };
        public const double ChipPast = 2, ChipReach = 10, ChipMax = 50;
        /// The cup's width over a round's (Hole.CupBoost), the same on all three shots (Adnan 11-22: 2.5× for every shot, not
        /// growing with the distance; a Bucket Cup twist is 2×).
        public const double CupBoost = 2.5;
        /// The shot's words for the menus and plates: "CHIP SHOT", "90–110 YD", "150–175 YD".
        public static string BandWords(int index) => index <= 0 ? "CHIP SHOT" : $"{Bands[Math.Min(index, Bands.Length - 1)].Min:F0}–{Bands[Math.Min(index, Bands.Length - 1)].Max:F0} YD";
        /// Beyond this many feet a shot that is not holed scores nothing.
        public const double ZeroFeet = 150;
        public const string CourseKey = "holeinone";

        /// A shot's points: holed 1000; otherwise 800 at the lip and less for every foot farther, nothing from 150 ft or in a hazard
        /// (`feet` < 0). Every foot counts (Adnan 11-15: "5 ft away should be worth more than 7 ft"): with k = 1 − ft/150 the points
        /// are 800·(0.6k² + 0.4k), about 8 a foot near the cup and never under 2 a foot out to 150 ft, so no two whole-foot distances
        /// tie (a pure k² flattened out there: 147, 148 and 149 ft all scored 0). The phone has the same curve (DailyHoleInOne.swift).
        public static int Score(double feet, bool holed)
        {
            if (holed) return Holed;
            if (feet < 0 || double.IsNaN(feet) || double.IsInfinity(feet)) return 0;
            double k = Math.Max(0, 1 - feet / ZeroFeet);
            return (int)Math.Round(BestMiss * (.6 * k * k + .4 * k), MidpointRounding.AwayFromZero);
        }

        /// A shot's words for the card: "HOLE IN ONE!", "9.4 FT", "IN THE WATER".
        public static string Words(double feet, bool holed) => holed ? "HOLE IN ONE!" : feet < 0 ? "IN THE HAZARD" : $"{feet:F1} FT";

        /// The UTC date as yyyymmdd (what the app sends; the editor and tests use it too).
        public static int Today(DateTime? utc = null)
        {
            var d = (utc ?? DateTime.UtcNow).ToUniversalTime();
            return d.Year * 10000 + d.Month * 100 + d.Day;
        }

        /// The day's stream for one purpose (`salt`): 0 the holes, 1 + index a hole's cup, 10 + index its spawn.
        static Dice DiceFor(int day, int salt) => new Dice(unchecked(day * 7919 + salt * 104729 + 17));

        /// The day's three holes, out of every modelled one, each with its cup moved about its green. Each shot takes the first hole
        /// in the day's shuffle that suits its distance: ground to play from on its ring and, for the longer two, a hole long enough
        /// that the spot can be back down its own fairway (else any hole with ground on the ring).
        public static Course.Course CourseFor(int day)
        {
            var pool = new List<Hole>();
            // (a green so big that the chip would be a long pitch is left out, and a green ringed by water or lava — Crater's, over
            // its lava inlet — has nowhere to play from at all)
            foreach (var c in Course.Course.All()) foreach (var h in c.Holes) if (h.GreenRadius <= 30) pool.Add(h);
            pool.Sort((a, b) => a.Number.CompareTo(b.Number));   // one order on every phone, whatever All() deals
            var dice = DiceFor(day, 0);
            for (int i = pool.Count - 1; i > 0; i--) { int j = dice.Next(i + 1); (pool[i], pool[j]) = (pool[j], pool[i]); }
            var holes = new List<Hole>();
            var used = new bool[pool.Count];
            for (int i = 0; i < Shots; i++)
            {
                int pick = -1;
                for (int pass = 0; pass < 2 && pick < 0; pass++)
                    for (int j = 0; j < pool.Count && pick < 0; j++)
                        if (!used[j] && (pass == 1 || i == 0 || pool[j].Length >= Bands[i].Min) && HasGround(pool[j], pool[j].GreenCenter, i)) pick = j;
                if (pick < 0) continue;
                used[pick] = true;
                var h = pool[pick];
                h.Ordinal = holes.Count + 1;
                h.CupBoost = CupBoost;
                h.CupOffset = CupFor(day, i, h);
                holes.Add(h);
            }
            return new Course.Course { Name = "Daily Hole in One", Key = CourseKey, Holes = holes.ToArray() };
        }

        /// How far from `cup` shot `index` is played along `heading` (radians), yards: the chip's few yards off the green there,
        /// else the shot's band.
        public static (double Min, double Max) BandFor(int index, Hole hole, CoursePoint cup, double heading)
        {
            if (index > 0) return Bands[Math.Min(index, Bands.Length - 1)];
            double edge = OffTheGreen(hole, cup, heading);
            double min = Math.Min(edge + ChipPast, ChipMax);
            return (min, Math.Min(min + ChipReach, ChipMax));
        }

        /// The yards from `cup` along `heading` (radians) to where the green and its fringe end.
        static double OffTheGreen(Hole hole, CoursePoint cup, double heading)
        {
            for (double y = .5; y < ChipMax; y += .5)
            {
                var lie = hole.LieAt(new CoursePoint(cup.X + y * Math.Sin(heading), cup.D + y * Math.Cos(heading)));
                if (lie != CourseLie.Green && lie != CourseLie.Fringe) return y;
            }
            return ChipMax;
        }

        /// Where the day's cup is cut: up to half the green's radius (at most 9 yd, 27 ft) from its middle, on the green and never in
        /// a hazard; the middle itself when no try fits.
        public static CoursePoint CupFor(int day, int index, Hole hole)
        {
            var dice = DiceFor(day, 1 + index);
            double reach = Math.Min(hole.GreenRadius * .5, 9);
            for (int attempt = 0; attempt < 24; attempt++)
            {
                double r = reach * Math.Sqrt(dice.NextDouble()), a = dice.NextDouble() * Math.PI * 2;
                var offset = new CoursePoint(r * Math.Sin(a), r * Math.Cos(a));
                var cup = new CoursePoint(hole.GreenCenter.X + offset.X, hole.GreenCenter.D + offset.D);
                // (and a fair lie somewhere on the shot's ring round it: a cup by the cliff edge can leave nothing but sea there)
                if (hole.LieAt(cup) == CourseLie.Green && hole.HazardAt(cup) == null && hole.GreenCenter.DistanceTo(cup) <= hole.GreenRadius - 3 && HasGround(hole, cup, index)) return offset;
            }
            return CoursePoint.Zero;
        }

        /// The spot the day's shot on a built hole is played from (index 0–2): the chip a few yards off the green, then the shot's
        /// band (Bands), on the side the hole is played from, on dry fairway with a clear line to the pin. Tries rough, then any side,
        /// before falling back to the hole's own line of play.
        public static CoursePoint StartFor(int day, int index, Hole hole, Func<CoursePoint, string> drawnAt = null)
        {
            // the turf as drawn (the model's FAIRWAY / TEE_BOX meshes; null: a hole without a model, where the lines are all there is)
            bool Turf(CoursePoint p) { var n = drawnAt?.Invoke(p); return n == null || n.StartsWith("FAIRWAY") || n.StartsWith("TEE_BOX"); }
            var cup = hole.Pin;
            // "the side the hole is played from": back along the line of play from the green
            double mid = index <= 0 ? hole.GreenRadius + ChipPast + ChipReach / 2 : (Bands[Math.Min(index, Bands.Length - 1)].Min + Bands[Math.Min(index, Bands.Length - 1)].Max) / 2;
            double back = cup.HeadingTo(BackAlong(hole, mid));
            // passes, strictest first: the middle of the fairway on drawn fairway turf (the modelled turf can be narrower than the
            // fairway's width, and on the Magma holes the ash beside it still counts as fairway), any fairway on drawn turf, rough on
            // drawn turf, then the lines alone, then any side of the green
            for (int pass = 0; pass < 5; pass++)
            {
                var dice = DiceFor(day, 10 + index * 5 + pass);   // each pass its own stream: a looser pass never changes a stricter one's picks
                // (the long shots keep closer to the line of play: 55° off it 175 yd out is across the next fairway)
                double spread = pass == 4 ? 180 : index >= 2 ? 25 : index == 1 ? 35 : 55;
                for (int attempt = 0; attempt < 80; attempt++)
                {
                    double u = dice.NextDouble();
                    double h = (back + (dice.NextDouble() * 2 - 1) * spread) * Math.PI / 180;
                    var band = BandFor(index, hole, cup, h);
                    double yards = band.Min + (band.Max - band.Min) * u;
                    var spot = new CoursePoint(cup.X + yards * Math.Sin(h), cup.D + yards * Math.Cos(h));
                    if (pass == 0 && hole.DistanceFromCenterline(spot) > hole.FairwayWidth * .3) continue;
                    if (pass < 3 && !Turf(spot)) continue;
                    if (Playable(hole, spot, cup, roughOk: pass > 1)) return spot;
                }
            }
            // every spot on the ring in turn, nearest the line of play first: on drawn turf with the full checks, the full checks,
            // then the lie alone
            for (int pass = 0; pass < 3; pass++)
                foreach (var spot in Ring(hole, cup, back, index))
                    if (pass == 0 ? Turf(spot) && Playable(hole, spot, cup, roughOk: true) : pass == 1 ? Playable(hole, spot, cup, roughOk: true) : FairLie(hole, spot, true)) return spot;
            var line = BackAlong(hole, mid);
            double d = line.DistanceTo(cup);
            return d < 1 ? line : new CoursePoint(cup.X + (line.X - cup.X) * mid / d, cup.D + (line.D - cup.D) * mid / d);
        }

        /// Shot `index`'s ring round `cup` (BandFor), as spots every 3° and 2 yd (1 yd for the chip), the ones nearest `back`
        /// (degrees) first.
        static IEnumerable<CoursePoint> Ring(Hole hole, CoursePoint cup, double back, int index)
        {
            for (int step = 0; step <= 60; step++)
                for (int side = step == 0 ? 1 : -1; side <= 1; side += 2)
                {
                    double h = (back + side * step * 3) * Math.PI / 180;
                    var band = BandFor(index, hole, cup, h);
                    double stride = index <= 0 ? 1 : 2;
                    for (double yards = band.Min + stride / 2; yards <= band.Max; yards += stride)
                        yield return new CoursePoint(cup.X + yards * Math.Sin(h), cup.D + yards * Math.Cos(h));
                }
        }

        /// The hole has dry, fair ground somewhere on shot `index`'s ring round `cup` (a hole with none is never dealt that shot).
        static bool HasGround(Hole hole, CoursePoint cup, int index)
        {
            foreach (var spot in Ring(hole, cup, 0, index)) if (FairLie(hole, spot, false)) return true;
            return false;
        }

        static bool FairLie(Hole hole, CoursePoint spot, bool roughOk)
        {
            var lie = hole.LieAt(spot);
            return (lie == CourseLie.Fairway || lie == CourseLie.Tee || (roughOk && lie == CourseLie.Rough)) && hole.OnLand(spot) && hole.HazardAt(spot) == null;
        }

        /// A point `yards` back from the green along the hole's centreline (its last leg, then the ones before it).
        static CoursePoint BackAlong(Hole hole, double yards)
        {
            var line = hole.Centerline;
            double left = yards;
            for (int i = line.Length - 1; i > 0; i--)
            {
                var a = line[i]; var b = line[i - 1];
                double leg = a.DistanceTo(b);
                if (leg >= left && leg > 0) { double t = left / leg; return new CoursePoint(a.X + (b.X - a.X) * t, a.D + (b.D - a.D) * t); }
                left -= leg;
            }
            return hole.Tee;
        }

        /// Can the shot be made from here: a fair lie on dry land, and nothing in the way along the line to the cup?
        public static bool Playable(Hole hole, CoursePoint spot, CoursePoint cup, bool roughOk)
        {
            if (!FairLie(hole, spot, roughOk)) return false;
            if (hole.Solids != null && hole.Solids.NearOver(spot.X, spot.D, 2)) return false;
            // the ground: no standing on a ledge far above or below the green, and no rise in the way the shot cannot clear
            double startY = Height(hole, spot), cupY = Height(hole, cup);
            if (Math.Abs(startY - cupY) > 9) return false;
            double arc = Arc(spot.DistanceTo(cup));
            for (int k = 1; k < 20; k++)
            {
                double t = k / 20.0;
                var p = new CoursePoint(spot.X + (cup.X - spot.X) * t, spot.D + (cup.D - spot.D) * t);
                // the line must stay inside the hole: no carrying over the tree line (out of bounds)
                if (hole.OnLand(p) && hole.LieAt(p) == CourseLie.OutOfBounds) return false;
                // (a long iron is well up in the air mid-flight: only what rises above its arc is in the way)
                double lift = arc * 4 * t * (1 - t);
                if (Height(hole, p) > Math.Max(startY, cupY) + 3.5 + lift) return false;
                if (t < .9 && lift < 8 && hole.Solids != null && hole.Solids.NearOver(p.X, p.D, 1.2)) return false;
            }
            // trees, rocks and walls standing near the line (the last few yards before the green too), unless the ball sails over
            foreach (var o in hole.Obstacles)
            {
                double reach = Math.Max(o.Radius, o.TrunkRadius) + 1.5;
                var c = new CoursePoint(o.X, o.D);
                if (c.DistanceTo(cup) < 3) continue;   // (the flagstick's neighbours: nothing the ball flies through)
                if (SegmentDistance(spot, cup, c, out double t) >= reach) continue;
                double flight = startY + (cupY - startY) * t + arc * 4 * t * (1 - t);
                if (arc <= 0 || o.Top + 2 > flight) return false;
            }
            return true;
        }

        /// How high (yards) a shot of `yards` is taken to fly over the middle of its line, at the least: nothing for a chip or a
        /// pitch, about 14 yd for a 175-yard iron (a real one peaks higher, so this keeps a margin).
        static double Arc(double yards) => yards < 60 ? 0 : yards * .08;

        static double Height(Hole hole, CoursePoint p) => hole.Ground != null ? hole.Ground(p) : 0;

        static double SegmentDistance(CoursePoint a, CoursePoint b, CoursePoint p, out double t)
        {
            double dx = b.X - a.X, dd = b.D - a.D, l2 = Math.Max(dx * dx + dd * dd, 1e-6);
            t = Math.Min(1, Math.Max(0, ((p.X - a.X) * dx + (p.D - a.D) * dd) / l2));
            return p.DistanceTo(new CoursePoint(a.X + t * dx, a.D + t * dd));
        }
    }

    /// The world board as the phone describes it (DailyHoleInOne.swift boardJSON): the menu's Daily Challenges screens and the
    /// round's last card draw it.
    [Serializable]
    public sealed class HoleInOneBoard
    {
        public int day; public bool played; public int total; public int[] shots; public float[] feet;
        public string state, note; public int rank, players, percentile, top, hours, minutes;
        public HoleInOneBoardEntry[] entries;

        public static HoleInOneBoard Parse(string json)
        {
            if (string.IsNullOrEmpty(json)) return null;
            try { return UnityEngine.JsonUtility.FromJson<HoleInOneBoard>(json); } catch { return null; }
        }
        /// "TOP 12%" once the world has ranked it, else what the phone says (loading, signed out).
        public bool Ranked => state == "live" && rank > 0 && players > 0;
    }

    [Serializable]
    public sealed class HoleInOneBoardEntry { public int rank; public string name; public int score; public bool me; }
}
