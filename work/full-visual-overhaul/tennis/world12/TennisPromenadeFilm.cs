#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad] public static class TennisPromenadeFilm
    {
        const string Flag="TennisPromenadeFilm";static IEnumerator script;
        static TennisPromenadeFilm(){EditorApplication.update+=Tick;}
        public static void Run(){TennisVenue.Selected=TennisVenueKind.Resort;EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");SessionState.SetBool(Flag,true);EditorApplication.isPlaying=true;}
        static void Tick(){if(!SessionState.GetBool(Flag,false)||!EditorApplication.isPlaying)return;var g=Object.FindFirstObjectByType<TennisGame>();if(!g||!g.Initialized)return;if(script==null)script=Go(g);try{if(!script.MoveNext())Done(0);}catch(Exception e){Debug.LogException(e);Done(1);}}
        static void Done(int code){SessionState.SetBool(Flag,false);Time.captureFramerate=0;if(Application.isBatchMode)EditorApplication.Exit(code);else EditorApplication.isPlaying=false;}
        static Transform Part(Transform root,string prefix){foreach(var t in root.GetComponentsInChildren<Transform>())if(t.name.StartsWith(prefix,StringComparison.Ordinal))return t;return null;}
        static string P(Vector3 p)=>$"{p.x:F5};{p.y:F5};{p.z:F5}";
        static void Shot(Camera cam,string file,Transform actor)
        {
            var pos=cam.transform.position;var rot=cam.transform.rotation;var fov=cam.fieldOfView;
            var from=actor.TransformPoint(2.4f,1.35f,3.0f);var at=actor.TransformPoint(0,.88f,0);cam.transform.SetPositionAndRotation(from,Quaternion.LookRotation(at-from));cam.fieldOfView=37;
            var rt=RenderTexture.GetTemporary(640,640,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Default,4);var old=cam.targetTexture;var active=RenderTexture.active;cam.targetTexture=rt;cam.Render();cam.targetTexture=old;RenderTexture.active=rt;
            var tex=new Texture2D(640,640,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,640,640),0,0);tex.Apply();File.WriteAllBytes(file,tex.EncodeToPNG());Object.DestroyImmediate(tex);RenderTexture.active=active;RenderTexture.ReleaseTemporary(rt);cam.transform.SetPositionAndRotation(pos,rot);cam.fieldOfView=fov;
        }
        static IEnumerator Go(TennisGame game)
        {
            var output=Path.GetFullPath(Environment.GetEnvironmentVariable("TWALK_OUT")??"../proof/full-visual-overhaul/tennis-promenade-film");Directory.CreateDirectory(output);Time.captureFramerate=60;
            var presentation=game.GetComponent<TennisPresentation>();if(presentation)presentation.Finish();
            typeof(TennisGame).GetProperty("Flow").GetSetMethod(true).Invoke(game,new object[]{TennisGame.Phase.PointOver});typeof(TennisGame).GetField("resetTimer",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(game,1e6f);
            int start=Time.frameCount;while(Time.frameCount-start<8)yield return null;
            var inventory=TennisNpcInventory.Save(output);if(inventory.status!="PASS")throw new InvalidOperationException("Promenade production inventory failed");
            var actors=new Transform[6];for(int i=0;i<6;i++){actors[i]=GameObject.Find("Premium promenade visitor "+i)?.transform;if(!actors[i])throw new InvalidOperationException("Visitor "+i+" missing");Shot(game.GameplayCamera,Path.Combine(output,"visitor_"+i+"_standing.png"),actors[i]);}
            var trace=new List<string>{"frame,visitor,actor,leftAnkle,rightAnkle,leftKnee,rightKnee"};
            // Visitor2's deterministic natural path phase reaches the short end dwell
            // and turn in this interval. No root/pose/clock is set by the fixture.
            for(int frame=0;frame<480;frame++)
            {
                int before=Time.frameCount;do{yield return null;}while(Time.frameCount==before);
                for(int i=0;i<6;i++)trace.Add($"{frame},{i},{P(actors[i].position)},{P(Part(actors[i],"FOOT_L").position)},{P(Part(actors[i],"FOOT_R").position)},{P(Part(actors[i],"SHIN_L").position)},{P(Part(actors[i],"SHIN_R").position)}");
                if(frame%2==0){string id=(frame/2).ToString("00000");GameCapture.Save(Path.Combine(output,"game_"+id+".png"),960,540);Shot(game.GameplayCamera,Path.Combine(output,"visitor_"+id+".png"),actors[2]);}
            }
            File.WriteAllLines(Path.Combine(output,"trace.csv"),trace);File.WriteAllText(Path.Combine(output,"audit.txt"),"Actual six independent fitted rigid visitors; natural walk/end-dwell/turn phase,60fps evaluated and30fps captured. No actor/pose/clock override. Stance and source2 visual identity still require real image/sequence review.\n");
        }
    }
}
#endif
