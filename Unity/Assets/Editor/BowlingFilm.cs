#if UNITY_EDITOR
using System;
using System.Collections;
using System.Globalization;
using System.IO;
using System.Text;
using GolfArcade.Bowling;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// P0 proof film of the bowling greybox: two players take turns and the autoplay bowls a set
    /// of deliveries that shows each release grade (perfect hook, straight, early, late, foul,
    /// gutter, drop). Batch:
    ///   -executeMethod GolfArcade.EditorTools.BowlingFilm.Run   BOWL_FILM_OUT=<new dir>
    /// Output: frames/f_00000.jpg at 30 fps and balls.csv (one row per delivery).
    [InitializeOnLoad]
    public static class BowlingFilm
    {
        const string Flag = "BowlingFilm";
        public const string ScenePath = "Assets/Scenes/Bowling.unity";
        static IEnumerator script;
        static int lastFrame = -1;
        static string output;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        static BowlingFilm() { EditorApplication.update += Tick; }

        /// Creates (or refreshes) the Bowling scene: one GameObject with BowlingGame, which builds everything.
        public static void EnsureScene()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            new GameObject("Bowling").AddComponent<BowlingGame>();
            Directory.CreateDirectory("Assets/Scenes");
            EditorSceneManager.SaveScene(scene, ScenePath);
        }

        public static void Run()
        {
            script = null; lastFrame = -1;
            if (!File.Exists(ScenePath)) EnsureScene();
            EditorSceneManager.OpenScene(ScenePath);
            EditorUtility.audioMasterMute = true;
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            var game = Object.FindFirstObjectByType<BowlingGame>();
            if (!game || !game.Initialized) return;
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
            SessionState.SetBool(Flag, false); Time.captureFramerate = 0;
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }

        /// BOWL_FILM_AUDIO=1: records what the listener hears to audio.wav (in real time; no frames) and
        /// silences the output while it does, so a batch run never plays through the Mac's speakers.
        sealed class WavTap : MonoBehaviour
        {
            readonly System.Collections.Generic.List<float> samples = new System.Collections.Generic.List<float>(48000 * 60 * 2);
            public int Channels = 2, Rate;
            void Awake() => Rate = AudioSettings.outputSampleRate;
            void OnAudioFilterRead(float[] data, int channels)
            {
                lock (samples) { Channels = channels; samples.AddRange(data); }
                Array.Clear(data, 0, data.Length);
            }
            public void Save(string path)
            {
                float[] d; lock (samples) d = samples.ToArray();
                using var w = new BinaryWriter(File.Create(path));
                int bytes = d.Length * 2;
                w.Write(Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + bytes); w.Write(Encoding.ASCII.GetBytes("WAVEfmt "));
                w.Write(16); w.Write((short)1); w.Write((short)Channels); w.Write(Rate); w.Write(Rate * Channels * 2); w.Write((short)(Channels * 2)); w.Write((short)16);
                w.Write(Encoding.ASCII.GetBytes("data")); w.Write(bytes);
                foreach (var v in d) w.Write((short)Mathf.Clamp(Mathf.RoundToInt(v * 32767), -32768, 32767));
            }
        }

        static IEnumerator Record(BowlingGame game)
        {
            output = Path.GetFullPath(Environment.GetEnvironmentVariable("BOWL_FILM_OUT") ?? "../work/bowling/proof/film");
            Directory.CreateDirectory(Path.Combine(output, "frames"));
            bool audio = Environment.GetEnvironmentVariable("BOWL_FILM_AUDIO") == "1";
            WavTap tap = null;
            if (audio)
            {
                var listener = Object.FindFirstObjectByType<AudioListener>();
                if (!listener) throw new Exception("no AudioListener in the bowling scene");
                EditorUtility.audioMasterMute = false; AudioListener.volume = 1; AudioListener.pause = false;
                tap = listener.gameObject.AddComponent<WavTap>();
            }
            else Time.captureFramerate = 30;
            // BOWL_FILM_CPU=1: exhibition, you against the computer (Steady Sam bowls his own balls)
            bool cpu = Environment.GetEnvironmentVariable("BOWL_FILM_CPU") == "1";
            game.CpuSkill.Clear(); if (cpu) { game.CpuSkill.Add(-1); game.CpuSkill.Add(.5f); }
            game.NewGame(cpu ? new[] { "Adnan", "Steady Sam" } : new[] { "Adnan", "Sam" });
            // BOWL_FILM_STILLS=1: the venue from four fixed angles first (stills/*.jpg; BOWL_VENUE picks the venue)
            if (Environment.GetEnvironmentVariable("BOWL_FILM_STILLS") == "1")
            {
                yield return null; yield return null;   // the reflection probes render after a frame
                var cam = Camera.main;
                var (was, wasRot) = (cam.transform.position, cam.transform.rotation);
                Directory.CreateDirectory(Path.Combine(output, "stills"));
                var views = new[]
                {
                    ("wide", new Vector3(0, 4.2f, -13.5f), new Vector3(0, .4f, 12)),
                    ("side", new Vector3(5.2f, 2.4f, -1f), new Vector3(-.5f, .4f, 12)),
                    ("pins", new Vector3(.4f, .55f, 15.6f), new Vector3(0, .2f, BowlingLane.FoulToHeadPin)),
                    ("lounge", new Vector3(2.5f, 1.8f, -3f), new Vector3(-1, 1.2f, -13)),
                };
                var meta = new StringBuilder("{\n");
                string V(Vector3 v) => $"[{F(v.x)},{F(v.y)},{F(v.z)}]";
                void Shoot(string name, Vector3 pos, Vector3 look)
                {
                    cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(look - pos));
                    BowlingLaneMirror.RenderNow();   // the lane mirror follows the camera before the offscreen render
                    GameCapture.Save(Path.Combine(output, "stills", name + ".jpg"), 1280, 720);
                    meta.Append($"  \"{name}\": {{\"pos\": {V(pos)}, \"look\": {V(look)}, \"fov\": {F(cam.fieldOfView)}}},\n");
                }
                // the setup shot as the game frames it (lane luma, ΔE between venues, draw budget)
                Shoot("setup", was, was + wasRot * Vector3.forward * 20);
                var stats = (b: UnityStats.batches, d: UnityStats.drawCalls, t: UnityStats.triangles);   // the setup render, if the editor counted it
                var planes = GeometryUtility.CalculateFrustumPlanes(cam);
                // in view: renderers, distinct materials (SetPass proxy), triangles (venue pieces counted before
                // static batching merged them; the instanced crowd is added by light_gate.py from the log)
                int renderers = 0; long tris = 0; var mats = new System.Collections.Generic.HashSet<Material>();
                // LOD groups draw one level: count only the renderers of the level this camera would pick
                var skip = new System.Collections.Generic.HashSet<Renderer>();
                foreach (var g in Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None))
                {
                    var lods = g.GetLODs(); if (lods.Length == 0) continue;
                    float dist = Vector3.Distance(cam.transform.position, g.transform.TransformPoint(g.localReferencePoint));
                    float size = g.size * Mathf.Max(g.transform.lossyScale.x, g.transform.lossyScale.y, g.transform.lossyScale.z);
                    float rel = size / (2 * dist * Mathf.Tan(cam.fieldOfView * .5f * Mathf.Deg2Rad)) / QualitySettings.lodBias;
                    int pick = lods.Length;   // culled
                    for (int i = 0; i < lods.Length; i++) if (rel >= lods[i].screenRelativeTransitionHeight) { pick = i; break; }
                    for (int i = 0; i < lods.Length; i++) if (i != pick) foreach (var lr in lods[i].renderers) if (lr) skip.Add(lr);
                }
                foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
                {
                    if (!r.enabled || !r.gameObject.activeInHierarchy || skip.Contains(r) || !GeometryUtility.TestPlanesAABB(planes, r.bounds)) continue;
                    var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh) continue;
                    foreach (var m in r.sharedMaterials) if (m) mats.Add(m);
                    if (BowlingVenue.Built.TryGetValue(r, out long t)) { renderers++; tris += t; continue; }
                    renderers += mf.sharedMesh.subMeshCount;
                    for (int k = 0; k < mf.sharedMesh.subMeshCount; k++) tris += mf.sharedMesh.GetIndexCount(k) / 3;
                }
                foreach (var r in Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None))
                    if (r.enabled && r.sharedMesh && GeometryUtility.TestPlanesAABB(planes, r.bounds)) { renderers += r.sharedMesh.subMeshCount; tris += r.sharedMesh.triangles.Length / 3; }
                foreach (var (name, pos, look) in views) Shoot(name, pos, look);
                // the menu's venue picture (MenuArt/map-bowling-<venue>.jpg): a three-quarter view down the lanes, no HUD
                var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
                foreach (var c in canvases) c.enabled = false;
                Shoot("map", new Vector3(1.6f, 1.75f, -4.2f), new Vector3(-.4f, .45f, 13));
                foreach (var c in canvases) c.enabled = true;
                // the reaction shot on the bowler standing at the stance (face luma)
                var bowler = Object.FindObjectsByType<BowlingHero>(FindObjectsSortMode.None);
                BowlingHero h = null; foreach (var b in bowler) if (b.Position.z > -8 && (!h || b.Position.z > h.Position.z)) h = b;
                if (h)
                {
                    // where the reaction shot finds them: at the foul line after the slide
                    var (hpWas, hrWas) = (h.transform.position, h.transform.rotation);
                    h.transform.position = new Vector3(hpWas.x, 0, BowlingApproach.SlideZ);
                    var hp = h.Position;
                    Shoot("react", new Vector3(hp.x + .6f, 1.4f, hp.z + 3.4f), new Vector3(hp.x, 1.05f, hp.z - 3));
                    // the rig is generic (not humanoid): find the head bone by name
                    Transform head = null;
                    foreach (var t in h.GetComponentsInChildren<Transform>(true))
                        if (t.name.EndsWith("Head", StringComparison.OrdinalIgnoreCase) || t.name.EndsWith("head")) { head = t; break; }
                    meta.Append($"  \"head\": {V(head ? head.position + Vector3.up * .06f : hp + Vector3.up * 1.6f)},\n");
                    h.transform.SetPositionAndRotation(hpWas, hrWas);
                }
                // the ball on the lane, from the rolling camera
                var ball = game.BallView;
                if (ball)
                {
                    var (bp, br, ba) = (ball.transform.position, ball.transform.rotation, ball.activeSelf);
                    var at = new Vector3(BowlingLane.BoardX(14), BowlingLane.BallRadius, 8);
                    ball.SetActive(true); ball.transform.position = at;
                    Shoot("ball", new Vector3(at.x * .5f, .62f, at.z - 2.6f), new Vector3(at.x * .4f, .1f, at.z + 6));
                    meta.Append($"  \"ballAt\": {V(at)},\n");
                    ball.transform.SetPositionAndRotation(bp, br); ball.SetActive(ba);
                }
                meta.Append($"  \"venue\": \"{BowlingVenue.Current}\", \"setupDraws\": {renderers}, \"setupTris\": {tris}, \"setupMaterials\": {mats.Count}, \"statsBatches\": {stats.b}, \"statsDraws\": {stats.d}, \"statsTris\": {stats.t}\n}}\n");
                File.WriteAllText(Path.Combine(output, "stills", "meta.json"), meta.ToString());
                cam.transform.SetPositionAndRotation(was, wasRot);
            }
            // board, mph→m/s speed, rpm, axis, timing error (s). Board counts from the right.
            var shots = new[]
            {
                new BowlingGame.Shot(3.5f, 7.6f, 300, 45, 0),     // a perfect hook from the outside dots → the pocket
                new BowlingGame.Shot(9, 7.4f, 250, 30, .03f),     // a medium hook (second ball, or the next player's first)
                new BowlingGame.Shot(17.5f, 7.8f, 120, 0, .06f),  // straight at the pocket (good release)
                new BowlingGame.Shot(20, 7.4f, 150, 5, -.18f),    // early release
                new BowlingGame.Shot(4, 7.6f, 300, 45, .18f),     // late, lofted
                new BowlingGame.Shot(14, 7.0f, 200, 20, 1f),      // held too long: FOUL
                new BowlingGame.Shot(4, 7.2f, 200, -30, .05f),    // outside board with a backup → gutter
                new BowlingGame.Shot(20, 7.0f, 150, 0, -.35f),    // slips out on the backswing
            };
            int limit = int.TryParse(Environment.GetEnvironmentVariable("BOWL_FILM_SHOTS"), out int l) ? l : shots.Length;   // a quick look: the first n shots
            var humanShots = new System.Collections.Generic.Queue<BowlingGame.Shot>();
            for (int i = 0; i < Mathf.Min(limit, shots.Length); i++) { if (cpu) humanShots.Enqueue(shots[i]); else game.Autoplay.Enqueue(shots[i]); }
            // BOWL_FILM_PHONE=1 (with BOWL_FILM_CPU=1): the person's balls go through the phone path the device uses (MotionInput,
            // PlayerMove/PlayerHold, NativeMotion samples at 100 Hz of a synthesized arm pendulum), on game time so the frames line up
            bool phone = cpu && Environment.GetEnvironmentVariable("BOWL_FILM_PHONE") == "1";
            PhoneSwing swing = null; int phoneBalls = 0;
            if (phone) { game.KeyboardEnabled = false; game.MotionInput = true; game.Clock = () => Time.timeAsDouble; }
            // BOWL_FILM_BOWLERCAM=1: a second picture per frame, a close three-quarter view of the bowler (body/skin deformities)
            bool bowlerCam = Environment.GetEnvironmentVariable("BOWL_FILM_BOWLERCAM") == "1";
            if (bowlerCam) Directory.CreateDirectory(Path.Combine(output, "bowler"));
            var heroesField = typeof(BowlingGame).GetField("heroes", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            var approachField = typeof(BowlingGame).GetField("approachT", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            var timeline = new StringBuilder("frame,t,flow,player,cpu,approachT,clipRate,clipTime,clip,swing,board,left,idle\n");
            var csv = new StringBuilder("ball,player,grade,board,speed_mph,rpm,axis,launch_deg,loft,knocked,standing_after,settle_s\n");
            int balls = 0;
            game.BallFinished += (th, act) =>
            {
                csv.Append(string.Join(",", balls++, game.Players[game.Current], th.Grade, F(th.Board), F(th.Speed * 2.237f), F(th.RevRpm), F(th.AxisDeg),
                    F(th.LaunchDeg), F(th.LoftHeight), act.Knocked, BowlingLeave.Numbers(act.StandingAfter), F(act.SettleTime))).Append('\n');
            };
            int frame = 0; float idle = 0, start = Time.time; var lastLogged = BowlingGame.Phase.Setup;
            float filmLimit = float.TryParse(Environment.GetEnvironmentVariable("BOWL_FILM_SECONDS"), NumberStyles.Float, Inv, out float fl) ? fl : 120;
            while (Time.time - start < filmLimit)   // (game time: 30 fps captures, real time when recording audio)
            {
                if (!audio) GameCapture.Save(Path.Combine(output, "frames", $"f_{frame:00000}.jpg"), 1280, 720);
                var heroes = (System.Collections.Generic.List<BowlingHero>)heroesField.GetValue(game);
                var bowler = heroes.Count > game.Current ? heroes[game.Current] : null;
                if (bowlerCam && !audio && bowler)
                {
                    var cam = Camera.main; var (was, wasRot) = (cam.transform.position, cam.transform.rotation);
                    var hp = bowler.Position;
                    var pos = hp + new Vector3(1.9f, 1.25f, 2.3f); var at = hp + Vector3.up * .85f;
                    // the pins' turn: a close look at the deck (pin action, replay, the sweep) from inside the kickbacks
                    var phase = game.Flow;
                    if (phase == BowlingGame.Phase.Pins || phase == BowlingGame.Phase.Replay || phase == BowlingGame.Phase.Sweep || (phase == BowlingGame.Phase.Result && !bowler.ClipPlaying))
                    { pos = new Vector3(.6f, .7f, BowlingLane.FoulToHeadPin - 1.3f); at = new Vector3(0, .12f, BowlingLane.FoulToHeadPin + .45f); }
                    cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(at - pos));
                    var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
                    foreach (var c in canvases) c.enabled = false;
                    BowlingLaneMirror.RenderNow();
                    GameCapture.Save(Path.Combine(output, "bowler", $"f_{frame:00000}.jpg"), 1280, 720);
                    foreach (var c in canvases) c.enabled = true;
                    cam.transform.SetPositionAndRotation(was, wasRot);
                }
                timeline.Append(string.Join(",", frame, F(Time.time - start), game.Flow, game.Current, game.IsCpu(game.Current) ? 1 : 0, F((float)approachField.GetValue(game)),
                    F(bowler && bowler.Anim ? bowler.Anim.ActionRate : 1), F(bowler ? bowler.ClipTime : 0), bowler && bowler.Anim ? bowler.Anim.Playing : "", swing?.Kind ?? "", F(game.Board), humanShots.Count, F(idle))).Append('\n');
                frame++;
                // the heroes' renderers at each turn (skin problems: what changes between a clean turn and a bad one)
                if (game.Flow == BowlingGame.Phase.Hold && lastLogged != BowlingGame.Phase.Hold)
                {
                    var log = new StringBuilder($"[BowlingFilm] renderers t={Time.time - start:0.0} bowler={game.Current}\n");
                    foreach (var h in heroes)
                    {
                        if (!h) continue;
                        foreach (var r in h.GetComponentsInChildren<Renderer>(true))
                        {
                            var smr = r as SkinnedMeshRenderer; var mesh = smr ? smr.sharedMesh : r.GetComponent<MeshFilter>()?.sharedMesh;
                            log.Append($"  {h.name}/{r.name} on={r.enabled && r.gameObject.activeInHierarchy} mesh={(mesh ? mesh.name + ":" + mesh.vertexCount + "v/" + mesh.subMeshCount : "-")}");
                            foreach (var m in r.sharedMaterials) log.Append(m ? $" [{m.name}|{m.shader.name}|{(m.HasProperty("_BaseMap") && m.GetTexture("_BaseMap") ? m.GetTexture("_BaseMap").name : "-")}]" : " [null]");
                            log.Append('\n');
                        }
                    }
                    Debug.Log(log.ToString());
                }
                lastLogged = game.Flow;
                if (phone && game.Current == 0)
                {
                    if (game.Flow == BowlingGame.Phase.Setup && swing == null && humanShots.Count > 0)
                    {
                        var target = humanShots.Peek().Board;
                        float diff = target - game.Board;
                        if (Mathf.Abs(diff) > .25f) game.PlayerMove(Mathf.Clamp(diff, -.5f, .5f));
                        else if ((idle += Time.deltaTime) > .8f)
                        {
                            game.PlayerHold(true);   // (refused while the bowler is still walking up: press again next frame)
                            if (game.Flow == BowlingGame.Phase.Hold)
                            {
                                humanShots.Dequeue(); idle = 0;
                                swing = new PhoneSwing(PhoneSwing.Kinds[phoneBalls++ % PhoneSwing.Kinds.Length], Time.timeAsDouble);
                            }
                        }
                    }
                    if (swing != null)
                    {
                        swing.Feed(game, Time.timeAsDouble);
                        if (game.Flow != BowlingGame.Phase.Hold && game.Flow != BowlingGame.Phase.Approach) { if (game.Holding) game.PlayerHold(false); swing = null; }
                    }
                }
                // exhibition: the person's shots go in on their own turns (the computer plans its own)
                if (cpu && !phone && game.Current == 0 && game.Flow == BowlingGame.Phase.Setup && game.Autoplay.Count == 0 && humanShots.Count > 0) game.Autoplay.Enqueue(humanShots.Dequeue());
                if (cpu && humanShots.Count == 0 && swing == null && game.Current == 0 && game.Flow == BowlingGame.Phase.Setup && game.Autoplay.Count == 0 && (idle += Time.deltaTime) > 1.5f) { Debug.Log("[BowlingFilm] exhibition done"); break; }
                if (audio && Mathf.FloorToInt((Time.time - start) * 2) != Mathf.FloorToInt((Time.time - start - Time.deltaTime) * 2))
                {
                    var srcs = new StringBuilder();
                    var ba = Object.FindFirstObjectByType<BowlingAudio>();
                    if (ba) foreach (var a in ba.GetComponents<AudioSource>()) if (a.clip && (a.isPlaying || a.loop)) srcs.Append($" {a.clip.name}:{(a.isPlaying ? "on" : "off")}/v{a.volume:0.00}/p{a.pitch:0.00}");
                    Debug.Log($"[BowlingFilm] t={Time.time - start:0.0} flow={game.Flow} player={game.Current} board={game.Board:0.0} queued={game.Autoplay.Count} sfx={GolfArcade.Game.GameAudio.SfxVolume:0.00} music={GolfArcade.Game.GameAudio.MusicVolume:0.00} listener={AudioListener.volume:0.00}{srcs}");
                }
                if (!phone && game.Autoplay.Count == 0 && game.Flow == BowlingGame.Phase.Setup && (idle += Time.deltaTime) > 1.5f) { Debug.Log("[BowlingFilm] autoplay done"); break; }
                yield return null;
            }
            if (tap) tap.Save(Path.Combine(output, "audio.wav"));
            File.WriteAllText(Path.Combine(output, "balls.csv"), csv.ToString());
            File.WriteAllText(Path.Combine(output, "timeline.csv"), timeline.ToString());
            var sb = new StringBuilder();
            for (int p = 0; p < game.Players.Count; p++)
            {
                var sc = game.Scores[p];
                sb.Append(game.Players[p]).Append(": ");
                for (int f = 0; f < 10; f++) sb.Append('[').Append(sc.Mark(f, 0)).Append(sc.Mark(f, 1)).Append(f == 9 ? sc.Mark(f, 2) : "").Append(']');
                sb.Append(" total ").Append(sc.Total).Append('\n');
            }
            File.WriteAllText(Path.Combine(output, "scores.txt"), sb.ToString());
            Debug.Log($"[BowlingFilm] {frame} frames, {balls} balls → {output}\n{sb}");
        }

        static string F(float f) => f.ToString("0.00", Inv);

        /// A person's phone swing, as CoreMotion would report it (the pendulum of BowlingSelfTimedTests: stance 70° forward of
        /// hanging, pushaway, drop through the bottom, backswing, forward swing), starting `delay` s after the ball is held.
        ///   brisk:   swings as they press (tempo .33), lets go just past the bottom, a handshake wrist turn
        ///   relaxed: holds the stance 1.2 s after pressing, then a slow swing (tempo .42)
        ///   still:   presses and holds the phone still (no swing read), then lets go after 3 s
        sealed class PhoneSwing
        {
            public static readonly string[] Kinds = { "brisk", "relaxed", "still" };
            public readonly string Kind;
            readonly double t0, delay, q, letGo; double fed, bottom; float prevPhi = 70;
            public PhoneSwing(string kind, double now)
            {
                Kind = kind; t0 = fed = now;
                (delay, q) = kind == "relaxed" ? (1.2, .42) : (0.0, .33);
                Phi(0, q, out bottom);
                letGo = kind == "still" ? 3.0 : delay + bottom + BowlingGame.ReleaseAfterBottom;
            }
            static double Phi(double t, double q, out double bottom)
            {
                double q1 = q * .62, a = 80, q2 = q1 * a / 35, q4 = q * 90 / a;
                double tDrop = .45, tBack = tDrop + q1, tTop = tBack + q2; bottom = tTop + q;
                if (t <= 0) return 70;
                if (t < tDrop) { double u = t / tDrop; return 70 - 35 * u * u * (3 - 2 * u); }
                if (t < tBack) return 35 * Math.Cos(Math.PI / 2 * (t - tDrop) / q1);
                if (t < tTop) return -a * Math.Sin(Math.PI / 2 * (t - tBack) / q2);
                if (t < bottom) return -a * Math.Cos(Math.PI / 2 * (t - tTop) / q);
                return 90 * Math.Sin(Math.PI / 2 * Math.Min(1, (t - bottom) / q4));
            }
            public void Feed(BowlingGame game, double now)
            {
                const double dt = .01;
                for (; fed + dt <= now + 1e-9; fed += dt)
                {
                    double t = fed + dt - t0, s = t - delay;
                    float phi = Kind == "still" ? 70 : (float)Phi(s, q, out _);
                    var rel = Quaternion.AngleAxis(phi - 70, Vector3.right);
                    float rate = (phi - prevPhi) * Mathf.Deg2Rad / (float)dt;
                    // brisk: a handshake turn about world up through the bottom
                    float yaw = Kind == "brisk" && Math.Abs(s - bottom) < .15 ? 4f : 0;
                    var deviceRate = Quaternion.Inverse(rel) * (Vector3.right * rate + Vector3.forward * yaw);
                    game.NativeMotion(fed + dt, rel.x, rel.y, rel.z, rel.w, deviceRate.x, deviceRate.y, deviceRate.z);
                    prevPhi = phi;
                }
                if (now - t0 >= letGo && game.Holding) game.PlayerHold(false);
            }
        }
    }
}
#endif
