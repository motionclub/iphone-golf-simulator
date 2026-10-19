using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// CLONE-ONLY (10-17 male cap re-hug): splits AccessoriesClipCheck's "skin inside the cap" vertices by body region (dominant bone:
    /// head/neck, hand/arm, other), same test (+Y ray parity through the cap + within 20 mm of it), Unity skinning. Writes CSV to CAPPROBE_OUT.
    /// Env: CAPPROBE_OUT, CAPPROBE_HEROES, CAPPROBE_FILTER (regex), CAPPROBE_FPS (10)
    public static class CapRegionProbe
    {
        public static void RunBatch()
        {
            int code = 0;
            try { Run(); } catch (Exception e) { Debug.LogException(e); code = 1; }
            EditorApplication.Exit(code);
        }

        static Vector3[] World(SkinnedMeshRenderer r, Mesh scratch, out int[] tris)
        {
            r.BakeMesh(scratch, true);
            var m = Matrix4x4.TRS(r.transform.position, r.transform.rotation, Vector3.one);
            var v = scratch.vertices; for (int i = 0; i < v.Length; i++) v[i] = m.MultiplyPoint3x4(v[i]);
            tris = scratch.triangles; return v;
        }

        static bool Parity(Vector3 q, Vector3[] P, int[] T)
        {
            int hits = 0;
            for (int i = 0; i < T.Length; i += 3)
            {
                Vector3 a = P[T[i]], b = P[T[i + 1]], c = P[T[i + 2]];
                if (q.x < Mathf.Min(a.x, Mathf.Min(b.x, c.x)) || q.x > Mathf.Max(a.x, Mathf.Max(b.x, c.x)) || q.z < Mathf.Min(a.z, Mathf.Min(b.z, c.z)) || q.z > Mathf.Max(a.z, Mathf.Max(b.z, c.z))) continue;
                if (Mathf.Max(a.y, Mathf.Max(b.y, c.y)) < q.y) continue;
                Vector3 e1 = b - a, e2 = c - a, pv = new Vector3(e2.z, 0, -e2.x);
                float det = Vector3.Dot(e1, pv); if (Mathf.Abs(det) < 1e-12f) continue;
                float inv = 1f / det; Vector3 tv = q - a; float u = Vector3.Dot(tv, pv) * inv; if (u < 0 || u > 1) continue;
                Vector3 qv = Vector3.Cross(tv, e1); float v = qv.y * inv; if (v < 0 || u + v > 1) continue;
                if (Vector3.Dot(e2, qv) * inv > 1e-6f) hits++;
            }
            return (hits & 1) == 1;
        }

        static float MinDist(Vector3 q, Vector3[] P)
        {
            float d = float.MaxValue; foreach (var p in P) d = Mathf.Min(d, (p - q).sqrMagnitude); return Mathf.Sqrt(d);
        }

        static void Run()
        {
            var inv = CultureInfo.InvariantCulture;
            string outDir = Environment.GetEnvironmentVariable("CAPPROBE_OUT"); Directory.CreateDirectory(outDir);
            var rx = new Regex(Environment.GetEnvironmentVariable("CAPPROBE_FILTER") ?? ".", RegexOptions.IgnoreCase);
            float fps = float.Parse(Environment.GetEnvironmentVariable("CAPPROBE_FPS") ?? "10", inv);
            var heroes = (Environment.GetEnvironmentVariable("CAPPROBE_HEROES") ?? "MatchHero_Male,GolfKitHero_Male").Split(',');
            var keep = QualitySettings.skinWeights; QualitySettings.skinWeights = SkinWeights.FourBones;
            var csv = new StringBuilder("hero,clip,frames,head_n,head_mm,head_t,hand_n,hand_mm,hand_t,other_n,other_mm,other_t\n");
            foreach (var id in heroes)
            {
                var root = AccessoriesProof.BuildHero(id, out var idle);
                var look = root.GetComponent<MatchHeroLook>();
                var acc = HeroAccessories.For(look);
                var clips = AccessoriesProof.ClipsFor(id, root);
                var bodyR = look.body; var bones = bodyR.bones; var bw = bodyR.sharedMesh.boneWeights;
                var region = new int[bw.Length];   // 0 head/neck, 1 hand/arm, 2 other
                for (int i = 0; i < bw.Length; i++)
                {
                    var b = bw[i]; int bi = b.boneIndex0; float w = b.weight0;
                    if (b.weight1 > w) { bi = b.boneIndex1; w = b.weight1; } if (b.weight2 > w) { bi = b.boneIndex2; w = b.weight2; } if (b.weight3 > w) { bi = b.boneIndex3; }
                    string n = bi >= 0 && bi < bones.Length && bones[bi] ? bones[bi].name : "";
                    region[i] = (n.Contains("Head") || n.Contains("Neck") || n.Contains("Jaw") || n.Contains("Eye")) ? 0
                        : (n.Contains("Hand") || n.Contains("Thumb") || n.Contains("Index") || n.Contains("Middle") || n.Contains("Ring") || n.Contains("Little") || n.Contains("Arm")) ? 1 : 2;
                }
                var scratch = new Mesh();
                foreach (var name in clips.Keys.Where(n => rx.IsMatch(n)).OrderBy(n => n, StringComparer.Ordinal))
                {
                    var clip = clips[name]; int nf = Mathf.Max(2, Mathf.CeilToInt(clip.length * fps) + 1);
                    var cnt = new int[3]; var mm = new float[3]; var tt = new float[3] { -1, -1, -1 };
                    for (int f = 0; f < nf; f++)
                    {
                        float t = Mathf.Min(clip.length, f / fps);
                        AccessoriesProof.Pose(root, idle, $"{name}@{t.ToString(inv)}", clips);
                        var cap = acc.AllRenderers().FirstOrDefault(r => r.enabled && r.name == "Acc_Cap"); if (!cap) continue;
                        var av = World(cap, scratch, out var at);
                        var bnd = new Bounds(av[0], Vector3.zero); foreach (var v in av) bnd.Encapsulate(v); bnd.Expand(.04f);
                        var bv = World(bodyR, scratch, out _);
                        for (int i = 0; i < bv.Length; i++)
                        {
                            if (!bnd.Contains(bv[i])) continue;
                            float d = MinDist(bv[i], av); if (d > .02f) continue;
                            if (!Parity(bv[i], av, at)) continue;
                            int r = region[i]; cnt[r]++; if (d * 1000 > mm[r]) { mm[r] = d * 1000; tt[r] = t; }
                        }
                    }
                    csv.AppendLine($"{id},{name},{nf},{cnt[0]},{mm[0].ToString("F1", inv)},{tt[0].ToString("F2", inv)},{cnt[1]},{mm[1].ToString("F1", inv)},{tt[1].ToString("F2", inv)},{cnt[2]},{mm[2].ToString("F1", inv)},{tt[2].ToString("F2", inv)}");
                    Debug.Log($"[CapRegionProbe] {id} {name}: head {cnt[0]}/{mm[0]:F1}mm hand {cnt[1]}/{mm[1]:F1}mm other {cnt[2]}/{mm[2]:F1}mm");
                }
                UnityEngine.Object.DestroyImmediate(scratch); UnityEngine.Object.DestroyImmediate(root);
            }
            QualitySettings.skinWeights = keep;
            File.WriteAllText(Path.Combine(outDir, "cap_region_probe.csv"), csv.ToString());
        }
    }
}
