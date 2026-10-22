#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Tennis;
using UnityEngine;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class FemaleDeformationDiagnostic {
  public static void Capture(MatchHeroLook look,string folder) {
   Directory.CreateDirectory(folder);
   var body=look.body;var mesh=body.sharedMesh;var materials=body.sharedMaterials;
   var complete=(Mesh)typeof(MatchHeroLook).GetField("kitV2CoverSource",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(look);
   var top=look.kit.First(r=>r&&r.name=="Kit_Top");bool topOn=top.enabled;
   var full=Object.Instantiate(mesh);full.triangles=complete.triangles;
   var unlit=new Material(Shader.Find("Universal Render Pipeline/Unlit"));unlit.SetColor("_BaseColor",new Color(.84f,.62f,.43f));
   var baked=new Mesh();GameObject staticBody=null;
   void Shot(string name) {typeof(FemaleAliveCapture).GetMethod("Detail",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,new object[]{look,Path.Combine(folder,name+".jpg")});}
   void Dump(string name,Mesh m) {
    using var w=new BinaryWriter(File.Create(Path.Combine(folder,name+".bin")));
    w.Write(m.vertexCount);w.Write(m.triangles.Length);
    foreach(var v in m.vertices){w.Write(v.x);w.Write(v.y);w.Write(v.z);}
    foreach(var v in m.normals){w.Write(v.x);w.Write(v.y);w.Write(v.z);}
    foreach(var i in m.triangles)w.Write(i);
   }
   try {
    Shot("00-original");top.enabled=false;
    Shot("01-body-lit");body.BakeMesh(baked);Dump("original-posed",baked);
    body.sharedMaterials=materials.Select(_=>unlit).ToArray();unlit.SetFloat("_Cull",2);Shot("02-unlit-masked");
    body.sharedMesh=full;Shot("03-unlit-full");unlit.SetFloat("_Cull",0);Shot("04-unlit-full-double-sided");
    body.BakeMesh(baked);Dump("full-posed",baked);
    var staticMesh=Object.Instantiate(full);staticMesh.ClearBlendShapes();staticMesh.vertices=baked.vertices;staticMesh.RecalculateNormals();staticMesh.RecalculateBounds();
    staticBody=new GameObject("Diagnostic static body");staticBody.transform.SetPositionAndRotation(body.transform.position,body.transform.rotation);staticBody.transform.localScale=body.transform.lossyScale;
    staticBody.AddComponent<MeshFilter>().sharedMesh=staticMesh;var renderer=staticBody.AddComponent<MeshRenderer>();renderer.sharedMaterials=materials;renderer.renderingLayerMask=body.renderingLayerMask;
    body.enabled=false;Shot("05-recalculated-posed-normals");body.enabled=true;Object.DestroyImmediate(staticBody);Object.DestroyImmediate(staticMesh);staticBody=null;
    for(int i=0;i<full.blendShapeCount;i++)if(full.GetBlendShapeName(i).StartsWith("ShoulderFold_"))body.SetBlendShapeWeight(i,0);
    body.sharedMaterials=materials;Shot("06-no-shoulder-fold");body.BakeMesh(baked);Dump("no-fold-posed",baked);
    top.enabled=true;Shot("07-no-fold-with-tank");
    File.WriteAllText(Path.Combine(folder,"info.json"),JsonUtility.ToJson(new Info {mesh=mesh.name,vertices=mesh.vertexCount,currentTriangles=mesh.triangles.Length/3,fullTriangles=full.triangles.Length/3,bones=body.bones.Length,clip=look.GetComponent<HeroTennisDriver>().PlayingClip,time=look.GetComponent<HeroTennisDriver>().PlayingClipTime},true));
   }finally {body.sharedMesh=mesh;body.sharedMaterials=materials;body.enabled=true;top.enabled=topOn;look.GetComponent<HeroShoulderDeformation>().Apply();if(staticBody)Object.DestroyImmediate(staticBody);Object.DestroyImmediate(full);Object.DestroyImmediate(unlit);Object.DestroyImmediate(baked);}
  }
  [Serializable]class Info {public string mesh,clip;public int vertices,currentTriangles,fullTriangles,bones;public float time;}
 }
}
#endif
