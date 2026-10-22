// Temporary capture helper. No saved scene or runtime asset changes.
using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.LowLevel;
using GolfArcade.Game;
using GolfArcade.Course;
namespace GolfArcade.EditorTools {
[InitializeOnLoad] public static class PostcardFlyThroughCapture {
 const string Flag="PostcardFlyThroughCapture"; const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
 [Serializable] public class Key {public float t,fov; public float[] pos,look;}
 [Serializable] public class Route {public string name;public int hole;public Key[] keys;}
 [Serializable] public class Config {public int width,height,fps,seconds;public Route[] routes;}
 static Config cfg;static string output;static int routeIndex=-1,loadFrame,index,renderIndex=-1,renderFrame=-1;static bool active,installed;
 static double deadline;static Camera cam;static GolfGame game;static CameraRig rig;static RenderTexture rt;static Texture2D tex;static PlayerLoopSystem original;
 static PostcardFlyThroughCapture(){EditorApplication.update+=Tick;RenderPipelineManager.endCameraRendering+=Rendered;}
 public static void Run(){SessionState.SetString(Flag+"out",Environment.GetEnvironmentVariable("GOLF_MOVIE_OUT"));SessionState.SetString(Flag+"cfg",Environment.GetEnvironmentVariable("GOLF_MOVIE_CFG"));SessionState.SetBool(Flag,true);EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");EditorApplication.isPlaying=true;}
 static PlayerLoopSystem Copy(PlayerLoopSystem s){var c=s;if(s.subSystemList!=null){c.subSystemList=new PlayerLoopSystem[s.subSystemList.Length];for(int i=0;i<s.subSystemList.Length;i++)c.subSystemList[i]=Copy(s.subSystemList[i]);}return c;}
 static bool Insert(ref PlayerLoopSystem s){if(s.type==typeof(UnityEngine.PlayerLoop.Update)){var old=s.subSystemList??Array.Empty<PlayerLoopSystem>();var n=new PlayerLoopSystem[old.Length+1];n[0]=new PlayerLoopSystem{type=typeof(PostcardFlyThroughCapture),updateDelegate=PlayerUpdate};Array.Copy(old,0,n,1,old.Length);s.subSystemList=n;return true;}if(s.subSystemList!=null)for(int i=0;i<s.subSystemList.Length;i++){var c=s.subSystemList[i];if(Insert(ref c)){s.subSystemList[i]=c;return true;}}return false;}
 static void Tick(){if(!SessionState.GetBool(Flag,false)||!EditorApplication.isPlaying)return;try{
 if(cfg==null){if(!HoleView.Current)return;game=UnityEngine.Object.FindFirstObjectByType<GolfGame>();rig=UnityEngine.Object.FindFirstObjectByType<CameraRig>();if(!game||!rig)return;cam=rig.Camera;output=SessionState.GetString(Flag+"out","");cfg=JsonUtility.FromJson<Config>(File.ReadAllText(SessionState.GetString(Flag+"cfg","")));Directory.CreateDirectory(output);rt=new RenderTexture(cfg.width,cfg.height,24,RenderTextureFormat.ARGB32){antiAliasing=4};rt.Create();tex=new Texture2D(cfg.width,cfg.height,TextureFormat.RGB24,false);Time.captureFramerate=cfg.fps;original=PlayerLoop.GetCurrentPlayerLoop();var changed=Copy(original);if(!Insert(ref changed))throw new Exception("Missing player loop");PlayerLoop.SetPlayerLoop(changed);installed=true;LoadNext();return;}
 if(active){if(EditorApplication.timeSinceStartup>deadline)throw new Exception("No completed automatic camera frame for 60 seconds");return;}
 if(index>=cfg.seconds*cfg.fps){if(routeIndex==cfg.routes.Length-1){File.WriteAllText(Path.Combine(output,"capture_complete.json"),JsonUtility.ToJson(cfg,true));Finish(0);return;}LoadNext();return;}
 if(Time.frameCount-loadFrame<12||UnityEngine.Object.FindObjectsByType<HoleView>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length!=1)return;
 if(HoleView.Current.Hole.Number!=cfg.routes[routeIndex].hole)throw new Exception("Wrong actual hole");
 foreach(var c in UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None))c.enabled=false;
 var golfer=(GolferView)typeof(GolfGame).GetField("golfer",Private).GetValue(game);if(golfer)golfer.SetVisible(false);
 var line=(LineRenderer)typeof(GolfGame).GetField("aimLine",Private).GetValue(game);if(line)line.enabled=false;
 var marker=(Transform)typeof(GolfGame).GetField("landingMarker",Private).GetValue(game);if(marker)marker.gameObject.SetActive(false);
 var ball=(Transform)typeof(GolfGame).GetField("ball",Private).GetValue(game);if(ball)ball.gameObject.SetActive(false);
 game.enabled=false;rig.enabled=false;foreach(var c in UnityEngine.Object.FindObjectsByType<Camera>(FindObjectsSortMode.None))c.enabled=c==cam;
 cam.targetTexture=rt;cam.farClipPlane=2000;cam.enabled=true;active=true;deadline=EditorApplication.timeSinceStartup+60;Pose();Debug.Log("[FlyThrough] START "+cfg.routes[routeIndex].name+" actual hole="+HoleView.Current.Hole.Number+" pipeline="+GraphicsSettings.currentRenderPipeline.name);
 }catch(Exception e){Debug.LogException(e);Finish(1);}}
 static void LoadNext(){routeIndex++;index=0;renderIndex=-1;renderFrame=-1;cam.targetTexture=null;game.enabled=true;rig.enabled=true;var n=Array.FindIndex(GolfArcade.Course.Course.Postcards().Holes,h=>h.Number==cfg.routes[routeIndex].hole);typeof(GolfGame).GetMethod("StartHole",Private).Invoke(game,new object[]{n});loadFrame=Time.frameCount;Directory.CreateDirectory(Path.Combine(output,cfg.routes[routeIndex].name));}
 static Vector3 V(float[] a)=>new Vector3(a[0],a[1],a[2]);
 static Vector3 S(Vector3 a,Vector3 b,Vector3 c,Vector3 d,float t)=>.5f*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
 static void Pose(){var keys=cfg.routes[routeIndex].keys;float time=index/(float)cfg.fps;int k=0;while(k<keys.Length-2&&time>keys[k+1].t)k++;float t=Mathf.Clamp01((time-keys[k].t)/(keys[k+1].t-keys[k].t));var a=keys[Math.Max(0,k-1)];var b=keys[k];var c=keys[k+1];var d=keys[Math.Min(keys.Length-1,k+2)];var pos=S(V(a.pos),V(b.pos),V(c.pos),V(d.pos),t);var look=S(V(a.look),V(b.look),V(c.look),V(d.look),t);cam.transform.SetPositionAndRotation(pos,Quaternion.LookRotation(look-pos,Vector3.up));cam.fieldOfView=Mathf.Lerp(b.fov,c.fov,t*t*(3-2*t));}
 static void Rendered(ScriptableRenderContext context,Camera c){if(active&&c==cam){renderIndex=index;renderFrame=Time.frameCount;}}
 public static void PlayerUpdate(){if(!active)return;try{if(renderIndex==index&&renderFrame<Time.frameCount){var old=RenderTexture.active;try{RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,cfg.width,cfg.height),0,0);tex.Apply(false);File.WriteAllBytes(Path.Combine(output,cfg.routes[routeIndex].name,"f_"+index.ToString("D5")+".jpg"),tex.EncodeToJPG(93));}finally{RenderTexture.active=old;}index++;deadline=EditorApplication.timeSinceStartup+60;if(index%60==0)Debug.Log("[FlyThrough] "+cfg.routes[routeIndex].name+" "+index+"/"+(cfg.seconds*cfg.fps));if(index>=cfg.seconds*cfg.fps){active=false;cam.enabled=false;return;}}Pose();}catch(Exception e){Debug.LogException(e);Finish(1);}}
 static void Finish(int code){active=false;SessionState.SetBool(Flag,false);Time.captureFramerate=0;if(installed)PlayerLoop.SetPlayerLoop(original);if(cam)cam.targetTexture=null;if(rt){rt.Release();UnityEngine.Object.DestroyImmediate(rt);}if(tex)UnityEngine.Object.DestroyImmediate(tex);Debug.Log("[FlyThrough] EXIT "+code);EditorApplication.Exit(code);}
}}

