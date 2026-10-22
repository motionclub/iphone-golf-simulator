using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using GolfArcade.Tennis;

namespace GolfArcade.EditorTools
{
    /// Proof captures for the rendered-backgrounds work (work/rendered-backgrounds), always 1920x1080:
    ///   HERO_VENUE=resort BG_OUT=<dir> DREAM_UTC=<unix> DREAM_WEATHER=Clear GOLF_MUTE=1 Unity -projectPath <clone>
    ///     -executeMethod GolfArcade.EditorTools.RenderedBackgroundsCapture.Run
    /// Every camera that sees the background: chase (gameplay + serve), elevated, the long-lens
    /// stare-downs, the emote intro, three flyover points, a 2 m dolly pair (parallax gate), a horizon
    /// ring, a character crop pair, and a perf proxy (BG_PERF=1: synchronous 1920x1080 renders).
    /// Editor audio is muted for the whole run. Never writes outside BG_OUT.
    [InitializeOnLoad]
    public static class RenderedBackgroundsCapture
    {
        const string Flag = "RenderedBackgroundsCapture";
        const int W = 1920, H = 1080;
        static int frame, lastFrame = -1;
        static System.Collections.IEnumerator capture;
        static readonly System.Collections.Generic.Stack<System.Collections.IEnumerator> steps = new();
        static string Out => Path.GetFullPath(System.Environment.GetEnvironmentVariable("BG_OUT") ?? "/tmp/bg_capture");

        static RenderedBackgroundsCapture() { EditorApplication.update += Tick; }

        public static void Run()
        {
            EditorUtility.audioMasterMute = true;
            frame = 0; lastFrame = -1; capture = null; steps.Clear();
            Directory.CreateDirectory(Out);
            EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity");
            SessionState.SetBool(Flag, true);
            EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying) return;
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            if (Time.frameCount == lastFrame) return; lastFrame = Time.frameCount;
            var game = Object.FindFirstObjectByType<TennisGame>();
            if (!game || !game.Initialized) return;
            if (++frame < 60) return;
            try
            {
                if (capture == null) { capture = Capture(game); steps.Push(capture); }
                while (steps.Count > 0)
                {
                    var step = steps.Peek();
                    if (!step.MoveNext()) { steps.Pop(); continue; }
                    if (step.Current is System.Collections.IEnumerator nested) { steps.Push(nested); continue; }
                    return;
                }
                Finish(0);
            }
            catch (System.Exception e) { Debug.LogError("[BgCapture] " + e); Finish(1); }
        }

        static void Finish(int result)
        {
            SessionState.SetBool(Flag, false);
            if (Application.isBatchMode) EditorApplication.Exit(result); else EditorApplication.isPlaying = false;
        }

        static string Only => System.Environment.GetEnvironmentVariable("BG_SHOTS");

