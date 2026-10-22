using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
namespace GolfArcade.Tennis {
 // Isolated candidate: fixed garment morphs driven by shoulder rotation, including twist.
 // No skeleton, body, motion or vertex-buffer changes during playback.
 [DefaultExecutionOrder(1210), DisallowMultipleComponent]
 public sealed class TailoredPoloDeformation : MonoBehaviour {
  [Serializable] public sealed class Anchor { public string shape,sample; public float[] feature,deltas,normalDeltas; }
  [Serializable] public sealed class Profile { public int vertexCount;public float[] vertices,normals;public string[] featureBones;public float featurePositionScale;public Anchor[] anchors; }
  const string Prefix="PoloTwist_";
  static Profile loaded;
  public MatchHeroLook look;
  readonly List<Mesh> owned=new();
  Profile profile;SkinnedMeshRenderer top;Mesh previous;
  int chest;int[] boneIds,shapeIds;Matrix4x4[] binds;float[] feature,lastWeights;
  readonly int[] nearest=new int[4];readonly double[] distances=new double[4];
  static Profile Load(){
#if UNITY_EDITOR
   if(loaded!=null)return loaded;
   string path=Environment.GetEnvironmentVariable("VISUAL_TAILORED_MOTION_PROFILE");
   if(string.IsNullOrEmpty(path))return null;
   loaded=JsonUtility.FromJson<Profile>(File.ReadAllText(path));
   if(loaded?.featureBones==null||loaded.anchors==null||loaded.vertexCount<=0)throw new InvalidOperationException("Invalid polo motion profile");
   return loaded;
#else
   return null;
#endif
  }
  public static Mesh Prepare(MatchHeroLook hero,SkinnedMeshRenderer r,Mesh src){
   if(!hero||hero.female||hero.golfKit||!r||r.name!="Kit_Top"||!src||src.name.Contains("(polo twist)"))return src;
   var p=Load();if(p==null)return src;
   if(src.vertexCount!=p.vertexCount)throw new InvalidOperationException("Polo motion profile requires its exact full-detail basis");
   var v=src.vertices;var n=src.normals;
   if(p.vertices.Length!=v.Length*3||p.normals.Length!=v.Length*3)throw new InvalidOperationException("Polo motion basis array length");
   for(int i=0;i<v.Length;i++)if((v[i]-V(p.vertices,i)).sqrMagnitude>1e-10f)throw new InvalidOperationException("Polo motion basis position mismatch");
   var result=Instantiate(src);result.name=src.name+" (polo twist)";result.hideFlags=HideFlags.DontSave;
   foreach(var a in p.anchors){
    if(a.feature.Length!=p.featureBones.Length*9||a.deltas.Length!=v.Length*3||a.normalDeltas.Length!=v.Length*3)throw new InvalidOperationException("Polo motion anchor array length");
    var dv=new Vector3[v.Length];var dn=new Vector3[v.Length];
    for(int i=0;i<v.Length;i++){dv[i]=V(a.deltas,i);dn[i]=V(a.normalDeltas,i);if(!float.IsFinite(dv[i].sqrMagnitude)||!float.IsFinite(dn[i].sqrMagnitude))throw new InvalidOperationException("Nonfinite polo motion anchor");}
    result.AddBlendShapeFrame(Prefix+a.shape,100,dv,dn,null);
   }
   var component=hero.GetComponent<TailoredPoloDeformation>();if(!component)component=hero.gameObject.AddComponent<TailoredPoloDeformation>();component.look=hero;component.owned.Add(result);
   Debug.Log($"[TailoredPoloDeformation] fixed basis v={v.Length}, anchors={p.anchors.Length}; body/rig/source motion unchanged");return result;
  }
  static Vector3 V(float[] a,int i)=>new(a[i*3],a[i*3+1],a[i*3+2]);
  void OnDestroy(){foreach(var mesh in owned)if(mesh)Destroy(mesh);}
  bool Init(){
   if(!look)look=GetComponent<MatchHeroLook>();if(!look)return false;
   profile??=Load();if(profile==null)return false;
   top??=look.kit.FirstOrDefault(r=>r&&r.name=="Kit_Top");if(!top||!top.sharedMesh)return false;
   if(previous!=top.sharedMesh){
    previous=top.sharedMesh;binds=previous.bindposes;chest=Array.FindIndex(top.bones,b=>b&&b.name=="Chest");boneIds=profile.featureBones.Select(name=>Array.FindIndex(top.bones,b=>b&&b.name==name)).ToArray();shapeIds=profile.anchors.Select(a=>previous.GetBlendShapeIndex(Prefix+a.shape)).ToArray();
    if(chest<0||boneIds.Any(i=>i<0)||shapeIds.Any(i=>i<0))throw new InvalidOperationException("Polo motion palette/shape mismatch");
    feature=new float[profile.featureBones.Length*9];lastWeights=new float[shapeIds.Length];
   }
   return true;
  }
  public void Apply(){
   if(!Init())return;
   var toMesh=top.transform.worldToLocalMatrix;var inverseChest=(toMesh*top.bones[chest].localToWorldMatrix*binds[chest]).inverse;int at=0;
   foreach(int bone in boneIds){var m=inverseChest*toMesh*top.bones[bone].localToWorldMatrix*binds[bone];for(int col=0;col<2;col++)for(int row=0;row<3;row++)feature[at++]=m[row,col];for(int row=0;row<3;row++)feature[at++]=m[row,3]*profile.featurePositionScale;}
   for(int j=0;j<4;j++){nearest[j]=-1;distances[j]=double.MaxValue;}
   for(int a=0;a<profile.anchors.Length;a++){
    double d=0;var sample=profile.anchors[a].feature;for(int j=0;j<feature.Length;j++){double e=feature[j]-sample[j];d+=e*e;}d/=feature.Length;
    for(int j=0;j<4;j++)if(d<distances[j]){for(int k=3;k>j;k--){distances[k]=distances[k-1];nearest[k]=nearest[k-1];}distances[j]=d;nearest[j]=a;break;}
   }
   double total=0;bool exact=distances[0]<1e-10;for(int j=0;j<4;j++){distances[j]=nearest[j]<0?0:exact?(j==0?1:0):1/Math.Pow(Math.Max(1e-8,distances[j]),2);total+=distances[j];}
   for(int a=0;a<shapeIds.Length;a++){
    float value=0;for(int j=0;j<4;j++)if(nearest[j]==a)value=(float)(100*distances[j]/total);
    if(Mathf.Abs(value-lastWeights[a])>1e-5f){top.SetBlendShapeWeight(shapeIds[a],value);lastWeights[a]=value;}
   }
  }
  void LateUpdate(){var driver=GetComponent<HeroTennisDriver>();if(driver&&driver.isActiveAndEnabled&&driver.actor&&!(driver.game&&driver.game.ReplayPlaying))return;Apply();}
 }
}
