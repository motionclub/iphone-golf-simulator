using System;
using System.Collections;
using System.IO;
using System.Reflection;
using System.Text;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class AnimationSafetyFilm
    {
        const string Flag = "AnimationSafetyFilm";
        static IEnumerator routine; static int lastFrame = -1;
        static AnimationSafetyFilm() => EditorApplication.update += Tick;
        public static void Run()
        {
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            var game = Object.FindFirstObjectByType<TennisGame>(); if (!game || !game.Initialized) return;
            routine ??= Film(game);
            try { if (!routine.MoveNext()) Finish(0); }
            catch (Exception e) { Debug.LogException(e); Finish(1); }
        }
        static void Finish(int code)
        {
            Time.captureFramerate = 0; SessionState.SetBool(Flag, false);
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }
        static IEnumerator Film(TennisGame game)
        {
            string dir = Environment.GetEnvironmentVariable("ANIMATION_FILM") ?? "/private/tmp/animation-safety-live";
            Directory.CreateDirectory(dir); Time.captureFramerate = 60;
            game.SelectCharacter(Environment.GetEnvironmentVariable("ANIMATION_MALE") != "1");
            game.ConfigureMatch(TennisGame.Mode.Campaign, "Viktor", "Viktor", "ROUND");
            game.GetComponent<TennisPresentation>()?.Finish();
            for (int i = 0; i < 90; i++) yield return null;
            var driver = game.Player.GetComponentInChildren<HeroTennisDriver>();
            var camera = Object.Instantiate(game.GameplayCamera); camera.name = "Animation proof camera";
            camera.enabled = false; camera.fieldOfView = 38;
            foreach (var behaviour in camera.GetComponents<Behaviour>())
                if (behaviour != camera && !(behaviour is UnityEngine.Rendering.Universal.UniversalAdditionalCameraData)) behaviour.enabled = false;
            var trace = new StringBuilder("clip,frame,time,active,armResidual,footSkate\n");
            foreach (var clip in new[] { HeroTennisDriver.Clip.IntroWave, HeroTennisDriver.Clip.EmoteShock,
                HeroTennisDriver.Clip.EmoteFistPump, HeroTennisDriver.Clip.IntroPushups, HeroTennisDriver.Clip.EmoteDefeat })
            {
                string only=Environment.GetEnvironmentVariable("ANIMATION_ONLY");if(!string.IsNullOrEmpty(only)&&!Array.Exists(only.Split(','),name=>name==clip.ToString()))continue;
                typeof(TennisGame).GetProperty("Flow").GetSetMethod(true).Invoke(game, new object[] { TennisGame.Phase.PointOver });
                typeof(TennisGame).GetField("resetTimer", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(game, 1e6f);
                driver.ResetForPoint();
                for (int i = 0; i < 30; i++) yield return null;
                if (!driver.PlayEmote(clip)) throw new Exception("Cannot play " + clip);
                int frames = Mathf.CeilToInt((driver.EmoteDuration(clip) + .5f) * 60);
                for (int frame = 0; frame < frames; frame++)
                {
                    yield return null;
                    trace.AppendLine($"{clip},{frame},{driver.PlayingClipTime:R},{driver.EmoteActive},{driver.FinalArmPenetration:R},{driver.FootSkate:R}");
                    if (frame % 20 != 0) continue;
                    var root = game.Player.transform;
                    camera.transform.SetPositionAndRotation(root.TransformPoint(.4f, 1.5f, 4.1f), Quaternion.LookRotation(root.TransformPoint(0, .8f, .1f) - root.TransformPoint(.4f, 1.5f, 4.1f)));
                    camera.fieldOfView = 38;
                    Save(camera, $"{dir}/{clip}_{frame:000}.png");
                    if(Environment.GetEnvironmentVariable("ANIMATION_DEFORM_DUMP")=="1" && (frame==80 || Environment.GetEnvironmentVariable("ANIMATION_DENSE_DUMP")=="1")) {
                        var look=driver.GetComponent<MatchHeroLook>();string suffix=Environment.GetEnvironmentVariable("ANIMATION_DENSE_DUMP")=="1"?$"_{frame:000}":"";FemaleDeformationAudit.Dump(look.body,$"{dir}/{clip}{suffix}_body");
                        foreach(var r in look.kit)if(r&&(r.name=="Kit_Bottom"||r.name=="Kit_Top"))FemaleDeformationAudit.Dump(r,$"{dir}/{clip}{suffix}_{r.name}");
                        var focus=(look.Bone(HumanBodyBones.Head).position+look.Bone(HumanBodyBones.Hips).position+(look.Bone(HumanBodyBones.LeftFoot).position+look.Bone(HumanBodyBones.RightFoot).position)*.5f)/3;
                        var from=focus+root.TransformVector(3.6f,.65f,.6f);camera.transform.SetPositionAndRotation(from,Quaternion.LookRotation(focus-from));
                        Save(camera,$"{dir}/{clip}{suffix}_side.png");
                    }
                }
                if (driver.EmoteActive) throw new Exception("Emote did not finish " + clip);
            }
            if(Environment.GetEnvironmentVariable("ANIMATION_POSES")=="1") {
                typeof(TennisGame).GetProperty("Flow").GetSetMethod(true).Invoke(game,new object[]{TennisGame.Phase.PointOver});
                typeof(TennisGame).GetField("resetTimer",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(game,1e6f);
                driver.ResetForPoint();for(int settle=0;settle<30;settle++)yield return null;
                driver.enabled=false;
                foreach(var clip in new[]{HeroTennisDriver.Clip.Backhand,HeroTennisDriver.Clip.BackhandWide,HeroTennisDriver.Clip.Serve}) {
                    driver.Sample(HeroTennisDriver.Clip.Ready,.1f);
                    for(int settle=0;settle<30;settle++)yield return null;
                    int frames=Mathf.CeilToInt(driver.LengthOf(clip)*60);
                    for(int frame=0;frame<=frames;frame++) {
                        driver.Sample(clip,Mathf.Min(driver.LengthOf(clip),frame/60f));yield return null;
                        if(frame%10!=0)continue;
                        var root=game.Player.transform;
                        camera.transform.SetPositionAndRotation(root.TransformPoint(2.5f,1.35f,3.6f),Quaternion.LookRotation(root.TransformPoint(0,.8f,.1f)-root.TransformPoint(2.5f,1.35f,3.6f)));
                        Save(camera,$"{dir}/{clip}_pose_{frame:000}.png");
                        if(Environment.GetEnvironmentVariable("ANIMATION_DENSE_DUMP")=="1") {
                            var look=driver.GetComponent<MatchHeroLook>();FemaleDeformationAudit.Dump(look.body,$"{dir}/{clip}_{frame:000}_body");
                            foreach(var r in look.kit)if(r&&r.name=="Kit_Bottom")FemaleDeformationAudit.Dump(r,$"{dir}/{clip}_{frame:000}_Kit_Bottom");
                        }
                    }
                }
                driver.enabled=true;
            }
            File.WriteAllText(dir + "/live-trace.csv", trace.ToString());
            Debug.Log("[AnimationSafetyFilm] completed " + dir);
        }
        static void Save(Camera camera, string path)
        {
            var rt = RenderTexture.GetTemporary(640, 800, 24); var previous = RenderTexture.active;
            camera.targetTexture = rt; camera.Render(); RenderTexture.active = rt;
            var tex = new Texture2D(640, 800, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 640, 800), 0, 0); tex.Apply(); File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.Destroy(tex); RenderTexture.active = previous; camera.targetTexture = null; RenderTexture.ReleaseTemporary(rt);
        }
    }
}
