// CHARACTER LOD (2026-10-17): index-only mesh simplification for the heroes.
// Every LOD triangle references an ORIGINAL vertex, so skin weights, bind poses, blendshapes (garment correctives, blink),
// normals and UVs stay exactly the ones of LOD0. Half-edge collapse with quadric error (area-weighted face planes plus
// constraint planes on borders and attribute seams), meshoptimizer-style vertex kinds (manifold / border / seam / locked),
// a feature penalty (skin weights, blendshape deltas, normals) and a flip test. Pure C# with no UnityEngine types: it runs
// on a worker thread at runtime and under plain mono for the offline tests (work/character-lod/test).
using System;
using System.Collections.Generic;

namespace GolfArcade.CharacterLod
{
    public static class HeroLodSimplifier
    {
        public sealed class Input
        {
            public float[] positions;      // 3 per vertex (bind space, metres)
            public int[][] submeshes;      // triangle lists per submesh
            public float[] features;       // optional, featureDim per vertex: penalty = |f_a - f_b|^2 (metres^2 units)
            public int featureDim;
        }

        public sealed class Result
        {
            public int[][] submeshes;
            public int triangles;
            public double maxError;        // metres (sqrt of the largest accepted collapse cost)
            public int passes;
        }

        const byte Manifold = 0, Border = 1, Seam = 2, Locked = 3;

