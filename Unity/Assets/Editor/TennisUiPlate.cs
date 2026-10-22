#if UNITY_EDITOR
using System;
using System.IO;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.EditorTools
{
    /// One clean tennis frame with no HUD (the tennis camera as the HUD review tool frames it), for laying UI mock-ups over.
    /// Run with -executeMethod GolfArcade.EditorTools.TennisUiPlate.Run and GOLF_UI_OUT=<dir>.
    [InitializeOnLoad]
    public static class TennisUiPlate
    {
        const string Flag = "TennisUiPlate";
        static int frame; static double due; static TennisGame game;
        static TennisUiPlate() { EditorApplication.update += Tick; }

        public static void Run()
        {
            SessionState.SetString(Flag + "out", Environment.GetEnvironmentVariable("GOLF_UI_OUT"));
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying) return;
            try
            {
                if (!game)
                {
                    game = UnityEngine.Object.FindFirstObjectByType<TennisGame>();
                    if (!game || !game.Initialized) { game = null; return; }
                    if (++frame < 50) { game = null; return; }
                    game.enabled = false;
                    var presentation = UnityEngine.Object.FindFirstObjectByType<TennisPresentation>();
                    if (presentation) { presentation.Finish(); presentation.enabled = false; }
                    due = EditorApplication.timeSinceStartup + .6; return;
                }
                if (EditorApplication.timeSinceStartup < due) return;
                Capture();
                SessionState.SetBool(Flag, false);
                if (Application.isBatchMode) EditorApplication.Exit(0); else EditorApplication.isPlaying = false;
            }
            catch (Exception e) { SessionState.SetBool(Flag, false); Debug.LogException(e); if (Application.isBatchMode) EditorApplication.Exit(1); }
        }

        static void Capture()
        {
            var camera = game.GameplayCamera;
            camera.transform.position = new Vector3(0.6f, 3.2f, -15.4f);
            camera.transform.rotation = Quaternion.LookRotation(new Vector3(0, 1.1f, -1.5f) - camera.transform.position); camera.fieldOfView = 50;
            camera.rect = new Rect(0, 0, 1, 1);
            var rt = new RenderTexture(1920, 1080, 24) { antiAliasing = 4 }; camera.targetTexture = rt;
            foreach (var canvas in UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) canvas.enabled = false;
            camera.Render();
            var previous = RenderTexture.active; RenderTexture.active = rt;
            var image = new Texture2D(1920, 1080, TextureFormat.RGB24, false); image.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); image.Apply();
            var dir = SessionState.GetString(Flag + "out", "."); Directory.CreateDirectory(dir);
            File.WriteAllBytes(Path.Combine(dir, "tennis_plate.png"), image.EncodeToPNG());
            RenderTexture.active = previous; camera.targetTexture = null; rt.Release();
        }
    }
}
#endif
