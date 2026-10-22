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
 /// Female face review (2026-10-17 jaw/lips + skin pass). HeroTurnaround studio (game shaders, tennis light profile), body bind pose,
 /// a real locker skin pick, head framed like reference sheet 07 (front 0, three-quarter 45/315, profiles 90/270) plus expressions.
 /// FACE_REVIEW_OUT = folder; FACE_REVIEW_SKIN = hex (default E2A06E); FACE_REVIEW_SET = "views" (default) | "rig" | "tones".
 public static class FemaleFaceReview {
  static object Call(string n,params object[] a)=>typeof(HeroTurnaround).GetMethod(n,BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,a);
  static void Shot(Camera c,string p,int w,int h) {
   var rt=RenderTexture.GetTemporary(w,h,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,8);var prior=RenderTexture.active;c.targetTexture=rt;c.aspect=(float)w/h;c.Render();RenderTexture.active=rt;var t=new Texture2D(w,h,TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,w,h),0,0);t.Apply();File.WriteAllBytes(p,t.EncodeToPNG());RenderTexture.active=prior;c.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(t);
  }
  public static void Run() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("FACE_REVIEW_OUT");Directory.CreateDirectory(output);
   string skin=Environment.GetEnvironmentVariable("FACE_REVIEW_SKIN");if(string.IsNullOrEmpty(skin))skin="E2A06E";
   string set=Environment.GetEnvironmentVariable("FACE_REVIEW_SET");if(string.IsNullOrEmpty(set))set="views";
   var log=new System.Text.StringBuilder();
   Call("Studio",false);
   object[] args={"MatchHero_Female",null,null};var root=(GameObject)typeof(HeroTurnaround).GetMethod("BuildHero",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,args);var look=root.GetComponent<MatchHeroLook>();
   Call("RestPose",root);
   foreach(var pair in new[]{(HumanBodyBones.LeftUpperArm,HumanBodyBones.LeftLowerArm),(HumanBodyBones.RightUpperArm,HumanBodyBones.RightLowerArm)}){var upper=look.Bone(pair.Item1);var lower=look.Bone(pair.Item2);float sign=Mathf.Sign(upper.position.x);var direction=Vector3.down*Mathf.Cos(25*Mathf.Deg2Rad)+Vector3.right*sign*Mathf.Sin(25*Mathf.Deg2Rad);upper.rotation=Quaternion.FromToRotation(lower.position-upper.position,direction)*upper.rotation;}
   look.SetKit("BEBEBC","EAE7DE","FFFFFF");
   var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");
   c.backgroundColor=new Color(.89f,.89f,.87f);
   var head=look.Bone(HumanBodyBones.Head);
   // the head's own frame: crown..chin centre ~ head bone + 7 cm up
   Vector3 centre=new Vector3(0,head.position.y+.065f,head.position.z+.01f);
   string[] tones=set=="tones"?new[]{"F3C9A6","EEBB8F","E2A06E","C47A4C","965835","603924"}:new[]{skin};
   var moods=set=="rig"?new[]{("neutral",0f,0f,0f,0f),("blink",0f,0f,0f,1f),("smile",1f,0f,0f,0f),("sad",0f,1f,0f,0f),("shock",0f,0f,1f,0f),("smile_blink",1f,0f,0f,1f)}:new[]{("neutral",0f,0f,0f,0f)};
   var views=set=="views"?new[]{("front",0f),("tq45",45f),("right90",90f),("tq315",315f),("left270",270f)}:set=="rig"?new[]{("front",0f),("tq45",45f),("right90",90f)}:new[]{("front",0f),("tq45",45f)};
   foreach(var tone in tones) foreach(var (mood,smile,sad,shock,blink) in moods) {
    look.SetSkin(HeroKit.Hex(tone));
    var finish=root.GetComponent<FemaleGarmentFinish>();if(finish)finish.Apply();
    HeroFaceReferenceFit.ApplyMood(look,smile,sad,shock);
    look.SetFacePerformance(blink,Vector2.zero);
    Call("Correctives",root);
    foreach(var r in root.GetComponentsInChildren<Renderer>(true))if(r.name.StartsWith("Acc_")||r.name.Contains("Cap"))r.enabled=false;   // bald head, like sheet 07
    var pivot=new GameObject("Face bake").transform;object[] ba={root,pivot,null};var parts=(IEnumerable)typeof(HeroTurnaround).GetMethod("Bake",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,ba);
    { float d0=1.8f; c.fieldOfView=2*Mathf.Atan(.185f/d0)*Mathf.Rad2Deg; c.transform.position=centre+Vector3.forward*d0; c.transform.LookAt(centre); Shot(c,Path.Combine(output,"_prime.png"),256,256); File.Delete(Path.Combine(output,"_prime.png")); }   // first render after a shader change is a placeholder
    foreach(var (view,yaw) in views) {
     float dist=1.8f; c.fieldOfView=2*Mathf.Atan(.185f/dist)*Mathf.Rad2Deg;
     c.transform.position=centre+Quaternion.Euler(0,yaw,0)*Vector3.forward*dist;c.transform.LookAt(centre);
     string stem=set=="views"?view:set=="rig"?mood+"_"+view:tone+"_"+view;
     Shot(c,Path.Combine(output,stem+".png"),1080,1080);
     if(view=="front"||view=="right90"){   // mouth/jaw close-up
      c.fieldOfView=2*Mathf.Atan(.075f/dist)*Mathf.Rad2Deg;var lower=centre+new Vector3(0,-.075f,view=="front"?0:.075f);
      c.transform.position=lower+Quaternion.Euler(0,yaw,0)*Vector3.forward*dist;c.transform.LookAt(lower);
      Shot(c,Path.Combine(output,stem+"_lower.png"),1080,1080);
     }
    }
    foreach(var p in parts)Object.DestroyImmediate((GameObject)p.GetType().GetField("go").GetValue(p));foreach(var rr in (List<Renderer>)ba[2])if(rr)rr.enabled=true;Object.DestroyImmediate(pivot.gameObject);
    log.AppendLine($"{tone} {mood} smile={smile} sad={sad} shock={shock} blink={blink}");
   }
   log.AppendLine($"head bone {head.position.ToString("F4")} centre {centre.ToString("F4")}");
   foreach(var r in root.GetComponentsInChildren<Renderer>(true))foreach(var m in r.sharedMaterials)if(m&&m.HasProperty("_SkinFinish"))log.AppendLine($"{r.name} {m.name} shader={m.shader.name} skinFinish={m.GetFloat("_SkinFinish")}");
   log.AppendLine($"globals film={Shader.GetGlobalFloat("_HeroFilmResponse")} profile={Shader.GetGlobalFloat("_HeroProfile")} lighting={Shader.GetGlobalFloat("_HeroLightingEnabled")} fill={Shader.GetGlobalFloat("_HeroPresentationFill")}");
   Object.DestroyImmediate(root);Call("Release");
   File.WriteAllText(Path.Combine(output,"log.txt"),log.ToString());
  }
 }
}
#endif
