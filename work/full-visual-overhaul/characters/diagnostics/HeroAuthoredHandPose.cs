using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
namespace GolfArcade.Tennis {
 /// Authored pose is represented by pose*inverse-rest skin matrices. Bone-axis
 /// pre/post rotations cancel, so a mesh and an armature-only FBX cannot diverge.
 public static class HeroAuthoredHandPose {
  [Serializable] sealed class BoneSource {public string name;public float[] restHead,delta;}
  [Serializable] sealed class PoseSource {public string version;public BoneSource[] bones;}
  sealed class Contract {public Matrix4x4 axis;public Dictionary<string,Matrix4x4> handPoses=new();public Dictionary<string,Matrix4x4> handBind=new();}
  static readonly Dictionary<bool,Contract> poses=new();
  static Matrix4x4 Matrix(float[] a){var m=new Matrix4x4();for(int i=0;i<16;i++)m[i]=a[i];return m;}
  static Vector3 Point(float[] a)=>new(a[0],a[1],a[2]);
  static Contract Load(bool female){
   if(poses.TryGetValue(female,out var cached))return cached;
   string sex=female?"Female":"Male";
   var text=Resources.Load<TextAsset>("Tennis/Premium/HandPose/"+sex);
   if(!text)throw new InvalidOperationException("Hand-v3 skin-delta contract missing "+sex);
   var data=JsonUtility.FromJson<PoseSource>(text.text);
   if(data.version!=HeroThumbRigMigration.Version)throw new InvalidOperationException("Hand-v3 pose/rest version mismatch "+data.version);
   var prefab=Resources.Load<GameObject>("Tennis/Premium/HandRest/"+sex);
   var skin=prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name.StartsWith("Body"));
   var bind=skin.bones.Select((b,i)=>new{b.name,rest=skin.sharedMesh.bindposes[i].inverse}).ToDictionary(b=>b.name,b=>b.rest);
   var source=data.bones.Where(b=>bind.ContainsKey(b.name)).ToArray();
   var origin=source.First(b=>b.name=="Hips");float best=float.PositiveInfinity;Matrix4x4 axis=Matrix4x4.identity;
   int[][] permutations={new[]{0,1,2},new[]{0,2,1},new[]{1,0,2},new[]{1,2,0},new[]{2,0,1},new[]{2,1,0}};
   foreach(var permutation in permutations)for(int signs=0;signs<8;signs++){
    var candidate=Matrix4x4.zero;candidate[3,3]=1;
    for(int row=0;row<3;row++)candidate[row,permutation[row]]=(signs&(1<<row))==0?1:-1;
    candidate.SetColumn(3,(Vector4)((Vector3)bind[origin.name].GetColumn(3)-candidate.MultiplyPoint3x4(Point(origin.restHead))));candidate[3,3]=1;
    float error=source.Sum(b=>(candidate.MultiplyPoint3x4(Point(b.restHead))-(Vector3)bind[b.name].GetColumn(3)).sqrMagnitude);
    if(error<best){best=error;axis=candidate;}
   }
   float worst=source.Max(b=>Vector3.Distance(axis.MultiplyPoint3x4(Point(b.restHead)),bind[b.name].GetColumn(3)));
   if(worst>.0001f)throw new InvalidOperationException("Hand-v3 source/imported body basis does not match53boneheads: "+worst);
   var result=new Contract{axis=axis};var inverse=axis.inverse;
   foreach(string side in new[]{"Left","Right"}){
    var handInverse=bind[side+"Hand"].inverse;result.handBind[side]=handInverse;
    foreach(var bone in source.Where(b=>new[]{"Thumb","Index","Middle","Ring","Little"}.Any(d=>b.name.StartsWith(side+d))))result.handPoses[bone.name]=handInverse*axis*Matrix(bone.delta)*inverse*bind[bone.name];
   }
   if(result.handPoses.Count!=30)throw new InvalidOperationException("Hand-v3 skin-delta contract expected30digits");
   poses[female]=result;Debug.Log("[HeroAuthoredHandPose] "+sex+"53bonehead body-axis maxerror="+worst+" axis="+axis+";30skin-delta poses loaded");return result;
  }
  static void Decompose(Matrix4x4 m,out Vector3 p,out Quaternion q,out Vector3 s){p=m.GetColumn(3);Vector3 x=m.GetColumn(0),y=m.GetColumn(1),z=m.GetColumn(2);s=new Vector3(x.magnitude,y.magnitude,z.magnitude);if(Vector3.Dot(Vector3.Cross(x,y),z)<0)s.x=-s.x;q=Quaternion.LookRotation(z/s.z,y/s.y);}
  public static bool ApplyFist(MatchHeroLook hero,bool left,float strength){
   if(!hero||!hero.body||!hero.body.sharedMesh.name.Contains("(hand v3 bind)"))return false;
   var target=Load(hero.female);float weight=Mathf.Clamp01(strength);string side=left?"Left":"Right";
   var hand=hero.Bone(left?HumanBodyBones.LeftHand:HumanBodyBones.RightHand);var handWorld=hand.localToWorldMatrix;
   foreach(string digit in new[]{"Thumb","Index","Middle","Ring","Little"})foreach(string joint in new[]{"Proximal","Intermediate","Distal"}){
    string name=side+digit+joint;var b=hero.Bone((HumanBodyBones)Enum.Parse(typeof(HumanBodyBones),name));if(!b||!target.handPoses.TryGetValue(name,out var pose))throw new InvalidOperationException("Authored fist missing bone "+name);
    Decompose(b.parent.worldToLocalMatrix*handWorld*pose,out var p,out var q,out var s);
    b.localPosition=Vector3.Lerp(b.localPosition,p,weight);b.localRotation=Quaternion.Slerp(b.localRotation,q,weight);b.localScale=Vector3.Lerp(b.localScale,s,weight);
   }
   int shape=Enumerable.Range(0,hero.body.sharedMesh.blendShapeCount).Where(i=>hero.body.sharedMesh.GetBlendShapeName(i).EndsWith("Hero_Fist_"+side)).DefaultIfEmpty(-1).First();
   if(shape>=0)hero.body.SetBlendShapeWeight(shape,weight*100f);
   return true;
  }
  public static Vector3 SourceToImportedBody(bool female,Vector3 source)=>Load(female).axis.MultiplyPoint3x4(source);
  public static Vector3 ExpectedSourcePoint(MatchHeroLook hero,bool left,Vector3 source){var c=Load(hero.female);string side=left?"Left":"Right";var hand=hero.Bone(left?HumanBodyBones.LeftHand:HumanBodyBones.RightHand);return hand.TransformPoint(c.handBind[side].MultiplyPoint3x4(c.axis.MultiplyPoint3x4(source)));}
 }
}
