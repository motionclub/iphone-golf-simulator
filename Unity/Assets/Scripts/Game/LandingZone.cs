using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Game
{
    /// The landing zone in the course view: an amber ring on the ground where a full swing
    /// comes down, with a soft fill, breathing slowly so the eye finds it. Amber is the target's
    /// own colour — the callout's yardage matches it — kept apart from the sky accent.
    public sealed class LandingZone : MonoBehaviour
    {
        public static readonly Color Amber = new(1f, 0.72f, 0.25f);
        Mesh mesh;
        float radius = 3f;

        public static LandingZone Create(Transform parent)
        {
            var go = new GameObject("Landing zone") { layer = BallLook.OverlayLayer };
            go.transform.SetParent(parent, false);
            var z = go.AddComponent<LandingZone>();
            z.mesh = new Mesh { name = "Landing zone" };
            go.AddComponent<MeshFilter>().mesh = z.mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = GreenRead.Material();
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            z.Build(1f);
            return z;
        }

        /// Where the shot can come down rather than one spot: an ellipse `across` yards either
        /// side of the line and `along` yards short and long of the ring's centre, turned to the
        /// aim `heading` (degrees, 0 = +z) — the same zone the minimap draws.
        public void SetZone(float across, float along, float heading)
        {
            radius = Mathf.Max(1.5f, Mathf.Max(across, along));
            transform.localScale = new Vector3(Mathf.Max(1.5f, across), 1f, Mathf.Max(1.5f, along));
            transform.rotation = Quaternion.Euler(0, heading, 0);
        }

        // The ring is built once; each frame only its outer edge moves with the pulse (11-22: the whole mesh, its lists and 112 small
        // arrays were rebuilt every frame while aiming, most of golf's garbage).
        const int Segs = 56;
        Vector3[] verts; int ringStart; Renderer view;

        void Build(float pulse)
        {
            var colors = new List<Color>(); var tris = new List<int>(); var v = new List<Vector3>();
            // soft fill
            var fill = Amber; fill.a = 0.16f;
            v.Add(Vector3.zero); colors.Add(fill);
            for (int i = 0; i <= Segs; i++)
            {
                float a = i * Mathf.PI * 2 / Segs;
                v.Add(new Vector3(Mathf.Cos(a) * 0.86f, 0, Mathf.Sin(a) * 0.86f)); colors.Add(fill);
            }
            for (int i = 1; i <= Segs; i++) tris.AddRange(new[] { 0, i, i + 1 });
            // the ring, a band whose width breathes
            float inner = 0.86f;
            var ring = Amber; ring.a = 0.95f;
            ringStart = v.Count;
            for (int i = 0; i <= Segs; i++)
            {
                float a = i * Mathf.PI * 2 / Segs;
                v.Add(new Vector3(Mathf.Cos(a) * inner, 0, Mathf.Sin(a) * inner)); colors.Add(ring);
                v.Add(Vector3.zero); colors.Add(ring);   // (the outer edge: Pulse)
            }
            for (int i = 0; i < Segs; i++)
            {
                int k = ringStart + i * 2;
                tris.AddRange(new[] { k, k + 2, k + 1, k + 1, k + 2, k + 3 });
            }
            verts = v.ToArray();
            mesh.Clear();
            mesh.vertices = verts; mesh.SetColors(colors); mesh.SetTriangles(tris, 0);
            Pulse(pulse);
        }

        void Pulse(float pulse)
        {
            float outer = 1f + 0.06f * pulse;
            for (int i = 0; i <= Segs; i++)
            {
                float a = i * Mathf.PI * 2 / Segs;
                verts[ringStart + i * 2 + 1] = new Vector3(Mathf.Cos(a) * outer, 0, Mathf.Sin(a) * outer);
            }
            mesh.vertices = verts;
            mesh.RecalculateBounds();
        }

        void Update()
        {
            if (!view) view = GetComponent<Renderer>();
            view.enabled = GolfArcade.EnvironmentArt.DreamVisibility.Visible(transform.position);
            Pulse(0.5f + 0.5f * Mathf.Sin(Time.time * 2.2f));
        }
    }
}
