using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Quadric-error decimation for MajesticCrowd's lod path, run once per source mesh and cached. Half-edge collapses
    /// only: every kept vertex keeps its authored position, normal and palette colour (the spectator shader reads the
    /// surface role from vertex alpha), so the result is a subset of the source vertices with a new index buffer.
    /// A collapse is refused when it would pull an open border or a colour/normal seam off its line, pinch the surface
    /// (link condition) or flip a face.
    public static class MajesticMeshLod
    {
        static readonly Dictionary<(Mesh, int), Mesh> cache = new();
        // the decimation only reads positions and the index buffer (a seam is a vertex split), so fans that share a
        // shape and differ in palette share one plan: FAN_0/2/4 and FAN_1/3/5 decimate once each
        static readonly Dictionary<(ulong, int, int), (List<int> keep, List<int>[] lists)> plans = new();

        /// `src` cut to about `targetTris` triangles (cached; meshes already at or under the target come back as is).
        public static Mesh Decimated(Mesh src, int targetTris)
        {
            if (!src || !src.isReadable || Tris(src) <= targetTris) return src;
            if (cache.TryGetValue((src, targetTris), out var m) && m) return m;
            m = Decimate(src, targetTris);
            m.hideFlags = HideFlags.DontUnloadUnusedAsset;   // venues rebuild their crowd from the cache
            cache[(src, targetTris)] = m;
            return m;
        }

        public static long Tris(Mesh m) { long t = 0; for (int k = 0; k < m.subMeshCount; k++) t += m.GetIndexCount(k) / 3; return t; }

        public static Mesh Decimate(Mesh src, int targetTris)
        {
            var verts = src.vertices;
            var tris = new int[src.subMeshCount][];
            ulong sig = 1469598103934665603;
            void Mix(int x) { sig = (sig ^ (uint)x) * 1099511628211; }
            foreach (var v in verts) { Mix(v.x.GetHashCode()); Mix(v.y.GetHashCode()); Mix(v.z.GetHashCode()); }
            for (int s = 0; s < tris.Length; s++) { tris[s] = src.GetTriangles(s); Mix(-1); foreach (int i in tris[s]) Mix(i); }
            if (!plans.TryGetValue((sig, verts.Length, targetTris), out var plan))
                plans[(sig, verts.Length, targetTris)] = plan = Plan(verts, tris, targetTris);
            var (keep, lists) = plan;
            var mesh = new Mesh { name = src.name + "_LOD", indexFormat = keep.Count > 65535 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16 };
            mesh.SetVertices(Pick(verts, keep));
            var normals = src.normals; if (normals.Length == verts.Length) mesh.SetNormals(Pick(normals, keep));
            var tangents = src.tangents; if (tangents.Length == verts.Length) mesh.SetTangents(Pick(tangents, keep));
            var colors = src.colors32; if (colors.Length == verts.Length) mesh.SetColors(Pick(colors, keep));
            var uv = new List<Vector2>();
            for (int ch = 0; ch < 4; ch++) { src.GetUVs(ch, uv); if (uv.Count == verts.Length) mesh.SetUVs(ch, Pick(uv.ToArray(), keep)); }
            mesh.subMeshCount = lists.Length;
            for (int s = 0; s < lists.Length; s++) mesh.SetTriangles(lists[s], s, false);
            mesh.bounds = src.bounds;   // same pivots and placement as the source part
            return mesh;
        }

        /// which source vertices survive, and the new index lists per submesh
        static (List<int> keep, List<int>[] lists) Plan(Vector3[] verts, int[][] tris, int targetTris)
        {
            // weld by position: the importer splits vertices at colour/normal seams; topology works on positions,
            // attributes stay per face corner (the source vertex index)
            var posId = new Dictionary<Vector3, int>(); var posOf = new int[verts.Length]; var pos = new List<Vector3>();
            for (int i = 0; i < verts.Length; i++)
            {
                if (!posId.TryGetValue(verts[i], out int p)) { p = pos.Count; posId[verts[i]] = p; pos.Add(verts[i]); }
                posOf[i] = p;
            }
            var corner = new List<int>(); var sub = new List<int>();
            for (int s = 0; s < tris.Length; s++)
            {
                var idx = tris[s];
                for (int i = 0; i < idx.Length; i += 3)
                {
                    int a = posOf[idx[i]], b = posOf[idx[i + 1]], c = posOf[idx[i + 2]];
                    if (a == b || b == c || a == c) continue;
                    corner.Add(idx[i]); corner.Add(idx[i + 1]); corner.Add(idx[i + 2]); sub.Add(s);
                }
            }
            var d = new Decimator(pos, posOf, corner.ToArray());
            d.Run(targetTris);

            var remap = new Dictionary<int, int>(); var keep = new List<int>();
            var lists = new List<int>[tris.Length];
            for (int s = 0; s < lists.Length; s++) lists[s] = new List<int>();
            for (int f = 0; f < sub.Count; f++)
            {
                if (d.dead[f]) continue;
                for (int k = 0; k < 3; k++)
                {
                    int u = d.corner[f * 3 + k];
                    if (!remap.TryGetValue(u, out int n)) { n = keep.Count; remap[u] = n; keep.Add(u); }
                    lists[sub[f]].Add(n);
                }
            }
            return (keep, lists);
        }

        static T[] Pick<T>(T[] a, List<int> keep) { var r = new T[keep.Count]; for (int i = 0; i < r.Length; i++) r[i] = a[keep[i]]; return r; }

        sealed class Decimator
        {
            readonly List<Vector3> pos; readonly int[] posOf;
            public readonly int[] corner; public readonly bool[] dead;
            readonly List<int>[] faces;
            readonly double[][] q;
            readonly int[] stamp;
            readonly List<(double cost, int v, int w, int stamp)> heap = new();
            int alive;

            public Decimator(List<Vector3> pos, int[] posOf, int[] corner)
            {
                this.pos = pos; this.posOf = posOf; this.corner = corner;
                int nf = corner.Length / 3; dead = new bool[nf]; alive = nf;
                faces = new List<int>[pos.Count]; q = new double[pos.Count][]; stamp = new int[pos.Count];
                for (int p = 0; p < pos.Count; p++) { faces[p] = new List<int>(6); q[p] = new double[10]; }
                var edges = new Dictionary<long, (int f0, int f1, int n)>();
                for (int f = 0; f < nf; f++)
                {
                    Vector3 a = P(f, 0), b = P(f, 1), c = P(f, 2);
                    var n = Vector3.Cross(b - a, c - a); float area = n.magnitude * .5f;
                    if (area > 0) { n /= area * 2; for (int k = 0; k < 3; k++) AddPlane(q[Pid(f, k)], n, Vector3.Dot(n, a), area); }
                    for (int k = 0; k < 3; k++)
                    {
                        faces[Pid(f, k)].Add(f);
                        long key = EdgeKey(Pid(f, k), Pid(f, (k + 1) % 3));
                        edges[key] = edges.TryGetValue(key, out var e) ? (e.f0, f, e.n + 1) : (f, -1, 1);
                    }
                }
                // open borders and attribute seams get planes standing on the edge, so collapses keep their line
                foreach (var kv in edges)
                {
                    int pa = (int)(kv.Key >> 32), pb = (int)(kv.Key & 0xffffffff); var (f0, f1, cnt) = kv.Value;
                    bool hard = cnt != 2 || Attr(f0, pa) != Attr(f1, pa) || Attr(f0, pb) != Attr(f1, pb);
                    if (!hard) continue;
                    foreach (int f in cnt == 2 ? new[] { f0, f1 } : new[] { f0 })
                    {
                        // (the parts are authored small and scaled up by their nodes: Vector3.normalized would zero these)
                        Vector3 a = P(f, 0), fn = Unit(Vector3.Cross(P(f, 1) - a, P(f, 2) - a));
                        Vector3 e = pos[pb] - pos[pa]; var n = Unit(Vector3.Cross(e, fn));
                        if (n == Vector3.zero) continue;
                        double w = 8 * e.sqrMagnitude;
                        AddPlane(q[pa], n, Vector3.Dot(n, pos[pa]), w); AddPlane(q[pb], n, Vector3.Dot(n, pos[pa]), w);
                    }
                }
            }

            int Pid(int f, int k) => posOf[corner[f * 3 + k]];
            Vector3 P(int f, int k) => pos[Pid(f, k)];
            static Vector3 Unit(Vector3 v) { float m = v.magnitude; return m > 0 ? v / m : Vector3.zero; }
            static long EdgeKey(int a, int b) => a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a;
            int Attr(int f, int p) { for (int k = 0; k < 3; k++) if (Pid(f, k) == p) return corner[f * 3 + k]; return -1; }
            bool Has(int f, int p) => Pid(f, 0) == p || Pid(f, 1) == p || Pid(f, 2) == p;

            static void AddPlane(double[] m, Vector3 n, float dist, double w)
            {
                double a = n.x, b = n.y, c = n.z, d = -dist;
                m[0] += w * a * a; m[1] += w * a * b; m[2] += w * a * c; m[3] += w * a * d;
                m[4] += w * b * b; m[5] += w * b * c; m[6] += w * b * d;
                m[7] += w * c * c; m[8] += w * c * d; m[9] += w * d * d;
            }

            static double Error(double[] m1, double[] m2, Vector3 p)
            {
                double x = p.x, y = p.y, z = p.z, e = 0;
                for (int pass = 0; pass < 2; pass++)
                {
                    var m = pass == 0 ? m1 : m2;
                    e += m[0] * x * x + 2 * m[1] * x * y + 2 * m[2] * x * z + 2 * m[3] * x
                       + m[4] * y * y + 2 * m[5] * y * z + 2 * m[6] * y + m[7] * z * z + 2 * m[8] * z + m[9];
                }
                return e;
            }

            void Live(int p)
            {
                var l = faces[p]; int n = 0;
                for (int i = 0; i < l.Count; i++) if (!dead[l[i]]) l[n++] = l[i];
                l.RemoveRange(n, l.Count - n);
            }

            void Neighbours(int p, HashSet<int> into)
            {
                into.Clear();
                foreach (int f in faces[p]) for (int k = 0; k < 3; k++) { int x = Pid(f, k); if (x != p) into.Add(x); }
            }

            readonly HashSet<int> nv = new(), nw = new();
            readonly Dictionary<int, int> map = new();

            /// can v collapse onto w? fills `map` (v's corner attributes -> w's on the same side)
            bool Valid(int v, int w)
            {
                map.Clear(); int shared = 0;
                foreach (int f in faces[v]) if (Has(f, w)) { shared++; map.TryAdd(Attr(f, v), Attr(f, w)); }
                if (shared == 0 || shared > 2) return false;
                // a border vertex only slides along its border
                Neighbours(v, nv);
                foreach (int x in nv)
                {
                    int c = 0; foreach (int f in faces[v]) if (Has(f, x)) c++;
                    if (c == 1 && shared != 1) return false;
                }
                // link condition: v and w share only the opposite corners of the faces on their edge
                Neighbours(w, nw); int common = 0;
                foreach (int x in nv) if (nw.Contains(x)) common++;
                if (common != shared) return false;
                foreach (int f in faces[v])
                {
                    if (Has(f, w)) continue;
                    // a seam vertex only collapses along its seam: every corner attribute of v must reappear on the edge
                    if (!map.ContainsKey(Attr(f, v))) return false;
                    Vector3 a = P(f, 0), b = P(f, 1), c = P(f, 2);
                    var before = Vector3.Cross(b - a, c - a);
                    Vector3 a2 = Pid(f, 0) == v ? pos[w] : a, b2 = Pid(f, 1) == v ? pos[w] : b, c2 = Pid(f, 2) == v ? pos[w] : c;
                    var after = Vector3.Cross(b2 - a2, c2 - a2);
                    double bb = before.sqrMagnitude, aa = after.sqrMagnitude;
                    if (aa < 1e-6 * bb || Vector3.Dot(before, after) < .3 * System.Math.Sqrt(aa * bb)) return false;
                }
                return true;
            }

            readonly HashSet<int> scratch = new();
            readonly List<int> touched = new();

            void Push(int v)
            {
                stamp[v]++;
                if (faces[v].Count == 0) return;
                Neighbours(v, scratch);
                double best = double.MaxValue; int bw = -1;
                foreach (int w in scratch)
                {
                    double e = Error(q[v], q[w], pos[w]);
                    if (e < best && Valid(v, w)) { best = e; bw = w; }
                }
                if (bw >= 0) HeapPush((best, v, bw, stamp[v]));
            }

            public void Run(int target)
            {
                for (int p = 0; p < pos.Count; p++) Push(p);
                while (alive > target && heap.Count > 0)
                {
                    var (_, v, w, st) = HeapPop();
                    if (st != stamp[v] || faces[v].Count == 0 || faces[w].Count == 0) continue;
                    if (!Valid(v, w)) { Push(v); continue; }
                    foreach (int f in faces[v])
                    {
                        if (Has(f, w)) { dead[f] = true; alive--; continue; }
                        for (int k = 0; k < 3; k++)
                            if (Pid(f, k) == v) corner[f * 3 + k] = map[corner[f * 3 + k]];
                        faces[w].Add(f);
                    }
                    faces[v].Clear();
                    for (int i = 0; i < 10; i++) q[w][i] += q[v][i];
                    Live(w);
                    Neighbours(w, nw);
                    touched.Clear(); touched.AddRange(nw); touched.Add(w);
                    foreach (int x in touched) { Live(x); Push(x); }
                }
            }

            void HeapPush((double, int, int, int) e)
            {
                heap.Add(e); int i = heap.Count - 1;
                while (i > 0) { int p = (i - 1) / 2; if (heap[p].cost <= heap[i].cost) break; (heap[p], heap[i]) = (heap[i], heap[p]); i = p; }
            }

            (double cost, int v, int w, int stamp) HeapPop()
            {
                var top = heap[0]; int last = heap.Count - 1; heap[0] = heap[last]; heap.RemoveAt(last);
                int i = 0;
                while (true)
                {
                    int l = i * 2 + 1, r = l + 1, m = i;
                    if (l < heap.Count && heap[l].cost < heap[m].cost) m = l;
                    if (r < heap.Count && heap[r].cost < heap[m].cost) m = r;
                    if (m == i) break;
                    (heap[m], heap[i]) = (heap[i], heap[m]); i = m;
                }
                return top;
            }
        }
    }
}
