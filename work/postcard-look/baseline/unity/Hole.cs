using System;
using System.Collections.Generic;

namespace GolfArcade.Course
{
    /// A spot on the ground, in yards: `X` to the right of the tee line, `D` down the hole.
    public struct CoursePoint
    {
        public double X, D;
        public CoursePoint(double x, double d) { X = x; D = d; }
        public static readonly CoursePoint Zero = new(0, 0);
        public double DistanceTo(CoursePoint o) { double dx = X - o.X, dd = D - o.D; return Math.Sqrt(dx * dx + dd * dd); }
        /// Degrees right of straight down the hole (+D) toward `o`.
        public double HeadingTo(CoursePoint o) => Math.Atan2(o.X - X, o.D - D) * 180 / Math.PI;
        public override string ToString() => $"({X:F1}, {D:F1})";
    }

    public enum CourseLie { Tee, Fairway, Rough, Bunker, Green, Water, OutOfBounds }

    public static class CourseLies
    {
        public static string Label(this CourseLie lie) => lie switch
        {
            CourseLie.Tee => "Tee",
            CourseLie.Fairway => "Fairway",
            CourseLie.Rough => "Rough",
            CourseLie.Bunker => "Bunker",
            CourseLie.Green => "Green",
            CourseLie.Water => "Water",
            _ => "Out of bounds",
        };

        /// What the lie costs in club speed.
        public static double PowerFactor(this CourseLie lie) => lie switch
        {
            CourseLie.Rough => 0.85,
            CourseLie.Bunker => 0.6,
            _ => 1,
        };

        public static int PenaltyStrokes(this CourseLie lie) => lie is CourseLie.Water or CourseLie.OutOfBounds ? 1 : 0;
    }

    public enum HazardKind { Bunker, Water }

    /// An elliptical hazard, in yards.
    public struct CourseHazard
    {
        public HazardKind Kind;
        public double X, Distance, Width, Length;

        public CourseHazard(HazardKind kind, double x, double distance, double width, double length)
        {
            Kind = kind; X = x; Distance = distance; Width = width; Length = length;
        }

        public bool Contains(CoursePoint p)
        {
            double dx = (p.X - X) / Math.Max(Width / 2, 0.001);
            double dz = (p.D - Distance) / Math.Max(Length / 2, 0.001);
            return dx * dx + dz * dz <= 1;
        }
    }

    /// One hole, in the flight model's yards so drawing and scoring share one source of truth.
    public sealed class Hole
    {
        public int Number;
        public int Par;
        public CoursePoint[] Centerline;
        public double FairwayWidth;
        public double GreenRadius;
        public CourseHazard[] Hazards = Array.Empty<CourseHazard>();
        /// Dry land, as a polygon in course yards; anything outside it is water. Null means the
        /// hole is inland and the tree line is the only edge.
        public CoursePoint[] Shore;

        /// Rough on each side of the fairway. Beyond it (the tree line) is out of bounds.
        public double RoughWidth = 24.0;
        /// Small, explicit arcade tolerance around the cup, in yards.
        public const double CupCaptureRadius = 0.12;

        public CoursePoint Tee => Centerline[0];
        public CoursePoint Pin => Centerline[Centerline.Length - 1];

        public double Length
        {
            get { double l = 0; for (int i = 1; i < Centerline.Length; i++) l += Centerline[i - 1].DistanceTo(Centerline[i]); return l; }
        }

        /// Follow the next landing station, not a straight shortcut through a dogleg.
        public CoursePoint RecommendedTarget(CoursePoint ball)
        {
            if (Centerline.Length <= 2 || ball.DistanceTo(Pin) <= GreenRadius + 20) return Pin;
            double closest = double.PositiveInfinity;
            int segment = 0;
            for (int i = 0; i < Centerline.Length - 1; i++)
            {
                var a = Centerline[i]; var b = Centerline[i + 1];
                double dx = b.X - a.X, dd = b.D - a.D;
                double t = Math.Min(1, Math.Max(0, ((ball.X - a.X) * dx + (ball.D - a.D) * dd) / Math.Max(0.001, dx * dx + dd * dd)));
                double distance = ball.DistanceTo(new CoursePoint(a.X + t * dx, a.D + t * dd));
                if (distance <= closest) { closest = distance; segment = i; }
            }
            int station = segment + 1;
            while (station < Centerline.Length - 1 && ball.DistanceTo(Centerline[station]) < 35) station++;
            return Centerline[station];
        }

