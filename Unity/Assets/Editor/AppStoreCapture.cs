#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Shot;
using GolfArcade.Tennis;
using GolfArcade.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// App Store landscape shots (2868x1320) of real gameplay with the real HUD.
    /// -executeMethod GolfArcade.EditorTools.AppStoreCapture.RunGolf / RunTennis, APPSTORE_OUT=<dir>.
    [InitializeOnLoad]
    public static class AppStoreCapture
    {
        const string Key = "AppStoreCapture"; const int W = 2868, H = 1320;
        static readonly BindingFlags P = BindingFlags.Instance | BindingFlags.NonPublic;
        static IEnumerator script; static int last = -1; static RenderTexture rt;
        static string Out => SessionState.GetString(Key + "out", ".");

        static AppStoreCapture() { EditorApplication.update += Tick; }
        public static void RunGolf() => Start("golf", "Assets/Scenes/Golf.unity");
        public static void RunTennis() => Start("tennis", "Assets/Scenes/Tennis.unity");
        static void Start(string mode, string scene)
        {
            var o = Environment.GetEnvironmentVariable("APPSTORE_OUT") ?? Path.GetFullPath("../work/appstore-shots");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", o); SessionState.SetString(Key, mode);
            EditorSceneManager.OpenScene(scene); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            var mode = SessionState.GetString(Key, "");
            if (mode == "" || !EditorApplication.isPlaying || last == Time.frameCount) return;
            last = Time.frameCount;
            try
            {
                if (script == null)
                {
                    if (mode == "golf") { var g = Object.FindFirstObjectByType<GolfGame>(); if (!g || g.Swing == null) return; script = Golf(g); }
                    else { var t = Object.FindFirstObjectByType<TennisGame>(); if (!t || !t.Initialized) return; script = Tennis(t); }
                }
                if (!script.MoveNext()) Finish(0);
            }
            catch (Exception e) { Debug.LogException(e); File.WriteAllText(Path.Combine(Out, mode + "_error.txt"), e.ToString()); Finish(1); }
        }
        static void Finish(int code) { SessionState.SetString(Key, ""); Time.captureFramerate = 0; EditorApplication.Exit(code); }

        // Point every phone camera and overlay HUD at a 2868x1320 surface and keep them there, so canvases lay out at that size.
        static void Bind(Camera main)
        {
            if (!rt) { rt = new RenderTexture(W, H, 24) { antiAliasing = 4 }; rt.Create(); }
            OffscreenSize.Override = new Vector2Int(W, H);
            foreach (var c in Object.FindObjectsByType<Camera>(FindObjectsSortMode.None))
                if (c.enabled && c.gameObject.activeInHierarchy && c.targetDisplay == 0 && (!c.targetTexture || c.targetTexture == rt)) { c.targetTexture = rt; c.aspect = (float)W / H; }
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None))
                if (c.isRootCanvas && c.renderMode == RenderMode.ScreenSpaceOverlay) { c.renderMode = RenderMode.ScreenSpaceCamera; c.worldCamera = main; c.planeDistance = .5f; }
        }
        static void Shot(Camera main, string name)
        {
            Bind(main);
            foreach (var h in Object.FindObjectsByType<GolfShotHud>(FindObjectsSortMode.None)) h.RefreshLayout();
            foreach (var c in Object.FindObjectsByType<HoleOutCard>(FindObjectsSortMode.None)) c.RefreshLayout();
            Canvas.ForceUpdateCanvases();
            var cams = new List<Camera>();
            foreach (var c in Object.FindObjectsByType<Camera>(FindObjectsSortMode.None)) if (c.enabled && c.gameObject.activeInHierarchy && c.targetTexture == rt) cams.Add(c);
            cams.Sort((a, b) => a.depth.CompareTo(b.depth));
            foreach (var c in cams) c.Render();
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false); var a = RenderTexture.active;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = a;
            File.WriteAllBytes(Path.Combine(Out, name + ".png"), tex.EncodeToPNG()); Object.DestroyImmediate(tex);
            Debug.Log("[AppStoreCapture] wrote " + name);
        }

        static IEnumerator Golf(GolfGame game)
        {
            Time.captureFramerate = 30; game.InstantReplays = false;
            var cam = game.GameplayCamera; var rig = cam.GetComponent<CameraRig>();
            game.PrepareNativeAddress();
            for (int i = 0; i < 40; i++) yield return null;
            typeof(GolfGame).GetMethod("ChangeWeather", P).Invoke(game, new object[] { Weather.Clear });
            game.SetWind(new Wind(6, 20));
            Bind(cam);
            for (int i = 0; i < 20; i++) yield return null;
            void Frame() { typeof(GolfGame).GetMethod("FrameAim", P).Invoke(game, null); rig.SnapNext(); rig.ApplyFrame(); }
            void Pin() { var hud = game.TutorialHud; var b = hud.Map.Ball; var p = hud.Map.Pin; b.y = p.y = 0; hud.SetPinMarker(cam, hud.Map.Pin + Vector3.up * 3.2f, "PIN  " + (p - b).magnitude.ToString("F0") + " YD"); }
            Frame(); for (int i = 0; i < 8; i++) yield return null;
            Pin(); Shot(cam, "golf_hole1_tee");
            typeof(GolfGame).GetMethod("SelectClub", P).Invoke(game, new object[] { GolfClub.Driver });
            for (int i = 0; i < 28; i++) { game.TutorialHud.SetMeter(.85f, null, "204 yd"); yield return null; }
            Pin(); Shot(cam, "golf_hole1_swing");
            game.TutorialHud.SetMeter(0f);
            game.JumpToHole(7); game.DropBall(game.CurrentHole.Tee); for (int i = 0; i < 20; i++) yield return null;
            Bind(cam); Frame(); for (int i = 0; i < 8; i++) yield return null;
            Pin(); Shot(cam, "golf_hole7_tee");
        }

        static IEnumerator Tennis(TennisGame game)
        {
            Time.captureFramerate = 30;
            var pres0 = Object.FindFirstObjectByType<TennisPresentation>();
            for (int i = 0; i < 1500 && pres0 && pres0.isActiveAndEnabled && pres0.gameObject.activeInHierarchy; i++) yield return null;
            for (int i = 0; i < 240; i++) yield return null;
            Debug.Log("[AppStoreCapture] tennis phase " + game.Flow);
            var cam = game.GameplayCamera; Bind(cam);
            for (int i = 0; i < 10; i++) yield return null;
            Shot(cam, "tennis_live");
            game.enabled = false;
            var pres = Object.FindFirstObjectByType<TennisPresentation>(); if (pres) { pres.Finish(); pres.enabled = false; }
            var hud = game.GetComponent<TennisHud>(); hud.MatchVisible = true; hud.PlayerName = "ADNAN"; hud.OpponentName = "MILO";
            var match = TennisMatch.New(true, 2, 6); match.PlayerGames = 3; match.OpponentGames = 2; match.PlayerSets = 1; match.PlayerPoints = 2; match.OpponentPoints = 1;
            typeof(TennisGame).GetField("match", P).SetValue(game, match);
            hud.Refresh(game); hud.ShowGrade(Timing.Perfect, false, "FOREHAND · 98 KM/H");
            for (int i = 0; i < 10; i++) { hud.Refresh(game); yield return null; }
            Shot(cam, "tennis_rally_gamecam");
            cam.transform.position = new Vector3(0.6f, 3.2f, -15.4f);
            cam.transform.rotation = Quaternion.LookRotation(new Vector3(0, 1.1f, -1.5f) - cam.transform.position); cam.fieldOfView = 50;
            hud.ShowGrade(Timing.Perfect, false, "FOREHAND · 98 KM/H");
            for (int i = 0; i < 10; i++) { hud.Refresh(game); yield return null; }
            Shot(cam, "tennis_rally_wide");
        }
    }
}
#endif
