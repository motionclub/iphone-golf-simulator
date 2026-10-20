#if UNITY_EDITOR
// Chat E (course-fx) proof harness: copied into ~/unity-clones/course-fx/Assets/Editor/CFXLocal by film.sh.
// 1) Rock audit: loads every hole of the three courses and logs each rock's gap to the ground before/after the
//    RockGrounding snap, the course model's ROCK nodes as they end up, and the dream gates' floating rocks.
// 2) Films from the gameplay cameras: the tee view of the flag on several holes, a pad shot charged and spent (hole 7),
//    a fairway iron (impact), the bullseye (hole 20) and the Crater's pad (hole 10).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class CourseFxFilm
    {
        const string Flag = "CourseFxFilm.Active";
        static CourseFxFilm() { EditorApplication.update += Boot; }
        public static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;
        public static void Run() { EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity"); SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true; }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<CourseFxRecorder>()) return;
            var g = Object.FindFirstObjectByType<GolfGame>(); if (!g || !HoleView.Current) return;
            try { new GameObject("Course fx film").AddComponent<CourseFxRecorder>().Begin(g); } catch (Exception e) { Debug.LogException(e); End(1); }
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    [DefaultExecutionOrder(10000)]
    public sealed class CourseFxRecorder : MonoBehaviour
    {
        (double clock, double plan)? pending;
        GolfGame game; string dir; IEnumerator<int> script; bool done; double toBall = .3;
        static string F(double v) => v.ToString("F3", CultureInfo.InvariantCulture);
        static void Log(string s) => Debug.Log("[CourseFxFilm] " + s);

        public void Begin(GolfGame g)
        {
            game = g;
            dir = Path.GetFullPath(CourseFxFilm.Env("FILM_OUT", "../work/course-fx/proof/run")); Directory.CreateDirectory(dir);
            PresentationPolicy.Configure("full", false, true, false);
            Time.captureFramerate = 30; UnityEngine.Random.InitState(1019);
            game.Demo = true; game.InstantReplays = false;
            RockGrounding.Recording = true;
            game.PrepareNativeAddress("cliffside");
            game.SetWind(new Wind(0, 0));
            game.NativeReady(); game.TryNativePresentation();
            script = Script();
            Log("begin " + dir + " snap " + RockGrounding.Snap);
        }

        void LateUpdate()
        {
            if (done || !game) return;
            var cam = Camera.main; if (cam) { cam.aspect = 16f / 9f; cam.rect = new Rect(0, 0, 1, 1); }
            try { if (!script.MoveNext()) Finish(0); } catch (Exception e) { Debug.LogException(e); Finish(1); }
        }

        void Shot(string name) => GameCapture.Save(Path.Combine(dir, name + ".jpg"), 960, 540);

        /// Wait (frames) until the game is at address; skips any opening the way the phone's button does.
        IEnumerable<int> ToAim(int limit = 1800)
        {
            for (int f = 0; f < limit; f++)
            {
                if (game.Current == GolfGame.State.Aim && f > 20) yield break;
                if (game.Current == GolfGame.State.Intro && f % 45 == 44) game.NativeContinue();
                if (game.Current is GolfGame.State.HoleDone && f % 60 == 59) game.NativeContinue();
                yield return f;
            }
            throw new TimeoutException("aim");
        }

        IEnumerable<int> Hole(int number)
        {
            if (game.CurrentHole == null || game.CurrentHole.Number != number) game.JumpToHole(number);
            foreach (var f in ToAim()) yield return f;
            game.SetWind(new Wind(0, 0));
            for (int i = 0; i < 20; i++) yield return i;
        }

        /// Where the pin is and what of it draws, from the camera at address (why a flag might not show).
        void PinDiag(int n)
        {
            var view = HoleView.Current; var cam = Camera.main; if (!view || !cam || !view.Flag) { Log($"pin {n}: none"); return; }
            var root = view.Flag.parent ? view.Flag.parent : view.Flag;
            var sp = cam.WorldToScreenPoint(root.position);
            Log($"pin {n}: root {root.name} at {root.position} scale {root.localScale} active {root.gameObject.activeInHierarchy} screen ({F(sp.x)},{F(sp.y)},{F(sp.z)}) of {cam.pixelWidth}x{cam.pixelHeight} far {cam.farClipPlane}");
            foreach (var r in root.GetComponentsInChildren<Renderer>(true))
                Log($"  {r.name} {r.GetType().Name} on {r.enabled} active {r.gameObject.activeInHierarchy} layer {r.gameObject.layer} cull {cam.layerCullDistances[r.gameObject.layer]} visible {r.isVisible} bounds {r.bounds.center} {r.bounds.size} mat {(r.sharedMaterial ? r.sharedMaterial.shader.name : "-")}");
            var beacon = root.GetComponent<FlagBeacon>(); Log($"  beacon {(beacon ? "yes" : "no")}");
            var top = cam.WorldToScreenPoint(root.position + Vector3.up * 2.4f * root.lossyScale.y);
            Log($"  pole top on screen ({F(top.x)},{F(top.y)}) ground under camera ray: {(Physics.Linecast(cam.transform.position, root.position + Vector3.up * 1.5f, out var hit) ? hit.collider.name + " at " + F(hit.distance) : "clear")}");
        }

        Mover Find(MoverKind kind) => game.CurrentHole.Movers?.All.FirstOrDefault(m => m.Kind == kind);

        /// Strike at `target` (swinging from address as the phone does), filming every frame through contact and
        /// every other frame after, until the ball is at rest and the game back at address (or the hole is done).
        IEnumerable<int> Strike(string label, CoursePoint target, int seconds = 12, CourseShot planned = null)
        {
            var seq = Path.Combine(dir, label); Directory.CreateDirectory(seq);
            for (int w = 0; w < 28; w++) { game.ShowBackswing(.9 * Mathf.SmoothStep(0, 1, w / 27f)); yield return w; }
            // the movers' clock is set now, after the backswing's frames (it runs on while the club goes back)
            if (pending.HasValue) { game.CurrentHole.Movers.SetClock(pending.Value.clock); game.CurrentHole.Movers.PhaseAtLaunch = pending.Value.plan; pending = null; }
            var mv = game.CurrentHole.Movers; double c0 = mv?.Clock ?? 0;
            if (planned != null)
            {
                // the strike the plan made with the movers out of the way, played as StrikeToward plays its own
                const System.Reflection.BindingFlags Any = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public;
                var type = typeof(GolfGame);
                type.GetField("heading", Any).SetValue(game, planned.Heading);
                type.GetField("aimedByPlayer", Any).SetValue(game, true);
                type.GetMethod("UpdateAimVisuals", Any).Invoke(game, null);
                type.GetField("plannedShot", Any).SetValue(game, true);
                type.GetMethod("OnImpact", Any).Invoke(game, new object[] { new GolfArcade.Swing.SwingImpact { Power = planned.Power, Backswing = 0.8, Commit = 1.2, TempoSeconds = 1.0, DownswingSeconds = 0.25 } });
            }
            else game.StrikeToward(target);
            if (mv != null) { toBall = mv.PhaseAtLaunch - c0; }
            var shot = game.LastShot;
            Log($"{label}: strike toward ({F(target.X)},{F(target.D)}) toBall {F(toBall)} rest ({F(shot.Rest.X)},{F(shot.Rest.D)}) lie {shot.Lie} knocks [{string.Join(",", shot.Knocks.Select(k => k.Kind + "@" + F(k.Time)))}]");
            int saved = 0;
            for (int f = 0; f < seconds * 30; f++)
            {
                if (f < 45 || f % 2 == 0)
                {
                    // every sixth saved frame also without what this chat added about the hole (the "before" twin)
                    var movers = HoleView.Current ? HoleView.Current.transform.Find("Movers") : null;
                    if (movers && saved % 6 == 0 && game.CurrentHole.Movers != null && game.CurrentHole.Movers.All.Any(m => m.Kind is MoverKind.Launchpad or MoverKind.Target))
                    {
                        var hidden = new List<GameObject>();
                        foreach (Transform t in movers) if (t.name.StartsWith("Launchpad") || t.name.StartsWith("Target")) { t.gameObject.SetActive(false); hidden.Add(t.gameObject); }
                        GameCapture.Save(Path.Combine(seq, $"bare_{saved:D4}.jpg"), 960, 540);
                        foreach (var g in hidden) g.SetActive(true);
                    }
                    GameCapture.Save(Path.Combine(seq, $"f_{saved++:D4}.jpg"), 960, 540);
                }
                if (f > 60 && game.Current is GolfGame.State.Aim or GolfGame.State.HoleDone or GolfGame.State.RoundDone or GolfGame.State.Intro) break;
                yield return f;
            }
            Log($"{label}: {saved} frames, state {game.Current}");
        }

        /// Set the movers' clock so mover `m` is `cycle` of the way round when a shot at `target` reaches `meet`. The game's
        /// own aim (PlanStrike) runs before the strike against the movers as they are at PhaseAtLaunch, and steers away
        /// from a charged pad or the board (hitting one moves the landing), so it plans with them at `planCycle`.
        /// The shot the game would play at `target` with nothing moving about the hole (so it does not steer round them).
        CourseShot Bare(CoursePoint target)
        {
            var hole = game.CurrentHole; var mv = hole.Movers;
            hole.Movers = null;
            try { return game.PlanFor(target); } finally { hole.Movers = mv; }
        }

        CourseShot SetTiming(Mover m, CoursePoint target, double cycle, Func<CourseShot, double> meet, double planCycle)
        {
            var mv = game.CurrentHole.Movers;
            var plan = Bare(target);
            double t = meet(plan), now = m.CycleAt(0);
            double p = ((cycle - now - t / m.Period) % 1 + 1) % 1 * m.Period + 4 * m.Period;
            pending = (p - toBall, p + (planCycle - cycle) * m.Period);
            Log($"timing {m.Kind}: meets at {F(t)} s, phase at launch {F(p)}, clock {F(p - toBall)}, bare landing ({F(plan.Landing.X)},{F(plan.Landing.D)}) power {F(plan.Power)}");
            return plan;
        }

        IEnumerator<int> Script()
        {
            foreach (var f in ToAim()) yield return f;
            // ---- 1: the rock audit over every hole
            var report = new StreamWriter(Path.Combine(dir, "rocks.csv"));
            report.WriteLine("hole,source,x,y,z,before,after");
            var gates = new StreamWriter(Path.Combine(dir, "gates.csv"));
            gates.WriteLine("hole,dream_hazard,floating_rocks_before,floating_rock_objects_now,movers");
            foreach (var course in Course.Course.All())
                foreach (var h in course.Holes)
                {
                    if (CourseFxFilm.Env("FILM_AUDIT", "1") == "0") break;
                    RockGrounding.Audit.Clear();
                    game.JumpToHole(h.Number);
                    for (int i = 0; i < 40; i++) yield return i;
                    foreach (var e in RockGrounding.Audit)
                        report.WriteLine($"{e.Hole},{e.Source},{F(e.At.x)},{F(e.At.y)},{F(e.At.z)},{F(e.Before)},{F(e.After)}");
                    // the model's rocks as they stand now, measured again
                    var view = HoleView.Current;
                    foreach (var mf in view.GetComponentsInChildren<MeshFilter>(true))
                        if (RockGrounding.IsModelRock(mf.name) && mf.sharedMesh && mf.gameObject.activeInHierarchy)
                        {
                            float gap = RockGrounding.Clearance(mf.sharedMesh, mf.transform.localToWorldMatrix);
                            report.WriteLine($"{h.Number},final {mf.name},{F(mf.transform.position.x)},{F(mf.transform.position.y)},{F(mf.transform.position.z)},{F(gap)},{F(gap)}");
                        }
                    var hole = game.CurrentHole;
                    string kinds = hole.Dream == null ? "" : string.Join(" ", hole.Dream.Hazards.Select(z => z.Kind.ToString()));
                    int before = hole.Dream == null ? 0 : hole.Dream.Hazards.Count(z => z.Kind is DreamHazardKind.RockGate or DreamHazardKind.BasaltGate) * 2;
                    int now = Object.FindObjectsByType<Transform>(FindObjectsSortMode.None).Count(t => t.name == "Solid floating rock" && t.gameObject.activeInHierarchy);
                    string movers = hole.Movers == null ? "" : string.Join(" ", hole.Movers.All.Select(m => m.Kind.ToString()));
                    gates.WriteLine($"{h.Number},{kinds},{before},{now},{movers}");
                    Log($"audit hole {h.Number}: {RockGrounding.Audit.Count} rock checks, gate rocks before {before} now {now}, movers [{movers}]");
                }
            report.Dispose(); gates.Dispose();
            RockGrounding.Recording = false;

            // ---- 2: the flag from the tee, in the game's own address camera
            bool only10 = CourseFxFilm.Env("FILM_ONLY", "") == "10";
            foreach (int n in only10 ? new int[0] : new[] { 8, 13, 22, 15 })
            {
                foreach (var f in Hole(n)) yield return f;
                Shot($"flag_tee_h{n}"); PinDiag(n);
            }

            // ---- 3: hole 7, the launchpad: charged, then spent; then an iron off the fairway for the impact
            if (!only10) foreach (var f in Hole(7)) yield return f;
            if (!only10) Shot("flag_tee_h7");
            var pad = only10 ? null : Find(MoverKind.Launchpad);
            if (pad != null)
            {
                var c = new CoursePoint(pad.At(0).x, pad.At(0).d);
                Log($"hole 7 pad goal lie {game.CurrentHole.LieAt(pad.Goal)}");
                Log($"hole 7 pad at ({F(c.X)},{F(c.D)}) goal ({F(pad.Goal.X)},{F(pad.Goal.D)})");
                double Meet(CourseShot s) { var k = s.Knocks.FirstOrDefault(z => z.Kind == ObstacleKind.Launchpad); return k.Kind == ObstacleKind.Launchpad ? k.Time : s.LandingTime; }
                var plan = SetTiming(pad, c, .25, Meet, .75);
                foreach (var f in Strike("h7_pad_charged", c, 12, plan)) yield return f;
                foreach (var f in ToAim()) yield return f;
                Shot("h7_after_charged");
                game.DropBall(game.CurrentHole.Tee);
                foreach (var f in ToAim(200)) yield return f;
                plan = SetTiming(pad, c, .75, Meet, .75);
                foreach (var f in Strike("h7_pad_spent", c, 12, plan)) yield return f;
                foreach (var f in ToAim()) yield return f;
                // from where the fizzle left it (on the fairway): an iron at the green, for the divot and the flash
                var green = game.GreenTarget(5, 18, 7) ?? game.CurrentHole.Pin;
                foreach (var f in Strike("h7_fairway_iron", green, 8)) yield return f;
            }
            else Log("hole 7: no launchpad placed");

            // ---- 4: hole 20, the bullseye
            if (!only10) foreach (var f in Hole(20)) yield return f;
            if (!only10) Shot("flag_tee_h20");
            var target = only10 ? null : Find(MoverKind.Target);
            if (target != null)
            {
                var a = target.RailFrom; var b = target.RailTo; var mid = new CoursePoint((a.X + b.X) / 2, (a.D + b.D) / 2);
                var tee = game.CurrentHole.Tee; double aim = tee.HeadingTo(mid) * Math.PI / 180;
                // the aim point past the board whose flight passes closest to the board's height there
                CoursePoint best = mid; double bestMiss = double.MaxValue, bestT = 0;
                for (double past = 0; past <= 140; past += 5)
                {
                    var p = new CoursePoint(mid.X + Math.Sin(aim) * past, mid.D + Math.Cos(aim) * past);
                    var plan = Bare(p);
                    double tc = 0, nearest = double.MaxValue;
                    for (double t = 0; t < plan.LandingTime; t += .01) { var w = plan.WorldAt(t, HoleView.GroundHeight); double dd = Math.Sqrt((w.x - mid.X) * (w.x - mid.X) + (w.d - mid.D) * (w.d - mid.D)); if (dd < nearest) { nearest = dd; tc = t; } }
                    double miss = Math.Abs(plan.WorldAt(tc, HoleView.GroundHeight).y - target.Height) + nearest;
                    if (miss < bestMiss) { bestMiss = miss; best = p; bestT = tc; }
                }
                Log($"hole 20 target rail ({F(a.X)},{F(a.D)})-({F(b.X)},{F(b.D)}) board y {F(target.Height)}: aim ({F(best.X)},{F(best.D)}) miss {F(bestMiss)} at {F(bestT)} s");
                double crossAt = bestT;
                var plan20 = SetTiming(target, best, .25, _ => crossAt, 0);
                foreach (var f in Strike("h20_bullseye", best, 12, plan20)) yield return f;
            }
            else Log("hole 20: no target placed");

            // ---- 5: hole 10, the Crater's pad
            foreach (var f in Hole(10)) yield return f;
            Shot("flag_tee_h10");
            var pad10 = Find(MoverKind.Launchpad);
            if (pad10 != null)
            {
                var c = new CoursePoint(pad10.At(0).x, pad10.At(0).d);
                Log($"hole 10 pad at ({F(c.X)},{F(c.D)}) goal ({F(pad10.Goal.X)},{F(pad10.Goal.D)}) lie {game.CurrentHole.LieAt(pad10.Goal)}");
                double Meet(CourseShot s) { var k = s.Knocks.FirstOrDefault(z => z.Kind == ObstacleKind.Launchpad); return k.Kind == ObstacleKind.Launchpad ? k.Time : s.LandingTime; }
                var plan10 = SetTiming(pad10, c, .25, Meet, .75);
                foreach (var f in Strike("h10_pad_charged", c, 12, plan10)) yield return f;
            }
            Log("script done");
        }

        void Finish(int code)
        {
            if (done) return; done = true;
            Log($"done code {code}");
            CourseFxFilm.End(code);
        }
    }
}
#endif
