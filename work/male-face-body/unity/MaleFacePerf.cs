#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Diagnostics;
using UnityEngine;
using UnityEditor;
using GolfArcade.Tennis;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 /// Shader cost check for the 2026-10-17 male face pass (chat 11, copy of FemaleFacePerf): both heroes (HeroTurnaround studio, game shaders) rendered at 1920x1080,
 /// 400 frames per view, each frame synced with a 1-pixel readback so the time includes the GPU. Views: "pair" (both full bodies,
 /// gameplay-like size) and "face" (the male face filling the frame: worst case for HeroFaceSkin). FACE_PERF_OUT = text file.
 public static class MaleFacePerf {
  static object Call(string n,params object[] a)=>typeof(HeroTurnaround).GetMethod(n,BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,a);
  static GameObject Build(string id){object[] args={id,null,null};var root=(GameObject)typeof(HeroTurnaround).GetMethod("BuildHero",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,args);Call("RestPose",root);return root;}
  public static void Run() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("FACE_PERF_OUT");
   Call("Studio",false);
   var female=Build("MatchHero_Female"); var male=Build("MatchHero_Male");
   female.transform.position=new Vector3(-.45f,0,0); male.transform.position=new Vector3(.45f,0,0);
   female.GetComponent<MatchHeroLook>().SetSkin(HeroKit.Hex("E2A06E"));
   var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");
   var rt=new RenderTexture(1920,1080,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB){antiAliasing=4};rt.Create();
   var px=new Texture2D(1,1,TextureFormat.RGBA32,false);
   var log=new System.Text.StringBuilder();
   var head=male.GetComponent<MatchHeroLook>().Bone(HumanBodyBones.Head);   // male face fills the frame (chat 11)
   foreach(var (view,pos,target,fov) in new[]{("pair",new Vector3(0,1.0f,4.2f),new Vector3(0,.9f,0),40f),("face",head.position+new Vector3(0,.05f,.55f),head.position+new Vector3(0,.05f,0),30f)}){
    c.targetTexture=rt;c.fieldOfView=fov;c.aspect=1920f/1080f;c.transform.position=pos;c.transform.LookAt(target);
    for(int k=0;k<30;k++){c.Render();RenderTexture.active=rt;px.ReadPixels(new Rect(0,0,1,1),0,0);}
    var times=new double[400];
    for(int k=0;k<times.Length;k++){var sw=Stopwatch.StartNew();c.Render();RenderTexture.active=rt;px.ReadPixels(new Rect(0,0,1,1),0,0);px.Apply();sw.Stop();times[k]=sw.Elapsed.TotalMilliseconds;}
    Array.Sort(times);
    log.AppendLine($"{view} 1920x1080 msaa4: median {times[200]:F3} ms  p10 {times[40]:F3}  p90 {times[360]:F3}");
    var tex=new Texture2D(1920,1080,TextureFormat.RGB24,false);RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,1920,1080),0,0);tex.Apply();
    File.WriteAllBytes(Path.ChangeExtension(output,null)+"_"+view+".jpg",tex.EncodeToJPG(85));Object.DestroyImmediate(tex);
   }
   c.targetTexture=null;RenderTexture.active=null;rt.Release();
   log.AppendLine("device="+SystemInfo.graphicsDeviceName+" api="+SystemInfo.graphicsDeviceType);
   File.WriteAllText(output,log.ToString());
   Object.DestroyImmediate(female);Object.DestroyImmediate(male);Call("Release");
  }
 }
}
#endif
