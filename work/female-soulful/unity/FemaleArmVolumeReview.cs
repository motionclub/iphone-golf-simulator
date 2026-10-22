#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using GolfArcade.Tennis;
using GolfArcade.Game;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class FemaleArmVolumeReview {
  static object Call(string n,params object[] a)=>typeof(HeroTurnaround).GetMethod(n,BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,a);
  static void Shot(Camera c,string p) {
   var rt=RenderTexture.GetTemporary(800,1000,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,4);var prior=RenderTexture.active;
   c.targetTexture=rt;c.Render();RenderTexture.active=rt;var t=new Texture2D(800,1000,TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,800,1000),0,0);t.Apply();File.WriteAllBytes(p,t.EncodeToJPG(94));RenderTexture.active=prior;c.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(t);
  }
  static void Dump(SkinnedMeshRenderer s,string p) {
   using(var w=new BinaryWriter(File.Create(p+"_weights.f32")))foreach(var b in s.sharedMesh.boneWeights){w.Write((float)b.boneIndex0);w.Write((float)b.boneIndex1);w.Write((float)b.boneIndex2);w.Write((float)b.boneIndex3);w.Write(b.weight0);w.Write(b.weight1);w.Write(b.weight2);w.Write(b.weight3);}
   using(var w=new BinaryWriter(File.Create(p+"_skin.f32")))for(int j=0;j<s.bones.Length;j++){var matrix=s.bones[j].localToWorldMatrix*s.sharedMesh.bindposes[j];for(int r=0;r<4;r++)for(int c=0;c<4;c++)w.Write(matrix[r,c]);}
   var m=new Mesh();s.BakeMesh(m,true);using(var w=new BinaryWriter(File.Create(p+".f32")))foreach(var v in m.vertices){var q=s.transform.TransformPoint(v);w.Write(q.x);w.Write(q.y);w.Write(q.z);}Object.DestroyImmediate(m);
   File.WriteAllText(p+".json","{\"bones\":["+string.Join(",",s.bones.Take(53).Select(b=>"{\"name\":\""+b.name+"\",\"position\":["+b.position.x+","+b.position.y+","+b.position.z+"],\"scale\":["+b.lossyScale.x+","+b.lossyScale.y+","+b.lossyScale.z+"]}"))+ "]}");
  }
  public static void Run() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("ARM_REVIEW_OUT");Directory.CreateDirectory(output);
   foreach(bool golf in new[]{true,false}) {
    Call("Studio",golf);object[] args={golf?"GolfKitHero_Female":"MatchHero_Female",null,null};var root=(GameObject)typeof(HeroTurnaround).GetMethod("BuildHero",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,args);var look=root.GetComponent<MatchHeroLook>();
    var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");c.fieldOfView=28;c.aspect=.8f;
    var clips=golf?Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(true)).Where(x=>!x.name.StartsWith("__preview__")).ToArray():root.GetComponent<HeroTennisDriver>().slots.Select(x=>x.clip).Distinct().ToArray();
    var names=golf?new[]{"Cheer","Drive"}:new[]{"Female_Emote_JumpJoy","Female_Intro_Wave"};
    if(Environment.GetEnvironmentVariable("ARM_REVIEW_BODY_ONLY")=="1") {
     foreach(var r in look.kit)if(r)r.enabled=false;
     var source=(Mesh)typeof(MatchHeroLook).GetField("kitV2CoverSource",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(look);
     var full=Object.Instantiate(look.body.sharedMesh);full.triangles=source.triangles;look.body.sharedMesh=full;
    }
    foreach(var mode in new[]{"before"}) {
     if(mode!="before")HeroArmSkinning.Build(look.body);
     foreach(var name in names) {
      var clip=clips.FirstOrDefault(x=>x.name==name);if(!clip)throw new Exception("Missing "+name+"; "+string.Join(",",clips.Select(x=>x.name)));
      float t=name.Contains("Cheer")?.25f:.5f;clip.SampleAnimation(root,t*clip.length);Call("Correctives",root);
      if(mode=="volume-no-shoulder")for(int i=0;i<look.body.sharedMesh.blendShapeCount;i++)if(look.body.sharedMesh.GetBlendShapeName(i).StartsWith("FemaleShoulderFit_"))look.body.SetBlendShapeWeight(i,0);
      string stem=Path.Combine(output,(golf?"golf":"tennis")+"_"+name+"_"+mode);Dump(look.body,stem);
      var pivot=new GameObject("Motion bake").transform;object[] ba={root,pivot,null};var parts=(IEnumerable)typeof(HeroTurnaround).GetMethod("Bake",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,ba);
      var target=new Vector3(0,1.38f,0);c.transform.position=target+Quaternion.Euler(0,30,0)*Vector3.forward*1.65f;c.transform.LookAt(target);Shot(c,stem+".jpg");
      foreach(var p in parts){var go=(GameObject)p.GetType().GetField("go").GetValue(p);Object.DestroyImmediate(go);}foreach(var r in (List<Renderer>)ba[2])if(r)r.enabled=true;Object.DestroyImmediate(pivot.gameObject);
     }
    }
    Object.DestroyImmediate(root);Call("Release");
   }
  }
 }
}
#endif
