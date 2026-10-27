using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The regulation tenpin, lathed from its profile: the render mesh (white body, two red neck
    /// stripes as submesh 1) and three convex hulls for PhysX (base→belly, belly→neck, neck→top).
    /// Origin at the centre of the base, +y up.
    public static class BowlingPinShape
    {
        const float In = .0254f;

        // USBC pin profile: height above the base, diameter (inches).
        static readonly Vector2[] Profile =
        {
            new Vector2(0, 2.031f), new Vector2(.375f, 2.48f), new Vector2(.75f, 2.828f), new Vector2(1.5f, 3.43f),
            new Vector2(2.25f, 3.906f), new Vector2(3.375f, 4.510f), new Vector2(4.5f, 4.766f), new Vector2(5.875f, 4.563f),
            new Vector2(7.25f, 3.989f), new Vector2(8.625f, 3.100f), new Vector2(9.375f, 2.580f), new Vector2(10f, 2.12f),
            new Vector2(10.875f, 1.797f), new Vector2(11.75f, 1.90f), new Vector2(12.5f, 2.25f), new Vector2(13.5f, 2.547f),
            new Vector2(14.25f, 2.25f), new Vector2(14.7f, 1.6f), new Vector2(14.93f, .9f), new Vector2(15f, 0),
        };

        // Two red neck stripes (heights in inches).
        static readonly Vector2[] Stripes = { new Vector2(9.0f, 9.45f), new Vector2(9.75f, 10.2f) };

        public const float BellyHeight = 4.5f * In, NeckHeight = 10.875f * In;

        public static float Radius(float height)
        {
            float h = height / In;
            for (int i = 1; i < Profile.Length; i++)
                if (h <= Profile[i].x)
                {
                    float t = Mathf.InverseLerp(Profile[i - 1].x, Profile[i].x, h);
                    return Mathf.Lerp(Profile[i - 1].y, Profile[i].y, t) * .5f * In;
                }
            return 0;
        }

        static List<float> Rings(float from, float to, float step)
        {
            var heights = new List<float>();
            for (float h = from; h < to - 1e-5f; h += step) heights.Add(h);
            heights.Add(to);
            return heights;
        }

        /// Render mesh: submesh 0 = white lacquer, submesh 1 = red stripes.
        public static Mesh Build(int segments = 28)
        {
            var heights = new List<float>();
            foreach (var p in Profile) heights.Add(p.x * In);
            foreach (var s in Stripes) { heights.Add(s.x * In); heights.Add(s.y * In); }
            for (float h = .25f; h < 15; h += .5f) heights.Add(h * In);
            heights.Sort();
            for (int i = heights.Count - 1; i > 0; i--) if (heights[i] - heights[i - 1] < .002f) heights.RemoveAt(i);

            var verts = new List<Vector3>(); var normals = new List<Vector3>(); var uvs = new List<Vector2>();
            var white = new List<int>(); var red = new List<int>();
            int ring = segments + 1;
            for (int r = 0; r < heights.Count; r++)
            {
                float h = heights[r], rad = Radius(h);
                float slope = (Radius(Mathf.Min(BowlingLane.PinHeight, h + .002f)) - Radius(Mathf.Max(0, h - .002f))) / .004f;
                for (int s = 0; s <= segments; s++)
                {
                    float a = s * 2 * Mathf.PI / segments;
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    verts.Add(dir * rad + Vector3.up * h);
                    normals.Add((dir - Vector3.up * slope).normalized);
                    uvs.Add(new Vector2(s / (float)segments, h / BowlingLane.PinHeight));
                }
            }
            for (int r = 0; r + 1 < heights.Count; r++)
            {
                float mid = (heights[r] + heights[r + 1]) * .5f / In;
                bool stripe = false;
                foreach (var s in Stripes) stripe |= mid > s.x && mid < s.y;
                var list = stripe ? red : white;
                for (int s = 0; s < segments; s++)
                {
                    int a = r * ring + s, b = a + 1, c = a + ring, d = c + 1;
                    list.Add(a); list.Add(c); list.Add(b);
                    list.Add(b); list.Add(c); list.Add(d);
                }
            }
            // Base cap.
            int centre = verts.Count;
            verts.Add(Vector3.zero); normals.Add(Vector3.down); uvs.Add(new Vector2(.5f, 0));
            int baseStart = verts.Count;
            for (int s = 0; s <= segments; s++)
            {
                verts.Add(verts[s]); normals.Add(Vector3.down); uvs.Add(uvs[s]);
            }
            for (int s = 0; s < segments; s++) { white.Add(centre); white.Add(baseStart + s); white.Add(baseStart + s + 1); }

            var mesh = new Mesh { name = "BowlingPin" };
            mesh.SetVertices(verts); mesh.SetNormals(normals); mesh.SetUVs(0, uvs);
            mesh.subMeshCount = 2;
            mesh.SetTriangles(white, 0); mesh.SetTriangles(red, 1);
            mesh.RecalculateBounds();
            return mesh;
        }

        /// Convex hull approximations of one section of the profile (a stack of rings).
        public static Mesh Hull(float from, float to, int segments = 12, int rings = 5)
        {
            var verts = new List<Vector3>();
            foreach (float h in Rings(from, to, (to - from) / rings))
            {
                float rad = Mathf.Max(Radius(h), .004f);
                for (int s = 0; s < segments; s++)
                {
                    float a = s * 2 * Mathf.PI / segments;
                    verts.Add(new Vector3(Mathf.Cos(a) * rad, h, Mathf.Sin(a) * rad));
                }
            }
            // PhysX cooks the convex hull from the points; triangles only have to exist.
            var tris = new List<int>();
            for (int i = 2; i < verts.Count; i++) { tris.Add(0); tris.Add(i - 1); tris.Add(i); }
            var mesh = new Mesh { name = "BowlingPinHull" };
            mesh.SetVertices(verts); mesh.SetTriangles(tris, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        public static Mesh[] Hulls() => new[]
        {
            Hull(0, BellyHeight),
            Hull(BellyHeight, NeckHeight),
            Hull(NeckHeight, BowlingLane.PinHeight),
        };
    }
}
