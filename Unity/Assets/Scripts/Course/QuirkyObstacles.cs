using System;
using System.Collections.Generic;

namespace GolfArcade.Course
{
    /// The quirky things set out on a few holes (Adnan 10-19: "more random stuff"): a timed launchpad beside the
    /// drive's landing zone, and a bullseye sliding along a gantry over the rough. Both stand off the line of play:
    /// going for one is a choice, never a toll: a launchpad on Cliffside's opener (7) and a bullseye on Windmill Links
    /// (20). Placed from the hole's own lie map, so a pad never lies in water or sand and a gantry's posts
    /// stand on land. Every phone gets the same ones from the round's seed.
    public static class QuirkyObstacles
    {
        readonly struct Spot
        {
            public readonly int Hole; public readonly MoverKind Kind; public readonly double Along, Side, Offset;
            public Spot(int hole, MoverKind kind, double along, double side, double offset) { Hole = hole; Kind = kind; Along = along; Side = side; Offset = offset; }
        }

        static readonly Spot[] Spots =
        {
            new(7, MoverKind.Launchpad, .50, 1, 14),
            // (the Crater, hole 10, had a pad in the first pass: its test lob came down among the crater's rocks and ran
            // into the lava, so it is out until a spot is picked by hand; work/course-fx/GATE_RESULTS.md)
            new(20, MoverKind.Target, .30, 1, 10),
        };

        /// A target's rail runs this far out across the hole, starting `Offset` yards off the line.
        public const double RailLength = 16;
        /// Nothing comes nearer the line of play than this (yards), so the straight shot is always open.
        public const double Clear = 9.5;
        public const double PadPeriod = 4.2, TargetPeriod = 6.5;

        public static bool Has(int holeNumber) => Array.Exists(Spots, s => s.Hole == holeNumber);

        /// The quirky movers on `hole` today (none on most holes).
        public static Mover[] For(Hole hole, int seed, Func<CoursePoint, double> ground, DreamCourseLayout dream)
        {
            var list = new List<Mover>();
            if (hole?.Centerline == null || hole.Centerline.Length < 2) return list.ToArray();
            ground ??= hole.Ground ?? (_ => 0.0);
            foreach (var spot in Spots)
            {
                if (spot.Hole != hole.Number) continue;
                double phase = RoundEvents.Mix(seed, hole.Number, 0x51A7 + (int)spot.Kind) % 1000 / 1000.0;
                var mover = spot.Kind == MoverKind.Launchpad ? Pad(hole, spot, phase, ground, dream) : Gantry(hole, spot, phase, ground, dream);
                if (mover != null) list.Add(mover);
            }
            return list.ToArray();
        }

        /// The spots tried round the authored one: a little up and down the hole, then the other side.
        static IEnumerable<(CoursePoint at, double heading, double side)> Around(Hole hole, Spot spot)
        {
            foreach (double side in new[] { spot.Side, -spot.Side })
                foreach (double shift in new[] { 0, .04, -.04, .08, -.08, .12 })
                {
                    double f = Math.Max(.15, Math.Min(.85, spot.Along + shift));
                    var at = DreamCourseLayout.Along(hole, f); var next = DreamCourseLayout.Along(hole, f + .02);
                    yield return (at, at.HeadingTo(next) * Math.PI / 180, side);
                }
        }

        static CoursePoint Off(CoursePoint at, double heading, double side, double offset) =>
            new(at.X + Math.Cos(heading) * side * offset, at.D - Math.Sin(heading) * side * offset);

        static bool Dry(Hole hole, CoursePoint p) =>
            hole.LieAt(p) is not (CourseLie.Water or CourseLie.OutOfBounds or CourseLie.Bunker or CourseLie.Green or CourseLie.Fringe or CourseLie.Tee or CourseLie.Ice);

        static bool AwayFrom(Hole hole, CoursePoint p, DreamCourseLayout dream)
        {
            if (p.DistanceTo(hole.Tee) < 60 || p.DistanceTo(hole.Pin) < 45) return false;
            if (DreamCourseLayout.CorridorDistance(p, hole.Centerline) < Clear) return false;
            if (dream != null) foreach (var h in dream.Hazards) if (h.Centre.DistanceTo(p) < 32) return false;
            return true;
        }

