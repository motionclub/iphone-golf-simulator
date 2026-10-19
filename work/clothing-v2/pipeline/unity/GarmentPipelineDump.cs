using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// GARMENT PIPELINE (work/clothing-v2/pipeline): dumps each hero exactly as the game builds it, so garments can be fitted and checked
    /// against every clip without Unity in the loop.
    ///   hero.json            parts (body + every worn Kit_* / Acc_* skinned piece): bones by name, bind poses, blend shape names, submeshes
    ///   <tag>_*.f32/.i32      mesh data (pos, nrm, tri, bi, bw, uv) + <tag>_shapes.f32 (blend shape position deltas, shape-major)
    ///   body_src_tri.i32      the FULL body triangles (kitV2CoverSource, before the garment cover removed covered skin)
    ///   clips/<clip>.f32      per frame: root-space matrices of every bone named in `bones` (row-major 4x4) then every part's blend shape weights
    ///   check/<clip>_<f>.f32  BakeMesh of body + parts at a few frames, to prove the offline rebuild == Unity
    /// Per frame the runtime pose corrections run in their execution order (grip polish, arm-volume support bones, shoulder folds, garment pose
    /// correctives), exactly like LateUpdate in the game. Tool only: runs in an APFS clone, saves nothing in the project.
    /// Env: GP_OUT (abs dir), GP_FPS (30), GP_HEROES (comma list), FEMALE_ALIVE=0 recommended (breathing morphs are time driven).
    public static class GarmentPipelineDump
    {
        static readonly string[] AllHeroes = { "MatchHero_Male", "MatchHero_Female", "GolfKitHero_Male", "GolfKitHero_Female" };
        const string PrefabDir = "Assets/Resources/Tennis/Customization/";

        public static int LastCode;   // for GarmentPipelineBatch (GP_NOEXIT=1: several tools in one Editor session)

        public static void Run()
        {
            int code = 0;
            EditorUtility.audioMasterMute = true;   // every Unity run muted (also launch with GOLF_MUTE=1)
            try
            {
                string outRoot = Environment.GetEnvironmentVariable("GP_OUT");
                float fps = float.TryParse(Environment.GetEnvironmentVariable("GP_FPS"), out var f) ? f : 30f;
                string filter = Environment.GetEnvironmentVariable("GP_HEROES");
                var heroes = string.IsNullOrEmpty(filter) ? AllHeroes : filter.Split(',');
                QualitySettings.skinWeights = SkinWeights.FourBones;
                foreach (var id in heroes) DumpHero(id, Path.Combine(outRoot, id), fps);
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            LastCode = code;
            if (Application.isBatchMode && Environment.GetEnvironmentVariable("GP_NOEXIT") != "1") EditorApplication.Exit(code);
        }

        static void W(string path, float[] data) { using var w = new BinaryWriter(File.Create(path)); foreach (var x in data) w.Write(x); }
        static void W(string path, int[] data) { using var w = new BinaryWriter(File.Create(path)); foreach (var x in data) w.Write(x); }
        static float[] V3(Vector3[] v) { var a = new float[v.Length * 3]; for (int i = 0; i < v.Length; i++) { a[i * 3] = v[i].x; a[i * 3 + 1] = v[i].y; a[i * 3 + 2] = v[i].z; } return a; }
        static void M(List<float> o, Matrix4x4 m) { for (int r = 0; r < 4; r++) for (int c = 0; c < 4; c++) o.Add(m[r, c]); }   // row-major
        static string J(Matrix4x4 m) { var l = new List<float>(); M(l, m); return "[" + string.Join(",", l.Select(x => x.ToString("R", System.Globalization.CultureInfo.InvariantCulture))) + "]"; }
        static string Q(string s) => "\"" + s.Replace("\"", "'") + "\"";

        static GameObject Build(string id, out List<(AnimationClip clip, string source)> clips)
        {
            bool golf = id.StartsWith("GolfKit"), female = id.EndsWith("Female");
            string sex = female ? "Female" : "Male";
            GameObject root;
            if (golf)
            {
                var golfer = HeroGolfer.Build(null, new HeroLook { Female = female, Haircut = (int)HeroGolfer.Haircut.Bald, Skin = female ? new Color(.953f, .855f, .788f) : new Color(.949f, .816f, .686f), HairColor = new Color(.35f, .25f, .18f) });
                root = golfer.Root;
            }
            else root = (GameObject)Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "Player" + sex + ".prefab"));
            root.name = id;
            root.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity); root.transform.localScale = Vector3.one;
            var driver = root.GetComponent<HeroTennisDriver>();
            if (driver) driver.ResolvePerformanceClips();
            var look = root.GetComponent<MatchHeroLook>();
            typeof(MatchHeroLook).GetMethod("OwnMaterials", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(look, null);
            // what Awake attaches in the game
            if (!look.GetComponent<HeroGripPolish>()) look.gameObject.AddComponent<HeroGripPolish>().look = look;
            KitV2PoseCorrectives.Attach(look);
            foreach (var smr in root.GetComponentsInChildren<SkinnedMeshRenderer>(true)) { smr.quality = SkinQuality.Bone4; smr.updateWhenOffscreen = true; }
            clips = new List<(AnimationClip, string)>();
            if (golf) clips.AddRange(Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(female)).Where(c => !c.name.StartsWith("__preview__")).Select(c => (c, "golf")));
            else clips.AddRange(driver.slots.Where(s => s.clip).Select(s => s.clip).Distinct().Select(c => (c, "tennis")));
            clips.AddRange(Resources.LoadAll<AnimationClip>("HeroMoves/" + sex).Where(c => !c.name.StartsWith("__preview__")).Select(c => (c, "moves")));
            return root;
        }

        /// LateUpdate of the runtime pose components, in execution order (garment correctives last).
        static void RuntimeCorrections(GameObject root, bool golfSwing)
        {
            var look = root.GetComponent<MatchHeroLook>();
            if (look.golfKit) { if (golfSwing) HeroGripPolish.ApplyGolfGrip(look); }
            else HeroGripPolish.ApplyGrip(look);
            look.body.GetComponent<HeroArmSkinning>()?.Apply();
            root.GetComponent<HeroShoulderDeformation>()?.Apply();
            root.GetComponent<KitV2PoseCorrectives>()?.Apply();
        }

        static void RestPose(GameObject root)
        {
            var body = root.GetComponent<MatchHeroLook>().body;
            var bones = body.bones; var bind = body.sharedMesh.bindposes; var l2w = body.transform.localToWorldMatrix;
            int Depth(Transform t) { int d = 0; for (; t; t = t.parent) d++; return d; }
            foreach (int i in Enumerable.Range(0, bones.Length).Where(i => bones[i]).OrderBy(i => Depth(bones[i])))
            {
                var m = l2w * bind[i].inverse;
                bones[i].SetPositionAndRotation(m.GetColumn(3), Quaternion.LookRotation(m.GetColumn(2), m.GetColumn(1)));
            }
        }

        static string DumpSkinned(SkinnedMeshRenderer r, Mesh mesh, string dir, string tag, string kind)
        {
            W(Path.Combine(dir, tag + "_pos.f32"), V3(mesh.vertices));
            W(Path.Combine(dir, tag + "_nrm.f32"), V3(mesh.normals));
            var tris = new List<int>(); var subs = new List<string>();
            for (int s = 0; s < mesh.subMeshCount; s++)
            {
                var t = mesh.GetTriangles(s); subs.Add($"{{\"start\":{tris.Count / 3},\"count\":{t.Length / 3},\"material\":{Q(s < r.sharedMaterials.Length && r.sharedMaterials[s] ? r.sharedMaterials[s].name : "")}}}");
                tris.AddRange(t);
            }
            W(Path.Combine(dir, tag + "_tri.i32"), tris.ToArray());
            var bw = mesh.boneWeights; var wi = new int[bw.Length * 4]; var ww = new float[bw.Length * 4];
            for (int i = 0; i < bw.Length; i++)
            {
                wi[i * 4] = bw[i].boneIndex0; wi[i * 4 + 1] = bw[i].boneIndex1; wi[i * 4 + 2] = bw[i].boneIndex2; wi[i * 4 + 3] = bw[i].boneIndex3;
                ww[i * 4] = bw[i].weight0; ww[i * 4 + 1] = bw[i].weight1; ww[i * 4 + 2] = bw[i].weight2; ww[i * 4 + 3] = bw[i].weight3;
            }
            W(Path.Combine(dir, tag + "_bi.i32"), wi); W(Path.Combine(dir, tag + "_bw.f32"), ww);
            if (mesh.uv.Length == mesh.vertexCount) W(Path.Combine(dir, tag + "_uv.f32"), mesh.uv.SelectMany(u => new[] { u.x, u.y }).ToArray());
            var shapes = new List<float>(); var shapeNames = new List<string>();
            var dv = new Vector3[mesh.vertexCount]; var dn = new Vector3[mesh.vertexCount]; var dt = new Vector3[mesh.vertexCount];
            for (int s = 0; s < mesh.blendShapeCount; s++)
            {
                int fc = mesh.GetBlendShapeFrameCount(s);
                mesh.GetBlendShapeFrameVertices(s, fc - 1, dv, dn, dt);
                float fw = mesh.GetBlendShapeFrameWeight(s, fc - 1);
                foreach (var d in dv) { shapes.Add(d.x * 100 / fw); shapes.Add(d.y * 100 / fw); shapes.Add(d.z * 100 / fw); }   // delta at weight 100
                shapeNames.Add(mesh.GetBlendShapeName(s) + (fc > 1 ? "#frames" + fc : ""));
            }
            if (shapes.Count > 0) W(Path.Combine(dir, tag + "_shapes.f32"), shapes.ToArray());
            var sb = new StringBuilder();
            sb.Append($"{{\"tag\":{Q(tag)},\"name\":{Q(r.name)},\"kind\":{Q(kind)},\"enabled\":{(r.enabled && r.gameObject.activeInHierarchy ? "true" : "false")},\"mesh\":{Q(mesh.name)},\"vertexCount\":{mesh.vertexCount},\"submeshes\":[{string.Join(",", subs)}],");
            sb.Append($"\"bones\":[{string.Join(",", r.bones.Select(b => Q(b ? b.name : "")))}],");
            sb.Append($"\"bindposes\":[{string.Join(",", mesh.bindposes.Select(J))}],\"rendererToRoot\":{J(r.transform.localToWorldMatrix)},");
            sb.Append($"\"blendShapes\":[{string.Join(",", shapeNames.Select(Q))}]}}");
            return sb.ToString();
        }

        static void DumpHero(string id, string dir, float fps)
        {
            Directory.CreateDirectory(dir); Directory.CreateDirectory(Path.Combine(dir, "clips")); Directory.CreateDirectory(Path.Combine(dir, "check"));
            var root = Build(id, out var clips);
            try
            {
                var look = root.GetComponent<MatchHeroLook>();
                var body = look.body;
                RestPose(root); RuntimeCorrections(root, false);
                var src = (Mesh)typeof(MatchHeroLook).GetField("kitV2CoverSource", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(look) ?? body.sharedMesh;
                if (src.vertexCount != body.sharedMesh.vertexCount) throw new InvalidOperationException("cover source vertex count differs from the live body");
                var parts = new List<SkinnedMeshRenderer> { body };
                var tags = new List<string> { "body" };
                var json = new List<string> { DumpSkinned(body, body.sharedMesh, dir, "body", "body") };
                W(Path.Combine(dir, "body_src_tri.i32"), src.triangles);
                foreach (var k in root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r => r != body && r.sharedMesh && (r.name.StartsWith("Kit_") || r.name.StartsWith("Acc_"))))
                {
                    if (!(k.enabled && k.gameObject.activeInHierarchy)) continue;          // only what the hero wears
                    if (k.bones.Length > 0 && k.bones.Any(b => !b)) continue;
                    string tag = k.name; int dup = 2; while (tags.Contains(tag)) tag = k.name + "_" + dup++;
                    parts.Add(k); tags.Add(tag);
                    json.Add(DumpSkinned(k, k.sharedMesh, dir, tag, k.name.StartsWith("Acc_") ? "accessory" : "kit"));
                }
                // every bone any part is skinned to, by name (the body's palette first)
                var boneT = new List<Transform>();
                foreach (var p in parts) foreach (var b in p.bones) if (b && !boneT.Contains(b)) boneT.Add(b);
                var w2r = root.transform.worldToLocalMatrix;
                var clipJson = new List<string>();
                var baked = new Mesh();
                int clipIndex = 0;
                foreach (var (clip, source) in clips)
                {
                    int n = Mathf.Max(2, Mathf.CeilToInt(clip.length * fps) + 1);
                    var data = new List<float>();
                    string safe = source + "__" + clip.name.Replace("/", "_").Replace(" ", "_");
                    for (int fi = 0; fi < n; fi++)
                    {
                        float t = clip.length * fi / (n - 1);
                        clip.SampleAnimation(root, t);
                        RuntimeCorrections(root, source == "golf");
                        foreach (var b in boneT) M(data, w2r * b.localToWorldMatrix);
                        foreach (var p in parts) for (int s = 0; s < p.sharedMesh.blendShapeCount; s++) data.Add(p.GetBlendShapeWeight(s));
                        if ((fi == n / 2 && clipIndex % 4 == 0) || (fi == 0 && clipIndex == 0))
                            for (int pi = 0; pi < parts.Count; pi++)
                            {
                                parts[pi].BakeMesh(baked, true);
                                var pl = w2r * Matrix4x4.TRS(parts[pi].transform.position, parts[pi].transform.rotation, Vector3.one);
                                W(Path.Combine(dir, "check", $"{safe}_{fi}_{tags[pi]}.f32"), V3(baked.vertices.Select(v => pl.MultiplyPoint3x4(v)).ToArray()));
                            }
                    }
                    W(Path.Combine(dir, "clips", safe + ".f32"), data.ToArray());
                    clipJson.Add($"{{\"name\":{Q(clip.name)},\"source\":{Q(source)},\"file\":{Q(safe)},\"length\":{clip.length:R},\"frames\":{n},\"loop\":{(clip.isLooping ? "true" : "false")}}}");
                    clipIndex++;
                }
                Object.DestroyImmediate(baked);
                var allT = root.GetComponentsInChildren<Transform>(true);
                var rig = "{" + string.Join(",", allT.GroupBy(t => t.name).Select(g => Q(g.Key) + ":" + J(w2r * g.First().localToWorldMatrix))) + "}";
                File.WriteAllText(Path.Combine(dir, "hero.json"),
                    $"{{\"id\":{Q(id)},\"fps\":{fps:R},\"bodyToRoot\":{J(w2r * Matrix4x4.TRS(body.transform.position, body.transform.rotation, Vector3.one))},\"bones\":[{string.Join(",", boneT.Select(b => Q(b.name)))}],\"parts\":[{string.Join(",", json)}],\"clips\":[{string.Join(",", clipJson)}],\"rig\":{rig}}}");
                Debug.Log($"[GP] dumped {id}: body v={body.sharedMesh.vertexCount} parts={parts.Count} bones={boneT.Count} clips={clips.Count}");
            }
            finally { Object.DestroyImmediate(root); }
        }
    }
}
