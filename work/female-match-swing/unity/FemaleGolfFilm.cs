#if UNITY_EDITOR
// Review capture 10-19 (work/review-capture-1019): one full hole of the phone's own golf flow on cliffside hole 1
// (flyover, address + waggle, drive, post-shot watch, approach, putts until holed, hole-out reaction), filmed from the gameplay
// camera (with HUD) and six extra review angles at 30 fps, then character stills (male address + idle, female idle + address).
// Built on chat A's GolfFlowFilm and chat B's GolfMannerismFilm.
using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Shot;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class FemaleGolfFilm
    {
        const string Flag = "FemaleGolfFilm.Active";
        static FemaleGolfFilm() { EditorApplication.update += Boot; }
        public static void Run()
        {
            EditorUtility.audioMasterMute = true;
            GolferStyle.Body = Environment.GetEnvironmentVariable("FILM_MALE")=="1" ? GolferStyle.BodyKind.Male : GolferStyle.BodyKind.Female;
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity"); SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<FemaleGolfRecorder>()) return;
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            var g = Object.FindFirstObjectByType<GolfGame>(); if (!g || !HoleView.Current) return;
            try { new GameObject("Female golf film").AddComponent<FemaleGolfRecorder>().Begin(g); } catch (Exception e) { Debug.LogException(e); End(1); }
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    [DefaultExecutionOrder(32000)]
    public sealed class FemaleGolfRecorder : MonoBehaviour
    {
        GolfGame game; string root, frames; StreamWriter trace, log; int frame, saved, stage, wait, strokes, putts; bool done, record, sawEmote; int idleFrames;
        StreamWriter boneLog; static readonly string[] BoneNames = { "Hips", "Chest", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand", "Club" };
        ReviewAngle[] angles; Vector3 chest = Vector3.right, line = Vector3.forward, prevBall; bool haveChest; string events = "";
        static readonly BindingFlags Any = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
        GolferView Golfer => (GolferView)typeof(GolfGame).GetField("golfer", Any).GetValue(game);
        string Club => typeof(GolfGame).GetField("club", Any).GetValue(game).ToString();
        Transform Ball { get { var f = typeof(GolfGame).GetField("ball", Any); var v = f?.GetValue(game); return v is Component c ? c.transform : v is GameObject go ? go.transform : GameObject.Find("Ball")?.transform; } }
        Vector3 Pin => HoleView.ToWorld(game.CurrentHole.Pin);
        Vector3 Tee => HoleView.ToWorld(game.CurrentHole.Tee);

        public void Begin(GolfGame g)
        {
            game = g;
            root = Path.GetFullPath(ReviewShared.Env("REVIEW_OUT", Path.Combine(Environment.GetEnvironmentVariable("HOME"), "review-1019-frames/golf")));
            frames = root; Directory.CreateDirectory(root);
            PresentationPolicy.Configure("full", false, true, false);
            foreach (var key in new[] { "golf.walkon", "golf.start" }) PlayerPrefs.DeleteKey("presentation.v" + PresentationPolicy.Revision + "." + key);
            foreach (var c in new[] { "cliffside", "wildisles", "magma" })
                for (int i = 1; i <= 30; i++) PlayerPrefs.DeleteKey("presentation.v" + PresentationPolicy.Revision + ".golf.venue." + c + "." + i);
            Time.captureFramerate = 30; UnityEngine.Random.InitState(1019);
            if (Environment.GetEnvironmentVariable("FILM_NOCLEARANCE") == "1") GolfArcade.Tennis.HeroPoseSafety.Disabled = true;
            if (Environment.GetEnvironmentVariable("FILM_NOTRACKS") == "1") GolfArcade.Tennis.HeroClearanceTracks.Enabled = false;
            boneLog = new StreamWriter(Path.Combine(root, "bones.csv")); boneLog.WriteLine("frame,saved,stage," + string.Join(",", BoneNames.Select(n => n + "_qx," + n + "_qy," + n + "_qz," + n + "_qw," + n + "_px," + n + "_py," + n + "_pz")));
            game.Demo = true; game.InstantReplays = false;
            game.PrepareNativeAddress("cliffside");
            game.SetWind(new Wind(0, 0));
            game.NativeReady(); game.TryNativePresentation();
            angles = new[]
            {
                new ReviewAngle("side_on_wide", Path.Combine(root, "side_on_wide"), 960, 540),
                new ReviewAngle("face_on_close", Path.Combine(root, "face_on_close"), 960, 540),
                new ReviewAngle("drone_ball", Path.Combine(root, "drone_ball"), 960, 540),
                new ReviewAngle("behind_green", Path.Combine(root, "behind_green"), 960, 540),
                new ReviewAngle("chase_low", Path.Combine(root, "chase_low"), 960, 540),
                new ReviewAngle("establishing", Path.Combine(root, "establishing"), 960, 540),
                new ReviewAngle("hands_close", Path.Combine(root, "hands_close"), 900, 900),
            };
            Directory.CreateDirectory(Path.Combine(root, "gameplay"));
            trace = new StreamWriter(Path.Combine(root, "trace.csv"));
            trace.WriteLine("frame,saved,time,stage,state,beat,performing,club,golferActive,golferAlpha,camX,camY,camZ,ballX,ballY,ballZ");
            log = new StreamWriter(Path.Combine(root, "events.txt"));
            Debug.Log("[FemaleGolf] begin " + root);
        }
        void Note(string s) { string m = $"{saved / 30f:F2}s (saved {saved}, frame {frame}) {s}"; log.WriteLine(m); log.Flush(); Debug.Log("[FemaleGolf] " + m); }
        void Next(string why) { stage++; wait = 0; Note($"stage {stage}: {why} state {game.Current} club {Club}"); }
        void LateUpdate() { if (done || !game) return; try { Step(); } catch (Exception e) { Debug.LogException(e); Finish(1); } }

        void Step()
        {
            var cam = Camera.main; if (cam) { cam.aspect = 16f / 9f; cam.rect = new Rect(0, 0, 1, 1); }
            frame++; wait++;
            if (Environment.GetEnvironmentVariable("FILM_NOBODY") == "1" && Golfer != null && Golfer.Hero != null) { var bd = Golfer.Hero.Part("Body"); if (bd) bd.enabled = false; }
            var s = game.Current;
            record = true;
            switch (stage)
            {
                case 0: // the flyover, as long as it runs by itself (up to 12 s), then the phone's continue
                    if (s == GolfGame.State.Intro && game.PresentationBeatIndex == 0 && wait > 360) game.NativeContinue();
                    if (s == GolfGame.State.Aim) Next("address");
                    if (wait > 1500) throw new TimeoutException("intro");
                    break;
                case 1: // address: 3 s for the waggle, male address stills at 2 s, then a 0.9 s backswing and the drive
                    if (wait == 60) { var c = Camera.main;  }
                    if (wait > 90 && wait <= 117) game.ShowBackswing(.9 * Mathf.SmoothStep(0, 1, (wait - 90) / 27f));
                    if (wait == 124)
                    {
                        var h = game.CurrentHole; double a = h.Tee.HeadingTo(h.Pin) * Math.PI / 180, d = Math.Min(h.Length * .62, 230);
                        var target = game.GreenTarget(5, 14, 7) ?? new CoursePoint(h.Tee.X + Math.Sin(a) * d, h.Tee.D + Math.Cos(a) * d);
                        game.StrikeToward(target); strokes++; Next("drive struck");
                    }
                    break;
                case 2: // the flight, the post-shot watch and the result, until the next address
                    if (Environment.GetEnvironmentVariable("FILM_DRIVE_ONLY") == "1" && wait > 90) { Note("film done after the drive"); record = false; Finish(0); return; }
                    if (wait > 40 && s == GolfGame.State.Aim && strokes >= 2) { Note("film done after the approach"); record = false; Finish(0); return; }
                    else if (wait > 40 && s == GolfGame.State.Aim) { stage = Club == "Putter" ? 5 : 3; wait = 0; Note($"next address, club {Club}"); }
                    else if (wait > 40 && s is GolfGame.State.HoleDone) { stage = 8; wait = 0; Note("holed from off the green"); }
                    if (wait > 1800) throw new TimeoutException("shot");
                    break;
                case 3: // the approach: 1.2 s at address, a 0.8 s backswing, onto the green ~5-9 yd from the pin
                    if (wait > 36 && wait <= 60) game.ShowBackswing(.8 * Mathf.SmoothStep(0, 1, (wait - 36) / 24f));
                    if (wait == 66)
                    {
                        var target = game.GreenTarget(4, 9, 3) ?? game.CurrentHole.Pin;
                        game.StrikeToward(target); strokes++; stage = 2; wait = 0; Note("approach struck");
                    }
                    break;
                case 5: // a putt: the first one aimed just past/short of the hole (a real miss), later ones holed
                    if (wait > 30 && wait <= 50) game.ShowBackswing(.45 * Mathf.SmoothStep(0, 1, (wait - 30) / 20f));
                    if (wait == 56)
                    {
                        putts++; strokes++;
                        if (putts == 1)
                        {
                            var h = game.CurrentHole; var ball = Ball.position; var pin = h.Pin;
                            var at = HoleView.ToCourse(ball); double dx = pin.X - at.X, dd = pin.D - at.D, len = Math.Max(.01, Math.Sqrt(dx * dx + dd * dd));
                            if (len < 2.5) { if (!game.StrikeHolingPutt()) game.StrikeToward(pin); }
                            else game.StrikeToward(new CoursePoint(pin.X - dx / len * 1.1 + dd / len * .7, pin.D - dd / len * 1.1 - dx / len * .7));
                        }
                        else if (!game.StrikeHolingPutt()) game.StrikeToward(game.CurrentHole.Pin);
                        stage = 6; wait = 0; Note($"putt {putts} struck");
                    }
                    break;
                case 6: // the putt rolling: holed -> hole-out, else the next putt
                    if (wait > 40 && s == GolfGame.State.Aim) { stage = 5; wait = 0; Note("putt missed, next putt"); }
                    else if (wait > 20 && s is GolfGame.State.HoleDone or GolfGame.State.RoundDone or GolfGame.State.Intro || wait > 20 && s == GolfGame.State.Result && !string.IsNullOrEmpty(Golfer.Performing) && Golfer.Performing != "Idle")
                    { stage = 8; wait = 0; Note($"holed, state {s} performing {Golfer.Performing}"); }
                    if (wait > 1500) throw new TimeoutException("putt");
                    break;
                case 8: // the hole-out reaction, until it has played and settled (or the round card), 25 s at most
                    var p = Golfer ? Golfer.Performing : null;
                    if (!string.IsNullOrEmpty(p) && p != "Idle" && !sawEmote) { sawEmote = true; Note("hole-out reaction " + p); }
                    if (sawEmote && (string.IsNullOrEmpty(p) || p == "Idle")) idleFrames++;
                    bool gone = s is GolfGame.State.Intro or GolfGame.State.RoundDone;
                    if (idleFrames > 45 || gone && wait > 30 || wait > 750) { Note($"hole-out over: state {s} performing {p}, strokes {strokes}, putts {putts}"); stage = 9; wait = 0; record = false; Save(); FinishFilm(); return; }
                    break;
                default: record = false; StillsStep(); return;
            }
            Save();
        }

        // ---- stills after the film: the game held, the hero standing (male, then female) ----
        int stillStep;
        void StillsStep()
        {
            var g = Golfer; var c = Camera.main; var dir = Path.Combine(root, "stills");
            var gs = game.Current;
            switch (stillStep)
            {   // a fresh round on cliffside, skipped to the tee: the stills stand on the actual course (the finished round has moved on)
                case 0: game.PrepareNativeAddress("cliffside"); game.SetWind(new Wind(0, 0)); game.NativeReady(); game.TryNativePresentation(); stillStep = 1; wait = 0; Note("stills round"); break;
                case 1:
                    if (gs == GolfGame.State.Intro && game.PresentationBeatIndex == 0 && wait > 20) game.NativeContinue();
                    if (gs == GolfGame.State.Aim && wait > 10) { stillStep = 2; wait = 0; }
                    if (wait > 1500) throw new TimeoutException("stills intro");
                    break;
                case 2: if (wait > 30) { game.enabled = false; SetOpaque(g); g.Perform("Idle"); stillStep = 3; wait = 0; } break;
                case 3:
                    if (wait > 40)
                    {
                        ReviewShared.Stills(c, g, dir, "golf_male_idle"); Note("male idle stills");
                        game.enabled = true; GolferStyle.Body = GolferStyle.BodyKind.Female; game.RestyleGolfer(); stillStep = 4; wait = 0; Note("female restyled");
                    }
                    break;
                case 4: if (wait > 60) { ReviewShared.Stills(c, g, dir, "golf_female_address"); Note("female address stills"); game.enabled = false; g.Perform("Idle"); stillStep = 5; wait = 0; } break;
                case 5: if (wait > 40) { ReviewShared.Stills(c, g, dir, "golf_female_idle"); Note("female idle stills"); stillStep = 6; } break;
                default: Finish(0); return;
            }
            wait++;
        }
        static void SetOpaque(GolferView g) { var fade = g ? g.GetComponent<GolferFade>() : null; if (fade) fade.Restore(); }

        void UpdateAngles()
        {
            var g = Golfer; var ballT = Ball; var s = game.Current;
            bool golferOn = g && g.gameObject.activeInHierarchy;
            Vector3 G = golferOn ? g.transform.position : Tee, P = Pin, T = Tee;
            Vector3 ball = ballT && ballT.gameObject.activeInHierarchy ? ballT.position : G;
            var tp = P - T; tp.y = 0; float L = tp.magnitude; var dTP = tp.normalized;
            if (s == GolfGame.State.Aim && golferOn)
            {
                var toPin = P - G; toPin.y = 0; line = toPin.sqrMagnitude > .01f ? toPin.normalized : dTP;
                var toBall = ball - G; toBall.y = 0;
                chest = toBall.magnitude > .15f ? toBall.normalized : Vector3.Cross(Vector3.up, line);
                if (Vector3.Dot(chest, Vector3.Cross(Vector3.up, line)) < -.2f) chest = Vector3.Cross(Vector3.up, line);
                haveChest = true;
            }
            if (!haveChest) { line = dTP; chest = Vector3.Cross(Vector3.up, line); }
            float sc = 1f;
            HandsAngle();
            // 1 side-on wide: up the target line looking back at the golfer (lead-side profile), a little to the chest side
            angles[0].Aim(G + line * 9f + chest * 2.6f + Vector3.up * 1.5f, G + Vector3.up * 1.0f, s == GolfGame.State.Aim ? 1 : .2f); angles[0].Fov = 38;
            // 2 face-on close-up: in front of the chest
            angles[1].Aim(G + chest * 3.3f - line * .25f + Vector3.up * 1.25f, G + Vector3.up * .95f, s == GolfGame.State.Aim ? 1 : .2f); angles[1].Fov = 34;
            // 3 high drone following the ball
            bool flying = s is GolfGame.State.Flight or GolfGame.State.Result;
            var focus = flying ? ball : G; var fl = P - focus; fl.y = 0; var fdir = fl.sqrMagnitude > 1 ? fl.normalized : line;
            angles[2].Aim(focus - fdir * 11f + Vector3.up * 17f, focus, frame < 3 ? 1 : .09f); angles[2].Fov = 40;
            // 4 behind the green looking back at the tee
            var bg = P + dTP * 30f + Vector3.Cross(Vector3.up, dTP) * 11f + Vector3.up * 9f; angles[3].Aim(bg, Vector3.Lerp(P, T, .55f) + Vector3.up * 2f); angles[3].Fov = 34;
            // 5 low chase behind the ball
            var v = (ball - prevBall) * 30f; prevBall = ball;
            if (flying && v.magnitude > 3f) { var vd = v.normalized; angles[4].Aim(ball - vd * 5.5f + Vector3.up * .9f, ball + vd * 2f, .3f); }
            else { var bl = P - ball; bl.y = 0; var bd = bl.sqrMagnitude > .04f ? bl.normalized : line; angles[4].Aim(ball - bd * 3.6f + Vector3.up * .75f, ball + bd * 5f, s == GolfGame.State.Aim ? 1 : .15f); }
            angles[4].Fov = 50;
            // 6 fixed wide establishing: off the side of the hole's middle, high
            if (frame < 2 || establishingSide == 0) establishingSide = PickSide(T, P, dTP, L);
            var M = Vector3.Lerp(T, P, .5f); var side = Vector3.Cross(Vector3.up, dTP) * establishingSide;
            angles[5].Aim(M + side * L * .62f + Vector3.up * L * .33f - dTP * L * .1f, M); angles[5].Fov = 58;
        }
        void HandsAngle()
        {
            var g = Golfer; if (g == null || g.Hero == null || !g.gameObject.activeInHierarchy) return;
            if (!g.Hero.Bones.TryGetValue("LeftHand", out var lh) || !g.Hero.Bones.TryGetValue("RightHand", out var rh)) return;
            var mid = (lh.position + rh.position) * .5f; var side = Vector3.Cross(Vector3.up, line);
            // from the golfer's front-left, close on the grip
            angles[6].Aim(mid + (chest * 1.25f - side * .55f) + Vector3.up * .25f, mid, .35f); angles[6].Fov = 24;
        }
        int establishingSide;
        static int PickSide(Vector3 T, Vector3 P, Vector3 dTP, float L)
        {
            var M = Vector3.Lerp(T, P, .5f);
            foreach (int sgn in new[] { 1, -1 })
            {
                var pos = M + Vector3.Cross(Vector3.up, dTP) * sgn * L * .62f + Vector3.up * L * .33f;
                if (!Physics.Linecast(pos, M + Vector3.up * 3)) return sgn;
            }
            return 1;
        }

        void Save()
        {
            if (!record) return;
            var g = Golfer; var cam = Camera.main;
            UpdateAngles();
            GameCapture.Save(Path.Combine(root, "gameplay", $"f_{saved:D5}.jpg"), 1280, 720);
            foreach (var a in angles) a.Render(cam);
            var fade = g ? g.GetComponent<GolferFade>() : null; float alpha = fade ? fade.Opacity : 1f;
            var b = Ball ? Ball.position : Vector3.zero; var c = cam.transform.position;
            string F(float x) => x.ToString("F2", CultureInfo.InvariantCulture);
            trace.WriteLine(string.Join(",", frame, saved, F(Time.time), stage, game.Current, game.PresentationBeatIndex, g ? g.Performing ?? "" : "", Club, g && g.gameObject.activeInHierarchy, F(alpha), F(c.x), F(c.y), F(c.z), F(b.x), F(b.y), F(b.z)));
            DumpBones();
            saved++;
        }
        void DumpBones()
        {
            var g = Golfer; if (g == null || g.Hero == null) return;
            var sb = new System.Text.StringBuilder(); sb.Append(frame).Append(',').Append(saved).Append(',').Append(stage);
            foreach (var n in BoneNames)
            {
                if (!g.Hero.Bones.TryGetValue(n, out var t)) { sb.Append(",0,0,0,1,0,0,0"); continue; }
                var rl = Quaternion.Inverse(g.Hero.Root.transform.rotation) * t.rotation; var pl = g.Hero.Root.transform.InverseTransformPoint(t.position);
                sb.Append(',').Append(rl.x.ToString("F5")).Append(',').Append(rl.y.ToString("F5")).Append(',').Append(rl.z.ToString("F5")).Append(',').Append(rl.w.ToString("F5"))
                  .Append(',').Append(pl.x.ToString("F4")).Append(',').Append(pl.y.ToString("F4")).Append(',').Append(pl.z.ToString("F4"));
            }
            boneLog.WriteLine(sb.ToString());
        }
        void FinishFilm() { trace?.Flush(); Note($"film done: {saved} frames"); }
        void Finish(int code)
        {
            if (done) return; done = true; trace?.Dispose(); boneLog?.Dispose();
            Note($"done code {code} frames {frame} saved {saved} state {game.Current}"); log?.Dispose();
            FemaleGolfFilm.End(code);
        }
    }
}
#endif
