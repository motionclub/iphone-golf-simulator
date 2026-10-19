using System;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Tennis;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    // Clone-only inspection. Restore the complete triangle list in the fitting
    // dump: clothing coverage is a runtime presentation mask, not anatomy.
    public static class FemaleSoulfulAudit
    {
        const BindingFlags Private = BindingFlags.Static | BindingFlags.Instance | BindingFlags.NonPublic;
        public static void Run()
        {
            string folder = Environment.GetEnvironmentVariable("CV2_OUT");
            foreach (string id in new[] {"MatchHero_Female", "GolfKitHero_Female"})
            {
                object[] args = {id, null};
                var root = (GameObject)typeof(ClothingV2Dump).GetMethod("Build", Private).Invoke(null,args);
                try
                {
                    var look = root.GetComponent<MatchHeroLook>();
                    var complete = (Mesh)typeof(MatchHeroLook).GetField("kitV2CoverSource",Private).GetValue(look);
                    if (!complete || complete.vertexCount != look.body.sharedMesh.vertexCount)
                        throw new InvalidOperationException("Complete body source unavailable");
                    string dir = Path.Combine(folder,id);
                    using (var writer = new BinaryWriter(File.Create(Path.Combine(dir,"body_tri.i32"))))
                        foreach (int index in complete.triangles) writer.Write(index);
                    var face = (SkinnedMeshRenderer)look.face;
                    using (var writer = new BinaryWriter(File.Create(Path.Combine(dir,"face_pos.f32"))))
                        foreach (var p in face.sharedMesh.vertices) {writer.Write(p.x);writer.Write(p.y);writer.Write(p.z);}
                    using (var writer = new BinaryWriter(File.Create(Path.Combine(dir,"face_tri.i32"))))
                        foreach (int index in face.sharedMesh.triangles) writer.Write(index);
                    File.WriteAllLines(Path.Combine(dir,"face-materials.txt"),face.sharedMaterials.Select((m,i)=>$"{i}: {m.name} tris={face.sharedMesh.GetTriangles(i).Length/3}"));
                    Debug.Log($"[FemaleSoulful] {id} completeBody={complete.vertexCount}/{complete.triangles.Length/3} face={face.sharedMesh.vertexCount}");
                }
                finally {Object.DestroyImmediate(root);}
            }
        }
    }
}
