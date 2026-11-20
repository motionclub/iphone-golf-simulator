// KIT TUCK (2026-11-20, work/cloth-rip-1120): skin under a garment is pulled a few millimetres inward, so the body cannot poke
// through the cloth near the garment's openings (hem, cuffs, armholes, waistband, sock tops) in a swing.
// The deep inside of a garment is already not drawn (the _hide lists); the band near the openings must stay drawn (it shows
// when a hem rides up), and that band is where skin came through the cloth with the 11-19 strokes.
// Per garment: Resources/<Sport>/KitsV2/<Sex>/KitV2_<Sport>_<Sex>_<Tag>_tuck.bytes = int32 bodyVertexCount, int32 n,
// n x (int32 vertex, float32 depth metres). depth = geodesic distance into the garment's rest coverage (negative just outside it,
// for a smooth taper). Baked from the real runtime meshes by ClothAudit (CA_TUCK_OUT). Inward offset = clamp(Slope*(depth+Lead(tag)), 0, cap).
// Off: KIT_TUCK=0.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    public static class KitTuck
    {
        public static bool Enabled = Environment.GetEnvironmentVariable("KIT_TUCK") != "0";
        public const float Slope = .45f, Outside = .02f;
        /// How far past the coverage border the taper starts (metres): tops reach out further, so arm and neck skin at a tight cuff or collar stays inside the opening.
        public static float Lead(string tag) => tag == "Top" ? .013f : tag.StartsWith("Sock") ? .004f : .006f;
        /// Largest inward offset per garment tag: loose tops/bottoms tuck deep, tight pieces (socks, gloves) barely.
        public static float Cap(string tag) => tag.StartsWith("Sock") ? .003f : tag.StartsWith("Glove") ? .0015f : tag.StartsWith("Shoe") ? 0f : tag == "Belt" ? .004f : .012f;

        /// Combine the worn garments' tuck data into per-vertex inward offsets (metres) for a body mesh of vertexCount vertices.
        public static float[] Offsets(string sport, string sex, IEnumerable<string> wornTags, int vertexCount)
        {
            if (!Enabled) return null;
            float[] off = null;
            foreach (var tag in wornTags)
            {
                float cap = Cap(tag), lead = Lead(tag); if (cap <= 0) continue;
                var ta = Resources.Load<TextAsset>($"{sport}/KitsV2/{sex}/KitV2_{sport}_{sex}_{tag}_tuck");
                if (!ta) continue;
                var b = ta.bytes; if (b.Length < 8 || BitConverter.ToInt32(b, 0) != vertexCount) { Debug.LogWarning($"[KitTuck] {ta.name} does not fit a {vertexCount}-vertex body"); continue; }
                int n = BitConverter.ToInt32(b, 4);
                off ??= new float[vertexCount];
                for (int i = 0; i < n; i++)
                {
                    int v = BitConverter.ToInt32(b, 8 + i * 8); float d = BitConverter.ToSingle(b, 12 + i * 8);
                    float s = Mathf.Clamp(Slope * (d + lead), 0, cap);
                    if (v >= 0 && v < vertexCount && s > off[v]) off[v] = s;
                }
            }
            return off;
        }

        /// Pull vertices inward along their normals (bind space); the mesh must be the hero's own copy.
        public static void Apply(Mesh mesh, float[] off)
        {
            if (off == null || !mesh) return;
            var v = mesh.vertices; var n = mesh.normals; if (n == null || n.Length != v.Length) return;
            int moved = 0;
            for (int i = 0; i < v.Length; i++) if (off[i] > 0) { v[i] -= n[i] * off[i]; moved++; }
            mesh.vertices = v; mesh.RecalculateBounds();
        }

        /// Signed geodesic depth of every body vertex inside one garment's rest coverage (both meshes in one common space).
        /// Covered = the nearest garment vertex lies over the skin (skin behind its outward normal, at most 1.5 cm out, 8 cm in,
        /// tangential offset under 1.5 cm). Depth is measured over the welded body surface; outside the coverage it is negative
        /// down to -Outside. Returns NaN where neither applies.
        public static float[] Depth(Vector3[] bv, int[] btris, Vector3[] gv, Vector3[] gn, int[] gtris = null, Vector3[] bn = null)
        {
            const float cell = .03f;
            var grid = new Dictionary<Vector3Int, List<int>>();
            for (int i = 0; i < gv.Length; i++) { var c = Vector3Int.FloorToInt(gv[i] / cell); if (!grid.TryGetValue(c, out var l)) grid[c] = l = new List<int>(); l.Add(i); }
            var weld = new Dictionary<Vector3Int, int>(); var wid = new int[bv.Length];
            for (int i = 0; i < bv.Length; i++) { var q = Vector3Int.RoundToInt(bv[i] * 2000f); if (!weld.TryGetValue(q, out int w)) weld[q] = w = weld.Count; wid[i] = w; }
            int W = weld.Count; var wpos = new Vector3[W]; var cov = new bool[W];
            for (int i = 0; i < bv.Length; i++)
            {
                wpos[wid[i]] = bv[i];
                var c0 = Vector3Int.FloorToInt(bv[i] / cell); float bd = 1e9f; int bj = -1;
                for (int x = -2; x <= 2; x++) for (int y = -2; y <= 2; y++) for (int z = -2; z <= 2; z++)
                    if (grid.TryGetValue(c0 + new Vector3Int(x, y, z), out var l)) foreach (int j in l) { float d = (gv[j] - bv[i]).sqrMagnitude; if (d < bd) { bd = d; bj = j; } }
                if (bj < 0) continue;
                var off = bv[i] - gv[bj]; float nrm = Vector3.Dot(off, gn[bj]); float tan = (off - gn[bj] * nrm).magnitude;
                if (nrm < .015f && nrm > -.08f && tan < .015f) cov[wid[i]] = true;
            }
            // layered openings (cuff linings, facings): the nearest cloth may face the skin, so also cast a ray out along the skin normal
            if (gtris != null && bn != null)
            {
                var tgrid = new Dictionary<Vector3Int, List<int>>();
                for (int t = 0; t < gtris.Length; t += 3)
                {
                    var c = Vector3Int.FloorToInt((gv[gtris[t]] + gv[gtris[t + 1]] + gv[gtris[t + 2]]) / 3f / cell);
                    if (!tgrid.TryGetValue(c, out var l)) tgrid[c] = l = new List<int>(); l.Add(t);
                }
                for (int i = 0; i < bv.Length; i++)
                {
                    if (cov[wid[i]]) continue;
                    var o = bv[i]; var d = bn[i]; if (d.sqrMagnitude < .5f) continue;
                    bool hit = false; var seen = new HashSet<Vector3Int>();
                    for (float r = 0; r <= .06f && !hit; r += .01f)
                    {
                        var c0 = Vector3Int.FloorToInt((o + d * r) / cell);
                        for (int x = -1; x <= 1 && !hit; x++) for (int y = -1; y <= 1 && !hit; y++) for (int z = -1; z <= 1 && !hit; z++)
                        {
                            var c = c0 + new Vector3Int(x, y, z); if (!seen.Add(c) || !tgrid.TryGetValue(c, out var l)) continue;
                            foreach (int t in l) if (Ray(o, d, gv[gtris[t]], gv[gtris[t + 1]], gv[gtris[t + 2]], .06f)) { hit = true; break; }
                        }
                    }
                    if (hit) cov[wid[i]] = true;
                }
            }
            var adj = new List<int>[W]; for (int i = 0; i < W; i++) adj[i] = new List<int>(6);
            for (int t = 0; t < btris.Length; t += 3) for (int e = 0; e < 3; e++) { int a = wid[btris[t + e]], b = wid[btris[t + (e + 1) % 3]]; if (a != b) { adj[a].Add(b); adj[b].Add(a); } }
            // inside: distance to the nearest uncovered vertex; outside: distance to the nearest covered vertex (two Dijkstra fronts)
            float[] Front(bool fromCovered, float limit)
            {
                var dist = new float[W]; var heap = new SortedSet<(float, int)>();
                for (int i = 0; i < W; i++) { bool src = cov[i] == fromCovered; dist[i] = src ? 0 : 1e9f; if (src) heap.Add((0, i)); }
                while (heap.Count > 0)
                {
                    var (d0, a) = heap.Min; heap.Remove(heap.Min); if (d0 > dist[a] || d0 > limit) continue;
                    foreach (int b in adj[a]) { float nd = d0 + (wpos[a] - wpos[b]).magnitude; if (nd < dist[b]) { if (dist[b] < 1e8f) heap.Remove((dist[b], b)); dist[b] = nd; heap.Add((nd, b)); } }
                }
                return dist;
            }
            var inside = Front(false, .05f); var outside = Front(true, Outside);
            var res = new float[bv.Length];
            for (int i = 0; i < bv.Length; i++)
            {
                int w = wid[i];
                res[i] = cov[w] ? Mathf.Min(inside[w], .05f) : outside[w] <= Outside ? -outside[w] : float.NaN;
            }
            return res;
        }

        static bool Ray(Vector3 o, Vector3 d, Vector3 a, Vector3 b, Vector3 c, float maxT)
        {
            var e1 = b - a; var e2 = c - a; var p = Vector3.Cross(d, e2); float det = Vector3.Dot(e1, p);
            if (Mathf.Abs(det) < 1e-10f) return false;
            float inv = 1 / det; var s = o - a; float u = Vector3.Dot(s, p) * inv; if (u < 0 || u > 1) return false;
            var q = Vector3.Cross(s, e1); float v = Vector3.Dot(d, q) * inv; if (v < 0 || u + v > 1) return false;
            float t = Vector3.Dot(e2, q) * inv; return t > -.003f && t < maxT;
        }
        public static byte[] Encode(float[] depth)
        {
            var list = new List<(int, float)>();
            for (int i = 0; i < depth.Length; i++) if (!float.IsNaN(depth[i])) list.Add((i, depth[i]));
            var b = new byte[8 + list.Count * 8];
            BitConverter.GetBytes(depth.Length).CopyTo(b, 0); BitConverter.GetBytes(list.Count).CopyTo(b, 4);
            for (int k = 0; k < list.Count; k++) { BitConverter.GetBytes(list[k].Item1).CopyTo(b, 8 + k * 8); BitConverter.GetBytes(list[k].Item2).CopyTo(b, 12 + k * 8); }
            return b;
        }
    }
}