        public double DistanceFromCenterline(CoursePoint p)
        {
            double best = double.PositiveInfinity;
            for (int i = 1; i < Centerline.Length; i++)
            {
                var a = Centerline[i - 1]; var b = Centerline[i];
                double dx = b.X - a.X, dd = b.D - a.D;
                double l2 = Math.Max(dx * dx + dd * dd, 0.0001);
                double t = Math.Min(Math.Max(((p.X - a.X) * dx + (p.D - a.D) * dd) / l2, 0), 1);
                best = Math.Min(best, p.DistanceTo(new CoursePoint(a.X + dx * t, a.D + dd * t)));
            }
            return best;
        }

        public bool OnLand(CoursePoint p) => Shore == null || Inside(Shore, p);

        /// Even-odd point-in-polygon.
        static bool Inside(CoursePoint[] poly, CoursePoint p)
        {
            bool inside = false;
            for (int i = 0, j = poly.Length - 1; i < poly.Length; j = i++)
            {
                var a = poly[i]; var b = poly[j];
                if ((a.D > p.D) != (b.D > p.D) && p.X < (b.X - a.X) * (p.D - a.D) / (b.D - a.D) + a.X) inside = !inside;
            }
            return inside;
        }

        public CourseLie LieAt(CoursePoint p)
        {
            foreach (var h in Hazards) if (h.Contains(p)) return h.Kind == HazardKind.Water ? CourseLie.Water : CourseLie.Bunker;
            if (!OnLand(p)) return CourseLie.Water;
            if (p.DistanceTo(Pin) <= GreenRadius) return CourseLie.Green;
            if (p.DistanceTo(Tee) <= 4) return CourseLie.Tee;
            double offset = DistanceFromCenterline(p);
            if (offset <= FairwayWidth / 2) return CourseLie.Fairway;
            if (offset <= FairwayWidth / 2 + RoughWidth) return CourseLie.Rough;
            return CourseLie.OutOfBounds;
        }
    }

    public sealed class Course
    {
        public string Name;
        public Hole[] Holes;
        public int Par { get { int p = 0; foreach (var h in Holes) p += h.Par; return p; } }

        static CoursePoint P(double x, double d) => new(x, d);
        static CourseHazard Bunker(double x, double d, double w, double l) => new(HazardKind.Bunker, x, d, w, l);

        /// Cliffside: the Blender-built island hole (blender/hole_07.blend), in the flight model's
        /// yards. Tee at the origin, the hole running straight up +D, ocean off the east cliffs.
        /// The numbers come from blender/scripts/hole07_design.py: metres from the tee marker
        /// times 1.0936; the shore is the island's control polygon.
        public static Course Cliffside() => new()
        {
            Name = "Cliffside",
            Holes = new[]
            {
                new Hole
                {
                    Number = 7, Par = 4,
                    Centerline = new[] { P(0, 0), P(-8.7, 206.7), P(8.7, 312.8), P(18.6, 415.6) },
                    FairwayWidth = 48, GreenRadius = 26,
                    RoughWidth = 100, // the whole island top plays as rough; the shore decides water
                    Hazards = new[]
                    {
                        Bunker(-41.6, 319.3, 35.0, 21.9), Bunker(-30.6, 280.0, 26.2, 17.5), Bunker(50.3, 253.7, 32.8, 21.9),
                        Bunker(-35.0, 382.8, 28.4, 19.7), Bunker(54.7, 374.0, 30.6, 21.9), Bunker(50.3, 430.9, 24.1, 17.5),
                    },
                    Shore = new[]
                    {
                        P(-17, -46), P(33, -42), P(77, -15), P(94, 28), P(79, 79), P(85, 120), P(68, 162), P(39, 201), P(57, 241), P(101, 273),
                        P(92, 319), P(70, 359), P(98, 394), P(79, 435), P(57, 468), P(24, 499), P(-13, 490), P(-42, 464), P(-59, 427), P(-63, 383),
                        P(-90, 339), P(-70, 295), P(-94, 249), P(-101, 206), P(-116, 160), P(-107, 101), P(-92, 52), P(-77, 7), P(-46, -28),
                    },
                },
            },
        };

