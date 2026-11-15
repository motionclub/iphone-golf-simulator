#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Hero depth audit (work/hero-depth-1111, clone only): the tennis player in an autoplayed rally, filmed close from four fixed
    /// directions that follow the player (back as the game sees them, front, side, feet). HM_OUT, HM_FEMALE=1, HM_FRAMES, HM_STEP.
    [InitializeOnLoad]
    public static class HeroMotionFilm
    {
        const string Key = "HeroMotionFilm";
        static IEnumerator script; static int last = -1;
        static string Out => SessionState.GetString(Key + "out", ".");
        static HeroMotionFilm() { EditorApplication.update += Tick; }
        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("HM_OUT"); Directory.CreateDirectory(o);
            SessionState.SetString(Key + "out", o); SessionState.SetBool(Key, true);
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity"); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Key, false) || !EditorApplication.isPlaying || last == Time.frameCount) return;
            last = Time.frameCount;
            try
            {
                if (script == null) { var t = Object.FindFirstObjectByType<TennisGame>(); if (!t || !t.Initialized) return; script = Film(t); }
                if (!script.MoveNext()) Finish(0);
            }
            catch (Exception e) { Debug.LogException(e); File.WriteAllText(Path.Combine(Out, "error.txt"), e.ToString()); Finish(1); }
        }
        static void Finish(int code) { SessionState.SetBool(Key, false); Time.captureFramerate = 0; EditorApplication.Exit(code); }
        static RenderTexture rt; static Texture2D tex;
        static void Shot(Camera cam, Vector3 from, Vector3 at, float fov, string path, int S = 640)
        {
            if (!rt) { rt = new RenderTexture(S, S, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 }; tex = new Texture2D(S, S, TextureFormat.RGB24, false); }
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(at - from, Vector3.up)); cam.fieldOfView = fov; cam.nearClipPlane = .05f;
            cam.aspect = 1; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, S, S), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(path, tex.EncodeToJPG(88));
        }
        static IEnumerator Film(TennisGame game)
        {
            Time.captureFramerate = 30;
            if (Environment.GetEnvironmentVariable("HM_FEMALE") == "1") { game.SelectCharacter(true); for (int i = 0; i < 3; i++) yield return null; }
            var pres = Object.FindFirstObjectByType<TennisPresentation>();
            for (int i = 0; i < 1500 && pres && pres.isActiveAndEnabled && pres.gameObject.activeInHierarchy; i++) yield return null;
            game.ConfigureMatch(TennisGame.Mode.Exhibition, null, "Rival", "AUDIT");
            game.AutoPlay = true;
            var cam = new GameObject("Hero motion cam").AddComponent<Camera>(); cam.CopyFrom(game.GameplayCamera); cam.enabled = false;
            { var d = cam.GetUniversalAdditionalCameraData(); var s = game.GameplayCamera.GetUniversalAdditionalCameraData(); d.renderPostProcessing = s.renderPostProcessing; d.volumeLayerMask = s.volumeLayerMask; d.antialiasing = s.antialiasing; }
            int frames = int.TryParse(Environment.GetEnvironmentVariable("HM_FRAMES"), out var n) ? n : 600;
            int step = int.TryParse(Environment.GetEnvironmentVariable("HM_STEP"), out var st) ? st : 3;
            for (int i = 0; i < 60; i++) yield return null;
            for (int i = 0; i < frames; i++)
            {
                if (i % step == 0)
                {
                    var p = game.Player.transform.position; var mid = p + Vector3.up * .95f; string f = $"{i:0000}_{game.Flow}";
                    Shot(cam, p + new Vector3(.5f, 1.35f, -3.3f), mid, 30, $"{Out}/back_{f}.jpg");
                    Shot(cam, p + new Vector3(.6f, 1.15f, 3.3f), mid, 30, $"{Out}/front_{f}.jpg");
                    Shot(cam, p + new Vector3(3.3f, 1.1f, .3f), mid, 30, $"{Out}/side_{f}.jpg");
                    Shot(cam, p + new Vector3(.9f, .38f, 1.5f), p + Vector3.up * .13f, 28, $"{Out}/feet_{f}.jpg");
                    Shot(cam, p + new Vector3(.5f, 1.3f, 1.9f), p + Vector3.up * 1.12f, 30, $"{Out}/upper_{f}.jpg");
                }
                yield return null;
            }
        }
    }
}
#endif
