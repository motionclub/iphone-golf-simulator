using System;
using UnityEngine;
using GolfArcade.Course;
using GolfArcade.Shot;

namespace GolfArcade.Game
{
    /// The putt's power meter on the minimap: while a putt is lined up the map zooms onto the
    /// green (FrameMinimap) and shows where each quarter of the meter rolls the ball on the flat,
    /// in feet, the same way a full shot's map shows its 25/50/75/100 % landings. As the putter
    /// comes back a live dot slides out along the line to where the stroke would stop. The meter's
    /// own stops sit at the same four loads with the same feet, so the meter and the map agree.
    public sealed partial class GolfGame
    {
        static readonly float[] PuttPowers = { 0.25f, 0.5f, 0.75f, 1f };
        readonly double[] puttMarkFeet = new double[PuttPowers.Length];
        double puttLoad;

        /// Feet a putt with this much meter rolls on the flat here.
        double PuttFeet(double load) => GolfClub.Putter.DistanceYards(load) * 3 * hole.Rules.CarryFactor(GolfClub.Putter);

        /// Where a putt of `feet` along the aim stops on the flat.
        CoursePoint PuttSpot(double feet)
        {
            double yards = feet / 3, h = heading * Math.PI / 180;
            return new CoursePoint(ballAt.X + yards * Math.Sin(h), ballAt.D + yards * Math.Cos(h));
        }

        /// How far up the line the putt map reaches, in yards: out to the first mark past the hole
        /// and past the live reading (all four when they are beyond them), so the framing holds
        /// still while you aim and steps out a mark at a time as the backswing passes one.
        double PuttMapReach(double liveFeet = 0)
        {
            double past = Math.Max(ballAt.DistanceTo(hole.Pin) * 3, liveFeet), feet = puttMarkFeet[puttMarkFeet.Length - 1];
            foreach (var f in puttMarkFeet) if (f > past) { feet = f; break; }
            return feet / 3;
        }

        void LayPuttMarks()
        {
            var plan = hud.Map;
            plan.Putt = true;
            plan.Targets.Clear(); plan.TargetLabels.Clear();
            var labels = new string[PuttPowers.Length];
            for (int i = 0; i < PuttPowers.Length; i++)
            {
                puttMarkFeet[i] = PuttFeet(PuttPowers[i]);
                var spot = PuttSpot(puttMarkFeet[i]);
                plan.Targets.Add(new Vector3((float)spot.X, 0, (float)spot.D));
                labels[i] = $"{puttMarkFeet[i]:F0} ft";
                plan.TargetLabels.Add(labels[i]);
            }
            ShowPuttLoad(puttLoad);   // (laid again as the aim moves: a backswing under way keeps its reading)
            hud.SetCheckpoints(PuttPowers, labels);
        }

        /// The putter's backswing: the live dot on the map out to where this load rolls, with its feet.
        void ShowPuttLoad(double load)
        {
            puttLoad = load;
            var plan = hud.Map;
            if (!plan.Putt) return;
            double feet = PuttFeet(load);
            var spot = PuttSpot(feet);
            plan.Load = new Vector3((float)spot.X, 0, (float)spot.D);
            plan.ShowLoad = load > 0.01;
            plan.LoadLabel = $"{feet:F0} ft";
            // (back to the hole's own reach when the backswing is let go)
            float reach = (float)PuttMapReach(load > 0.01 ? feet : 0);
            if (!Mathf.Approximately(reach, plan.PuttReach)) { plan.PuttReach = reach; plan.Changed(); }
        }

        /// The putt is struck or the club changed: the marks and the live dot go. The map stays on
        /// the green while a struck putt rolls (FrameMinimap reads `Putt` with the club in hand).
        void HidePuttMarks(bool keepZoom = false)
        {
            puttLoad = 0;
            var plan = hud.Map;
            plan.TargetLabels.Clear(); plan.LoadLabel = null; plan.ShowLoad = false;
            if (!keepZoom) plan.Putt = false;
        }
    }
}
