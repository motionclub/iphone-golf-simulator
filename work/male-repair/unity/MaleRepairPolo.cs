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
    /// 2026-10-19 chat F (male repair), golf polo G1: at address the bent back pulls the tucked hem (3 cm under the belt top) up over the
    /// belt and the skin shows. Garment-only fix on the golf male Kit_Top asset: the band from 2 cm above the belt top down is stretched so the
    /// tail reaches MR_TAIL (default 9 cm) under the belt top, kept 6 mm inside the trousers, and below the belt it takes the trousers' skin
    /// weights (by bone name) and drops its pose-corrective deltas, so it rides with the waistband like a tucked shirt. Writes the asset in
    /// the project it runs in (the clone); log -> MR_OUT/polo_log.txt.
    public static class MaleRepairPolo
    {
        const float TUCK = .015f;
        const string Prefab = "Assets/Resources/Tennis/Customization/PlayerMaleGolfKit.prefab";

        /// The belt tears in a swing (its own weights + correctives disagree with the waistband it sits on): every belt vertex takes the
        /// skin weights of its nearest trouser vertex (by bone name) and the belt's pose-corrective deltas are dropped.
        static void Belt(SkinnedMeshRenderer belt, SkinnedMeshRenderer pants, List<string> log)
        {
            var mesh = belt.sharedMesh; var bv = mesh.vertices; var bw = mesh.boneWeights;
            var map = Matrix4x4.identity;
            { int i = Array.FindIndex(belt.bones, b => b && b.name == "Hips"), j = Array.FindIndex(pants.bones, b => b && b.name == "Hips"); if (i >= 0 && j >= 0) map = pants.sharedMesh.bindposes[j].inverse * mesh.bindposes[i]; }
            var pv = pants.sharedMesh.vertices; var pw = pants.sharedMesh.boneWeights;
            var idx = new Dictionary<string, int>(); for (int i = 0; i < belt.bones.Length; i++) if (belt.bones[i] && !idx.ContainsKey(belt.bones[i].name)) idx[belt.bones[i].name] = i;
            int ok = 0, miss = 0; var missing = new HashSet<string>(); var near = new int[bv.Length];
            for (int i = 0; i < bv.Length; i++)
            {
                var p = map.MultiplyPoint3x4(bv[i]); int bi = 0; float best = float.MaxValue;
                for (int j = 0; j < pv.Length; j++) { float d = (pv[j] - p).sqrMagnitude; if (d < best) { best = d; bi = j; } }
                near[i] = bi;
                var w = pw[bi]; int[] bs = { w.boneIndex0, w.boneIndex1, w.boneIndex2, w.boneIndex3 }; float[] ws = { w.weight0, w.weight1, w.weight2, w.weight3 };
                bool good = true; for (int q = 0; q < 4; q++) if (ws[q] > 0 && !idx.ContainsKey(pants.bones[bs[q]].name)) { good = false; missing.Add(pants.bones[bs[q]].name); }
                if (!good) { miss++; continue; }
                int I(int q) => ws[q] > 0 ? idx[pants.bones[bs[q]].name] : 0;
                bw[i] = new BoneWeight { boneIndex0 = I(0), boneIndex1 = I(1), boneIndex2 = I(2), boneIndex3 = I(3), weight0 = ws[0], weight1 = ws[1], weight2 = ws[2], weight3 = ws[3] }; ok++;
            }
            mesh.boneWeights = bw;
            int shapes = mesh.blendShapeCount;
            // the belt rides the waistband's own correctives: nearest trouser vertex deltas per shape, and the trousers' RBF coefficients
            var pm = pants.sharedMesh; int copied = 0;
            if (shapes > 0)
            {
                var names = Enumerable.Range(0, shapes).Select(mesh.GetBlendShapeName).ToArray(); mesh.ClearBlendShapes();
                foreach (var n in names)
                {
                    int ps = pm.GetBlendShapeIndex(n); var d = new Vector3[bv.Length]; var nn = new Vector3[bv.Length]; var tt = new Vector3[bv.Length]; float fw = 100;
                    if (ps >= 0)
                    {
                        var pd = new Vector3[pm.vertexCount]; var pnn = new Vector3[pm.vertexCount]; var ptt = new Vector3[pm.vertexCount];
                        pm.GetBlendShapeFrameVertices(ps, 0, pd, pnn, ptt); fw = pm.GetBlendShapeFrameWeight(ps, 0);
                        var inv = map.inverse;
                        for (int i = 0; i < bv.Length; i++) { d[i] = inv.MultiplyVector(pd[near[i]]); nn[i] = inv.MultiplyVector(pnn[near[i]]); }
                        copied++;
                    }
                    mesh.AddBlendShapeFrame(n, fw, d, nn, tt);
                }
                string bottom = "Assets/Resources/Golf/KitsV2/Male/KitV2_Golf_Male_Bottom_correctives.json", beltJson = "Assets/Resources/Golf/KitsV2/Male/KitV2_Golf_Male_Belt_correctives.json";
                File.Copy(bottom, beltJson, true); AssetDatabase.ImportAsset(beltJson);
            }
            { var bz = bv.Select(v => map.MultiplyPoint3x4(v)).ToArray(); float top = bz.Max(v => v.z); var low = bz.Where(v => v.z < top - .05f).ToArray();
              log.Add($"belt z {bz.Min(v => v.z):F4}..{top:F4}; {low.Length} verts more than 5 cm under the belt top" + (low.Length > 0 ? $", centre {new Vector3(low.Average(v => v.x), low.Average(v => v.y), low.Average(v => v.z)).ToString("F3")}" : "")); }
            EditorUtility.SetDirty(mesh); AssetDatabase.SaveAssets();
            log.Add($"belt {mesh.name} v={bv.Length} map identity={map.isIdentity}: rebound {ok}, kept {miss} (missing bones: {string.Join(",", missing)}); correctives copied from the trousers {copied}/{shapes} + Bottom RBF json; asset {AssetDatabase.GetAssetPath(mesh)}");
        }
        public static void Run()
        {
            string output = Environment.GetEnvironmentVariable("MR_OUT"); Directory.CreateDirectory(output);
            float tail = float.Parse(Environment.GetEnvironmentVariable("MR_TAIL") ?? ".09", System.Globalization.CultureInfo.InvariantCulture);
            var log = new List<string>();
            var look = AssetDatabase.LoadAssetAtPath<GameObject>(Prefab).GetComponent<MatchHeroLook>();
            SkinnedMeshRenderer P(string n) => look.kit.First(r => r && r.name == n);
            var top = P("Kit_Top"); var pants = P("Kit_Bottom"); var belt = P("Kit_Belt");
            var mesh = top.sharedMesh; string path = AssetDatabase.GetAssetPath(mesh);
            Matrix4x4 Bind(SkinnedMeshRenderer r) { int i = Array.FindIndex(r.bones, b => b && b.name == "Hips"); return r.sharedMesh.bindposes[i]; }
            var toTop = Bind(top).inverse * Bind(pants);   // pants mesh -> top mesh (expected identity)
            var tv = mesh.vertices; var pv = pants.sharedMesh.vertices.Select(v => toTop.MultiplyPoint3x4(v)).ToArray();
            var pn = pants.sharedMesh.normals.Select(n => toTop.MultiplyVector(n).normalized).ToArray();
            float beltTop = belt.sharedMesh.vertices.Select(v => (Bind(top).inverse * Bind(belt)).MultiplyPoint3x4(v).z).Max();
            float hem = tv.Min(v => v.z), bandTop = beltTop + .02f, want = beltTop - tail;
            float k = (bandTop - want) / Mathf.Max(bandTop - hem, 1e-4f);
            log.Add($"{mesh.name} v={tv.Length} shapes={mesh.blendShapeCount} toTop identity={toTop.isIdentity} beltTop {beltTop:F4} hem {hem:F4} -> {want:F4} (k {k:F3})");
            if (hem <= want + .005f) { log.Add("already long enough; nothing done"); File.WriteAllLines(Path.Combine(output, "polo_log.txt"), log); if (Application.isBatchMode) EditorApplication.Exit(0); return; }
            // bone index map pants -> top by name
            var topIndex = new Dictionary<string, int>(); for (int i = 0; i < top.bones.Length; i++) if (top.bones[i] && !topIndex.ContainsKey(top.bones[i].name)) topIndex[top.bones[i].name] = i;
            var pw = pants.sharedMesh.boneWeights; var tw = mesh.boneWeights;
            var tailVerts = new HashSet<int>(); int moved = 0, pushed = 0, rebound = 0;
            for (int i = 0; i < tv.Length; i++)
            {
                var p = tv[i]; if (p.z >= bandTop) continue;
                p.z = bandTop - (bandTop - p.z) * k; moved++;
                int bi = -1; float best = float.MaxValue;
                for (int j = 0; j < pv.Length; j++) { float d = (pv[j] - p).sqrMagnitude; if (d < best) { best = d; bi = j; } }
                if (bi >= 0)
                {   // tucked 15 mm inside the trousers under the belt (deeper than the waistband's own pose correctives move it), ramping in
                    // over the 14 mm just around the belt top so the belt's top edge covers the turn
                    float depth = TUCK * (1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(beltTop - .008f, beltTop + .006f, p.z)));
                    float side = Vector3.Dot(pn[bi], p - pv[bi]);
                    if (depth > 0 && side > -depth) { p -= pn[bi] * (side + depth); pushed++; }
                }
                if (p.z < beltTop - .012f && bi >= 0)
                {
                    var w = pw[bi];
                    string[] names = { pants.bones[w.boneIndex0].name, pants.bones[w.boneIndex1].name, pants.bones[w.boneIndex2].name, pants.bones[w.boneIndex3].name };
                    float[] ws = { w.weight0, w.weight1, w.weight2, w.weight3 };
                    bool ok = true; for (int q = 0; q < 4; q++) if (ws[q] > 0 && !topIndex.ContainsKey(names[q])) ok = false;
                    if (ok)
                    {
                        int I(int q) => ws[q] > 0 ? topIndex[names[q]] : 0;
                        tw[i] = new BoneWeight { boneIndex0 = I(0), boneIndex1 = I(1), boneIndex2 = I(2), boneIndex3 = I(3), weight0 = ws[0], weight1 = ws[1], weight2 = ws[2], weight3 = ws[3] };
                        rebound++;
                    }
                    tailVerts.Add(i);
                }
                tv[i] = p;
            }
            // blend shapes: the tail drops its corrective deltas (it now follows the waistband)
            int shapes = mesh.blendShapeCount;
            var frames = new List<(string name, float w, Vector3[] d, Vector3[] n, Vector3[] t)>();
            for (int s = 0; s < shapes; s++) for (int f = 0; f < mesh.GetBlendShapeFrameCount(s); f++)
            {
                var d = new Vector3[tv.Length]; var n = new Vector3[tv.Length]; var t = new Vector3[tv.Length];
                mesh.GetBlendShapeFrameVertices(s, f, d, n, t);
                foreach (int i in tailVerts) { d[i] = Vector3.zero; n[i] = Vector3.zero; t[i] = Vector3.zero; }
                frames.Add((mesh.GetBlendShapeName(s), mesh.GetBlendShapeFrameWeight(s, f), d, n, t));
            }
            mesh.vertices = tv; mesh.boneWeights = tw;
            if (shapes > 0) { mesh.ClearBlendShapes(); foreach (var fr in frames) mesh.AddBlendShapeFrame(fr.name, fr.w, fr.d, fr.n, fr.t); }
            mesh.RecalculateBounds();
            EditorUtility.SetDirty(mesh); AssetDatabase.SaveAssets();
            log.Add($"moved {moved}, tail (below belt) {tailVerts.Count}, pushed inside {pushed}, rebound to trouser weights {rebound}; asset {path}; new hem {tv.Min(v => v.z):F4}");
            if (Environment.GetEnvironmentVariable("MR_BELT") == "1") Belt(belt, pants, log);   // 10-19: tried, made the backswing top worse; off by default
            File.WriteAllLines(Path.Combine(output, "polo_log.txt"), log);
            if (Application.isBatchMode) EditorApplication.Exit(0);
        }
    }
}
#endif
