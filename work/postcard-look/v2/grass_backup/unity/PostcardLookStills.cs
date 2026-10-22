using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using GolfArcade.Course;
using GolfArcade.Game;

namespace GolfArcade.EditorTools
{
    /// Game-view stills of the postcard holes (8 Needle, 9 Split, 10 Crater) for the POSTCARD_LOOK proof: Play mode, the real GolfGame / HoleView /
    /// CameraRig / GolfAtmosphere, a 900x1600 RenderTexture (the phone), the Canvas and the golfer hidden. PostcardCameraStills (JPG address
    /// stills of the older pass) stays as it was.
    ///
    ///   [GOLF_STILLS_OUT=<dir>] [GOLF_STILLS_CFG=<shots.json>] [GOLF_STILLS_HOLES=8,9,10] [GOLF_STILLS_BOARD=1] [GOLF_STILLS_PIPELINE=<URP asset name>]
    ///     Unity -batchmode -projectPath Unity -executeMethod GolfArcade.EditorTools.PostcardLookStills.Run -logFile <abs log>
    ///   (always through work/postcard-look/heavy.sh)
    ///
    /// Output (default dir ArtDir/screenshots/golf_postcards/look/): <name>.png per shot and stills_stats.json (pixel statistics per shot).
    ///
    /// Shots: with no GOLF_STILLS_CFG every selected hole gets "holeNN_tee" and "holeNN_approach" (CameraRig.FrameAddress, the game's own
    /// address framing: 4.5 yd behind the ball, 2.4 yd up, looking 1.5 yd ahead). GOLF_STILLS_CFG names a JSON file that REPLACES the defaults:
    ///   { "shots": [
    ///       { "name": "hole08_tee",  "hole": 8, "kind": "address", "ball": [0, 0], "aim": [19, 178], "putting": false },
    ///       { "name": "hole08_arch", "hole": 8, "kind": "landmark", "pos": [x, y, z], "look": [x, y, z], "fov": 50, "ball": [x, z] } ] }
    ///   "address": ball = [course x, course d] (the ball is put there, the camera frames it toward aim = [x, d] of the target); "putting" optional.
    ///   "landmark" (the default kind when "pos" is present): pos / look are Unity WORLD YARDS (x right, y up with the play surface at 6.56,
    ///   z down the hole), fov in degrees (default 60), optional "ball": [course x, course d] puts the game ball there (resting on the ground
    ///   under it, as in play) so a shot can prove the ball is not hidden. The camera is the game's camera; near .3, far 900.
    /// GOLF_STILLS_PIPELINE=<asset name, e.g. HeroBaseStudioURP or TennisURP> renders the stills under that URP asset (set IN MEMORY on the current quality level, restored at the
    /// end; ProjectSettings is never written). v2 repair round 1: the stills used to render under whatever QualitySettings pointed at (TennisURP today), so there was no
    /// HeroBaseStudioURP Game-view still. stills_stats.json "pipeline" names the asset that was really used.
    /// GOLF_STILLS_VARIANTS (v2 repair round 3, experiments only, never proof shots): extra renders of every shot with IN-MEMORY tweaks, written as <name>__<variant>.png (no stats):
    ///   "name:key=v[,v..];key=v|name2:..."   keys: fog=0|1, fogcolor=r,g,b (sRGB 0..1), fogrange=start,end, lights=<x> (LAVA_LIGHT intensity multiplier), sun=r,g,b (key colour),
    ///   ambient=<x> (multiplies the trilight colours), ambeq / ambsky / ambgnd=r,g,b (replace one trilight colour), basalt_tint=r,g,b, basalt_emis=r,g,b (LINEAR multiplier), basalt_smooth=<x>, nosmoke=1 (DRESS_SMOKE cards off), smoke=gain,power,softfade,lit,self,fogshare (LK_SMOKE material), hide=<renderer name prefix>.
    ///   Everything is put back after each render. The Game-view proof shots are always rendered WITHOUT variants.
    /// GOLF_STILLS_BOARD=1 lays the real LK_ materials on test strips in front of the tee (rough | fairway | green or sand, a lava sheet on
    /// Crater): the proof that the pipeline works while a hole FBX is still the flat baseline. Never use it for proof shots.
    ///
    /// stills_stats.json: { "tool", "unity", "pipeline", "qualityLevel", "size": [900, 1600], "shots": [ {
    ///     "name", "hole", "file", "camera": { "pos", "look", "fov" },
    ///     "mean_rgb": [r, g, b] (0..255, whole frame), "luminance" (0..255, whole frame),
    ///     "central_lower_third": { "region": [x0, y0, x1, y1] (px, y up from the bottom), "mean_rgb", "mean_hsv": [h deg, s, v], "luminance" },
    ///     "hue_bands": { "red_0_30": f, "orange_30_60": f, "yellow_60_90": f, ... "magenta_330_360": f, "grey": f, "dark": f },   // fraction of
    ///                    all pixels; "grey" = S < .15 (and not dark), "dark" = V < .15; 12 hue bands of 30 degrees for the rest
    ///     "smoke": { "cards": n (renderers named DRESS_SMOKE*), and when n > 0: "changed_px" (|delta luminance| > 1.5 between the frame and the SAME frame rendered with the
    ///                smoke cards switched off), "share_changed", "readable_px" (|delta| >= 10 levels: a plume a phone user can pick out), "share_readable" (of the whole frame),
    ///                "delta_lum_median" / "delta_lum_p95" / "delta_lum_p99" (over the changed pixels), "plume_mean_rgb" } }
    ///                v2 repair round 1: the reviewers found no readable plume in any Crater still while the old per-card gate passed on 0.44 % / 0.07 % of the frame;
    ///                postcard_look_verify.py SMOKE_VISIBLE_STILLS reads share_readable from here.
    /// } ] }
    [InitializeOnLoad]
    public static class PostcardLookStills
    {
        const string Flag = "PostcardLookStills";
        const int W = 900, H = 1600;
        const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;