        /// Simplify to at most `targetRatio` of the triangles, never accepting a collapse whose cost exceeds `maxError` metres.
        public static Result Simplify(Input input, double targetRatio, double maxError)
        {
            var P = input.positions; int nv = P.Length / 3;
            // ---- weld positions (attribute copies of one point share a position id) ----
            var pid = new int[nv]; var key = new Dictionary<(int, int, int), int>();
            var ppos = new List<double>();
            for (int v = 0; v < nv; v++)
            {
                var k = (Q(P[3 * v]), Q(P[3 * v + 1]), Q(P[3 * v + 2]));
                if (!key.TryGetValue(k, out int id)) { id = key.Count; key[k] = id; ppos.Add(P[3 * v]); ppos.Add(P[3 * v + 1]); ppos.Add(P[3 * v + 2]); }
                pid[v] = id;
            }
            int np = key.Count; var pp = ppos.ToArray();
            // ---- triangles ----
            var tv = new List<int>(); var tsm = new List<int>();
            for (int s = 0; s < input.submeshes.Length; s++)
            {
                var ix = input.submeshes[s];
                for (int i = 0; i + 2 < ix.Length; i += 3)
                {
                    int a = ix[i], b = ix[i + 1], c = ix[i + 2];
                    if (pid[a] == pid[b] || pid[b] == pid[c] || pid[a] == pid[c]) continue;
                    tv.Add(a); tv.Add(b); tv.Add(c); tsm.Add(s);
                }
            }
            var T = tv.ToArray(); var SM = tsm.ToArray(); int nt = SM.Length;
            var alive = new bool[nt]; for (int t = 0; t < nt; t++) alive[t] = true;
            int liveTris = nt, target = Math.Max(1, (int)(nt * targetRatio));
            // ---- quadrics on position ids: face planes (area weighted) ----
            var Qd = new double[np * 11];   // 10 symmetric terms + weight
            for (int t = 0; t < nt; t++)
            {
                int a = pid[T[3 * t]], b = pid[T[3 * t + 1]], c = pid[T[3 * t + 2]];
                Plane(pp, a, b, c, out double nx, out double ny, out double nz, out double d, out double area);
                if (area <= 0) continue;
                AddPlane(Qd, a, nx, ny, nz, d, area); AddPlane(Qd, b, nx, ny, nz, d, area); AddPlane(Qd, c, nx, ny, nz, d, area);
            }
            var features = input.features; int fd = input.featureDim;
            double maxCost = maxError * maxError; double worst = 0; int passes = 0;
            var kind = new byte[np];
            bool constraintsAdded = false;
            while (liveTris > target && passes < 64)
            {
                passes++;
                // ---- adjacency (CSR of live triangles per position id) ----
                var cnt = new int[np + 1];
                for (int t = 0; t < nt; t++) if (alive[t]) for (int c = 0; c < 3; c++) cnt[pid[T[3 * t + c]] + 1]++;
                for (int i = 0; i < np; i++) cnt[i + 1] += cnt[i];
                var adj = new int[cnt[np]]; var fill = (int[])cnt.Clone();
                for (int t = 0; t < nt; t++) if (alive[t]) for (int c = 0; c < 3; c++) adj[fill[pid[T[3 * t + c]]]++] = t;
                // ---- edges: position-id pair -> up to two (triangle) owners ----
                var edges = new EdgeTable(T, pid, alive, nt);
                // ---- vertex kinds ----
                var borderN = new int[np]; var seamN = new int[np]; var complexV = new bool[np];
                foreach (var kv in edges.All())
                {
                    int a = (int)(kv.Key >> 32), b = (int)(kv.Key & 0xffffffff); var e = kv.Value;
                    if (e.count > 2) { complexV[a] = complexV[b] = true; continue; }
                    if (e.count == 1) { borderN[a]++; borderN[b]++; continue; }
                    if (IsSeam(T, SM, pid, e.t0, e.t1, a, b)) { seamN[a]++; seamN[b]++; }
                }
                for (int p = 0; p < np; p++)
                {
                    if (complexV[p]) { kind[p] = Locked; continue; }
                    if (borderN[p] > 0) kind[p] = (borderN[p] == 2 && seamN[p] == 0) ? Border : Locked;
                    else if (seamN[p] > 0) kind[p] = seamN[p] == 2 ? Seam : Locked;
                    else kind[p] = Manifold;
                    if (kind[p] == Manifold || kind[p] == Border)
                    {
                        // one attribute copy expected around a manifold / border point
                        int v0 = -1;
                        for (int i = cnt[p]; i < cnt[p + 1]; i++) { int v = CornerOf(T, pid, adj[i], p); if (v0 < 0) v0 = v; else if (v != v0) { kind[p] = Locked; break; } }
                    }
                }
                if (!constraintsAdded)
                {
                    // constraint planes along borders and seams keep their curves in place
                    constraintsAdded = true;
                    foreach (var kv in edges.All())
                    {
                        int a = (int)(kv.Key >> 32), b = (int)(kv.Key & 0xffffffff); var e = kv.Value;
                        bool border = e.count == 1, seam = e.count == 2 && IsSeam(T, SM, pid, e.t0, e.t1, a, b);
                        if (!border && !seam) continue;
                        for (int side = 0; side < (border ? 1 : 2); side++)
                        {
                            int t = side == 0 ? e.t0 : e.t1;
                            Plane(pp, pid[T[3 * t]], pid[T[3 * t + 1]], pid[T[3 * t + 2]], out double fx, out double fy, out double fz, out _, out double area);
                            double ex = pp[3 * b] - pp[3 * a], ey = pp[3 * b + 1] - pp[3 * a + 1], ez = pp[3 * b + 2] - pp[3 * a + 2];
                            double len = Math.Sqrt(ex * ex + ey * ey + ez * ez); if (len <= 0) continue;
                            // plane through the edge, perpendicular to the face
                            double cx = ey * fz - ez * fy, cy = ez * fx - ex * fz, cz = ex * fy - ey * fx;
                            double cl = Math.Sqrt(cx * cx + cy * cy + cz * cz); if (cl <= 0) continue;
                            cx /= cl; cy /= cl; cz /= cl;
                            double cd = -(cx * pp[3 * a] + cy * pp[3 * a + 1] + cz * pp[3 * a + 2]);
                            double w = len * len * 4;   // strong: borders/seams move far less than open surface
                            AddPlane(Qd, a, cx, cy, cz, cd, w, false); AddPlane(Qd, b, cx, cy, cz, cd, w, false);
                        }
                    }
                }
                // ---- best collapse per position id ----
                var cand = new List<(double cost, int a, int b)>();
                var mapFrom = new int[2]; var mapTo = new int[2];
                var options = new List<(double cost, int b, EdgeInfo e)>();
                for (int a = 0; a < np; a++)
                {
                    if (kind[a] == Locked || cnt[a] == cnt[a + 1]) continue;
                    options.Clear();
                    for (int i = cnt[a]; i < cnt[a + 1]; i++)
                    {
                        int t = adj[i];
                        for (int c = 0; c < 3; c++)
                        {
                            int b = pid[T[3 * t + c]]; if (b == a) continue;
                            bool dup = false; foreach (var o in options) if (o.b == b) { dup = true; break; }
                            if (dup) continue;
                            long k = a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a;
                            var e = edges.Get(k);
                            if (!Allowed(kind, T, SM, pid, e, a, b)) continue;
                            double cost = Cost(Qd, pp, a, b) + FeatureCost(features, fd, T, pid, e, a, b);
                            if (cost <= maxCost) options.Add((cost, b, e));
                        }
                    }
                    if (options.Count == 0) continue;
                    options.Sort((x, y) => x.cost.CompareTo(y.cost));
                    // the expensive topology tests only until the cheapest valid option is found
                    foreach (var o in options)
                        if (LinkOk(T, pid, adj, cnt, a, o.b, o.e.count) && !Flips(T, pp, pid, adj, cnt, a, o.b)) { cand.Add((o.cost, a, o.b)); break; }
                }
                if (cand.Count == 0) break;
                cand.Sort((x, y) => x.cost.CompareTo(y.cost));
                var touched = new bool[np]; int applied = 0;
                int passBudget = Math.Max(1, (liveTris - target + 1) / 2 + 1);
                foreach (var (cost, a, b) in cand)
                {
                    if (liveTris <= target) break;
                    if (touched[a] || touched[b]) continue;
                    // attribute-copy map a -> b from the triangles on edge ab
                    long k = a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a;
                    var e = edges.Get(k);
                    if (!CopyMap(T, pid, e, a, b, mapFrom, mapTo, out int maps)) continue;
                    // a's other copies must all be mapped
                    bool ok = true;
                    for (int i = cnt[a]; i < cnt[a + 1] && ok; i++)
                    {
                        int t = adj[i]; if (!alive[t]) continue;
                        int v = CornerOf(T, pid, t, a);
                        if (v != mapFrom[0] && (maps < 2 || v != mapFrom[1])) ok = false;
                    }
                    if (!ok) continue;
                    // lock the neighbourhood for this pass so candidates stay independent
                    touched[a] = touched[b] = true;
                    for (int i = cnt[a]; i < cnt[a + 1]; i++) { int t = adj[i]; for (int c = 0; c < 3; c++) touched[pid[T[3 * t + c]]] = true; }
                    for (int i = cnt[b]; i < cnt[b + 1]; i++) { int t = adj[i]; for (int c = 0; c < 3; c++) touched[pid[T[3 * t + c]]] = true; }
                    for (int i = cnt[a]; i < cnt[a + 1]; i++)
                    {
                        int t = adj[i]; if (!alive[t]) continue;
                        bool hasB = false; for (int c = 0; c < 3; c++) if (pid[T[3 * t + c]] == b) hasB = true;
                        if (hasB) { alive[t] = false; liveTris--; continue; }
                        for (int c = 0; c < 3; c++)
                            if (pid[T[3 * t + c]] == a) { int v = T[3 * t + c]; T[3 * t + c] = v == mapFrom[0] ? mapTo[0] : mapTo[1]; }
                    }
                    for (int j = 0; j < 11; j++) Qd[b * 11 + j] += Qd[a * 11 + j];
                    if (cost > worst) worst = cost;
                    applied++;
                    if (applied >= passBudget) break;
                }
                if (applied == 0) break;
            }
            // ---- output ----
            var outLists = new List<int>[input.submeshes.Length];
            for (int s = 0; s < outLists.Length; s++) outLists[s] = new List<int>();
            int tris = 0;
            for (int t = 0; t < nt; t++)
            {
                if (!alive[t]) continue;
                int a = T[3 * t], b = T[3 * t + 1], c = T[3 * t + 2];
                if (a == b || b == c || a == c) continue;
                outLists[SM[t]].Add(a); outLists[SM[t]].Add(b); outLists[SM[t]].Add(c); tris++;
            }
            var res = new Result { submeshes = new int[outLists.Length][], triangles = tris, maxError = Math.Sqrt(worst), passes = passes };
            for (int s = 0; s < outLists.Length; s++) res.submeshes[s] = outLists[s].ToArray();
            return res;
        }

