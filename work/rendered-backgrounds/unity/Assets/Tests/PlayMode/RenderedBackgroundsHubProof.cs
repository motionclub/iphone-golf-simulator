using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.EnvironmentArt;
using GolfArcade.Game;
using GolfArcade.Hub;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// Plaza hub proof for the rendered backgrounds (work/rendered-backgrounds): 1920x1080 stills from the hub cameras,
    /// the sun/sky audit, a 60 m crane pair (parallax), the hero painted-vs-rendered pair (same frame) and the
    /// interleaved perf A/B. Runs only with BG_OUT set: BG_OUT=<dir> [BG_PERF_AB=1] GOLF_MUTE=1 Unity -runTests ...
    public class RenderedBackgroundsHubProof
    {
        const int W = 1920, H = 1080;
        static string Dir => Environment.GetEnvironmentVariable("BG_OUT");
        GameObject host;

        [TearDown] public void Clean() { HubWorld.EditorDriven = false; if (host) Object.DestroyImmediate(host); Time.timeScale = 1; }

        [UnityTest, Timeout(600000)] public IEnumerator Plaza()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("BG_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "hub-test", action = "start", sport = "hub", female = false, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF" }));
            for (int i = 0; i < 900 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); var p = hub.Player; var cam = hub.Camera;
            if (hub.Arriving) { hub.HurryArrival(); for (int i = 0; i < 300 && hub.Arriving; i++) yield return null; }
            p.Teleport(HubLayout.Spawn, 0); yield return new WaitForSeconds(1.2f);
            var log = new StringBuilder();
            var sun = RenderSettings.sun;
            if (sun) { var d = -sun.transform.forward; log.AppendLine($"sun dir_to_light={d:F4} azimuth_deg={Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg:F2} elevation_deg={Mathf.Asin(d.y) * Mathf.Rad2Deg:F2}"); }
            var dome = GameObject.Find("Rendered sky dome");
            if (dome)
            {
                var sd = Shader.GetGlobalVector("_RSkySunDir"); var sc = Shader.GetGlobalVector("_RSkyScatterDir");
                log.AppendLine($"rendered_sky_disc dir={((Vector3)sd):F4}");
                log.AppendLine($"rendered_sky_scatter dir={((Vector3)sc):F4} azimuth_deg={Mathf.Atan2(sc.x, sc.z) * Mathf.Rad2Deg:F2}");
            }
            var oldSun = GameObject.Find("Sun"); log.AppendLine($"old painted sun disc present={(oldSun && oldSun.activeInHierarchy)}");
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                if (r.enabled && r.gameObject.activeInHierarchy)
                    foreach (var m in r.sharedMaterials) if (m) foreach (var id in m.GetTexturePropertyNameIDs()) { var t = m.GetTexture(id); if (t && (t.name == "Hub sky" || RenderedSky.IsPainted(t))) log.AppendLine($"tex {t.name} slot={id} shader={m.shader.name} on={r.name}"); }

            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            void Now(string name)
            {
                var prevA = cam.aspect; cam.aspect = W / (float)H; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = prevA;
                RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
                File.WriteAllBytes(Path.Combine(Dir, "hub_" + name + ".png"), tex.EncodeToPNG());
            }
            Now("01_spawn");
            var pos = cam.transform.position; var rot = cam.transform.rotation; float fov = cam.fieldOfView;
            void Shot(string name, Vector3 at, Vector3 lookAt) { cam.transform.SetPositionAndRotation(at, Quaternion.LookRotation(lookAt - at)); Now(name); }
            Shot("02_overview", new Vector3(0, 30, -30), new Vector3(0, 0, 4));
            Shot("03_play_door", new Vector3(2, 3.0f, 3), new Vector3(0, 4.5f, 15));
            Shot("04_overview_low", new Vector3(-22, 9, -26), new Vector3(0, 1, 4));
            Shot("05_toward_light", new Vector3(0, 4, 0), new Vector3(0, 4, 0) + new Vector3(HubArt.SunLightDir.x, .25f, HubArt.SunLightDir.z) * 10);
            var c0 = new Vector3(0, 30, -40); var look = new Vector3(0, 22, 400);
            cam.fieldOfView = 46;
            Shot("06_crane0", c0, look);
            Shot("06_crane60", c0 + Vector3.right * 60, look + Vector3.right * 60);
            foreach (var (lname, top0, radius) in RenderedBackdrop.Landmarks)
            {
                var top = lname.StartsWith("Cloud") ? RenderedBackdrop.Drifted(top0) : top0;
                cam.transform.SetPositionAndRotation(c0, Quaternion.LookRotation(look - c0)); cam.aspect = W / (float)H;
                var s0 = Vector3.Scale(cam.WorldToViewportPoint(top), new Vector3(W, H, 1));
                cam.transform.position = c0 + Vector3.right * 60;
                var s2 = Vector3.Scale(cam.WorldToViewportPoint(top), new Vector3(W, H, 1));
                if (s0.z > 0 && s0.x > 80 && s0.x < W - 80 && H - s0.y > 40 && H - s0.y < H - 40)
                    log.AppendLine($"landmark crane {lname} dist_m={Vector3.Distance(c0, top):F0} radius_m={radius:F0} a_px=({s0.x:F2},{H - s0.y:F2}) b_px=({s2.x:F2},{H - s2.y:F2}) predicted_dx={s2.x - s0.x:F3}");
            }
            cam.transform.SetPositionAndRotation(pos, rot); cam.fieldOfView = fov;
            // hero: the painted dome vs the rendered one, same frame
            if (dome)
            {
                var domeR = dome.GetComponent<MeshRenderer>(); var rendered = domeR.sharedMaterial;
                var painted = new Material(Shader.Find("Universal Render Pipeline/Unlit")); painted.SetTexture("_BaseMap", HubArt.SkyTexture);
                var backdrop = GameObject.Find("Rendered backdrop");
                Time.timeScale = 0; foreach (var a in Object.FindObjectsByType<Animator>(FindObjectsSortMode.None)) a.speed = 0;
                domeR.sharedMaterial = painted; if (backdrop) backdrop.SetActive(false); Now("10_char_A");
                domeR.sharedMaterial = rendered; if (backdrop) backdrop.SetActive(true); Now("10_char_B");
                var keep = p.GetComponentsInChildren<Renderer>().ToHashSet();
                var hidden = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.enabled && !keep.Contains(r)).ToList();
                foreach (var r in hidden) r.enabled = false;
                var flags = cam.clearFlags; var bg = cam.backgroundColor; cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black;
                Now("10_char_mask");
                cam.clearFlags = flags; cam.backgroundColor = bg; foreach (var r in hidden) r.enabled = true;
                foreach (var a in Object.FindObjectsByType<Animator>(FindObjectsSortMode.None)) a.speed = 1; Time.timeScale = 1;
                if (Environment.GetEnvironmentVariable("BG_PERF_AB") == "1")
                {
                    var prt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32); var ptex = new Texture2D(1, 1, TextureFormat.RGB24, false);
                    foreach (var (label, at, lk) in new[] { ("spawn", pos, pos + rot * Vector3.forward), ("overview", new Vector3(-22, 9, -26), new Vector3(0, 1, 4)) })
                    {
                        cam.transform.SetPositionAndRotation(at, Quaternion.LookRotation(lk - at)); cam.aspect = W / (float)H;
                        var A = new System.Collections.Generic.List<double>(); var B = new System.Collections.Generic.List<double>();
                        for (int round = 0; round < 10; round++)
                            for (int side = 0; side < 2; side++)
                            {
                                bool useB = side == (round & 1);
                                domeR.sharedMaterial = useB ? rendered : painted; if (backdrop) backdrop.SetActive(useB);
                                for (int i = 0; i < 22; i++)
                                {
                                    var sw = System.Diagnostics.Stopwatch.StartNew();
                                    cam.targetTexture = prt; cam.Render(); RenderTexture.active = prt; ptex.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); ptex.Apply(); RenderTexture.active = null; cam.targetTexture = null;
                                    sw.Stop(); if (i >= 2) (useB ? B : A).Add(sw.Elapsed.TotalMilliseconds);
                                }
                                yield return null;
                            }
                        A.Sort(); B.Sort();
                        log.AppendLine($"perfAB {label} {W}x{H} painted_median_ms={A[A.Count / 2]:F3} rendered_median_ms={B[B.Count / 2]:F3} delta_median_ms={B[B.Count / 2] - A[A.Count / 2]:F3} n={A.Count}/{B.Count}");
                    }
                    domeR.sharedMaterial = rendered; if (backdrop) backdrop.SetActive(true); prt.Release();
                }
            }
            cam.transform.SetPositionAndRotation(pos, rot);
            File.WriteAllText(Path.Combine(Dir, "hub_capture.txt"), log.ToString());
            // the rooms' outdoor grounds (their own small domes)
            foreach (var (room, name) in new[] { (HubLayout.TennisRoom, "07_tennis_court"), (HubLayout.GolfRoom, "08_golf_range") })
            {
                hub.GoTo(room); while (hub.Transitioning) yield return null;
                p.SetStick(0, 1, .4f); yield return new WaitForSeconds(1.4f); p.SetStick(0, 0, 0); yield return new WaitForSeconds(.8f);
                Now(name);
                var domes = Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None).Where(r => r.name == "Rendered sky dome").Select(r => $"{r.transform.position:F0} r{r.transform.localScale.x:F0} vis={r.isVisible} en={r.enabled}");
                File.AppendAllText(Path.Combine(Dir, "hub_capture.txt"), $"room {name}: sun={(RenderSettings.sun ? RenderSettings.sun.name + " " + (-RenderSettings.sun.transform.forward).ToString("F3") : "none")} params={Shader.GetGlobalVector("_RSkyParams")} sunDir={Shader.GetGlobalVector("_RSkySunDir")} cam={cam.transform.position:F1} far={cam.farClipPlane} clear={cam.clearFlags} skybox={(RenderSettings.skybox ? RenderSettings.skybox.name : "none")} domes={string.Join(" | ", domes)}\n");
            }
        }
    }
}