        [System.Serializable] sealed class Cfg { public ShotCfg[] shots; }
        [System.Serializable] sealed class ShotCfg
        {
            public string name; public int hole; public string kind;
            public float[] pos, look, ball, aim; public float fov; public bool putting;
        }

        sealed class Shot
        {
            public string Name; public int Hole; public bool Landmark;
            public Vector3 Pos, Look; public float Fov = 60;
            public bool HasBall; public float BallX, BallD; public float AimX, AimD; public bool Putting;
        }

        // defaults: hole number -> (ball x, ball d, aim x, aim d) for the tee and the approach (on-land addresses of the older stills)
        static readonly Dictionary<int, ((float, float, float, float) tee, (float, float, float, float) approach)> Defaults = new()
        {
            [8] = ((0f, 0f, 19f, 178f), (19f, 178f, -6f, 340f)),
            [9] = ((0f, 0f, 3f, 60f), (11.8f, 235f, 6f, 416f)),
            [10] = ((0f, 0f, 14.3f, 66.2f), (107.1f, 159.3f, 261f, 164.7f)),
        };

        static readonly List<Shot> queue = new();
        static int warm, shotIndex = -1, wait, startFrame, settleTicks, staleShots;
        static string outDir; static bool board;
        static RenderTexture rt; static Texture2D tex; static Camera cam;
        static GolfGame game; static CameraRig rig; static GameObject boardRoot;
        static int currentHole = -1;
        static readonly List<string> statsJson = new();
        const string SmokePrefix = "DRESS_SMOKE";
        const float ReadableDelta = 10f;       // luminance levels: a plume that moves a pixel by >= 10 (of 255) can be picked out on a phone
        static UnityEngine.Rendering.RenderPipelineAsset previousPipeline; static bool pipelineSwapped;

        static PostcardLookStills() { EditorApplication.update += Tick; }

        public static void Run()
        {
            outDir = System.Environment.GetEnvironmentVariable("GOLF_STILLS_OUT");
            if (string.IsNullOrEmpty(outDir)) outDir = Path.GetFullPath("../ArtDir/screenshots/golf_postcards/look");
            outDir = Path.GetFullPath(outDir);
            Directory.CreateDirectory(outDir);
            SessionState.SetString(Flag + "out", outDir);
            SessionState.SetString(Flag + "cfg", System.Environment.GetEnvironmentVariable("GOLF_STILLS_CFG") ?? "");
            SessionState.SetString(Flag + "holes", System.Environment.GetEnvironmentVariable("GOLF_STILLS_HOLES") ?? "8,9,10");
            SessionState.SetBool(Flag + "board", System.Environment.GetEnvironmentVariable("GOLF_STILLS_BOARD") == "1");
            SessionState.SetString(Flag + "pipeline", System.Environment.GetEnvironmentVariable("GOLF_STILLS_PIPELINE") ?? "");
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            SessionState.SetBool(Flag, true);
            EditorApplication.isPlaying = true;
        }

