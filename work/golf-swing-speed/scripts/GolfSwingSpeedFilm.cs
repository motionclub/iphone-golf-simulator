#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
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
using Q = System.Numerics.Quaternion;
using V3 = System.Numerics.Vector3;

namespace GolfArcade.EditorTools
{
    /// GOLF SWING SPEED film (APFS clone ONLY). Plays the golfer's swing on Cliffside hole 1 through the PHONE path the
    /// device build uses: PrepareNativeAddress -> NativeReady -> NativeStartSwing(grip) -> a stream of 100 Hz phone motion
    /// samples into GolfGame.NativeMotion (the detector fires Load / downswing -> GolferView.Strike() / impact -> Launch ->
    /// Strike(atImpact)). The phone swing is synthetic: a club-like turn about the phone's X axis with a chosen downswing time.
    /// Mode "touch" plays the old SwingFilm path instead (OnLoad + StrikeToward, NativeControlled off) = replays / touch / TV.
    ///   GSS_OUT=<dir> GSS_SWINGS=male:Driver:motion:0.25,female:Iron:touch GSS_VIEWS=game,faceon,dtl ("none" = trace only)
    ///   GSS_TRACKS=0 or a 5th field 'notracks' (hand-clearance baked tracks off)   GSS_BACK=0.80 (phone backswing seconds)
    /// Output: <dir>/<tag>/<view>_#####.jpg, trace.csv (per frame), events.txt, summary.txt
    [InitializeOnLoad]
    public static class GolfSwingSpeedFilm
    {
        const string Flag = "GolfSwingSpeedFilm";
        static IEnumerator script; static int lastFrame = -1;
        static GolfSwingSpeedFilm() { EditorApplication.update += Tick; }
        static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;
        public static void Run()
        {
            script = null; lastFrame = -1;
            EditorUtility.audioMasterMute = true;
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            EditorUtility.audioMasterMute = true;
            if (script == null) { var g = Object.FindFirstObjectByType<GolfGame>(); if (!g) return; script = All(g); }
            try { if (!script.MoveNext()) Done(0); } catch (Exception e) { Debug.LogException(e); Done(1); }
        }
        static void Done(int c)
        {
            SessionState.SetBool(Flag, false); Time.captureFramerate = 0; Time.timeScale = 1;
            if (Application.isBatchMode) EditorApplication.Exit(c); else EditorApplication.isPlaying = false;
        }
        static string F(double x) => x.ToString("0.00000", CultureInfo.InvariantCulture);
        static string V(Vector3 v) => F(v.x) + ";" + F(v.y) + ";" + F(v.z);

