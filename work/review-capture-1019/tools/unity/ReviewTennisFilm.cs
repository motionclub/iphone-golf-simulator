#if UNITY_EDITOR
// Review capture 10-19 (work/review-capture-1019): a real AutoPlay exhibition point (male player vs female rival) filmed from the
// gameplay camera (with HUD) and six review angles at 30 fps, point by point until one with a real rally (3+ shots) has been
// played through its point reaction; plus tennis-kit stills of both heroes on court before the first serve.
// Set-up follows chat 4's TennisAnimIntegrityFilm (work/tennis-anim-integrity).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class ReviewTennisFilm
    {
        const string Flag = "ReviewTennisFilm.Active";
        static ReviewTennisFilm() { EditorApplication.update += Boot; }
        public static void Run()
        {
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity"); SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<ReviewTennisRecorder>()) return;
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            var g = Object.FindFirstObjectByType<TennisGame>(); if (!g || !g.Initialized) return;
            try { new GameObject("Review tennis film").AddComponent<ReviewTennisRecorder>().Begin(g); } catch (Exception e) { Debug.LogException(e); End(1); }
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    [DefaultExecutionOrder(32000)]
    public sealed class ReviewTennisRecorder : MonoBehaviour
    {
        TennisGame game; string root, pointDir; StreamWriter trace, log; int frame, wait, stage, point, saved, shots, afterOver, tail; bool done, sawOver;
        ReviewAngle[] angles; readonly List<string> keep = new();
        public void Begin(TennisGame g)
        {
            game = g;
            root = Path.GetFullPath(ReviewShared.Env("REVIEW_OUT", Path.Combine(Environment.GetEnvironmentVariable("HOME"), "review-1019-frames/tennis")));
            Directory.CreateDirectory(root);
            log = new StreamWriter(Path.Combine(root, "events.txt"));
            Time.captureFramerate = 60; UnityEngine.Random.InitState(1019);   // the game steps at 60 Hz (at 30 the AutoPlay player whiffed every return); every other frame is saved
            TennisGame.AutoPlayTimingJitter = float.Parse(ReviewShared.Env("REVIEW_JITTER", ".08"), CultureInfo.InvariantCulture);
            game.ManualSimulation = false; game.AutoPlay = false; game.NativeControlled = true; game.SetControllerSetup(false);
            var presentation = game.GetComponent<TennisPresentation>(); if (presentation) presentation.Finish();
            game.SelectCharacter(false);
            if (game.Opponent.Female == false) game.ConfigureMatch(TennisGame.Mode.Exhibition, "Lina", null, "REVIEW");
            else game.ConfigureMatch(TennisGame.Mode.Exhibition, null, "Rival", "REVIEW");
            game.Refeed();
            TennisGame.ContactMade += OnContact; TennisGame.OpponentStruck += OnRival;
            Note($"begin {root}: player female {game.Player.Female}, rival female {game.Opponent.Female}");
        }
        void OnContact(Vector2 face, Timing t, bool super) { shots++; Note($"player contact {t}"); }
        void OnRival() { shots++; Note("rival contact"); }
        void OnDestroy() { TennisGame.ContactMade -= OnContact; TennisGame.OpponentStruck -= OnRival; }
        void Note(string s) { var m = $"point {point} t {saved / 30f:F2}s (frame {frame}) {s}"; log?.WriteLine(m); log?.Flush(); Debug.Log("[ReviewTennis] " + m); }
        void LateUpdate() { if (done || !game) return; try { Step(); } catch (Exception e) { Debug.LogException(e); Finish(1); } }

        void StartPoint()
        {
            point++; saved = 0; shots = 0; sawOver = false; afterOver = 0; tail = 0;
            pointDir = Path.Combine(root, "p" + point); Directory.CreateDirectory(Path.Combine(pointDir, "gameplay"));
            string[] names = { "umpire_side", "behind_near", "behind_far", "overhead", "close_near", "net_level" };
            if (angles == null) { angles = new ReviewAngle[names.Length]; for (int i = 0; i < names.Length; i++) angles[i] = new ReviewAngle(names[i], null, 960, 540); }
            for (int i = 0; i < names.Length; i++) { angles[i].Dir = Path.Combine(pointDir, names[i]); angles[i].Saved = 0; Directory.CreateDirectory(angles[i].Dir); }
            trace?.Dispose(); trace = new StreamWriter(Path.Combine(pointDir, "trace.csv"));
            trace.WriteLine("frame,saved,flow,rallyShots,score,feedback,px,pz,ox,oz,bx,by,bz");
            Note("recording starts, flow " + game.Flow);
        }

        void Step()
        {
            var cam = game.GameplayCamera ? game.GameplayCamera : Camera.main;
            if (cam) { cam.aspect = 16f / 9f; }
            frame++; wait++;
            if (stage == 0)
            {   // both heroes standing at their serve positions: tennis-kit stills, then the AutoPlay match starts
                if (wait == 48)
                {
                    var dir = Path.Combine(root, "stills");
                    ReviewShared.Stills(Camera.main, game.Player, dir, game.Player.Female ? "tennis_female" : "tennis_male");
                    ReviewShared.Stills(Camera.main, game.Opponent, dir, game.Opponent.Female ? "tennis_female" : "tennis_male");
                    GameCapture.Save(Path.Combine(dir, "tennis_gameplay_camera_before_serve.jpg"), 1920, 1080);
                    Note("stills done");
                }
                if (wait == 60) { game.AutoPlayLean = true; game.AutoPlay = true; stage = 1; StartPoint(); }
                return;
            }
            var flow = game.Flow;
            if (flow is TennisGame.Phase.PointOver or TennisGame.Phase.MatchOver)
            {
                if (!sawOver) { sawOver = true; Note($"point over: {game.Feedback} shots {shots} score {game.Match.Scoreboard}"); }
                afterOver++;
            }
            else if (sawOver)
            {   // the next point has begun: this point is complete
                if (tail == 0) Note($"point complete ({saved} frames, {shots} shots), next point begins");
                if (shots >= 3 || point >= 5)
                {   // keep 4 s of the walk back / reaction into the next point's set-up, then stop
                    if (++tail >= 240) { keep.Add(pointDir); File.WriteAllText(Path.Combine(root, "chosen.txt"), "p" + point + "\n"); Finish(0); return; }
                }
                else StartPoint();
            }
            if (saved > 30 * 75) { Note("point ran past 75 s, kept as is"); File.WriteAllText(Path.Combine(root, "chosen.txt"), "p" + point + "\n"); Finish(0); return; }
            if (frame % 2 == 0) Save(cam);
        }

        void UpdateAngles()
        {
            var P = game.Player.transform.position; var O = game.Opponent.transform.position;
            float n = P.z < 0 ? -1 : 1;   // the near half's sign
            float k = saved < 2 ? 1 : .15f;
            float hw = TennisRules.CourtHalfWidth;
            angles[0].Aim(new Vector3(-(hw + 10.5f), 7.2f, 0), new Vector3(0, .2f, 0)); angles[0].Fov = 52;
            angles[1].Aim(new Vector3(P.x * .6f, 2.5f, P.z + n * 5.2f), new Vector3(P.x * .35f, 1.0f, P.z - n * 9f), k); angles[1].Fov = 55;
            angles[2].Aim(new Vector3(O.x * .6f, 2.5f, O.z - n * 5.2f), new Vector3(O.x * .35f, 1.0f, O.z + n * 9f), k); angles[2].Fov = 55;
            angles[3].Aim(new Vector3(0, 33f, 0), new Vector3(0, 0, .001f)); angles[3].Up = Vector3.right; angles[3].Fov = 25;
            var front = new Vector3(0, 0, -n);
            angles[4].Aim(P + front * 3.3f + Vector3.right * 1.6f + Vector3.up * 1.45f, P + Vector3.up * 1.0f, saved < 2 ? 1 : .2f); angles[4].Fov = 36;
            angles[5].Aim(new Vector3(hw + 1.2f, .95f, n * .6f), new Vector3(P.x, 1.0f, P.z), saved < 2 ? 1 : .2f); angles[5].Fov = 24;
        }

        void Save(Camera cam)
        {
            UpdateAngles();
            GameCapture.Save(Path.Combine(pointDir, "gameplay", $"f_{saved:D5}.jpg"), 1280, 720);
            foreach (var a in angles) a.Render(cam);
            var P = game.Player.transform.position; var O = game.Opponent.transform.position; var b = game.BallPosition;
            string F(float x) => x.ToString("F2", CultureInfo.InvariantCulture);
            trace.WriteLine(string.Join(",", frame, saved, game.Flow, game.RallyShots, game.Match.Scoreboard.Replace(',', ' '), (game.Feedback ?? "").Replace(',', ' '), F(P.x), F(P.z), F(O.x), F(O.z), F(b.x), F(b.y), F(b.z)));
            saved++;
        }
        void Finish(int code)
        {
            if (done) return; done = true; trace?.Dispose();
            Note($"done code {code}"); log?.Dispose();
            ReviewTennisFilm.End(code);
        }
    }
}
#endif