        /// Where a lob from (`from`, height `fromY`) launched `up` yards a second should finish: on the fairway short of
        /// the green, with clear running room ahead toward the pin (no water, sand or out of bounds in the next 30 yards,
        /// nothing standing within 6 yards of it), and a flight there that meets nothing standing on the course (the
        /// Crater's rocks threw the first test lob into the lava), so a good launch leaves a chip, not trouble. The
        /// front of the green when the fairway has no such spot.
        static CoursePoint Goal(Hole hole, CoursePoint from, double fromY, double up, Func<CoursePoint, double> ground)
        {
            for (double f = .88; f >= .62; f -= .02)
            {
                var p = DreamCourseLayout.Along(hole, f);
                if (hole.LieAt(p) != CourseLie.Fairway || Crowded(hole, p, 10)) continue;
                double length = p.DistanceTo(hole.Pin); if (length < 25) continue;
                double ux = (hole.Pin.X - p.X) / length, ud = (hole.Pin.D - p.D) / length;
                bool open = true;
                for (double s = 3; s <= 30 && open; s += 3)
                {
                    var q = new CoursePoint(p.X + ux * s, p.D + ud * s);
                    open = hole.LieAt(q) is not (CourseLie.Water or CourseLie.OutOfBounds or CourseLie.Bunker) && !Crowded(hole, q, 6);
                }
                if (open && ClearFlight(hole, from, fromY, p, ground(p), up, ground)) return p;
            }
            var front = DreamCourseLayout.Along(hole, .93);
            return hole.LieAt(front).PenaltyStrokes() == 0 ? front : hole.Pin;
        }

        /// The lob (CourseMovers.Lob, flown as CourseShot's fall flies it) comes down on dry ground without touching
        /// anything standing on the course, and runs out clear, at the three strays its luck can give it.
        static bool ClearFlight(Hole hole, CoursePoint from, double fromY, CoursePoint goal, double goalY, double up, Func<CoursePoint, double> ground)
        {
            // only what stands near the line from the pad to the goal can be met
            var near = new List<Obstacle>();
            if (hole.Obstacles != null)
                foreach (var o in hole.Obstacles)
                    if (DreamCourseLayout.CorridorDistance(new CoursePoint(o.X, o.D), new[] { from, goal }) < o.Footprint + 6) near.Add(o);
            foreach (double luck in new[] { 0.0, 0.5, 1.0 })
            {
                var (vx, vy, vd) = CourseMovers.Lob(from.X, fromY, from.D, goal, goalY, up, luck);
                double x = from.X, y = fromY, d = from.D; const double dt = 1.0 / 60;
                for (int step = 0; step < 60 * 12; step++)
                {
                    vy -= CourseShot.GravityYards * dt; vx *= 1 - 0.25 * dt; vd *= 1 - 0.25 * dt;
                    x += vx * dt; y += vy * dt; d += vd * dt;
                    foreach (var o in near) if (o.Touches(x, y, d, CourseShot.BallRadius, out _, out _)) return false;
                    if (step > 30 && y <= ground(new CoursePoint(x, d))) break;
                }
                if (hole.LieAt(new CoursePoint(x, d)).PenaltyStrokes() > 0) return false;
                // it lands short of the goal by its run and runs on along the lob's line, past the goal a little: all of
                // that on clear, dry ground (hole 10's first lob bounced off a crater rock into the lava)
                double rx = goal.X - x, rd = goal.D - d, run = Math.Sqrt(rx * rx + rd * rd);
                if (run > 0.5)
                    for (double s = 0; s <= run + 10; s += 2)
                    {
                        var q = new CoursePoint(x + rx / run * s, d + rd / run * s);
                        if (hole.LieAt(q) is CourseLie.Water or CourseLie.OutOfBounds or CourseLie.Bunker || Crowded(hole, q, 3)) return false;
                    }
            }
            return true;
        }

