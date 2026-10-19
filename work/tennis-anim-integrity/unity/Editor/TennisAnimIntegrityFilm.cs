#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Debug = UnityEngine.Debug;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Chat 4 (tennis animation integrity, 2026-10-17): films a real AutoPlay match and records what both heroes actually render.
    /// TAI_OUT=<new dir> TAI_SEX=male|female (the player; the rival is the other sex) TAI_SECONDS=300 TAI_VIDEO=1 TAI_FFMPEG=<path>
    /// Output: film.mp4 (1920x720, 60 fps: gameplay camera | player side view over rival side view), frames.csv (per hero per frame: state),
    /// bones.f32 (per hero per frame: 55 humanoid bones world pos+rot, grip, strings, ball, root), events.csv (contacts), meta.json.
    [InitializeOnLoad]
    public static class TennisAnimIntegrityFilm
    {
        const string Flag = "TennisAnimIntegrityFilm";
        static IEnumerator script; static int lastFrame = -1; static string output;
        static TennisAnimIntegrityFilm() { EditorApplication.update += Tick; }
        public static void Run()
        {
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;   // Adnan: every Unity run muted
            script = null; lastFrame = -1;
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            var game = Object.FindFirstObjectByType<TennisGame>();
            if (!game || !game.Initialized) return;
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            try { if (script == null) script = Record(game); if (!script.MoveNext()) Finish(0); }
            catch (Exception e)
            {
                Debug.LogException(e);
                if (!string.IsNullOrEmpty(output)) File.WriteAllText(Path.Combine(output, "error.txt"), e.ToString());
                Finish(1);
            }
        }
        static void Finish(int code)
        {
            TaiRecorder.Stop();
            SessionState.SetBool(Flag, false); Time.captureFramerate = 0;
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }
        static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;

        /// TAI_MODE=servesweep: the work/tennis-gameplay-audit ServeSweep offsets (swing this long after the toss apex), but on real
        /// rendered frames with the recorder on, so the hero's visible serve swing is measured (the audit's ManualSimulation steps never draw).
        static IEnumerator ServeSweep(TennisGame game)
        {
            var offsets = new[] { -.40f, -.30f, -.20f, -.12f, -.06f, -.03f, 0f, .03f, .06f, .12f, .20f, .30f, .40f };
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null); game.AutoPlay = false;
            var rec = new GameObject("TAI recorder").AddComponent<TaiRecorder>();
            rec.Begin(game, output, false, "", 60 * 60 * 30);
            var log = new StringBuilder("offset,swingTick,flowAfter\n");
            foreach (float off in offsets)
            {
                game.Refeed();
                int guard = 0; while (game.Flow != TennisGame.Phase.PlayerServeHold && guard++ < 600) yield return null;
                for (int w = 0; w < 30; w++) yield return null;
                game.Toss(1f);
                guard = 0; while (game.Flow != TennisGame.Phase.PlayerServeToss && guard++ < 600) yield return null;
                float wait = (TennisRules.ServeApex + off) / TennisGame.GameSpeed;   // game seconds of toss -> real seconds at the rally pace
                for (float t = 0; t < wait && game.Flow == TennisGame.Phase.PlayerServeToss; t += 1f / 60) yield return null;
                if (game.Flow == TennisGame.Phase.PlayerServeToss)
                {
                    game.BeginSwing(0, .3f, 1, 0);
                    for (int i = 0; i < 2; i++) yield return null;
                    game.RequestSwing(.8f, 0, .3f, 1, .03f);
                }
                log.Append(off.ToString(CultureInfo.InvariantCulture) + "," + Time.frameCount + "," + game.Flow + "\n");
                for (int i = 0; i < 180; i++) yield return null;
            }
            File.WriteAllText(Path.Combine(output, "servesweep.csv"), log.ToString());
            TaiRecorder.Stop();
        }

        static IEnumerator Record(TennisGame game)
        {
            output = Path.GetFullPath(Env("TAI_OUT", "../work/tennis-anim-integrity/films/run"));
            Directory.CreateDirectory(output);
            bool female = Env("TAI_SEX", "male") == "female";
            int seconds = int.Parse(Env("TAI_SECONDS", "300"), CultureInfo.InvariantCulture);
            Time.captureFramerate = 60;
            TennisGame.AutoPlayTimingJitter = float.Parse(Env("TAI_JITTER", ".20"), CultureInfo.InvariantCulture);
            game.ManualSimulation = false; game.AutoPlay = false; game.NativeControlled = true; game.SetControllerSetup(false);
            var presentation = game.GetComponent<TennisPresentation>(); if (presentation) presentation.Finish();
            game.SelectCharacter(female);
            // the rival is the other hero: a standard rival of the other sex if the default one matches the player
            if (game.Opponent.Female == female) game.ConfigureMatch(TennisGame.Mode.Exhibition, female ? "Dex" : "Lina", null, "INTEGRITY");
            else game.ConfigureMatch(TennisGame.Mode.Exhibition, null, "Rival", "INTEGRITY");
            game.Refeed();
            for (int w = 0; w < 30; w++) yield return null;
            game.GameplayCamera.aspect = 1280f / 720f;
            if (Env("TAI_MODE", "") == "servesweep") { var sweep = ServeSweep(game); while (sweep.MoveNext()) yield return sweep.Current; yield break; }
            game.AutoPlayLean = true; game.AutoPlay = true;
            var rec = new GameObject("TAI recorder").AddComponent<TaiRecorder>();
            rec.Begin(game, output, Env("TAI_VIDEO", "1") == "1", Env("TAI_FFMPEG", ""), seconds * 60);
            while (!rec.Done) yield return null;
            Debug.Log("[TAI] complete " + output);
        }
    }

}
#endif
