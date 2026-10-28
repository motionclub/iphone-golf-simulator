using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Course
{
    /// Rocks sit on the ground (Adnan 10-19: "remove floating rocks from maps"). Every place that sets a rock down
    /// asks here how far its lowest point is above the ground under it, and lowers it onto the ground when that
    /// gap is more than Gap: the resort dresser's boulders (GolfResortDress), the Majestic scatter's
    /// (MajesticScatter), the dream catalogue's spires and columns (DreamWorldArt) and the rocks baked into the
    /// Blender course models (ROCK_*, HoleView). The gap is measured at the rock's own bottom vertices, each against
    /// the ground straight under it, so a boulder on a slope or against a cliff face counts as floating when no
    /// part of it touches. The sea counts as ground: a stone in the water is not floating. Each check is logged
    /// (Audit) with the gap before and after, for the proof run (work/course-fx).
    public static class RockGrounding
    {
        /// A rock whose lowest point is more than this above the ground floats (yards: about 5 cm).
        public const float Gap = .055f;
        /// How far a lowered rock is set into the ground, so it reads as bedded rather than balanced.
        public const float Bed = .08f;
        public const float SeaLevel = 0f;

        public struct Entry { public int Hole; public string Source; public Vector3 At; public float Before, After; }
        public static readonly List<Entry> Audit = new();
        /// Off (ROCK_SNAP=0) only for measuring the "before".
        public static bool Snap = System.Environment.GetEnvironmentVariable("ROCK_SNAP") != "0";
        public static int Hole;
        /// Keep the log (the proof run turns it on; a round does not need it).
        public static bool Recording;

        static readonly RaycastHit[] hits = new RaycastHit[16];
        static readonly List<Vector3> vertices = new();

        /// The ground straight under (x, z): the highest collider that is not water, never below the sea.
        public static float GroundAt(float x, float z)
        {
            float best = SeaLevel;
            int n = Physics.RaycastNonAlloc(new Vector3(x, 600, z), Vector3.down, hits, 1200, ~GolfSolidProps.Mask, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < n; i++)
            {
                var c = hits[i].collider; if (!c) continue;
                var nm = c.name;
                if (nm.Contains("WATER") || nm.Contains("Water") || nm.Contains("sea") || nm.Contains("Sea") || nm.StartsWith("Majestic")) continue;
                if (hits[i].point.y > best) best = hits[i].point.y;
            }
            return best;
        }

        /// How far the lowest part of `mesh` (placed by `toWorld`) is above the ground: the smallest of
        /// (vertex height − ground under it) over its bottom vertices (up to 32). Negative: it is set into the ground.
        public static float Clearance(Mesh mesh, Matrix4x4 toWorld)
        {
            if (!mesh) return 0;
            if (!mesh.isReadable) return ClearanceOfBounds(toWorld.MultiplyPoint3x4(mesh.bounds.center), Vector3.Scale(mesh.bounds.extents, toWorld.lossyScale));
            mesh.GetVertices(vertices);
            if (vertices.Count == 0) return 0;
            float low = float.MaxValue, high = float.MinValue;
            foreach (var v in vertices) { float y = toWorld.MultiplyPoint3x4(v).y; low = Mathf.Min(low, y); high = Mathf.Max(high, y); }
            float band = low + (high - low) * .3f;   // the bottom third: what could rest on the ground
            int bottom = 0; foreach (var v in vertices) if (toWorld.MultiplyPoint3x4(v).y <= band) bottom++;
            int stride = Mathf.Max(1, bottom / 32), k = 0;
            float clearance = float.MaxValue;
            foreach (var v in vertices)
            {
                var w = toWorld.MultiplyPoint3x4(v);
                if (w.y > band || k++ % stride != 0) continue;
                clearance = Mathf.Min(clearance, w.y - GroundAt(w.x, w.z));
            }
            return clearance == float.MaxValue ? 0 : clearance;
        }

        /// For a shape with no readable mesh: its bottom face's middle and four corners over the ground.
        public static float ClearanceOfBounds(Vector3 centre, Vector3 extents)
        {
            float bottom = centre.y - extents.y, clearance = float.MaxValue;
            for (int i = 0; i < 5; i++)
            {
                float x = centre.x + (i == 0 ? 0 : (i % 2 == 0 ? 1 : -1) * extents.x * .6f), z = centre.z + (i == 0 ? 0 : (i < 3 ? 1 : -1) * extents.z * .6f);
                clearance = Mathf.Min(clearance, bottom - GroundAt(x, z));
            }
            return clearance;
        }

        /// A gap bigger than this is not a rock in the air but one standing on ground the game has no collider for (the
        /// Crater's basalt walls on LavaWorld's rim, 20-48 yd over the lava): it is left where it is, and logged.
        public const float MaxSnap = 2.5f;

        /// How far to lower a rock that is `clearance` above the ground (0 if it touches), logged as `source`.
        public static float Settle(string source, Vector3 at, float clearance)
        {
            float drop = Snap && clearance > Gap && clearance <= MaxSnap ? clearance + Bed : 0;
            if (Recording) Audit.Add(new Entry { Hole = Hole, Source = source, At = at, Before = clearance, After = clearance - drop });
            return drop;
        }

        /// The same for a mesh rock: measure it and say how far to lower it.
        public static float Settle(string source, Mesh mesh, Matrix4x4 toWorld) =>
            Settle(source, toWorld.MultiplyPoint3x4(mesh ? mesh.bounds.center : Vector3.zero), Clearance(mesh, toWorld));

        /// Is this model node one of the course's own rocks (blender phase7_rocks: ROCK_*, BOULDER_*)? The cliffs'
        /// own boulders (CLIFF_ROCK) are part of the shore and stand in the sea.
        public static bool IsModelRock(string name) => name.StartsWith("ROCK") || name.StartsWith("BOULDER") || name.StartsWith("STONE_");

        /// Lower every rock of a course model onto the ground under it (before the obstacles are read off it).
        public static int SettleModel(Transform model, int hole)
        {
            Hole = hole; int lowered = 0;
            foreach (var mf in model.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!IsModelRock(mf.name) || !mf.sharedMesh) continue;
                float drop = Settle("model " + mf.name, mf.sharedMesh, mf.transform.localToWorldMatrix);
                if (drop <= 0) continue;
                mf.transform.position -= Vector3.up * drop; lowered++;
            }
            return lowered;
        }
    }
}