        static void Shot(Camera cam, string path, Vector3 from, Vector3 look, float fov, int w, int h)
        {
            var hidden = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.enabled && c.renderMode != RenderMode.WorldSpace).ToList();
            foreach (var c in hidden) c.enabled = false;
            var p = cam.transform.position; var r = cam.transform.rotation; var f = cam.fieldOfView; var a = cam.aspect;
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(look - from, Vector3.up)); cam.fieldOfView = fov; cam.aspect = w / (float)h;
            var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 4);
            var prev = cam.targetTexture; cam.targetTexture = rt; cam.Render(); cam.targetTexture = prev;
            var tex = new Texture2D(w, h, TextureFormat.RGB24, false); var act = RenderTexture.active;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, w, h), 0, 0); tex.Apply(); RenderTexture.active = act; RenderTexture.ReleaseTemporary(rt);
            File.WriteAllBytes(path, tex.EncodeToJPG(90)); Object.DestroyImmediate(tex);
            cam.transform.SetPositionAndRotation(p, r); cam.fieldOfView = f; cam.aspect = a;
            foreach (var c in hidden) c.enabled = true;
        }

        static readonly BindingFlags Any = BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance;
        static readonly MethodInfo OnLoad = typeof(GolfGame).GetMethod("OnLoad", Any);
        static readonly MethodInfo SelectClub = typeof(GolfGame).GetMethod("SelectClub", Any);
        static readonly MethodInfo NativeSet = typeof(GolfGame).GetProperty("NativeControlled").GetSetMethod(true);
        static readonly MethodInfo TouchSet = typeof(NativeSportsSession).GetProperty("Touch", BindingFlags.Public | BindingFlags.Static).GetSetMethod(true);
        static readonly FieldInfo BallField = typeof(GolfGame).GetField("ball", Any);
        static readonly FieldInfo GvTime = typeof(GolferView).GetField("time", Any);
        static readonly FieldInfo GvPhase = typeof(GolferView).GetField("phase", Any);
        static readonly FieldInfo GvClip = typeof(GolferView).GetField("clipName", Any);
        static readonly FieldInfo GvTop = typeof(GolferView).GetField("TopTime", Any);
        static readonly FieldInfo GvImpact = typeof(GolferView).GetField("ImpactTime", Any);
        static readonly FieldInfo GvEnd = typeof(GolferView).GetField("EndTime", Any);
        static readonly FieldInfo GvFade = typeof(GolferView).GetField("fade", Any);

        /// On the device the native bridge owns the samples and SwingController.Update stands aside (NativeSportsSession.Active);
        /// in the Editor its synthetic source would feed the same detector every frame, so it gets a source that never speaks.
        sealed class Silent : GolfArcade.Swing.IMotionSource
        {
            public bool IsAvailable => true; public void Start() { } public void Stop() { }
            public bool TryRead(out GolfArcade.Swing.MotionSample sample) { sample = default; return false; }
        }

        struct Spec { public bool female; public GolfClub club; public string mode; public double down; public string tag; }

        static IEnumerator All(GolfGame game)
        {
            string root = Path.GetFullPath(Env("GSS_OUT", "gss_out")); Directory.CreateDirectory(root);
            var savedBody = GolferStyle.Body;
            var report = new List<string>();
            var tracksOn = Env("GSS_TRACKS", "1") != "0";
            var tracksType = typeof(GolfArcade.Tennis.HeroClearanceTracks);
            tracksType.GetField("Enabled", BindingFlags.Public | BindingFlags.Static)?.SetValue(null, tracksOn);
            try
            {
                Time.captureFramerate = 60; Time.timeScale = 1; UnityEngine.Random.InitState(3108);
                GolfGame.LoadCoverMinimum = 0.1f; game.InstantReplays = false;
                for (int i = 0; i < 10; i++) yield return null;
                var list = Env("GSS_SWINGS", "male:Driver:motion:0.25");
                var listFile = Path.Combine(root, "swings.txt");   // (a file next to the output wins: lets a queued run change its takes)
                if (File.Exists(listFile)) list = File.ReadAllText(listFile).Trim();
                foreach (var s in list.Split(','))
                {
                    var p = s.Split(':');
                    var spec = new Spec
                    {
                        female = p[0] == "female", club = (GolfClub)Enum.Parse(typeof(GolfClub), p[1]),
                        mode = p.Length > 2 ? p[2] : "motion", down = p.Length > 3 ? double.Parse(p[3], CultureInfo.InvariantCulture) : 0.25,
                    };
                    bool on = tracksOn && !(p.Length > 4 && p[4] == "notracks");
                    tracksType.GetField("Enabled", BindingFlags.Public | BindingFlags.Static)?.SetValue(null, on);
                    spec.tag = $"{p[0]}_{p[1]}_{spec.mode}" + (spec.mode == "motion" ? "_" + (int)Math.Round(spec.down * 1000) : "") + (on ? "" : "_notracks");
                    var e = OneSwing(game, root, spec, report);
                    while (true)
                    {
                        bool more;
                        try { more = e.MoveNext(); }
                        catch (Exception ex) { report.Add($"{spec.tag}: FAILED {ex.GetType().Name}: {ex.Message}"); Debug.LogException(ex); break; }
                        if (!more) break;
                        yield return e.Current;
                    }
                    File.WriteAllLines(Path.Combine(root, "summary.txt"), report);
                }
            }
            finally
            {
                TouchSet.Invoke(null, new object[] { false });
                GolferStyle.Body = savedBody;
                File.WriteAllLines(Path.Combine(root, "summary.txt"), report);
                Debug.Log("[GSSFilm] " + string.Join(" | ", report));
            }
        }

        /// The phone's turn from address (radians, + = back) at swing time s, and its rate.
        /// address 0.5 s still, backswing `back` s (eased), top pause 0.06 s, downswing with constant angular acceleration that
        /// reaches the ball (angle 0) after `down` s, then a follow-through that decelerates to -2.3 rad.
        static (double angle, double rate, string stage) Phone(double s, double back, double down, double A = 2.75)
        {
            const double Addr = 0.5, Pause = 0.06;
            double Finish = A * 0.84;
            if (s < Addr) return (0, 0, "address");
            s -= Addr;
            if (s < back) { double u = s / back; return (A * (0.5 - 0.5 * Math.Cos(Math.PI * u)), A * 0.5 * Math.PI / back * Math.Sin(Math.PI * u), "backswing"); }
            s -= back;
            if (s < Pause) return (A, 0, "top");
            s -= Pause;
            if (s < down) { double k = A / (down * down); return (A - k * s * s, -2 * k * s, "downswing"); }
            s -= down;
            double v = 2 * A / down, T = 2 * Finish / v;
            if (s < T) return (-(v * s - 0.5 * v / T * s * s), -(v - v / T * s), "through");
            return (-Finish, 0, "finish");
        }

        static IEnumerator OneSwing(GolfGame game, string root, Spec spec, List<string> report)
        {
            string dir = Path.Combine(root, spec.tag); Directory.CreateDirectory(dir);
            foreach (var f in Directory.GetFiles(dir, "*.jpg")) File.Delete(f);
            GolferStyle.Body = spec.female ? GolferStyle.BodyKind.Female : GolferStyle.BodyKind.Male;
            var golfer = game.GetComponentInChildren<GolferView>(true); golfer.ApplyStyle();
            bool motion = spec.mode == "motion", tap = spec.mode == "tap";
            TouchSet.Invoke(null, new object[] { tap });
            game.PrepareNativeAddress("cliffside");
            for (int i = 0; i < 5; i++) yield return null;
            if (game.Current != GolfGame.State.Aim) throw new InvalidOperationException("not aiming after PrepareNativeAddress: " + game.Current);
            game.SetWind(new Wind(0, 0));
            if (!(game.Swing.Source is Silent)) game.Swing.UseSource(new Silent());
            if (!motion && !tap) NativeSet.Invoke(game, new object[] { false });
            golfer = game.GetComponentInChildren<GolferView>(true);
            if (!golfer.IsHero) throw new InvalidOperationException("golfer is not the Hero");
            SelectClub.Invoke(game, new object[] { spec.club });
            var cam = game.GameplayCamera ? game.GameplayCamera : Camera.main;
            foreach (var smr in golfer.GetComponentsInChildren<SkinnedMeshRenderer>(true)) smr.updateWhenOffscreen = true;
            for (int i = 0; i < 30; i++) { cam.aspect = 16f / 9f; yield return null; }
            var hole = game.CurrentHole;
            var ball = BallField.GetValue(game) as Transform;
            if (motion) { game.NativeReady(); game.NativeStartSwing(Q.Identity); }
            if (motion && !Object.FindFirstObjectByType<GSSPhoneFeed>()) new GameObject("GSS phone feed").AddComponent<GSSPhoneFeed>();
            if (tap) game.NativeReady();

            var g = golfer.transform.position; var face = golfer.transform.forward; face.y = 0; face.Normalize();
            var aim = Vector3.Cross(face, Vector3.up).normalized;
            float ground = ball ? ball.position.y : g.y;
            var c = new Vector3(g.x, ground, g.z) + face * 0.30f;
            var look = c + Vector3.up * 1.0f;
            const float D = 5.2f, H = 1.15f;
            Vector3 At(Vector3 d) { d.y = 0; return c + d.normalized * D + Vector3.up * H; }
            var views = new List<(string name, Vector3 from, Vector3 look)>
            {
                ("faceon", At(face), look),
                ("dtl", At(-aim) + face * 0.35f, look + face * 0.35f),
            };
            var want = Env("GSS_VIEWS", "game,faceon,dtl").Split(',');
            views = views.Where(v => want.Contains(v.name)).ToList();
            bool gameShot = want.Contains("game");

            var allT = golfer.GetComponentsInChildren<Transform>(true);
            Transform Bone(string n) => allT.FirstOrDefault(t => t.name == n);
            var lh = Bone("LeftHand"); var rh = Bone("RightHand"); var head = Bone("Head"); var hips = Bone("Hips");
            var rows = new List<string> { "frame,t,stage,phoneAngle,detPhase,state,gvPhase,clip,clipTime,fade,clubHead,leftHand,rightHand,head,hips,ball" };
            var events = new List<string>();
            double back = double.Parse(Env("GSS_BACK", "0.80"), CultureInfo.InvariantCulture);
            double amp = spec.club == GolfClub.Putter ? 0.45 : 2.75;   // a putt's stroke is a short arc (the putter's detector: full at 0.6 rad)
            double t0 = 10.0, sent = -1;           // phone clock (s) at frame 0
            int frames = Mathf.RoundToInt((float)((0.5 + back + 0.06 + spec.down + 1.6) * 60));
            int strikeFrame = Mathf.RoundToInt((float)((0.5 + back + 0.06) * 60));   // touch: the impact call at the top
            var target = hole.RecommendedTarget(hole.Tee);
            string lastState = game.Current.ToString(); object lastPhase = GvPhase.GetValue(golfer);
            Vector3? ballStart = ball ? ball.position : (Vector3?)null; bool ballMoved = false;
            string stage = "address";
            for (int k = 0; k < frames; k++)
            {
                double now = k / 60.0;
                if (motion)
                {
                    // every 100 Hz sample up to this frame's time, drained in the frame's Update (GSSPhoneFeed) as the native session does
                    double until = now;
                    GSSPhoneFeed.Hook = () =>
                    {
                        for (double s = Math.Floor(sent * 100 + 1) / 100; s <= until + 1e-9; s += 0.01)
                        {
                            var (ang, rate, st) = Phone(s, back, spec.down, amp);
                            var q = Q.Normalize(Q.CreateFromAxisAngle(V3.UnitX, (float)ang));
                            game.NativeMotion(new NativeSportsSession.Sample { time = t0 + s, qx = q.X, qy = q.Y, qz = q.Z, qw = q.W, rx = (float)rate });
                            sent = s;
                        }
                    };
                    stage = Phone(now, back, spec.down, amp).stage;
                }
                else if (tap)
                {
                    stage = k < strikeFrame ? "address" : "through";
                    if (k == strikeFrame) { game.NativeSwing(0.8f); events.Add($"{k} tap NativeSwing(0.8)"); }
                }
                else
                {
                    double u = (now - 0.5) / back;
                    stage = now < 0.5 ? "address" : u < 1 ? "backswing" : k < strikeFrame ? "top" : "through";
                    if (stage == "backswing" || stage == "top") OnLoad.Invoke(game, new object[] { stage == "top" ? 1.0 : 0.5 - 0.5 * Math.Cos(Math.PI * u) });
                    if (k == strikeFrame) { game.StrikeToward(target); events.Add($"{k} touch StrikeToward"); }
                }
                cam.aspect = 16f / 9f;
                yield return null;
                var state = game.Current.ToString(); var ph = GvPhase.GetValue(golfer);
                if (state != lastState) { events.Add($"{k} state {lastState}->{state}"); lastState = state; }
                if (!Equals(ph, lastPhase)) { events.Add($"{k} golfer phase {lastPhase}->{ph} clipTime={F((float)GvTime.GetValue(golfer))}"); lastPhase = ph; }
                if (!ballMoved && ball && ballStart is Vector3 b0 && (ball.position - b0).sqrMagnitude > 1e-4f) { ballMoved = true; events.Add($"{k} ball moves"); }
                string id = k.ToString("00000");
                if (gameShot) GameCapture.Save($"{dir}/game_{id}.jpg", 1280, 720);
                foreach (var v in views) Shot(cam, $"{dir}/{v.name}_{id}.jpg", v.from, v.look, 38f, 720, 960);
                rows.Add(string.Join(",", k, F(now), stage, motion ? F(Phone(now, back, spec.down, amp).angle) : "", game.Swing.Detector.Phase, state, ph, GvClip.GetValue(golfer),
                    F((float)GvTime.GetValue(golfer)), F((float)GvFade.GetValue(golfer)),
                    golfer.ClubHeadWorld() is Vector3 h ? V(h - c) : "", lh ? V(lh.position - c) : "", rh ? V(rh.position - c) : "",
                    head ? V(head.position - c) : "", hips ? V(hips.position - c) : "", ball ? V(ball.position - c) : ""));
            }
            GSSPhoneFeed.Hook = null;
            File.WriteAllText(dir + "/trace.csv", string.Join("\n", rows) + "\n");
            File.WriteAllText(dir + "/events.txt", string.Join("\n", events) + "\n");
            File.WriteAllText(dir + "/frame.txt", $"c={V(c)} face={V(face)} aim={V(aim)}\n");
            string line = $"{spec.tag}: clip={GvClip.GetValue(golfer)} top={F((float)GvTop.GetValue(golfer))} impact={F((float)GvImpact.GetValue(golfer))} end={F((float)GvEnd.GetValue(golfer))} " +
                          $"frames={frames} state={game.Current} events=[{string.Join("; ", events)}]";
            report.Add(line); Debug.Log("[GSSFilm] " + line);
        }
    }
}
#endif
