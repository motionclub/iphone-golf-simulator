using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// HAND CLEARANCE in the real game (work/hand-clearance): films a live AI tennis rally + three emotes, or a live golf tee
    /// shot, at 1920x1080 / 30 fps through the gameplay camera, and measures the clearance pass of every hero on screen each
    /// frame (HeroPoseSafety -> HeroClearance.LastMs). Writes frames/f_00000.jpg, cost.csv, cost.json.
    ///   -executeMethod GolfArcade.EditorTools.HeroClearanceFilm.Tennis   (FILM_OUT, FILM_SECONDS=20, FILM_EMOTES=EmoteSlump,EmoteShock,EmoteFistPump)
    ///   -executeMethod GolfArcade.EditorTools.HeroClearanceFilm.Golf     (FILM_OUT)
    [InitializeOnLoad]
    public static class HeroClearanceFilm
    {
        const string Flag = "HeroClearanceFilm"; const int W = 1920, H = 1080;
        static IEnumerator script; static int lastFrame = -1; static string kind;
        static HeroClearanceFilm() { EditorApplication.update += Tick; }
        static string Env(string k, string d) { var v = Environment.GetEnvironmentVariable(k); return string.IsNullOrEmpty(v) ? d : v; }
        public static void Tennis() => Start("tennis", "Assets/Scenes/Tennis.unity");
        public static void Golf() => Start("golf", "Assets/Scenes/Golf.unity");
        /// The first tee shot of a round, every frame from the start (FILM_TRACKS=0: no baked tracks; FILM_CLEARANCE=0: no hand clearance at all).
        public static void GolfFirstShot() => Start("golffirst", "Assets/Scenes/Golf.unity");
        static void Start(string k, string scene)
        {
            EditorUtility.audioMasterMute = true;
            script = null; lastFrame = -1; SessionState.SetString(Flag, k);
            EditorSceneManager.OpenScene(scene); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            kind = SessionState.GetString(Flag, "");
            if (kind == "" || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount; EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            try
            {
                if (script == null)
                {
                    if (kind == "tennis") { var g = Object.FindFirstObjectByType<TennisGame>(); if (!g || !g.Initialized) return; script = TennisFilm(g); }
                    else { var g = Object.FindFirstObjectByType<GolfGame>(); if (!g) return; script = kind == "golffirst" ? GolfFirst(g) : GolfFilm(g); }
                }
                if (!script.MoveNext()) Done(0);
            }
            catch (Exception e) { Debug.LogException(e); Done(1); }
        }
        static void Done(int code)
        {
            SessionState.SetString(Flag, ""); Time.captureFramerate = 0;
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }

        // ---------------------------------------------------------------- cost bookkeeping
        sealed class Cost { public string who; public List<float> ms = new List<float>(); public int frames; }
        static HeroPoseSafety SafetyOf(object owner, string field) =>
            owner?.GetType().GetField(field, BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(owner) as HeroPoseSafety;
        static void Record(Cost c, HeroPoseSafety s, StringBuilder csv, int frame)
        {
            if (s?.clearance == null || !s.clearance.Ready) return;
            float ms = (float)s.LastMs; c.ms.Add(ms); c.frames++;   // the whole pass: track + residual
            var ph = s.clearance.Phase; int ev = HeroClearance.EvalCalls, bu = HeroClearance.Builds; HeroClearance.EvalCalls = 0; HeroClearance.Builds = 0;
            csv.AppendLine($"{frame},{c.who},{ms.ToString("0.####", CultureInfo.InvariantCulture)},{(s.ResidualDepth * 1000).ToString("0.##", CultureInfo.InvariantCulture)},{ph.refresh.ToString("0.####", CultureInfo.InvariantCulture)},{ph.translate.ToString("0.####", CultureInfo.InvariantCulture)},{ph.swivel.ToString("0.####", CultureInfo.InvariantCulture)},{ph.prop.ToString("0.####", CultureInfo.InvariantCulture)},{ph.lookups},{ev},{bu}");
        }
        static string Summary(IEnumerable<Cost> costs)
        {
            string P(List<float> v, float q) { if (v.Count == 0) return "0"; var s = v.OrderBy(x => x).ToList(); return s[Mathf.Clamp((int)(q * (s.Count - 1)), 0, s.Count - 1)].ToString("0.####", CultureInfo.InvariantCulture); }
            return "{" + string.Join(",", costs.Select(c => $"\"{c.who}\":{{\"frames\":{c.frames},\"meanMs\":{(c.ms.Count == 0 ? 0 : c.ms.Average()).ToString("0.####", CultureInfo.InvariantCulture)},\"p50Ms\":{P(c.ms, .5f)},\"p95Ms\":{P(c.ms, .95f)},\"maxMs\":{P(c.ms, 1)}}}")) + $",\"resolution\":\"{W}x{H}\",\"unity\":\"{Application.unityVersion}\",\"device\":\"{SystemInfo.deviceModel} / {SystemInfo.processorType}\"}}";
        }
        static void Shot(string dir, ref int n)
        {
            if (GameCapture.Save(Path.Combine(dir, "frames", $"f_{n:00000}.jpg"), W, H) == null) throw new InvalidOperationException("capture failed");
            n++;
        }

        // ---------------------------------------------------------------- tennis: a live rally, then three emotes
        static IEnumerator TennisFilm(TennisGame game)
        {
            string dir = Path.GetFullPath(Env("FILM_OUT", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "hand-clearance-work/film/tennis")));
            Directory.CreateDirectory(Path.Combine(dir, "frames"));
            Time.captureFramerate = 60; TennisGame.AutoPlayTimingJitter = .20f;
            game.ManualSimulation = false; game.AutoPlay = false; game.NativeControlled = true; game.SetControllerSetup(false);
            game.GetComponent<TennisPresentation>()?.Finish();
            game.Refeed();
            for (int i = 0; i < 30; i++) yield return null;
            game.GameplayCamera.aspect = W / (float)H;
            game.AutoPlayLean = true; game.AutoPlay = true;
            var pd = game.Player.GetComponentInChildren<HeroTennisDriver>(); var od = game.Opponent.GetComponentInChildren<HeroTennisDriver>();
            var costs = new[] { new Cost { who = "player" }, new Cost { who = "opponent" } };
            var csv = new StringBuilder("frame,hero,ms,residualMm,refresh,translate,swivel,prop,lookups,evals,builds\n"); int n = 0;
            int seconds = int.Parse(Env("FILM_SECONDS", "20"));
            for (int tick = 0; tick < seconds * 60; tick++)
            {
                yield return null;
                game.GameplayCamera.aspect = W / (float)H;
                Record(costs[0], SafetyOf(pd, "poseSafety"), csv, tick); Record(costs[1], SafetyOf(od, "poseSafety"), csv, tick);
                if (tick % 2 == 1) Shot(dir, ref n);
            }
            // emotes, live through the driver (as after a point)
            game.AutoPlay = false;
            foreach (var name in Env("FILM_EMOTES", "EmoteSlump,EmoteShock,EmoteFistPump").Split(','))
            {
                var clip = (HeroTennisDriver.Clip)Enum.Parse(typeof(HeroTennisDriver.Clip), name);
                typeof(TennisGame).GetProperty("Flow").GetSetMethod(true).Invoke(game, new object[] { TennisGame.Phase.PointOver });
                typeof(TennisGame).GetField("resetTimer", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(game, 1e6f);
                pd.ResetForPoint();
                for (int i = 0; i < 20; i++) yield return null;
                // the hero may still be finishing a swing from the rally: try every frame until it is free
                bool started = false;
                for (int w = 0; w < 360 && !(started = pd.PlayEmote(clip)); w++) yield return null;
                if (!started) throw new Exception("cannot play " + clip);
                int frames = Mathf.CeilToInt((pd.EmoteDuration(clip) + .3f) * 60);
                for (int f = 0; f < frames; f++)
                {
                    yield return null;
                    Record(costs[0], SafetyOf(pd, "poseSafety"), csv, 100000 + f);
                    if (f % 2 == 1) Shot(dir, ref n);
                }
            }
            File.WriteAllText(Path.Combine(dir, "cost.csv"), csv.ToString());
            File.WriteAllText(Path.Combine(dir, "cost.json"), Summary(costs));
            Debug.Log("[HeroClearanceFilm] tennis " + Summary(costs) + " frames " + n);
            if (Env("FILM_BAKE", "0") == "1") { HeroClearanceBake.Check(Path.Combine(dir, "bake"), true); Debug.Log("[HeroClearanceFilm] bake check written"); }
        }

        // ---------------------------------------------------------------- golf: a live tee shot
        static IEnumerator GolfFirst(GolfGame game)
        {
            string dir = Path.GetFullPath(Env("FILM_OUT", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "hand-clearance-work/film/golffirst")));
            Directory.CreateDirectory(Path.Combine(dir, "frames"));
            HeroClearanceTracks.Enabled = Env("FILM_TRACKS", "1") == "1"; HeroPoseSafety.Disabled = Env("FILM_CLEARANCE", "1") != "1";
            var body = Env("FILM_BODY", ""); if (body.Length > 0) GolfArcade.Game.GolferStyle.Body = body == "female" ? GolfArcade.Game.GolferStyle.BodyKind.Female : GolfArcade.Game.GolferStyle.BodyKind.Male;
            Time.captureFramerate = 60; Time.timeScale = 1; UnityEngine.Random.InitState(3108);
            game.Demo = true; game.InstantReplays = false; game.ChooseHoles(0); game.Play();
            var csv = new StringBuilder("tick,state,phase,clip,fade,hipsYaw,hipsPitch,hipsRoll,spineYaw,spinePitch,spineRoll,chestYaw,chestPitch,chestRoll,coverage,applied,ms\n"); int n = 0, tick = 0;
            var gf = typeof(GolfGame).GetField("golfer", BindingFlags.Instance | BindingFlags.NonPublic);
            Vector3 Rel(Transform b, Transform r) { var q = Quaternion.Inverse(r.rotation) * b.rotation; var e = q.eulerAngles; return new Vector3(Mathf.DeltaAngle(0, e.y), Mathf.DeltaAngle(0, e.x), Mathf.DeltaAngle(0, e.z)); }
            string F3(Vector3 v) => $"{v.x:0.0},{v.y:0.0},{v.z:0.0}";
            void Frame()
            {
                var cam = Camera.main; if (cam) { cam.aspect = W / (float)H; cam.rect = new Rect(0, 0, 1, 1); }
                var view = gf?.GetValue(game); var vt = view?.GetType();
                var model = vt?.GetField("modelGo", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(view) as GameObject;
                var safety = SafetyOf(view, "poseSafety");
                string line = $"{tick},{game.Current},{vt?.GetField("phase", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(view)},{vt?.GetField("clipName", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(view)},{vt?.GetField("fade", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(view)}";
                var look = model ? model.GetComponentInParent<MatchHeroLook>() ?? model.GetComponentInChildren<MatchHeroLook>() : null;
                if (look && model)
                {
                    var r = model.transform;
                    line += "," + F3(Rel(look.Bone(HumanBodyBones.Hips), r)) + "," + F3(Rel(look.Bone(HumanBodyBones.Spine), r)) + "," + F3(Rel(look.Bone(HumanBodyBones.UpperChest) ? look.Bone(HumanBodyBones.UpperChest) : look.Bone(HumanBodyBones.Chest), r));
                    line += $",{(safety?.Tracks != null ? safety.Tracks.Coverage : -1):0.00},{(safety?.Tracks != null ? safety.Tracks.Applied : -1)},{(safety != null ? safety.LastMs : 0):0.000}";
                }
                csv.AppendLine(line);
                if (tick % 2 == 0) Shot(dir, ref n);
                tick++;
            }
            // from the first frame: the round's start (intro / flyover), the walk-in, address, the backswing
            for (int i = 0; i < 900 && game.Current != GolfGame.State.Aim; i++) { yield return null; Frame(); }
            for (int i = 0; i < 90; i++) { yield return null; Frame(); }
            for (int i = 1; i <= 54; i++) { game.ShowBackswing(.9 * Mathf.SmoothStep(0, 1, i / 54f)); yield return null; Frame(); }
            var target = game.GreenTarget(5, 18, 7);
            if (!target.HasValue) { var h = game.CurrentHole; double d = Math.Min(h.Length * .7, 195), a = h.Tee.HeadingTo(h.Pin) * Math.PI / 180; target = new GolfArcade.Course.CoursePoint(h.Tee.X + Math.Sin(a) * d, h.Tee.D + Math.Cos(a) * d); }
            game.StrikeToward(target.Value);
            for (int i = 0; i < 120; i++) { yield return null; Frame(); }
            File.WriteAllText(Path.Combine(dir, "pose.csv"), csv.ToString());
            Debug.Log($"[HeroClearanceFilm] golf first shot: {tick} frames, {n} images, tracks {HeroClearanceTracks.Enabled}, clearance {!HeroPoseSafety.Disabled}");
        }

        static IEnumerator GolfFilm(GolfGame game)
        {
            string dir = Path.GetFullPath(Env("FILM_OUT", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "hand-clearance-work/film/golf")));
            Directory.CreateDirectory(Path.Combine(dir, "frames"));
            Time.captureFramerate = 60; Time.timeScale = 1; UnityEngine.Random.InitState(3108);
            game.Demo = true; game.InstantReplays = false; game.ChooseHoles(0); game.Play();
            var hole = Env("FILM_HOLE", ""); if (hole.Length > 0) { game.JumpToHole(int.Parse(hole)); game.DropBall(game.CurrentHole.Tee); }   // default: the round's first hole (numbers are per course)
            var cost = new Cost { who = "golfer" }; var csv = new StringBuilder("frame,hero,ms,residualMm,refresh,translate,swivel,prop,lookups,evals,builds\n"); int n = 0;
            object view = null;
            for (int wait = 0; wait < 600 && game.Current != GolfGame.State.Aim; wait++) yield return null;
            for (int i = 0; i < 60; i++) yield return null;
            view = typeof(GolfGame).GetField("golfer", BindingFlags.Instance | BindingFlags.NonPublic)?.GetValue(game);
            int tick = 0;
            void Frame() { var cam = Camera.main; if (cam) { cam.aspect = W / (float)H; cam.rect = new Rect(0, 0, 1, 1); } Record(cost, SafetyOf(view, "poseSafety"), csv, tick); if (tick % 2 == 1) Shot(dir, ref n); tick++; }
            for (int i = 0; i < 40; i++) { yield return null; Frame(); }
            for (int i = 1; i <= 54; i++) { game.ShowBackswing(.9 * Mathf.SmoothStep(0, 1, i / 54f)); yield return null; Frame(); }
            for (int i = 0; i < 12; i++) { yield return null; Frame(); }
            var target = game.GreenTarget(5, 18, 7);
            if (!target.HasValue) { var h = game.CurrentHole; double d = Math.Min(h.Length * .7, 195), a = h.Tee.HeadingTo(h.Pin) * Math.PI / 180; target = new GolfArcade.Course.CoursePoint(h.Tee.X + Math.Sin(a) * d, h.Tee.D + Math.Cos(a) * d); }
            game.StrikeToward(target.Value);
            for (int i = 0; i < 150; i++) { yield return null; Frame(); }
            File.WriteAllText(Path.Combine(dir, "cost.csv"), csv.ToString());
            File.WriteAllText(Path.Combine(dir, "cost.json"), Summary(new[] { cost }));
            Debug.Log("[HeroClearanceFilm] golf " + Summary(new[] { cost }) + " frames " + n);
        }
    }
}
