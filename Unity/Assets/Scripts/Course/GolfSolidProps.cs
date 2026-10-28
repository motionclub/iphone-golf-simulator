using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Course
{
    /// The ball meets what it sees (Adnan 10-28: the tulip beds on Windmill Links "are a bunch of
    /// colors and the ball goes through them ... that can only happen with leaves and grass").
    ///  - Solid dressing (fences, bridges, jetties, boats, tulip beds, braziers, the landmark kit's
    ///    houses, gazebos, lanterns and gates) gets mesh colliders on its own layer, which the
    ///    ground query never reads (a roof is not ground), and goes into the hole's SolidProps for
    ///    the shot model to bounce off.
    ///  - Render-only rock that dresses the ground (the eroded cliff shell, bluffs at the cliff
    ///    foot, shore boulders, hole 12's chalk faces) gets ground colliders, so a ball dropping over
    ///    an edge lands on the rock it sees instead of sinking through it to the old face behind.
    /// Every collider made here is a child named COLLIDER_…, so the visual dressing gate can tell
    /// them from the hole's own.
    public static class GolfSolidProps
    {
        public const int Layer = 28;
        public const int Mask = 1 << Layer;
        public const string Prefix = "COLLIDER_";

        /// Model meshes that stand solid (course_extras.py names). Trees, bushes, rocks and the
        /// named buildings are already Obstacles; their meshes are added too, so a farmhouse is its
        /// own shape rather than only the round wall ObstacleScan gives it.
        static readonly string[] SolidNames =
        {
            "FENCE", "FLOWERS", "WHITE_BRIDGE", "BRIDGE", "ARCH_BRIDGE", "JETTY", "BOAT", "STAIRS", "BRAZIER", "STACKS",
            "RUIN", "TEMPLE", "WINDMILL", "FARMHOUSE", "CABIN", "LIGHTHOUSE", "TOWER", "CLUBHOUSE", "SNOWMAN",
            "DRESS_ARCH", "DRESS_BLOCK", "DRESS_RUIN", "DRESS_CONE", "DRESS_PADRIM", "TEE_FENCE",
        };

        static readonly Collider[] overlap = new Collider[8];

        /// A fresh registry for `hole`, sweeping a sphere against the solid layer.
        public static SolidProps Registry() => new(Sweep);

        static bool Sweep(double ax, double ay, double ad, double bx, double by, double bd, double r,
            out double along, out double nx, out double ny, out double nd)
        {
            along = 1; nx = ny = nd = 0;
            var a = new Vector3((float)ax, (float)ay, (float)ad);
            var step = new Vector3((float)(bx - ax), (float)(by - ay), (float)(bd - ad));
            float length = step.magnitude;
            if (length < 1e-5f) return false;
            // (a ball already inside one is let go rather than stuck: a sweep can't see out of it)
            if (Physics.OverlapSphereNonAlloc(a, (float)r, overlap, Mask, QueryTriggerInteraction.Ignore) > 0) return false;
            if (!Physics.SphereCast(a, (float)r, step / length, out var hit, length, Mask, QueryTriggerInteraction.Ignore)) return false;
            along = hit.distance / length;
            nx = hit.normal.x; ny = hit.normal.y; nd = hit.normal.z;
            return true;
        }

        /// The model's solid dressing (HoleView, once the model is placed).
        public static void FromModel(Transform model, Hole hole)
        {
            int n = 0;
            foreach (var mf in model.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!mf.sharedMesh || !mf.gameObject.activeInHierarchy || !IsSolid(mf.name)) continue;
                if (Solid(mf, mf.sharedMesh, hole)) n++;
            }
            Physics.SyncTransforms();
            Debug.Log($"[GolfSolidProps] hole {hole.Number}: {n} solid model pieces");
        }

        /// A landmark-kit piece standing on the course (MajesticHoleKit / MajesticCoastKit): its
        /// nearest solid LOD, not its FX cards or impostor.
        public static void FromKit(GameObject piece, Hole hole)
        {
            if (!piece || hole == null) return;
            var filters = piece.GetComponentsInChildren<MeshFilter>(true);
            bool Has(string lod) { foreach (var mf in filters) if (mf.name.Contains(lod)) return true; return false; }
            // the middle LOD where there is one (KeepLod(…, 1) leaves only it), else the full one
            string pick = Has("_LOD1") ? "_LOD1" : Has("_LOD0") ? "_LOD0" : null;
            foreach (var mf in filters)
            {
                if (!mf.sharedMesh) continue;
                string name = mf.name;
                if (pick != null && !name.Contains(pick)) continue;
                if (name.Contains("_FX") || name.Contains("Impostor")) continue;
                if (mf.TryGetComponent<Renderer>(out var r) && r.sharedMaterial && r.sharedMaterial.name.Contains("FX")) continue;
                Solid(mf, mf.sharedMesh, hole);
            }
            Physics.SyncTransforms();
        }

        static bool IsSolid(string name)
        {
            name = name.ToUpperInvariant();
            if (name.StartsWith(Prefix)) return false;
            foreach (var s in SolidNames) if (name.StartsWith(s)) return true;
            return false;
        }

        static bool Solid(MeshFilter mf, Mesh mesh, Hole hole)
        {
            if (mf.transform.Find(Prefix + mf.name)) return false;
            var go = new GameObject(Prefix + mf.name) { layer = Layer };
            go.transform.SetParent(mf.transform, false);
            var c = go.AddComponent<MeshCollider>();
            c.sharedMesh = mesh;
            var b = c.bounds;
            if (b.size.sqrMagnitude < 1e-4f) { Object.Destroy(go); return false; }
            hole.Solids ??= Registry();
            hole.Solids.Add(b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z);
            return true;
        }

        /// A ground collider for render-only rock under `parent` (its local space): the ground query
        /// reads it like the terrain.
        public static MeshCollider Ground(Transform parent, Mesh mesh, string name)
        {
            if (!mesh || mesh.vertexCount == 0) return null;
            var go = new GameObject(Prefix + name);
            go.transform.SetParent(parent, false);
            var c = go.AddComponent<MeshCollider>();
            c.sharedMesh = mesh;
            return c;
        }

        /// The steep faces of `mesh` (world normals more sideways than `maxUp`), as a mesh in the
        /// same local space: a cliff's walls without the turf on its top, which the hole's own
        /// ground already has exactly.
        public static Mesh Faces(Mesh mesh, Transform at, float maxUp)
        {
            if (!mesh || !mesh.isReadable) return null;
            var v = mesh.vertices; var tris = mesh.triangles; var keep = new List<int>();
            for (int t = 0; t + 2 < tris.Length; t += 3)
            {
                var a = at.TransformPoint(v[tris[t]]); var b = at.TransformPoint(v[tris[t + 1]]); var c = at.TransformPoint(v[tris[t + 2]]);
                var n = Vector3.Cross(b - a, c - a); float l = n.magnitude;
                if (l < 1e-8f || Mathf.Abs(n.y / l) > maxUp) continue;
                keep.Add(tris[t]); keep.Add(tris[t + 1]); keep.Add(tris[t + 2]);
            }
            if (keep.Count == 0) return null;
            var m = new Mesh { name = mesh.name + " faces", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            m.SetVertices(v); m.SetTriangles(keep, 0); m.RecalculateBounds();
            return m;
        }
    }
}
