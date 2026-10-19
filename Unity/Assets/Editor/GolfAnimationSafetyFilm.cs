using System;
using System.Collections;
using System.IO;
using System.Text;
using GolfArcade.Game;
using GolfArcade.Shot;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class GolfAnimationSafetyFilm
    {
        const string Flag = "GolfAnimationSafetyFilm";
        static IEnumerator routine; static int lastFrame = -1;
        static GolfAnimationSafetyFilm() => EditorApplication.update += Tick;
        public static void Run()
        {
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            var game = Object.FindFirstObjectByType<GolfGame>(); if (!game) return;
            routine ??= Film(game);
            try { if (!routine.MoveNext()) Finish(0); }
            catch (Exception e) { Debug.LogException(e); Finish(1); }
        }
        static void Finish(int code)
        {
            Time.captureFramerate = 0; SessionState.SetBool(Flag, false);
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }
        static IEnumerator Film(GolfGame game)
        {
            string dir = Environment.GetEnvironmentVariable("ANIMATION_FILM") ?? "/private/tmp/golf-animation-safety-live";
            Directory.CreateDirectory(dir); Time.captureFramerate = 60;
            for (int i = 0; i < 10; i++) yield return null;
            game.PrepareNativeAddress(); game.JumpToHole(7);
            for (int i = 0; i < 30; i++) yield return null;
            game.enabled = false;
            var camera = Object.Instantiate(game.GameplayCamera); camera.name = "Golf animation proof camera"; camera.enabled = false;
            foreach (var behaviour in camera.GetComponents<Behaviour>())
                if (behaviour != camera && !(behaviour is UnityEngine.Rendering.Universal.UniversalAdditionalCameraData)) behaviour.enabled = false;
            var golfer = (GolferView)typeof(GolfGame).GetField("golfer", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).GetValue(game);
            golfer.SetVisible(true);
            var trace = new StringBuilder("sex,move,frame,wristGap,facePerformer\n");
            foreach (bool female in new[] { false, true })
            {
                if(Environment.GetEnvironmentVariable("ANIMATION_FEMALE_ONLY")=="1" && !female) continue;
                GolferStyle.Body = female ? GolferStyle.BodyKind.Female : GolferStyle.BodyKind.Male; golfer.ApplyStyle();
                for (int i = 0; i < 3; i++) yield return null;
                foreach (var club in new[] { GolfClub.Driver, GolfClub.Putter })
                {
                    golfer.Settle(); golfer.SetClub(club, false);
                    for (int frame = 0; frame < 50; frame++) { golfer.ShowLoad(frame / 40f); yield return null; if (frame % 10 == 0) Capture(club + "_load", frame); }
                    golfer.Strike();
                    for (int frame = 0; frame < 150; frame++) { yield return null; if (frame % 10 == 0) Capture(club + "_swing", frame); }
                }
                foreach (string move in new[] { "Intro_Wave", "Emote_JumpJoy", "Emote_Shock", "Emote_Defeat" })
                {
                    if (!golfer.Perform(move, loop: false)) throw new Exception("Missing golf move " + move);
                    int frames = Mathf.CeilToInt((golfer.PerformanceDuration + .4f) * 60);
                    for (int frame = 0; frame < frames; frame++) { yield return null; if (frame % 20 == 0) Capture(move, frame); }
                }
                void Capture(string move, int frame)
                {
                    var root = golfer.transform; var hero = golfer.Hero;
                    var at = root.position + Vector3.up * .9f;
                    var from = root.TransformPoint(.7f, 1.6f, 4.5f);
                    camera.transform.SetPositionAndRotation(from, Quaternion.LookRotation(at - from)); camera.fieldOfView = 38;
                    Save(camera, $"{dir}/{(female ? "female" : "male")}_{move}_{frame:000}.png");
                    if(female && frame%40==0 && Environment.GetEnvironmentVariable("ANIMATION_DEFORM_DUMP")=="1") {
                        var look=hero.Root.GetComponent<MatchHeroLook>();FemaleDeformationAudit.Dump(look.body,$"{dir}/{move}_{frame:000}_body");
                        foreach(var part in look.kit)if(part&&part.name=="Kit_Bottom")FemaleDeformationAudit.Dump(part,$"{dir}/{move}_{frame:000}_Kit_Bottom");
                    }
                    float gap = Vector3.Distance(hero.Bones["LeftHand"].position, hero.Bones["RightHand"].position);
                    trace.AppendLine($"{female},{move},{frame},{gap:R},{hero.Root.GetComponent<MatchHeroFacePerformance>() != null}");
                }
            }
            File.WriteAllText(dir + "/golf-live-trace.csv", trace.ToString());
            Debug.Log("[GolfAnimationSafetyFilm] completed " + dir);
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