        static bool BuildQueue(out string error)
        {
            error = null;
            queue.Clear();
            var holes = new HashSet<int>();
            foreach (var t in SessionState.GetString(Flag + "holes", "8,9,10").Split(',')) if (int.TryParse(t.Trim(), out var n)) holes.Add(n);
            string cfgPath = SessionState.GetString(Flag + "cfg", "");
            if (string.IsNullOrEmpty(cfgPath))
            {
                foreach (var kv in Defaults.OrderBy(k => k.Key))
                {
                    if (!holes.Contains(kv.Key)) continue;
                    var (tee, app) = kv.Value;
                    queue.Add(new Shot { Name = $"hole{kv.Key:00}_tee", Hole = kv.Key, HasBall = true, BallX = tee.Item1, BallD = tee.Item2, AimX = tee.Item3, AimD = tee.Item4 });
                    queue.Add(new Shot { Name = $"hole{kv.Key:00}_approach", Hole = kv.Key, HasBall = true, BallX = app.Item1, BallD = app.Item2, AimX = app.Item3, AimD = app.Item4 });
                }
                return true;
            }
            if (!File.Exists(cfgPath)) { error = "GOLF_STILLS_CFG not found: " + cfgPath; return false; }
            var cfg = JsonUtility.FromJson<Cfg>(File.ReadAllText(cfgPath));
            if (cfg == null || cfg.shots == null || cfg.shots.Length == 0) { error = "GOLF_STILLS_CFG has no shots"; return false; }
            foreach (var c in cfg.shots)
            {
                if (string.IsNullOrEmpty(c.name)) { error = "a shot has no name"; return false; }
                if (!GolfLook.IsPostcard(c.hole)) { error = $"shot '{c.name}': hole {c.hole} is not a postcard hole (8, 9, 10)"; return false; }
                bool landmark = c.kind == "landmark" || (string.IsNullOrEmpty(c.kind) && c.pos != null);
                var s = new Shot { Name = c.name, Hole = c.hole, Landmark = landmark, Fov = c.fov > 1 ? c.fov : 60, Putting = c.putting };
                if (landmark)
                {
                    if (c.pos == null || c.pos.Length < 3 || c.look == null || c.look.Length < 3) { error = $"shot '{c.name}': landmark needs pos [x,y,z] and look [x,y,z]"; return false; }
                    s.Pos = new Vector3(c.pos[0], c.pos[1], c.pos[2]); s.Look = new Vector3(c.look[0], c.look[1], c.look[2]);
                    if (c.ball != null && c.ball.Length >= 2) { s.HasBall = true; s.BallX = c.ball[0]; s.BallD = c.ball[1]; }
                }
                else
                {
                    if (c.ball == null || c.ball.Length < 2 || c.aim == null || c.aim.Length < 2) { error = $"shot '{c.name}': address needs ball [x,d] and aim [x,d]"; return false; }
                    s.HasBall = true; s.BallX = c.ball[0]; s.BallD = c.ball[1]; s.AimX = c.aim[0]; s.AimD = c.aim[1];
                }
                queue.Add(s);
            }
            var ordered = queue.Select((s, i) => (s, i)).OrderBy(t => t.s.Hole).ThenBy(t => t.i).Select(t => t.s).ToList();   // shots of one hole together, file order kept
            queue.Clear(); queue.AddRange(ordered);
            return true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying) return;
            if (shotIndex < 0)
            {
                if (!HoleView.Current || ++warm < 90) return;
                outDir = SessionState.GetString(Flag + "out", outDir);
                board = SessionState.GetBool(Flag + "board", false);
                if (!BuildQueue(out var error)) { Debug.LogError("[PostcardLookStills] " + error); Finish(1); return; }
                game = Object.FindFirstObjectByType<GolfGame>();
                rig = Object.FindFirstObjectByType<CameraRig>();
                cam = rig ? rig.GetComponentInChildren<Camera>() : Camera.main;
                foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
                if (!UsePipeline(SessionState.GetString(Flag + "pipeline", ""), out error)) { Debug.LogError("[PostcardLookStills] " + error); Finish(1); return; }
                rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
                tex = new Texture2D(W, H, TextureFormat.RGB24, false);
                var pipeline = QualitySettings.renderPipeline ? QualitySettings.renderPipeline : UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline;
                Debug.Log($"[PostcardLookStills] {queue.Count} shot(s) -> {outDir}; pipeline asset '{(pipeline ? pipeline.name : "none")}', quality level {QualitySettings.GetQualityLevel()} '{QualitySettings.names[QualitySettings.GetQualityLevel()]}'{(board ? "; TEST BOARD ON (not proof)" : "")}");
                shotIndex = 0; currentHole = -1; wait = 1; return;
            }
            if (--wait > 0) return;
            if (shotIndex >= queue.Count) { Finish(staleShots > 0 ? 2 : 0); return; }
            var s = queue[shotIndex];
            if (s.Hole != currentHole) { LoadHole(s.Hole); return; }
            // review K 2026-10-04: EditorApplication.update can tick faster than the player loop in batch mode, so "30 ticks" did not guarantee that GolfGame.StartHole's
            // Destroy(previous HoleView) had run (the probe then rendered the previous model under the new one). Wait for real player-loop frames and a single HoleView.
            if (!Settled(out var why) && ++settleTicks < 3000) return;
            settleTicks = 0;
            Take(s);
            shotIndex++; wait = 3;
        }

