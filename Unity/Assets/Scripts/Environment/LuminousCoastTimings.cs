using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.EnvironmentArt
{
    /// Explicit device-review launch only. Records native frame timings without
    /// screenshots/readback in the measurement loop. Zero GPU values mean unavailable.
    public sealed class LuminousCoastTimings : MonoBehaviour
    {
        [Serializable] sealed class Row {
            public float elapsed, intervalMs; public double cpuMs,gpuMs,mainMs,renderMs;
            public ulong timestamp; public int width,height,target,msaa,shadowResolution,shadowCascades,qualityReductions;
            public float renderScale; public string scene;
        }
        [Serializable] sealed class Report {
            public string device,unity,graphics,startedUtc;
            public bool hardwareGpuSamplesAvailable; public List<Row> samples;
        }
        readonly FrameTiming[] timing=new FrameTiming[1];
        readonly List<Row> rows=new(12000);
        float elapsed; string start,path;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Install() {
            if(Application.isEditor || Environment.GetEnvironmentVariable("LUMINOUS_BENCH_TIMINGS")!="1")return;
            var go=new GameObject("Luminous Coast device timings");DontDestroyOnLoad(go);go.AddComponent<LuminousCoastTimings>();
        }
        void Awake() {
            start=DateTime.UtcNow.ToString("o");
            string directory=Path.Combine(Application.persistentDataPath,"luminous-coast");Directory.CreateDirectory(directory);
            path=Path.Combine(directory,"timings-"+DateTime.UtcNow.ToString("yyyyMMdd-HHmmss")+".json");
        }
        void LateUpdate() {
            elapsed+=Time.unscaledDeltaTime;
            if(elapsed>150) {enabled=false;Save();return;}
            FrameTimingManager.CaptureFrameTimings();
            uint count=FrameTimingManager.GetLatestTimings(1,timing);
            var t=count>0?timing[0]:default;
            var pipeline=GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            rows.Add(new Row {elapsed=elapsed,intervalMs=Time.unscaledDeltaTime*1000,
                cpuMs=t.cpuFrameTime,gpuMs=t.gpuFrameTime,mainMs=t.cpuMainThreadFrameTime,
                renderMs=t.cpuRenderThreadFrameTime,timestamp=t.frameStartTimestamp,
                width=Screen.width,height=Screen.height,target=Application.targetFrameRate,
                renderScale=pipeline?pipeline.renderScale:1,msaa=pipeline?pipeline.msaaSampleCount:QualitySettings.antiAliasing,
                shadowResolution=pipeline?pipeline.mainLightShadowmapResolution:0,shadowCascades=pipeline?pipeline.shadowCascadeCount:0,
                qualityReductions=GolfArcade.Tennis.TennisQuality.Reductions,scene=SceneManager.GetActiveScene().name});
            // Persist after the active 120-second benchmark window, avoiding
            // large JSON serialization/write spikes inside that window.
        }
        void Save() {
            var report=new Report {device=SystemInfo.deviceModel,unity=Application.unityVersion,
                graphics=SystemInfo.graphicsDeviceType.ToString(),startedUtc=start,
                hardwareGpuSamplesAvailable=rows.Exists(r=>r.gpuMs>0),samples=rows};
            File.WriteAllText(path,JsonUtility.ToJson(report));
        }
        void OnApplicationPause(bool paused) {if(paused && path!=null)Save();}
        void OnDestroy() {if(path!=null)Save();}
    }
}
