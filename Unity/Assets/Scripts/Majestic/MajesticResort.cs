using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Resort dressing toward concepts/after/tennis_resort_clear.jpg: bunting on the pergola and clubhouse,
    /// blossoms in the planters and the back hedge, sailboats and gulls on the bay, a striped lawn instead of
    /// the dark run-off, a royal-blue court and a turquoise-to-sapphire sea. Positions come from the venue
    /// builders (TennisResortVista.Pergola x=-16.6, TennisVenueArt planters x=±14.2 z=-17.5+7i, hedge z=30,
    /// EnvV4_BeachHouse at x≈18..28). All meshes are merged per kind; one material; ~3-4 draw calls.
    public static class MajesticResort
    {
        static readonly List<Transform> boats = new(), gulls = new();
        static readonly List<(Material m, string prop, object value)> saved = new();
        static Material dressing;
        static Texture2D stripes;
        static bool applied;

        static readonly Color[] Pennants =
        {
            new(.93f,.20f,.18f), new(1f,.80f,.16f), new(.16f,.46f,.92f), new(.22f,.72f,.32f),
            new(1f,.52f,.12f), new(.95f,.38f,.62f), new(.97f,.96f,.92f),
        };
        static readonly Color[] Blossoms = { new(.98f,.30f,.45f), new(.95f,.18f,.22f), new(1f,.55f,.30f), new(1f,.85f,.30f), new(.98f,.62f,.78f), new(.95f,.95f,.92f) };

        public static Material DressingMaterial()
        {
            if (dressing) return dressing;
            var shader = Resources.Load<Shader>("Majestic/MajesticDressing") ?? Shader.Find("GolfArcade/MajesticDressing");
            dressing = new Material(shader) { name = "Majestic dressing", enableInstancing = false };
            return dressing;
        }

        public static void Build(Transform root, MajesticLook look)
        {
            boats.Clear(); gulls.Clear();
            var mat = DressingMaterial();
            var rng = new System.Random(1017);

            // ---- bunting ----
            var flags = new MeshBuilder();
            // pergola front beam (court side) between the five columns, and its rear L-return
            for (int i = 0; i < 4; i++)
                Bunting(flags, new Vector3(-15.0f, 5.40f, -13.4f + i * 6.7f), new Vector3(-15.0f, 5.40f, -13.4f + (i + 1) * 6.7f), .55f, rng);
            for (int i = 0; i < 2; i++)
                Bunting(flags, new Vector3(-23.6f + i * 4.1f, 5.40f, 22.9f), new Vector3(-23.6f + (i + 1) * 4.1f, 5.40f, 22.9f), .35f, rng);
            Bunting(flags, new Vector3(-15.4f, 5.40f, 22.9f), new Vector3(-15.0f, 5.40f, 13.4f), .7f, rng);
            // across the promenade from the pergola to the far lamp line, and along the clubhouse balcony
            Bunting(flags, new Vector3(-15.0f, 5.40f, 13.4f), new Vector3(-10.9f, 3.95f, 18.0f), .45f, rng);
            for (int i = 0; i < 3; i++)
                Bunting(flags, new Vector3(18.0f, 6.30f, -2.5f + i * 5.2f), new Vector3(18.0f, 6.30f, -2.5f + (i + 1) * 5.2f), .45f, rng);
            Bunting(flags, new Vector3(18.0f, 6.30f, 13.1f), new Vector3(10.9f, 3.95f, 18.0f), .55f, rng);
            Mesh(root, "Majestic bunting", flags, mat, true);

            // ---- blossoms ----
            var flowers = new MeshBuilder();
            for (int side = -1; side <= 1; side += 2)
                for (int i = 0; i < 6; i++)
                    Blossoms_(flowers, new Vector3(side * 14.2f, 1.15f, -17.5f + i * 7), .62f, 18, rng);
            for (int i = 0; i < 9; i++)
                Blossoms_(flowers, new Vector3(-30 + i * 7.5f, .9f, 29.3f), 1.3f, 26, rng);
            // the ivory ceramic planters beside the court (one merged mesh): find each pot by clustering its
            // vertices along Z and crown it with blossoms
            foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (r.name != "Crafted resort ceramic planters") continue;
                var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh || !mf.sharedMesh.isReadable) continue;
                var pts = new List<Vector3>(); mf.sharedMesh.GetVertices(pts);
                for (int i = 0; i < pts.Count; i++) pts[i] = r.transform.TransformPoint(pts[i]);
                pts.Sort((p, q) => p.z.CompareTo(q.z));
                int start = 0;
                for (int i = 1; i <= pts.Count; i++)
                {
                    if (i < pts.Count && pts[i].z - pts[i - 1].z < .6f) continue;
                    Vector3 lo = pts[start], hi = pts[start];
                    for (int k = start; k < i; k++) { lo = Vector3.Min(lo, pts[k]); hi = Vector3.Max(hi, pts[k]); }
                    float size = Mathf.Max(hi.x - lo.x, hi.z - lo.z);
                    if (size > .3f && size < 3) Blossoms_(flowers, new Vector3((lo.x + hi.x) * .5f, hi.y + .12f, (lo.z + hi.z) * .5f), size * .42f, 14, rng);
                    start = i;
                }
            }
            Mesh(root, "Majestic blossoms", flowers, mat, false);

            // ---- sailboats ----
            foreach (var (pos, scale, yaw) in new[] { (new Vector3(-22, -4.0f, 150), 1.0f, 20f), (new Vector3(48, -4.0f, 235), 1.25f, -35f), (new Vector3(-95, -4.0f, 290), 1.1f, 60f) })
            {
                var mb = new MeshBuilder(); Sailboat(mb);
                var t = Mesh(root, "Majestic sailboat", mb, mat, false).transform;
                t.position = pos; t.localScale = Vector3.one * scale; t.rotation = Quaternion.Euler(0, yaw, 0);
                boats.Add(t);
            }
            MajesticCrowd.Build(root);
            // ---- gulls ----
            for (int i = 0; i < 6; i++)
            {
                var mb = new MeshBuilder(); Gull(mb, (float)rng.NextDouble());
                var t = Mesh(root, "Majestic gull", mb, mat, false).transform;
                t.position = new Vector3(-20 + i * 9, 16 + i % 3 * 5, 70 + i * 12);
                gulls.Add(t);
            }
        }

        public static void Animate(MajesticLook look, float t)
        {
            for (int i = 0; i < boats.Count; i++)
            {
                var b = boats[i]; if (!b) continue;
                var p = b.position; p.y = -4.0f + Mathf.Sin(t * .8f + i * 1.7f) * .12f; p.x += Time.deltaTime * .35f * (i % 2 == 0 ? 1 : -1); b.position = p;
                b.rotation = Quaternion.Euler(Mathf.Sin(t * .6f + i) * 2.5f, b.eulerAngles.y, Mathf.Sin(t * .9f + i * 2) * 3.5f);
            }
            for (int i = 0; i < gulls.Count; i++)
            {
                var g = gulls[i]; if (!g) continue;
                float a = t * (.16f + i * .013f) + i * 1.3f, r = 22 + i * 4;
                var c = new Vector3(-6 + i * 3, 18 + i % 3 * 5 + Mathf.Sin(t * .4f + i) * 1.5f, 95 + i * 10);
                var p = c + new Vector3(Mathf.Cos(a) * r, 0, Mathf.Sin(a) * r * .6f);
                var dir = p - g.position; if (dir.sqrMagnitude > 1e-6) g.rotation = Quaternion.Slerp(g.rotation, Quaternion.LookRotation(dir.normalized) * Quaternion.Euler(0, 0, -12), .1f);
                g.position = p;
            }
        }

        // ---- materials ----

        static readonly HashSet<Material> styled = new();
        /// Idempotent: styles any resort material not yet styled (the venue's own layers swap some
        /// materials for copies after the match starts, so MajesticVenue calls this again now and then).
        public static void SetMaterials(bool on, MajesticLook look)
        {
            if (on)
            {
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    foreach (var m in r.sharedMaterials)
                    {
                        if (!m || styled.Contains(m)) continue; string n = m.name;
                        if (n.StartsWith("TropicalV3_011")) Lawn(m, look);
                        else if (n.StartsWith("TropicalV3_002")) Set(m, "_BaseColor", look.Court);
                        else if (n.StartsWith("Resort sea")) Sea(m, look);
                        else continue;
                        styled.Add(m);
                    }
                applied = true;
            }
            else if (applied)
            {
                for (int i = saved.Count - 1; i >= 0; i--)
                {
                    var (m, prop, value) = saved[i]; if (!m) continue;
                    switch (value) { case Color c: m.SetColor(prop, c); break; case float f: m.SetFloat(prop, f); break; case Texture tex: m.SetTexture(prop, tex); break; case null: m.SetTexture(prop, null); break; }
                }
                saved.Clear(); styled.Clear(); applied = false;
            }
        }

        static void Set(Material m, string prop, object value)
        {
            if (!m.HasProperty(prop)) return;
            object old = value switch { Color => m.GetColor(prop), float => m.GetFloat(prop), _ => m.GetTexture(prop) };
            if (saved.Exists(s => s.m == m && s.prop == prop) == false) saved.Add((m, prop, old));
            switch (value) { case Color c: m.SetColor(prop, c); break; case float f: m.SetFloat(prop, f); break; case Texture t: m.SetTexture(prop, t); break; }
        }

        static void Lawn(Material m, MajesticLook look)
        {
            if (!stripes)
            {
                // two mown bands per tile along X (bands run down the court's length), soft 6 px edges
                const int w = 64; stripes = new Texture2D(w, 4, TextureFormat.RGBA32, false, false) { wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, name = "Majestic lawn stripes" };
                var px = new Color[w * 4];
                float lo = look.Lawn.grayscale, hi = look.LawnStripe.grayscale, k = hi / Mathf.Max(lo, .01f);
                for (int x = 0; x < w; x++)
                {
                    float s = Mathf.SmoothStep(0, 1, Mathf.Clamp01((Mathf.Abs(x - w / 2f) - w / 4f) / 6f + .5f));
                    float v = Mathf.Lerp(1f, k, s);
                    for (int y = 0; y < 4; y++) px[y * w + x] = new Color(v * .5f, v * .5f, v * .5f, 1);
                }
                stripes.SetPixels(px); stripes.Apply(false, true);
            }
            Set(m, "_BaseColor", look.Lawn);
            Set(m, "_WorldMap", stripes);
            Set(m, "_WorldMapWeight", 1f);
            Set(m, "_WorldMapScale", 1f / 3.4f);
            Set(m, "_WorldMapReference", .5f);
            Set(m, "_Variation", .07f);
            Set(m, "_Smoothness", .18f);
        }

        static void Sea(Material m, MajesticLook look)
        {
            Set(m, "_Shallow", look.SeaShallow); Set(m, "_Deep", look.SeaDeep); Set(m, "_Sky", look.SeaSky);
            Set(m, "_Sparkle", look.SeaSparkle); Set(m, "_SunSheen", look.SeaSheen);
        }

        // ---- meshes ----

        sealed class MeshBuilder
        {
            public readonly List<Vector3> v = new(), n = new(); public readonly List<Color> c = new();
            public readonly List<Vector2> uv = new(), uv1 = new(); public readonly List<int> t = new();
            public void Tri(Vector3 a, Vector3 b, Vector3 d, Color col, Vector2 sa, Vector2 sb, Vector2 sd, Vector2 f = default)
            {
                var nn = Vector3.Cross(b - a, d - a).normalized; int i = v.Count;
                v.Add(a); v.Add(b); v.Add(d); n.Add(nn); n.Add(nn); n.Add(nn); c.Add(col); c.Add(col); c.Add(col);
                uv.Add(sa); uv.Add(sb); uv.Add(sd); uv1.Add(f); uv1.Add(f); uv1.Add(f); t.Add(i); t.Add(i + 1); t.Add(i + 2);
            }
            public void Quad(Vector3 a, Vector3 b, Vector3 d, Vector3 e, Color col, Vector2 s0, Vector2 s1)
            { Tri(a, b, d, col, s0, s0, s1); Tri(a, d, e, col, s0, s1, s1); }
        }

        static GameObject Mesh(Transform root, string name, MeshBuilder b, Material mat, bool shadows)
        {
            var go = new GameObject(name); go.transform.SetParent(root, false);
            var mesh = new Mesh { name = name, indexFormat = b.v.Count > 65000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16 };
            mesh.SetVertices(b.v); mesh.SetNormals(b.n); mesh.SetColors(b.c); mesh.SetUVs(0, b.uv); mesh.SetUVs(1, b.uv1); mesh.SetTriangles(b.t, 0);
            mesh.RecalculateBounds(); mesh.bounds = new Bounds(mesh.bounds.center, mesh.bounds.size + Vector3.one * 2);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>(); r.sharedMaterial = mat;
            r.shadowCastingMode = shadows ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = true;
            return go;
        }

        /// A rope with triangular pennants hanging along a catenary-ish sag.
        static void Bunting(MeshBuilder b, Vector3 a, Vector3 d, float sag, System.Random rng)
        {
            float len = Vector3.Distance(a, d); int count = Mathf.Max(2, Mathf.RoundToInt(len / .46f));
            Vector3 along = (d - a).normalized;
            Vector3 P(float s) => Vector3.Lerp(a, d, s) + Vector3.down * sag * 4 * s * (1 - s);
            int colour = rng.Next(Pennants.Length);
            // rope
            var rope = new Color(.92f, .90f, .84f);
            for (int i = 0; i < 16; i++)
            {
                Vector3 p0 = P(i / 16f), p1 = P((i + 1) / 16f);
                b.Quad(p0, p1, p1 + Vector3.down * .025f, p0 + Vector3.down * .025f, rope, new Vector2(0, 0), new Vector2(0, 0));
            }
            for (int i = 0; i < count; i++)
            {
                float s0 = (i + .12f) / count, s1 = (i + .88f) / count, sm = (s0 + s1) * .5f;
                Vector3 p0 = P(s0), p1 = P(s1), tip = P(sm) + Vector3.down * .42f;
                var col = Pennants[(colour + i) % Pennants.Length];
                float phase = (float)rng.NextDouble();
                b.Tri(p0, p1, tip, col, new Vector2(0, phase), new Vector2(0, phase), new Vector2(.25f, phase));
            }
        }

        static void Blossoms_(MeshBuilder b, Vector3 centre, float radius, int count, System.Random rng)
        {
            for (int i = 0; i < count; i++)
            {
                float a = (float)rng.NextDouble() * Mathf.PI * 2, r = Mathf.Sqrt((float)rng.NextDouble()) * radius;
                var p = centre + new Vector3(Mathf.Cos(a) * r, (float)rng.NextDouble() * .35f * radius * (1 - r / radius), Mathf.Sin(a) * r);
                var col = Blossoms[rng.Next(Blossoms.Length)];
                float s = .07f + (float)rng.NextDouble() * .06f;
                // five-petal star facing up-ish, plus a small dome so it reads from the side
                var up = (Vector3.up + new Vector3((float)rng.NextDouble() - .5f, 0, (float)rng.NextDouble() - .5f) * .8f).normalized;
                var t1 = Vector3.Cross(up, Vector3.forward).normalized; var t2 = Vector3.Cross(up, t1);
                for (int k = 0; k < 5; k++)
                {
                    float q0 = k * Mathf.PI * 2 / 5, q1 = q0 + Mathf.PI * 2 / 5, qm = (q0 + q1) * .5f;
                    Vector3 e0 = p + (t1 * Mathf.Cos(q0) + t2 * Mathf.Sin(q0)) * s * .45f, e1 = p + (t1 * Mathf.Cos(q1) + t2 * Mathf.Sin(q1)) * s * .45f;
                    Vector3 tip = p + (t1 * Mathf.Cos(qm) + t2 * Mathf.Sin(qm)) * s + up * s * .15f;
                    b.Tri(e0, tip, e1, col, Vector2.zero, Vector2.zero, Vector2.zero);
                    b.Tri(p + up * s * .25f, e0, e1, col * .92f, Vector2.zero, Vector2.zero, Vector2.zero);
                }
            }
        }

        static void Sailboat(MeshBuilder b)
        {
            var hull = new Color(.96f, .95f, .92f); var stripe = new Color(.16f, .38f, .78f); var sail = new Color(.99f, .98f, .95f);
            // hull: tapered box 6 m long
            Vector3[] top = { new(-.9f, .6f, -3f), new(.9f, .6f, -3f), new(.9f, .6f, 2.2f), new(0, .6f, 3.2f), new(-.9f, .6f, 2.2f) };
            Vector3[] bot = { new(-.5f, -.2f, -2.6f), new(.5f, -.2f, -2.6f), new(.5f, -.2f, 1.9f), new(0, -.2f, 2.6f), new(-.5f, -.2f, 1.9f) };
            for (int i = 0; i < 5; i++) { int j = (i + 1) % 5; b.Quad(top[i], top[j], bot[j], bot[i], i == 0 ? hull : stripe, Vector2.zero, Vector2.zero); }
            b.Tri(top[0], top[2], top[1], hull, Vector2.zero, Vector2.zero, Vector2.zero); b.Tri(top[0], top[4], top[2], hull, Vector2.zero, Vector2.zero, Vector2.zero); b.Tri(top[4], top[3], top[2], hull, Vector2.zero, Vector2.zero, Vector2.zero);
            // mast + main sail + jib (sails sway gently: weight grows toward the free edge)
            b.Quad(new Vector3(-.06f, .6f, .2f), new Vector3(.06f, .6f, .2f), new Vector3(.06f, 8.6f, .2f), new Vector3(-.06f, 8.6f, .2f), new Color(.85f, .82f, .78f), Vector2.zero, Vector2.zero);
            b.Tri(new Vector3(0, 8.4f, .1f), new Vector3(0, 1.1f, .1f), new Vector3(.15f, 1.1f, -2.6f), sail, new Vector2(0, .3f), new Vector2(0, .3f), new Vector2(.05f, .3f));
            b.Tri(new Vector3(0, 7.6f, .35f), new Vector3(0, 1.0f, 2.9f), new Vector3(0, 1.0f, .35f), sail, new Vector2(0, .7f), new Vector2(.04f, .7f), new Vector2(0, .7f));
        }

        static void Gull(MeshBuilder b, float phase)
        {
            var white = new Color(.97f, .97f, .96f); var grey = new Color(.62f, .66f, .72f);
            // body + two wings; wing tips flap (uv1.x amplitude, uv1.y speed)
            b.Tri(new Vector3(0, 0, .35f), new Vector3(-.06f, 0, -.3f), new Vector3(.06f, 0, -.3f), white, new Vector2(0, phase), new Vector2(0, phase), new Vector2(0, phase));
            foreach (float s in new[] { -1f, 1f })
            {
                b.Tri(new Vector3(0, 0, .12f), new Vector3(s * .38f, .05f, .05f), new Vector3(0, 0, -.12f), white, new Vector2(0, phase), new Vector2(0, phase), new Vector2(0, phase), new Vector2(.0f, 9));
                b.Tri(new Vector3(s * .38f, .05f, .05f), new Vector3(s * .72f, 0, -.08f), new Vector3(0, 0, -.12f), grey, new Vector2(0, phase), new Vector2(0, phase), new Vector2(0, phase), new Vector2(.22f, 9));
            }
        }
    }
}
