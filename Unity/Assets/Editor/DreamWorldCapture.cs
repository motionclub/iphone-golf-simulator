using System;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Tennis;
using GolfArcade.EnvironmentArt;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad] public static class DreamWorldCapture
    {
        const string Key="DreamWorldCapture";static int frame=-1,slot=-1,stage;static string output;static double deadline;
        static readonly int[] holes=(System.Environment.GetEnvironmentVariable("DREAM_PROOF_HOLES")??"7,8,9,12,15,13,14,17,18,19,20,10,16,21,22,23").Split(',').Select(int.Parse).ToArray();
        static readonly string[] modes=(System.Environment.GetEnvironmentVariable("DREAM_PROOF_MODES")??"day,sunset,night,fog,storm").Split(',');
        static AsyncOperation sceneLoad;static GolfGame golf;static CameraRig rig;static TennisGame tennis;static Camera camera;
        static readonly BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
        static DreamWorldCapture(){EditorApplication.update+=Tick;}
        public static void Run(){output=System.Environment.GetEnvironmentVariable("DREAM_PROOF_OUT")??"../work/dream-worlds-20261015/proof/rollout";Directory.CreateDirectory(output);SessionState.SetString(Key+"out",Path.GetFullPath(output));SessionState.SetBool(Key,true);bool tennisOnly=System.Environment.GetEnvironmentVariable("DREAM_PROOF_TENNIS_ONLY")=="1";SessionState.SetInt(Key+"sport",tennisOnly?1:0);EditorSceneManager.OpenScene(tennisOnly?"Assets/Scenes/Tennis.unity":"Assets/Scenes/Golf.unity");EditorApplication.isPlaying=true;}
        static void Tick()
        {
            if(!SessionState.GetBool(Key,false)||!EditorApplication.isPlaying)return;
            if(sceneLoad!=null){if(!sceneLoad.isDone)return;sceneLoad=null;tennis=null;}
            try{
                if(output==null)output=SessionState.GetString(Key+"out","");
                int sport=SessionState.GetInt(Key+"sport",0);
                if(sport==0&&!golf){golf=Object.FindFirstObjectByType<GolfGame>();rig=Object.FindFirstObjectByType<CameraRig>();if(!golf||!rig||!HoleView.Current)return;golf.ChooseHoles(0);golf.Play();camera=rig.Camera;Next();return;}
                if(sport==1&&!tennis){tennis=Object.FindFirstObjectByType<TennisGame>();if(!tennis||!tennis.Initialized){tennis=null;return;}camera=tennis.GameplayCamera;Next();return;}
                if(Time.frameCount-frame<20)return;
                if(EditorApplication.timeSinceStartup>deadline)throw new TimeoutException("capture did not settle");
                Capture(sport);Next();
            }catch(Exception e){Debug.LogException(e);SessionState.SetBool(Key,false);EditorApplication.Exit(1);}
        }
        static void Next()
        {
            int sport=SessionState.GetInt(Key+"sport",0);slot++;
            int max=sport==0?holes.Length*modes.Length:3*modes.Length;
            if(slot>=max){
                if(sport==0){if(System.Environment.GetEnvironmentVariable("DREAM_PROOF_GOLF_ONLY")=="1"){SessionState.SetBool(Key,false);EditorApplication.Exit(0);return;}SessionState.SetInt(Key+"sport",1);slot=-1;golf=null;rig=null;sceneLoad=UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Tennis");return;}
                SessionState.SetBool(Key,false);EditorApplication.Exit(0);return;
            }
            int mode=slot%modes.Length;string modeName=modes[mode];var utc=new DateTimeOffset(2026,10,15,modeName=="sunset"?23:modeName=="night"?3:17,0,0,TimeSpan.Zero).ToUnixTimeSeconds();
            System.Environment.SetEnvironmentVariable("DREAM_UTC",utc.ToString());System.Environment.SetEnvironmentVariable("DREAM_WEATHER",modeName=="fog"?"Fog":modeName=="storm"?"Storm":"Clear");
            if(sport==0){golf.enabled=true;rig.enabled=true;if(mode==0||modeName=="fog"||modeName=="storm")golf.JumpToHole(holes[slot/modes.Length]);golf.DropBall(golf.CurrentHole.Tee);}
            else{
                var venue=(TennisVenueKind)(slot/modes.Length);
                if(TennisVenue.Current!=venue){TennisVenue.Selected=venue;tennis=null;sceneLoad=UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Tennis");slot--;return;}
                // Force a new boundary only in this editor capture; gameplay keeps conditions locked per game.
                var conditions=tennis.GetComponent<TennisConditions>();if(conditions)typeof(TennisConditions).GetField("lastGame",Private).SetValue(conditions,-1);
                TennisConditions.Boundary(tennis);
            }
            frame=Time.frameCount;deadline=EditorApplication.timeSinceStartup+180;
        }
        static void Capture(int sport)
        {
            string prefix=sport==0?"hole"+holes[slot/modes.Length].ToString("00"):TennisVenue.Current.ToString().ToLowerInvariant();string path=Path.Combine(output,prefix+"_"+modes[slot%modes.Length]);
            camera.aspect=9f/16;
            if(sport==0){
                golf.enabled=false;rig.enabled=false;var h=golf.CurrentHole;
                string mode=modes[slot%modes.Length];
                if(mode.StartsWith("vent-")){
                    var vent=h.Dream.Hazards.First(x=>x.Kind==DreamHazardKind.LavaVent);
                    double phase=mode=="vent-warning"?7.5:mode=="vent-active"?9.5:2;
                    h.Movers.PhaseAtLaunch=phase-vent.Phase;h.Movers.Hold(0);
                    var view=Object.FindFirstObjectByType<DreamHazardView>();
                    var centre=new Vector3((float)vent.Centre.X,(float)vent.Height,(float)vent.Centre.D);
                    camera.transform.position=centre+new Vector3(25,24,-48);camera.transform.LookAt(centre+Vector3.up*(float)vent.ActiveHeight*.4f);camera.fieldOfView=60;
                    typeof(DreamHazardView).GetMethod("LateUpdate",Private).Invoke(view,null);
                    Save(path+"_hazard.png",false);
                    File.WriteAllText(path+".json",JsonUtility.ToJson(new Report{location=h.Number,weather=golf.CurrentWeather.ToString(),utc=DreamEnvironment.Utc,hazards=vent.Id+":"+vent.Stage(h.Movers.Now)},true));return;
                }
                void Address(CoursePoint at){rig.FrameAddress(HoleView.ToWorld(at,.06),HoleView.ToWorld(h.Pin)-HoleView.ToWorld(at),false);rig.SnapNext();rig.ApplyFrame();}
                Address(h.Tee);Save(path+"_tee.png",false);Save(path+"_hud.png",true);
                Address(DreamCourseLayout.Along(h,.85));Save(path+"_approach.png",false);
                var tee=HoleView.ToWorld(h.Tee);var pin=HoleView.ToWorld(h.Pin);var c=(tee+pin)*.5f;camera.transform.position=c+new Vector3(150,230,-180);camera.transform.LookAt(c);Save(path+"_wide.png",false);Save(path+"_preview.jpg",false,1280,720);
                File.WriteAllText(path+".json",JsonUtility.ToJson(new Report{location=h.Number,weather=golf.CurrentWeather.ToString(),utc=DreamEnvironment.Utc,hazards=h.Dream?.Code,meshes=Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None).Sum(x=>x.sharedMesh?(int)x.sharedMesh.GetIndexCount(0)/3:0),draws=UnityStats.drawCalls,submittedTriangles=UnityStats.triangles,setPasses=UnityStats.setPassCalls},true));
            }else{
                tennis.enabled=false;var presentation=tennis.GetComponent<TennisPresentation>();if(presentation)presentation.Finish();
                TennisShoulderCamera.Frame(tennis.Player.transform.position,false,Vector3.zero,false,camera.aspect,out var position,out var look,out var fov);camera.transform.position=position;camera.transform.LookAt(look);camera.fieldOfView=fov;Save(path+"_near.png",true);
                camera.transform.position=new Vector3(-position.x,position.y,-position.z);camera.transform.LookAt(new Vector3(-look.x,look.y,-look.z));Save(path+"_far.png",true);
                camera.transform.position=new Vector3(40,45,-55);camera.transform.LookAt(Vector3.zero);Save(path+"_wide.png",false);Save(path+"_preview.jpg",false,1280,720);tennis.enabled=true;
                File.WriteAllText(path+".json",JsonUtility.ToJson(new Report{location=100+(int)TennisVenue.Current,weather=TennisConditions.Weather.ToString(),utc=DreamEnvironment.Utc,meshes=Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None).Sum(x=>x.sharedMesh?(int)x.sharedMesh.GetIndexCount(0)/3:0),draws=UnityStats.drawCalls,submittedTriangles=UnityStats.triangles,setPasses=UnityStats.setPassCalls},true));
            }
        }
        [Serializable]class Report{public int location,meshes,draws,submittedTriangles,setPasses;public string measurement="Unity Editor counters; not hardware frame-time measurements";public string weather,hazards;public double utc;}
        static void Save(string path,bool hud,int width=720,int height=1280)
        {
            float previousAspect=camera.aspect;camera.aspect=(float)width/height;
            var canvases=Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);var states=canvases.Select(c=>(c.enabled,c.renderMode,c.worldCamera)).ToArray();
            for(int i=0;i<canvases.Length;i++){canvases[i].enabled=hud&&states[i].enabled;if(hud&&canvases[i].renderMode==RenderMode.ScreenSpaceOverlay){canvases[i].renderMode=RenderMode.ScreenSpaceCamera;canvases[i].worldCamera=camera;canvases[i].planeDistance=1;}}
            var old=camera.targetTexture;var active=RenderTexture.active;var rt=RenderTexture.GetTemporary(width,height,24);camera.targetTexture=rt;camera.Render();RenderTexture.active=rt;var tex=new Texture2D(width,height,TextureFormat.RGB24,false);tex.ReadPixels(new Rect(0,0,width,height),0,0);tex.Apply();File.WriteAllBytes(path,path.EndsWith(".jpg")?tex.EncodeToJPG(92):tex.EncodeToPNG());Object.DestroyImmediate(tex);camera.targetTexture=old;RenderTexture.active=active;RenderTexture.ReleaseTemporary(rt);camera.aspect=previousAspect;
            for(int i=0;i<canvases.Length;i++){canvases[i].enabled=states[i].enabled;canvases[i].renderMode=states[i].renderMode;canvases[i].worldCamera=states[i].worldCamera;}
        }
    }
}
