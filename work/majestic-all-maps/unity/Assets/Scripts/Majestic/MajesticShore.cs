using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Majestic
{
    /// Island edges (chat 10, PLAN §4.1; targets refs/holes/*_flyOpen.jpg): every sea hole's coastline gets a turquoise
    /// shallows band fading out to the deep sea and a soft animated foam ring, so no island edge reads as a bare bevel on a
    /// flat teal plane. The coastline is found by raycasting the ground on a grid round the hole (land = ground clearly above
    /// the sea), traced with marching squares and smoothed. Two meshes, one transparent material, ~1-3 k triangles.
    public static class MajesticShore
    {
        const float Step = 3f, Margin = 70f, ShallowWidth = 22f, FoamWidth = 4.5f;
        static Material material;
        static int lastLand, lastCells;
        /// The coastlines of the last Build (MajesticCoastKit lays the kit's shore tiles along them).
        public static List<List<Vector3>> LastLines = new();

        public static void Build(Transform root, MajesticLook look, Bounds course, float seaY)
        {
            var lines = Coast(course, seaY); LastLines = lines;
            int pts = 0; foreach (var l in lines) pts += l.Count;
            Debug.Log($"[MajesticShore] bounds {course.min}-{course.max} seaY {seaY}: {lines.Count} coastlines, {pts} points, land cells {lastLand}/{lastCells}");
            if (lines.Count == 0) return;
            if (!material)
            {
                var sh = Shader.Find("GolfArcade/MajesticFoam"); if (!sh) return;
                material = new Material(sh) { name = "Majestic shore", renderQueue = 2990 };
            }
            material.SetColor("_Shallow", look.SeaShallow == default ? new Color(.12f, .8f, .8f) : look.SeaShallow);
            var verts = new List<Vector3>(); var cols = new List<Color>(); var uvs = new List<Vector2>(); var tris = new List<int>();
            foreach (var line in lines)
            {
                if (line.Count < 6) continue;
                float along = 0;
                for (int i = 0; i < line.Count; i++)
                {
                    var p = line[i];
                    var prev = line[Mathf.Max(0, i - 1)]; var next = line[Mathf.Min(line.Count - 1, i + 1)];
                    var t = (next - prev); t.y = 0; t.Normalize();
                    var n = new Vector3(t.z, 0, -t.x);                           // outward = right of the walking direction
                    if (Land(p + n * 4, seaY)) n = -n;                            // the line is walked either way round
                    if (i > 0) along += Vector3.Distance(line[i - 1], p);
                    // rows: inland lip (-1.2), coast (0), foam edge, shallow fade (+ShallowWidth)
                    float[] off = { -1.2f, 0, FoamWidth, ShallowWidth * .5f, ShallowWidth };
                    float[] foamW = { 1, 1, 0, 0, 0 };
                    float[] shallowA = { 1, 1, .85f, .45f, 0 };
                    for (int k = 0; k < off.Length; k++)
                    {
                        var q = p + n * off[k]; q.y = seaY + .04f + (k == 0 ? .06f : 0);
                        verts.Add(q); cols.Add(new Color(foamW[k], shallowA[k], 0, 1)); uvs.Add(new Vector2(along / 6f, off[k] / FoamWidth));
                    }
                    if (i > 0)
                    {
                        int a = verts.Count - 10, b = verts.Count - 5;
                        for (int k = 0; k < 4; k++) { tris.Add(a + k); tris.Add(b + k); tris.Add(a + k + 1); tris.Add(a + k + 1); tris.Add(b + k); tris.Add(b + k + 1); }
                    }
                }
            }
            if (tris.Count == 0) return;
            var mesh = new Mesh { name = "Majestic shore", indexFormat = verts.Count > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
            mesh.SetVertices(verts); mesh.SetColors(cols); mesh.SetUVs(0, uvs); mesh.SetTriangles(tris, 0, true);
            var normals = new Vector3[verts.Count]; for (int i = 0; i < normals.Length; i++) normals[i] = Vector3.up; mesh.normals = normals;
            var go = new GameObject("Majestic shore"); go.transform.SetParent(root, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>(); r.sharedMaterial = material;
            r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; r.lightProbeUsage = LightProbeUsage.Off;
        }

        static readonly RaycastHit[] hits = new RaycastHit[8];
        static bool Land(Vector3 p, float seaY)
        {
            int n = Physics.RaycastNonAlloc(new Vector3(p.x, 400, p.z), Vector3.down, hits, 800, ~0, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < n; i++)
            {
                var c = hits[i].collider; if (!c) continue;
                if (c.name.Contains("sea") || c.name.Contains("Sea") || c.name.Contains("WATER") || c.name.Contains("Water")) continue;
                if (hits[i].point.y > seaY + .6f) return true;
            }
            return false;
        }

        /// Coastlines as smoothed polylines (marching squares over a land mask round the course).
        static List<List<Vector3>> Coast(Bounds course, float seaY)
        {
            var min = course.min - new Vector3(Margin, 0, Margin); var max = course.max + new Vector3(Margin, 0, Margin);
            int nx = Mathf.Clamp(Mathf.CeilToInt((max.x - min.x) / Step), 2, 600), nz = Mathf.Clamp(Mathf.CeilToInt((max.z - min.z) / Step), 2, 600);
            var land = new bool[nx + 1, nz + 1];
            lastLand = 0; lastCells = (nx + 1) * (nz + 1);
            for (int i = 0; i <= nx; i++) for (int j = 0; j <= nz; j++) { land[i, j] = Land(new Vector3(min.x + i * Step, 0, min.z + j * Step), seaY); if (land[i, j]) lastLand++; }
            Vector3 P(float i, float j) => new(min.x + i * Step, seaY, min.z + j * Step);
            // segments per cell; edge midpoints keyed so they chain
            var next = new Dictionary<long, long>(); var pos = new Dictionary<long, Vector3>();
            long Key(int i, int j, int e) => ((long)i * 4096 + j) * 4 + e;   // e: 0 bottom, 1 right (stored as left of i+1), ...
            long EdgeKey(int i, int j, int side)
            {
                // canonical: horizontal edges keyed by their lower-left cell's bottom, vertical by their left
                return side switch { 0 => Key(i, j, 0), 2 => Key(i, j + 1, 0), 3 => Key(i, j, 1), _ => Key(i + 1, j, 1) };
            }
            Vector3 Mid(int i, int j, int side) => side switch { 0 => P(i + .5f, j), 2 => P(i + .5f, j + 1), 3 => P(i, j + .5f), _ => P(i + 1, j + .5f) };
            for (int i = 0; i < nx; i++)
                for (int j = 0; j < nz; j++)
                {
                    int c = (land[i, j] ? 1 : 0) | (land[i + 1, j] ? 2 : 0) | (land[i + 1, j + 1] ? 4 : 0) | (land[i, j + 1] ? 8 : 0);
                    if (c == 0 || c == 15) continue;
                    var segs = Cases(c);
                    foreach (var (s0, s1) in segs)
                    {
                        long a = EdgeKey(i, j, s0), b = EdgeKey(i, j, s1);
                        pos[a] = Mid(i, j, s0); pos[b] = Mid(i, j, s1);
                        next[a] = b;
                    }
                }
            var lines = new List<List<Vector3>>(); var used = new HashSet<long>();
            foreach (var start in next.Keys)
            {
                if (used.Contains(start)) continue;
                var line = new List<Vector3>(); long k = start;
                while (!used.Contains(k) && next.ContainsKey(k)) { used.Add(k); line.Add(pos[k]); k = next[k]; }
                if (line.Count > 4) lines.Add(Smooth(Smooth(line)));
            }
            return lines;
        }

        // marching-squares segments: sides 0 bottom, 1 right, 2 top, 3 left; walk so land is on the left
        static (int, int)[] Cases(int c) => c switch
        {
            1 => new[] { (3, 0) }, 2 => new[] { (0, 1) }, 3 => new[] { (3, 1) }, 4 => new[] { (1, 2) },
            5 => new[] { (3, 2), (1, 0) }, 6 => new[] { (0, 2) }, 7 => new[] { (3, 2) }, 8 => new[] { (2, 3) },
            9 => new[] { (2, 0) }, 10 => new[] { (0, 3), (2, 1) }, 11 => new[] { (2, 1) }, 12 => new[] { (1, 3) },
            13 => new[] { (1, 0) }, 14 => new[] { (0, 3) }, _ => new (int, int)[0],
        };

        static List<Vector3> Smooth(List<Vector3> l)
        {
            var o = new List<Vector3>(l.Count * 2) { l[0] };
            for (int i = 0; i < l.Count - 1; i++) { o.Add(Vector3.Lerp(l[i], l[i + 1], .25f)); o.Add(Vector3.Lerp(l[i], l[i + 1], .75f)); }
            o.Add(l[^1]); return o;
        }
    }
}
