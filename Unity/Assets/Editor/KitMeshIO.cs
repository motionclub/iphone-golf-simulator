#if UNITY_EDITOR
using System; using System.IO; using System.Linq;
using UnityEditor; using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// KIT MESH IO (clothing-mm clone, 2026-10-30 drape-in-place): read a hero prefab's worn meshes out of the project and write a top's
    /// draped vertex positions back, nothing else (weights, bind poses, GP_Pose correctives, UVs, maps, hide lists stay as installed).
    ///   Export: env KMIO_OUT, KMIO_HEROES -> <out>/<hero>/<renderer>.bin for Kit_Top, Kit_Bottom, Kit_Belt and the body (prefab root space)
    ///   Import: env KMIO_IN, KMIO_HEROES  <- <in>/<hero>/Kit_Top_new.bin (positions + normals, root space) into the Kit_Top mesh asset
    /// bin: int nv, int nt, float3[nv] pos, float3[nv] nrm, int3[nt] tri
    public static class KitMeshIO
    {
        static readonly (string hero, string prefab)[] Heroes =
        {
            ("MatchHero_Male", "Assets/Resources/Tennis/Customization/PlayerMale.prefab"),
            ("MatchHero_Female", "Assets/Resources/Tennis/Customization/PlayerFemale.prefab"),
            ("GolfKitHero_Male", "Assets/Resources/Tennis/Customization/PlayerMaleGolfKit.prefab"),
            ("GolfKitHero_Female", "Assets/Resources/Tennis/Customization/PlayerFemaleGolfKit.prefab"),
            ("BowlingKitHero_Male", "Assets/Resources/Tennis/Customization/PlayerMaleBowlingKit.prefab"),
            ("BowlingKitHero_Female", "Assets/Resources/Tennis/Customization/PlayerFemaleBowlingKit.prefab"),
        };
        static string[] Only => (Environment.GetEnvironmentVariable("KMIO_HEROES") ?? "").Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);

        static SkinnedMeshRenderer Body(GameObject root) =>
            root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r => r.sharedMesh && !r.name.StartsWith("Kit_") && !r.name.StartsWith("Acc_"))
                .OrderByDescending(r => r.sharedMesh.vertexCount).FirstOrDefault();

        static void Write(string file, Matrix4x4 m, Mesh mesh)
        {
            var v = mesh.vertices; var n = mesh.normals; var t = mesh.triangles;
            using (var w = new BinaryWriter(File.Create(file)))
            {
                w.Write(v.Length); w.Write(t.Length / 3);
                foreach (var p in v) { var q = m.MultiplyPoint3x4(p); w.Write(q.x); w.Write(q.y); w.Write(q.z); }
                foreach (var p in n) { var q = m.MultiplyVector(p).normalized; w.Write(q.x); w.Write(q.y); w.Write(q.z); }
                foreach (var i in t) w.Write(i);
                var uv = mesh.uv; w.Write(uv.Length); foreach (var u in uv) { w.Write(u.x); w.Write(u.y); }    // appended: uv0 (older readers stop before it)
            }
        }

        public static void Export()
        {
            string dir = Environment.GetEnvironmentVariable("KMIO_OUT");
            foreach (var (hero, prefab) in Heroes)
            {
                if (Only.Length > 0 && !Only.Contains(hero)) continue;
                var root = PrefabUtility.LoadPrefabContents(prefab); string d = Path.Combine(dir, hero); Directory.CreateDirectory(d);
                var toRoot = root.transform.worldToLocalMatrix;
                foreach (var r in root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                    if (r.sharedMesh && (r.name == "Kit_Top" || r.name == "Kit_Bottom" || r.name == "Kit_Belt"))
                    { Write(Path.Combine(d, r.name + ".bin"), toRoot * r.transform.localToWorldMatrix, r.sharedMesh); Debug.Log($"[KitMeshIO] {hero} {r.name} {r.sharedMesh.vertexCount} v  {AssetDatabase.GetAssetPath(r.sharedMesh)}"); }
                var bones = new System.Collections.Generic.List<string>();
                foreach (var n in new[] { "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm", "Neck", "Hips", "Spine" })
                { var tr = root.GetComponentsInChildren<Transform>(true).FirstOrDefault(x => x.name == n); if (tr) { var q = toRoot.MultiplyPoint3x4(tr.position); bones.Add($"\"{n}\": [{q.x}, {q.y}, {q.z}]"); } }
                File.WriteAllText(Path.Combine(d, "bones.json"), "{" + string.Join(", ", bones) + "}");
                var b = Body(root);
                if (b) { Write(Path.Combine(d, "Body.bin"), toRoot * b.transform.localToWorldMatrix, b.sharedMesh); Debug.Log($"[KitMeshIO] {hero} body {b.name} {b.sharedMesh.vertexCount} v"); }
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        public static void Import()
        {
            string dir = Environment.GetEnvironmentVariable("KMIO_IN");
            foreach (var (hero, prefab) in Heroes)
            {
                if (Only.Length > 0 && !Only.Contains(hero)) continue;
                string file = Path.Combine(dir, hero, "Kit_Top_new.bin"); if (!File.Exists(file)) continue;
                var root = PrefabUtility.LoadPrefabContents(prefab);
                var r = root.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(x => x.name == "Kit_Top");
                var toMesh = (root.transform.worldToLocalMatrix * r.transform.localToWorldMatrix).inverse;
                var mesh = r.sharedMesh; var v = mesh.vertices; var n = mesh.normals;
                using (var rd = new BinaryReader(File.OpenRead(file)))
                {
                    int nv = rd.ReadInt32(); rd.ReadInt32();
                    if (nv != v.Length) throw new Exception($"{hero}: {nv} vertices in {file}, mesh has {v.Length}");
                    for (int i = 0; i < nv; i++) v[i] = toMesh.MultiplyPoint3x4(new Vector3(rd.ReadSingle(), rd.ReadSingle(), rd.ReadSingle()));
                    for (int i = 0; i < nv; i++) n[i] = toMesh.MultiplyVector(new Vector3(rd.ReadSingle(), rd.ReadSingle(), rd.ReadSingle())).normalized;
                }
                mesh.vertices = v; mesh.normals = n; mesh.RecalculateTangents(); mesh.RecalculateBounds();
                EditorUtility.SetDirty(mesh); AssetDatabase.SaveAssets();
                Debug.Log($"[KitMeshIO] {hero} Kit_Top draped positions written to {AssetDatabase.GetAssetPath(mesh)}");
                PrefabUtility.UnloadPrefabContents(root);
            }
        }
    }
}
#endif