        struct EdgeInfo { public int count, t0, t1; }

        /// Edges of the live triangles keyed by their position-id pair: a sorted table (much faster than a dictionary under mono).
        sealed class EdgeTable
        {
            readonly long[] keys; readonly EdgeInfo[] info;
            public EdgeTable(int[] T, int[] pid, bool[] alive, int nt)
            {
                int n = 0; for (int t = 0; t < nt; t++) if (alive[t]) n += 3;
                var k = new long[n]; var owner = new int[n]; int j = 0;
                for (int t = 0; t < nt; t++)
                {
                    if (!alive[t]) continue;
                    for (int c = 0; c < 3; c++)
                    {
                        int a = pid[T[3 * t + c]], b = pid[T[3 * t + (c + 1) % 3]];
                        k[j] = a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a; owner[j++] = t;
                    }
                }
                Array.Sort(k, owner);
                var uk = new List<long>(n / 2 + 1); var ui = new List<EdgeInfo>(n / 2 + 1);
                for (int i = 0; i < n;)
                {
                    int e = i; while (e < n && k[e] == k[i]) e++;
                    var inf = new EdgeInfo { count = e - i, t0 = owner[i], t1 = e - i > 1 ? owner[i + 1] : -1 };
                    uk.Add(k[i]); ui.Add(inf); i = e;
                }
                keys = uk.ToArray(); info = ui.ToArray();
            }
            public EdgeInfo Get(long k) { int i = Array.BinarySearch(keys, k); return i >= 0 ? info[i] : default; }
            public IEnumerable<KeyValuePair<long, EdgeInfo>> All() { for (int i = 0; i < keys.Length; i++) yield return new KeyValuePair<long, EdgeInfo>(keys[i], info[i]); }
        }

