#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    // Live, muted game capture. No camera transform, animation clip or asset edits.
    [InitializeOnLoad]
    public static class FemaleAliveCapture
    {
        const string Flag = "FemaleAliveCapture";
        static IEnumerator run; static int frame = -1;
        static string Output => Environment.GetEnvironmentVariable("ALIVE_OUT");
        static FemaleAliveCapture() { EditorApplication.update += Tick; }
        public static void Run()
        {
            SessionState.SetBool(Flag,true);
            EditorSceneManager.OpenScene("Assets/Scenes/" + (Environment.GetEnvironmentVariable("ALIVE_MODE")=="golf" ? "Golf" : "Tennis") + ".unity");
            EditorApplication.isPlaying=true;
        }
        static void Tick()
        {
            if(!SessionState.GetBool(Flag,false)||!EditorApplication.isPlaying||frame==Time.frameCount)return;
            frame=Time.frameCount;
            try {
                if(run==null) {
                    if(Environment.GetEnvironmentVariable("ALIVE_MODE")=="golf") {
                        var g=Object.FindFirstObjectByType<GolfGame>(); if(!g||!GolfArcade.Course.HoleView.Current)return;
                        run=Golf(g);
                    } else {
                        var g=Object.FindFirstObjectByType<TennisGame>(); if(!g||!g.Initialized)return;
                        run=Tennis(g);
                    }
                }
                if(!run.MoveNext()) {SessionState.SetBool(Flag,false);Time.captureFramerate=0;EditorApplication.Exit(0);}
            } catch(Exception e) {Debug.LogException(e);SessionState.SetBool(Flag,false);EditorApplication.Exit(1);}
        }
        static void Hold(TennisGame g)
        {
            typeof(TennisGame).GetProperty("Flow").GetSetMethod(true).Invoke(g,new object[]{TennisGame.Phase.PointOver});
            typeof(TennisGame).GetField("resetTimer",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(g,100000f);
        }
        static void Detail(MatchHeroLook look, string path)
        {
            var camera = new GameObject("Alive diagnostic camera").AddComponent<Camera>();
            camera.CopyFrom(Camera.main);camera.enabled=false;camera.tag="Untagged";
            var root=look.transform;var head=look.Bone(HumanBodyBones.Head);
            var at=head.position-root.up*.24f;
            camera.transform.position=at+root.forward*2.3f+root.right*.65f;
            camera.transform.LookAt(at,root.up);camera.fieldOfView=38;camera.aspect=1;
            var rt=RenderTexture.GetTemporary(640,640,24);var prev=RenderTexture.active;
            camera.targetTexture=rt;camera.Render();RenderTexture.active=rt;
            var tex=new Texture2D(640,640,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,640,640),0,0);tex.Apply();
            File.WriteAllBytes(path,tex.EncodeToJPG(92));RenderTexture.active=prev;
            camera.targetTexture=null;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(tex);Object.DestroyImmediate(camera.gameObject);
        }
        static IEnumerator Tennis(TennisGame g)
        {
            Time.captureFramerate=60; UnityEngine.Random.InitState(3108);
            using var profiler=Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Scripts,"FemaleHeroAlive.Tick",1);
            long maxCpu=0,totalCpu=0;int cpuSamples=0;
            g.AutoPlay=false;g.NativeControlled=true;g.SetControllerSetup(false);
            g.GetComponent<TennisPresentation>()?.Finish();g.SelectCharacter(true);
            g.GetComponent<TennisPresentation>()?.Finish();Hold(g);
            for(int i=0;i<120;i++)yield return null;
            var driver=g.Player.GetComponentInChildren<HeroTennisDriver>();
            if(!driver.matchLook.female)throw new Exception("Not female");
            Directory.CreateDirectory(Output);
            using(var info=new StreamWriter(Path.Combine(Output,"mesh-info.txt")))
            foreach(var r in driver.matchLook.GetComponentsInChildren<SkinnedMeshRenderer>()) {
                info.WriteLine(r.name+" | "+r.sharedMesh.name+" | "+r.sharedMesh.vertexCount+" | "+r.sharedMesh.bounds);
                for(int b=0;b<r.sharedMesh.blendShapeCount;b++)info.WriteLine("  "+r.sharedMesh.GetBlendShapeName(b));
            }
            var modes=new[]{"idle","wave","joy","slump"};
            var clips=new[]{HeroTennisDriver.Clip.Ready,HeroTennisDriver.Clip.IntroWave,HeroTennisDriver.Clip.EmoteJumpJoy,HeroTennisDriver.Clip.EmoteSlump};
            for(int m=0;m<modes.Length;m++) {
                Hold(g);string dir=Path.Combine(Output,modes[m]);Directory.CreateDirectory(dir);
                if(m>0&&!driver.PlayEmote(clips[m]))throw new Exception("Emote failed: "+modes[m]);
                using(var trace=new StreamWriter(Path.Combine(dir,"trace.csv"))) {
                    trace.WriteLine("frame,seconds,clip,clipTime,headX,headY,headZ,aliveIdle,cloth,blink,smile");
                    for(int i=0;i<(m==0?240:m==3?270:240);i++) {
                        yield return null;
                        if(profiler.Valid && profiler.LastValue>0){maxCpu=Math.Max(maxCpu,profiler.LastValue);totalCpu+=profiler.LastValue;cpuSamples++;}
                        if(i%2==1) {
                            GameCapture.Save(Path.Combine(dir,$"f_{i/2:D5}.jpg"),1280,720);
                            if(Environment.GetEnvironmentVariable("ALIVE_DETAIL")=="1") Detail(driver.matchLook,Path.Combine(dir,$"detail_{i/2:D5}.jpg"));
                            var h=driver.matchLook.Bone(HumanBodyBones.Head).position;
                            var alive=driver.matchLook.GetComponent<FemaleHeroAlive>();
                            var body=driver.matchLook.body;var bi=body.sharedMesh.GetBlendShapeIndex("Hero_Blink");var si=body.sharedMesh.GetBlendShapeIndex("Face_Smile");
                            float blink=bi<0?0:body.GetBlendShapeWeight(bi),smile=si<0?0:body.GetBlendShapeWeight(si);
                            trace.WriteLine(FormattableString.Invariant($"{i/2},{(i+1)/60f:F4},{driver.PlayingClip},{driver.PlayingClipTime:F4},{h.x:F5},{h.y:F5},{h.z:F5},{(alive?alive.IdleWeight:0):F4},{(alive?alive.ClothWeight:0):F4},{blink:F4},{smile:F4}"));
                        }
                    }
                }
            }
            File.WriteAllText(Path.Combine(Output,"cpu.txt"),$"Editor CPU marker only; not a phone GPU/frame-rate measurement. samples={cpuSamples} meanMs={(cpuSamples>0?totalCpu/(double)cpuSamples/1000000:0):F6} maxMs={maxCpu/1000000.0:F6}\n");
            var live=driver.matchLook.GetComponent<FemaleHeroAlive>();
            if(live&&live.IdleWeight<.9f)throw new Exception("Female idle did not resume after emotes");
        }
        static IEnumerator Golf(GolfGame g)
        {
            // Reuse the shot recorder, then select a temporary female look after its Play reset.
            var recorder=new GameObject("Female alive golf film").AddComponent<CurrentGolfSwingRecorder>();recorder.Begin(g);
            GolferStyle.Wear(GolferStyle.Current);GolferStyle.Body=GolferStyle.BodyKind.Female;
            Object.FindFirstObjectByType<GolferView>().ApplyStyle();
            while(true)yield return null;
        }
    }
}
#endif
