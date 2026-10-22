using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Rendering.Universal;
using GolfArcade.Tennis;

namespace GolfArcade.EditorTools
{
    /// The tennis HUD in the clear style on the real tennis scene: rally, serve power, point scored (GOLF_UI_OUT for the folder).
    [InitializeOnLoad]
    public static class TennisUiHudCapture
    {
        const string Flag = "TennisUiHudCapture";
        static int frame, shot; static double due; static TennisGame game; static TennisHud hud;
        static readonly string Output = System.Environment.GetEnvironmentVariable("GOLF_UI_OUT") ?? Path.GetFullPath("../ArtDir/ui/tennis-clear");
        static TennisUiHudCapture() { EditorApplication.update += Tick; }
        public static void Run()
        {
            Directory.CreateDirectory(Output);
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");
            SessionState.SetBool(Flag,true); EditorApplication.isPlaying=true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag,false) || !EditorApplication.isPlaying) return;
            try
            {
                if (!game)
                {
                    game=UnityEngine.Object.FindFirstObjectByType<TennisGame>();
                    if (!game || !game.Initialized) { game=null; return; }
                    if (++frame<50) { game=null; return; }
                    game.enabled=false;
                    var presentation=UnityEngine.Object.FindFirstObjectByType<TennisPresentation>();
                    if (presentation) { presentation.Finish(); presentation.enabled=false; }
                    hud=game.GetComponent<TennisHud>(); hud.MatchVisible=true;
                    hud.PlayerName="ADNAN"; hud.OpponentName="MILO";
                    hud.EventLabel="MOTION CLUB · TENNIS";
                    Prepare(); return;
                }
                hud.Refresh(game);
                if (EditorApplication.timeSinceStartup<due) return;
                Capture();
                if (++shot<3) { Prepare(); return; }
                SessionState.SetBool(Flag,false);
                Debug.Log("[TennisUi] PASS: real-scene HUD captures written to "+Output);
                if (Application.isBatchMode) EditorApplication.Exit(0); else EditorApplication.isPlaying=false;
            }
            catch(Exception e)
            {
                SessionState.SetBool(Flag,false); Debug.LogException(e);
                if (Application.isBatchMode) EditorApplication.Exit(1);
            }
        }
        static void Prepare()
        {
            typeof(TennisHud).GetField("callAt",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(hud,-9f);
            var queue=typeof(TennisHud).GetField("calls",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(hud); queue.GetType().GetMethod("Clear").Invoke(queue,null);
            typeof(TennisHud).GetField("badgeAt",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(hud,-9f);
            var match=TennisMatch.New(true,2,6);
            match.PlayerGames=3; match.OpponentGames=2; match.PlayerSets=1;
            match.PlayerPoints=shot==2?1:0; match.OpponentPoints=shot==1?1:0;
            typeof(TennisGame).GetField("match",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(game,match);
            hud.Refresh(game);
            hud.ShowServeMeter(shot==1);
            if(shot==1) hud.SetServeMeter(.78f,true);
            if(shot==0) hud.ShowGrade(Timing.Perfect,false,"FOREHAND · 98 KM/H");
            if(shot==2) hud.ShowPointResult("You","OUT · 15–0",true);
            due=EditorApplication.timeSinceStartup+.35;
        }
        static void Capture()
        {
            var camera=game.GameplayCamera;
            camera.transform.position=new Vector3(0.6f,3.2f,-15.4f);
            camera.transform.rotation=Quaternion.LookRotation(new Vector3(0,1.1f,-1.5f)-camera.transform.position); camera.fieldOfView=50;
            camera.rect=new Rect(0,0,1,1);
            camera.GetUniversalAdditionalCameraData().renderPostProcessing=false;
            var rt=new RenderTexture(1920,1080,24){antiAliasing=4}; camera.targetTexture=rt;
            foreach(var canvas in UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None))
            {
                if(canvas.name!="Tennis HUD") {canvas.enabled=false;continue;}
                canvas.enabled=true; canvas.renderMode=RenderMode.ScreenSpaceCamera; canvas.worldCamera=camera; canvas.planeDistance=1;
            }
            Canvas.ForceUpdateCanvases(); camera.Render();
            var previous=RenderTexture.active; RenderTexture.active=rt;
            var image=new Texture2D(1920,1080,TextureFormat.RGB24,false); image.ReadPixels(new Rect(0,0,1920,1080),0,0); image.Apply();
            File.WriteAllBytes(Path.Combine(Output,new[]{"tennis_rally.png","tennis_serve.png","tennis_point.png"}[shot]),image.EncodeToPNG());
            RenderTexture.active=previous; camera.targetTexture=null; rt.Release(); UnityEngine.Object.DestroyImmediate(rt); UnityEngine.Object.DestroyImmediate(image);
        }
    }
}
