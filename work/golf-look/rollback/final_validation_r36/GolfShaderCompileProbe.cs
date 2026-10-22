using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Rendering;
using UnityEngine;
namespace GolfArcade.EditorTools
{
 public static class GolfShaderCompileProbe
 {
  static string Out=>Environment.GetEnvironmentVariable("GOLF_COMPILE_OUT");
  static void Dump(object value,string tag,List<string> log)
  {
   foreach(var f in value.GetType().GetFields(BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic))
   {
    var v=f.GetValue(value);
    if(v is byte[] bytes)File.WriteAllBytes(Path.Combine(Out,tag+"_"+f.Name+".bin"),bytes);
    else if(v is string s)File.WriteAllText(Path.Combine(Out,tag+"_"+f.Name+".txt"),s);
    else log.Add(tag+" "+f.Name+"="+v);
   }
  }
  public static void Run()
  {
   Directory.CreateDirectory(Out);UnityEditor.SceneManagement.EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");var camera=UnityEngine.Object.FindFirstObjectByType<Camera>();if(camera){var rt=new RenderTexture(64,64,24);camera.targetTexture=rt;camera.Render();camera.targetTexture=null;UnityEngine.Object.DestroyImmediate(rt);}var log=new List<string>();bool ok=true;
   foreach(string name in new[]{"GolfArcade/GolfGround","GolfArcade/GolfRock","GolfArcade/GolfPlants","GolfArcade/TennisCharacter","GolfArcade/TennisFace","GolfArcade/TennisCloth","Universal Render Pipeline/Lit"})
   {
    var shader=Shader.Find(name);if(!shader){log.Add("MISSING "+name);ok=false;continue;}
    var warm=new Material(shader);warm.SetPass(0);UnityEngine.Object.DestroyImmediate(warm);
    var pass=ShaderUtil.GetShaderData(shader).GetSubshader(0).GetPass(0);
    foreach(string mode in name=="GolfArcade/GolfGround"?new[]{"plain","golf","sand_plain","sand_golf"}:new[]{"plain","golf"})
    {
     bool lit=mode.EndsWith("golf");
     var keywords=lit?new List<string>{"_MAIN_LIGHT_SHADOWS","_ADDITIONAL_LIGHTS","FOG_LINEAR"}:new List<string>();
     if(mode.StartsWith("sand"))keywords.Add("_GOLF_SAND");
     if(lit)keywords.Add(name.StartsWith("GolfArcade/Golf")?"_SHADOWS_SOFT":"_SHADOWS_SOFT_LOW");
     if(name=="Universal Render Pipeline/Lit")keywords.AddRange(new[]{"_NORMALMAP","_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A"});
     var result=pass.CompileVariant(ShaderType.Fragment,keywords.ToArray(),ShaderCompilerPlatform.Metal,BuildTarget.iOS);
     string tag=name.Split('/').Last()+"_"+mode;Dump(result,tag,log);ok&=result.Success;
     log.Add(tag+" SUCCESS="+result.Success+" keywords="+string.Join(",",keywords));
     foreach(var msg in result.Messages)log.Add(tag+" "+msg.severity+" "+msg.message);
     if(name=="GolfArcade/GolfPlants"){var vertex=pass.CompileVariant(ShaderType.Vertex,keywords.ToArray(),ShaderCompilerPlatform.Metal,BuildTarget.iOS);Dump(vertex,tag+"_vertex",log);ok&=vertex.Success;log.Add(tag+" VERTEX_SUCCESS="+vertex.Success);foreach(var msg in vertex.Messages)log.Add(tag+" VERTEX "+msg.severity+" "+msg.message);}
    }
    var type=typeof(ShaderUtil);var compat=type.GetMethod("GetSRPBatcherCompatibilityCode",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic,null,new[]{typeof(Shader),typeof(int)},null);
    if(compat!=null){int code=(int)compat.Invoke(null,new object[]{shader,0});log.Add(name+" SRP_CODE="+code);
        var reason=type.GetMethod("GetSRPBatcherCompatibilityIssueReason",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic,null,new[]{typeof(Shader),typeof(int),typeof(int)},null);
        if(reason!=null)log.Add(name+" SRP_REASON="+reason.Invoke(null,new object[]{shader,0,code}));ok&=code==0;}
    foreach(var msg in ShaderUtil.GetShaderMessages(shader)){log.Add(name+" "+msg.severity+" "+msg.message);if(msg.severity.ToString()=="Error")ok=false;}
   }
   File.WriteAllLines(Path.Combine(Out,"compiled_metal.txt"),log);EditorApplication.Exit(ok?0:1);
  }
 }
}
