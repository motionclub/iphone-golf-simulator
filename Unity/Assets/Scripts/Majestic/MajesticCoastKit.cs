using System.Collections.Generic;
using GolfArcade.Course;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Island edges from the landmark kit (brief rule: "island edges are never a bare bevel"; work/majestic-landmarks README):
    /// along MajesticShore's coastlines near the hole, a 20 m tile every 20 m: CliffSkirt where the land stands high
    /// above the sea, ShoreBand (Magma: BlackSandShore) where it is low, each with a FoamStrip at its foot. Tiles: pivot at
    /// the waterline, repeat along local X, land toward local -Z (Blender +Y), sea toward +Z. Visual only, no colliders.
    /// Also the hole set pieces that need the course's lie to find their spot (17 ice-fishing hut, 20 canal bridge).
    public static class MajesticCoastKit
    {
        const float TileM = 20f, Reach = 170f;   // budget: 260 yd put 180+ tiles in some views (r23); at 200 the median view was 0.806 M (r26)

        public static int Build(Transform root, Hole hole, MajesticCourses.Kind course, Vector3 tee, Vector3 pin, float seaY)
        {
            int n = 0;
            // 10-18 share-video review: on the real cliffs the CliffSkirt tiles stood as flat pale walls in front of the
            // course's own cliff faces and the foam strips read as white shards at the cliff foot (seen from the ball-follow
            // and flyover cameras, never from the 5 reference views). Off by default until rebuilt; MAJESTIC_COAST=1 opts in.
            if (System.Environment.GetEnvironmentVariable("MAJESTIC_COAST") != "1") return SetPieces(root, hole, tee, pin, seaY);
            float tile = TileM * MajesticKit.YardsPerMeter;
            foreach (var line in MajesticShore.LastLines)
            {
                if (line.Count < 8) continue;
                float carry = tile * .5f;
                for (int i = 1; i < line.Count; i++)
                {
                    float seg = Vector3.Distance(line[i - 1], line[i]); carry += seg;
                    if (carry < tile) continue;
                    carry -= tile;
                    var p = line[i];
                    if (DistToSegment(p, tee, pin) > Reach) continue;
                    var prev = line[Mathf.Max(0, i - 3)]; var next = line[Mathf.Min(line.Count - 1, i + 3)];
                    var t = next - prev; t.y = 0; if (t.sqrMagnitude < .01f) continue; t.Normalize();
                    var sea = new Vector3(t.z, 0, -t.x);
                    if (Land(p + sea * 5, seaY)) sea = -sea;
                    float inland = MajesticKit.Ground(p - sea * 6, seaY, out bool land);
                    if (!land) continue;
                    float height = inland - seaY;
                    bool cliff = height > 4.5f && course != MajesticCourses.Kind.Magma;
                    string name = cliff ? "CliffSkirt" : course == MajesticCourses.Kind.Magma ? "BlackSandShore" : "ShoreBand";
                    var rot = Quaternion.LookRotation(sea);
                    var go = MajesticKit.Spawn(name, root, new Vector3(p.x, seaY, p.z), rot, 1f, false);
                    MajesticKit.KeepLod(go, 1);   // r23 budget: the big tiles kept LOD0 (CliffSkirt 4.5 k tris) at every distance
                    if (go && cliff)
                    {
                        // the kit's turf lip is 5.5 m (6 yd) above the sea: stretch to this coast's height
                        float k = Mathf.Clamp(height / (5.5f * MajesticKit.YardsPerMeter), .7f, 2.5f);
                        var ls = go.transform.localScale; go.transform.localScale = new Vector3(ls.x, ls.y * k, ls.z);
                    }
                    MajesticKit.Spawn("FoamStrip", root, new Vector3(p.x, seaY + .03f, p.z) + sea * 1.3f, rot, 1f, false);
                    n++;
                }
            }
            n += SetPieces(root, hole, tee, pin, seaY);
            return n;
        }

        static int SetPieces(Transform root, Hole hole, Vector3 tee, Vector3 pin, float seaY)
        {
            var fwd = pin - tee; fwd.y = 0; float len = fwd.magnitude; fwd /= Mathf.Max(1, len);
            var right = Vector3.Cross(Vector3.up, fwd);
            if (hole.Number == 17)
            {
                // the ice-fishing hut out on the frozen lake (brief: off-line views)
                foreach (var f in new[] { .45f, .35f, .55f, .25f, .65f })
                    foreach (var side in new[] { -1f, 1f })
                        for (float r = 25; r <= 90; r += 8)
                        {
                            var p = tee + fwd * (len * f) + right * (side * r);
                            if (hole.LieAt(HoleView.ToCourse(p)) != CourseLie.Ice) continue;
                            float y = (float)HoleView.GroundHeight(HoleView.ToCourse(p));
                            GolfSolidProps.FromKit(MajesticKit.Spawn("IceFishingHut", root, new Vector3(p.x, y, p.z), Quaternion.LookRotation(-right * side), 1.2f, true), hole);
                            return 1;
                        }
            }
            if (hole.Number == 20)
            {
                // a little brick bridge across a canal beside the line (brief: canals with small brick bridges)
                int placed = 0;
                foreach (var f in new[] { .2f, .55f, .8f })
                    foreach (var side in new[] { 1f, -1f })
                        for (float r = 22; r <= 70 && placed < 2; r += 4)
                        {
                            var p = tee + fwd * (len * f) + right * (side * r);
                            if (hole.LieAt(HoleView.ToCourse(p)) != CourseLie.Water) continue;
                            // the canal runs where the water reaches furthest; the bridge spans across it
                            Vector3 best = fwd; float bestRun = 0;
                            for (int a = 0; a < 8; a++)
                            {
                                var d = Quaternion.Euler(0, a * 22.5f, 0) * Vector3.forward; float run = 0;
                                for (float s = 2; s <= 30; s += 2) { if (hole.LieAt(HoleView.ToCourse(p + d * s)) != CourseLie.Water || hole.LieAt(HoleView.ToCourse(p - d * s)) != CourseLie.Water) break; run = s; }
                                if (run > bestRun) { bestRun = run; best = d; }
                            }
                            var across = Vector3.Cross(Vector3.up, best);
                            float y = MajesticKit.Ground(p + across * 6, seaY, out _);
                            GolfSolidProps.FromKit(MajesticKit.Spawn("CanalBridge", root, new Vector3(p.x, Mathf.Max(seaY, y - .3f), p.z), Quaternion.LookRotation(best), 1f, true), hole);
                            placed++; break;
                        }
                return placed;
            }
            return 0;
        }

        static bool Land(Vector3 p, float seaY) { MajesticKit.Ground(p, seaY, out bool land); return land; }

        static float DistToSegment(Vector3 p, Vector3 a, Vector3 b)
        {
            p.y = a.y = b.y = 0; var ab = b - a; float t = Mathf.Clamp01(Vector3.Dot(p - a, ab) / Mathf.Max(.01f, ab.sqrMagnitude));
            return Vector3.Distance(p, a + ab * t);
        }
    }
}
