#if UNITY_IOS && !UNITY_EDITOR
// Measurement-only player component copied into the isolated build, never installed in shared source.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using GolfArcade.Tennis;
public class ClothDeviceProfile : MonoBehaviour {
 [Serializable] class Frame {public double cpuMs,gpuMs,cpuMainThreadMs,cpuRenderThreadMs,presentWaitMs;public float elapsedMs;}
 [Serializable] class Report {public string device,gpu,os,variant;public int heroes;public Frame[] frames;}
 [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)] static void Boot(){var go=new GameObject("ClothDeviceProfile");DontDestroyOnLoad(go);go.AddComponent<ClothDeviceProfile>();}
 IEnumerator Start() {
  TennisGame g=null;while(!(g=FindFirstObjectByType<TennisGame>())||!g.Initialized)yield return null;
  yield return new WaitForSeconds(8);
  g.SelectCharacter(false);
  yield return new WaitForSeconds(3);
  var presentation=g.GetComponent<TennisPresentation>();if(presentation)presentation.Finish();
  foreach(var b in FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))if(b is TennisGame||b is TennisActor||b is HeroTennisDriver||b.GetType().Name.Contains("Camera"))b.enabled=false;
  var drivers=FindObjectsByType<HeroTennisDriver>(FindObjectsSortMode.None);foreach(var d in drivers){d.enabled=false;var a=d.GetComponent<Animator>();if(a)a.enabled=false;}
  var cam=g.GameplayCamera?g.GameplayCamera:Camera.main;var root=g.Player.GetComponentInChildren<HeroTennisDriver>().transform;
  var from=root.position+new Vector3(0,5.8f,-5.8f);var target=root.position+new Vector3(0,.95f,7.2f);cam.transform.SetPositionAndRotation(from,Quaternion.LookRotation(target-from));cam.fieldOfView=54;
  var rows=new List<Frame>();var timing=new FrameTiming[4];
  for(int i=0;i<720;i++){
   foreach(var d in drivers){var s=d.slots.First(x=>x.id==HeroTennisDriver.Clip.Ready);s.clip.SampleAnimation(d.gameObject,(i/60f)%s.clip.length);}
   FrameTimingManager.CaptureFrameTimings();yield return new WaitForEndOfFrame();
   if(i>=180&&FrameTimingManager.GetLatestTimings(1,timing)>0)rows.Add(new Frame{cpuMs=timing[0].cpuFrameTime,gpuMs=timing[0].gpuFrameTime,cpuMainThreadMs=timing[0].cpuMainThreadFrameTime,cpuRenderThreadMs=timing[0].cpuRenderThreadFrameTime,presentWaitMs=timing[0].cpuMainThreadPresentWaitTime,elapsedMs=Time.unscaledDeltaTime*1000});
  }
  var r=new Report{device=SystemInfo.deviceModel,gpu=SystemInfo.graphicsDeviceName,os=SystemInfo.operatingSystem,variant=Application.version,heroes=drivers.Length,frames=rows.ToArray()};
  var path=Path.Combine(Application.persistentDataPath,"cloth_device_profile.json");File.WriteAllText(path,JsonUtility.ToJson(r,true));Debug.Log("CLOTH_PROFILE_COMPLETE "+path+" samples="+rows.Count+" heroes="+drivers.Length);
  enabled=false;
 }
}

#endif
