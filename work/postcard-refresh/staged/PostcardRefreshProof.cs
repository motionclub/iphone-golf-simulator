#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Unity.Profiling;
using GolfArcade.Game;
using GolfArcade.Course;
using GolfArcade.Tennis;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class PostcardRefreshProof
    {
        const string Key="PostcardRefreshProof";
        static PostcardRefreshProof(){EditorApplication.update+=Tick;}
        public static void Run(){SessionState.SetBool(Key,true);EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");EditorApplication.isPlaying=true;}
        static void Tick(){if(!SessionState.GetBool(Key,false)||!EditorApplication.isPlaying)return;SessionState.SetBool(Key,false);new GameObject("Postcard refresh proof").AddComponent<PostcardRefreshProofRunner>();}
    }
    public sealed class PostcardRefreshProofRunner:MonoBehaviour
    {
        [Serializable] public sealed class Row
        {
            public int hole,drawCalls,triangles,instancedPlantDraws,instancedPlants,grassCells,volumes;
            public bool hdr,post,rendererResources,aces,bloom,physicsExact;
            public float fogStart,fill,heroFill;public string gate;
        }
        [Serializable] public sealed class Report {public string scope="Metal Editor, actual gameplay camera with HUD and minimap, completed automatic frames; no phone FPS claim.";public string gate="PASS";public List<Row> holes=new();}
        readonly Report report=new();
        readonly int[] holes={9,10,12,16,17,18,21,22,23};
        GolfGame game;CameraRig rig;Camera cam;int index=-1,warm,frame;bool placed;
        ProfilerRecorder draws,triangles;int peakDraw,peakTriangles;string output;
        void Start(){output=Environment.GetEnvironmentVariable("POSTCARD_REFRESH_PROOF_OUT");if(string.IsNullOrEmpty(output))throw new Exception("POSTCARD_REFRESH_PROOF_OUT required");Directory.CreateDirectory(output);draws=ProfilerRecorder.StartNew(ProfilerCategory.Render,"Draw Calls Count",32);triangles=ProfilerRecorder.StartNew(ProfilerCategory.Render,"Triangles Count",32);}
        void Update()
        {
            try{
                if(!game){if(++warm<35||!HoleView.Current)return;game=FindFirstObjectByType<GolfGame>();rig=FindFirstObjectByType<CameraRig>();cam=rig.Camera;game.Play();Next();return;}
                int elapsed=Time.frameCount-frame;
                if(!placed){if(elapsed<12)return;game.DropBall(game.CurrentHole.Tee);rig.FrameAddress(game.BallPosition,new Vector3((float)(game.CurrentHole.Pin.X-game.CurrentHole.Tee.X),0,(float)(game.CurrentHole.Pin.D-game.CurrentHole.Tee.D)).normalized,false);rig.SnapNext();rig.ApplyFrame();rig.enabled=false;game.enabled=false;placed=true;frame=Time.frameCount;return;}
                if(elapsed<6)return;
                peakDraw=Mathf.Max(peakDraw,(int)draws.LastValue);peakTriangles=Mathf.Max(peakTriangles,(int)triangles.LastValue);
                if(elapsed<12)return;
                var renderer=Resources.Load<UniversalRendererData>("Tennis/Rendering/TennisURP_Renderer");var owner=cam.GetComponent<SportsPostProcessing>();var volume=owner?owner.Volume:null;
                bool aces=volume&&volume.profile.TryGet(out Tonemapping tone)&&tone.active&&tone.mode.value==TonemappingMode.ACES;
                bool bloom=volume&&volume.profile.TryGet(out Bloom glow)&&glow.active&&glow.intensity.value>0;
                var turf=HoleView.Current.GetComponentInChildren<GolfCoastalTurf>();
                var row=new Row{hole=holes[index],drawCalls=peakDraw,triangles=peakTriangles,hdr=cam.allowHDR,post=cam.GetUniversalAdditionalCameraData().renderPostProcessing,rendererResources=renderer&&renderer.postProcessData,
                    aces=aces,bloom=bloom,fogStart=RenderSettings.fogStartDistance,heroFill=Shader.GetGlobalFloat("_HeroPresentationFill"),grassCells=turf?turf.CellCount:0,volumes=cam.GetComponentsInChildren<Volume>().Length};
                foreach(var cluster in HoleView.Current.GetComponentsInChildren<GolfBotanicalInstances>()){row.instancedPlantDraws+=cluster.LastDrawCalls;row.instancedPlants+=cluster.LastInstances;}
                // Captured by the existing before/after dressing witness at the model boundary.
                row.physicsExact=GolfVisualPhysicsGate.Reports.TryGetValue(row.hole,out var physics)&&physics.gate=="PASS";
                if(physics!=null) File.WriteAllText(Path.Combine(output,$"hole{row.hole:00}-physics.json"),JsonUtility.ToJson(physics,true));
                row.gate=draws.Valid&&peakDraw>0&&peakDraw<=250&&row.hdr&&row.post&&row.rendererResources&&aces&&bloom&&row.volumes==1&&row.fogStart<=150&&row.grassCells>0&&row.physicsExact?"PASS":"FAIL";
                if(row.gate=="FAIL")report.gate="FAIL";report.holes.Add(row);
                File.WriteAllText(Path.Combine(output,"render-gates.json"),JsonUtility.ToJson(report,true));
                Debug.Log($"[PostcardRefreshProof] hole {row.hole} {row.gate}: {row.drawCalls} draws, {row.triangles} triangles, post={row.post}, turf={row.grassCells}");Next();
            }catch(Exception e){Debug.LogException(e);File.WriteAllText(Path.Combine(output,"error.txt"),e.ToString());EditorApplication.Exit(1);}
        }
        void Next(){if(++index==holes.Length){EditorApplication.Exit(report.gate=="PASS"?0:1);return;}game.enabled=true;rig.enabled=true;game.JumpToHole(holes[index]);frame=Time.frameCount;placed=false;peakDraw=peakTriangles=0;}
        void OnDestroy(){draws.Dispose();triangles.Dispose();}
    }
}
#endif
