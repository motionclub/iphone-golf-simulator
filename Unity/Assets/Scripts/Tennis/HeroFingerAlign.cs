using System;
using System.Collections.Generic;
using UnityEngine;
namespace GolfArcade.Tennis
{
 /// FEMALE HANDS (2026-11-08, user: "her arms are inverted, she looks like a monster, mainly when she isn't holding anything; copy the
 /// male anatomy since it works, and fingers"). Every hand pose is built from bone lines (the relaxed stand, fists, the run, grips), and
 /// the male's finger skin lies within ~5 deg of his finger bones. Hers did not: HeroHandShape's fuller fingers fanned them 26-38 deg off
 /// their bones (index to the thumb side, ring and little the other way; measured with PhoneMenuCapture's TipDiag,
 /// work/app-review-1107/proof/arms), so the same pose splayed and hooked them into a claw, and the thumb stuck out. That pass is no longer
 /// run, and this straightens what is left (up to 17 deg, the racket grip bound into her skin): each finger segment's skin is turned about
 /// the segment's joint by the angle between the middle of its skin and its bone line (a vertex shared by two bones takes each one's turn
 /// by its weight), so her skin sits on her bones as his does and every pose gives her his hand. Bones, bind poses, weights, topology and
 /// everything outside the fingers are untouched.
 public static class HeroFingerAlign {
  static readonly Dictionary<Mesh,Mesh> cache=new();
  static readonly string[] Fingers={"Thumb","Index","Middle","Ring","Little"},Joints={"Proximal","Intermediate","Distal"};
  /// No segment turns by more than this (a stray weight must never fold a finger back).
  const float MaxTurn=60f;
  public static Mesh Prepare(SkinnedMeshRenderer body,bool female) {
   var source=body?body.sharedMesh:null;
   if(!female||!source||!source.isReadable||source.name.Contains("(finger align)"))return source;
#if UNITY_EDITOR
   if(Environment.GetEnvironmentVariable("FEMALE_FINGER_ALIGN")=="0")return source;
#endif
   if(cache.TryGetValue(source,out var done)&&done)return done;
   var palette=body.bones;var bind=source.bindposes;var weights=source.boneWeights;var vertices=source.vertices;var normals=source.normals;
   if(weights.Length!=vertices.Length||bind.Length!=palette.Length)return source;
   // each finger bone's turn: about its head, from the middle of the skin it carries to its bone line
   var turn=new Dictionary<int,(Vector3 head,Quaternion q)>();float largest=0;
   foreach(string side in new[]{"Left","Right"})
    foreach(string finger in Fingers) {
     var ids=new int[3];bool all=true;
     for(int j=0;j<3;j++){string name=side+finger+Joints[j];ids[j]=Array.FindIndex(palette,b=>b&&b.name==name);all&=ids[j]>=0;}
     if(!all)continue;
     Vector3 Head(int id)=>bind[id].inverse.GetColumn(3);
     for(int j=0;j<3;j++) {
      int id=ids[j];var head=Head(id);
      // the bone line: to the next joint, and on through the last one for the fingertip (it has no child)
      var line=j<2?Head(ids[j+1])-head:head-Head(ids[1]);
      Vector3 sum=Vector3.zero;int n=0;
      for(int v=0;v<vertices.Length;v++)if(Weight(weights[v],id)>=.5f){sum+=vertices[v];n++;}
      if(n<6||line.sqrMagnitude<1e-10f)continue;
      var skin=sum/n-head;if(skin.sqrMagnitude<1e-10f)continue;
      var q=Quaternion.FromToRotation(skin.normalized,line.normalized);
      float angle=Quaternion.Angle(Quaternion.identity,q);if(angle>MaxTurn)q=Quaternion.Slerp(Quaternion.identity,q,MaxTurn/angle);
      turn[id]=(head,q);largest=Mathf.Max(largest,Mathf.Min(angle,MaxTurn));
     }
    }
   if(turn.Count==0)return source;
   int moved=0;float maxMove=0;bool hasNormals=normals!=null&&normals.Length==vertices.Length;
   for(int v=0;v<vertices.Length;v++) {
    var w=weights[v];int[] idx={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] amt={w.weight0,w.weight1,w.weight2,w.weight3};
    bool touched=false;for(int k=0;k<4;k++)if(amt[k]>0&&turn.ContainsKey(idx[k]))touched=true;
    if(!touched)continue;
    Vector3 p=Vector3.zero,nrm=Vector3.zero;float total=0;
    for(int k=0;k<4;k++) {
     if(amt[k]<=0)continue;total+=amt[k];
     if(turn.TryGetValue(idx[k],out var t)){p+=amt[k]*(t.head+t.q*(vertices[v]-t.head));if(hasNormals)nrm+=amt[k]*(t.q*normals[v]);}
     else{p+=amt[k]*vertices[v];if(hasNormals)nrm+=amt[k]*normals[v];}
    }
    if(total<=0)continue;p/=total;
    float d=(p-vertices[v]).magnitude;if(d>1e-6f)moved++;maxMove=Mathf.Max(maxMove,d);
    vertices[v]=p;if(hasNormals&&nrm.sqrMagnitude>1e-10f)normals[v]=nrm.normalized;
   }
   var mesh=UnityEngine.Object.Instantiate(source);mesh.name=source.name+" (finger align)";mesh.hideFlags=HideFlags.DontSave;
   mesh.vertices=vertices;if(hasNormals)mesh.normals=normals;mesh.RecalculateBounds();
   cache[source]=mesh;
   Debug.Log("[HeroFingerAlign] Female fingers on their bones: segments="+turn.Count+" largestTurn="+largest.ToString("F0")+" deg vertices="+moved+" maxMove="+(maxMove*1000f).ToString("F1")+" mm; bones, binds, weights and topology retained");
   return mesh;
  }
  static float Weight(BoneWeight w,int id)=>(w.boneIndex0==id?w.weight0:0)+(w.boneIndex1==id?w.weight1:0)+(w.boneIndex2==id?w.weight2:0)+(w.boneIndex3==id?w.weight3:0);
 }
}