        static int Q(float x) => (int)Math.Round(x * 1e5);   // 0.01 mm weld

        static int CornerOf(int[] T, int[] pid, int t, int p)
        {
            for (int c = 0; c < 3; c++) if (pid[T[3 * t + c]] == p) return T[3 * t + c];
            return -1;
        }

        static bool IsSeam(int[] T, int[] SM, int[] pid, int t0, int t1, int a, int b)
        {
            if (SM[t0] != SM[t1]) return true;
            return CornerOf(T, pid, t0, a) != CornerOf(T, pid, t1, a) || CornerOf(T, pid, t0, b) != CornerOf(T, pid, t1, b);
        }

        static bool Allowed(byte[] kind, int[] T, int[] SM, int[] pid, EdgeInfo e, int a, int b)
        {
            if (e.count > 2) return false;
            switch (kind[a])
            {
                case Manifold: return true;
                case Border: return e.count == 1 && (kind[b] == Border || kind[b] == Locked);
                case Seam: return e.count == 2 && IsSeam(T, SM, pid, e.t0, e.t1, a, b) && (kind[b] == Seam || kind[b] == Locked);
                default: return false;
            }
        }

        static bool CopyMap(int[] T, int[] pid, EdgeInfo e, int a, int b, int[] from, int[] to, out int maps)
        {
            maps = 0;
            for (int side = 0; side < Math.Min(2, e.count); side++)
            {
                int t = side == 0 ? e.t0 : e.t1;
                int va = CornerOf(T, pid, t, a), vb = CornerOf(T, pid, t, b);
                if (maps == 1 && from[0] == va) { if (to[0] != vb) return false; continue; }
                from[maps] = va; to[maps] = vb; maps++;
            }
            return maps > 0;
        }

        static void Plane(double[] pp, int a, int b, int c, out double nx, out double ny, out double nz, out double d, out double area)
        {
            double ux = pp[3 * b] - pp[3 * a], uy = pp[3 * b + 1] - pp[3 * a + 1], uz = pp[3 * b + 2] - pp[3 * a + 2];
            double vx = pp[3 * c] - pp[3 * a], vy = pp[3 * c + 1] - pp[3 * a + 1], vz = pp[3 * c + 2] - pp[3 * a + 2];
            nx = uy * vz - uz * vy; ny = uz * vx - ux * vz; nz = ux * vy - uy * vx;
            double l = Math.Sqrt(nx * nx + ny * ny + nz * nz); area = l * .5;
            if (l > 0) { nx /= l; ny /= l; nz /= l; }
            d = -(nx * pp[3 * a] + ny * pp[3 * a + 1] + nz * pp[3 * a + 2]);
        }

