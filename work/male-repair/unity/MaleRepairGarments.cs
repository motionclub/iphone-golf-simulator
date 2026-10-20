#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// 2026-10-19 chat F (male repair): golf male skin that pokes through the trousers / belt in a swing.
    /// The trousers + belt cover the legs and hips completely, so every body triangle that sits inside them (bind pose)
    /// is added to the Bottom hide list (MatchHeroLook.ApplyKitV2Cover drops those triangles; the body mesh is untouched).
    /// MR_OUT = folder for the new KitV2_Golf_Male_Bottom_hide.bytes + log. Nothing in Assets is written.
    public static class MaleRepairGarments
    {
        const string Prefab = "Assets/Resources/Tennis/Customization/PlayerMaleGolfKit.prefab";
        const string HidePath = "Assets/Resources/Golf/KitsV2/Male/KitV2_Golf_Male_Bottom_hide.bytes";
        static long Key(int a, int b, int c) { if (a > b) (a, b) = (b, a); if (b > c) (b, c) = (c, b); if (a > b) (a, b) = (b, a); return ((long)a << 42) | ((long)b << 21) | (long)c; }

        /// Mesh-space positions of a skinned mesh brought into the body's mesh space through the shared bind poses (Hips).
        static Vector3[] InBodySpace(SkinnedMeshRenderer piece, SkinnedMeshRenderer body, out Vector3[] normals)
        {
            var m = piece.sharedMesh; var v = m.vertices; var n = m.normals;
            int hb = Array.FindIndex(body.bones, b => b && b.name == "Hips"), hp = Array.FindIndex(piece.bones, b => b && b.name == "Hips");
            var toBody = hb >= 0 && hp >= 0 ? body.sharedMesh.bindposes[hb].inverse * m.bindposes[hp] : Matrix4x4.identity;
            normals = n.Select(x => toBody.MultiplyVector(x).normalized).ToArray();
            return v.Select(x => toBody.MultiplyPoint3x4(x)).ToArray();
        }

        public static void Run()
        {
            string output = Environment.GetEnvironmentVariable("MR_OUT"); Directory.CreateDirectory(output);
            var log = new List<string>();
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(Prefab);
            var look = go.GetComponent<MatchHeroLook>();
            var body = look.body; var bm = body.sharedMesh; var bv = bm.vertices;
            SkinnedMeshRenderer Piece(string n) => look.kit.First(r => r && r.name == n);
            var pants = Piece("Kit_Bottom"); var belt = Piece("Kit_Belt"); var top = Piece("Kit_Top");
            var pv = InBodySpace(pants, body, out var pn); var lv = InBodySpace(belt, body, out var ln); var tv = InBodySpace(top, body, out _);
            Bounds B(Vector3[] a) { var b = new Bounds(a[0], Vector3.zero); foreach (var p in a) b.Encapsulate(p); return b; }
            log.Add($"body {bm.name} v={bv.Length} bounds {B(bv)}");
            log.Add($"pants {pants.sharedMesh.name} v={pv.Length} bounds {B(pv)}");
            log.Add($"belt {belt.sharedMesh.name} bounds {B(lv)}  top {top.sharedMesh.name} bounds {B(tv)}");
            foreach (var r in look.kit) if (r) log.Add($"kit {r.name}: mats {string.Join(",", r.sharedMaterials.Select(m => m ? m.name + " cull=" + (m.HasProperty("_Cull") ? m.GetFloat("_Cull") : -1) : "null"))}");
            float beltTop = B(lv).max.z, pantsLow = B(pv).min.z;   // mesh space is Z-up (Blender)
            float topY = beltTop - .004f, lowY = pantsLow + float.Parse(Environment.GetEnvironmentVariable("MR_HEM_MARGIN") ?? ".035", System.Globalization.CultureInfo.InvariantCulture);
            // nearest-cloth test on a coarse grid (trousers + belt): inside when the body point is behind the nearest cloth vertex's normal
            var cloth = pv.Concat(lv).ToArray(); var clothN = pn.Concat(ln).ToArray();
            const float cell = .03f;
            var grid = new Dictionary<Vector3Int, List<int>>();
            Vector3Int C(Vector3 p) => new Vector3Int(Mathf.FloorToInt(p.x / cell), Mathf.FloorToInt(p.y / cell), Mathf.FloorToInt(p.z / cell));
            for (int i = 0; i < cloth.Length; i++) { var c = C(cloth[i]); if (!grid.TryGetValue(c, out var l)) grid[c] = l = new List<int>(); l.Add(i); }
            var inside = new bool[bv.Length]; int nin = 0;
            for (int i = 0; i < bv.Length; i++)
            {
                var p = bv[i]; if (p.z > topY || p.z < lowY) continue;
                var c = C(p); float best = float.MaxValue; int bi = -1;
                for (int dx = -2; dx <= 2; dx++) for (int dy = -2; dy <= 2; dy++) for (int dz = -2; dz <= 2; dz++)
                    if (grid.TryGetValue(c + new Vector3Int(dx, dy, dz), out var l)) foreach (int k in l) { float d = (cloth[k] - p).sqrMagnitude; if (d < best) { best = d; bi = k; } }
                if (bi < 0 || best > .06f * .06f) continue;
                if (Vector3.Dot(clothN[bi], p - cloth[bi]) < .004f) { inside[i] = true; nin++; }
            }
            var old = File.ReadAllBytes(HidePath); var hide = new HashSet<long>(); var list = new List<int>();
            for (int i = 0; i + 12 <= old.Length; i += 12) { int a = BitConverter.ToInt32(old, i), b = BitConverter.ToInt32(old, i + 4), c = BitConverter.ToInt32(old, i + 8); if (hide.Add(Key(a, b, c))) list.AddRange(new[] { a, b, c }); }
            int before = hide.Count, added = 0;
            for (int s = 0; s < bm.subMeshCount; s++)
            {
                var t = bm.GetTriangles(s);
                for (int i = 0; i < t.Length; i += 3)
                    if (inside[t[i]] && inside[t[i + 1]] && inside[t[i + 2]] && hide.Add(Key(t[i], t[i + 1], t[i + 2]))) { list.AddRange(new[] { t[i], t[i + 1], t[i + 2] }); added++; }
            }
            log.Add($"beltTop {beltTop:F4} pantsLow {pantsLow:F4} band {lowY:F4}..{topY:F4}; inside verts {nin}; hide tris {before} -> {hide.Count} (+{added}) of {bm.triangles.Length / 3}");
            using (var w = new BinaryWriter(File.Create(Path.Combine(output, "KitV2_Golf_Male_Bottom_hide.bytes")))) foreach (int i in list) w.Write(i);
            File.WriteAllLines(Path.Combine(output, "garments_log.txt"), log);
            if (Application.isBatchMode) EditorApplication.Exit(0);
        }
    }
}
#endif
