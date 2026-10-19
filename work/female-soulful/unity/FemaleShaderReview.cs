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
 /// Female material review (2026-10-16 shader pass). Same studio, pose, camera
 /// and lights as FemaleSurfaceReview, but the hero wears a real locker skin pick
 /// (the game never shows the imported FBX default). Small JPGs only.
 /// SHADER_REVIEW_OUT = folder; SHADER_REVIEW_SET = "core" (default) or "tones".
 public static class FemaleShaderReview {
  static object Call(string n,params object[] a)=>typeof(HeroTurnaround).GetMethod(n,BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,a);
  static void Shot(Camera c,string p,int w,int h) {
   var rt=RenderTexture.GetTemporary(w,h,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,4);var prior=RenderTexture.active;c.targetTexture=rt;c.aspect=(float)w/h;c.Render();RenderTexture.active=rt;var t=new Texture2D(w,h,TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,w,h),0,0);t.Apply();File.WriteAllBytes(p,t.EncodeToJPG(90));RenderTexture.active=prior;c.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(t);
  }
  static readonly string[] SkinHex={"F3C9A6","EEBB8F","E2A06E","C47A4C","965835","603924"};
  public static void Run() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("SHADER_REVIEW_OUT");Directory.CreateDirectory(output);
   bool tones=Environment.GetEnvironmentVariable("SHADER_REVIEW_SET")=="tones";
   var log=new System.Text.StringBuilder();
   foreach(bool golf in new[]{false,true}) {
    Call("Studio",golf);object[] args={golf?"GolfKitHero_Female":"MatchHero_Female",null,null};var root=(GameObject)typeof(HeroTurnaround).GetMethod("BuildHero",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,args);var look=root.GetComponent<MatchHeroLook>();
    Call("RestPose",root);
    foreach(var pair in new[]{(HumanBodyBones.LeftUpperArm,HumanBodyBones.LeftLowerArm),(HumanBodyBones.RightUpperArm,HumanBodyBones.RightLowerArm)}){var upper=look.Bone(pair.Item1);var lower=look.Bone(pair.Item2);float sign=Mathf.Sign(upper.position.x);var direction=Vector3.down*Mathf.Cos(25*Mathf.Deg2Rad)+Vector3.right*sign*Mathf.Sin(25*Mathf.Deg2Rad);upper.rotation=Quaternion.FromToRotation(lower.position-upper.position,direction)*upper.rotation;}
    Call("Correctives",root);
    var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");
    var head=look.Bone(HumanBodyBones.Head);
    var runs=tones ? new[]{("fair",SkinHex[0],"default"),("tan",SkinHex[2],"default"),("deep",SkinHex[5],"default")}
                   : new[]{("cream",SkinHex[1],"default"),("cream",SkinHex[1],"light"),("cream",SkinHex[1],"dark")};
    foreach(var (skinName,skinHex,swatch) in runs) {
     look.SetKit(swatch=="light"?"EDEBE5":swatch=="dark"?"18233B":golf?"E87B65":"C0D52F",golf?"23304B":"EAE7DE","FFFFFF");
     look.SetSkin(HeroKit.Hex(skinHex));
     var finish=root.GetComponent<FemaleGarmentFinish>();if(finish)finish.Apply();
     Call("Correctives",root);
     var pivot=new GameObject("Surface bake").transform;object[] ba={root,pivot,null};var parts=(IEnumerable)typeof(HeroTurnaround).GetMethod("Bake",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,ba);
     Vector3 face=new Vector3(0,head.position.y+.035f,0);
     var views=new List<(string,Vector3,float,float,float,int,int)>{("face",face,.70f,28,24,720,720),("polo",new Vector3(0,head.position.y-.30f,0),1.15f,30,28,720,720)};
     if(swatch=="default"){views.Add(("eyes",face+new Vector3(0,.02f,0),.36f,22,12,720,360));views.Add(("full",new Vector3(0,.90f,0),3.35f,30,28,600,750));}
     string stem=(golf?"golf":"tennis")+"_"+skinName+"_"+swatch;
     foreach(var (view,target,dist,yaw,fov,w,h) in views) {
      c.fieldOfView=fov;c.transform.position=target+Quaternion.Euler(0,yaw,0)*Vector3.forward*dist;c.transform.LookAt(target);
      Shot(c,Path.Combine(output,stem+"_"+view+".jpg"),w,h);
     }
     foreach(var p in parts)Object.DestroyImmediate((GameObject)p.GetType().GetField("go").GetValue(p));foreach(var rr in (List<Renderer>)ba[2])if(rr)rr.enabled=true;Object.DestroyImmediate(pivot.gameObject);
     log.AppendLine(stem+" skin="+skinHex);
    }
    // Active female material flags as rendered (proof that the branches are wired).
    foreach(var r in root.GetComponentsInChildren<Renderer>(true))foreach(var m in r.sharedMaterials)if(m&&m.name.Contains("(hero)"))
     log.AppendLine($"{(golf?"golf":"tennis")} {r.name} {m.name} shader={m.shader.name} female={(m.HasProperty("_FemaleSurface")?m.GetFloat("_FemaleSurface"):-1)} eye={(m.HasProperty("_FemaleEyeRole")?m.GetFloat("_FemaleEyeRole"):-1)} skin={(m.HasProperty("_SkinFinish")?m.GetFloat("_SkinFinish"):-1)} wrap={(m.HasProperty("_Wrap")?m.GetFloat("_Wrap"):-1)}");
    log.AppendLine($"globals film={Shader.GetGlobalFloat("_HeroFilmResponse")} profile={Shader.GetGlobalFloat("_HeroProfile")} lighting={Shader.GetGlobalFloat("_HeroLightingEnabled")} fill={Shader.GetGlobalFloat("_HeroPresentationFill")} skinExp={Shader.GetGlobalFloat("_HeroSkinLightExposure")}");
    Object.DestroyImmediate(root);Call("Release");
   }
   File.WriteAllText(Path.Combine(output,"materials.txt"),log.ToString());
  }
 }
}
#endif
