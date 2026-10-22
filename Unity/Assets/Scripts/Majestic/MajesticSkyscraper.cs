using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Skyscraper dressing toward concepts/after/tennis_skyscraper_clear.jpg (blue hour): a smiling blimp
    /// towing a banner, two sweeping searchlights, warm string lights and bunting down both sides, two flag
    /// poles at the far corners, and a cheering terrace crowd on a bench along the right edge of the deck
    /// (deck tower is ±15.5 m in X, ±21 m in Z).
    public static class MajesticSkyscraper
    {
        static Transform blimp; static readonly List<Transform> beams = new();
        static readonly List<(Material m, string prop, object value)> saved = new();
        static readonly HashSet<Material> styled = new();

        public static void Build(Transform root, MajesticLook look)
        {
            beams.Clear();
            var mat = MajesticMesh.Dressing();
            var rng = new System.Random(101);
            var warm = new Color(1f, .78f, .45f);

            // ---- string lights + bunting along both sides and across the far end ----
            var deco = new MajesticMesh();
            for (int i = 0; i < 4; i++)
            {
                float z0 = -12 + i * 8, z1 = z0 + 8;
                deco.StringLights(new Vector3(-12.6f, 3.0f, z0), new Vector3(-12.6f, 3.0f, z1), .35f, warm);
                deco.StringLights(new Vector3(12.8f, 3.0f, z0), new Vector3(12.8f, 3.0f, z1), .35f, warm);
                deco.Bunting(new Vector3(-12.4f, 3.6f, z0), new Vector3(-12.4f, 3.6f, z1), .45f, rng);
            }
            deco.Bunting(new Vector3(12.6f, 3.6f, 4), new Vector3(12.6f, 3.6f, 20), .8f, rng);
            // posts for the strings (thin dark poles)
            foreach (float x in new[] { -12.6f, 12.8f })
                for (int i = 0; i <= 4; i++)
                {
                    var f = new Vector3(x, 0, -12 + i * 8);
                    deco.Quad(f + new Vector3(-.05f, 0, 0), f + new Vector3(.05f, 0, 0), f + new Vector3(.05f, 3.7f, 0), f + new Vector3(-.05f, 3.7f, 0), new Color(.10f, .10f, .12f));
                    deco.Quad(f + new Vector3(0, 0, -.05f), f + new Vector3(0, 0, .05f), f + new Vector3(0, 3.7f, .05f), f + new Vector3(0, 3.7f, -.05f), new Color(.10f, .10f, .12f));
                }
            // flags at the far corners
            deco.Flag(new Vector3(-10.5f, 0, 20.5f), 9.5f, new Vector2(2.2f, 1.2f), new[] { new Color(.95f, .22f, .20f) }, .2f);
            deco.Flag(new Vector3(10.5f, 0, 20.5f), 7.5f, new Vector2(1.3f, 2.6f), new[] { new Color(.20f, .40f, .90f), new Color(1f, .80f, .15f), new Color(.92f, .22f, .22f) }, .7f);
            // terrace bench for the crowd on the right edge
            var stone = new Color(.42f, .40f, .44f);
            Box(deco, new Vector3(14.1f, .3f, 10.5f), new Vector3(1.6f, .6f, 15f), stone);
            deco.Build(root, "Majestic terrace dressing", mat, true);

            var seats = new List<(Vector3, float)>();
            for (int i = 0; i < 12; i++) seats.Add((new Vector3(14.0f + (i % 2) * .45f, .63f, 5.0f + i * .95f), -90f));
            MajesticCrowd.Build(root, seats);

            // ---- blimp ----
            var b = new MajesticMesh();
            b.Blob(Vector3.zero, new Vector3(9, 3.6f, 3.6f), new Color(.97f, .97f, .98f), new Color(.30f, .52f, .95f), 16);
            foreach (var (dy, dz) in new[] { (1f, 0f), (-1f, 0f), (0f, 1f), (0f, -1f) })
                b.Tri(new Vector3(-6.5f, 0, 0), new Vector3(-9.6f, dy * 3.2f, dz * 3.2f), new Vector3(-9.8f, 0, 0), new Color(.25f, .45f, .92f));
            b.Blob(new Vector3(0, -3.7f, 0), new Vector3(1.6f, .6f, .7f), new Color(.85f, .85f, .9f), new Color(.3f, .3f, .35f), 8);
            // friendly face on the nose (facing the court, -Z side)
            b.Blob(new Vector3(6.6f, .9f, -2.9f), new Vector3(.32f, .5f, .2f), new Color(.08f, .08f, .1f), new Color(.08f, .08f, .1f), 6);
            b.Blob(new Vector3(7.6f, .9f, -2.2f), new Vector3(.32f, .5f, .2f), new Color(.08f, .08f, .1f), new Color(.08f, .08f, .1f), 6);
            for (int i = 0; i < 6; i++)
            {
                float a0 = Mathf.Lerp(-.9f, .9f, i / 6f), a1 = Mathf.Lerp(-.9f, .9f, (i + 1) / 6f);
                Vector3 m0 = new Vector3(7.1f + Mathf.Sin(a0) * .9f, -.3f - Mathf.Cos(a0) * .5f, -2.75f), m1 = new Vector3(7.1f + Mathf.Sin(a1) * .9f, -.3f - Mathf.Cos(a1) * .5f, -2.75f);
                b.Quad(m0, m1, m1 + Vector3.up * .14f, m0 + Vector3.up * .14f, new Color(.08f, .08f, .1f));
            }
            b.Glow = 5; b.Blob(new Vector3(-9.6f, 0, 0), Vector3.one * .3f, new Color(1f, .2f, .2f), new Color(1f, .2f, .2f), 6);
            b.Blob(new Vector3(0, -4.4f, 0), Vector3.one * .25f, new Color(.4f, 1f, .5f), new Color(.4f, 1f, .5f), 6);
            b.Glow = 0;
            // tow line + banner
            b.Quad(new Vector3(-9.6f, -.1f, 0), new Vector3(-9.6f, .1f, 0), new Vector3(-15, .1f, 0), new Vector3(-15, -.1f, 0), new Color(.2f, .2f, .2f));
            b.Glow = .6f;
            for (int i = 0; i < 8; i++)
            {
                float x0 = -15 - i * 1.4f, x1 = x0 - 1.4f;
                b.Quad(new Vector3(x0, 1.4f, 0), new Vector3(x1, 1.4f, 0), new Vector3(x1, -1.4f, 0), new Vector3(x0, -1.4f, 0), new Color(1f, .86f, .25f), new Vector2(i / 8f * .5f, i * .3f), new Vector2((i + 1) / 8f * .5f, i * .3f + .3f));
            }
            blimp = b.Build(root, "Majestic blimp", mat, false).transform;
            blimp.position = new Vector3(-40, 58, 150);

            // ---- searchlights (additive shafts) ----
            foreach (var (pos, phase) in new[] { (new Vector3(-55, -10, 230), 0f), (new Vector3(75, -10, 280), 2.2f) })
            {
                var m = new MajesticMesh();
                const float L = 420, w0 = 1.2f, w1 = 22;
                foreach (var side in new[] { Vector3.right, Vector3.forward })
                {
                    m.Tri(-side * w0, side * w0, side * w1 + Vector3.up * L, Color.white, new Vector2(0, -1), new Vector2(0, 1), new Vector2(1, 1));
                    m.Tri(-side * w0, side * w1 + Vector3.up * L, -side * w1 + Vector3.up * L, Color.white, new Vector2(0, -1), new Vector2(1, 1), new Vector2(1, -1));
                }
                var go = m.Build(root, "Majestic searchlight", MajesticMesh.Beam(), false);
                go.transform.position = pos; go.transform.localEulerAngles = new Vector3(0, 0, phase);
                go.GetComponent<MeshRenderer>().receiveShadows = false;
                beams.Add(go.transform);
            }
        }

        static void Box(MajesticMesh m, Vector3 c, Vector3 s, Color col)
        {
            Vector3 h = s * .5f;
            Vector3[] p = { c + new Vector3(-h.x, -h.y, -h.z), c + new Vector3(h.x, -h.y, -h.z), c + new Vector3(h.x, h.y, -h.z), c + new Vector3(-h.x, h.y, -h.z), c + new Vector3(-h.x, -h.y, h.z), c + new Vector3(h.x, -h.y, h.z), c + new Vector3(h.x, h.y, h.z), c + new Vector3(-h.x, h.y, h.z) };
            m.Quad(p[3], p[2], p[6], p[7], col); m.Quad(p[0], p[1], p[2], p[3], col * .85f); m.Quad(p[5], p[4], p[7], p[6], col * .85f);
            m.Quad(p[4], p[0], p[3], p[7], col * .75f); m.Quad(p[1], p[5], p[6], p[2], col * .75f);
        }

        public static void Animate(MajesticLook look, float t)
        {
            if (blimp)
            {
                var p = blimp.position; p.x += Time.deltaTime * 2.2f; if (p.x > 90) p.x = -90;
                p.y = 58 + Mathf.Sin(t * .3f) * 1.2f; blimp.position = p;
                blimp.rotation = Quaternion.Euler(0, 0, Mathf.Sin(t * .25f) * 2);
            }
            for (int i = 0; i < beams.Count; i++)
                beams[i].localRotation = Quaternion.Euler(Mathf.Sin(t * .21f + i * 2.4f) * 14, 0, Mathf.Sin(t * .17f + i * 1.3f) * 22 + (i == 0 ? 12 : -12));
        }

        public static void SetMaterials(bool on, MajesticLook look)
        {
            if (on)
            {
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    foreach (var m in r.sharedMaterials)
                    {
                        if (!m || styled.Contains(m)) continue;
                        string sh = m.shader ? m.shader.name : "";
                        if (sh.EndsWith("TennisTowerAtmosphere")) { Set(m, "_EmissionColor", new Color(2.6f, 1.55f, .72f)); Set(m, "_Smoothness", .55f); }
                        else if (sh.EndsWith("TennisRooftopSky")) Set(m, "_Exposure", .52f);
                        else if (sh.EndsWith("TennisCloudAtmosphere")) Set(m, "_Exposure", .64f);
                        else if (m.name.StartsWith("TropicalV3_002")) { Set(m, "_BaseColor", look.Court); Set(m, "_Smoothness", .58f); }
                        else if (m.name.StartsWith("TropicalV3_011")) { Set(m, "_BaseColor", look.Lawn); Set(m, "_Smoothness", .38f); }
                        else continue;
                        styled.Add(m);
                    }
            }
            else
            {
                for (int i = saved.Count - 1; i >= 0; i--)
                {
                    var (m, prop, value) = saved[i]; if (!m) continue;
                    if (value is Color c) m.SetColor(prop, c); else if (value is float f) m.SetFloat(prop, f);
                }
                saved.Clear(); styled.Clear();
            }
        }

        static void Set(Material m, string prop, object value)
        {
            if (!m.HasProperty(prop)) return;
            object old = value switch { Color => m.GetColor(prop), _ => m.GetFloat(prop) };
            if (!saved.Exists(s => s.m == m && s.prop == prop)) saved.Add((m, prop, old));
            if (value is Color c) m.SetColor(prop, c); else if (value is float f) m.SetFloat(prop, f);
        }
    }
}
