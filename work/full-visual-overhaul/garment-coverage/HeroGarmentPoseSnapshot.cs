using System;
using System.IO;
using System.Linq;
using UnityEngine;
using GolfArcade.Tennis;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 /// Optional source data for a corrective. Never modifies the live pose.
 public static class HeroGarmentPoseSnapshot {
  [Serializable] public class Part {public string name;public float[] vertices,normals,posedVertices,posedNormals,uv,weights,bindposes,skinMatrices,rendererToRoot;public int[] triangles,indices;public string[] bones;public float bakeOracleMaxMetres;}
  [Serializable] public class Report {public string label,sex,sport;public Part[] parts;}
  public static void Save(MatchHeroLook hero,string label,string output){
   if(string.IsNullOrEmpty(output)||!hero)return;
   Directory.CreateDirectory(output);
   var renderers=new[]{hero.body}.Concat(hero.kit.Where(r=>r&&r.name=="Kit_Top")).Where(r=>r&&r.sharedMesh.isReadable).ToArray();
   var report=new Report{label=label,sex=hero.female?"Female":"Male",sport=hero.golfKit?"Golf":"Tennis",parts=renderers.Select(Read).ToArray()};
   File.WriteAllText(Path.Combine(output,label+".json"),JsonUtility.ToJson(report));
  }
  static Part Read(SkinnedMeshRenderer r){
   var m=r.sharedMesh;var bake=new Mesh();r.BakeMesh(bake);var p=m.vertices;var w=m.boneWeights;
   var matrices=r.bones.Select((b,i)=>r.transform.worldToLocalMatrix*b.localToWorldMatrix*m.bindposes[i]).ToArray();
   float max=0;var expected=bake.vertices;
   var shapePositions=(Vector3[])p.Clone();
   for(int s=0;s<m.blendShapeCount;s++){
    float amount=r.GetBlendShapeWeight(s)/m.GetBlendShapeFrameWeight(s,m.GetBlendShapeFrameCount(s)-1);if(Mathf.Abs(amount)<.000001f)continue;
    var delta=new Vector3[p.Length];m.GetBlendShapeFrameVertices(s,m.GetBlendShapeFrameCount(s)-1,delta,null,null);for(int i=0;i<p.Length;i++)shapePositions[i]+=delta[i]*amount;
   }
   for(int i=0;i<p.Length;i++){
    var b=w[i];var predicted=matrices[b.boneIndex0].MultiplyPoint3x4(shapePositions[i])*b.weight0+matrices[b.boneIndex1].MultiplyPoint3x4(shapePositions[i])*b.weight1+matrices[b.boneIndex2].MultiplyPoint3x4(shapePositions[i])*b.weight2+matrices[b.boneIndex3].MultiplyPoint3x4(shapePositions[i])*b.weight3;
    max=Mathf.Max(max,(predicted-expected[i]).magnitude);
   }
   float[] V(Vector3[] v)=>v.SelectMany(q=>new[]{q.x,q.y,q.z}).ToArray();
   float[] M(Matrix4x4[] array)=>array.SelectMany(q=>Enumerable.Range(0,16).Select(i=>q[i/4,i%4])).ToArray();
   var owner=r.GetComponentInParent<MatchHeroLook>();var toRoot=owner.transform.worldToLocalMatrix*r.transform.localToWorldMatrix;
   var part=new Part{name=r.name,vertices=V(p),normals=V(m.normals),posedVertices=V(expected),posedNormals=V(bake.normals),uv=m.uv.SelectMany(q=>new[]{q.x,q.y}).ToArray(),triangles=m.triangles,weights=w.SelectMany(q=>new[]{q.weight0,q.weight1,q.weight2,q.weight3}).ToArray(),indices=w.SelectMany(q=>new[]{q.boneIndex0,q.boneIndex1,q.boneIndex2,q.boneIndex3}).ToArray(),bones=r.bones.Select(b=>b.name).ToArray(),bindposes=M(m.bindposes),skinMatrices=M(matrices),rendererToRoot=M(new[]{toRoot}),bakeOracleMaxMetres=max};
   Debug.Log("[HeroGarmentPoseSnapshot] "+r.name+" exact LBS/bake oracle="+max+"m");Object.DestroyImmediate(bake);return part;
  }
 }
}
