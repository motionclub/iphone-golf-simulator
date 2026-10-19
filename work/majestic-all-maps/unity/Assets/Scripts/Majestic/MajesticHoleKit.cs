using System.Collections.Generic;
using GolfArcade.Course;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Where each hole's landmarks and set pieces stand (work/majestic-all-maps/design/HOLE_BRIEFS.md: one subject per
    /// direction). Positions are in the hole's own frame: from the tee (T) or the pin (P), `f` yards along the line tee->pin,
    /// `r` yards to its right. Pieces face the tee. Anything that would land within the play corridor is pushed out of it,
    /// so nothing stands in a shot. Visual only: no colliders.
    public static class MajesticHoleKit
    {
        struct Piece
        {
            public string name; public bool fromPin; public float f, r, scale, yaw; public bool shadows, sea;
            public Piece(string n, bool pin, float f, float r, float s, bool shadows = true, float yaw = 0, bool sea = false)
            { name = n; fromPin = pin; this.f = f; this.r = r; scale = s; this.shadows = shadows; this.yaw = yaw; this.sea = sea; }
        }
        const bool T = false, P = true;

        static readonly Dictionary<int, Piece[]> Holes = new()
        {
            // Cliffside: the lighthouse from every tee
            [7] = new[] { new Piece("Lighthouse", P, 120, 80, 2.2f, false) },
            [8] = new[] { new Piece("Lighthouse", P, 190, 240, 2.4f, false), new Piece("StoneGazebo", T, -16, -8, 1.1f) },
            [9] = new[] { new Piece("Lighthouse", P, 170, 210, 2.4f, false) },
            [12] = new[] { new Piece("Lighthouse", P, 30, 26, 1.1f) },
            [15] = new[] { new Piece("Lighthouse", P, 90, 250, 2.4f, false), new Piece("StoneGazebo", P, 18, -14, 1f),
                           new Piece("Balustrade", T, -2, 7, 1.1f, true, 90), new Piece("Balustrade", T, -2, -7, 1.1f, true, -90),
                           new Piece("Planter", T, -5, 7, 1.1f), new Piece("Planter", T, -5, -7, 1.1f) },
            // Wild Isles: the twin falls far away from every hole, a set piece per isle
            [13] = new[] { new Piece("LookoutTower", P, 12, 8, 1.3f), new Piece("Waterwheel", T, 90, -38, 1.3f), new Piece("TwinFallsIsle", T, 720, -360, 2.2f, false, 0, true) },
            [14] = new[] { new Piece("WitchCottage", P, 20, 16, 1.2f), new Piece("TwinFallsIsle", T, 680, 320, 2.2f, false, 0, true) },
            [17] = new[] { new Piece("AlpineChalet", P, 26, -28, 1.3f), new Piece("TwinFallsIsle", T, 700, -300, 2.2f, false, 0, true) },
            [18] = new[] { new Piece("MesaArch", P, 24, 22, 1.6f), new Piece("WaterTower", T, -10, -16, 1.2f), new Piece("TwinFallsIsle", T, 650, 280, 2.2f, false, 0, true) },
            [19] = new[] { new Piece("StepTemple", P, 32, 0, 1.5f), new Piece("TwinFallsIsle", P, 230, 0, 2.4f, false, 0, true), new Piece("StoneGate", T, -7, 0, 1.2f),
                           new Piece("StiltHut", T, 70, -75, 1.2f, true, 0, true), new Piece("StiltHut", T, 90, 80, 1.2f, true, 0, true) },
            [20] = new[] { new Piece("Windmill", P, 14, 24, 1.4f), new Piece("Windmill", P, -130, -75, .8f), new Piece("Farmhouse", T, -12, -24, 1.2f),
                           new Piece("TwinFallsIsle", T, 700, 320, 2.2f, false, 0, true) },
            // Magma Open: the caldera volcano on every horizon (21-23: r21 coverage, 2.1x at 950 yd so the peak clears the caldera rim)
            [10] = new[] { new Piece("CalderaVolcano", T, 1150, 0, 1.5f, false, 0, true), new Piece("ToriiGate", T, -9, 0, 1.2f),
                           new Piece("StoneLantern", T, -6, 5, 1.2f), new Piece("StoneLantern", T, -6, -5, 1.2f) },
            [16] = new[] { new Piece("CalderaVolcano", P, 280, 0, 1.6f, false, 0, true), new Piece("RangerHut", T, -9, -13, 1.2f),
                           new Piece("StoneLantern", T, -4, 5, 1.2f), new Piece("StoneLantern", T, -4, -5, 1.2f) },
            [21] = new[] { new Piece("CalderaVolcano", P, 950, 0, 2.1f, false, 0, true) },
            [22] = new[] { new Piece("CalderaVolcano", P, 950, 150, 2.1f, false, 0, true), new Piece("ObsidianArch", T, 10, -14, 1.2f), new Piece("BasaltSpire", P, 22, 16, 1.3f) },
            [23] = new[] { new Piece("CalderaVolcano", P, 950, -100, 2.1f, false, 0, true), new Piece("BasaltSpire", T, 140, -70, 1.4f) },
        };

        public static void Build(Transform root, Hole hole, Vector3 tee, Vector3 pin, Vector3 fwd, float seaY)
        {
            if (!Holes.TryGetValue(hole.Number, out var pieces)) return;
            var right = Vector3.Cross(Vector3.up, fwd).normalized;
            foreach (var p in pieces)
            {
                var at = (p.fromPin ? pin : tee) + fwd * p.f + right * p.r;
                at = OutOfCorridor(hole, at, p.r >= 0 ? right : -right);
                float y = MajesticKit.Ground(at, seaY, out bool land);
                if (!land && !p.sea)
                {
                    at = Inland(at, p.fromPin ? pin : tee, seaY, out y);
                    // cover r18: on the lava holes the walk back to land ended ON the tee (h23 spire beside the golfer)
                    if (Flat(at - tee) < 30 || Flat(at - pin) < 22) continue;
                }
                at.y = land || !p.sea ? y : seaY;
                var toTee = tee - at; toTee.y = 0;
                var rot = Quaternion.LookRotation(toTee.sqrMagnitude > 1 ? toTee.normalized : -fwd) * Quaternion.Euler(0, p.yaw, 0);
                var go = MajesticKit.Spawn(p.name, root, at, rot, p.scale, p.shadows);
                if (p.name == "CalderaVolcano")
                {
                    MajesticKit.TintFX(go, "Plume", new Color(.40f, .33f, .36f, .85f));   // ash, not steam
                    MajesticKit.Darken(go, .3f, new Color(.95f, .85f, .95f));            // r21: the grey cone read pale against the dusk; lava and crater keep their glow
                }
                if (p.name is "BasaltSpire" or "ObsidianArch") { MajesticKit.KeepLod(go, 1); MajesticKit.Darken(go, .2f, new Color(.95f, .85f, .95f)); }   // the kit grey reads pale lilac in the dusk
            }
            if (hole.Number is 21 or 22 or 23) Caldera(root, seaY);
        }

        static float Flat(Vector3 v) { v.y = 0; return v.magnitude; }

        /// Pushed sideways until it is clear of the fairway and the green (corridor = half the fairway + 14 yd).
        static Vector3 OutOfCorridor(Hole hole, Vector3 at, Vector3 away)
        {
            float clear = (float)hole.FairwayWidth * .5f + 14;
            for (int i = 0; i < 12; i++)
            {
                var c = HoleView.ToCourse(at);
                if (DreamCourseLayout.CorridorDistance(c, hole.Centerline) >= clear && c.DistanceTo(hole.Pin) >= 22) return at;
                at += away * 6;
            }
            return at;
        }

        /// A piece meant for land that came out over the sea walks back toward its anchor until it stands on ground.
        static Vector3 Inland(Vector3 at, Vector3 anchor, float seaY, out float y)
        {
            for (int i = 1; i <= 20; i++)
            {
                var q = Vector3.Lerp(at, anchor, i / 20f);
                y = MajesticKit.Ground(q, seaY, out bool land);
                if (land) return q;
            }
            y = seaY; return at;
        }

        /// Holes 21-23: the caldera wall ring round the lava lake (kit: 24 segments of 15 deg at radius 200 m),
        /// scaled so the ring stands just outside the lake's visible edge and alternating the lava-fall and plain walls.
        static void Caldera(Transform root, float seaY)
        {
            Renderer lake = null; float size = 0;
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                var n = r.name.ToLowerInvariant();
                if (!n.Contains("lava") || !r.enabled || !r.gameObject.activeInHierarchy) continue;
                float s = Mathf.Max(r.bounds.size.x, r.bounds.size.z);
                if (s > size) { size = s; lake = r; }
            }
            if (!lake || size < 150) return;
            var centre = lake.bounds.center; centre.y = lake.bounds.max.y - .5f;
            float radius = size * .5f * 1.02f;
            float scale = radius / (200f * MajesticKit.YardsPerMeter);
            Debug.Log($"[MajesticHoleKit] caldera ring: lake '{lake.name}' {size:F0} yd, radius {radius:F0} yd, wall scale {scale:F2}");
            for (int k = 0; k < 24; k++)
            {
                float a = k * 15f;
                var dir = Quaternion.Euler(0, a, 0) * Vector3.forward;
                var at = centre + dir * radius;
                // the wall's front (+Z) faces the lake centre
                var rot = Quaternion.LookRotation(-dir);
                var wall = MajesticKit.Spawn(k % 2 == 0 ? "CalderaWall_A" : "CalderaWall_B", root, at, rot, scale, false);   // round 6: a lava fall every other wall (targets)
                MajesticKit.KeepLod(wall, 1);
                MajesticKit.TintFX(wall, "LavaFall", new Color(1f, .42f, .10f, 1));   // orange, not bloom-white
                MajesticKit.Darken(wall, .22f, new Color(1f, .85f, .9f));             // dark basalt (r13-r19 this call sat behind a comment)
                if (wall) { var ls = wall.transform.localScale; wall.transform.localScale = new Vector3(ls.x, ls.y * .6f, ls.z); }   // round 6: the kit wall at ring scale already rises ~13 deg from the green; x1.9 (round 2) filled the sky with wall, the targets show cliffs ~5-8 deg high
            }
        }
    }
}
