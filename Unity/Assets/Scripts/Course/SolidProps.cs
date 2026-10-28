using System;
using System.Collections.Generic;

namespace GolfArcade.Course
{
    /// The solid things dressed onto a hole that are neither ground nor plants: a bench of tulips,
    /// a fence, a bridge, a jetty, a farmhouse, a gazebo (Adnan 10-28: "obstacles in the background
    /// [can't be] transparent ... that can only happen with leaves and grass"). The ball meets them
    /// as they are drawn: the game hands in a sweep against their real shapes (GolfSolidProps), and
    /// keeps a box round each here so a shot only asks about the ones it passes. Course yards, world
    /// heights.
    public sealed class SolidProps
    {
        /// From a to b, a ball of radius r: where along it (0–1) it first touches one, and the
        /// face's outward normal there.
        public delegate bool Sweeper(double ax, double ay, double ad, double bx, double by, double bd, double r,
            out double along, out double nx, out double ny, out double nd);

        readonly Sweeper sweep;
        readonly List<(double minX, double minY, double minD, double maxX, double maxY, double maxD)> boxes = new();

        public SolidProps(Sweeper sweep) { this.sweep = sweep; }

        public int Count => boxes.Count;

        public void Add(double minX, double minY, double minD, double maxX, double maxY, double maxD) =>
            boxes.Add((minX, minY, minD, maxX, maxY, maxD));

        /// Is (x, d) within `reach` of any of them, seen from above?
        public bool NearOver(double x, double d, double reach)
        {
            foreach (var b in boxes)
                if (x > b.minX - reach && x < b.maxX + reach && d > b.minD - reach && d < b.maxD + reach) return true;
            return false;
        }

        public bool Sweep(double ax, double ay, double ad, double bx, double by, double bd, double r,
            out double along, out double nx, out double ny, out double nd)
        {
            along = 1; nx = ny = nd = 0;
            if (sweep == null) return false;
            double loX = Math.Min(ax, bx) - r, hiX = Math.Max(ax, bx) + r;
            double loY = Math.Min(ay, by) - r, hiY = Math.Max(ay, by) + r;
            double loD = Math.Min(ad, bd) - r, hiD = Math.Max(ad, bd) + r;
            bool any = false;
            foreach (var b in boxes)
                if (hiX > b.minX && loX < b.maxX && hiY > b.minY && loY < b.maxY && hiD > b.minD && loD < b.maxD) { any = true; break; }
            return any && sweep(ax, ay, ad, bx, by, bd, r, out along, out nx, out ny, out nd);
        }

        /// A ball meeting one: back off the face with some bounce (painted wood and stone give a
        /// little less than a rock does), the run along the face kept.
        public static (double vx, double vy, double vd) Rebound(double vx, double vy, double vd, double nx, double ny, double nd, double kick = 1)
        {
            double vn = vx * nx + vy * ny + vd * nd;
            if (vn >= 0) return (vx, vy, vd);
            double e = 0.5, slide = 0.86;
            if (kick != 1) { e = Math.Min(1.15, e * kick); slide = Math.Min(0.95, slide + 0.1 * (kick - 1)); }
            double tx = vx - vn * nx, ty = vy - vn * ny, td = vd - vn * nd;
            return (slide * tx - e * vn * nx, slide * ty - e * vn * ny, slide * td - e * vn * nd);
        }
    }
}
