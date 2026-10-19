using System;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.EnvironmentArt;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Golf proof captures for the rendered-backgrounds work, 1920x1080, muted:
    ///   BG_OUT=<dir> BG_HOLES=7,13,10 DREAM_UTC=<unix> DREAM_WEATHER=Clear [BG_PERF_AB=1] GOLF_MUTE=1 Unity -projectPath <clone>
    ///     -executeMethod GolfArcade.EditorTools.RenderedBackgroundsGolfCapture.Run
    /// Per hole: tee address, approach, aerial, a long lens down the hole, a 60 m crane pair (parallax), the golfer
    /// painted-vs-rendered pair (same frame) + mask, the texture/sun audit and the interleaved perf A/B.
    [InitializeOnLoad]
    public static class RenderedBackgroundsGolfCapture
    {
        const string Key = "RenderedBackgroundsGolfCapture";
        const int W = 1920, H = 1080;
        static int frame = -1, slot = -1; static double deadline;
        static GolfGame golf; static CameraRig rig; static Camera camera;
        static int[] Holes => (Environment.GetEnvironmentVariable("BG_HOLES") ?? "7,13,10").Split(',').Select(int.Parse).ToArray();
        static string Out => Path.GetFullPath(Environment.GetEnvironmentVariable("BG_OUT") ?? "/tmp/bg_golf");

        static RenderedBackgroundsGolfCapture() { EditorApplication.update += Tick; }

        public static void Run()
        {
            EditorUtility.audioMasterMute = true;
            Directory.CreateDirectory(Out);
            SessionState.SetBool(Key, true);
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false) || !EditorApplication.isPlaying) return;
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;
            try
            {
                if (!golf)
                {
                    golf = Object.FindFirstObjectByType<GolfGame>(); rig = Object.FindFirstObjectByType<CameraRig>();
                    if (!golf || !rig || !HoleView.Current) { golf = null; return; }
                    golf.ChooseHoles(0); golf.Play(); camera = rig.Camera; Next(); return;
                }
                if (Time.frameCount - frame < 40) return;
                if (EditorApplication.timeSinceStartup > deadline) throw new TimeoutException("hole did not settle");
                Capture(); Next();
            }
            catch (Exception e) { Debug.LogException(e); SessionState.SetBool(Key, false); EditorApplication.Exit(1); }
        }

        static void Next()
        {
            slot++;
            if (slot >= Holes.Length) { SessionState.SetBool(Key, false); EditorApplication.Exit(0); return; }
            golf.enabled = true; rig.enabled = true;
            golf.JumpToHole(Holes[slot]); golf.DropBall(golf.CurrentHole.Tee);
            frame = Time.frameCount; deadline = EditorApplication.timeSinceStartup + 240;
        }

        static void Capture()
        {
            var h = golf.CurrentHole; string name = "hole" + h.Number.ToString("00");
            golf.enabled = false; rig.enabled = false;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            camera.aspect = W / (float)H;
            var log = new StringBuilder();
            var sun = RenderSettings.sun;
            if (sun)
            {
                var d = -sun.transform.forward;
                log.AppendLine($"sun dir_to_light={d:F4} azimuth_deg={Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg:F2} elevation_deg={Mathf.Asin(d.y) * Mathf.Rad2Deg:F2} colour={sun.color} intensity={sun.intensity:F3}");
            }
            var sd = Shader.GetGlobalVector("_RSkySunDir");
            if (RenderSettings.skybox && RenderSettings.skybox.shader.name == "GolfArcade/RenderedSky")
            {
                var sc = Shader.GetGlobalVector("_RSkyScatterDir");
                log.AppendLine($"rendered_sky_disc dir={((Vector3)sd):F4}");
                log.AppendLine($"rendered_sky_scatter dir={((Vector3)sc):F4} azimuth_deg={Mathf.Atan2(sc.x, sc.z) * Mathf.Rad2Deg:F2}");
            }
            log.AppendLine($"skybox={(RenderSettings.skybox ? RenderSettings.skybox.name + " / " + RenderSettings.skybox.shader.name : "none")}");
            log.AppendLine($"fog={RenderSettings.fog} {RenderSettings.fogColor} {RenderSettings.fogStartDistance}-{RenderSettings.fogEndDistance} far={camera.farClipPlane} hole={h.Number} utc={DreamEnvironment.Utc}");
            var seen = new System.Collections.Generic.HashSet<string>();
            void Audit(Material m, string who)
            {
                if (!m) return;
                foreach (var id in m.GetTexturePropertyNameIDs())
                {
                    var t = m.GetTexture(id); if (!t) continue;
                    if (seen.Add(t.name + m.shader.name + id)) log.AppendLine($"tex {t.name} {t.width}x{t.height} slot={id} shader={m.shader.name} mat={m.name} on={who}");
                }
            }
            Audit(RenderSettings.skybox, "skybox");
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                if (r.enabled && r.gameObject.activeInHierarchy) foreach (var m in r.sharedMaterials) Audit(m, r.name);

            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            void Shot(string label)
            {
                camera.targetTexture = rt; camera.Render(); RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null; camera.targetTexture = null;
                File.WriteAllBytes($"{Out}/{name}_{label}.png", tex.EncodeToPNG());
                log.AppendLine($"shot {label} pos={camera.transform.position:F2} rot={camera.transform.eulerAngles:F2} fov={camera.fieldOfView:F1}");
            }
            void Address(CoursePoint at) { rig.FrameAddress(HoleView.ToWorld(at, .06), HoleView.ToWorld(h.Pin) - HoleView.ToWorld(at), false); rig.SnapNext(); rig.ApplyFrame(); }
            Address(h.Tee); Shot("01_tee");
            var addrPos = camera.transform.position; var addrRot = camera.transform.rotation; float addrFov = camera.fieldOfView;
            Address(DreamCourseLayout.Along(h, .85)); Shot("02_approach");
            var tee = HoleView.ToWorld(h.Tee); var pin = HoleView.ToWorld(h.Pin); var mid = (tee + pin) * .5f;
            camera.transform.position = mid + new Vector3(150, 230, -180); camera.transform.LookAt(mid); camera.fieldOfView = 50; Shot("03_aerial");
            var down = pin - tee; down.y = 0; down.Normalize();
            var eye = tee + Vector3.up * 1.7f;
            camera.transform.position = eye; camera.transform.rotation = Quaternion.LookRotation(down + Vector3.up * .05f); camera.fieldOfView = 20; Shot("04_longlens");
            // crane pair (parallax): 30 yd up behind the tee, looking down the hole, then 60 yd to the side
            var right = Vector3.Cross(Vector3.up, down);
            var c0 = tee - down * 40 + Vector3.up * 90; var look = c0 + down * 400 - Vector3.up * 8;   // above crater rims
            camera.fieldOfView = 46;
            camera.transform.position = c0; camera.transform.rotation = Quaternion.LookRotation(look - c0); Shot("05_crane0");
            camera.transform.position = c0 + right * 60; camera.transform.rotation = Quaternion.LookRotation(look - c0); Shot("05_crane60");
            foreach (var (lname, top0, radius) in RenderedBackdrop.Landmarks)
            {
                var top = lname.StartsWith("Cloud") ? RenderedBackdrop.Drifted(top0) : top0;
                camera.transform.position = c0; camera.transform.rotation = Quaternion.LookRotation(look - c0);
                var s0 = Vector3.Scale(camera.WorldToViewportPoint(top), new Vector3(W, H, 1));
                camera.transform.position = c0 + right * 60;
                var s2 = Vector3.Scale(camera.WorldToViewportPoint(top), new Vector3(W, H, 1));
                if (s0.z > 0 && s0.x > 80 && s0.x < W - 80 && H - s0.y > 40 && H - s0.y < H - 40)
                    log.AppendLine($"landmark crane {lname} dist_m={Vector3.Distance(c0, top):F0} radius_m={radius:F0} a_px=({s0.x:F2},{H - s0.y:F2}) b_px=({s2.x:F2},{H - s2.y:F2}) predicted_dx={s2.x - s0.x:F3}");
            }
            // golfer: painted vs rendered in the same frame + mask
            camera.transform.SetPositionAndRotation(addrPos, addrRot); camera.fieldOfView = addrFov;
            var rendered = RenderSettings.skybox;
            if (rendered && rendered.shader.name == "GolfArcade/RenderedSky")
            {
                var painted = new Material(Shader.Find("GolfArcade/DreamSky"));
                painted.SetTexture("_Panorama", Resources.Load<Texture2D>("Environment/LuminousCoast/ArchipelagoSky")); painted.SetFloat("_Day", 1);
                var backdrop = Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None).Where(t => t.name.StartsWith("Rendered backdrop")).Select(t => t.gameObject).ToArray();
                float ts = Time.timeScale; Time.timeScale = 0;
                foreach (var a in Object.FindObjectsByType<Animator>(FindObjectsSortMode.None)) a.speed = 0;
                RenderSettings.skybox = painted; foreach (var g in backdrop) g.SetActive(false); Shot("10_char_A");
                RenderSettings.skybox = rendered; foreach (var g in backdrop) g.SetActive(true); Shot("10_char_B");
                var keep = Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None).Where(r => r.enabled).Cast<Renderer>().ToHashSet();
                var hidden = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.enabled && !keep.Contains(r)).ToList();
                foreach (var r in hidden) r.enabled = false;
                var flags = camera.clearFlags; camera.clearFlags = CameraClearFlags.SolidColor; var bg = camera.backgroundColor; camera.backgroundColor = Color.black;
                Shot("10_char_mask");
                camera.clearFlags = flags; camera.backgroundColor = bg; foreach (var r in hidden) r.enabled = true;
                foreach (var a in Object.FindObjectsByType<Animator>(FindObjectsSortMode.None)) a.speed = 1;
                Time.timeScale = ts;
                if (Environment.GetEnvironmentVariable("BG_PERF_AB") == "1")
                {
                    var prt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
                    var ptex = new Texture2D(1, 1, TextureFormat.RGB24, false);
                    var shots = new (string, Vector3, Quaternion, float)[] { ("tee", addrPos, addrRot, addrFov), ("crane", c0, Quaternion.LookRotation(look - c0), 46) };
                    foreach (var (label, p, q, f) in shots)
                    {
                        camera.transform.SetPositionAndRotation(p, q); camera.fieldOfView = f;
                        var A = new System.Collections.Generic.List<double>(); var B = new System.Collections.Generic.List<double>();
                        for (int round = 0; round < 10; round++)
                            for (int side = 0; side < 2; side++)
                            {
                                bool useB = side == (round & 1);
                                RenderSettings.skybox = useB ? rendered : painted; foreach (var g in backdrop) g.SetActive(useB);
                                for (int i = 0; i < 22; i++)
                                {
                                    var sw = System.Diagnostics.Stopwatch.StartNew();
                                    camera.targetTexture = prt; camera.Render(); RenderTexture.active = prt;
                                    ptex.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); ptex.Apply(); RenderTexture.active = null; camera.targetTexture = null;
                                    sw.Stop(); if (i >= 2) (useB ? B : A).Add(sw.Elapsed.TotalMilliseconds);
                                }
                            }
                        A.Sort(); B.Sort();
                        log.AppendLine($"perfAB {label} {W}x{H} painted_median_ms={A[A.Count / 2]:F3} rendered_median_ms={B[B.Count / 2]:F3} delta_median_ms={B[B.Count / 2] - A[A.Count / 2]:F3} n={A.Count}/{B.Count}");
                    }
                    RenderSettings.skybox = rendered; foreach (var g in backdrop) g.SetActive(true);
                    Object.DestroyImmediate(prt);
                }
                Object.DestroyImmediate(painted);
            }
            File.WriteAllText($"{Out}/{name}_capture.txt", log.ToString());
            Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
            Debug.Log("[BgGolfCapture] wrote " + name);
        }
    }
}
