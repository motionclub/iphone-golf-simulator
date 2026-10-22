using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Majestic
{
    /// Golf make-room (chat 10, PLAN §3 M1): the shadow pass is drawn from coarse proxies instead of the full meshes.
    /// Every big static caster of a hole (tree batches, cliff/terrain surface batches) keeps drawing exactly as before but
    /// stops casting; a shadows-only copy simplified by vertex clustering casts in its place. At shadow-map resolution
    /// (4096 over 320 yd, ~0.08 yd a texel at best) the proxy's shadow is the same shape, so nothing pops or changes,
    /// while the shadow pass submits a fraction of the triangles. Off with MAJESTIC=0 or MAJESTIC_BUDGET=0; restores
    /// every renderer exactly when switched off.
    public static class MajesticBudget
    {
        public static bool Enabled = System.Environment.GetEnvironmentVariable("MAJESTIC_BUDGET") != "0";
        const int MinTriangles = 6000;          // smaller casters are cheap: leave them
        static readonly List<(MeshRenderer r, ShadowCastingMode was, GameObject proxy)> done = new();
        static readonly Dictionary<Mesh, Mesh> proxies = new();
        static Material shadowMaterial;
        public static Material ShadowMaterial { get { if (!shadowMaterial) shadowMaterial = new Material(Shader.Find("GolfArcade/MajesticShadowOnly")) { name = "Majestic shadow proxy", enableInstancing = true }; return shadowMaterial; } }

        public static int ProxiedRenderers => done.Count;
        public static long SavedTriangles;

        public static void Apply(Transform holeRoot)
        {
            Restore();
            if (!Enabled || !holeRoot) return;
            SavedTriangles = 0;
            foreach (var r in holeRoot.GetComponentsInChildren<MeshRenderer>())
            {
                if (!r.enabled || r.shadowCastingMode != ShadowCastingMode.On) continue;
                if (r.GetComponent<SkinnedMeshRenderer>() || r.name.StartsWith("Majestic")) continue;
                var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh || !mf.sharedMesh.isReadable) continue;
                long tris = Tris(mf.sharedMesh); if (tris < MinTriangles) continue;
                bool tree = r.name.Contains("BOTANICAL") || r.name.Contains("TREE") || r.name.Contains("PINE") || r.name.Contains("PALM") || r.name.Contains("OAK");
                bool surface = r.name.Contains("SURFACE") || r.name.Contains("CLIFF") || r.name.Contains("Cliff") || r.name.Contains("ROCK");
                if (!tree && !surface) continue;
                if (!proxies.TryGetValue(mf.sharedMesh, out var proxyMesh))
                    proxies[mf.sharedMesh] = proxyMesh = Cluster(mf.sharedMesh, tree ? .55f : 1.1f);
                if (!proxyMesh) continue;
                var go = new GameObject(r.name + " (shadow proxy)") { layer = r.gameObject.layer };
                go.transform.SetParent(r.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = proxyMesh;
                var pr = go.AddComponent<MeshRenderer>();
                pr.sharedMaterial = ShadowMaterial;
                pr.shadowCastingMode = ShadowCastingMode.ShadowsOnly; pr.receiveShadows = false;
                pr.lightProbeUsage = LightProbeUsage.Off; pr.reflectionProbeUsage = ReflectionProbeUsage.Off;
                done.Add((r, r.shadowCastingMode, go));
                r.shadowCastingMode = ShadowCastingMode.Off;
                SavedTriangles += tris - Tris(proxyMesh);
            }
            FarTrees(holeRoot);
        }

        public static void Restore()
        {
            foreach (var (r, was, proxy) in done) { if (r) r.shadowCastingMode = was; if (proxy) Object.Destroy(proxy); }
            done.Clear();
            foreach (var (g, far) in farTrees) { if (g) Object.Destroy(g); if (far) Object.Destroy(far); }
            farTrees.Clear();
        }

        /// 10-18 (coordinator: pines past ~80 m to a far version): every resort tree cell (GolfResortDress
        /// "RESORT_BOTANICAL_n_PINE/PALM/OAK_NEAR", one combined mesh per 48 yd cell) gets a LODGroup whose second level is a
        /// colour-preserving clustered copy (ClusterVisual), switching when the cell centre is ~130 yd away (r34 pop check: 87 yd swapped in view). The
        /// near mesh is untouched; switched off, the LODGroup and the copy are removed.
        static readonly List<(LODGroup g, GameObject far)> farTrees = new();
        static readonly Dictionary<Mesh, Mesh> farMeshes = new();
        /// Proof tooling (pop check): force every far-tree cell to one level (0 = full mesh), -1 = normal selection.
        public static void ForceFarLod(int lod) { foreach (var (g, _) in farTrees) if (g) g.ForceLOD(lod); }
        public static IEnumerable<LODGroup> FarGroups { get { foreach (var (g, _) in farTrees) if (g) yield return g; } }
        public static long FarSavedTriangles; public static int FarCells => farTrees.Count;
        const float FarYards = 130f;   // pop check r34: at 87 yd the flyover saw the swap on trees in view
        static void FarTrees(Transform holeRoot)
        {
            FarSavedTriangles = 0;
            foreach (var r in holeRoot.GetComponentsInChildren<MeshRenderer>())
            {
                var n = r.name;
                if (!n.StartsWith("RESORT_BOTANICAL_") || !(n.EndsWith("_PINE_NEAR") || n.EndsWith("_PALM_NEAR") || n.EndsWith("_OAK_NEAR"))) continue;
                if (r.GetComponent<LODGroup>()) continue;
                var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh || !mf.sharedMesh.isReadable) continue;
                if (!farMeshes.TryGetValue(mf.sharedMesh, out var farMesh)) farMeshes[mf.sharedMesh] = farMesh = ClusterVisual(mf.sharedMesh, .65f);   // .9 merged the pine tiers into blobs
                if (!farMesh) continue;
                var go = new GameObject(n + " (far)") { layer = r.gameObject.layer };
                go.transform.SetParent(r.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = farMesh;
                var fr = go.AddComponent<MeshRenderer>(); fr.sharedMaterials = r.sharedMaterials;
                fr.shadowCastingMode = ShadowCastingMode.Off; fr.receiveShadows = r.receiveShadows;
                fr.lightProbeUsage = r.lightProbeUsage; fr.reflectionProbeUsage = ReflectionProbeUsage.Off;
                var g = r.gameObject.AddComponent<LODGroup>();
                g.SetLODs(new[] { new LOD(1, new Renderer[] { r }), new LOD(.0001f, new Renderer[] { fr }) });
                g.RecalculateBounds();
                // screen-relative height of the group at FarYards beyond its own half size, at the 50 deg game FOV
                float size = g.size, at = (n.EndsWith("_PALM_NEAR") ? FarYards * 1.5f : FarYards) + size * .5f;   // r35 pop check: palm fronds read at 90 yd
                var lods = g.GetLODs(); lods[0].screenRelativeTransitionHeight = Mathf.Clamp(size / (2 * at * Mathf.Tan(25 * Mathf.Deg2Rad)), .02f, .95f);
                g.SetLODs(lods);
                farTrees.Add((g, go));
                FarSavedTriangles += Tris(mf.sharedMesh) - Tris(farMesh);
            }
        }

        /// Vertex clustering that keeps the look at distance: vertices merge per grid cell AND per quantized colour (trunk and
        /// crown never blend), averaging position, normal and colour. Returns null when it saves less than 40 %.
        public static Mesh ClusterVisual(Mesh src, float cell)
        {
            var v = src.vertices; var nrm = src.normals; var col = src.colors; bool hasC = col != null && col.Length == v.Length, hasN = nrm != null && nrm.Length == v.Length;
            var idx = new List<int>(); for (int s = 0; s < src.subMeshCount; s++) idx.AddRange(src.GetIndices(s));
            var cellOf = new int[v.Length]; var keys = new Dictionary<(Vector3Int, int), int>();
            var sp = new List<Vector3>(); var sn = new List<Vector3>(); var sc = new List<Color>(); var cnt = new List<int>();
            for (int i = 0; i < v.Length; i++)
            {
                var k = new Vector3Int(Mathf.FloorToInt(v[i].x / cell), Mathf.FloorToInt(v[i].y / cell), Mathf.FloorToInt(v[i].z / cell));
                int ck = hasC ? Mathf.RoundToInt(col[i].r * 7) * 64 + Mathf.RoundToInt(col[i].g * 7) * 8 + Mathf.RoundToInt(col[i].b * 7) : 0;
                if (!keys.TryGetValue((k, ck), out int c)) { c = sp.Count; keys[(k, ck)] = c; sp.Add(Vector3.zero); sn.Add(Vector3.zero); sc.Add(Color.clear); cnt.Add(0); }
                cellOf[i] = c; sp[c] += v[i]; if (hasN) sn[c] += nrm[i]; if (hasC) sc[c] += col[i]; cnt[c]++;
            }
            var outV = new Vector3[sp.Count]; var outN = new Vector3[sp.Count]; var outC = new Color[sp.Count];
            for (int c = 0; c < outV.Length; c++) { outV[c] = sp[c] / cnt[c]; outN[c] = sn[c].sqrMagnitude > 0 ? sn[c].normalized : Vector3.up; outC[c] = sc[c] / cnt[c]; }
            var outI = new List<int>(idx.Count / 3); var seen = new HashSet<(int, int, int)>();
            for (int i = 0; i + 2 < idx.Count; i += 3)
            {
                int a = cellOf[idx[i]], b = cellOf[idx[i + 1]], c = cellOf[idx[i + 2]];
                if (a == b || b == c || a == c) continue;
                var key = a < b ? (b < c ? (a, b, c) : a < c ? (a, c, b) : (c, a, b)) : (a < c ? (b, a, c) : b < c ? (b, c, a) : (c, b, a));
                if (!seen.Add(key)) continue;
                outI.Add(a); outI.Add(b); outI.Add(c);
            }
            if (outI.Count / 3 > Tris(src) * .6f) return null;
            var m = new Mesh { name = src.name + " (far)", indexFormat = outV.Length > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
            m.vertices = outV; m.normals = outN; if (hasC) m.colors = outC; m.SetTriangles(outI, 0, true);
            return m;
        }

        static long Tris(Mesh m) { long t = 0; for (int s = 0; s < m.subMeshCount; s++) t += m.GetIndexCount(s) / 3; return t; }

        /// Vertex clustering: every vertex snaps to the centre of mass of its cell; triangles whose corners share a cell
        /// vanish. One submesh (the shadow pass needs no materials split). Returns null when it saves less than 40 %.
        public static Mesh Cluster(Mesh src, float cell)
        {
            var v = src.vertices; var idx = new List<int>();
            for (int s = 0; s < src.subMeshCount; s++) idx.AddRange(src.GetIndices(s));
            var cellOf = new int[v.Length]; var keys = new Dictionary<Vector3Int, int>(); var sums = new List<Vector3>(); var counts = new List<int>();
            for (int i = 0; i < v.Length; i++)
            {
                var k = new Vector3Int(Mathf.FloorToInt(v[i].x / cell), Mathf.FloorToInt(v[i].y / cell), Mathf.FloorToInt(v[i].z / cell));
                if (!keys.TryGetValue(k, out int c)) { c = sums.Count; keys[k] = c; sums.Add(Vector3.zero); counts.Add(0); }
                cellOf[i] = c; sums[c] += v[i]; counts[c]++;
            }
            var outV = new Vector3[sums.Count]; for (int c = 0; c < outV.Length; c++) outV[c] = sums[c] / counts[c];
            var outI = new List<int>(idx.Count / 3); var seen = new HashSet<(int, int, int)>();
            for (int i = 0; i + 2 < idx.Count; i += 3)
            {
                int a = cellOf[idx[i]], b = cellOf[idx[i + 1]], c = cellOf[idx[i + 2]];
                if (a == b || b == c || a == c) continue;
                var key = a < b ? (b < c ? (a, b, c) : a < c ? (a, c, b) : (c, a, b)) : (a < c ? (b, a, c) : b < c ? (b, c, a) : (c, b, a));
                if (!seen.Add(key)) continue;
                outI.Add(a); outI.Add(b); outI.Add(c);
            }
            if (outI.Count / 3 > Tris(src) * .6f) return null;
            var m = new Mesh { name = src.name + " (shadow proxy)", indexFormat = outV.Length > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
            m.vertices = outV; m.SetTriangles(outI, 0, true); m.RecalculateNormals();
            return m;
        }
    }
}
