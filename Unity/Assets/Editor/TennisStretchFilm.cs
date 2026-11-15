#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    /// STRETCH REACH 2026-11-13 (it replaced the dive, whose code-bent pose warped the hero): one real rally per hero that opens
    /// with a fast wide ball from a rival at the net, out of easy reach, then plays on (AutoPlay against the CPU). Evaluated at
    /// 60 fps, recorded at 30 fps: the gameplay camera and a side view of the player. TSF_OUT sets the folder.
    [InitializeOnLoad] public static class TennisStretchFilm
    {
        const string Flag="TennisStretchFilm";static IEnumerator script;static int lastFrame=-1;
        static TennisStretchFilm(){EditorApplication.update+=Tick;}
        public static void Run(){script=null;lastFrame=-1;EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");SessionState.SetBool(Flag,true);EditorApplication.isPlaying=true;}
        static void Tick()
        {
            if(!SessionState.GetBool(Flag,false)||!EditorApplication.isPlaying||lastFrame==Time.frameCount)return;lastFrame=Time.frameCount;
            var game=Object.FindFirstObjectByType<TennisGame>();if(!game||!game.Initialized)return;
            if(script==null)script=Go(game);
            try{if(!script.MoveNext())Done(0);}catch(Exception e){Debug.LogException(e);Done(1);}
        }
        static void Done(int code){SessionState.SetBool(Flag,false);Time.captureFramerate=0;if(Application.isBatchMode)EditorApplication.Exit(code);else EditorApplication.isPlaying=false;}
        static void Shot(Camera camera,string path,Vector3 at)
        {
            var oldPosition=camera.transform.position;var oldRotation=camera.transform.rotation;float oldFov=camera.fieldOfView;
            // a close camera in front of the player, following them, so the body at full stretch can be judged
            var position=new Vector3(at.x+.6f,1.15f,at.z+3.1f);var target=new Vector3(at.x,.8f,at.z);
            camera.transform.SetPositionAndRotation(position,Quaternion.LookRotation(target-position));camera.fieldOfView=42;
            var rt=RenderTexture.GetTemporary(960,540,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Default,4);
            var oldTarget=camera.targetTexture;var oldActive=RenderTexture.active;camera.targetTexture=rt;camera.Render();camera.targetTexture=oldTarget;RenderTexture.active=rt;
            var image=new Texture2D(960,540,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,960,540),0,0);image.Apply();File.WriteAllBytes(path,image.EncodeToPNG());Object.DestroyImmediate(image);
            RenderTexture.active=oldActive;RenderTexture.ReleaseTemporary(rt);camera.transform.SetPositionAndRotation(oldPosition,oldRotation);camera.fieldOfView=oldFov;
        }
        static IEnumerator Go(TennisGame game)
        {
            string directory=Path.GetFullPath(Environment.GetEnvironmentVariable("TSF_OUT")??"../proof/remove-dive");Directory.CreateDirectory(directory);Time.captureFramerate=60;
            var audit=new List<string>{"Real rally: injected wide ball from a rival at the net, AutoPlay swings (real StartRallySwing -> BeginStretch), then the rally plays on against the CPU."};
            var presentation=game.GetComponent<TennisPresentation>();
            foreach(bool female in new[]{false,true})
            {
                int side=female?-1:1;
                game.SelectCharacter(female);string rival=female?"Viktor":"Nadia";game.ConfigureMatch(TennisGame.Mode.Campaign,rival,rival,"STRETCH PROOF");if(presentation)presentation.Finish();
                game.AutoPlay=false;TennisGame.AutoPlayTimingJitter=0;
                for(int n=0;n<35;n++)yield return null;
                game.PrepareLesson();for(int n=0;n<12;n++)yield return null;
                var driver=game.Player.GetComponentInChildren<HeroTennisDriver>();foreach(var skin in driver.GetComponentsInChildren<SkinnedMeshRenderer>(true))skin.updateWhenOffscreen=true;
                string path=Path.Combine(directory,female?"female":"male");Directory.CreateDirectory(path);
                var trace=new List<string>{"frame,flow,stretchActive,stretches,returns,clip,clipTime,ttc,actorX,actorZ,heroRollDeg,ballX,ballY,ballZ"};
                int stretches0=game.Stretches,returns0=game.Returns,injected=-1,stretchFrame=-1,returnFrame=-1;float maxRoll=0;Vector3 lungeFrom=Vector3.zero;float lungeTo=0;
                for(int frame=0;frame<420;frame++)
                {
                    if(frame==20)
                    {
                        // the rival at the net cuts a hard volley wide of the player: too quick for the run to get all the way there
                        var p=game.Player.transform.position;
                        game.Opponent.transform.position=new Vector3(p.x+side*.2f,game.Opponent.transform.position.y,1.7f);
                        // TSF_BALL=low: a ball that bounces and arrives at about 0.5 m (the low pick-up clip); default: waist high, no bounce
                        bool low=Environment.GetEnvironmentVariable("TSF_BALL")=="low";
                        var from=new Vector3(p.x+side*.5f,1.05f,.9f);float vz=-23f,t=(from.z-(p.z+.6f))/-vz;
                        game.InjectBall(from,new Vector3(side*(low?2.2f:1.85f)/t,low?-1.8f:(1.0f-1.05f+4.905f*t*t)/t,vz));
                        game.Opponent.Swing(.6f,side<0,TennisActor.Stroke.Volley);
                        game.AutoPlay=true;injected=frame;lungeFrom=p;
                    }
                    yield return null;
                    if(stretchFrame<0&&game.StretchActive)stretchFrame=frame;
                    if(stretchFrame>=0&&!game.StretchActive&&lungeTo==0)lungeTo=game.Player.transform.position.x-lungeFrom.x;
                    if(returnFrame<0&&game.Returns>returns0)returnFrame=frame;
                    float roll=Mathf.Abs(Mathf.DeltaAngle(0,driver.transform.localEulerAngles.z));maxRoll=Mathf.Max(maxRoll,roll);
                    var a=game.Player.transform.position;var b=game.BallPosition;
                    trace.Add($"{frame},{game.Flow},{game.StretchActive},{game.Stretches-stretches0},{game.Returns-returns0},{driver.PlayingClip},{driver.PlayingClipTime:F3},{driver.actor.SignedTimeToContact:F3},{a.x:F3},{a.z:F3},{roll:F2},{b.x:F3},{b.y:F3},{b.z:F3}");
                    if(frame%2==0)
                    {
                        string id=(frame/2).ToString("00000");GameCapture.Save(Path.Combine(path,"game_"+id+".png"),960,540);
                        var camera=game.GameplayCamera?game.GameplayCamera:Camera.main;Shot(camera,Path.Combine(path,"side_"+id+".png"),game.Player.transform.position);
                    }
                }
                game.AutoPlay=false;
                File.WriteAllLines(Path.Combine(path,"trace.csv"),trace);
                string line=$"{(female?"female":"male")}: stretches={game.Stretches-stretches0} stretchFrame={stretchFrame} lungeX={lungeTo:F2} wideReturnFrame={returnFrame} returnsIn7s={game.Returns-returns0} maxHeroRollDeg={maxRoll:F2}";
                audit.Add(line);Debug.Log("[TennisStretchFilm] "+line);
            }
            File.WriteAllLines(Path.Combine(directory,"audit.txt"),audit);Debug.Log("[TennisStretchFilm] complete "+directory);
        }
    }
}
#endif
