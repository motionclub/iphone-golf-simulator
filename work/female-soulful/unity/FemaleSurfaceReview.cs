#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using UnityEditor;
using GolfArcade.Tennis;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class FemaleSurfaceReview {
  static object Call(string n,params object[] a)=>typeof(HeroTurnaround).GetMethod(n,BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,a);
  static void Shot(Camera c,string p) {
   var rt=RenderTexture.GetTemporary(960,1200,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,4);var prior=RenderTexture.active;c.targetTexture=rt;c.Render();RenderTexture.active=rt;var t=new Texture2D(960,1200,TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,960,1200),0,0);t.Apply();File.WriteAllBytes(p,t.EncodeToJPG(95));RenderTexture.active=prior;c.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(t);
  }
  public static void Run() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("SURFACE_REVIEW_OUT");Directory.CreateDirectory(output);
   foreach(bool golf in new[]{false,true}) {
    Call("Studio",golf);object[] args={golf?"GolfKitHero_Female":"MatchHero_Female",null,null};var root=(GameObject)typeof(HeroTurnaround).GetMethod("BuildHero",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,args);var look=root.GetComponent<MatchHeroLook>();
    Call("RestPose",root);
    foreach(var pair in new[]{(HumanBodyBones.LeftUpperArm,HumanBodyBones.LeftLowerArm),(HumanBodyBones.RightUpperArm,HumanBodyBones.RightLowerArm)}){var upper=look.Bone(pair.Item1);var lower=look.Bone(pair.Item2);float sign=Mathf.Sign(upper.position.x);var direction=Vector3.down*Mathf.Cos(25*Mathf.Deg2Rad)+Vector3.right*sign*Mathf.Sin(25*Mathf.Deg2Rad);upper.rotation=Quaternion.FromToRotation(lower.position-upper.position,direction)*upper.rotation;}
    Call("Correctives",root);
    var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");c.fieldOfView=28;c.aspect=.8f;
    foreach(var swatch in new[]{"default","light","dark"}) {
     look.SetKit(swatch=="light"?"EDEBE5":swatch=="dark"?"18233B":golf?"E87B65":"C0D52F",golf?"23304B":"EAE7DE","FFFFFF");Call("Correctives",root);
     var pivot=new GameObject("Surface bake").transform;object[] ba={root,pivot,null};var parts=(IEnumerable)typeof(HeroTurnaround).GetMethod("Bake",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,ba);
     foreach(var view in new[]{"close","full"}) {var target=new Vector3(0,view=="close"?1.39f:.90f,0);c.transform.position=target+Quaternion.Euler(0,30,0)*Vector3.forward*(view=="close"?1.55f:3.35f);c.transform.LookAt(target);Shot(c,Path.Combine(output,(golf?"golf":"tennis")+"_"+swatch+"_"+view+".jpg"));}
     foreach(var p in parts)Object.DestroyImmediate((GameObject)p.GetType().GetField("go").GetValue(p));foreach(var rr in (List<Renderer>)ba[2])if(rr)rr.enabled=true;Object.DestroyImmediate(pivot.gameObject);
    }
    Object.DestroyImmediate(root);Call("Release");
   }
  }
 }
}
#endif
