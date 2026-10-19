#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using GolfArcade.Tennis;
using GolfArcade.Game;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class FemaleTopMotionReview {
  static object Call(string n,params object[] a)=>typeof(HeroTurnaround).GetMethod(n,BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,a);
  static void Shot(Camera c,string p) {
   var rt=RenderTexture.GetTemporary(640,800,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,4);var prior=RenderTexture.active;
   c.targetTexture=rt;c.Render();RenderTexture.active=rt;var t=new Texture2D(640,800,TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,640,800),0,0);t.Apply();File.WriteAllBytes(p,t.EncodeToJPG(94));RenderTexture.active=prior;c.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(t);
  }
  public static void Run() {
   bool golf=Environment.GetEnvironmentVariable("TOP_REVIEW_SPORT")!="tennis";
   string output=Environment.GetEnvironmentVariable("TOP_REVIEW_OUT");Directory.CreateDirectory(output);
   Call("Studio",golf);object[] args={golf?"GolfKitHero_Female":"MatchHero_Female",null,null};
   var root=(GameObject)typeof(HeroTurnaround).GetMethod("BuildHero",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,args);var look=root.GetComponent<MatchHeroLook>();
   var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");c.fieldOfView=28;c.aspect=.8f;
   var clips=golf?Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(true)).Where(x=>!x.name.StartsWith("__preview__")).ToArray():root.GetComponent<HeroTennisDriver>().slots.Select(x=>x.clip).Distinct().ToArray();
   string names=Environment.GetEnvironmentVariable("TOP_REVIEW_CLIPS")??(golf?"Idle,Drive,IronSwing,Cheer,Wave":"Ready,EmoteJumpJoy,IntroWave");
   foreach(var name in names.Split(',')) {
    var clip=clips.FirstOrDefault(x=>x.name==name);if(!clip)throw new Exception("Missing "+name+"; "+string.Join(",",clips.Select(x=>x.name)));
    foreach(float t in new[]{0f,.25f,.5f,.75f}) {
     clip.SampleAnimation(root,t*clip.length);Call("Correctives",root);
     var corr=root.GetComponent<KitV2PoseCorrectives>();
     var flags=BindingFlags.Instance|BindingFlags.NonPublic;
     var features=(float[])typeof(KitV2PoseCorrectives).GetField("features",flags).GetValue(corr);
     var weights=(float[])typeof(KitV2PoseCorrectives).GetField("weights",flags).GetValue(corr);
     File.WriteAllText(Path.Combine(output,$"{name}_{t:F2}_features.json"),"{\"features\":["+string.Join(",",features.Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)))+"],\"weights\":["+string.Join(",",weights.Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)))+"]}");

     if(Environment.GetEnvironmentVariable("TOP_REVIEW_HIDE_BODY")=="1")look.body.enabled=false;
     var pivot=new GameObject("Motion bake").transform;object[] ba={root,pivot,null};var parts=(IEnumerable)typeof(HeroTurnaround).GetMethod("Bake",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,ba);
     var target=new Vector3(0,1.19f,0);
     foreach(int yaw in new[]{30,150}) {
      var dir=Quaternion.Euler(0,yaw,0)*Vector3.forward;c.transform.position=target+dir*2.0f;c.transform.LookAt(target);Shot(c,Path.Combine(output,$"{name}_{t:F2}_{yaw}.jpg"));
     }
     foreach(var p in parts){var go=(GameObject)p.GetType().GetField("go").GetValue(p);Object.DestroyImmediate(go);}
     foreach(var r in (System.Collections.Generic.List<Renderer>)ba[2])if(r)r.enabled=true;
     Object.DestroyImmediate(pivot.gameObject);
    }
   }
   Object.DestroyImmediate(root);Call("Release");
  }
 }
}
#endif
