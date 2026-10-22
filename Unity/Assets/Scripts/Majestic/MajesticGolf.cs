using System.Collections.Generic;
using GolfArcade.Course;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Golf dressing (concepts/after/golf_h12_clear.jpg, golf_h08_storm.jpg): hot-air balloons drifting
    /// beyond the hole and gulls circling over the fairway, placed from the tee along tee->pin. Sky-only
    /// pieces, so they never sit in terrain or water; rebuilt on every hole.
    public static class MajesticGolf
    {
        public static Hole Hole; public static Vector3 Forward = Vector3.forward, Tee, Pin;
        static readonly List<(Transform t, Vector3 home, float phase)> balloons = new(), gulls = new(), boats = new();
        static Transform whale; static Vector3 whaleHome; static float seaLevel;

        public static void Build(Transform root, MajesticLook look)
        {
            balloons.Clear(); gulls.Clear();
            if (Hole == null) return;
            var mat = MajesticMesh.Dressing();
            var rng = new System.Random(Hole.Number * 31 + 7);
            var right = Vector3.Cross(Vector3.up, Forward).normalized;
            Color[][] gores =
            {
                new[] { new Color(.95f, .25f, .22f), new Color(1f, .85f, .2f) },
                new[] { new Color(.2f, .55f, .95f), new Color(.98f, .97f, .94f) },
                new[] { new Color(.3f, .78f, .42f), new Color(1f, .55f, .15f), new Color(.95f, .4f, .7f) },
            };
            for (int i = 0; i < 3; i++)
            {
                var m = new MajesticMesh(); Balloon(m, gores[i]);
                var go = m.Build(root, "Majestic balloon", mat, false);
                var home = Tee + Forward * (260 + i * 85) + right * ((i - 1) * 140 + (float)rng.NextDouble() * 40) + Vector3.up * (68 + i * 22);
                go.transform.position = home; go.transform.localScale = Vector3.one * (1.6f + i * .25f);
                balloons.Add((go.transform, home, i * 2.1f));
            }
            // sea life only where the hole's sea is: the largest water surface, points inside its bounds
            boats.Clear(); whale = null;
            Renderer sea = null;
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                if (r.name == "Open sea" && r.enabled && r.gameObject.activeInHierarchy) { sea = r; break; }
            if (sea && sea.bounds.size.x > 300)
            {
                seaLevel = sea.transform.position.y + .1f;
                bool OnSea(Vector3 p) => p.x > sea.bounds.min.x + 20 && p.x < sea.bounds.max.x - 20 && p.z > sea.bounds.min.z + 20 && p.z < sea.bounds.max.z - 20;
                for (int i = 0; i < 3; i++)
                {
                    var p = Pin + Forward * (160 + i * 120) + right * ((i - 1) * 190 + (float)rng.NextDouble() * 50); p.y = seaLevel;
                    if (!OnSea(p)) continue;
                    var mb = new MajesticMesh(); MajesticSea.Sailboat(mb);
                    var go = mb.Build(root, "Majestic sailboat", mat, false); go.transform.position = p; go.transform.localScale = Vector3.one * 1.5f;
                    go.transform.rotation = Quaternion.Euler(0, (float)rng.NextDouble() * 360, 0);
                    boats.Add((go.transform, p, i * 1.7f));
                }
                var wp = Pin + Forward * 140 - right * 160; wp.y = seaLevel;
                if (OnSea(wp))
                {
                    var mb = new MajesticMesh(); MajesticSea.Whale(mb);
                    whale = mb.Build(root, "Majestic whale", mat, false).transform; whaleHome = wp; whale.localScale = Vector3.one * 1.6f;
                    whale.rotation = Quaternion.LookRotation(right);
                }
            }
            for (int i = 0; i < 6; i++)
            {
                var m = new MajesticMesh(); m.Gull((float)rng.NextDouble());
                var go = m.Build(root, "Majestic gull", mat, false); go.transform.localScale = Vector3.one * 1.3f;
                var home = Tee + Forward * (70 + i * 14) + right * ((float)rng.NextDouble() - .5f) * 50 + Vector3.up * (22 + i % 3 * 6);
                gulls.Add((go.transform, home, i * 1.1f));
            }
        }

        static void Balloon(MajesticMesh m, Color[] stripes)
        {
            const int seg = 16, rings = 8;
            Vector3 P(int k, int j)
            {
                float a = k * Mathf.PI * 2 / seg, v = j / (float)rings;              // v 0 top .. 1 bottom
                float y = Mathf.Lerp(7.5f, -2.5f, v);
                float r = v < .55f ? Mathf.Sin(Mathf.Lerp(.15f, 1.05f, v / .55f) * Mathf.PI * .5f) * 5.2f : Mathf.Lerp(5.1f, 1.1f, (v - .55f) / .45f);
                return new Vector3(Mathf.Cos(a) * r, y, Mathf.Sin(a) * r);
            }
            for (int j = 0; j < rings; j++)
                for (int k = 0; k < seg; k++)
                    m.Quad(P(k, j), P(k + 1, j), P(k + 1, j + 1), P(k, j + 1), stripes[k % stripes.Length]);
            for (int k = 0; k < seg; k++) m.Tri(P(k + 1, 0), P(k, 0), new Vector3(0, 7.9f, 0), stripes[0]);
            var basket = new Color(.55f, .38f, .22f);
            float b = .7f, y0 = -4.6f, y1 = -3.6f;
            m.Quad(new Vector3(-b, y0, -b), new Vector3(b, y0, -b), new Vector3(b, y1, -b), new Vector3(-b, y1, -b), basket);
            m.Quad(new Vector3(b, y0, b), new Vector3(-b, y0, b), new Vector3(-b, y1, b), new Vector3(b, y1, b), basket);
            m.Quad(new Vector3(-b, y0, b), new Vector3(-b, y0, -b), new Vector3(-b, y1, -b), new Vector3(-b, y1, b), basket * .85f);
            m.Quad(new Vector3(b, y0, -b), new Vector3(b, y0, b), new Vector3(b, y1, b), new Vector3(b, y1, -b), basket * .85f);
            var rope = new Color(.3f, .25f, .2f);
            foreach (var c in new[] { new Vector2(-b, -b), new Vector2(b, -b), new Vector2(b, b), new Vector2(-b, b) })
                m.Quad(new Vector3(c.x, y1, c.y), new Vector3(c.x + .05f, y1, c.y), new Vector3(c.x * 1.4f + .05f, -2.5f, c.y * 1.4f), new Vector3(c.x * 1.4f, -2.5f, c.y * 1.4f), rope);
        }

        public static void Animate(MajesticLook look, float t)
        {
            foreach (var (tr, home, phase) in boats)
                if (tr) { tr.position = home + new Vector3(0, Mathf.Sin(t * .8f + phase) * .15f, 0) + tr.forward * (t * .6f % 60); tr.rotation = Quaternion.Euler(Mathf.Sin(t * .6f + phase) * 2.5f, tr.eulerAngles.y, Mathf.Sin(t * .9f + phase) * 3); }
            if (whale)
            {
                // a breach every 14 s: rise out of the water on an arc, roll, splash back down
                float c = Mathf.Repeat(t, 14f) / 2.6f;
                bool up = c < 1; whale.gameObject.SetActive(up);
                if (up)
                {
                    float y = Mathf.Sin(c * Mathf.PI) * 9 - 4;
                    whale.position = whaleHome + new Vector3(0, y, 0) + whale.forward * (c * 10 - 5);
                    whale.rotation = Quaternion.LookRotation(whale.forward, Vector3.up) * Quaternion.Euler(Mathf.Lerp(-55, 55, c), 0, Mathf.Sin(c * Mathf.PI) * 25);
                }
            }
            foreach (var (tr, home, phase) in balloons)
            {
                if (!tr) continue;
                tr.position = home + new Vector3(Mathf.Sin(t * .05f + phase) * 12, Mathf.Sin(t * .23f + phase) * 2.5f, Mathf.Cos(t * .04f + phase) * 8);
                tr.rotation = Quaternion.Euler(0, t * 3 + phase * 40, Mathf.Sin(t * .3f + phase) * 2);
            }
            for (int i = 0; i < gulls.Count; i++)
            {
                var (tr, home, phase) = gulls[i]; if (!tr) continue;
                float a = t * (.17f + i * .012f) + phase, r = 16 + i * 3;
                var p = home + new Vector3(Mathf.Cos(a) * r, Mathf.Sin(t * .4f + i) * 1.5f, Mathf.Sin(a) * r * .6f);
                var dir = p - tr.position; if (dir.sqrMagnitude > 1e-6) tr.rotation = Quaternion.Slerp(tr.rotation, Quaternion.LookRotation(dir.normalized) * Quaternion.Euler(0, 0, -12), .1f);
                tr.position = p;
            }
        }
    }
}
