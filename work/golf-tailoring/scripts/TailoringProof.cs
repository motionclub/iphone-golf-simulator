using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using GolfArcade.Game;
using GolfArcade.Tennis;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class TailoringProof {
  static string Out=>Environment.GetEnvironmentVariable("TAILOR_OUT");
  public static void Run(){try{Capture();EditorApplication.Exit(0);}catch(Exception e){Debug.LogException(e);EditorApplication.Exit(1);}}
  public static void After(){try{AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);GolfGarmentRepair.Build();Capture();MatchHeroLockerExport.RunGolf();}catch(Exception e){Debug.LogException(e);EditorApplication.Exit(1);}}
  static void Capture(){
   Directory.CreateDirectory(Out);EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
   QualitySettings.skinWeights=SkinWeights.FourBones;QualitySettings.antiAliasing=4;
   RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.48f,.48f,.48f);RenderSettings.fog=false;
   var l=new GameObject("Key").AddComponent<Light>();l.type=LightType.Directional;l.intensity=1.7f;l.transform.rotation=Quaternion.Euler(35,-35,0);l.shadows=LightShadows.Soft;
   var fill=new GameObject("Fill").AddComponent<Light>();fill.type=LightType.Directional;fill.intensity=.65f;fill.transform.rotation=Quaternion.Euler(30,145,0);
   var cam=new GameObject("Proof camera").AddComponent<Camera>();cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.24f,.28f,.32f);cam.nearClipPlane=.02f;cam.farClipPlane=100;cam.orthographic=true;
   foreach(bool female in new[]{false,true}){
    string sex=female?"Female":"Male";
    var holder=new GameObject("Hero holder");var hero=HeroGolfer.Build(holder.transform,new HeroLook{Female=female,Skin=new Color(.95f,.78f,.64f),HairColor=new Color(.2f,.14f,.1f),Haircut=1});
    var look=hero.Root.GetComponent<MatchHeroLook>();typeof(MatchHeroLook).GetMethod("OwnMaterials",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(look,null);
    var clips=AssetDatabase.LoadAllAssetsAtPath("Assets/Resources/Hero/golfer_"+(female?"f":"m")+".fbx").OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__")).ToArray();
    Debug.Log("TAILOR_CLIPS "+sex+" "+string.Join(",",clips.Select(c=>c.name+":"+c.length)));
    var clip=clips.FirstOrDefault(c=>c.name.IndexOf("drive",StringComparison.OrdinalIgnoreCase)>=0)??clips.First();
    var poses=new[]{("Address",0f),("Backswing",56f/30),("Impact",69f/30),("Finish",clip.length*.9f)};
    foreach(var pose in poses){
     clip.SampleAnimation(hero.Root,pose.Item2);hero.Root.GetComponent<GolfGarmentCorrectives>().Apply();
     foreach(var r in hero.Root.GetComponentsInChildren<SkinnedMeshRenderer>())r.updateWhenOffscreen=true;
     foreach(int angle in pose.Item1=="Address"?new[]{0,90,180,270}:new[]{0,90}){
      var bounds=new Bounds();bool first=true;
      foreach(var r in look.kit.Where(r=>r.enabled)){var mesh=new Mesh();r.BakeMesh(mesh);foreach(var p in mesh.vertices){var w=r.transform.TransformPoint(p);if(first){bounds=new Bounds(w,Vector3.zero);first=false;}else bounds.Encapsulate(w);}Object.DestroyImmediate(mesh);}
      var target=bounds.center;target.y=.88f;cam.orthographicSize=.98f;
      var off=Quaternion.Euler(0,angle,0)*new Vector3(0,.05f,-4);cam.transform.SetPositionAndRotation(target+off,Quaternion.LookRotation(-off));
      Save(cam,sex+"_"+pose.Item1+"_"+angle,900,1100);
      if(pose.Item1=="Address"&&angle==0){cam.orthographicSize=.29f;target.y=.97f;cam.transform.SetPositionAndRotation(target+off,Quaternion.LookRotation(-off));Save(cam,sex+"_Waist",1100,750);cam.orthographicSize=.24f;target.y=.15f;cam.transform.SetPositionAndRotation(target+off,Quaternion.LookRotation(-off));Save(cam,sex+"_Shoes",1100,750);}
     }
    }
    Object.DestroyImmediate(holder);
   }
   foreach(var s in new[]{"GolfArcade/TennisCloth","GolfArcade/TennisCharacter"}){var shader=Shader.Find(s);if(!shader||ShaderUtil.ShaderHasError(shader))throw new Exception("Shader failed "+s);}
   File.WriteAllText(Path.Combine(Out,"PASS.txt"),"Both live HeroGolfer instances, four sampled poses, front/side/back captures; shaders compile on "+SystemInfo.graphicsDeviceType);
  }
  static void Save(Camera cam,string file,int w,int h){var rt=RenderTexture.GetTemporary(w,h,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Default,4);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var tex=new Texture2D(w,h,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,w,h),0,0);tex.Apply();File.WriteAllBytes(Path.Combine(Out,file+".png"),tex.EncodeToPNG());cam.targetTexture=null;RenderTexture.active=null;Object.DestroyImmediate(tex);RenderTexture.ReleaseTemporary(rt);}
 }
}