        static System.Collections.IEnumerator Capture(TennisGame game)
        {
            foreach (var lod in Object.FindObjectsByType<HeroGarmentLOD>(FindObjectsSortMode.None)) lod.Prepare(game.GameplayCamera);
            foreach (var skin in Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None)) skin.updateWhenOffscreen = true;
            var presentation = game.GetComponent<TennisPresentation>(); if (presentation) presentation.Finish();
            var venue = TennisVenue.Current.ToString().ToLowerInvariant();
            game.enabled = false;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            var cam = game.GameplayCamera;
            cam.aspect = W / (float)H;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            var log = new StringBuilder();
            var sun = RenderSettings.sun;
            if (sun)
            {
                var d = -sun.transform.forward;
                float az = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg, el = Mathf.Asin(d.y) * Mathf.Rad2Deg;
                log.AppendLine($"sun dir_to_light={d:F4} azimuth_deg={az:F2} elevation_deg={el:F2} colour={sun.color} intensity={sun.intensity:F3}");
            }
            var skyDir = Shader.GetGlobalVector("_RSkySunDir");
            if (skyDir.sqrMagnitude > 0)
            {
                float az = Mathf.Atan2(skyDir.x, skyDir.z) * Mathf.Rad2Deg, el = Mathf.Asin(Mathf.Clamp(skyDir.y, -1, 1)) * Mathf.Rad2Deg;
                log.AppendLine($"rendered_sky_disc dir={((Vector3)skyDir):F4} azimuth_deg={az:F2} elevation_deg={el:F2}");
                var sc = Shader.GetGlobalVector("_RSkyScatterDir");
                log.AppendLine($"rendered_sky_scatter dir={((Vector3)sc):F4} azimuth_deg={Mathf.Atan2(sc.x, sc.z) * Mathf.Rad2Deg:F2}");
            }
            log.AppendLine($"skybox={(RenderSettings.skybox ? RenderSettings.skybox.name + " / " + RenderSettings.skybox.shader.name : "none")}");
            log.AppendLine($"fog={RenderSettings.fog} {RenderSettings.fogMode} {RenderSettings.fogColor} {RenderSettings.fogStartDistance}-{RenderSettings.fogEndDistance} far={cam.farClipPlane} near={cam.nearClipPlane}");
            log.AppendLine($"dream_utc={System.Environment.GetEnvironmentVariable("DREAM_UTC")} weather={TennisConditions.Weather} rendered_sky_env={System.Environment.GetEnvironmentVariable("RENDERED_SKY")}");
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                if (r.name.StartsWith("Ocean") || r.name.Contains("Sea") || r.name == "Rendered clouds")
                    log.AppendLine($"renderer {r.name} enabled={r.enabled} bounds={r.bounds.center:F1}/{r.bounds.size:F1}");
            // texture audit: every texture bound on any enabled renderer's material + the skybox + globals
            var seen = new System.Collections.Generic.HashSet<string>();
            void Audit(Material m, string who)
            {
                if (!m) return;
                foreach (var id in m.GetTexturePropertyNameIDs())
                {
                    var t = m.GetTexture(id); if (!t) continue;
                    string key = t.name + " <- " + m.shader.name + " " + id;
                    if (seen.Add(key)) log.AppendLine($"tex {t.name} {t.width}x{t.height} slot={id} shader={m.shader.name} mat={m.name} on={who}");
                }
            }
            Audit(RenderSettings.skybox, "skybox");
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                if (r.enabled && r.gameObject.activeInHierarchy) foreach (var m in r.sharedMaterials) Audit(m, r.name);
            foreach (var g in new[] { "_SkyMap", "_ReflectionMap", "_Panorama", "_SkyPanorama" }) { var t = Shader.GetGlobalTexture(g); if (t) log.AppendLine($"global {g}={t.name}"); }

            System.Collections.IEnumerator Shot(string label, Vector3 pos, Vector3 look, float fov)
            {
                if (!string.IsNullOrEmpty(Only) && System.Array.IndexOf(Only.Split(','), label) < 0) yield break;
                cam.transform.position = pos; cam.transform.rotation = Quaternion.LookRotation(look - pos); cam.fieldOfView = fov;
                for (int warm = 0; warm < 3; warm++) yield return null;
                cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                File.WriteAllBytes($"{Out}/{venue}_{label}.png", tex.EncodeToPNG());
                log.AppendLine($"shot {label} pos={pos:F3} look={look:F3} fov={fov}");
            }

