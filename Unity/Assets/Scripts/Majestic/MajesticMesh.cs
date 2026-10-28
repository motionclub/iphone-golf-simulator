using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Majestic
{
    /// Shared procedural mesh kit for the majestic dressing (GolfArcade/MajesticDressing):
    /// colour = vertex colour, uv0 = (sway weight, phase), uv1 = (flap amplitude, flap speed),
    /// uv2.x = glow (emission multiplier; picked up by bloom).
    public sealed class MajesticMesh
    {
        public readonly List<Vector3> v = new(), n = new(); public readonly List<Color> c = new();
        public readonly List<Vector2> uv = new(), uv1 = new(), uv2 = new(); public readonly List<int> t = new();
        public float Glow;

        public void Tri(Vector3 a, Vector3 b, Vector3 d, Color col, Vector2 sa, Vector2 sb, Vector2 sd, Vector2 f = default)
        {
            var nn = Vector3.Cross(b - a, d - a).normalized; int i = v.Count;
            v.Add(a); v.Add(b); v.Add(d); n.Add(nn); n.Add(nn); n.Add(nn); c.Add(col); c.Add(col); c.Add(col);
            uv.Add(sa); uv.Add(sb); uv.Add(sd); uv1.Add(f); uv1.Add(f); uv1.Add(f);
            var g = new Vector2(Glow, 0); uv2.Add(g); uv2.Add(g); uv2.Add(g);
            t.Add(i); t.Add(i + 1); t.Add(i + 2);
        }
        /// Quad with per-corner colour and glow (smooth gradients, e.g. lava rivers).
        public void QuadV(Vector3 a, Vector3 b, Vector3 d, Vector3 e, Color ca, Color cb, Color cd, Color ce, float ga, float gb, float gd, float ge)
        {
            void T(Vector3 p0, Vector3 p1, Vector3 p2, Color c0, Color c1, Color c2, float g0, float g1, float g2)
            {
                var nn = Vector3.Cross(p1 - p0, p2 - p0).normalized; int i = v.Count;
                v.Add(p0); v.Add(p1); v.Add(p2); n.Add(nn); n.Add(nn); n.Add(nn); c.Add(c0); c.Add(c1); c.Add(c2);
                uv.Add(Vector2.zero); uv.Add(Vector2.zero); uv.Add(Vector2.zero); uv1.Add(Vector2.zero); uv1.Add(Vector2.zero); uv1.Add(Vector2.zero);
                uv2.Add(new Vector2(g0, 0)); uv2.Add(new Vector2(g1, 0)); uv2.Add(new Vector2(g2, 0));
                t.Add(i); t.Add(i + 1); t.Add(i + 2);
            }
            T(a, b, d, ca, cb, cd, ga, gb, gd); T(a, d, e, ca, cd, ce, ga, gd, ge);
        }
        public void Tri(Vector3 a, Vector3 b, Vector3 d, Color col) => Tri(a, b, d, col, Vector2.zero, Vector2.zero, Vector2.zero);
        public void Quad(Vector3 a, Vector3 b, Vector3 d, Vector3 e, Color col, Vector2 s0, Vector2 s1)
        { Tri(a, b, d, col, s0, s0, s1); Tri(a, d, e, col, s0, s1, s1); }
        public void Quad(Vector3 a, Vector3 b, Vector3 d, Vector3 e, Color col) => Quad(a, b, d, e, col, Vector2.zero, Vector2.zero);

        /// Low-poly blob (icosphere-ish, 2 rings) — bulbs, puffs, blossoms seen from afar.
        public void Blob(Vector3 p, Vector3 r, Color top, Color bottom, int seg = 8)
        {
            var rings = new[] { -.6f, 0f, .6f };
            Vector3 P(int ring, int k)
            {
                float y = ring < 0 ? -1 : ring >= rings.Length ? 1 : rings[ring];
                float rad = Mathf.Sqrt(Mathf.Max(0, 1 - y * y)); float a = k * Mathf.PI * 2 / seg;
                return p + Vector3.Scale(new Vector3(Mathf.Cos(a) * rad, y, Mathf.Sin(a) * rad), r);
            }
            for (int ring = -1; ring < rings.Length; ring++)
                for (int k = 0; k < seg; k++)
                {
                    float y0 = ring < 0 ? -1 : rings[ring], y1 = ring + 1 >= rings.Length ? 1 : rings[ring + 1];
                    var col = Color.Lerp(bottom, top, (y0 + y1) * .25f + .5f);
                    if (ring < 0) Tri(P(-1, 0), P(0, k + 1), P(0, k), col);
                    else if (ring + 1 >= rings.Length) Tri(P(ring, k), P(ring, k + 1), P(rings.Length, 0), col);
                    else Quad(P(ring, k), P(ring, k + 1), P(ring + 1, k + 1), P(ring + 1, k), col);
                }
        }

        public GameObject Build(Transform root, string name, Material mat, bool shadows)
        {
            var go = new GameObject(name); go.transform.SetParent(root, false);
            var mesh = new Mesh { name = name, indexFormat = v.Count > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
            mesh.SetVertices(v); mesh.SetNormals(n); mesh.SetColors(c); mesh.SetUVs(0, uv); mesh.SetUVs(1, uv1); mesh.SetUVs(2, uv2); mesh.SetTriangles(t, 0);
            mesh.RecalculateBounds(); mesh.bounds = new Bounds(mesh.bounds.center, mesh.bounds.size + Vector3.one * 2);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>(); r.sharedMaterial = mat;
            r.shadowCastingMode = shadows ? ShadowCastingMode.On : ShadowCastingMode.Off; r.receiveShadows = true;
            return go;
        }

        // ---- shared pieces ----

        public static readonly Color[] Pennants =
        {
            new(.93f,.20f,.18f), new(1f,.80f,.16f), new(.16f,.46f,.92f), new(.22f,.72f,.32f),
            new(1f,.52f,.12f), new(.95f,.38f,.62f), new(.97f,.96f,.92f),
        };

        // (not inlined: Xcode 26.2's clang crashed in its register coalescer compiling Bunting with this inlined into it, IL2CPP -O3)
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        public static Vector3 Sag(Vector3 a, Vector3 d, float sag, float s) => Vector3.Lerp(a, d, s) + Vector3.down * sag * 4 * s * (1 - s);

        /// Rope with triangular pennants hanging along a sagging span.
        public void Bunting(Vector3 a, Vector3 d, float sag, System.Random rng, float size = 1)
        {
            float len = Vector3.Distance(a, d); int count = Mathf.Max(2, Mathf.RoundToInt(len / (.46f * size)));
            var rope = new Color(.92f, .90f, .84f);
            for (int i = 0; i < 16; i++)
            {
                Vector3 p0 = Sag(a, d, sag, i / 16f), p1 = Sag(a, d, sag, (i + 1) / 16f);
                Quad(p0, p1, p1 + Vector3.down * .025f, p0 + Vector3.down * .025f, rope);
            }
            int colour = rng.Next(Pennants.Length);
            for (int i = 0; i < count; i++)
            {
                float s0 = (i + .12f) / count, s1 = (i + .88f) / count, sm = (s0 + s1) * .5f;
                // hung from the rope's lower edge and 4 mm in front of its plane: a pennant overlapping the rope band in the
                // same plane z-fought with it (the menu's flicker along every string)
                Vector3 hang = Vector3.down * .025f + Vector3.Cross(d - a, Vector3.up).normalized * .004f;
                Vector3 p0 = Sag(a, d, sag, s0) + hang, p1 = Sag(a, d, sag, s1) + hang, tip = Sag(a, d, sag, sm) + hang + Vector3.down * .42f * size;
                float phase = (float)rng.NextDouble();
                Tri(p0, p1, tip, Pennants[(colour + i) % Pennants.Length], new Vector2(0, phase), new Vector2(0, phase), new Vector2(.25f, phase));
            }
        }

        /// Warm fairy lights: a dark cord with glowing bulbs every ~0.55 m.
        public void StringLights(Vector3 a, Vector3 d, float sag, Color bulb, float glow = 6)
        {
            var cord = new Color(.12f, .11f, .10f);
            for (int i = 0; i < 16; i++)
            {
                Vector3 p0 = Sag(a, d, sag, i / 16f), p1 = Sag(a, d, sag, (i + 1) / 16f);
                Quad(p0, p1, p1 + Vector3.down * .02f, p0 + Vector3.down * .02f, cord);
            }
            int count = Mathf.Max(2, Mathf.RoundToInt(Vector3.Distance(a, d) / .55f));
            float keep = Glow; Glow = glow;
            for (int i = 0; i <= count; i++) Blob(Sag(a, d, sag, i / (float)count) + Vector3.down * .07f, Vector3.one * .055f, bulb, bulb, 6);
            Glow = keep;
        }

        /// A flag on a pole; the cloth sways and ripples on the shared wind.
        public void Flag(Vector3 foot, float height, Vector2 cloth, Color[] stripes, float phase)
        {
            var pole = new Color(.82f, .80f, .76f);
            Quad(foot + new Vector3(-.04f, 0, 0), foot + new Vector3(.04f, 0, 0), foot + new Vector3(.04f, height, 0), foot + new Vector3(-.04f, height, 0), pole);
            Quad(foot + new Vector3(0, 0, -.04f), foot + new Vector3(0, 0, .04f), foot + new Vector3(0, height, .04f), foot + new Vector3(0, height, -.04f), pole);
            Vector3 top = foot + Vector3.up * (height - .1f);
            int cols = 6; float w = cloth.x, h = cloth.y;
            for (int s = 0; s < stripes.Length; s++)
            {
                float y0 = -h * s / stripes.Length, y1 = -h * (s + 1) / stripes.Length;
                for (int i = 0; i < cols; i++)
                {
                    float x0 = w * i / cols, x1 = w * (i + 1) / cols;
                    Vector3 a = top + new Vector3(0, y0, x0), b = top + new Vector3(0, y0, x1), d = top + new Vector3(0, y1, x1), e = top + new Vector3(0, y1, x0);
                    Tri(a, b, d, stripes[s], new Vector2(x0 / w * .8f, phase + x0 * .4f), new Vector2(x1 / w * .8f, phase + x1 * .4f), new Vector2(x1 / w * .8f, phase + x1 * .4f));
                    Tri(a, d, e, stripes[s], new Vector2(x0 / w * .8f, phase + x0 * .4f), new Vector2(x1 / w * .8f, phase + x1 * .4f), new Vector2(x0 / w * .8f, phase + x0 * .4f));
                }
            }
        }

        public void Gull(float phase)
        {
            var white = new Color(.97f, .97f, .96f); var grey = new Color(.62f, .66f, .72f);
            Tri(new Vector3(0, 0, .35f), new Vector3(-.06f, 0, -.3f), new Vector3(.06f, 0, -.3f), white, new Vector2(0, phase), new Vector2(0, phase), new Vector2(0, phase));
            foreach (float s in new[] { -1f, 1f })
            {
                Tri(new Vector3(0, 0, .12f), new Vector3(s * .38f, .05f, .05f), new Vector3(0, 0, -.12f), white, new Vector2(0, phase), new Vector2(0, phase), new Vector2(0, phase), new Vector2(.06f, 9));
                Tri(new Vector3(s * .38f, .05f, .05f), new Vector3(s * .72f, 0, -.08f), new Vector3(0, 0, -.12f), grey, new Vector2(0, phase), new Vector2(0, phase), new Vector2(0, phase), new Vector2(.22f, 9));
            }
        }

        static Material dressing, beam;
        public static Material Dressing()
        {
            if (dressing) return dressing;
            var shader = Resources.Load<Shader>("Majestic/MajesticDressing") ?? Shader.Find("GolfArcade/MajesticDressing");
            return dressing = new Material(shader) { name = "Majestic dressing" };
        }
        public static Material Beam()
        {
            if (beam) return beam;
            var shader = Resources.Load<Shader>("Majestic/MajesticBeam") ?? Shader.Find("GolfArcade/MajesticBeam");
            return beam = new Material(shader) { name = "Majestic beam" };
        }
    }
}
