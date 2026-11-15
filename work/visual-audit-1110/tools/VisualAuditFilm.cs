#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Visual audit only (lives in the audit clone): an autoplayed tennis rally, gameplay camera + HUD, 1280x720.
    /// Every 6th frame, plus every frame for 8 frames after each contact (the hit effects). VA_OUT = folder, VA_FRAMES = length.
    [InitializeOnLoad]
    public static class VisualAuditFilm
    {
        const string Key = "VisualAuditFilm";
        static IEnumerator script; static int last = -1, burst; static string tagNext = "";
        static string Out => SessionState.GetString(Key + "out", ".");
        static VisualAuditFilm() { EditorApplication.update += Tick; }
        public static void RunTennis()
        {
            var o = Environment.GetEnvironmentVariable("VA_OUT"); Directory.CreateDirectory(o);
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
        static IEnumerator Film(TennisGame game)
        {
            Time.captureFramerate = 30;
            var pres = Object.FindFirstObjectByType<TennisPresentation>();
            for (int i = 0; i < 1500 && pres && pres.isActiveAndEnabled && pres.gameObject.activeInHierarchy; i++)
            { if (i % 30 == 0) GameCapture.Save($"{Out}/intro_{i:0000}.jpg", 1280, 720); yield return null; }
            game.ConfigureMatch(TennisGame.Mode.Exhibition, null, "Rival", "AUDIT");
            game.AutoPlay = true;
            TennisGame.ContactMade += (f, g, s) => { burst = 8; tagNext = "_hit" + g; };
            TennisGame.OpponentStruck += () => { burst = 6; tagNext = "_rival"; };
            int frames = int.TryParse(Environment.GetEnvironmentVariable("VA_FRAMES"), out var n) ? n : 1500;
            string tag = "";
            for (int i = 0; i < frames; i++)
            {
                if (tagNext != "") { tag = tagNext; tagNext = ""; }
                if (burst > 0 || i % 6 == 0) GameCapture.Save($"{Out}/f_{i:0000}{(burst > 0 ? tag : "")}_{game.Flow}.jpg", 1280, 720);
                if (burst > 0) burst--;
                yield return null;
            }
        }
    }
}
#endif
