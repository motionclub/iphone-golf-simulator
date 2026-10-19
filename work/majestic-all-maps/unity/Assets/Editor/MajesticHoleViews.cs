#if UNITY_EDITOR
// Chat 10 (majestic-all-maps): every view a player sees through a golf hole, 1920x1080, muted, clone only.
//   MAM_OUT=<dir> [MAM_HOLES=7,8,...] [DREAM_WEATHER=Clear] [DREAM_UTC=<unix>] GOLF_MUTE=1 Unity -projectPath <clone>
//     -executeMethod GolfArcade.EditorTools.MajesticHoleViews.Run
// Per hole it writes hNN_<view>.jpg and hNN_cameras.json (position, forward, fov, ball spot and lie per view), so the
// same camera set can be re-shot later for REF_MATCH / NO_EMPTY_VIEW gates.
//   game-framed (ball dropped there, the game's own aim camera): tee, mid, approach, offL, offR, puttFront, puttLeft, puttRight
//   posed: flyOpen + flyH1..flyH3 (HoleIntro.Pose, the real flyover), greenBack (reverse from behind the pin),
//          reverseMid (from mid-fairway back to the tee), pan0/90/180/270 (360 at mid-fairway), crane, map (top-down)
//   live: driveGood / driveBad (StrikeToward, the game's follow + landing cameras at 1.0/2.2/3.6 s and at rest)
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class MajesticHoleViews
    {
        const string Key = "MajesticHoleViews";
        const int W = 1920, H = 1080;
        static IEnumerator<object> job; static int lastFrame = -1;
        static MajesticHoleViews() { EditorApplication.update += Tick; }

        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("MAM_OUT"); if (string.IsNullOrEmpty(o)) throw new ArgumentException("MAM_OUT");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", Path.GetFullPath(o)); SessionState.SetBool(Key, true);
            EditorUtility.audioMasterMute = true;
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DREAM_WEATHER"))) Environment.SetEnvironmentVariable("DREAM_WEATHER", "Clear");
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("DREAM_UTC"))) Environment.SetEnvironmentVariable("DREAM_UTC", "1792263600");
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity"); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false)) return;
            if (!EditorUtility.audioMasterMute) EditorUtility.audioMasterMute = true;
            if (!EditorApplication.isPlaying) return;
            if (AudioListener.volume != 0) AudioListener.volume = 0;
            if (Time.frameCount == lastFrame) return; lastFrame = Time.frameCount;
            try { job ??= Main(); if (!job.MoveNext()) { SessionState.SetBool(Key, false); EditorApplication.Exit(0); } }
            catch (Exception e) { Debug.LogException(e); SessionState.SetBool(Key, false); EditorApplication.Exit(1); }
        }

        static string Out => SessionState.GetString(Key + "out", "/tmp/mam");
        static IEnumerable<object> Wait(int n) { for (int i = 0; i < n; i++) yield return null; }
        static IEnumerable<object> WaitGame(float s) { float t = Time.time + s; int guard = Time.frameCount + 2000; while (Time.time < t && Time.frameCount < guard) yield return null; }

        static GolfGame golf; static CameraRig rig; static Camera cam;
        static RenderTexture rt; static Texture2D tex;
        static readonly StringBuilder json = new(); static bool first;
        static readonly CultureInfo IC = CultureInfo.InvariantCulture;

        static IEnumerator<object> Main()
        {
            while (!golf || !rig || !HoleView.Current) { golf = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>(); yield return null; }
            golf.ChooseHoles(0); golf.Play(); cam = rig.Camera;
            foreach (var o in Wait(30)) yield return o;
            rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            var all = new[] { 7, 8, 9, 12, 15, 13, 14, 17, 18, 19, 20, 10, 16, 21, 22, 23 };
            var env = Environment.GetEnvironmentVariable("MAM_HOLES");
            var holes = string.IsNullOrEmpty(env) ? all : env.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(int.Parse).ToArray();
            foreach (var number in holes)
            {
                var it = HoleViews(number);
                while (true)
                {
                    bool more;
                    try { more = it.MoveNext(); }
                    catch (Exception e) { Debug.LogException(e); Debug.Log($"[MajesticHoleViews] hole {number} FAILED: {e.Message}"); more = false; }
                    if (!more) break; yield return it.Current;
                }
            }
            Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
            Debug.Log("[MajesticHoleViews] all done");
        }

        static IEnumerator<object> HoleViews(int number)
        {
            golf.enabled = true; rig.enabled = true; Canvases(true);
            golf.JumpToHole(number);
            foreach (var o in Wait(20)) yield return o;
            var h = golf.CurrentHole; string name = "h" + number.ToString("00");
            json.Clear(); json.Append("{\n  \"hole\": ").Append(number).Append(", \"name\": \"").Append(h.Name).Append("\", \"par\": ").Append(h.Par).Append(",\n  \"views\": {\n");
            first = true;

            Vector3 W3(CoursePoint p, double up = 0) => HoleView.ToWorld(p, up);
            var tee = W3(h.Tee); var pin = W3(h.Pin);
            var fwd = pin - tee; fwd.y = 0; fwd.Normalize(); var right = Vector3.Cross(Vector3.up, fwd);
            CoursePoint Mid(double f) => DreamCourseLayout.Along(h, f);
            Vector3 DirAt(double f) { var a = W3(Mid(Math.Max(0, f - .03))); var b = W3(Mid(Math.Min(1, f + .03))); var d = b - a; d.y = 0; return d.sqrMagnitude > .01f ? d.normalized : fwd; }

            // ---- game-framed views: the ball dropped on a spot, the game's own aim camera (putter on the green)
            CoursePoint Dry(CoursePoint p, CoursePoint toward)
            {
                for (int i = 0; i < 12; i++) { var l = h.LieAt(p); if (l != CourseLie.Water && l != CourseLie.OutOfBounds) return p; p = new CoursePoint(p.X + (toward.X - p.X) * .15, p.D + (toward.D - p.D) * .15); }
                return p;
            }
            CoursePoint Side(double f, float sideSign, double extra)
            {
                var c = Mid(f); var r = Vector3.Cross(Vector3.up, DirAt(f)) * sideSign; double d = h.FairwayWidth / 2 + extra;
                return Dry(new CoursePoint(c.X + r.x * d, c.D + r.z * d), c);
            }
            // a spot on the line that is in play (not water/out of bounds): walk along the line toward the green, then back
            CoursePoint InPlay(double f)
            {
                for (double k = 0; k <= .3; k += .02)
                    foreach (var g in new[] { f + k, f - k })
                    {
                        if (g < .05 || g > .97) continue;
                        var p = Mid(g); var l = h.LieAt(p);
                        if (l != CourseLie.Water && l != CourseLie.OutOfBounds) return p;
                    }
                return Mid(f);
            }
            var gp = new List<(string, CoursePoint)> { ("tee", h.Tee) };
            if (h.Par >= 4) { gp.Add(("mid", InPlay(.5))); gp.Add(("approach", InPlay(.8))); gp.Add(("offL", Side(.5, -1, 18))); gp.Add(("offR", Side(.5, 1, 18))); }
            else { gp.Add(("approach", InPlay(.55))); gp.Add(("offL", Side(.75, -1, 14))); gp.Add(("offR", Side(.75, 1, 14))); }
            var gfwd = DirAt(.97); var gright = Vector3.Cross(Vector3.up, gfwd);
            CoursePoint OnGreen(Vector3 off) { for (float s = 1; s > .2f; s -= .15f) { var p = new CoursePoint(h.Pin.X + off.x * s, h.Pin.D + off.z * s); if (h.LieAt(p) == CourseLie.Green) return p; } return new CoursePoint(h.Pin.X + off.x * .25, h.Pin.D + off.z * .25); }
            gp.Add(("puttFront", OnGreen(-gfwd * 8))); gp.Add(("puttLeft", OnGreen(-gright * 7))); gp.Add(("puttRight", OnGreen(gright * 7)));
            foreach (var (label, at) in gp)
            {
                if (!Want(label)) continue;
                golf.enabled = true; rig.enabled = true;
                golf.DropBall(at);
                foreach (var o in WaitGame(1.6f)) yield return o;
                Shot(name, label, at);
            }

            // ---- posed views (the game paused so nothing moves the camera)
            golf.enabled = false; rig.enabled = false;
            var intro = new HoleIntro(h);
            int n = intro.Highlights.Count;
            var times = new List<(string, float)> { ("flyOpen", 1.4f) };
            for (int i = 0; i < Math.Min(3, n); i++) times.Add(("flyH" + (i + 1), HoleIntro.Opening + i * HoleIntro.ShotSeconds + .85f));
            foreach (var (label, t) in times)
            {
                if (!Want(label)) continue;
                intro.Pose(true, t, 16f / 9, out var p, out var look, out var fov);
                Pose(p, look, fov); foreach (var o in Wait(3)) yield return o; Shot(name, label, null);
            }
            var gbPos = pin + gfwd * 9 + Vector3.up * 2.2f; gbPos.y = Mathf.Max(gbPos.y, (float)HoleView.GroundHeight(HoleView.ToCourse(gbPos)) + 2.2f);
            Pose(gbPos, W3(Mid(.45), 3), 50); foreach (var o in Wait(3)) yield return o; Shot(name, "greenBack", null);
            if (Environment.GetEnvironmentVariable("MAM_PROBE") == "pop")
            {
                // moving-camera pop check for the far tree cells: every frame rendered as played (n) and with the cells
                // forced to the full mesh (r); a swap shows as extra frame-to-frame change in n that r does not have
                var dir = Path.Combine(Out, "pop"); Directory.CreateDirectory(dir);
                var srt = new RenderTexture(960, 540, 24); var stex = new Texture2D(960, 540, TextureFormat.RGB24, false);
                // the far cells' LOD state as Unity selects it (relative height x LOD bias vs the LOD0 threshold); every switch
                // is logged with the cell's screen rectangle so the analysis measures exactly the swapped area
                var swaps = new StringBuilder("["); bool firstSwap = true; var state = new Dictionary<LODGroup, int>();
                void Track(string seq, int frame)
                {
                    float tanHalf = Mathf.Tan(cam.fieldOfView * .5f * Mathf.Deg2Rad);
                    foreach (var g in GolfArcade.Majestic.MajesticBudget.FarGroups)
                    {
                        var c = g.transform.TransformPoint(g.localReferencePoint); float dist = Vector3.Distance(cam.transform.position, c);
                        float rel = g.size / (2 * Mathf.Max(.01f, dist) * tanHalf) * QualitySettings.lodBias;
                        int lod = rel >= g.GetLODs()[0].screenRelativeTransitionHeight ? 0 : 1;
                        if (state.TryGetValue(g, out int was) && was != lod)
                        {
                            var b = new Bounds(c, Vector3.one * g.size); var mn = new Vector2(1, 1); var mx = new Vector2(0, 0); bool front = false;
                            for (int k2 = 0; k2 < 8; k2++)
                            {
                                var corner = b.center + Vector3.Scale(b.extents, new Vector3((k2 & 1) == 0 ? -1 : 1, (k2 & 2) == 0 ? -1 : 1, (k2 & 4) == 0 ? -1 : 1));
                                var v = cam.WorldToViewportPoint(corner); if (v.z <= 0) continue; front = true;
                                mn = Vector2.Min(mn, new Vector2(v.x, v.y)); mx = Vector2.Max(mx, new Vector2(v.x, v.y));
                            }
                            if (front && mx.x > 0 && mn.x < 1 && mx.y > 0 && mn.y < 1)
                            {
                                if (!firstSwap) swaps.Append(","); firstSwap = false;
                                swaps.Append(string.Format(IC, "{{\"seq\":\"{0}\",\"frame\":{1},\"to\":{2},\"dist\":{3:F1},\"rect\":[{4:F3},{5:F3},{6:F3},{7:F3}]}}", seq, frame, lod, dist, Mathf.Clamp01(mn.x), Mathf.Clamp01(1 - mx.y), Mathf.Clamp01(mx.x), Mathf.Clamp01(1 - mn.y)));
                            }
                        }
                        state[g] = lod;
                    }
                }
                void Grab(string file)
                {
                    cam.aspect = 960 / 540f; cam.targetTexture = srt; cam.Render(); RenderTexture.active = srt;
                    stex.ReadPixels(new Rect(0, 0, 960, 540), 0, 0); stex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                    File.WriteAllBytes(Path.Combine(dir, file), stex.EncodeToJPG(92));
                }
                Canvases(false);   // the HUD (power meter, moving labels) is not what this measures
                float flyLen = HoleIntro.Length(true); int k = 0;
                for (float t = 0; t <= flyLen; t += 1f / 30, k++)
                {
                    intro.Pose(true, t, 16f / 9, out var fp, out var flook, out var ffov); Pose(fp, flook, ffov);
                    foreach (var o in Wait(1)) yield return o;
                    Track($"{name}_fly", k);
                    Grab($"{name}_fly_{k:000}_n.jpg"); GolfArcade.Majestic.MajesticBudget.ForceFarLod(0); Grab($"{name}_fly_{k:000}_r.jpg"); GolfArcade.Majestic.MajesticBudget.ForceFarLod(-1);
                }
                for (int i = 0; i <= 240; i++)
                {
                    float f = .02f + .9f * i / 240f; var at = W3(Mid(f), 5); var d = DirAt(f);
                    Pose(at, at + d * 60 - Vector3.up * 3, 55);
                    foreach (var o in Wait(1)) yield return o;
                    if (i == 0) state.Clear();
                    Track($"{name}_dolly", i);
                    Grab($"{name}_dolly_{i:000}_n.jpg"); GolfArcade.Majestic.MajesticBudget.ForceFarLod(0); Grab($"{name}_dolly_{i:000}_r.jpg"); GolfArcade.Majestic.MajesticBudget.ForceFarLod(-1);
                }
                Canvases(true); Object.DestroyImmediate(srt); Object.DestroyImmediate(stex);
                swaps.Append("]"); File.WriteAllText(Path.Combine(dir, name + "_swaps.json"), swaps.ToString());
                Debug.Log($"[Probe] pop frames written for {name}: fly {k}, dolly 241");
            }
            if (Environment.GetEnvironmentVariable("MAM_PROBE") == "walls")
            {
                Debug.Log($"[Probe] fog {RenderSettings.fog} mode {RenderSettings.fogMode} start {RenderSettings.fogStartDistance} end {RenderSettings.fogEndDistance} density {RenderSettings.fogDensity} colour {RenderSettings.fogColor}");
                var walls = new List<Renderer>();
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                {
                    if (!r.name.StartsWith("CalderaWall")) continue;
                    walls.Add(r);
                    var mf = r.GetComponent<MeshFilter>(); var m = mf ? mf.sharedMesh : null; var c = m && m.isReadable && m.colors.Length > 0 ? m.colors[0] : Color.clear;
                    if (walls.Count <= 8) Debug.Log($"[Probe] {r.name} active={r.gameObject.activeInHierarchy} enabled={r.enabled} mat={(r.sharedMaterial ? r.sharedMaterial.name + "/" + r.sharedMaterial.shader.name : "none")} mesh={(m ? m.name : "none")} col0={c} bounds={r.bounds.center} size={r.bounds.size}");
                }
                Debug.Log($"[Probe] {walls.Count} wall renderers");
                foreach (var r in walls) r.enabled = false;
                foreach (var o in Wait(2)) yield return o; Shot(name, "greenBack_noWalls", null);
                foreach (var r in walls) r.enabled = true;
            }
            if (RefOnly) { Debug.Log("[MajesticHoleViews] " + name + " done (ref views only)"); json.Append("\n  }\n}\n"); File.WriteAllText(Path.Combine(Out, name + "_cameras.json"), json.ToString()); yield break; }
            var mid = W3(Mid(.55), 2);
            Pose(mid, tee + Vector3.up * 2, 55); foreach (var o in Wait(3)) yield return o; Shot(name, "reverseMid", null);
            var md = DirAt(.55);
            for (int a = 0; a < 360; a += 90)
            {
                var d = Quaternion.Euler(0, a, 0) * md;
                Pose(mid, mid + d * 50 + Vector3.up * 1.5f, 75); foreach (var o in Wait(2)) yield return o; Shot(name, "pan" + a, null);
            }
            var c0 = tee - fwd * 40 + Vector3.up * 90; Pose(c0, c0 + fwd * 400 - Vector3.up * 8, 46); foreach (var o in Wait(2)) yield return o; Shot(name, "crane", null);
            // top-down map: straight down over the middle, wide enough for the hole plus a ring of backdrop
            var centre = (tee + pin) * .5f; float span = Mathf.Max(220, Vector3.Distance(tee, pin) * 1.6f);
            cam.transform.position = centre + Vector3.up * (span / (2 * Mathf.Tan(30 * Mathf.Deg2Rad)) + 20);
            cam.transform.rotation = Quaternion.LookRotation(Vector3.down, fwd); cam.fieldOfView = 60;
            foreach (var o in Wait(2)) yield return o; Shot(name, "map", null);

            // ---- live drives: the game's follow and landing cameras, and where real balls come to rest
            Canvases(false);
            var good = h.Par >= 4 ? Mid(.55) : h.Pin;
            var bad = Side(h.Par >= 4 ? .5 : .85, number % 2 == 0 ? 1 : -1, 30);
            foreach (var (label, target) in new[] { ("driveGood", good), ("driveBad", bad) })
            {
                golf.enabled = true; rig.enabled = true;
                golf.DropBall(h.Tee); foreach (var o in WaitGame(1.2f)) yield return o;
                if (golf.Current != GolfGame.State.Aim) { Debug.Log($"[MajesticHoleViews] {name} {label} skipped: state {golf.Current}"); continue; }
                golf.StrikeToward(target);
                float t0 = Time.time; int k = 0;
                foreach (var stamp in new[] { 1.0f, 2.2f, 3.6f })
                {
                    while (Time.time - t0 < stamp && golf.Current == GolfGame.State.Flight) yield return null;
                    if (golf.Current != GolfGame.State.Flight) break;
                    Shot(name, label + "_" + (k++), HoleView.ToCourse(golf.BallPosition));
                }
                float limit = Time.time + 14;
                while (golf.Current == GolfGame.State.Flight && Time.time < limit) yield return null;
                foreach (var o in Wait(2)) yield return o;
                Shot(name, label + "_rest", HoleView.ToCourse(golf.BallPosition));
            }
            Canvases(true);
            json.Append("\n  }\n}\n");
            File.WriteAllText(Path.Combine(Out, name + "_cameras.json"), json.ToString());
            Debug.Log("[MajesticHoleViews] " + name + " done");
        }

        /// MAM_VIEWS=ref: only the five reference views per hole (tee, mid/approach, offL/offR, flyOpen, greenBack).
        static bool RefOnly => Environment.GetEnvironmentVariable("MAM_VIEWS") == "ref";
        static bool Want(string label) => !RefOnly || label is "tee" or "mid" or "approach" or "offL" or "offR" or "flyOpen";

        static void Pose(Vector3 p, Vector3 look, float fov) { cam.transform.position = p; cam.transform.rotation = Quaternion.LookRotation(look - p); cam.fieldOfView = fov; }

        static void Canvases(bool on) { foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = on; }

        static void Shot(string hole, string label, CoursePoint? ball)
        {
            var was = new List<Canvas>();
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (c.enabled) { was.Add(c); c.enabled = false; }
            cam.aspect = W / (float)H;
            cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
            File.WriteAllBytes(Path.Combine(Out, $"{hole}_{label}.jpg"), tex.EncodeToJPG(88));
            foreach (var c in was) c.enabled = true;
            var p = cam.transform.position; var f = cam.transform.forward;
            if (!first) json.Append(",\n"); first = false;
            json.Append(string.Format(IC, "    \"{0}\": {{\"pos\": [{1:F2}, {2:F2}, {3:F2}], \"fwd\": [{4:F4}, {5:F4}, {6:F4}], \"fov\": {7:F1}", label, p.x, p.y, p.z, f.x, f.y, f.z, cam.fieldOfView));
            if (ball.HasValue) json.Append(string.Format(IC, ", \"ball\": [{0:F1}, {1:F1}], \"lie\": \"{2}\"", ball.Value.X, ball.Value.D, golf.CurrentHole.LieAt(ball.Value)));
            json.Append("}");
        }
    }
}
#endif