        /// Postcards: three scenic one-height holes (8 Needle, 9 Split, 10 Crater) on the same scoring
        /// rules as Cliffside. Every number below is printed by blender/scripts/postcard_emit_cs.py from
        /// blender/scripts/hole08/09/10_design.py, the same data the Blender meshes were built from.
        /// The play surface is one height; cliffs, lava and the sea sit below it as scenery.
        public static Course Postcards() => new()
        {
            Name = "Postcards",
            Holes = new[]
            {
                new Hole
                {
                    // Needle: 202-point shore, centerline 342.9 yd, play surface flat at 6 m in blender/hole_08.blend
                    Number = 8, Par = 4,
                    Centerline = new[] { P(0, 0), P(19, 178), P(-6, 340) },
                    FairwayWidth = 16, GreenRadius = 14, RoughWidth = 8,
                    Hazards = new[]
                    {
                        Water(10.1, 90, 48, 94),
                        Water(6.6, 258, 48, 88),
                        Bunker(-12, 316, 9, 20),
                    },
                    Shore = new[]
                    {
                        P(15.8, -1.7), P(16.2, 2.3), P(16.7, 6.3), P(16.9, 10.3), P(16.5, 14.2), P(17.2, 18.1),
                        P(18.2, 22), P(18.7, 26), P(18.7, 30), P(18.7, 34), P(17.3, 37.7), P(15.8, 41.4),
                        P(15.9, 45.4), P(16.3, 49.4), P(15.3, 53.1), P(13, 56.4), P(11.9, 60.1), P(12.4, 64.1),
                        P(12.8, 68.1), P(13.2, 72.1), P(13.6, 76), P(14.1, 80), P(14.5, 84), P(14.9, 88),
                        P(15.3, 92), P(15.8, 95.9), P(16.2, 99.9), P(16.6, 103.9), P(17, 107.9), P(17.5, 111.8),
                        P(17.9, 115.8), P(18.3, 119.8), P(20.6, 123), P(23.5, 125.8), P(24.9, 129.4), P(25.3, 133.4),
                        P(26.3, 137.2), P(28.6, 140.4), P(30.5, 143.9), P(31.1, 147.9), P(32, 151.8), P(32.6, 155.7),
                        P(32.6, 159.7), P(32.4, 163.7), P(32.3, 167.7), P(32.7, 171.7), P(33.1, 175.7), P(33.1, 179.7),
                        P(32.6, 183.6), P(32.2, 187.6), P(32.1, 191.6), P(32.1, 195.6), P(31.7, 199.6), P(30.8, 203.5),
                        P(29.8, 207.4), P(28.3, 211), P(25.8, 214.1), P(24, 217.6), P(23.4, 221.6), P(22.5, 225.5),
                        P(19.7, 228.2), P(16.8, 231), P(15.8, 234.8), P(15.2, 238.8), P(14.6, 242.7), P(14, 246.7),
                        P(13.4, 250.6), P(12.7, 254.6), P(12.1, 258.5), P(11.5, 262.5), P(10.9, 266.4), P(10.3, 270.4),
                        P(9.7, 274.4), P(9.1, 278.3), P(8.5, 282.3), P(8, 286.2), P(9.7, 289.8), P(11.8, 293.2),
                        P(11.7, 297.2), P(11.1, 301.1), P(11.4, 305.1), P(12.8, 308.8), P(13.2, 312.7), P(12.5, 316.7),
                        P(12.4, 320.7), P(12.4, 324.7), P(11.8, 328.6), P(11.2, 332.6), P(10.6, 336.5), P(10, 340.5),
                        P(9.3, 344.4), P(7.7, 348.1), P(5.3, 351.2), P(2.1, 353.7), P(-1.6, 355.3), P(-5.5, 355.9),
                        P(-9.5, 355.5), P(-13.2, 354.2), P(-16.5, 351.9), P(-19.2, 348.9), P(-21, 345.4), P(-21.8, 341.5),
                        P(-21.7, 337.5), P(-21.1, 333.5), P(-20.5, 329.6), P(-19.9, 325.6), P(-19.3, 321.6), P(-18.6, 317.7),
                        P(-18, 313.7), P(-17.4, 309.8), P(-16, 306.1), P(-13.4, 303.1), P(-11.1, 299.8), P(-10.3, 295.9),
                        P(-9.7, 292), P(-7.5, 288.7), P(-4.4, 286.2), P(-2.7, 282.7), P(-2.1, 278.7), P(-1.5, 274.8),
                        P(-0.9, 270.8), P(-0.3, 266.9), P(0.3, 262.9), P(0.9, 259), P(1.6, 255), P(2.2, 251),
                        P(2.8, 247.1), P(3.4, 243.1), P(4, 239.2), P(4.6, 235.2), P(5.2, 231.3), P(4.4, 227.5),
                        P(2.2, 224.1), P(1.3, 220.3), P(1.9, 216.4), P(2.3, 212.4), P(1.1, 208.6), P(0, 204.7),
                        P(0.7, 200.9), P(1.8, 197), P(2.5, 193.1), P(2.7, 189.1), P(2.6, 185.1), P(2.9, 181.1),
                        P(3.5, 177.2), P(2.9, 173.2), P(2.7, 169.2), P(2.8, 165.2), P(3, 161.2), P(2.8, 157.2),
                        P(2, 153.3), P(1, 149.4), P(1.1, 145.5), P(2.6, 141.8), P(3.6, 137.9), P(3.2, 134),
                        P(2.9, 130), P(4.5, 126.4), P(6.8, 123.1), P(7.2, 119.2), P(6.8, 115.2), P(6.3, 111.3),
                        P(5.9, 107.3), P(5.5, 103.3), P(5.1, 99.3), P(4.6, 95.3), P(4.2, 91.4), P(3.8, 87.4),
                        P(3.4, 83.4), P(2.9, 79.4), P(2.5, 75.4), P(2.1, 71.5), P(1.7, 67.5), P(1.2, 63.5),
                        P(0.6, 59.6), P(-2.1, 56.7), P(-4.9, 53.8), P(-5.7, 49.9), P(-6.2, 46), P(-7.5, 42.2),
                        P(-9.8, 39), P(-11.2, 35.3), P(-10.9, 31.3), P(-11.1, 27.3), P(-11.8, 23.3), P(-12.9, 19.5),
                        P(-14, 15.6), P(-14.7, 11.7), P(-15.2, 7.7), P(-15.6, 3.8), P(-15.9, -0.2), P(-15.3, -4.2),
                        P(-13.8, -7.9), P(-11.4, -11.1), P(-8.3, -13.6), P(-4.7, -15.2), P(-0.7, -15.9), P(3.2, -15.6),
                        P(7, -14.3), P(10.3, -12.1), P(13, -9.1), P(14.9, -5.6),
                    },
                },
                new Hole
                {
                    // Split: 415-point shore, centerline 494.1 yd, play surface flat at 6 m in blender/hole_09.blend
                    Number = 9, Par = 5,
                    Centerline = new[] { P(0, 0), P(3, 60), P(6.3, 125), P(9.5, 190), P(11.8, 235), P(6, 416), P(-1, 454), P(-10, 492) },
                    FairwayWidth = 18, GreenRadius = 17, RoughWidth = 90,
                    Hazards = new[]
                    {
                        Water(8.8, 352, 84, 102),
                        Bunker(-2.5, 184, 11, 24),
                        Bunker(21.8, 200, 11, 24),
                        Bunker(9, 466, 16, 16),
                    },
                    Shore = new[]
                    {
                        P(-93.6, 25.8), P(-93.5, 20.8), P(-93.2, 15.8), P(-92.6, 10.8), P(-91.8, 5.9), P(-90.6, 1),
                        P(-88, -3.3), P(-84.5, -6.9), P(-80.6, -9.9), P(-76.3, -12.5), P(-71.9, -14.8), P(-67.4, -17.1),
                        P(-62.9, -19.3), P(-58.4, -21.4), P(-53.9, -23.4), P(-49.3, -25.4), P(-44.6, -27.2), P(-39.8, -28.8),
                        P(-35, -30.1), P(-30.2, -31.2), P(-25.2, -32.1), P(-20.3, -32.8), P(-15.3, -33.3), P(-10.3, -33.6),
                        P(-5.3, -33.6), P(-0.3, -33.2), P(4.6, -32.6), P(9.5, -31.5), P(14.2, -29.8), P(18.3, -27),
                        P(21.3, -23), P(22.8, -18.3), P(23.3, -13.3), P(23, -8.3), P(22.5, -3.3), P(22.2, 1.6),
                        P(22.1, 6.6), P(22.3, 11.6), P(22.5, 16.6), P(22.7, 21.6), P(22.9, 26.6), P(23.1, 31.6),
                        P(23.3, 36.6), P(23.5, 41.6), P(23.6, 46.6), P(23.7, 51.6), P(23.9, 56.6), P(24, 61.6),
                        P(24.1, 66.6), P(24.2, 71.6), P(24.3, 76.6), P(24.4, 81.6), P(24.6, 86.6), P(24.8, 91.6),
                        P(25, 96.6), P(25.3, 101.6), P(25.5, 106.6), P(25.8, 111.6), P(26.2, 116.6), P(26.5, 121.6),
                        P(26.9, 126.6), P(27.3, 131.5), P(27.7, 136.5), P(28.1, 141.5), P(28.5, 146.5), P(28.9, 151.5),
                        P(29.3, 156.5), P(29.6, 161.5), P(30, 166.4), P(30.3, 171.4), P(30.6, 176.4), P(30.9, 181.4),
                        P(31.2, 186.4), P(31.4, 191.4), P(31.7, 196.4), P(31.9, 201.4), P(32.1, 206.4), P(32.2, 211.4),
                        P(32.4, 216.4), P(32.5, 221.4), P(32.5, 226.4), P(32.5, 231.4), P(32.5, 236.4), P(32.4, 241.4),
                        P(32.3, 246.4), P(32.2, 251.4), P(32.1, 256.4), P(32, 261.4), P(31.9, 266.4), P(31.8, 271.4),
                        P(31.7, 276.4), P(31.7, 281.4), P(31.6, 286.4), P(31.6, 291.4), P(31.4, 296.4), P(30.7, 301.3),
                        P(26.8, 303.9), P(22.1, 302.6), P(17.3, 301.1), P(12.3, 300.3), P(7.3, 300.1), P(2.4, 300.7),
                        P(-2.5, 301.8), P(-7.4, 302), P(-10.3, 298.2), P(-10.6, 293.2), P(-10.2, 288.2), P(-9.8, 283.2),
                        P(-9.6, 278.2), P(-9.3, 273.2), P(-9.1, 268.3), P(-8.9, 263.3), P(-8.7, 258.3), P(-8.6, 253.3),
                        P(-8.5, 248.3), P(-8.4, 243.3), P(-8.4, 238.3), P(-8.5, 233.3), P(-8.6, 228.3), P(-8.8, 223.3),
                        P(-9, 218.3), P(-9.4, 213.3), P(-9.7, 208.3), P(-10.1, 203.3), P(-10.5, 198.3), P(-10.9, 193.3),
                        P(-11.3, 188.3), P(-11.7, 183.4), P(-12.1, 178.4), P(-12.5, 173.4), P(-12.9, 168.4), P(-13.2, 163.4),
                        P(-13.6, 158.4), P(-13.9, 153.4), P(-14.3, 148.4), P(-14.6, 143.5), P(-14.9, 138.5), P(-15.1, 133.5),
                        P(-15.4, 128.5), P(-15.6, 123.5), P(-15.8, 118.5), P(-16, 113.5), P(-16.2, 108.5), P(-16.3, 103.5),
                        P(-16.5, 98.5), P(-16.6, 93.5), P(-16.7, 88.5), P(-16.9, 83.5), P(-17, 78.5), P(-17.1, 73.5),
                        P(-17.2, 68.5), P(-17.4, 63.5), P(-17.5, 58.5), P(-17.8, 53.5), P(-18.3, 48.5), P(-19.6, 43.7),
                        P(-22.3, 39.5), P(-26.1, 36.3), P(-30.7, 34.5), P(-35.7, 34.2), P(-40.5, 35.5), P(-44.7, 38.1),
                        P(-47.9, 42), P(-49.7, 46.6), P(-50.3, 51.6), P(-50.4, 56.6), P(-50.3, 61.6), P(-50.2, 66.6),
                        P(-50.1, 71.6), P(-50, 76.6), P(-49.8, 81.6), P(-49.7, 86.6), P(-49.5, 91.6), P(-49.3, 96.6),
                        P(-49, 101.6), P(-48.7, 106.6), P(-48.4, 111.5), P(-48.1, 116.5), P(-47.7, 121.5), P(-47.3, 126.5),
                        P(-46.9, 131.5), P(-46.4, 136.5), P(-45.9, 141.4), P(-45.4, 146.4), P(-44.8, 151.4), P(-44.3, 156.4),
                        P(-43.7, 161.3), P(-43.1, 166.3), P(-42.5, 171.3), P(-41.9, 176.2), P(-41.2, 181.2), P(-40.6, 186.1),
                        P(-40, 191.1), P(-39.4, 196.1), P(-38.8, 201), P(-38.3, 206), P(-37.7, 211), P(-37.3, 216),
                        P(-36.9, 220.9), P(-36.5, 225.9), P(-36.3, 230.9), P(-36.3, 235.9), P(-36.2, 240.9), P(-36.3, 245.9),
                        P(-36.5, 250.9), P(-36.8, 255.9), P(-37.1, 260.9), P(-37.5, 265.9), P(-38, 270.9), P(-38.5, 275.9),
                        P(-39.1, 280.8), P(-39.7, 285.8), P(-40.3, 290.7), P(-41, 295.7), P(-41.7, 300.6), P(-42.4, 305.6),
                        P(-43.1, 310.6), P(-43.8, 315.5), P(-44.5, 320.5), P(-45.1, 325.4), P(-45.7, 330.4), P(-46.3, 335.4),
                        P(-46.8, 340.3), P(-47.3, 345.3), P(-47.7, 350.3), P(-48.1, 355.3), P(-48.4, 360.3), P(-48.6, 365.3),
                        P(-48.8, 370.3), P(-49, 375.3), P(-49.1, 380.3), P(-49.1, 385.3), P(-49.2, 390.3), P(-49.2, 395.3),
                        P(-49.2, 400.3), P(-49.2, 405.3), P(-49.2, 410.3), P(-49.4, 415.3), P(-49.8, 420.2), P(-50.4, 425.2),
                        P(-51.1, 430.2), P(-51.9, 435.1), P(-52.8, 440), P(-53.6, 445), P(-54.4, 449.9), P(-53.3, 454.8),
                        P(-51.2, 459.3), P(-47.8, 462.9), P(-43.4, 465.3), P(-38.6, 466.4), P(-33.6, 465.9), P(-29, 464),
                        P(-25.2, 460.8), P(-22.6, 456.6), P(-21.1, 451.8), P(-20, 447), P(-18.9, 442.1), P(-17.9, 437.2),
                        P(-16.9, 432.3), P(-16, 427.4), P(-15.2, 422.4), P(-14.5, 417.5), P(-14, 412.5), P(-13.7, 407.5),
                        P(-12.8, 402.6), P(-8.8, 400.2), P(-4, 401.6), P(0.8, 403), P(5.7, 403.8), P(10.7, 403.8),
                        P(15.7, 403.2), P(20.6, 402.2), P(25.3, 403.1), P(27.2, 407.6), P(26.9, 412.6), P(26, 417.5),
                        P(25.2, 422.4), P(24.8, 427.4), P(24.8, 432.4), P(25.1, 437.4), P(25.7, 442.4), P(26.3, 447.3),
                        P(27, 452.3), P(27.9, 457.2), P(28.8, 462.1), P(29.9, 467), P(30.6, 471.9), P(30.9, 476.9),
                        P(30.9, 481.9), P(30.5, 486.9), P(29.6, 491.8), P(28.3, 496.7), P(26.5, 501.3), P(24.4, 505.9),
                        P(21.8, 510.1), P(18.7, 514.1), P(15.2, 517.6), P(11.3, 520.7), P(6.9, 523.1), P(2.2, 524.9),
                        P(-2.6, 526.2), P(-7.5, 527.1), P(-12.5, 527.6), P(-17.5, 527.9), P(-22.5, 527.8), P(-27.5, 527.4),
                        P(-32.4, 526.8), P(-37.3, 525.9), P(-42.2, 524.7), P(-46.9, 523.1), P(-51.6, 521.3), P(-56.1, 519.1),
                        P(-60.4, 516.6), P(-64.6, 513.8), P(-68.6, 510.9), P(-72.7, 508), P(-76.6, 504.9), P(-80.5, 501.7),
                        P(-84.2, 498.4), P(-87.4, 494.5), P(-89.7, 490.1), P(-91.2, 485.4), P(-91.5, 480.4), P(-91.2, 475.4),
                        P(-91.1, 470.4), P(-91.5, 465.5), P(-92.5, 460.6), P(-93.2, 455.6), P(-93.3, 450.6), P(-92.9, 445.6),
                        P(-92.4, 440.7), P(-91.7, 435.7), P(-90.7, 430.8), P(-89.2, 426.1), P(-88, 421.2), P(-88.4, 416.2),
                        P(-89.8, 411.5), P(-90.7, 406.5), P(-90.8, 401.6), P(-90.4, 396.6), P(-89.7, 391.6), P(-88.7, 386.7),
                        P(-87.6, 381.8), P(-86.4, 377), P(-86, 372), P(-86.5, 367), P(-87.5, 362.2), P(-87.8, 357.2),
                        P(-87.4, 352.2), P(-86.4, 347.3), P(-85.1, 342.4), P(-83.8, 337.6), P(-82.9, 332.7), P(-82.4, 327.7),
                        P(-82.5, 322.7), P(-83.1, 317.8), P(-83.6, 312.8), P(-83.4, 307.8), P(-82.6, 302.9), P(-81.3, 298.1),
                        P(-79.4, 293.4), P(-77.8, 288.7), P(-77, 283.8), P(-76.8, 278.8), P(-76.7, 273.8), P(-76.6, 268.8),
                        P(-76.2, 263.8), P(-75.4, 258.9), P(-74.1, 254), P(-72.4, 249.3), P(-70.3, 244.8), P(-69, 240),
                        P(-68.8, 235), P(-69.6, 230.1), P(-70.2, 225.1), P(-70.6, 220.1), P(-70.9, 215.1), P(-71.1, 210.1),
                        P(-71.1, 205.1), P(-70.6, 200.2), P(-70, 195.2), P(-70.7, 190.3), P(-72.8, 185.8), P(-75.1, 181.3),
                        P(-76.8, 176.6), P(-77.9, 171.8), P(-78.8, 166.9), P(-79.8, 161.9), P(-80.5, 157), P(-80.5, 152),
                        P(-80.3, 147), P(-81.4, 142.2), P(-83.7, 137.7), P(-85.9, 133.3), P(-87, 128.4), P(-87, 123.4),
                        P(-86.9, 118.4), P(-87, 113.4), P(-86.8, 108.4), P(-86, 103.5), P(-85.1, 98.6), P(-85.7, 93.7),
                        P(-87.7, 89.1), P(-89.2, 84.3), P(-89.3, 79.4), P(-88.2, 74.5), P(-87.7, 69.5), P(-87.7, 64.5),
                        P(-87.6, 59.5), P(-87.1, 54.5), P(-86.9, 49.6), P(-88.2, 44.8), P(-90.4, 40.3), P(-92.2, 35.6),
                        P(-93.3, 30.7),
                    },
                },
                new Hole
                {
                    // Crater: 175-point shore, centerline 356.5 yd, play surface flat at 6 m in blender/hole_10.blend
                    Number = 10, Par = 4,
                    Centerline = new[] { P(0, 0), P(14.3, 66.2), P(50.2, 123.4), P(107.1, 159.3), P(261, 164.7) },
                    FairwayWidth = 22, GreenRadius = 16, RoughWidth = 13,
                    Hazards = new[]
                    {
                        Water(171.1, 161.5, 112, 76),
                        Bunker(57.4, 110.3, 17, 12),
                        Bunker(74.3, 154, 18, 13),
                    },
                    Shore = new[]
                    {
                        P(-15.6, -8.6), P(-15.5, -3.8), P(-14.8, 1), P(-14, 5.7), P(-13.1, 10.5), P(-12.3, 15.2),
                        P(-12, 20), P(-11.7, 24.8), P(-11.2, 29.6), P(-10.5, 34.4), P(-9.7, 39.1), P(-8.7, 43.8),
                        P(-7.8, 48.5), P(-7, 53.3), P(-6.3, 58), P(-5.7, 62.8), P(-5, 67.6), P(-3.8, 72.2),
                        P(-1.9, 76.6), P(0.5, 80.8), P(3, 84.9), P(5.6, 88.9), P(8.3, 93), P(10.9, 97),
                        P(13.5, 101.1), P(15.9, 105.2), P(18.3, 109.4), P(20.5, 113.7), P(22.7, 118), P(25, 122.2),
                        P(27.3, 126.4), P(29.8, 130.5), P(32.6, 134.5), P(35.7, 138.1), P(39.5, 141), P(43.7, 143.4),
                        P(47.9, 145.7), P(52.1, 148.1), P(56, 150.8), P(59.7, 153.9), P(63.2, 157.2), P(66.8, 160.4),
                        P(70.7, 163.2), P(75, 165.4), P(79.5, 167.2), P(83.9, 168.9), P(88.4, 170.7), P(92.9, 172.4),
                        P(97.4, 174.2), P(102, 175.7), P(106.7, 176.3), P(111.5, 175.9), P(116.2, 175.1), P(121, 174.6),
                        P(125.8, 174.5), P(130.6, 174.6), P(135.4, 174.8), P(140.2, 175), P(145.1, 175.1), P(149.9, 175.3),
                        P(154.7, 175.5), P(159.5, 175.6), P(164.3, 175.8), P(169.1, 176), P(173.9, 176.2), P(178.7, 176.3),
                        P(183.5, 176.5), P(188.3, 176.7), P(193.1, 176.8), P(198, 177), P(202.8, 177.2), P(207.6, 177.3),
                        P(212.4, 177.5), P(217.2, 177.7), P(222, 177.8), P(226.8, 178), P(231.6, 178.1), P(236.4, 178.5),
                        P(241.1, 179.6), P(245.4, 181.7), P(249.5, 184.2), P(253.8, 186.2), P(258.5, 187.3), P(263.3, 187.4),
                        P(268, 186.4), P(272.4, 184.4), P(276.3, 181.6), P(279.4, 178), P(281.8, 173.8), P(283.2, 169.2),
                        P(283.7, 164.5), P(283.2, 159.7), P(281.6, 155.2), P(279.2, 151.1), P(275.9, 147.6), P(272, 144.8),
                        P(267.6, 142.9), P(262.9, 142), P(258.1, 142.1), P(253.4, 143.3), P(249.1, 145.3), P(244.8, 147.5),
                        P(240.2, 148.9), P(235.4, 149.3), P(230.6, 149.2), P(225.8, 149), P(221, 148.8), P(216.2, 148.6),
                        P(211.4, 148.4), P(206.6, 148.3), P(201.8, 148.1), P(196.9, 147.9), P(192.1, 147.8), P(187.3, 147.6),
                        P(182.5, 147.4), P(177.7, 147.3), P(172.9, 147.1), P(168.1, 146.9), P(163.3, 146.8), P(158.5, 146.6),
                        P(153.7, 146.4), P(148.9, 146.3), P(144, 146.1), P(139.2, 145.9), P(134.4, 145.8), P(129.6, 145.6),
                        P(124.8, 145.3), P(120, 144.7), P(115.5, 143), P(111.5, 140.4), P(107.6, 137.6), P(103.5, 135),
                        P(99.4, 132.5), P(95.5, 129.7), P(91.7, 126.8), P(87.9, 123.8), P(84.2, 120.7), P(80.4, 117.7),
                        P(76.6, 114.9), P(72.7, 112.1), P(69, 108.9), P(66, 105.2), P(63.1, 101.3), P(60.2, 97.5),
                        P(57.1, 93.8), P(54, 90.1), P(51.1, 86.3), P(48.2, 82.5), P(45.3, 78.7), P(42.3, 74.9),
                        P(39.4, 71), P(36.5, 67.2), P(34, 63.1), P(32.4, 58.6), P(31.7, 53.8), P(31.2, 49),
                        P(30.6, 44.2), P(29.7, 39.5), P(28.5, 34.9), P(26.8, 30.4), P(24.9, 25.9), P(22.9, 21.5),
                        P(21, 17.2), P(19, 12.7), P(17.3, 8.2), P(16.1, 3.6), P(15, -1.1), P(13.8, -5.7),
                        P(12.4, -10.4), P(10.2, -14.5), P(6, -16.3), P(1.2, -15.8), P(-3.5, -14.8), P(-8.2, -13.8),
                        P(-12.7, -12.2),
                    },
                },
            },
        };

        static CourseHazard Water(double x, double d, double w, double l) => new(HazardKind.Water, x, d, w, l);

        /// Meadow Run: the iOS app's easy course, hole for hole.
        public static Course Meadow() => new()
        {
            Name = "Meadow Run",
            Holes = new[]
            {
                new Hole { Number = 1, Par = 4, Centerline = new[] { P(0, 0), P(0, 185), P(38, 245), P(105, 330) }, FairwayWidth = 50, GreenRadius = 20,
                    Hazards = new[] { Bunker(-22, 174, 16, 27), Bunker(60, 255, 18, 30), Bunker(86, 324, 14, 21) } },
                new Hole { Number = 2, Par = 4, Centerline = new[] { P(0, 0), P(0, 170), P(-18, 280) }, FairwayWidth = 46, GreenRadius = 20,
                    Hazards = new[] { Bunker(23, 172, 16, 22), Bunker(-38, 272, 12, 16) } },
                new Hole { Number = 3, Par = 3, Centerline = new[] { P(0, 0), P(8, 115) }, FairwayWidth = 50, GreenRadius = 20,
                    Hazards = new[] { Bunker(-12, 108, 14, 18) } },
            },
        };
    }
}
