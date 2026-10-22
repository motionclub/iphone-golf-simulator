#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;
using UnityEditor;
using GolfArcade.Game;
using GolfArcade.Tennis;
using GolfArcade.Shot;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools {
 public static class FemaleGolfRuntimeReview {
  static GameObject captureRoot;
  const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
  static void Call(object o,string n,params object[] args)=>o.GetType().GetMethod(n,Private).Invoke(o,args);
  static void Correct(MatchHeroLook l) {
   foreach(var palette in l.GetComponentsInChildren<HeroArmSkinning>(true))palette.Apply();foreach(var sleeve in l.GetComponentsInChildren<FemaleSleeveSweep>(true))sleeve.Apply();l.GetComponent<HeroShoulderDeformation>()?.Apply();l.GetComponent<FemaleShoulderFit>()?.Apply();l.GetComponent<FemaleGarmentFinish>()?.Apply();l.GetComponent<GolfGarmentCorrectives>()?.Apply();KitV2PoseCorrectives.Attach(l);l.GetComponent<KitV2PoseCorrectives>()?.Apply();
  }
  static void Shot(Camera c,string path) {
   // Diagnostic: GOLF_REVIEW_HIDE=Body,Kit_Top hides named renderers for identification shots.
   var hideNames=new System.Collections.Generic.HashSet<string>((Environment.GetEnvironmentVariable("GOLF_REVIEW_HIDE")??"").Split(',').Where(x=>x.Length>0));
   var hidden=captureRoot.GetComponentsInChildren<Renderer>(true).Where(r=>r.enabled&&hideNames.Contains(r.name)).ToArray();foreach(var r in hidden)r.enabled=false;
   var renderers=captureRoot.GetComponentsInChildren<Renderer>(true).Where(r=>r.enabled&&r.gameObject.activeInHierarchy).ToArray();
   var bakedObjects=new System.Collections.Generic.List<GameObject>();
   foreach(var skin in renderers.OfType<SkinnedMeshRenderer>()) {
    var mesh=Object.Instantiate(skin.sharedMesh);var points=mesh.vertices;var normals=mesh.normals;
    var dp=new Vector3[points.Length];var dn=new Vector3[points.Length];var dt=new Vector3[points.Length];
    for(int shape=0;shape<mesh.blendShapeCount;shape++){float weight=skin.GetBlendShapeWeight(shape)/100f;if(Mathf.Abs(weight)<.00001f)continue;mesh.GetBlendShapeFrameVertices(shape,mesh.GetBlendShapeFrameCount(shape)-1,dp,dn,dt);for(int i=0;i<points.Length;i++){points[i]+=dp[i]*weight;normals[i]+=dn[i]*weight;}}
    var weights=mesh.boneWeights;var bind=mesh.bindposes;var matrices=skin.bones.Select((b,i)=>b.localToWorldMatrix*bind[i]).ToArray();
    for(int i=0;i<points.Length;i++){var w=weights[i];var p=points[i];var n=normals[i];
     points[i]=matrices[w.boneIndex0].MultiplyPoint3x4(p)*w.weight0+matrices[w.boneIndex1].MultiplyPoint3x4(p)*w.weight1+matrices[w.boneIndex2].MultiplyPoint3x4(p)*w.weight2+matrices[w.boneIndex3].MultiplyPoint3x4(p)*w.weight3;
     normals[i]=(matrices[w.boneIndex0].MultiplyVector(n)*w.weight0+matrices[w.boneIndex1].MultiplyVector(n)*w.weight1+matrices[w.boneIndex2].MultiplyVector(n)*w.weight2+matrices[w.boneIndex3].MultiplyVector(n)*w.weight3).normalized;}
    mesh.ClearBlendShapes();mesh.vertices=points;mesh.normals=normals;mesh.RecalculateBounds();var go=new GameObject("CPU posed "+skin.name);go.AddComponent<MeshFilter>().sharedMesh=mesh;var r=go.AddComponent<MeshRenderer>();r.sharedMaterials=skin.sharedMaterials;r.renderingLayerMask=skin.renderingLayerMask;skin.enabled=false;bakedObjects.Add(go);
   }
   var rt=RenderTexture.GetTemporary(800,800,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,4);var prev=RenderTexture.active;c.targetTexture=rt;c.Render();RenderTexture.active=rt;
   var tex=new Texture2D(800,800,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,800,800),0,0);tex.Apply();File.WriteAllBytes(path,tex.EncodeToJPG(94));RenderTexture.active=prev;c.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(tex);
   foreach(var go in bakedObjects){Object.DestroyImmediate(go.GetComponent<MeshFilter>().sharedMesh);Object.DestroyImmediate(go);}foreach(var r in renderers)if(r)r.enabled=true;foreach(var r in hidden)if(r)r.enabled=true;
  }
  static void Dump(SkinnedMeshRenderer r,string path) {
   var m=new Mesh();r.BakeMesh(m);
   var bakedVertices=m.vertices;var v=r.sharedMesh.vertices;var w=r.sharedMesh.boneWeights;var b=r.sharedMesh.bindposes;var bones=r.bones;var posed=new Vector3[v.Length];float maxError=0;
   for(int i=0;i<v.Length;i++){var ww=w[i];posed[i]=(bones[ww.boneIndex0].localToWorldMatrix*b[ww.boneIndex0]).MultiplyPoint3x4(v[i])*ww.weight0+(bones[ww.boneIndex1].localToWorldMatrix*b[ww.boneIndex1]).MultiplyPoint3x4(v[i])*ww.weight1+(bones[ww.boneIndex2].localToWorldMatrix*b[ww.boneIndex2]).MultiplyPoint3x4(v[i])*ww.weight2+(bones[ww.boneIndex3].localToWorldMatrix*b[ww.boneIndex3]).MultiplyPoint3x4(v[i])*ww.weight3;maxError=Mathf.Max(maxError,Vector3.Distance(posed[i],r.transform.TransformPoint(bakedVertices[i])));}
   File.WriteAllText(path+".txt","bake/manual max difference "+maxError+" scale="+r.transform.lossyScale+" position="+r.transform.position+" manualCentre="+posed.Aggregate(Vector3.zero,(a,p)=>a+p)/posed.Length);
using(var writer=new BinaryWriter(File.Create(path))) {writer.Write(m.vertexCount);foreach(var p in posed){writer.Write(p.x);writer.Write(p.y);writer.Write(p.z);}}Object.DestroyImmediate(m);
  }
  [Serializable]class ClipRecord {public string name,file;public int frames;public float length;}
  [Serializable]class ClipInventory {public ClipRecord[] clips;}
  public static void DumpPoseBank() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("GOLF_RUNTIME_BANK_OUT");Directory.CreateDirectory(output);
   var inventory=JsonUtility.FromJson<ClipInventory>(File.ReadAllText(Environment.GetEnvironmentVariable("GOLF_RUNTIME_BANK_INVENTORY")));
   typeof(HeroTurnaround).GetMethod("PurgeDeadCaches",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,null);
   var golfer=GolferView.CreatePlayer(null,new GolferView.Look{Hero=new HeroLook{Female=true,Haircut=0,Skin=new Color(.953f,.855f,.788f),HairColor=Color.black}});
   var look=golfer.GetComponentInChildren<MatchHeroLook>();var clips=Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(true));
   foreach(var record in inventory.clips) {
    var clip=clips.FirstOrDefault(c=>c.name==record.name);if(!clip)continue;
    bool swing=new[]{"Drive","IronSwing","HalfSwing","Chip","Putt"}.Contains(record.name);
    if(swing)golfer.SetClub(record.name=="Drive"?GolfClub.Driver:record.name=="IronSwing"?GolfClub.Iron:record.name=="Putt"?GolfClub.Putter:GolfClub.Wedge,record.name=="Chip");
    else {typeof(GolferView).GetField("clipName",Private).SetValue(golfer,record.name);typeof(GolferView).GetField("EndTime",Private).SetValue(golfer,record.length);Call(golfer,"Play",clip,0f);}
    typeof(GolferView).GetField("phase",Private).SetValue(golfer,swing?0:4);Call(golfer,"TickFade",1f);
    using(var writer=new BinaryWriter(File.Create(Path.Combine(output,"clip_"+record.file+"_bones.f32")))) {
     for(int frame=0;frame<record.frames;frame++) {
      Call(golfer,"Show",record.length*frame/(record.frames-1));
      var inverse=look.transform.worldToLocalMatrix;
      foreach(var bone in look.body.bones.Take(53)){var matrix=inverse*bone.localToWorldMatrix;for(int col=0;col<4;col++)for(int row=0;row<4;row++)writer.Write(matrix[row,col]);}
     }
    }
   }
   Object.DestroyImmediate(golfer.gameObject);
  }
  public static void RunTopOnly() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("GOLF_RUNTIME_REVIEW_OUT");Directory.CreateDirectory(output);
   typeof(HeroTurnaround).GetMethod("Studio",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,new object[]{true});
   var golfer=GolferView.CreatePlayer(null,new GolferView.Look{Hero=new HeroLook{Female=true,Haircut=0,Skin=new Color(.953f,.855f,.788f),HairColor=Color.black}});
   var l=golfer.GetComponentInChildren<MatchHeroLook>();captureRoot=l.gameObject;Call(l,"OwnMaterials");
   typeof(GolferView).GetField("poseSafety",Private).SetValue(golfer,new HeroPoseSafety(l));
   golfer.SetClub(GolfClub.Driver,false);Call(golfer,"TickFade",1f);l.SetKit("E87B65","23304B","FFFFFF");
   var c=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(x=>x.name=="TurnaroundCamera");c.aspect=1;c.fieldOfView=30;c.nearClipPlane=.01f;
   File.WriteAllLines(Path.Combine(output,"renderers.txt"),captureRoot.GetComponentsInChildren<Renderer>(true).Select(r=>r.name+" enabled="+r.enabled+" active="+r.gameObject.activeInHierarchy));
   foreach(float time in (Environment.GetEnvironmentVariable("GOLF_REVIEW_TIMES")??"0,1.2,2.3,2.7,3.3").Split(',').Select(x=>float.Parse(x,System.Globalization.CultureInfo.InvariantCulture))) {
    Call(golfer,"Show",time);Correct(l);foreach(var sleeve in l.GetComponentsInChildren<FemaleSleeveSweep>(true))sleeve.Apply();
    var center=l.transform.TransformPoint(new Vector3(0,1.3f,0));c.transform.position=center+l.transform.TransformDirection(new Vector3(.7f,0,2.6f));c.transform.LookAt(center,l.transform.up);
    Shot(c,Path.Combine(output,$"{time:F2}-kit.jpg"));
   }
   Object.DestroyImmediate(golfer.gameObject);
   typeof(HeroTurnaround).GetMethod("Release",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,null);
  }
  public static void Run() {
   EditorUtility.audioMasterMute=true;AudioListener.volume=0;
   string output=Environment.GetEnvironmentVariable("GOLF_RUNTIME_REVIEW_OUT");Directory.CreateDirectory(output);
   typeof(HeroTurnaround).GetMethod("Studio",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,new object[]{true});
   var golfer=GolferView.CreatePlayer(null,new GolferView.Look{Hero=new HeroLook{Female=true,Haircut=0,Skin=new Color(.953f,.855f,.788f),HairColor=Color.black}});
   var l=golfer.GetComponentInChildren<MatchHeroLook>();captureRoot=l.gameObject;Call(l,"OwnMaterials");
   typeof(GolferView).GetField("poseSafety",Private).SetValue(golfer,new HeroPoseSafety(l));
   string solve=Environment.GetEnvironmentVariable("GOLF_RUNTIME_SOLVE");
   if(solve=="grip") {typeof(GolferView).GetField("poseSafety",Private).SetValue(golfer,null);typeof(GolferView).GetField("swingClearance",Private).SetValue(golfer,null);}
   if(solve=="clearance")typeof(GolferView).GetField("poseSafety",Private).SetValue(golfer,null);
   golfer.SetClub(GolfClub.Driver,false);Call(golfer,"TickFade",1f);
   l.SetKit("E87B65","23304B","FFFFFF");
   if(Environment.GetEnvironmentVariable("GOLF_TOP_OUTER_ONLY")=="1") {
    var top=l.kit.First(r=>r&&r.name=="Kit_Top");var shell=Object.Instantiate(top.sharedMesh);
    byte[] indexBytes=File.ReadAllBytes(Environment.GetEnvironmentVariable("GOLF_TOP_OUTER_INDICES"));var indices=new int[indexBytes.Length/4];Buffer.BlockCopy(indexBytes,0,indices,0,indexBytes.Length);shell.triangles=indices;top.sharedMesh=shell;
   }

   var camera=Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).First(c=>c.name=="TurnaroundCamera");camera.aspect=1;camera.fieldOfView=30;camera.nearClipPlane=.01f;
   var original=l.body.sharedMesh;
   var rows=new System.Collections.Generic.List<string>();
   foreach(var renderer in l.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r=>r.enabled&&(r.name.Contains("Glove")||r.name=="Kit_Top")))for(int i=0;i<renderer.bones.Length;i++){
    int b=Array.IndexOf(l.body.bones,renderer.bones[i]);if(b<0)continue;
    var a=renderer.sharedMesh.bindposes[i].inverse;var bb=original.bindposes[b].inverse;
    rows.Add(renderer.name+" "+renderer.bones[i].name+" bind distance="+Vector3.Distance(a.GetColumn(3),bb.GetColumn(3))+" angle="+Quaternion.Angle(a.rotation,bb.rotation)+" scale="+a.lossyScale+" bodyScale="+bb.lossyScale);
   }
   File.WriteAllLines(Path.Combine(output,"bind-comparison.txt"),rows);
   if(Environment.GetEnvironmentVariable("GOLF_BODY_ORIGINAL_WEIGHTS")=="1") {
    var sourceBody=Resources.Load<GameObject>("Tennis/OriginalSeamBlinkFinish/Female").GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name=="Body");
    var weightsMesh=Object.Instantiate(original);weightsMesh.boneWeights=sourceBody.sharedMesh.boneWeights;l.body.sharedMesh=original=weightsMesh;
   }
