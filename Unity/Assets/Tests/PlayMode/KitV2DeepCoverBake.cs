using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// SKIN THROUGH THE SHIRT (2026-11-10, avatar audit: on the serve the male polo showed patches of chest and flank). The V2 kits hide the
    /// skin under each garment from a list (KitV2_*_hide.bytes, work/clothing-v2/py/cover.py), and that list leaves out any skin some
    /// pose "uncovers": skin whose outward ray misses the garment. Skin that pokes THROUGH the cloth in a hard pose passes that same
    /// test, so exactly the skin that needed hiding was put back. This bake adds to the Top's list the skin that lies deep under the
    /// top: covered by it in the hero's rest pose and at least `Depth` along the body from any skin the top does not cover (collar,
    /// sleeve ends, hem, armholes keep that much skin, so cloth sliding there still shows skin, never a hole).
    /// Runs only with KITV2_DEEP_COVER=bake; idempotent (what is already hidden is not added again).
    public class KitV2DeepCoverBake
    {
        const float Cell = .03f;
        /// Per piece: how far off the skin its cloth may be and still count as covering it, and how deep under it skin must lie to be
        /// hidden. A bottom counts only where it lies on the skin (shorts liner, waist, seat): a skirt standing off the thighs covers
        /// nothing, since the thighs under it are seen whenever it lifts.
        static readonly (string piece, float reach, float depth)[] Pieces = { ("Kit_Top", .06f, .07f), ("Kit_Bottom", .015f, .04f) };

        [UnityTest, Timeout(900000)] public IEnumerator Bake()
        {
            Assume.That(System.Environment.GetEnvironmentVariable("KITV2_DEEP_COVER") == "bake", "set KITV2_DEEP_COVER=bake to bake");
            var report = new System.Text.StringBuilder();
            foreach (bool female in new[] { false, true })
                foreach (string path in new[] { GolfArcade.Game.HeroAssets.Match(female), GolfArcade.Game.HeroAssets.Bowling(female), GolfArcade.Game.HeroAssets.GolfKitPrefab(female) })
                {
                    var prefab = Resources.Load<GameObject>(path);
                    if (!prefab) { report.AppendLine(path + ": no prefab"); continue; }
                    var go = Object.Instantiate(prefab); yield return null; yield return null;
                    var look = go.GetComponentInChildren<MatchHeroLook>();
                    foreach (var (piece, reach, depth) in Pieces) report.AppendLine(path + " " + piece + ": " + (look ? BakeHero(look, piece, reach, depth) : "no MatchHeroLook"));
                    Object.Destroy(go); yield return null;
                }
            Debug.Log("[KitV2DeepCover]\n" + report);
            var outFile = System.Environment.GetEnvironmentVariable("KITV2_DEEP_COVER_REPORT");
            if (!string.IsNullOrEmpty(outFile)) File.WriteAllText(outFile, report.ToString());
        }

        static string BakeHero(MatchHeroLook look, string piece, float Reach, float Depth)
        {
            var src = (Mesh)typeof(MatchHeroLook).GetField("kitV2CoverSource", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(look);
            if (!look.kitV2 || !src || !look.body) return "not a V2 kit hero";
            var top = look.kit?.FirstOrDefault(r => r && r.enabled && r.name == piece) as SkinnedMeshRenderer;
            if (!top || !MatchHeroLook.IsKitV2(top)) return "no V2 piece";
            string sport = look.KitSportFolder, sex = look.female ? "Female" : "Male";
            string resource = $"{sport}/KitsV2/{sex}/KitV2_{sport}_{sex}_{piece.Substring(4)}_hide";
            if (!Resources.Load<TextAsset>(resource)) return "no hide list";

            // body and top in the same pose, world space
            var bodyMesh = new Mesh(); look.body.BakeMesh(bodyMesh, true);
            var topMesh = new Mesh(); top.BakeMesh(topMesh, true);
            var bm = look.body.transform.localToWorldMatrix; var tm = top.transform.localToWorldMatrix;
            var bp = bodyMesh.vertices.Select(v => bm.MultiplyPoint3x4(v)).ToArray();
            var bn = bodyMesh.normals.Select(n => bm.MultiplyVector(n).normalized).ToArray();
            var tp = topMesh.vertices.Select(v => tm.MultiplyPoint3x4(v)).ToArray();
            var tt = topMesh.triangles;
            if (bp.Length != src.vertexCount) return "body vertex count changed";

            // the top's triangles in a grid
            var grid = new Dictionary<Vector3Int, List<int>>();
            for (int t = 0; t < tt.Length; t += 3)
            {
                var lo = Vector3.Min(tp[tt[t]], Vector3.Min(tp[tt[t + 1]], tp[tt[t + 2]])); var hi = Vector3.Max(tp[tt[t]], Vector3.Max(tp[tt[t + 1]], tp[tt[t + 2]]));
                var a = Vector3Int.FloorToInt(lo / Cell); var b = Vector3Int.FloorToInt(hi / Cell);
                for (int x = a.x; x <= b.x; x++) for (int y = a.y; y <= b.y; y++) for (int z = a.z; z <= b.z; z++)
                { var k = new Vector3Int(x, y, z); if (!grid.TryGetValue(k, out var l)) grid[k] = l = new List<int>(); l.Add(t); }
            }
            bool Covered(Vector3 o, Vector3 d)
            {
                var e = o + d * Reach; var a = Vector3Int.FloorToInt(Vector3.Min(o, e) / Cell); var b = Vector3Int.FloorToInt(Vector3.Max(o, e) / Cell);
                for (int x = a.x; x <= b.x; x++) for (int y = a.y; y <= b.y; y++) for (int z = a.z; z <= b.z; z++)
                    if (grid.TryGetValue(new Vector3Int(x, y, z), out var l))
                        foreach (int t in l) if (Hit(o, d, tp[tt[t]], tp[tt[t + 1]], tp[tt[t + 2]], Reach)) return true;
                return false;
            }
            var covered = new bool[bp.Length];
            for (int v = 0; v < bp.Length; v++) covered[v] = Covered(bp[v] + bn[v] * .001f, bn[v]);

            // distance along the body from any skin the top does not cover (vertices welded by position: seams must not stop it)
            var weld = new Dictionary<Vector3Int, int>(); var id = new int[bp.Length]; var rest = src.vertices;
            for (int v = 0; v < bp.Length; v++) { var k = Vector3Int.RoundToInt(rest[v] * 20000f); if (!weld.TryGetValue(k, out id[v])) weld[k] = id[v] = weld.Count; }
            int n = weld.Count; var pos = new Vector3[n]; var open = new bool[n]; var seen = new bool[n];
            for (int v = 0; v < bp.Length; v++) { pos[id[v]] = bp[v]; if (!covered[v]) open[id[v]] = true; }
            var near = new List<int>[n]; for (int i = 0; i < n; i++) near[i] = new List<int>();
            var tris = new List<int>(); for (int s = 0; s < src.subMeshCount; s++) tris.AddRange(src.GetTriangles(s));
            for (int t = 0; t < tris.Count; t += 3)
                for (int e = 0; e < 3; e++) { int a = id[tris[t + e]], b = id[tris[t + (e + 1) % 3]]; if (a != b) { near[a].Add(b); near[b].Add(a); } }
            var dist = new float[n]; var queue = new SortedSet<(float, int)>();
            for (int i = 0; i < n; i++) { dist[i] = open[i] ? 0 : float.PositiveInfinity; if (open[i]) queue.Add((0, i)); }
            while (queue.Count > 0)
            {
                var (d, i) = queue.Min; queue.Remove(queue.Min);
                if (d > dist[i] || d > Depth + .02f) continue;
                foreach (int j in near[i]) { float nd = d + (pos[j] - pos[i]).magnitude; if (nd < dist[j]) { dist[j] = nd; queue.Add((nd, j)); } }
            }

            // what the worn pieces hide already
            var hidden = new HashSet<(int, int, int)>();
            foreach (var r in look.kit.Where(r => r && r.enabled))
            {
                var ta = Resources.Load<TextAsset>($"{sport}/KitsV2/{sex}/KitV2_{sport}_{sex}_{r.name.Substring(4).Replace("_", "")}_hide");
                if (!ta) continue; var b = ta.bytes;
                for (int i = 0; i + 12 <= b.Length; i += 12) hidden.Add(Key(System.BitConverter.ToInt32(b, i), System.BitConverter.ToInt32(b, i + 4), System.BitConverter.ToInt32(b, i + 8)));
            }
            var add = new List<int>();
            for (int t = 0; t < tris.Count; t += 3)
            {
                int a = tris[t], b = tris[t + 1], c = tris[t + 2];
                if (dist[id[a]] >= Depth && dist[id[b]] >= Depth && dist[id[c]] >= Depth && hidden.Add(Key(a, b, c))) { add.Add(a); add.Add(b); add.Add(c); }
            }
            Object.Destroy(bodyMesh); Object.Destroy(topMesh);
            if (add.Count == 0) return $"nothing to add (covered {covered.Count(c => c)} of {bp.Length} vertices)";
            string file = Path.GetFullPath($"Assets/Resources/{resource}.bytes");
            var old = File.ReadAllBytes(file); var bytes = new byte[old.Length + add.Count * 4];
            System.Buffer.BlockCopy(old, 0, bytes, 0, old.Length); System.Buffer.BlockCopy(add.ToArray(), 0, bytes, old.Length, add.Count * 4);
            File.WriteAllBytes(file, bytes);
            return $"covered {covered.Count(c => c)} of {bp.Length} vertices; hidden triangles {old.Length / 12} -> {bytes.Length / 12} (+{add.Count / 3})";
        }

        static (int, int, int) Key(int a, int b, int c) { if (a > b) (a, b) = (b, a); if (b > c) (b, c) = (c, b); if (a > b) (a, b) = (b, a); return (a, b, c); }

        /// Ray o + t d (0 <= t <= Reach) against a triangle, either side.
        static bool Hit(Vector3 o, Vector3 d, Vector3 a, Vector3 b, Vector3 c, float Reach)
        {
            Vector3 e1 = b - a, e2 = c - a, p = Vector3.Cross(d, e2); float det = Vector3.Dot(e1, p);
            if (Mathf.Abs(det) < 1e-12f) return false;
            float inv = 1 / det; Vector3 s = o - a; float u = Vector3.Dot(s, p) * inv; if (u < 0 || u > 1) return false;
            Vector3 q = Vector3.Cross(s, e1); float v = Vector3.Dot(d, q) * inv; if (v < 0 || u + v > 1) return false;
            float t = Vector3.Dot(e2, q) * inv; return t >= 0 && t <= Reach;
        }
    }
}