        static void LoadHole(int number)
        {
            int index = System.Array.FindIndex(GolfArcade.Course.Course.Postcards().Holes, h => h.Number == number);
            game.enabled = true; rig.enabled = true;
            startFrame = Time.frameCount; settleTicks = 0;
            typeof(GolfGame).GetMethod("StartHole", Private).Invoke(game, new object[] { index });
            currentHole = number; wait = 30;
            if (boardRoot) Object.Destroy(boardRoot);
            boardRoot = board ? TestBoard(number) : null;
        }

        /// The previous hole's HoleView is really gone and a few real frames have passed since StartHole.
        static bool Settled(out string why)
        {
            int frames = Time.frameCount - startFrame, views = Object.FindObjectsByType<HoleView>(FindObjectsInactive.Include, FindObjectsSortMode.None).Length;
            why = $"{frames} player frame(s) since StartHole, {views} HoleView(s) alive";
            return frames >= 5 && views == 1;
        }

        /// GOLF_STILLS_PIPELINE: swap the current quality level's URP asset for the named one (in memory; RestorePipeline puts it back). Empty = keep whatever is active.
        static bool UsePipeline(string name, out string error)
        {
            error = null;
            if (string.IsNullOrWhiteSpace(name)) return true;
            UnityEngine.Rendering.RenderPipelineAsset found = null;
            foreach (var guid in AssetDatabase.FindAssets(name.Trim() + " t:UniversalRenderPipelineAsset"))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (Path.GetFileNameWithoutExtension(path) == name.Trim()) { found = AssetDatabase.LoadAssetAtPath<UnityEngine.Rendering.RenderPipelineAsset>(path); break; }
            }
            if (!found) { error = "GOLF_STILLS_PIPELINE: no URP asset named '" + name + "'"; return false; }
            previousPipeline = QualitySettings.renderPipeline; pipelineSwapped = true;
            QualitySettings.renderPipeline = found;
            Debug.Log($"[PostcardLookStills] pipeline asset set in memory to '{found.name}' (was '{(previousPipeline ? previousPipeline.name : "none")}'; restored at the end, ProjectSettings is never written)");
            return true;
        }

        static void RestorePipeline()
        {
            if (!pipelineSwapped) return;
            QualitySettings.renderPipeline = previousPipeline; pipelineSwapped = false;
        }

        static void HideGameBits()
        {
            var golfer = (GolferView)typeof(GolfGame).GetField("golfer", Private).GetValue(game);
            if (golfer) golfer.SetVisible(false);
            var line = (LineRenderer)typeof(GolfGame).GetField("aimLine", Private).GetValue(game);
            if (line) line.enabled = false;
            var marker = (Transform)typeof(GolfGame).GetField("landingMarker", Private).GetValue(game);
            if (marker) marker.gameObject.SetActive(false);
        }

        static void Take(Shot s)
        {
            if (!Settled(out var why)) { staleShots++; Debug.LogError($"[PostcardLookStills] {s.Name}: NOT settled ({why}): the frame may show the previous hole too, the run will exit 2"); }
            HideGameBits();
            game.enabled = false; rig.enabled = false;
            var ballT = (Transform)typeof(GolfGame).GetField("ball", Private).GetValue(game);
            if (s.HasBall && ballT) { ballT.gameObject.SetActive(true); ballT.position = HoleView.ToWorld(new CoursePoint(s.BallX, s.BallD), 0.06); }
            cam.fieldOfView = s.Fov;
            if (s.Landmark)
            {
                rig.transform.position = s.Pos;
                rig.transform.rotation = Quaternion.LookRotation(s.Look - s.Pos, Vector3.up);
            }
            else
            {
                var ballAt = new CoursePoint(s.BallX, s.BallD);
                var ball = HoleView.ToWorld(ballAt, 0.06);
                var aim = HoleView.ToWorld(new CoursePoint(s.AimX, s.AimD), 0) - HoleView.ToWorld(ballAt, 0);
                aim.y = 0; aim.Normalize();
                rig.FrameAddress(ball, aim, s.Putting); rig.SnapNext(); rig.ApplyFrame();
            }
            cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
            File.WriteAllBytes(Path.Combine(outDir, s.Name + ".png"), tex.EncodeToPNG());
            var full = tex.GetPixels32();
            statsJson.Add(Stats(s, full, SmokeStats(full)));
            Debug.Log($"[PostcardLookStills] hole {s.Hole} {s.Name}");
            RenderVariants(s);
            cam.fieldOfView = 60;
        }

        // ------------------------------------------------------------------ variants (GOLF_STILLS_VARIANTS: experiments, in memory, put back after each render)

        static List<(string name, List<(string key, string val)> tweaks)> ParseVariants()
        {
            var list = new List<(string, List<(string, string)>)>();
            string spec = System.Environment.GetEnvironmentVariable("GOLF_STILLS_VARIANTS");
            if (string.IsNullOrWhiteSpace(spec)) return list;
            foreach (var v in spec.Split('|'))
            {
                int colon = v.IndexOf(':'); if (colon <= 0) continue;
                var tweaks = new List<(string, string)>();
                foreach (var t in v.Substring(colon + 1).Split(';'))
                {
                    int eq = t.IndexOf('='); if (eq <= 0) continue;
                    tweaks.Add((t.Substring(0, eq).Trim(), t.Substring(eq + 1).Trim()));
                }
                list.Add((v.Substring(0, colon).Trim(), tweaks));
            }
            return list;
        }

        static float[] Floats(string s) { var p = s.Split(','); var f = new float[p.Length]; for (int i = 0; i < p.Length; i++) float.TryParse(p[i], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out f[i]); return f; }

        static void RenderVariants(Shot s)
        {
            foreach (var (name, tweaks) in ParseVariants())
            {
                var undo = new List<System.Action>();
                foreach (var (key, val) in tweaks) Tweak(key, val, undo);
                cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                File.WriteAllBytes(Path.Combine(outDir, s.Name + "__" + name + ".png"), tex.EncodeToPNG());
                for (int i = undo.Count - 1; i >= 0; i--) undo[i]();
                Debug.Log($"[PostcardLookStills] variant {name} of {s.Name}");
            }
        }

        static void Tweak(string key, string val, List<System.Action> undo)
        {
            var f = key == "hide" ? null : Floats(val);
            switch (key)
            {
                case "fog": { bool o = RenderSettings.fog; RenderSettings.fog = f[0] != 0; undo.Add(() => RenderSettings.fog = o); break; }
                case "fogcolor": { var o = RenderSettings.fogColor; RenderSettings.fogColor = new Color(f[0], f[1], f[2]); undo.Add(() => RenderSettings.fogColor = o); break; }
                case "fogrange": { float a = RenderSettings.fogStartDistance, b = RenderSettings.fogEndDistance; RenderSettings.fogStartDistance = f[0]; RenderSettings.fogEndDistance = f[1]; undo.Add(() => { RenderSettings.fogStartDistance = a; RenderSettings.fogEndDistance = b; }); break; }
                case "ambient":
                {
                    Color a = RenderSettings.ambientSkyColor, b = RenderSettings.ambientEquatorColor, c = RenderSettings.ambientGroundColor;
                    RenderSettings.ambientSkyColor = a * f[0]; RenderSettings.ambientEquatorColor = b * f[0]; RenderSettings.ambientGroundColor = c * f[0];
                    undo.Add(() => { RenderSettings.ambientSkyColor = a; RenderSettings.ambientEquatorColor = b; RenderSettings.ambientGroundColor = c; });
                    break;
                }
                case "ambeq": { var o = RenderSettings.ambientEquatorColor; RenderSettings.ambientEquatorColor = new Color(f[0], f[1], f[2]); undo.Add(() => RenderSettings.ambientEquatorColor = o); break; }
                case "ambsky": { var o = RenderSettings.ambientSkyColor; RenderSettings.ambientSkyColor = new Color(f[0], f[1], f[2]); undo.Add(() => RenderSettings.ambientSkyColor = o); break; }
                case "ambgnd": { var o = RenderSettings.ambientGroundColor; RenderSettings.ambientGroundColor = new Color(f[0], f[1], f[2]); undo.Add(() => RenderSettings.ambientGroundColor = o); break; }
                case "sun": { var l = RenderSettings.sun; if (!l) break; var o = l.color; l.color = new Color(f[0], f[1], f[2]); undo.Add(() => l.color = o); break; }
                case "lights":
                {
                    var view = HoleView.Current; if (!view) break;
                    foreach (var l in view.GetComponentsInChildren<Light>(true)) if (l.type == LightType.Point) { float o = l.intensity; var ll = l; ll.intensity = o * f[0]; undo.Add(() => ll.intensity = o); }
                    break;
                }
                case "basalt_tint": { var m = GolfLook.Get("LK_BASALT"); var o = m.GetColor("_BaseColor"); m.SetColor("_BaseColor", new Color(f[0], f[1], f[2])); undo.Add(() => m.SetColor("_BaseColor", o)); break; }
                case "basalt_emis": { var m = GolfLook.Get("LK_BASALT"); var o = m.GetVector("_EmissionColor"); m.SetVector("_EmissionColor", new Vector4(f[0], f[1], f[2], 1)); undo.Add(() => m.SetVector("_EmissionColor", o)); break; }
                case "basalt_smooth": { var m = GolfLook.Get("LK_BASALT"); float o = m.GetFloat("_Smoothness"); m.SetFloat("_Smoothness", f[0]); undo.Add(() => m.SetFloat("_Smoothness", o)); break; }
                case "smoke":   // gain, power, softfade, lit, selflight, fogshare (any prefix of the list)
                {
                    var m = GolfLook.Get("LK_SMOKE");
                    string[] props = { "_AlphaGain", "_AlphaPower", "_SoftFade", "_Lit", "_Emission", "_FogShare" };
                    for (int i = 0; i < f.Length && i < props.Length; i++) { string pn = props[i]; float o = m.GetFloat(pn); m.SetFloat(pn, f[i]); undo.Add(() => m.SetFloat(pn, o)); }
                    break;
                }
                case "hide":    // renderers whose name starts with this prefix (string value, e.g. hide=DRESS_CONE)
                {
                    var view = HoleView.Current; if (!view) break;
                    foreach (var r in view.GetComponentsInChildren<Renderer>(false)) if (r.enabled && r.name.StartsWith(val)) { var rr = r; rr.enabled = false; undo.Add(() => rr.enabled = true); }
                    break;
                }
                case "ball":    // r,g,b multiplier on the ball's _BaseColor (a MaterialPropertyBlock on the game ball, put back afterwards)
                {
                    var ballT = (Transform)typeof(GolfGame).GetField("ball", Private).GetValue(game); var br = ballT ? ballT.GetComponent<Renderer>() : null; if (!br) break;
                    var mpb = new MaterialPropertyBlock(); mpb.SetColor("_BaseColor", new Color(f[0], f[1], f[2], 1)); br.SetPropertyBlock(mpb);
                    undo.Add(() => br.SetPropertyBlock(null));
                    break;
                }
                case "lavafog": { var m = GolfLook.Get("LK_LAVA"); if (!m.HasProperty("_FogShare")) break; float o = m.GetFloat("_FogShare"); m.SetFloat("_FogShare", f[0]); undo.Add(() => m.SetFloat("_FogShare", o)); break; }
                case "ballmat": // r,g,b exposure, selflight (GolfAtmosphere.SetBallLook; the previous values are put back)
                {
                    var e0 = GolfAtmosphere.BallExposureNow; float s0 = GolfAtmosphere.BallSelfLightNow;
                    GolfAtmosphere.SetBallLook(new Color(f[0], f[1], f[2]), f.Length > 3 ? f[3] : 0);
                    undo.Add(() => GolfAtmosphere.SetBallLook(e0, s0));
                    break;
                }
                case "nosmoke":
                {
                    var view = HoleView.Current; if (!view) break;
                    foreach (var r in view.GetComponentsInChildren<Renderer>(false)) if (r.enabled && r.name.StartsWith(SmokePrefix)) { var rr = r; rr.enabled = false; undo.Add(() => rr.enabled = true); }
                    break;
                }
                default: Debug.LogWarning("[PostcardLookStills] unknown variant tweak '" + key + "'"); break;
            }
        }

        static void Finish(int code)
        {
            string json = "{\n  \"tool\": \"PostcardLookStills\",\n  \"unity\": \"" + Application.unityVersion + "\",\n  \"pipeline\": \"" +
                (QualitySettings.renderPipeline ? QualitySettings.renderPipeline.name : UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline ? UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline.name : "none") +
                "\",\n  \"qualityLevel\": " + QualitySettings.GetQualityLevel() + ",\n  \"board\": " + (board ? "true" : "false") + ",\n  \"size\": [" + W + ", " + H + "],\n  \"shots\": [\n" +
                string.Join(",\n", statsJson.ToArray()) + "\n  ]\n}\n";
            if (statsJson.Count > 0) File.WriteAllText(Path.Combine(outDir, "stills_stats.json"), json);
            RestorePipeline();
            SessionState.SetBool(Flag, false);
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }

        // ------------------------------------------------------------------ pixel statistics

        static readonly string[] BandNames = { "red_0_30", "orange_30_60", "yellow_60_90", "lime_90_120", "green_120_150", "spring_150_180", "cyan_180_210", "azure_210_240", "blue_240_270", "violet_270_300", "magenta_300_330", "rose_330_360" };

        static string F(float v) => v.ToString("0.####", System.Globalization.CultureInfo.InvariantCulture);
        static string Arr(params float[] v) => "[" + string.Join(", ", System.Array.ConvertAll(v, F)) + "]";

        /// The smoke cards' own contribution to the frame: render the same camera again with every DRESS_SMOKE* renderer off and compare. (Two consecutive renders of
        /// one player frame share Time.time, so the animated sea does not move between them: only the cards differ.)
        static string SmokeStats(Color32[] full)
        {
            var view = HoleView.Current;
            var cards = new List<Renderer>();
            if (view) foreach (var r in view.GetComponentsInChildren<Renderer>(false)) if (r.enabled && r.name.StartsWith(SmokePrefix)) cards.Add(r);
            if (cards.Count == 0) return "\"smoke\": { \"cards\": 0 }";
            foreach (var r in cards) r.enabled = false;
            cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
            var dry = tex.GetPixels32();
            foreach (var r in cards) r.enabled = true;
            var deltas = new List<float>(); int readable = 0; double pr = 0, pg = 0, pb = 0;
            for (int i = 0; i < full.Length; i++)
            {
                float a = .2126f * full[i].r + .7152f * full[i].g + .0722f * full[i].b, b = .2126f * dry[i].r + .7152f * dry[i].g + .0722f * dry[i].b, d = Mathf.Abs(a - b);
                if (d <= 1.5f) continue;
                deltas.Add(d); pr += full[i].r; pg += full[i].g; pb += full[i].b;
                if (d >= ReadableDelta) readable++;
            }
            deltas.Sort();
            int n = deltas.Count; double all = full.Length;
            float Q(float q) => n == 0 ? 0 : deltas[Mathf.Min(n - 1, (int)(n * q))];
            return "\"smoke\": { \"cards\": " + cards.Count + ", \"changed_px\": " + n + ", \"share_changed\": " + F((float)(n / all)) + ", \"readable_px\": " + readable + ", \"share_readable\": " + F((float)(readable / all))
                 + ", \"delta_lum_median\": " + F(Q(.5f)) + ", \"delta_lum_p95\": " + F(Q(.95f)) + ", \"delta_lum_p99\": " + F(Q(.99f)) + ", \"plume_mean_rgb\": " + (n > 0 ? Arr((float)(pr / n), (float)(pg / n), (float)(pb / n)) : "[0, 0, 0]") + " }";
        }

        static string Stats(Shot s, Color32[] px, string smoke)
        {
            double r = 0, g = 0, b = 0, lum = 0;
            var bands = new int[BandNames.Length]; int grey = 0, dark = 0;
            foreach (var p in px)
            {
                r += p.r; g += p.g; b += p.b; lum += .2126 * p.r + .7152 * p.g + .0722 * p.b;
                Color.RGBToHSV(p, out var h, out var sat, out var v);
                if (v < .15f) dark++; else if (sat < .15f) grey++; else bands[Mathf.Min(BandNames.Length - 1, (int)(h * 12f))]++;
            }
            double n = px.Length;
            int x0 = W / 3, x1 = 2 * W / 3, y0 = 0, y1 = H / 3;
            double cr = 0, cg = 0, cb = 0, cl = 0; int cn = 0;
            for (int y = y0; y < y1; y++)
                for (int x = x0; x < x1; x++) { var p = px[y * W + x]; cr += p.r; cg += p.g; cb += p.b; cl += .2126 * p.r + .7152 * p.g + .0722 * p.b; cn++; }
            var mean = new Color((float)(cr / cn / 255), (float)(cg / cn / 255), (float)(cb / cn / 255));
            Color.RGBToHSV(mean, out var mh, out var ms, out var mv);
            var sb = new StringBuilder();
            sb.Append("    { \"name\": \"").Append(s.Name).Append("\", \"hole\": ").Append(s.Hole).Append(", \"file\": \"").Append(s.Name).Append(".png\",\n");
            sb.Append("      \"camera\": { \"pos\": ").Append(Arr(cam.transform.position.x, cam.transform.position.y, cam.transform.position.z))
              .Append(", \"look\": ").Append(Arr(cam.transform.position.x + cam.transform.forward.x, cam.transform.position.y + cam.transform.forward.y, cam.transform.position.z + cam.transform.forward.z))
              .Append(", \"fov\": ").Append(F(cam.fieldOfView)).Append(" },\n");
            sb.Append("      \"mean_rgb\": ").Append(Arr((float)(r / n), (float)(g / n), (float)(b / n))).Append(", \"luminance\": ").Append(F((float)(lum / n))).Append(",\n");
            sb.Append("      \"central_lower_third\": { \"region\": [").Append(x0).Append(", ").Append(y0).Append(", ").Append(x1).Append(", ").Append(y1).Append("], \"mean_rgb\": ")
              .Append(Arr((float)(cr / cn), (float)(cg / cn), (float)(cb / cn))).Append(", \"mean_hsv\": ").Append(Arr(mh * 360f, ms, mv)).Append(", \"luminance\": ").Append(F((float)(cl / cn))).Append(" },\n");
            sb.Append("      \"hue_bands\": { ");
            for (int i = 0; i < BandNames.Length; i++) sb.Append('"').Append(BandNames[i]).Append("\": ").Append(F((float)(bands[i] / n))).Append(", ");
            sb.Append("\"grey\": ").Append(F((float)(grey / n))).Append(", \"dark\": ").Append(F((float)(dark / n))).Append(" },\n      ").Append(smoke).Append(" }");
            return sb.ToString();
        }

        // ------------------------------------------------------------------ test board (GOLF_STILLS_BOARD=1; not for proof)

        static GameObject TestBoard(int number)
        {
            var root = new GameObject("Stills test board");
            var (ballAt, aim) = number switch { 8 => (new CoursePoint(0, 0), new Vector3(19, 0, 178)), 9 => (new CoursePoint(0, 0), new Vector3(3, 0, 60)), _ => (new CoursePoint(0, 0), new Vector3(14.3f, 0, 66.2f)) };
            var a = aim.normalized;
            var origin = HoleView.ToWorld(ballAt, 0); origin.y += .03f;
            var right = new Vector3(a.z, 0, -a.x);
            float len = number == 10 ? 22 : number == 8 ? 14 : 70;
            Material M(string n) => GolfLook.GetForHole(n, number);
            string left = number == 9 ? "LK_SCRUB" : "LK_ROUGH", third = number == 8 ? "LK_PATH" : number == 9 ? "LK_SAND" : "LK_GREEN";
            void Strip(string n, float x0, float x1, float tile) => LookPixels.Quad(root, n, M(n), tile, origin + right * x0, origin + right * x1, origin + right * x1 + a * len, origin + right * x0 + a * len, Vector3.up);
            Strip(left, -24, -8, 12); Strip("LK_FAIRWAY", -8, 8, 10); Strip(third, 8, 24, third == "LK_SAND" ? 6 : 5);
            if (number == 10)
            {
                var c = new Vector3(171.1f, .08f, 161.5f);
                LookPixels.Quad(root, "LK_LAVA", M("LK_LAVA"), 24, c + new Vector3(-160, 0, -160), c + new Vector3(-160, 0, 160), c + new Vector3(160, 0, 160), c + new Vector3(160, 0, -160), Vector3.up);
            }
            return root;
        }
    }
}