        /// Something standing on the course (a rock, a tree, a wall) within `clear` yards of `p`.
        static bool Crowded(Hole hole, CoursePoint p, double clear)
        {
            if (hole.Obstacles == null) return false;
            foreach (var o in hole.Obstacles) { double dx = o.X - p.X, dd = o.D - p.D, r = o.Footprint + clear; if (dx * dx + dd * dd < r * r) return true; }
            return false;
        }

        static Mover Pad(Hole hole, Spot spot, double phase, Func<CoursePoint, double> ground, DreamCourseLayout dream)
        {
            foreach (var (at, heading, side) in Around(hole, spot))
            {
                var p = Off(at, heading, side, spot.Offset);
                if (!AwayFrom(hole, p, dream) || !Dry(hole, p)) continue;
                bool dry = true;
                for (int i = 0; i < 8 && dry; i++)
                {
                    double a = i * Math.PI / 4;
                    var rim = new CoursePoint(p.X + Math.Cos(a) * Mover.PadRadius, p.D + Math.Sin(a) * Mover.PadRadius);
                    dry = Dry(hole, rim) && DreamCourseLayout.CorridorDistance(rim, hole.Centerline) > Clear - Mover.PadRadius - .5;
                }
                if (!dry) continue;
                var goal = Goal(hole, p, ground(p) + Mover.PadRise, Mover.PadLaunchUp, ground);
                return Mover.Launchpad(p, ground(p), goal, ground(goal), PadPeriod, phase);
            }
            return null;
        }

        static Mover Gantry(Hole hole, Spot spot, double phase, Func<CoursePoint, double> ground, DreamCourseLayout dream)
        {
            foreach (var (at, heading, side) in Around(hole, spot))
            {
                var from = Off(at, heading, side, spot.Offset);
                var to = Off(at, heading, side, spot.Offset + RailLength);
                var postA = Off(at, heading, side, spot.Offset - Mover.TargetPost);
                var postB = Off(at, heading, side, spot.Offset + RailLength + Mover.TargetPost);
                if (!AwayFrom(hole, from, dream) || !AwayFrom(hole, to, dream)) continue;
                if (hole.LieAt(postA) is CourseLie.Water or CourseLie.OutOfBounds || hole.LieAt(postB) is CourseLie.Water or CourseLie.OutOfBounds) continue;
                bool clear = true;
                for (int i = 0; i <= 8 && clear; i++)
                {
                    var q = new CoursePoint(from.X + (to.X - from.X) * i / 8, from.D + (to.D - from.D) * i / 8);
                    clear = DreamCourseLayout.CorridorDistance(q, hole.Centerline) >= Clear;
                }
                if (!clear) continue;
                // hung at the height an ordinary tee shot passes there (as the dream gates are sized), so a drive aimed
                // a little right of the line can find it
                var mid = Off(at, heading, side, spot.Offset + RailLength / 2);
                double groundMid = ground(mid), above = 14;
                double aim = hole.Tee.HeadingTo(mid) * Math.PI / 180;
                var beyond = new CoursePoint(mid.X + Math.Sin(aim) * 70, mid.D + Math.Cos(aim) * 70);
                var plan = CourseRings.StraightShot(hole.Tee, beyond, PlayRules.Standard);
                if (plan.HasValue)
                {
                    var flight = plan.Value.flight; double reach = hole.Tee.DistanceTo(mid);
                    for (double t = 0; t <= flight.CarryTime; t += .02)
                        if (flight.PositionAt(t).DistanceYards >= reach)
                        {
                            double g0 = ground(hole.Tee), g1 = ground(beyond);
                            double y = g0 + (g1 - g0) * t / Math.Max(.01, flight.CarryTime) + flight.PositionAt(t).HeightYards;
                            above = y - groundMid;
                            break;
                        }
                }
                above = Math.Max(6, Math.Min(24, above));
                var goal = Goal(hole, mid, groundMid + above, Mover.TargetLaunchUp, ground);
                return Mover.Target(from, to, groundMid + above, TargetPeriod, phase, goal, ground(goal));
            }
            return null;
        }
    }
}
