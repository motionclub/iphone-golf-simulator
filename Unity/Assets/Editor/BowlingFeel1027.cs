#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using GolfArcade.Bowling;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Proof for the 10-27 bowling feel pass (Adnan: easy power, aim by swinging, quick side to side):
    ///   -executeMethod GolfArcade.EditorTools.BowlingFeel1027.Run   BFEEL_OUT=<dir>  BFEEL=move,film  BFEEL_FPS=60
    /// move: board 20 → 3 the old ways (half-board taps at 6 a second, the old 7 pt-per-board drag) and the new ones (the lane
    /// slider, the held chevron's step schedule), each to the moment the approach starts with the hold pressed as soon as the game
    /// takes it (old rule: only once the bowler has arrived) → move.csv.
    /// film: Club Lanes through the phone path (MotionInput, NativeMotion at 100 Hz): two slider moves, then three brisk swings from
    /// board 20 — straight, swung 15° right, swung 15° left — frames at BFEEL_FPS (BakeMesh copies) + balls.csv.
    [InitializeOnLoad]
    public static class BowlingFeel1027
    {
        const string Flag = "BowlingFeel1027";
        static IEnumerator script;
        static int lastFrame = -1;
        static string output;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        static string F(float v) => v.ToString("0.###", Inv);
        const BindingFlags Any = BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance;

        static BowlingFeel1027() { EditorApplication.update += Tick; }

        public static void Run()
        {
            script = null; lastFrame = -1;
            if (!File.Exists(BowlingFilm.ScenePath)) BowlingFilm.EnsureScene();
            EditorSceneManager.OpenScene(BowlingFilm.ScenePath);
            EditorUtility.audioMasterMute = true;
            BowlingVenue.Selected = BowlingVenueKind.ClubLanes;
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            try { if (script == null) script = Record(); if (!script.MoveNext()) Finish(0); }
            catch (Exception e)
            {
                Debug.LogException(e);
                if (!string.IsNullOrEmpty(output)) File.WriteAllText(Path.Combine(output, "error.txt"), e.ToString());
                Finish(1);
            }
        }

        static void Finish(int code)
        {
            SessionState.SetBool(Flag, false); Time.captureFramerate = 0;
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }

        static IEnumerator Fresh(Action<BowlingGame> got)
        {
            BowlingVenue.Selected = BowlingVenueKind.ClubLanes;
            EditorSceneManager.LoadSceneInPlayMode(BowlingFilm.ScenePath, new LoadSceneParameters(LoadSceneMode.Single));
            yield return null; yield return null;
            for (int i = 0; i < 600; i++)
            {
                var g = Object.FindFirstObjectByType<BowlingGame>();
                if (g && g.Initialized)
                {
                    g.KeyboardEnabled = false; g.MotionInput = true; g.Clock = () => Time.timeAsDouble;
                    g.PlayerFemale.Clear(); g.PlayerFemale.Add(false);
                    g.NewGame(new[] { "You" });
                    got(g); yield break;
                }
                yield return null;
            }
            throw new Exception("no BowlingGame");
        }

        static IEnumerator Record()
        {
            output = Path.GetFullPath(Environment.GetEnvironmentVariable("BFEEL_OUT") ?? "../work/bowling/proof/feel-1027");
            Directory.CreateDirectory(output);
            var stages = (Environment.GetEnvironmentVariable("BFEEL") ?? "move,film").Split(',');
            if (Array.IndexOf(stages, "move") >= 0)
            {
                BowlingGame game = null;
                var w = Fresh(g => game = g); while (w.MoveNext()) yield return w.Current;
                var e = Move(game); while (e.MoveNext()) yield return e.Current;
            }
            if (Array.IndexOf(stages, "film") >= 0)
            {
                BowlingGame game = null;
                var w = Fresh(g => game = g); while (w.MoveNext()) yield return w.Current;
                var e = Film(game); while (e.MoveNext()) yield return e.Current;
            }
        }

        static BowlingHero Bowler(BowlingGame g) => (BowlingHero)typeof(BowlingGame).GetProperty("Bowler", Any).GetValue(g);

        // ------------------------------------------------------------------ move

        static IEnumerator Move(BowlingGame game)
        {
            Time.captureFramerate = 60;
            var csv = new StringBuilder("way,input_s,arrive_s,approach_s,commands\n");
            // each way: when (s after the start) each command goes, and whether the hold may be pressed before the bowler arrives
            var ways = new List<(string name, bool oldHold, List<(float t, Action<BowlingGame> act)> cmds)>();
            List<(float, Action<BowlingGame>)> Taps(int n, float gap, float boards) { var l = new List<(float, Action<BowlingGame>)>(); for (int i = 0; i < n; i++) l.Add((i * gap, g => g.PlayerMove(boards))); return l; }
            ways.Add(("before: +/- buttons, half a board per tap, 6 taps/s", true, Taps(34, 1 / 6f, -.5f)));
            ways.Add(("before: drag the BOARD pad, 1 board per 7 pt at 400 pt/s", true, Taps(17, 7 / 400f, -1)));
            ways.Add(("after: lane slider, one touch at the edge", false, new List<(float, Action<BowlingGame>)> { (0, g => g.PlayerBoard(3)) }));
            {
                // the held chevron: one step on touch, the next after 0.35 s, then gaps 0.25 s × 0.8 each down to 1/16 s
                var l = new List<(float, Action<BowlingGame>)>(); float t = 0, gap = .25f;
                for (int i = 0; i < 17; i++) { float b = 19 - i; l.Add((t, g => g.PlayerBoard(b))); if (i == 0) t = .35f; else { t += gap; gap = Mathf.Max(.0625f, gap * .8f); } }
                ways.Add(("after: hold the chevron (repeats, speeding up)", false, l));
            }
            foreach (var (name, oldHold, cmds) in ways)
            {
                // back to board 20, the bowler settled
                game.Move(20 - game.Board);
                for (int i = 0; i < 600 && !(game.Flow == BowlingGame.Phase.Setup && Bowler(game) && Bowler(game).Arrived && Mathf.Abs(game.Board - 20) < .01f); i++) yield return null;
                for (int i = 0; i < 30; i++) yield return null;
                float start = Time.time, input = -1, arrive = -1, approach = -1; int next = 0;
                while (Time.time - start < 12)
                {
                    float t = Time.time - start;
                    while (next < cmds.Count && cmds[next].t <= t + 1e-4f) { cmds[next].act(game); next++; if (next == cmds.Count) input = t; }
                    var h = Bowler(game);
                    bool atEdge = Mathf.Abs(game.Board - 3) < .01f;
                    if (atEdge && arrive < 0 && h && h.Arrived) arrive = t;
                    // the thumb goes down as soon as the game takes it: the old rule waited for the feet (a press before that was lost)
                    if (atEdge && game.Flow == BowlingGame.Phase.Setup && !game.Holding && (!oldHold || h.Arrived)) game.PlayerHold(true);
                    if (game.Flow == BowlingGame.Phase.Approach) { approach = t; break; }
                    yield return null;
                }
                csv.Append($"\"{name}\",{F(input)},{F(arrive)},{F(approach)},{cmds.Count}\n");
                Debug.Log($"[BowlingFeel1027] move {name}: input {input:0.00} s, arrived {arrive:0.00} s, approach {approach:0.00} s");
                // let this ball go (no swing read: the plain ball) and wait for the next setup
                for (int i = 0; i < 1800 && game.Flow != BowlingGame.Phase.Setup; i++)
                {
                    if (game.Holding && game.Flow == BowlingGame.Phase.Approach && (float)typeof(BowlingGame).GetField("approachT", Any).GetValue(game) > 2.0f) game.PlayerHold(false);
                    if (game.LongWalk || game.Flow == BowlingGame.Phase.Replay) { game.PlayerHold(true); game.PlayerHold(false); }
                    yield return null;
                }
            }
            File.WriteAllText(Path.Combine(output, "move.csv"), csv.ToString());
        }

        // ------------------------------------------------------------------ film

        static IEnumerator Film(BowlingGame game)
        {
            int fps = int.TryParse(Environment.GetEnvironmentVariable("BFEEL_FPS"), out int ff) ? ff : 60;
            string dir = Path.Combine(output, "film"); Directory.CreateDirectory(Path.Combine(dir, "frames"));
            foreach (var old in Directory.GetFiles(Path.Combine(dir, "frames"), "*.jpg")) File.Delete(old);
            Time.captureFramerate = fps;
            var heroes = (List<BowlingHero>)typeof(BowlingGame).GetField("heroes", Any).GetValue(game);
            var csv = new StringBuilder("ball,swing,swing_deg_read,aim_deg,launch_deg,grade,speed_mph,board,knocked,standing_after\n");
            float[] aims = { 0, 15, -15 }; string[] names = { "straight", "right 15", "left 15" };
            int balls = 0, thrown = 0; PhoneSwing swing = null; float idle = 0;
            game.BallFinished += (th, act) =>
            {
                csv.Append(string.Join(",", balls, names[Mathf.Min(balls, names.Length - 1)], F(game.LastReading.SwingAimDeg), F(game.LastAimDeg), F(th.LaunchDeg), th.Grade,
                    F(th.Speed * 2.237f), F(th.Board), act.Knocked, BowlingLeave.Numbers(act.StandingAfter))).Append('\n');
                balls++;
            };
            // wait for the bowler at the stance
            for (int i = 0; i < 600 && !(Bowler(game) && Bowler(game).Arrived); i++) yield return null;
            int frame = 0; float start = Time.time;
            var moves = new[] { (.6f, 10f), (2.2f, 20f) };   // the lane slider: across to board 10, back to 20
            int moved = 0;
            while (Time.time - start < 60 && !(balls >= aims.Length && game.Flow == BowlingGame.Phase.Setup))
            {
                float t = Time.time - start;
                BowlingFix1027.SaveBaked(heroes, Path.Combine(dir, "frames", $"f_{frame++:00000}.jpg"), 960, 540);
                if (moved < moves.Length && t >= moves[moved].Item1) game.PlayerBoard(moves[moved++].Item2);
                if (moved == moves.Length && thrown < aims.Length && swing == null && game.Flow == BowlingGame.Phase.Setup && t > 3.4f && (idle += Time.deltaTime) > .5f)
                {
                    game.PlayerHold(true);
                    if (game.Flow == BowlingGame.Phase.Hold) { swing = new PhoneSwing(aims[thrown++], Time.timeAsDouble); idle = 0; }
                }
                if (swing != null)
                {
                    swing.Feed(game, Time.timeAsDouble);
                    if (game.Flow != BowlingGame.Phase.Hold && game.Flow != BowlingGame.Phase.Approach) { if (game.Holding) game.PlayerHold(false); swing = null; }
                }
                // a tap skips the walks back and the replays (short film)
                if (swing == null && (game.LongWalk || game.Flow == BowlingGame.Phase.Replay)) { game.PlayerHold(true); game.PlayerHold(false); }
                yield return null;
            }
            File.WriteAllText(Path.Combine(dir, "balls.csv"), csv.ToString());
            Debug.Log($"[BowlingFeel1027] film {frame} frames at {fps} fps, {balls} balls\n{csv}");
            Time.captureFramerate = 30;
        }

        /// A brisk phone swing (BowlingSelfTimedTests' pendulum, tempo .33, 80° back) whose forward swing turns `aimDeg` off the
        /// backswing's line (+ = right) through its first 60 %, letting go just past the bottom. CoreMotion's z-up frame.
        sealed class PhoneSwing
        {
            readonly double t0, aim, q = .33; double fed, bottom; float prevPhi = 70, prevYaw;
            public PhoneSwing(float aimDeg, double now) { aim = aimDeg; t0 = fed = now; Phi(0, out bottom); }
            double Phi(double t, out double bot)
            {
                double q1 = q * .62, a = 80, q2 = q1 * a / 35, q4 = q * 90 / a;
                double tDrop = .45, tBack = tDrop + q1, tTop = tBack + q2; bot = tTop + q;
                if (t <= 0) return 70;
                if (t < tDrop) { double u = t / tDrop; return 70 - 35 * u * u * (3 - 2 * u); }
                if (t < tBack) return 35 * Math.Cos(Math.PI / 2 * (t - tDrop) / q1);
                if (t < tTop) return -a * Math.Sin(Math.PI / 2 * (t - tBack) / q2);
                if (t < bot) return -a * Math.Cos(Math.PI / 2 * (t - tTop) / q);
                return 90 * Math.Sin(Math.PI / 2 * Math.Min(1, (t - bot) / q4));
            }
            float Yaw(double t)
            {
                double top = bottom - q, u = Math.Max(0, Math.Min(1, (t - top) / (q * .6)));
                return (float)(aim * u * u * (3 - 2 * u));
            }
            public void Feed(BowlingGame game, double now)
            {
                const double dt = .01;
                for (; fed + dt <= now + 1e-9; fed += dt)
                {
                    double t = fed + dt - t0;
                    float phi = (float)Phi(t, out _), yaw = Yaw(t);
                    var plane = Quaternion.AngleAxis(-yaw, Vector3.forward);   // + aim = clockwise seen from above (z up)
                    var att = plane * Quaternion.AngleAxis(phi - 70, Vector3.right);
                    float rate = (phi - prevPhi) * Mathf.Deg2Rad / (float)dt, yawRate = -(yaw - prevYaw) * Mathf.Deg2Rad / (float)dt;
                    var world = plane * Vector3.right * rate + Vector3.forward * yawRate;
                    var device = Quaternion.Inverse(att) * world;
                    game.NativeMotion(fed + dt, att.x, att.y, att.z, att.w, device.x, device.y, device.z);
                    prevPhi = phi; prevYaw = yaw;
                }
                if (now - t0 >= bottom + BowlingGame.ReleaseAfterBottom && game.Holding) game.PlayerHold(false);
            }
        }
    }
}
#endif