var full=Object.Instantiate(original);var source=(Mesh)typeof(MatchHeroLook).GetField("kitV2CoverSource",Private).GetValue(l);full.triangles=source.triangles;
   foreach(float time in (Environment.GetEnvironmentVariable("GOLF_REVIEW_TIMES")??"0,.6,1.2,1.8,2.1,2.3,2.5,2.7,3,3.3").Split(',').Select(x=>float.Parse(x,System.Globalization.CultureInfo.InvariantCulture))) {
    if(solve=="raw")Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(true)).First(c=>c.name=="Drive").SampleAnimation(l.gameObject,time);else Call(golfer,"Show",time);Correct(l);
    if(Environment.GetEnvironmentVariable("GOLF_BODY_ORIGINAL_WEIGHTS")=="1")for(int i=0;i<original.blendShapeCount;i++)if(original.GetBlendShapeName(i).Contains("Shoulder")){l.body.SetBlendShapeWeight(i,0);}
var centre=l.transform.TransformPoint(new Vector3(0,1.3f,0));camera.transform.position=centre+l.transform.TransformDirection(new Vector3(.7f,0,2.6f));camera.transform.LookAt(centre,l.transform.up);
    var corr=l.GetComponent<KitV2PoseCorrectives>();var info=new {features=(float[])typeof(KitV2PoseCorrectives).GetField("features",Private).GetValue(corr),weights=(float[])typeof(KitV2PoseCorrectives).GetField("weights",Private).GetValue(corr)};
    string stem=Path.Combine(output,$"{time:F2}");File.WriteAllText(stem+"-features.json","{\"features\":["+string.Join(",",info.features)+"],\"weights\":["+string.Join(",",info.weights??new float[0])+"]}");
    if(Environment.GetEnvironmentVariable("GOLF_NO_TOP_POSE")=="1"){var shirt=l.kit.First(r=>r&&r.name=="Kit_Top");for(int i=0;i<shirt.sharedMesh.blendShapeCount;i++)shirt.SetBlendShapeWeight(i,0);}

    var wristRows=new System.Collections.Generic.List<string>();foreach(bool left in new[]{true,false}){var handBone=l.Bone(left?HumanBodyBones.LeftHand:HumanBodyBones.RightHand);var lower=l.Bone(left?HumanBodyBones.LeftLowerArm:HumanBodyBones.RightLowerArm);var mid=l.Bone(left?HumanBodyBones.LeftMiddleProximal:HumanBodyBones.RightMiddleProximal);wristRows.Add((left?"left":"right")+" wrist flex="+Vector3.Angle(handBone.position-lower.position,mid.position-handBone.position));}File.WriteAllLines(stem+"-wrists.txt",wristRows);