        static void AddPlane(double[] Qd, int p, double a, double b, double c, double d, double w, bool countWeight = true)
        {
            int o = p * 11;
            Qd[o] += w * a * a; Qd[o + 1] += w * a * b; Qd[o + 2] += w * a * c; Qd[o + 3] += w * a * d;
            Qd[o + 4] += w * b * b; Qd[o + 5] += w * b * c; Qd[o + 6] += w * b * d;
            Qd[o + 7] += w * c * c; Qd[o + 8] += w * c * d; Qd[o + 9] += w * d * d;
            if (countWeight) Qd[o + 10] += w;
        }

        /// Mean squared distance (m^2) of b's position to a's accumulated planes.
        static double Cost(double[] Qd, double[] pp, int a, int b)
        {
            int o = a * 11; double x = pp[3 * b], y = pp[3 * b + 1], z = pp[3 * b + 2];
            double e = Qd[o] * x * x + 2 * Qd[o + 1] * x * y + 2 * Qd[o + 2] * x * z + 2 * Qd[o + 3] * x
                     + Qd[o + 4] * y * y + 2 * Qd[o + 5] * y * z + 2 * Qd[o + 6] * y
                     + Qd[o + 7] * z * z + 2 * Qd[o + 8] * z + Qd[o + 9];
            double w = Qd[o + 10]; if (w <= 0) return double.MaxValue;
            return Math.Max(0, e) / w;
        }

        static double FeatureCost(float[] f, int fd, int[] T, int[] pid, EdgeInfo e, int a, int b)
        {
            if (f == null || fd == 0) return 0;
            double worst = 0;
            for (int side = 0; side < Math.Min(2, e.count); side++)
            {
                int t = side == 0 ? e.t0 : e.t1;
                int va = CornerOf(T, pid, t, a), vb = CornerOf(T, pid, t, b);
                double s = 0; for (int i = 0; i < fd; i++) { double d = f[va * fd + i] - f[vb * fd + i]; s += d * d; }
                if (s > worst) worst = s;
            }
            return worst;
        }

        /// Link condition: a and b may share only the apexes of the triangles on edge ab, or the collapse pinches the surface.
        static bool LinkOk(int[] T, int[] pid, int[] adj, int[] cnt, int a, int b, int edgeTris)
        {
            int common = 0;
            for (int i = cnt[a]; i < cnt[a + 1]; i++)
            {
                int t = adj[i];
                for (int c = 0; c < 3; c++)
                {
                    int n = pid[T[3 * t + c]]; if (n == a || n == b) continue;
                    // count each neighbour of a once: only at its first appearance in a's fan
                    bool seen = false;
                    for (int j = cnt[a]; j < i && !seen; j++) { int u = adj[j]; for (int d = 0; d < 3; d++) if (pid[T[3 * u + d]] == n) seen = true; }
                    if (seen) continue;
                    for (int j = cnt[b]; j < cnt[b + 1]; j++) { int u = adj[j]; bool hit = false; for (int d = 0; d < 3; d++) if (pid[T[3 * u + d]] == n) hit = true; if (hit) { common++; break; } }
                }
            }
            return common <= edgeTris;
        }

        /// True when moving a onto b turns any remaining triangle of a's fan over (or collapses it to a sliver).
        static bool Flips(int[] T, double[] pp, int[] pid, int[] adj, int[] cnt, int a, int b)
        {
            for (int i = cnt[a]; i < cnt[a + 1]; i++)
            {
                int t = adj[i]; int p0 = pid[T[3 * t]], p1 = pid[T[3 * t + 1]], p2 = pid[T[3 * t + 2]];
                if (p0 == b || p1 == b || p2 == b) continue;
                Plane(pp, p0, p1, p2, out double ax, out double ay, out double az, out _, out double area0);
                int q0 = p0 == a ? b : p0, q1 = p1 == a ? b : p1, q2 = p2 == a ? b : p2;
                Plane(pp, q0, q1, q2, out double bx, out double by, out double bz, out _, out double area1);
                if (area1 <= area0 * 1e-3) return true;
                if (ax * bx + ay * by + az * bz < 0.3) return true;   // > ~72 degrees
            }
            return false;
        }
    }
}
