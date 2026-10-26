using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// CHARACTER QUALITY 10-24 (clone tool): compares the shipped OriginalSeamBlinkFinish body with a re-export that only adds the SkinUnwrap
    /// UV layer, proves the triangle lists correspond 1:1, writes the new->old vertex map and remaps every body-index data file.
    /// Env: CQ_OLD=<asset path of the shipped fbx>  CQ_NEW=<asset path of the new fbx>  CQ_CONTROL=<optional re-export without changes>
    ///      CQ_SEX=Male|Female  CQ_OUT=<dir for the report, map and remapped .bytes>
    /// Unity -batchmode -projectPath <clone> -executeMethod GolfArcade.EditorTools.CharacterQualityMeshRemap.Run
    public static class CharacterQualityMeshRemap
    {
        static Mesh Body(string path)
        {
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(path) ?? throw new FileNotFoundException(path);
            return go.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r => r.name == "Body").sharedMesh;
        }

        public static void Run()
        {
            int code = 0;
            try { Compare(); } catch (Exception e) { Debug.LogException(e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }

        static void Compare()
        {
            string oldPath = Environment.GetEnvironmentVariable("CQ_OLD"), newPath = Environment.GetEnvironmentVariable("CQ_NEW");
            string control = Environment.GetEnvironmentVariable("CQ_CONTROL"), sex = Environment.GetEnvironmentVariable("CQ_SEX") ?? "Male";
            string outDir = Environment.GetEnvironmentVariable("CQ_OUT"); Directory.CreateDirectory(outDir);
            var log = new StringBuilder();
            var a = Body(oldPath); var b = Body(newPath);
            log.AppendLine($"old {oldPath}: v {a.vertexCount} tris {a.triangles.Length / 3} sub {a.subMeshCount} shapes {a.blendShapeCount}");
            log.AppendLine($"new {newPath}: v {b.vertexCount} tris {b.triangles.Length / 3} sub {b.subMeshCount} shapes {b.blendShapeCount}");
            if (!string.IsNullOrEmpty(control)) { var c = Body(control); log.AppendLine("control " + Diff(a, c, out _, out var cd)); log.Append(cd); }
            string verdict = Diff(a, b, out var newToOld, out var detail);
            log.AppendLine("new vs old " + verdict); log.Append(detail);
            File.WriteAllText(Path.Combine(outDir, "mesh_compare.txt"), log.ToString());
            Debug.Log("[CQRemap]\n" + log);
            if (newToOld == null) throw new Exception("triangle lists do not correspond: " + verdict);
            File.WriteAllBytes(Path.Combine(outDir, sex + "_new_to_old.bytes"), newToOld.SelectMany(BitConverter.GetBytes).ToArray());
            Remap(a, b, newToOld, sex, outDir);
        }

        /// Triangle t corner k of the new mesh must sit on the same position as in the old mesh, and every new vertex must carry the old
        /// vertex's data (normal, UV0, weights, shape deltas) exactly. Returns the new->old vertex map, or null when the lists differ.
        static string Diff(Mesh a, Mesh b, out int[] newToOld, out string detail)
        {
            newToOld = null; var d = new StringBuilder();
            var ta = a.triangles; var tb = b.triangles;
            if (ta.Length != tb.Length || a.subMeshCount != b.subMeshCount) { detail = ""; return $"FAIL triangle count {ta.Length / 3} vs {tb.Length / 3}"; }
            var pa = a.vertices; var pb = b.vertices; var na = a.normals; var nb = b.normals;
            var u0a = new List<Vector2>(); a.GetUVs(0, u0a); var u0b = new List<Vector2>(); b.GetUVs(0, u0b);
            var wa = a.boneWeights; var wb = b.boneWeights;
            var map = Enumerable.Repeat(-1, b.vertexCount).ToArray();
            int posBad = 0, mapConflict = 0;
            for (int i = 0; i < ta.Length; i++)
            {
                int o = ta[i], n = tb[i];
                if (pa[o] != pb[n]) posBad++;
                if (map[n] == -1) map[n] = o; else if (map[n] != o && pa[map[n]] != pa[o]) mapConflict++;
            }
            // loose vertices (in no triangle) cannot be reached through the triangles: pair them by position with the old loose ones
            var reached = new HashSet<int>(map.Where(x => x >= 0));
            var looseOld = Enumerable.Range(0, a.vertexCount).Where(o => !reached.Contains(o)).GroupBy(o => pa[o]).ToDictionary(g => g.Key, g => new Queue<int>(g));
            for (int n = 0; n < map.Length; n++)
                if (map[n] < 0 && looseOld.TryGetValue(pb[n], out var q) && q.Count > 0) map[n] = q.Dequeue();
            int unmapped = map.Count(x => x < 0), nrmBad = 0, uvBad = 0, wBad = 0; float nrmMax = 0;
            for (int n = 0; n < map.Length; n++)
            {
                int o = map[n]; if (o < 0) continue;
                if (na.Length > 0 && nb.Length > 0) { float ang = Vector3.Angle(na[o], nb[n]); nrmMax = Mathf.Max(nrmMax, ang); if (ang > .5f) nrmBad++; }
                if (u0a.Count > 0 && u0b.Count > 0 && (u0a[o] - u0b[n]).sqrMagnitude > 1e-12f) uvBad++;
                if (wa.Length > 0 && !wa[o].Equals(wb[n])) wBad++;
            }
            int shapeBad = 0;
            if (a.blendShapeCount != b.blendShapeCount) shapeBad = -1;
            else for (int s = 0; s < a.blendShapeCount; s++)
                for (int f = 0; f < a.GetBlendShapeFrameCount(s); f++)
                {
                    var dA = new Vector3[a.vertexCount]; var dB = new Vector3[b.vertexCount];
                    a.GetBlendShapeFrameVertices(s, f, dA, null, null); b.GetBlendShapeFrameVertices(s, f, dB, null, null);
                    for (int n = 0; n < map.Length; n++) if (map[n] >= 0 && (dA[map[n]] - dB[n]).sqrMagnitude > 1e-14f) shapeBad++;
                }
            var u4 = new List<Vector2>(); b.GetUVs(1, u4);
            d.AppendLine($"  corners off-position {posBad}, map conflicts {mapConflict}, unmapped new vertices {unmapped}");
            d.AppendLine($"  per-vertex: normals {nrmBad} (max {nrmMax:F3} deg), uv0 {uvBad}, weights {wBad}, shape deltas {shapeBad}; new uv1 (SkinUnwrap) count {u4.Count}");
            var olds = new HashSet<int>(map.Where(x => x >= 0)); d.AppendLine($"  old vertices reached {olds.Count}/{a.vertexCount}; new/old ratio {(float)b.vertexCount / a.vertexCount:F3}");
            detail = d.ToString();
            bool ok = posBad == 0 && mapConflict == 0 && unmapped == 0 && nrmBad == 0 && uvBad == 0 && wBad == 0 && shapeBad == 0 && olds.Count == a.vertexCount;
            if (ok) newToOld = map;
            return (ok ? "PASS" : "FAIL") + $" (v {a.vertexCount} -> {b.vertexCount})";
        }

        static long Key(int a, int b, int c)
        {
            if (a > b) (a, b) = (b, a); if (b > c) (b, c) = (c, b); if (a > b) (a, b) = (b, a);
            return ((long)a << 42) | ((long)b << 21) | (long)c;
        }

        /// Hide lists: each old triplet names an old triangle; the remapped triplet is the same triangle's corners in the new mesh.
        /// Contact lists: each old vertex's value goes to every new vertex made from it. Shoulder fit: per-vertex deltas likewise.
        static void Remap(Mesh a, Mesh b, int[] newToOld, string sex, string outDir)
        {
            var ta = a.triangles; var tb = b.triangles;
            var triOf = new Dictionary<long, int>();
            for (int t = 0; t < ta.Length / 3; t++) triOf[Key(ta[3 * t], ta[3 * t + 1], ta[3 * t + 2])] = t;
            var oldToNew = new Dictionary<int, List<int>>();
            for (int n = 0; n < newToOld.Length; n++) { if (!oldToNew.TryGetValue(newToOld[n], out var l)) oldToNew[newToOld[n]] = l = new List<int>(); l.Add(n); }
            var report = new StringBuilder();
            var files = new List<string>();
            foreach (var dir in new[] { $"Assets/Resources/Tennis/KitsV2/{sex}", $"Assets/Resources/Golf/KitsV2/{sex}", $"Assets/Resources/Accessories/{sex}" })
                if (Directory.Exists(dir)) files.AddRange(Directory.GetFiles(dir, "*.bytes", SearchOption.AllDirectories));
            foreach (var f in files.OrderBy(x => x, StringComparer.Ordinal))
            {
                string name = Path.GetFileName(f); var bytes = File.ReadAllBytes(f); byte[] outBytes = null; string note;
                if (name.EndsWith("_hide.bytes"))
                {
                    var o = new List<byte>(bytes.Length); int miss = 0, n3 = bytes.Length / 12;
                    for (int i = 0; i < n3; i++)
                    {
                        int x = BitConverter.ToInt32(bytes, 12 * i), y = BitConverter.ToInt32(bytes, 12 * i + 4), z = BitConverter.ToInt32(bytes, 12 * i + 8);
                        if (!triOf.TryGetValue(Key(x, y, z), out int t)) { miss++; continue; }
                        for (int k = 0; k < 3; k++) o.AddRange(BitConverter.GetBytes(tb[3 * t + k]));
                    }
                    outBytes = o.ToArray(); note = $"hide {n3} triangles, unmatched {miss}";
                }
                else if (name.EndsWith("_contact.bytes"))
                {
                    int count = bytes.Length / 8; var ids = new List<int>(); var vals = new List<float>(); int miss = 0;
                    for (int i = 0; i < count; i++)
                    {
                        int v = BitConverter.ToInt32(bytes, 4 * i); float c = BitConverter.ToSingle(bytes, 4 * count + 4 * i);
                        if (!oldToNew.TryGetValue(v, out var nl)) { miss++; continue; }
                        foreach (var nv in nl) { ids.Add(nv); vals.Add(c); }
                    }
                    outBytes = ids.SelectMany(BitConverter.GetBytes).Concat(vals.SelectMany(BitConverter.GetBytes)).ToArray();
                    note = $"contact {count} -> {ids.Count} vertices, unmatched {miss}";
                }
                else if (name == "FemaleShoulderFit.bytes")
                {
                    // header (vertices, active, anchors), active indices, then per anchor: active position deltas, active normal deltas
                    int verts = BitConverter.ToInt32(bytes, 0), active = BitConverter.ToInt32(bytes, 4), count = BitConverter.ToInt32(bytes, 8);
                    if (verts != a.vertexCount) throw new Exception($"{f}: header {verts} vertices, old body {a.vertexCount}");
                    var idx = new int[active]; for (int i = 0; i < active; i++) idx[i] = BitConverter.ToInt32(bytes, 12 + 4 * i);
                    var newIdx = new List<int>(); var srcOf = new List<int>();
                    for (int i = 0; i < active; i++) foreach (var nv in oldToNew[idx[i]]) { newIdx.Add(nv); srcOf.Add(i); }
                    var o = new List<byte>();
                    o.AddRange(BitConverter.GetBytes(b.vertexCount)); o.AddRange(BitConverter.GetBytes(newIdx.Count)); o.AddRange(BitConverter.GetBytes(count));
                    foreach (var v in newIdx) o.AddRange(BitConverter.GetBytes(v));
                    int at = 12 + 4 * active;
                    for (int k = 0; k < count; k++)
                        for (int part = 0; part < 2; part++)
                        {
                            foreach (var s in srcOf) o.AddRange(new ArraySegment<byte>(bytes, at + 12 * s, 12));
                            at += 12 * active;
                        }
                    if (at != bytes.Length) throw new Exception($"{f}: read {at} of {bytes.Length} bytes");
                    outBytes = o.ToArray(); note = $"shoulder fit {active} -> {newIdx.Count} active vertices x {count} anchors";
                }
                else { note = "not body-indexed, unchanged"; }
                report.AppendLine($"{f}: {note}");
                if (outBytes != null)
                {
                    var dst = Path.Combine(outDir, "remapped", f.Substring("Assets/Resources/".Length));
                    Directory.CreateDirectory(Path.GetDirectoryName(dst)); File.WriteAllBytes(dst, outBytes);
                }
            }
            // proof: the triangles each remapped hide list removes are the same triangles (by corner positions) as before
            var pa = a.vertices; var pb = b.vertices; int checkedFiles = 0, posDiff = 0;
            foreach (var f in files.Where(x => x.EndsWith("_hide.bytes")))
            {
                var src = File.ReadAllBytes(f); var dst = File.ReadAllBytes(Path.Combine(outDir, "remapped", f.Substring("Assets/Resources/".Length)));
                if (src.Length != dst.Length) { posDiff++; continue; }
                string Corners(byte[] buf, int at, Vector3[] p) => string.Join(";", Enumerable.Range(0, 3).Select(k => p[BitConverter.ToInt32(buf, at + 4 * k)])
                    .OrderBy(v => v.x).ThenBy(v => v.y).ThenBy(v => v.z).Select(v => $"{v.x:R},{v.y:R},{v.z:R}"));
                for (int i = 0; i + 12 <= src.Length; i += 12)
                    if (Corners(src, i, pa) != Corners(dst, i, pb)) posDiff++;
                checkedFiles++;
            }
            report.AppendLine($"GATE REMAP: {checkedFiles} hide lists, corner position mismatches {posDiff} -> {(posDiff == 0 ? "PASS" : "FAIL")}");
            File.WriteAllText(Path.Combine(outDir, "remap_report.txt"), report.ToString());
            Debug.Log("[CQRemap]\n" + report);
        }
    }
}