Shot(camera,stem+"-kit.jpg");Dump(l.kit.First(r=>r&&r.name=="Kit_Top"),stem+"-top.bin");
    var top=l.kit.First(r=>r&&r.name=="Kit_Top");top.enabled=false;l.body.sharedMesh=full;Shot(camera,stem+"-body.jpg");Dump(l.body,stem+"-body.bin");
    var hand=l.Bone(HumanBodyBones.LeftHand);var palm=l.Bone(HumanBodyBones.LeftMiddleProximal);var target=(hand.position+palm.position)*.5f;
    camera.transform.position=target+l.transform.TransformDirection(new Vector3(.15f,.12f,.65f));camera.transform.LookAt(target,l.transform.up);Shot(camera,stem+"-glove.jpg");
    foreach(var r in l.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r=>r.enabled&&r.name.Contains("Glove")))Dump(r,stem+"-"+r.name+".bin");
    File.WriteAllText(stem+"-bones.json","["+string.Join(",",l.body.bones.Take(53).Select(b=>"{\"name\":\""+b.name+"\",\"p\":["+b.position.x+","+b.position.y+","+b.position.z+"]}"))+"]");
    l.body.sharedMesh=original;top.enabled=true;
   }
   File.WriteAllText(Path.Combine(output,"renderers.txt"),string.Join("\n",l.GetComponentsInChildren<SkinnedMeshRenderer>(true).Select(r=>r.name+" enabled="+r.enabled+" bones="+r.bones.Length+" mesh="+r.sharedMesh.name)));
   Object.DestroyImmediate(golfer.gameObject);Object.DestroyImmediate(full);
   typeof(HeroTurnaround).GetMethod("Release",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,null);
  }
 }
}
#endif
