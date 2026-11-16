using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
namespace GolfArcade.Tennis {
 /// Versioned authored hand anatomy. Original approved clips are rebased from their
 /// old rest, preserving their old skinning deltas. Named hierarchy stays53/54.
 /// Manual samplers MUST BeforeSample -> old clip sample -> AfterSample.
 [DefaultExecutionOrder(1110),DisallowMultipleComponent]
 public sealed class HeroThumbRigMigration:MonoBehaviour {
  public const string Version="match-hero-hand-anatomy-v3";
  public MatchHeroLook look;
  sealed class Joint { public Transform bone;public Matrix4x4 oldRest,newRest;public Vector3 rawPosition,rawScale;public Quaternion rawRotation; }
  readonly List<Joint> joints=new();bool prepared,applied;
  public static HeroThumbRigMigration Prepare(MatchHeroLook hero) {
   if(!hero)return null;var migration=hero.GetComponent<HeroThumbRigMigration>();if(!migration)migration=hero.gameObject.AddComponent<HeroThumbRigMigration>();migration.look=hero;migration.Init();return migration;
  }
  void Init() {
   if(prepared||!look||!look.body)return;
   var body=look.body;var palette=body.bones;var binds=body.sharedMesh.bindposes;
   var old=new Dictionary<Transform,Matrix4x4>();var toRoot=transform.worldToLocalMatrix*body.transform.localToWorldMatrix;
   for(int b=0;b<palette.Length;b++)old[palette[b]]=toRoot*binds[b].inverse;
   var reference=Resources.Load<GameObject>("Tennis/Premium/HandRest/"+(look.female?"Female":"Male"));
   if(!reference)throw new InvalidOperationException("Authored hand-v3 rest missing");
   var source=reference.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name.StartsWith("Body"));
   var sourceToRoot=reference.transform.worldToLocalMatrix*source.transform.localToWorldMatrix;
   var authored=source.bones.Select((b,i)=>new{b.name,rest=sourceToRoot*source.sharedMesh.bindposes[i].inverse}).ToDictionary(x=>x.name,x=>x.rest);
   foreach(var entry in old){
    string name=entry.Key.name;
    bool digit=new[]{"Thumb","Index","Middle","Ring","Little"}.Any(d=>name.StartsWith("Left"+d)||name.StartsWith("Right"+d));
    if(!digit)continue;
    if(!authored.TryGetValue(name,out var wanted))throw new InvalidOperationException("Hand-v3 rest bone missing "+name);
    joints.Add(new Joint{bone=entry.Key,oldRest=entry.Value,newRest=wanted,rawPosition=entry.Key.localPosition,rawRotation=entry.Key.localRotation,rawScale=entry.Key.localScale});
   }
   // Parent-first order is required when converted world tracks become local TRS.
   joints.Sort((a,b)=>Depth(a.bone).CompareTo(Depth(b.bone)));
   // Every skin uses the same new inverse binds; distance swaps are prepared
   // through the same helper, so a palette cannot silently return to old rest.
   foreach(var renderer in new[]{look.body}.Concat(look.kit??Array.Empty<SkinnedMeshRenderer>()).Where(r=>r).Distinct())PrepareRenderer(renderer);
   var restore=gameObject.GetComponent<HeroThumbSourceRestore>();if(!restore)restore=gameObject.AddComponent<HeroThumbSourceRestore>();restore.migration=this;
   prepared=true;Debug.Log("[HeroThumbRigMigration] prepared "+Version+" "+(look.female?"Female":"Male")+"; names/hierarchy exact; old clips require consistent rebase");
  }
  static int Depth(Transform bone){int d=0;for(var p=bone.parent;p;p=p.parent)d++;return d;}
  readonly Dictionary<(Mesh source,int renderer),Mesh> boundMeshes=new();
  public void PrepareRenderer(SkinnedMeshRenderer renderer){
   if(!renderer||!renderer.sharedMesh)return;var source=renderer.sharedMesh;var key=(source,renderer.GetInstanceID());
   if(boundMeshes.TryGetValue(key,out var found)&&found){renderer.sharedMesh=found;return;}
   var updated=(Matrix4x4[])source.bindposes.Clone();bool changed=false;
   var sourceToRoot=transform.worldToLocalMatrix*renderer.transform.localToWorldMatrix;
   for(int b=0;b<renderer.bones.Length;b++){
    var joint=joints.FirstOrDefault(j=>j.bone==renderer.bones[b]);if(joint==null)continue;
    var wanted=joint.newRest.inverse*sourceToRoot;float error=0;for(int k=0;k<16;k++)error=Mathf.Max(error,Mathf.Abs(updated[b][k]-wanted[k]));
    if(error<.0000001f)continue;updated[b]=wanted;changed=true;
   }
   if(!changed){boundMeshes[key]=source;return;}
   var mesh=UnityEngine.Object.Instantiate(source);mesh.name=source.name+" (hand v3 bind)";mesh.hideFlags=HideFlags.DontSave;mesh.bindposes=updated;renderer.sharedMesh=mesh;boundMeshes[key]=mesh;boundMeshes[(mesh,renderer.GetInstanceID())]=mesh;
  }
  public void RestoreRaw() {
   if(!prepared)return;
   foreach(var j in joints){j.bone.localPosition=j.rawPosition;j.bone.localRotation=j.rawRotation;j.bone.localScale=j.rawScale;}
   applied=false;
  }
  public void Rebase() {
   Init();if(!prepared||applied)return;
   var rootInverse=transform.worldToLocalMatrix;var poses=joints.Select(j=>rootInverse*j.bone.localToWorldMatrix*j.oldRest.inverse*j.newRest).ToArray();
   for(int i=0;i<joints.Count;i++){var j=joints[i];j.rawPosition=j.bone.localPosition;j.rawRotation=j.bone.localRotation;j.rawScale=j.bone.localScale;}
   for(int i=0;i<joints.Count;i++) {
    var bone=joints[i].bone;var parent=transform.worldToLocalMatrix*bone.parent.localToWorldMatrix;var local=parent.inverse*poses[i];
    Decompose(local,out var position,out var rotation,out var scale);bone.localPosition=position;bone.localRotation=rotation;bone.localScale=scale;
   }
   applied=true;
  }
  static void Decompose(Matrix4x4 matrix,out Vector3 p,out Quaternion q,out Vector3 s) {
   p=matrix.GetColumn(3);Vector3 x=matrix.GetColumn(0),y=matrix.GetColumn(1),z=matrix.GetColumn(2);s=new Vector3(x.magnitude,y.magnitude,z.magnitude);if(Vector3.Dot(Vector3.Cross(x,y),z)<0)s.x=-s.x;q=Quaternion.LookRotation(z/s.z,y/s.y);
  }
  void LateUpdate(){Rebase();}
  public bool Applied=>applied;
 }
 [DefaultExecutionOrder(-1000),DisallowMultipleComponent] public sealed class HeroThumbSourceRestore:MonoBehaviour {public HeroThumbRigMigration migration;void Update(){if(migration)migration.RestoreRaw();}}
}
