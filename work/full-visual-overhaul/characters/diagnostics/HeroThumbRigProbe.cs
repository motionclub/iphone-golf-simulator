#if UNITY_EDITOR
using System;using System.Linq;using System.IO;using System.Collections.Generic;using UnityEngine;using UnityEditor;using UnityEditor.SceneManagement;using GolfArcade.Tennis;using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class HeroThumbRigProbe {
  static Vector3[] Skin(SkinnedMeshRenderer body){var v=body.sharedMesh.vertices;var w=body.sharedMesh.boneWeights;var bind=body.sharedMesh.bindposes;var matrices=body.bones.Select((b,i)=>body.transform.worldToLocalMatrix*b.localToWorldMatrix*bind[i]).ToArray();var result=new Vector3[v.Length];for(int i=0;i<v.Length;i++){var b=w[i];result[i]=matrices[b.boneIndex0].MultiplyPoint3x4(v[i])*b.weight0+matrices[b.boneIndex1].MultiplyPoint3x4(v[i])*b.weight1+matrices[b.boneIndex2].MultiplyPoint3x4(v[i])*b.weight2+matrices[b.boneIndex3].MultiplyPoint3x4(v[i])*b.weight3;}return result;}
  public static void Run(){
   int code=0;try {
    EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);string output=Environment.GetEnvironmentVariable("HTR_OUT")??Path.GetFullPath("../proof/full-visual-overhaul/thumb-rig-probe-1");Directory.CreateDirectory(output);var report=new System.Text.StringBuilder();
    var cam=new GameObject("Anatomical thumb proof").AddComponent<Camera>();cam.backgroundColor=new Color(.22f,.27f,.34f);cam.clearFlags=CameraClearFlags.SolidColor;cam.orthographic=true;cam.orthographicSize=.12f;
    var light=new GameObject("Thumb proof key").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.5f;light.transform.rotation=Quaternion.Euler(30,-30,0);RenderSettings.ambientLight=Color.white*.4f;RenderSettings.fog=false;
    foreach(string sex in new[]{"Male","Female"}){
     var root=Object.Instantiate(Resources.Load<GameObject>("Tennis/Customization/Player"+sex));var hero=root.GetComponent<MatchHeroLook>();var driver=root.GetComponent<HeroTennisDriver>();driver.enabled=false;
     var original=hero.body.sharedMesh;HeroThumbRigMigration migration=null;float maximum=0;
     foreach(var slot in driver.slots.Where(s=>s.clip))foreach(float phase in new[]{0f,.25f,.5f,.75f,1f}){
      if(migration)migration.RestoreRaw();slot.clip.SampleAnimation(root,slot.clip.length*phase);
      var live=hero.body.sharedMesh;hero.body.sharedMesh=original;var before=Skin(hero.body);hero.body.sharedMesh=live;
      migration=HeroThumbRigMigration.Prepare(hero);migration.Rebase();var after=Skin(hero.body);float max=0,sum=0;for(int v=0;v<before.Length;v++){float error=Vector3.Distance(before[v],after[v]);max=Mathf.Max(max,error);sum+=error;}maximum=Mathf.Max(maximum,max);
      report.AppendLine(sex+" "+slot.id+" "+phase+" old/new skin max="+max.ToString("G8")+" mean="+(sum/before.Length).ToString("G8"));
     }
     report.AppendLine(sex+" RUNTIME_REBASE_PARITY "+maximum);if(maximum>.00002f)throw new InvalidOperationException(sex+" old-clip skinning parity failed "+maximum);
     Object.DestroyImmediate(root);
     foreach(string mode in new[]{"baseline","Proximal_plus","Proximal_minus","Intermediate_plus","Intermediate_minus","Distal_plus","Distal_minus","fist","fist_thumb_plus","fist_thumb_minus"}){
      root=Object.Instantiate(Resources.Load<GameObject>("Tennis/Customization/Player"+sex));hero=root.GetComponent<MatchHeroLook>();driver=root.GetComponent<HeroTennisDriver>();driver.enabled=false;driver.slots.First(s=>s.id==HeroTennisDriver.Clip.Ready).clip.SampleAnimation(root,.6f);TennisPerformanceBuild.Pose(root.transform,hero,HeroTennisDriver.Clip.MatchWin,1,false);
      migration=HeroThumbRigMigration.Prepare(hero);migration.Rebase();migration.ApplyAnatomicalWeights();
      var hand=hero.Bone(HumanBodyBones.LeftHand);var bones=hero.body.bones;var binds=hero.body.sharedMesh.bindposes;var rest=bones.Select((b,i)=>new{b,m=binds[i].inverse}).ToDictionary(x=>x.b,x=>x.m);var toHand=rest[hand].inverse;
      Transform B(string digit,string joint)=>hero.Bone((HumanBodyBones)Enum.Parse(typeof(HumanBodyBones),"Left"+digit+joint));Vector3 H(Transform b)=>toHand.MultiplyPoint3x4(rest[b].GetColumn(3));
      var palm=Vector3.Cross((H(B("Index","Proximal"))-H(B("Little","Proximal"))).normalized,H(B("Middle","Proximal")).normalized).normalized;
      if(mode.StartsWith("fist"))HeroGripPolish.ApplyFist(hero,true,.85f);
      string[] joints={"Proximal","Intermediate","Distal"};for(int j=0;j<3;j++){
       var bone=B("Thumb",joints[j]);var next=j<2?B("Thumb",joints[j+1]):null;var frame=toHand*rest[bone];var direction=next?H(next)-H(bone):frame.MultiplyVector(Vector3.up);var hinge=frame.inverse.MultiplyVector(Vector3.Cross(direction.normalized,palm).normalized).normalized;
       float degrees=mode.StartsWith(joints[j]+"_")?(mode.EndsWith("plus")?30:-30):mode=="fist_thumb_plus"?new[]{25f,30f,15f}[j]:mode=="fist_thumb_minus"?-new[]{25f,30f,15f}[j]:0;
       if(degrees!=0)bone.localRotation*=Quaternion.AngleAxis(degrees,hinge);
       report.AppendLine(sex+" "+mode+" "+bone.name+" head="+H(bone)+" hinge="+hinge+" degrees="+degrees);
      }
      var mesh=new Mesh();hero.body.BakeMesh(mesh,true);var node=new GameObject("Evaluated anatomical hand");node.transform.SetParent(hero.body.transform,false);node.AddComponent<MeshFilter>().sharedMesh=mesh;node.AddComponent<MeshRenderer>().sharedMaterials=hero.body.sharedMaterials;
      foreach(var r in root.GetComponentsInChildren<Renderer>(true))if(r.gameObject!=node)r.enabled=false;
      var centre=hand.position+hand.up*.07f;
      foreach(var shot in new[]{("front",new Vector3(-.35f,.04f,.65f)),("side",new Vector3(-.65f,.08f,.12f))}){
       cam.transform.SetPositionAndRotation(centre+shot.Item2,Quaternion.LookRotation(-shot.Item2));var rt=RenderTexture.GetTemporary(640,640,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Default,4);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var tex=new Texture2D(640,640,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,640,640),0,0);tex.Apply();File.WriteAllBytes(Path.Combine(output,sex+"_"+mode+"_"+shot.Item1+".png"),tex.EncodeToPNG());cam.targetTexture=null;RenderTexture.active=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(tex);
      }
      Object.DestroyImmediate(root);Object.DestroyImmediate(mesh);
     }
    }
    File.WriteAllText(Path.Combine(output,"thumb-rig-v2-audit.txt"),report.ToString());Debug.Log("HERO_THUMB_RIG_PROBE_COMPLETE "+output);
   }catch(Exception e){Debug.LogException(e);code=1;}if(Application.isBatchMode)EditorApplication.Exit(code);
  }
 }
}
#endif
