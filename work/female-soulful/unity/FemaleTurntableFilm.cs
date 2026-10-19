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
 /// Female 360-degree orbit frames at several zoom levels (golf and tennis kits, studio lights, Cream skin).
 /// TURN_OUT = folder; frames land in <folder>/<sport>_<framing>/f_00000.jpg. TURN_FRAMES (default 120).
 public static class FemaleTurntableFilm {
  static object Call(string n,params object[] a)=>typeof(HeroTurnaround).GetMethod(n,BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,a);
  static void Shot(Camera c,string p,int w,int h){var rt=RenderTexture.GetTemporary(w,h,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,4);var prior=RenderTexture.active;c.targetTexture=rt;c.aspect=(float)w/h;c.Render();RenderTexture.active=rt;var t=new Texture2D(w,h,TextureFormat.RGB24,false);t.ReadPixels(new Rect(0,0,w,h),0,0);t.Apply();File.WriteAllBytes(p,t.EncodeToJPG(88));RenderTexture.active=prior;c.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(t);}
  public static void Run(){
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("TURN_OUT");int frames=int.Parse(Environment.GetEnvironmentVariable("TURN_FRAMES")??"120");
   foreach(bool golf in new[]{true,false}){
    Call("Studio",golf);object[] args={golf?"GolfKitHero_Female":"MatchHero_Female",null,null};var root=(GameObject)typeof(HeroTurnaround).GetMethod("BuildHero",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,args);var look=root.GetComponent<MatchHeroLook>();
    Call("RestPose",root);
    foreach(var pair in new[]{(HumanBodyBones.LeftUpperArm,HumanBodyBones.LeftLowerArm),(HumanBodyBones.RightUpperArm,HumanBodyBones.RightLowerArm)}){var upper=look.Bone(pair.Item1);var lower=look.Bone(pair.Item2);float sign=Mathf.Sign(upper.position.x);var direction=Vector3.down*Mathf.Cos(25*Mathf.Deg2Rad)+Vector3.right*sign*Mathf.Sin(25*Mathf.Deg2Rad);upper.rotation=Quaternion.FromToRotation(lower.position-upper.position,direction)*upper.rotation;}
    Call("Correctives",root);
    var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");
    var head=look.Bone(HumanBodyBones.Head);
    look.SetKit(golf?"E87B65":"C0D52F",golf?"23304B":"EAE7DE","FFFFFF");look.SetSkin(HeroKit.Hex("EEBB8F"));
    var finish=root.GetComponent<FemaleGarmentFinish>();if(finish)finish.Apply();
    Call("Correctives",root);
    var pivot=new GameObject("Turn bake").transform;object[] ba={root,pivot,null};var parts=(IEnumerable)typeof(HeroTurnaround).GetMethod("Bake",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,ba);
    float hy=head.position.y;
    var framings=new List<(string,Vector3,float,float)>{("face",new Vector3(0,hy+.03f,0),.62f,22),("upper",new Vector3(0,hy-.28f,0),1.25f,28),("lower",new Vector3(0,.62f,0),2.0f,28),("feet",new Vector3(0,.12f,0),1.1f,28),("full",new Vector3(0,.88f,0),3.6f,28)};
    foreach(var (name,target,dist,fov) in framings){
     string dir=Path.Combine(output,(golf?"golf":"tennis")+"_"+name);Directory.CreateDirectory(dir);c.fieldOfView=fov;
     for(int i=0;i<frames;i++){float yaw=360f*i/frames;c.transform.position=target+Quaternion.Euler(0,yaw,0)*Vector3.forward*dist;c.transform.LookAt(target);Shot(c,Path.Combine(dir,$"f_{i:D5}.jpg"),720,720);}
    }
    foreach(var p in parts)Object.DestroyImmediate((GameObject)p.GetType().GetField("go").GetValue(p));foreach(var rr in (List<Renderer>)ba[2])if(rr)rr.enabled=true;Object.DestroyImmediate(pivot.gameObject);
    Object.DestroyImmediate(root);Call("Release");
   }
  }
 }
}
#endif
