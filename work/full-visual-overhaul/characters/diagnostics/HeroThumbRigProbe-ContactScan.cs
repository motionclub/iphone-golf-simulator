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
     string handPath="Assets/Resources/Tennis/Premium/Hands/"+sex+".fbx";
     var importer=AssetImporter.GetAtPath(handPath) as ModelImporter;if(importer){importer.isReadable=true;importer.importAnimation=false;importer.importNormals=ModelImporterNormals.Import;importer.meshCompression=ModelImporterMeshCompression.Off;importer.SaveAndReimport();}
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
     foreach(string mode in new[]{"baseline","Proximal_plus","Proximal_minus","Intermediate_plus","Intermediate_minus","Distal_plus","Distal_minus","fist","fist_closed","fist60","fist78","fist_thumb_plus","fist_thumb_minus"}){
      root=Object.Instantiate(Resources.Load<GameObject>("Tennis/Customization/Player"+sex));hero=root.GetComponent<MatchHeroLook>();driver=root.GetComponent<HeroTennisDriver>();driver.enabled=false;driver.slots.First(s=>s.id==HeroTennisDriver.Clip.Ready).clip.SampleAnimation(root,.6f);TennisPerformanceBuild.Pose(root.transform,hero,HeroTennisDriver.Clip.MatchWin,1,false);
      var originalBody=hero.body.sharedMesh;var originalPalette=hero.body.bones.ToArray();var originalSkin=Skin(hero.body);var originalHandBind=originalBody.bindposes[Array.FindIndex(originalPalette,b=>b&&b.name=="LeftHand")];
      if(Environment.GetEnvironmentVariable("HTR_REBUILT")=="1")HeroContinuousHandMesh.Apply(hero);
      migration=HeroThumbRigMigration.Prepare(hero);migration.Rebase();if(!hero.body.sharedMesh.name.Contains("(continuous hands)"))migration.ApplyAnatomicalWeights();
      var hand=hero.Bone(HumanBodyBones.LeftHand);var bones=hero.body.bones;var binds=hero.body.sharedMesh.bindposes;var rest=bones.Select((b,i)=>new{b,m=binds[i].inverse}).ToDictionary(x=>x.b,x=>x.m);var toHand=rest[hand].inverse;
      Transform B(string digit,string joint)=>hero.Bone((HumanBodyBones)Enum.Parse(typeof(HumanBodyBones),"Left"+digit+joint));Vector3 H(Transform b)=>toHand.MultiplyPoint3x4(rest[b].GetColumn(3));
      var palm=Vector3.Cross((H(B("Index","Proximal"))-H(B("Little","Proximal"))).normalized,H(B("Middle","Proximal")).normalized).normalized;
      if(mode.StartsWith("fist"))HeroGripPolish.ApplyFist(hero,true,mode=="fist_closed"||mode=="fist60"||mode=="fist78"?1f:.85f,mode=="fist60"?.60f:mode=="fist78"?.78f:.68f);
      string[] joints={"Proximal","Intermediate","Distal"};for(int j=0;j<3;j++){
       var bone=B("Thumb",joints[j]);var next=j<2?B("Thumb",joints[j+1]):null;var frame=toHand*rest[bone];var direction=next?H(next)-H(bone):frame.MultiplyVector(Vector3.up);var hinge=frame.inverse.MultiplyVector(Vector3.Cross(direction.normalized,palm).normalized).normalized;
       float degrees=mode.StartsWith(joints[j]+"_")?(mode.EndsWith("plus")?30:-30):mode=="fist_thumb_plus"?new[]{25f,30f,15f}[j]:mode=="fist_thumb_minus"?-new[]{25f,30f,15f}[j]:0;
       if(degrees!=0)bone.localRotation*=Quaternion.AngleAxis(degrees,hinge);
       report.AppendLine(sex+" "+mode+" "+bone.name+" head="+H(bone)+" hinge="+hinge+" degrees="+degrees);
      }
      // Compare original/rebuilt wrist under the same final pose, including the
      // deliberate new-reaction wrist straightening. No old source clip is edited.
      var keepMesh=hero.body.sharedMesh;var keepPalette=hero.body.bones;hero.body.sharedMesh=originalBody;hero.body.bones=originalPalette;originalSkin=Skin(hero.body);hero.body.sharedMesh=keepMesh;hero.body.bones=keepPalette;
      var currentVertices=hero.body.sharedMesh.vertices;var currentSkin=Skin(hero.body);var currentWeights=hero.body.sharedMesh.boneWeights;var oldVertices=originalBody.vertices;var oldWeights=originalBody.boneWeights;
      Vector3Int Key(Vector3 v)=>new(Mathf.RoundToInt(v.x*1000000),Mathf.RoundToInt(v.y*1000000),Mathf.RoundToInt(v.z*1000000));
      var lookup=currentVertices.Select((v,i)=>new{v,i}).GroupBy(v=>Key(v.v)).ToDictionary(g=>g.Key,g=>g.First().i);
      var errors=new float[3];var counts=new int[3];int missing=0;float weightError=0;
      Dictionary<string,float> Weights(BoneWeight w,Transform[] palette){var map=new Dictionary<string,float>();int[] ids={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] ws={w.weight0,w.weight1,w.weight2,w.weight3};for(int k=0;k<4;k++)if(ws[k]>0){string name=palette[ids[k]].name;if(!map.ContainsKey(name))map[name]=0;map[name]+=ws[k];}return map;}
      for(int v=0;v<oldVertices.Length;v++){
       var local=originalHandBind.MultiplyPoint3x4(oldVertices[v]);if(Mathf.Abs(local.x)>.08f||Mathf.Abs(local.z)>.07f||local.y<-.03f||local.y>.034f)continue;
       var ow=Weights(oldWeights[v],originalPalette);if(ow.Any(k=>new[]{"Index","Middle","Ring","Little","Thumb"}.Any(d=>k.Key.Contains(d))&&k.Value>.001f))continue;
       if(!lookup.TryGetValue(Key(oldVertices[v]),out int current)){missing++;continue;}
       int band=local.y<-.005f?0:local.y<.020f?1:2;counts[band]++;errors[band]=Mathf.Max(errors[band],Vector3.Distance(originalSkin[v],currentSkin[current]));var nw=Weights(currentWeights[current],hero.body.bones);foreach(string n in ow.Keys.Union(nw.Keys))weightError=Mathf.Max(weightError,Mathf.Abs(ow.GetValueOrDefault(n)-nw.GetValueOrDefault(n)));
      }
      report.AppendLine(sex+" "+mode+" WRIST_EXACT_ORIGINAL bands[-30,-5]/[-5,20]/[20,34]mm counts="+string.Join(",",counts)+" skinnedMaxMetres="+string.Join(",",errors.Select(e=>e.ToString("G8")))+" missing="+missing+" weightMax="+weightError);
      foreach(string digit in new[]{"Index","Middle","Ring","Little","Thumb"}){
       int di=Array.FindIndex(hero.body.bones,b=>b&&b.name=="Left"+digit+"Distal");var tipCandidates=new List<int>();float far=0;
       for(int v=0;v<currentVertices.Length;v++){var w=currentWeights[v];float amount=(w.boneIndex0==di?w.weight0:0)+(w.boneIndex1==di?w.weight1:0)+(w.boneIndex2==di?w.weight2:0)+(w.boneIndex3==di?w.weight3:0);if(amount<.4f)continue;tipCandidates.Add(v);far=Mathf.Max(far,hero.body.sharedMesh.bindposes[di].MultiplyPoint3x4(currentVertices[v]).magnitude);}
       var chosen=tipCandidates.Where(v=>hero.body.sharedMesh.bindposes[di].MultiplyPoint3x4(currentVertices[v]).magnitude>far*.8f).ToArray();var tip=chosen.Length>0?chosen.Aggregate(Vector3.zero,(a,v)=>a+currentSkin[v])/chosen.Length:Vector3.zero;
       var sourceTip=chosen.Length>0?chosen.Aggregate(Vector3.zero,(a,v)=>a+hero.body.sharedMesh.bindposes[di].MultiplyPoint3x4(currentVertices[v]))/chosen.Length:Vector3.zero;var rigTip=hero.body.bones[di].TransformPoint(sourceTip);var target=HeroGripPolish.PalmContactTarget(hero,true,digit);
       report.AppendLine(sex+" "+mode+" ACTUAL_WEIGHTED_TIP "+digit+" world="+hero.body.transform.TransformPoint(tip)+" handLocal="+hand.InverseTransformPoint(hero.body.transform.TransformPoint(tip))+" target="+target+" rigTip="+rigTip+" rigTipContactError="+Vector3.Distance(rigTip,target)+" actualSkinContactError="+Vector3.Distance(hero.body.transform.TransformPoint(tip),target)+" samples="+chosen.Length);
      }
      var mesh=new Mesh();hero.body.BakeMesh(mesh,true);var node=new GameObject("Evaluated anatomical hand");node.transform.SetParent(hero.body.transform,false);node.AddComponent<MeshFilter>().sharedMesh=mesh;node.AddComponent<MeshRenderer>().sharedMaterials=hero.body.sharedMaterials;
      foreach(var r in root.GetComponentsInChildren<Renderer>(true))if(r.gameObject!=node)r.enabled=false;
      var centre=hand.position+hand.up*.07f;
      foreach(var shot in new[]{("front",new Vector3(-.35f,.04f,.65f)),("side",new Vector3(-.65f,.08f,.12f))}){
       cam.transform.SetPositionAndRotation(centre+shot.Item2,Quaternion.LookRotation(-shot.Item2));var rt=RenderTexture.GetTemporary(640,640,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Default,4);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var tex=new Texture2D(640,640,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,640,640),0,0);tex.Apply();File.WriteAllBytes(Path.Combine(output,sex+"_"+mode+"_"+shot.Item1+".png"),tex.EncodeToPNG());cam.targetTexture=null;RenderTexture.active=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(tex);
      }
      if(mode=="baseline"||mode=="fist_closed"||mode=="fist60"||mode=="fist78"){
       string[] digits={"Thumb","Index","Middle","Ring","Little"};Color[] colours={new Color(.5f,.5f,.5f),Color.magenta,Color.red,Color.green,Color.blue,Color.yellow};var groups=Enumerable.Range(0,6).Select(_=>new List<int>()).ToArray();var triangles=mesh.triangles;
       for(int t=0;t<triangles.Length;t+=3){var amount=new float[6];for(int k=0;k<3;k++){var bw=currentWeights[triangles[t+k]];int[] ids={bw.boneIndex0,bw.boneIndex1,bw.boneIndex2,bw.boneIndex3};float[] ws={bw.weight0,bw.weight1,bw.weight2,bw.weight3};for(int q=0;q<4;q++)for(int d=0;d<5;d++)if(hero.body.bones[ids[q]].name.StartsWith("Left"+digits[d]))amount[d+1]+=ws[q];}int group=0;float best=.5f;for(int d=1;d<6;d++)if(amount[d]>best){best=amount[d];group=d;}groups[group].AddRange(new[]{triangles[t],triangles[t+1],triangles[t+2]});}
       var diagnostic=Object.Instantiate(mesh);diagnostic.subMeshCount=6;for(int d=0;d<6;d++)diagnostic.SetTriangles(groups[d],d);node.GetComponent<MeshFilter>().sharedMesh=diagnostic;var materials=colours.Select((c,d)=>new Material(Shader.Find("Universal Render Pipeline/Unlit")){name="Semantic digit "+d,color=c}).ToArray();node.GetComponent<MeshRenderer>().sharedMaterials=materials;
       foreach(var shot in new[]{("front",new Vector3(-.35f,.04f,.65f)),("side",new Vector3(-.65f,.08f,.12f))}){cam.transform.SetPositionAndRotation(centre+shot.Item2,Quaternion.LookRotation(-shot.Item2));var rt=RenderTexture.GetTemporary(640,640,24);cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;var tex=new Texture2D(640,640,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,640,640),0,0);tex.Apply();File.WriteAllBytes(Path.Combine(output,sex+"_"+mode+"_semantic_"+shot.Item1+".png"),tex.EncodeToPNG());cam.targetTexture=null;RenderTexture.active=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(tex);}
       report.AppendLine(sex+" semantic colours: gray palm/wrist, magenta thumb, red index, green middle, blue ring, yellow little");Object.DestroyImmediate(diagnostic);foreach(var material in materials)Object.DestroyImmediate(material);
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