            var player = game.Player; var rival = game.Opponent;
            TennisShoulderCamera.Frame(player.transform.position, false, Vector3.zero, false, cam.aspect, out var gp, out var gl, out var gf);
            yield return Shot("01_gameplay", gp, gl, gf);
            // the parallax pairs are taken with time frozen: the clouds drift with the wind between frames
            float keepScale = Time.timeScale; Time.timeScale = 0;
            yield return Shot("02_dolly0", gp, gl, gf);
            yield return Shot("02_dolly2", gp + Vector3.right * 2, gl + Vector3.right * 2, gf);
            // PARALLAX: predicted screen position of every distant landmark for a 2 m dolly (brief) and a 60 m
            // crane move (drone scale), both from the camera maths; the gate measures the real image shift.
            yield return Shot("02_crane0", new Vector3(0, 90, -40), new Vector3(0, 82, 400), 46);
            yield return Shot("02_crane60", new Vector3(60, 90, -40), new Vector3(60, 82, 400), 46);
            yield return Shot("02_craneB0", new Vector3(0, 90, -40), new Vector3(0, 82, -480), 46);
            yield return Shot("02_craneB60", new Vector3(60, 90, -40), new Vector3(60, 82, -480), 46);
            foreach (var (lname, top0, radius) in GolfArcade.EnvironmentArt.RenderedBackdrop.Landmarks)
                foreach (var (tag, p0, l0, f0, off) in new[] { ("dolly", gp, gl, gf, Vector3.right * 2), ("crane", new Vector3(0, 90, -40), new Vector3(0, 82, 400), 46f, Vector3.right * 60), ("craneB", new Vector3(0, 90, -40), new Vector3(0, 82, -480), 46f, Vector3.right * 60) })
                {
                    var top = lname.StartsWith("Cloud") ? GolfArcade.EnvironmentArt.RenderedBackdrop.Drifted(top0) : top0;
                    cam.transform.position = p0; cam.transform.rotation = Quaternion.LookRotation(l0 - p0); cam.fieldOfView = f0;
                    var s0 = Vector3.Scale(cam.WorldToViewportPoint(top), new Vector3(W, H, 1));   // the RT size, not the batch screen
                    cam.transform.position = p0 + off;
                    var s2 = Vector3.Scale(cam.WorldToViewportPoint(top), new Vector3(W, H, 1));
                    if (s0.z > 0 && s0.x > 80 && s0.x < W - 80 && H - s0.y > 40 && H - s0.y < H - 40)
                        log.AppendLine($"landmark {tag} {lname} dist_m={Vector3.Distance(p0, top):F0} radius_m={radius:F0} a_px=({s0.x:F2},{H - s0.y:F2}) b_px=({s2.x:F2},{H - s2.y:F2}) predicted_dx={s2.x - s0.x:F3}");
                }
            Time.timeScale = keepScale;
            TennisShoulderCamera.Frame(player.transform.position, false, Vector3.zero, false, cam.aspect, out var ep, out var el2, out var ef, true);
            yield return Shot("03_elevated", ep, el2, ef);
            if (rival)
            {
                var head = rival.transform.position + Vector3.up * 1.36f;
                var fwd = rival.transform.forward; fwd.y = 0; fwd.Normalize();
                var p = rival.transform.position + Quaternion.AngleAxis(6, Vector3.up) * fwd * 2.55f + Vector3.up * 1.5f;
                var lk = head - Vector3.Cross(Vector3.up, (head - p).normalized) * .42f;
                yield return Shot("04_stare_rival", p, lk, 27);
                var ip = rival.transform.position + Quaternion.AngleAxis(9, Vector3.up) * fwd * 4.8f + Vector3.up * 1.25f;
                yield return Shot("05_intro_rival", ip, rival.transform.position + Vector3.up * .95f, 30);
            }
            {
                var head = player.transform.position + Vector3.up * 1.36f;
                var fwd = player.transform.forward; fwd.y = 0; fwd.Normalize();
                var p = player.transform.position + Quaternion.AngleAxis(-6, Vector3.up) * fwd * 2.55f + Vector3.up * 1.5f;
                var lk = head + Vector3.Cross(Vector3.up, (head - p).normalized) * .42f;
                yield return Shot("06_stare_player", p, lk, 27);
            }
            foreach (var k in new[] { 0f, .35f, .7f })
            {
                TennisVenue.Drone(k * .92f, out var p, out var l, out var f);
                yield return Shot($"07_drone{Mathf.RoundToInt(k * 100):00}", p, l, f);
            }
            for (int i = 0; i < 4; i++)
            {
                var dir = Quaternion.Euler(0, i * 90, 0) * Vector3.forward;
                var eye = new Vector3(0, 1.7f, 0);
                yield return Shot($"08_ring{i * 90:000}", eye, eye + dir * 10 + Vector3.up * 1.2f, 70);
            }
            yield return Shot("09_longlens", new Vector3(0, 1.7f, -12), new Vector3(0, 6f, 400), 14);
            // character crop (CHAR_SAME): the player from the chase camera, the rival at the stare-down
            if (rival)
            {
                var head = rival.transform.position + Vector3.up * 1.1f;
                yield return Shot("10_char_rival", head + rival.transform.forward * 3.2f + Vector3.up * .2f, head, 30);
                // CHAR_SAME: the same frame (no time passes, same pose) rendered with the painted sky and no
                // backdrop (A) and with the rendered sky + backdrop (B), plus a mask with only the rival drawn.
                void Now(string label)
                {
                    cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt;
                    tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                    File.WriteAllBytes($"{Out}/{venue}_{label}.png", tex.EncodeToPNG());
                }
                if (RenderSettings.skybox && RenderSettings.skybox.shader.name == "GolfArcade/RenderedSky")
                {
                    var rendered = RenderSettings.skybox;
                    var painted = new Material(Shader.Find("GolfArcade/DreamSky"));
                    painted.SetTexture("_Panorama", Resources.Load<Texture2D>("Environment/LuminousCoast/ArchipelagoSky")); painted.SetFloat("_Day", 1);
                    var backdrop = GameObject.Find("Rendered backdrop");
                    var simTime = Time.timeScale; Time.timeScale = 0;
                    foreach (var anim in Object.FindObjectsByType<Animator>(FindObjectsSortMode.None)) anim.speed = 0;
                    RenderSettings.skybox = painted; if (backdrop) backdrop.SetActive(false); Now("10_char_A");
                    RenderSettings.skybox = rendered; if (backdrop) backdrop.SetActive(true); Now("10_char_B");
                    var keep = new System.Collections.Generic.HashSet<Renderer>(rival.GetComponentsInChildren<Renderer>());
                    var hidden = new System.Collections.Generic.List<Renderer>();
                    foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)) if (r.enabled && !keep.Contains(r)) { r.enabled = false; hidden.Add(r); }
                    var flags = cam.clearFlags; var bg = cam.backgroundColor; cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black;
                    Now("10_char_mask");
                    cam.clearFlags = flags; cam.backgroundColor = bg; foreach (var r in hidden) r.enabled = true;
                    foreach (var anim in Object.FindObjectsByType<Animator>(FindObjectsSortMode.None)) anim.speed = 1;
                    Time.timeScale = simTime; Object.DestroyImmediate(painted);
                }
            }
            if (System.Environment.GetEnvironmentVariable("BG_PERF") == "1")
            {
                // Editor perf proxy at the target resolution: synchronous 1920x1080 renders of the gameplay
                // frame, each forced to complete with a 1-pixel readback. Same machine before/after.
                var prt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
                var ptex = new Texture2D(1, 1, TextureFormat.RGB24, false);
                cam.transform.position = gp; cam.transform.rotation = Quaternion.LookRotation(gl - gp); cam.fieldOfView = gf;
                yield return null;
                foreach (var label in new[] { "gameplay", "ring000" })
                {
                    if (label == "ring000") { var eye = new Vector3(0, 1.7f, 0); cam.transform.position = eye; cam.transform.rotation = Quaternion.LookRotation(Vector3.forward * 10 + Vector3.up * 1.2f); cam.fieldOfView = 70; }
                    var times = new System.Collections.Generic.List<double>();
                    for (int i = 0; i < 160; i++)
                    {
                        var sw = System.Diagnostics.Stopwatch.StartNew();
                        cam.targetTexture = prt; cam.Render(); RenderTexture.active = prt;
                        ptex.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); ptex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                        sw.Stop(); if (i >= 40) times.Add(sw.Elapsed.TotalMilliseconds);
                        if (i % 20 == 19) yield return null;
                    }
                    times.Sort();
                    log.AppendLine($"perf {label} {W}x{H} median_ms={times[times.Count / 2]:F3} p10_ms={times[times.Count / 10]:F3} p90_ms={times[times.Count * 9 / 10]:F3} n={times.Count}");
                }
                int rend = 0; long tris = 0; var planes = GeometryUtility.CalculateFrustumPlanes(cam);
                foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
                {
                    if (!r.enabled || !r.gameObject.activeInHierarchy || !GeometryUtility.TestPlanesAABB(planes, r.bounds)) continue;
                    var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh) continue;
                    rend++; for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) tris += mf.sharedMesh.GetIndexCount(s) / 3;
                }
                log.AppendLine($"perf frustum(ring000) mesh renderers={rend} tris={tris} (static batches counted per member)");
                var bd = GameObject.Find("Rendered backdrop");
                if (bd)
                {
                    long bt = 0; int bn = 0;
                    foreach (var mf in bd.GetComponentsInChildren<MeshFilter>()) { bn++; for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) bt += mf.sharedMesh.GetIndexCount(s) / 3; }
                    log.AppendLine($"perf rendered backdrop renderers={bn} tris={bt}");
                }
                Object.DestroyImmediate(prt);
            }
            if (System.Environment.GetEnvironmentVariable("BG_PERF_AB") == "1" && RenderSettings.skybox && RenderSettings.skybox.shader.name == "GolfArcade/RenderedSky")
            {
                // Interleaved A/B on one machine state: A = painted DreamSky panorama, no rendered backdrop;
                // B = the rendered sky + backdrop. 10 rounds x 20 renders each at 1920x1080, per camera.
                var rendered = RenderSettings.skybox;
                var painted = new Material(Shader.Find("GolfArcade/DreamSky"));
                painted.SetTexture("_Panorama", Resources.Load<Texture2D>("Environment/LuminousCoast/ArchipelagoSky"));
                painted.SetFloat("_Day", 1);
                var backdrop = GameObject.Find("Rendered backdrop");
                var prt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
                var ptex = new Texture2D(1, 1, TextureFormat.RGB24, false);
                var shots = new (string, Vector3, Vector3, float)[] { ("gameplay", gp, gl, gf), ("ring000", new Vector3(0, 1.7f, 0), new Vector3(0, 2.9f, 10), 70) };
                foreach (var (label, pos, look, fov) in shots)
                {
                    cam.transform.position = pos; cam.transform.rotation = Quaternion.LookRotation(look - pos); cam.fieldOfView = fov;
                    var a = new System.Collections.Generic.List<double>(); var b = new System.Collections.Generic.List<double>();
                    for (int round = 0; round < 10; round++)
                        for (int side = 0; side < 2; side++)
                        {
                            bool useB = side == (round & 1);
                            RenderSettings.skybox = useB ? rendered : painted; if (backdrop) backdrop.SetActive(useB);
                            for (int i = 0; i < 22; i++)
                            {
                                var sw = System.Diagnostics.Stopwatch.StartNew();
                                cam.targetTexture = prt; cam.Render(); RenderTexture.active = prt;
                                ptex.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); ptex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                                sw.Stop(); if (i >= 2) (useB ? b : a).Add(sw.Elapsed.TotalMilliseconds);
                            }
                            yield return null;
                        }
                    a.Sort(); b.Sort();
                    double ma = a[a.Count / 2], mb = b[b.Count / 2], la = a[a.Count / 4], lb = b[b.Count / 4];
                    log.AppendLine($"perfAB {label} {W}x{H} painted_median_ms={ma:F3} rendered_median_ms={mb:F3} delta_median_ms={mb - ma:F3} painted_q1_ms={la:F3} rendered_q1_ms={lb:F3} delta_q1_ms={lb - la:F3} n={a.Count}/{b.Count}");
                }
                RenderSettings.skybox = rendered; if (backdrop) backdrop.SetActive(true);
                Object.DestroyImmediate(prt); Object.DestroyImmediate(painted);
            }
            File.WriteAllText($"{Out}/{venue}_capture.txt", log.ToString());
            Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
            Debug.Log("[BgCapture] wrote " + Out);
        }
    }
}
