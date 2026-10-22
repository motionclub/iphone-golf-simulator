// Diagnostic player only. Never installed in shared runtime source.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using Unity.Profiling;
using GolfArcade.Course;
using GolfArcade.Game;
public sealed class GolfDeviceProfile:MonoBehaviour
{
 [Serializable] class Frame {public double cpuMs,gpuMs,cpuMainThreadMs,cpuRenderThreadMs,presentWaitMs;public float elapsedMs;public long drawCalls,triangles,batches;}
 [Serializable] class HoleReport {public int hole;public string camera;public Frame[] frames;}
 [Serializable] class Report {public string device,gpu,os,variant;public int width,height;public bool drawsValid,trianglesValid,batchesValid;public HoleReport[] holes;}
 [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)] static void Boot(){var g=new GameObject("Golf 30b device proof");DontDestroyOnLoad(g);g.AddComponent<GolfDeviceProfile>();}
 IEnumerator Start()
 {
  GolfGame game=null;while(!(game=FindFirstObjectByType<GolfGame>())||!HoleView.Current)yield return null;
  yield return new WaitForSeconds(8);
  var rig=FindFirstObjectByType<CameraRig>();var cam=game.GameplayCamera;
  game.enabled=false;rig.enabled=false;
  foreach(var c in FindObjectsByType<Canvas>(FindObjectsSortMode.None))c.enabled=false;
  var v4=FindObjectsByType<GolferView>(FindObjectsInactive.Include,FindObjectsSortMode.None).First();
  Destroy(HoleView.Current.gameObject);yield return null;
  using var draws=ProfilerRecorder.StartNew(ProfilerCategory.Render,"Draw Calls Count");
  using var tris=ProfilerRecorder.StartNew(ProfilerCategory.Render,"Triangles Count");
  using var batches=ProfilerRecorder.StartNew(ProfilerCategory.Render,"Batches Count");
  var results=new List<HoleReport>();var timing=new FrameTiming[4];
  var root=new GameObject("30b measured course");var sun=RenderSettings.sun;
  var holes=new[]{GolfArcade.Course.Course.Cliffside().Holes.First(h=>h.Number==7)}.Concat(GolfArcade.Course.Course.Postcards().Holes).ToArray();
  foreach(var hole in holes)
  {
   var view=HoleView.Build(hole,root.transform);GolfAtmosphere.Apply(sun,cam,hole.Number);
   var ball=HoleView.ToWorld(hole.Tee,.06);var heading=HoleView.ToWorld(hole.Pin)-HoleView.ToWorld(hole.Tee);heading.y=0;heading.Normalize();
   v4.gameObject.SetActive(true);v4.Stand(ball,heading);v4.ShowLoad(0);
   rig.FrameAddress(ball,heading,false);rig.SnapNext();rig.ApplyFrame();
   foreach(string camera in new[]{"gameplay","aerial"})
   {
    if(camera=="aerial"){
     Vector3 from,target;float fov=57;
     if(hole.Number==8){from=new Vector3(100,135,-55);target=new Vector3(2,6,185);}
     else if(hole.Number==9){from=new Vector3(120,185,-65);target=new Vector3(-22,6,230);}
     else if(hole.Number==10){from=new Vector3(-95,175,-105);target=new Vector3(145,6,125);fov=58;}
     else {target=(HoleView.ToWorld(hole.Tee)+HoleView.ToWorld(hole.Pin))*.5f;from=target+Vector3.up*180-heading*210+Vector3.right*90;fov=48;}
     cam.transform.SetPositionAndRotation(from,Quaternion.LookRotation(target-from));cam.fieldOfView=fov;
    }
    var frames=new List<Frame>();
    for(int i=0;i<540;i++){
     GolfWindSway.FreezeTime=i/60f;GolfWindSway.Push();
     FrameTimingManager.CaptureFrameTimings();yield return new WaitForEndOfFrame();
     if(i>=180&&FrameTimingManager.GetLatestTimings(1,timing)>0)frames.Add(new Frame{cpuMs=timing[0].cpuFrameTime,gpuMs=timing[0].gpuFrameTime,cpuMainThreadMs=timing[0].cpuMainThreadFrameTime,cpuRenderThreadMs=timing[0].cpuRenderThreadFrameTime,presentWaitMs=timing[0].cpuMainThreadPresentWaitTime,elapsedMs=Time.unscaledDeltaTime*1000,drawCalls=draws.Valid?draws.LastValue:-1,triangles=tris.Valid?tris.LastValue:-1,batches=batches.Valid?batches.LastValue:-1});
    }
    results.Add(new HoleReport{hole=hole.Number,camera=camera,frames=frames.ToArray()});
    Save(results,draws.Valid,tris.Valid,batches.Valid);
    Debug.Log("GOLF_PROFILE_HOLE "+hole.Number+" "+camera+" samples="+frames.Count);
   }
   Destroy(view.gameObject);yield return null;
  }
  GolfWindSway.FreezeTime=null;Debug.Log("GOLF_PROFILE_COMPLETE "+Application.persistentDataPath);enabled=false;
 }
 static void Save(List<HoleReport> holes,bool draws,bool tris,bool batches)
 {
  var r=new Report{device=SystemInfo.deviceModel,gpu=SystemInfo.graphicsDeviceName,os=SystemInfo.operatingSystem,variant=Application.version,width=Screen.width,height=Screen.height,drawsValid=draws,trianglesValid=tris,batchesValid=batches,holes=holes.ToArray()};
  File.WriteAllText(Path.Combine(Application.persistentDataPath,"golf_device_profile.json"),JsonUtility.ToJson(r,true));
 }
}
