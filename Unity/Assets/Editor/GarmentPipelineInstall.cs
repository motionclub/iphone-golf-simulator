using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// GARMENT PIPELINE (work/clothing-v2/GARMENT_PIPELINE.md): installs what work/clothing-v2/pipeline fitted onto the garment the hero
    /// already wears. The mesh asset is PATCHED, not rebuilt: geometry, UVs, normals, tangents, colours and submeshes stay byte-identical;
    /// only skin weights, bind poses and the pose-corrective blend shapes (GP_PoseNN replace any CV2_PoseNN) change. The renderer's bones
    /// and MatchHeroLook.kitV2Bones follow the new palette; the mesh name gets " [gp]" (old per-garment runtime binders skip such meshes).
    /// Per piece in work/clothing-v2/pipeline/out/<Hero>/: <Tag>.gp.json + .gp.bin, optional <Tag>_correctives.json (-> Resources
    /// ..._correctives.json, featureMode gp-rbf, read by GarmentPoseCorrectives) and <Tag>_hide.bin (-> ..._hide.bytes, the skin cover).
    /// Per hero: garment_offsets.json -> Resources/<Sport>/KitsV2/<Sex>/KitV2_<Sport>_<Sex>_offsets.json (chat 3 clearance proxies).
    /// Env GP_OUT (default ../work/clothing-v2/pipeline/out), GP_HEROES (comma list). Run in an APFS clone; GOLF_MUTE=1.
    public static class GarmentPipelineInstall
    {
        static readonly (string hero, string prefab)[] Heroes =
        {
            ("MatchHero_Male", "Assets/Resources/Tennis/Customization/PlayerMale.prefab"),
            ("MatchHero_Female", "Assets/Resources/Tennis/Customization/PlayerFemale.prefab"),
            ("GolfKitHero_Male", "Assets/Resources/Tennis/Customization/PlayerMaleGolfKit.prefab"),
            ("GolfKitHero_Female", "Assets/Resources/Tennis/Customization/PlayerFemaleGolfKit.prefab"),
        };
        [Serializable] class Patch { public string tag; public int vertexCount; public string[] bones; public float[] bindposes; public string[] shapes; }

        static string Source => Environment.GetEnvironmentVariable("GP_OUT") ?? Path.GetFullPath(Path.Combine(Application.dataPath, "../../work/clothing-v2/pipeline/out"));

        public static int LastCode;   // for GarmentPipelineBatch (GP_NOEXIT=1: several tools in one Editor session)

        public static void Run()
        {
            int code = 0;
            EditorUtility.audioMasterMute = true;
            try
            {
                var log = new StringBuilder();
                string only = Environment.GetEnvironmentVariable("GP_HEROES");
                foreach (var h in Heroes)
                    if (string.IsNullOrEmpty(only) || only.Split(',').Contains(h.hero)) log.Append(Install(h.hero, h.prefab));
                AssetDatabase.SaveAssets(); AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                File.WriteAllText(Path.Combine(Source, "install_report.txt"), log.ToString());
                Debug.Log("[GarmentPipeline] " + log);
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            LastCode = code;
            if (Application.isBatchMode && Environment.GetEnvironmentVariable("GP_NOEXIT") != "1") EditorApplication.Exit(code);
        }

        static void CopyIfChanged(string src, string dst)
        {
            if (!File.Exists(src)) return;
            Directory.CreateDirectory(Path.GetDirectoryName(dst));
            if (!File.Exists(dst) || !File.ReadAllBytes(src).SequenceEqual(File.ReadAllBytes(dst))) File.Copy(src, dst, true);
        }

        static string Install(string hero, string prefabPath)
        {
            var sb = new StringBuilder();
            string dir = Path.Combine(Source, hero);
            if (!Directory.Exists(dir)) return sb.ToString();
            string sport = hero.StartsWith("Golf") ? "Golf" : "Tennis", sex = hero.EndsWith("Female") ? "Female" : "Male";
            string res = $"Assets/Resources/{sport}/KitsV2/{sex}/";
            var root = PrefabUtility.LoadPrefabContents(prefabPath);
            try
            {
                var look = root.GetComponent<MatchHeroLook>();
                var byName = new Dictionary<string, Transform>();
                foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (!byName.ContainsKey(t.name)) byName[t.name] = t;
                var kit = look.kit.ToList();
                var names = (look.kitV2Bones ?? new MatchHeroLook.KitBones[0]).ToList();
                while (names.Count < kit.Count) names.Add(null);
                foreach (var jf in Directory.GetFiles(dir, "*.gp.json").OrderBy(f => f))
                {
                    var p = JsonUtility.FromJson<Patch>(File.ReadAllText(jf));
                    int slot = kit.FindIndex(r => r && r.name == p.tag);
                    if (slot < 0) throw new InvalidOperationException($"{hero}: no kit renderer {p.tag} on {prefabPath}");
                    var r = kit[slot];
                    var mesh = r.sharedMesh;
                    string meshPath = AssetDatabase.GetAssetPath(mesh);
                    if (string.IsNullOrEmpty(meshPath) || !meshPath.EndsWith(".asset")) throw new InvalidOperationException($"{hero} {p.tag}: mesh {mesh.name} is not a .asset ({meshPath})");
                    if (mesh.vertexCount != p.vertexCount) throw new InvalidOperationException($"{hero} {p.tag}: patch has {p.vertexCount} vertices, mesh {mesh.vertexCount}");
                    var bytes = File.ReadAllBytes(Path.Combine(dir, p.tag + ".gp.bin"));
                    int n = p.vertexCount, off = 0, S = p.shapes?.Length ?? 0;
                    int I() { int v = BitConverter.ToInt32(bytes, off); off += 4; return v; }
                    float F() { float v = BitConverter.ToSingle(bytes, off); off += 4; return v; }
                    var bi = new int[n * 4]; for (int i = 0; i < bi.Length; i++) bi[i] = I();
                    var bw = new float[n * 4]; for (int i = 0; i < bw.Length; i++) bw[i] = F();
                    var shapes = new Vector3[S][];
                    for (int s = 0; s < S; s++) { shapes[s] = new Vector3[n]; for (int i = 0; i < n; i++) shapes[s][i] = new Vector3(F(), F(), F()); }
                    var rest = new Vector3[n]; for (int i = 0; i < n; i++) rest[i] = new Vector3(F(), F(), F());
                    var v0 = mesh.vertices; float err = 0;
                    for (int i = 0; i < n; i++) err = Mathf.Max(err, (v0[i] - rest[i]).magnitude);
                    if (err > 5e-5f) throw new InvalidOperationException($"{hero} {p.tag}: patch geometry differs from the mesh by {err * 1000:F3} mm (re-dump / re-fit)");
                    var weights = new BoneWeight[n];
                    for (int i = 0; i < n; i++)
                        weights[i] = new BoneWeight { boneIndex0 = bi[i * 4], boneIndex1 = bi[i * 4 + 1], boneIndex2 = bi[i * 4 + 2], boneIndex3 = bi[i * 4 + 3],
                            weight0 = bw[i * 4], weight1 = bw[i * 4 + 1], weight2 = bw[i * 4 + 2], weight3 = bw[i * 4 + 3] };
                    var binds = new Matrix4x4[p.bones.Length];
                    for (int b = 0; b < binds.Length; b++) { var m = new Matrix4x4(); for (int k = 0; k < 16; k++) m[k % 4, k / 4] = p.bindposes[b * 16 + k]; binds[b] = m; }
                    // keep every non-corrective blend shape, drop old pose correctives, add the pipeline's
                    var keep = new List<(string name, float w, Vector3[] d, Vector3[] nn, Vector3[] tt)>();
                    for (int s = 0; s < mesh.blendShapeCount; s++)
                    {
                        string nm = mesh.GetBlendShapeName(s);
                        if (nm.StartsWith("CV2_Pose") || nm.StartsWith("GP_Pose")) continue;
                        for (int fr = 0; fr < mesh.GetBlendShapeFrameCount(s); fr++)
                        {
                            var d = new Vector3[n]; var nn = new Vector3[n]; var tt = new Vector3[n];
                            mesh.GetBlendShapeFrameVertices(s, fr, d, nn, tt); keep.Add((nm, mesh.GetBlendShapeFrameWeight(s, fr), d, nn, tt));
                        }
                    }
                    mesh.ClearBlendShapes();
                    foreach (var k in keep) mesh.AddBlendShapeFrame(k.name, k.w, k.d, k.nn, k.tt);
                    for (int s = 0; s < S; s++) mesh.AddBlendShapeFrame(p.shapes[s], 100, shapes[s], NormalDelta(mesh, shapes[s]), null);
                    mesh.boneWeights = weights; mesh.bindposes = binds;
                    if (!mesh.name.EndsWith(" [gp]")) mesh.name += " [gp]";
                    var bounds = mesh.bounds; bounds.Expand(.04f); mesh.bounds = bounds;
                    EditorUtility.SetDirty(mesh);
                    r.bones = p.bones.Select(b => byName.TryGetValue(b, out var t) ? t : b.StartsWith("ArmBlend_") ? look.body.transform : throw new InvalidOperationException($"{hero} {p.tag}: bone {b} missing")).ToArray();
                    names[slot] = new MatchHeroLook.KitBones { names = p.bones };
                    string tag = p.tag.Substring(4).Replace("_", "");
                    string corr = Path.Combine(dir, p.tag + "_correctives.json"), corrDst = res + $"KitV2_{sport}_{sex}_{tag}_correctives.json";
                    if (File.Exists(corr)) CopyIfChanged(corr, corrDst);
                    else if (S == 0 && File.Exists(corrDst) && File.ReadAllText(corrDst).Contains("\"gp-rbf\"")) AssetDatabase.DeleteAsset(corrDst);
                    sb.AppendLine($"  {hero} {p.tag}: weights + {p.bones.Length} bones, {S} pose correctives, max rest error {err * 1000:F4} mm ({meshPath})");
                }
                // the skin cover is solved for the whole worn set: every piece's hide list is replaced (empty file = hides nothing)
                foreach (var hf in Directory.GetFiles(dir, "Kit_*_hide.bin"))
                {
                    string piece = Path.GetFileName(hf).Replace("_hide.bin", "");
                    CopyIfChanged(hf, res + $"KitV2_{sport}_{sex}_{piece.Substring(4).Replace("_", "")}_hide.bytes");
                    sb.AppendLine($"  {hero} {piece}: hide list {new FileInfo(hf).Length / 12} triangles");
                }
                CopyIfChanged(Path.Combine(dir, "garment_offsets.json"), res + $"KitV2_{sport}_{sex}_offsets.json");
                look.kitV2Bones = names.ToArray();
                PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            return sb.ToString();
        }

        static Vector3[] NormalDelta(Mesh mesh, Vector3[] delta)
        {
            var p = mesh.vertices; var tris = mesh.triangles; var a = new Vector3[p.Length]; var b = new Vector3[p.Length];
            for (int i = 0; i < tris.Length; i += 3)
            {
                int x = tris[i], y = tris[i + 1], z = tris[i + 2];
                var n0 = Vector3.Cross(p[y] - p[x], p[z] - p[x]);
                var n1 = Vector3.Cross(p[y] + delta[y] - p[x] - delta[x], p[z] + delta[z] - p[x] - delta[x]);
                a[x] += n0; a[y] += n0; a[z] += n0; b[x] += n1; b[y] += n1; b[z] += n1;
            }
            var src = mesh.normals; var o = new Vector3[p.Length];
            for (int i = 0; i < p.Length; i++) if ((a[i] - b[i]).sqrMagnitude > 1e-18f) o[i] = Quaternion.FromToRotation(a[i], b[i]) * src[i] - src[i];
            return o;
        }
    }
}
