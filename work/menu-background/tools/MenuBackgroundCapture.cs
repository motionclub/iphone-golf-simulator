using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Hub.Menu;
using NUnit.Framework;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.TestTools;
using Debug = UnityEngine.Debug;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// Menu background proof (clone only, work/menu-background): boots the plaza in menu mode through the phone's start message,
    /// then for every MenuShots shot films a still at the TV's 1920x1080 with the pipeline's own MSAA, two 120-frame sequences
    /// (still camera; the menu's breathing drift stepped at an exact 60 fps), a render-cost sample and a scene inventory.
    /// MB_OUT = output folder. MB_SEQ = comma list of shots to film sequences for (default low,arrival). MB_HEROES=0 hides heroes everywhere.
    public class MenuBackgroundCapture
    {
        static string Dir => Environment.GetEnvironmentVariable("MB_OUT");
        GameObject host;
        [TearDown] public void Clean() { Time.captureFramerate = 0; MenuStage.ReduceMotion = false; HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        const int W = 1920, H = 1080;
        static int Msaa
        {
            get { var a = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset; return a ? Mathf.Max(1, a.msaaSampleCount) : 1; }
        }

        static RenderTexture rt; static Texture2D tex;
        static void Render(Camera cam)
        {
            if (!rt) { rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = Msaa }; tex = new Texture2D(W, H, TextureFormat.RGB24, false); }
            var prevA = cam.aspect; cam.aspect = W / (float)H; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = prevA;
        }
        /// Best-of-3 GPU-synced ms per render of `n` back-to-back renders into `target` (other jobs share this GPU: the minimum is the cost).
        static double Ms(Camera cam, RenderTexture target, int n = 40)
        {
            var px = new Texture2D(1, 1, TextureFormat.RGB24, false); double best = double.MaxValue;
            var prevA = cam.aspect; cam.aspect = W / (float)H; cam.targetTexture = target;
            void Sync() { RenderTexture.active = target; px.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); px.Apply(); RenderTexture.active = null; }
            for (int i = 0; i < 5; i++) cam.Render(); Sync();
            for (int rep = 0; rep < 3; rep++)
            {
                var sw = Stopwatch.StartNew(); for (int i = 0; i < n; i++) cam.Render(); Sync();
                best = Math.Min(best, sw.Elapsed.TotalMilliseconds / n);
            }
            cam.targetTexture = null; cam.aspect = prevA; Object.DestroyImmediate(px); return best;
        }
        static void Save(Camera cam, string path)
        {
            Render(cam);
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(path, tex.EncodeToPNG());
        }

        static void Breathe(float k, ref Vector3 pos, ref Vector3 look)
        {
            // MenuStage.Tick's idle drift, verbatim
            pos += new Vector3(Mathf.Sin(k * .37f) * .018f, Mathf.Sin(k * .53f) * .010f, 0);
            look += new Vector3(Mathf.Sin(k * .29f + 1.3f) * .012f, 0, 0);
        }
        static void Place(Camera cam, MenuShots.Shot s, Vector3 pos, Vector3 look)
        {
            cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(look - pos, Vector3.up)); cam.fieldOfView = s.fov; cam.farClipPlane = 600;
        }

        void HideTags(HubWorld hub)
        {
            foreach (var tr in hub.GetComponentsInChildren<Transform>(true))
                if (tr.name.StartsWith("Name tag") || tr.name == "Hub prompt") tr.gameObject.SetActive(false);
        }
        static void Heroes(HubWorld hub, bool on)
        {
            if (hub.Player) foreach (var r in hub.Player.GetComponentsInChildren<Renderer>(true)) r.enabled = on;
        }

        [UnityTest, Timeout(1800000)] public IEnumerator Capture()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("MB_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-bg", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = false, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "racket_back" }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Menu, "menu mode");
            var cam = hub.Camera; var stage = hub.Menu;
            hub.StartArrival();
            for (float t = 0; t < 2.5f; t += Time.unscaledDeltaTime) yield return null;
            HideTags(hub);
            var hud = hub.Hud ? hub.Hud.gameObject : null;
            bool heroesOn = Environment.GetEnvironmentVariable("MB_HEROES") != "0";
            var log = new List<string>();

            // ---- scene inventory: what renders, with what, how big
            var data = cam.GetUniversalAdditionalCameraData();
            var asset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            log.Add($"camera near {cam.nearClipPlane} far {cam.farClipPlane} hdr {cam.allowHDR} aa {data.antialiasing} q {data.antialiasingQuality} post {data.renderPostProcessing} depthTex {data.requiresDepthTexture} opaqueTex {data.requiresColorTexture} msaa(asset) {asset?.msaaSampleCount} scale {asset?.renderScale} shadowDist {asset?.shadowDistance} cascades {asset?.shadowCascadeCount} shadowRes {asset?.mainLightShadowmapResolution} quality {QualitySettings.GetQualityLevel()} {QualitySettings.names[QualitySettings.GetQualityLevel()]} lodBias {QualitySettings.lodBias} aniso {QualitySettings.anisotropicFiltering} tier {GolfArcade.Tennis.TennisQuality.Current}");
            foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None)) log.Add($"light {l.name} {l.type} int {l.intensity} shadows {l.shadows} bias {l.shadowBias} nbias {l.shadowNormalBias} res {l.shadowResolution}");
            foreach (var g in Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None)) log.Add($"lodgroup {Path(g.transform)} fade {g.fadeMode} lods {g.lodCount}");
            var inv = new List<string>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                int tris = 0; var mf = r.GetComponent<MeshFilter>(); if (mf && mf.sharedMesh) for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) tris += (int)mf.sharedMesh.GetIndexCount(s) / 3;
                var mats = string.Join("|", r.sharedMaterials.Where(m => m).Select(m => m.name + "{" + m.shader.name + " q" + m.renderQueue + "}"));
                var b = r.bounds;
                inv.Add($"{Path(r.transform)}\t{r.GetType().Name}\t{tris}\t{b.center.x:F1},{b.center.y:F1},{b.center.z:F1}\t{b.size.x:F1},{b.size.y:F1},{b.size.z:F1}\t{r.shadowCastingMode}\t{r.receiveShadows}\t{r.gameObject.layer}\t{r.isPartOfStaticBatch}\t{mats}");
            }
            File.WriteAllLines(System.IO.Path.Combine(Dir, "inventory.tsv"), inv);
            string[] shotIds = { MenuShots.Low, MenuShots.Close, MenuShots.Mid, MenuShots.Solo, MenuShots.Arrival };
            var seqList = (Environment.GetEnvironmentVariable("MB_SEQ") ?? "low,arrival").Split(',').Where(s => s.Length > 0).ToArray();
            int seqFrames = int.TryParse(Environment.GetEnvironmentVariable("MB_FRAMES"), out var nf) ? nf : 120;
            MenuStage.ReduceMotion = true;   // the test places the camera itself (deterministic drift below)
            Time.captureFramerate = 60;      // shader / wind / water time steps exactly 1/60 s per frame

            foreach (var id in shotIds)
            {
                var s = MenuShots.For(id, 1);
                stage.GoTo(id == MenuShots.Arrival ? MenuShots.Low : id, true);
                if (id == MenuShots.Arrival) stage.PrepareArrival();
                Heroes(hub, heroesOn);
                for (int i = 0; i < 30; i++) yield return null;
                HideTags(hub);
                Place(cam, s, s.position, s.look);
                Save(cam, System.IO.Path.Combine(Dir, $"shot_{id}.png"));

                // render cost: 90 back-to-back renders at the TV size, GPU-synced at the end (max of CPU, GPU per frame)
                using (var batches = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count"))
                using (var setpass = ProfilerRecorder.StartNew(ProfilerCategory.Render, "SetPass Calls Count"))
                using (var trisR = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count"))
                using (var shadowCasters = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Shadow Casters Count"))
                {
                    yield return null;
                    for (int i = 0; i < 10; i++) Render(cam);
                    var px = new Texture2D(1, 1, TextureFormat.RGB24, false);
                    RenderTexture.active = rt; px.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); px.Apply(); RenderTexture.active = null;
                    var sw = Stopwatch.StartNew(); const int n = 90;
                    for (int i = 0; i < n; i++) Render(cam);
                    RenderTexture.active = rt; px.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); px.Apply(); RenderTexture.active = null;
                    double ms = sw.Elapsed.TotalMilliseconds / n; Object.DestroyImmediate(px);
                    yield return null;
                    log.Add($"cost {id}: {ms:F2} ms/render @{W}x{H} msaa{Msaa}; per render (frame totals / {n + 1}): batches {batches.LastValue / (n + 1)} setpass {setpass.LastValue / (n + 1)} tris {trisR.LastValue / (n + 1)} shadowCasters {shadowCasters.LastValue / (n + 1)}");
                }

                if (Array.IndexOf(seqList, id) < 0) continue;
                Heroes(hub, false); BuildingMask(cam, System.IO.Path.Combine(Dir, $"mask_{id}.png")); Heroes(hub, heroesOn);
                foreach (var mode in new[] { "still", "breath" })
                {
                    var folder = System.IO.Path.Combine(Dir, $"seq_{id}_{mode}"); Directory.CreateDirectory(folder);
                    Heroes(hub, false);
                    for (int f = 0; f < seqFrames; f++)
                    {
                        yield return new WaitForEndOfFrame();
                        Vector3 pos = s.position, look = s.look;
                        if (mode == "breath") Breathe(100f + f / 60f, ref pos, ref look);
                        Place(cam, s, pos, look);
                        Save(cam, System.IO.Path.Combine(folder, $"f{f:000}.png"));
                    }
                    Heroes(hub, heroesOn);
                }
            }
            // lighting variants (MB_SUNS="az:el,az:el"): the sun turned, home and close shots filmed for each, then put back
            var suns = Environment.GetEnvironmentVariable("MB_SUNS");
            if (!string.IsNullOrEmpty(suns))
            {
                var sunLight = RenderSettings.sun; var keep = sunLight.transform.rotation;
                foreach (var v in suns.Split(','))
                {
                    var ae = v.Split(':'); float az = float.Parse(ae[0], System.Globalization.CultureInfo.InvariantCulture) * Mathf.Deg2Rad, el = float.Parse(ae[1], System.Globalization.CultureInfo.InvariantCulture) * Mathf.Deg2Rad;
                    var toLight = new Vector3(Mathf.Sin(az) * Mathf.Cos(el), Mathf.Sin(el), Mathf.Cos(az) * Mathf.Cos(el));
                    sunLight.transform.rotation = Quaternion.LookRotation(-toLight, Vector3.up);
                    foreach (var id in new[] { MenuShots.Low, MenuShots.Close })
                    {
                        var sh = MenuShots.For(id, 1); stage.GoTo(id, true); Heroes(hub, heroesOn);
                        for (int i = 0; i < 6; i++) yield return null;
                        Place(cam, sh, sh.position, sh.look);
                        Save(cam, System.IO.Path.Combine(Dir, $"sun_{ae[0]}_{ae[1]}_{id}.png"));
                    }
                }
                sunLight.transform.rotation = keep; for (int i = 0; i < 6; i++) yield return null;
            }
            // GPU cost breakdown on the home shot (heroes in): each feature off in turn, measured against the full frame right before it
            {
                var s = MenuShots.For(MenuShots.Low, 1); stage.GoTo(MenuShots.Low, true); Heroes(hub, true);
                yield return null; Place(cam, s, s.position, s.look);
                var data2 = cam.GetUniversalAdditionalCameraData();
                var rt1 = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
                var urpData = Resources.Load<UniversalRendererData>("Tennis/Rendering/TennisURP_Renderer");
                var ssao = urpData ? urpData.rendererFeatures.FirstOrDefault(f => f is ScreenSpaceAmbientOcclusion) : null;
                Renderer[] Find(string part) => Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.enabled && Path(r.transform).Contains(part)).ToArray();
                void Toggle(Renderer[] rs, bool on) { foreach (var r in rs) r.enabled = on; }
                var sky = Find("Rendered sky dome"); var clouds = Find("Rendered backdrop"); var majestic = Find("Majestic"); var heroes = hub.Player ? hub.Player.GetComponentsInChildren<Renderer>() : new Renderer[0];
                var sea = Find("/Sea"); var grounds = Find("/Grounds/"); var life = Find("Hub life");
                var vol = cam.GetComponentInChildren<Volume>(); DepthOfField dof = null; Bloom bloom = null; vol?.sharedProfile.TryGet(out dof); vol?.sharedProfile.TryGet(out bloom);
                var cases = new (string name, Action off, Action on)[]
                {
                    ("post-processing off", () => data2.renderPostProcessing = false, () => data2.renderPostProcessing = true),
                    ("depth of field off", () => { if (dof) dof.active = false; }, () => { if (dof) dof.active = true; }),
                    ("bloom off", () => { if (bloom) bloom.active = false; }, () => { if (bloom) bloom.active = true; }),
                    ("sun shadows off", () => data2.renderShadows = false, () => data2.renderShadows = true),
                    ("SSAO off", () => ssao?.SetActive(false), () => ssao?.SetActive(true)),
                    ("sky dome off", () => Toggle(sky, false), () => Toggle(sky, true)),
                    ("clouds off", () => Toggle(clouds, false), () => Toggle(clouds, true)),
                    ("sea off", () => Toggle(sea, false), () => Toggle(sea, true)),
                    ("grounds (outside the hedge) off", () => Toggle(grounds, false), () => Toggle(grounds, true)),
                    ("Majestic dressing off", () => Toggle(majestic, false), () => Toggle(majestic, true)),
                    ("hub life off", () => Toggle(life, false), () => Toggle(life, true)),
                    ("heroes off", () => Toggle(heroes, false), () => Toggle(heroes, true)),
                };
                log.Add($"GPU breakdown, home shot {W}x{H} (best of 3 x 40 renders; full = everything on, MSAA {Msaa}):");
                double full0 = Ms(cam, rt);
                log.Add($"  full frame: {full0:F2} ms;  MSAA off: {Ms(cam, rt1):F2} ms");
                foreach (var (name, off, on) in cases)
                {
                    double full = Ms(cam, rt); off(); double cut = Ms(cam, rt); on();
                    log.Add($"  {name}: {cut:F2} ms (full {full:F2}, saves {full - cut:F2})");
                }
                rt1.Release(); Object.DestroyImmediate(rt1);
            }
            // a second, unbatched build of the plaza (static batching makes the live one unreadable), dumped then destroyed:
            // world-space triangles of every static mesh (tools/coplanar.py finds faces that share a plane and overlap = z-fighting)
            var dump = new GameObject("Mesh dump"); HubArt.BuildPlaza(dump.transform); GolfArcade.Majestic.MajesticHub.Build(dump.transform, null);
            using (var w = new BinaryWriter(File.Create(System.IO.Path.Combine(Dir, "meshes.bin"))))
            {
                var mrs = dump.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.enabled && r.gameObject.activeInHierarchy && r.GetComponent<MeshFilter>()?.sharedMesh && r.GetComponent<MeshFilter>().sharedMesh.isReadable).ToList();
                w.Write(mrs.Count);
                foreach (var r in mrs)
                {
                    var mesh = r.GetComponent<MeshFilter>().sharedMesh; var m = r.transform.localToWorldMatrix; var vs = mesh.vertices;
                    var name = System.Text.Encoding.UTF8.GetBytes(Path(r.transform)); w.Write(name.Length); w.Write(name);
                    w.Write(vs.Length); foreach (var v in vs) { var p = m.MultiplyPoint3x4(v); w.Write(p.x); w.Write(p.y); w.Write(p.z); }
                    w.Write(mesh.subMeshCount);
                    for (int s = 0; s < mesh.subMeshCount; s++)
                    {
                        var idx = mesh.GetTriangles(s); var mat = s < r.sharedMaterials.Length && r.sharedMaterials[s] ? r.sharedMaterials[s].name : "?";
                        var mn = System.Text.Encoding.UTF8.GetBytes(mat); w.Write(mn.Length); w.Write(mn);
                        w.Write(idx.Length); foreach (var i in idx) w.Write(i);
                    }
                }
            }
            Object.DestroyImmediate(dump);
            File.WriteAllLines(System.IO.Path.Combine(Dir, "report.txt"), log);
            Debug.Log("MenuBackgroundCapture done: " + Dir);
        }

        /// Which pixels are building: the three houses' own surfaces (stone, slate, trim, glass, signs; not the hedges, roses and
        /// topiaries batched with them) drawn white, everything else black but still in front of them where it stands in front.
        static void BuildingMask(Camera cam, string path)
        {
            var white = new Material(Shader.Find("Universal Render Pipeline/Unlit")); white.SetColor("_BaseColor", Color.white);
            var black = new Material(Shader.Find("Universal Render Pipeline/Unlit")); black.SetColor("_BaseColor", Color.black);
            var kept = new List<(Renderer r, Material[] m)>(); var canvases = new List<Canvas>();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                var p = Path(r.transform);
                bool house = p.Contains("/LOCKER house/") || p.Contains("/CLUBHOUSE house/") || p.Contains("/PLAY hall/");
                var mats = r.sharedMaterials; kept.Add((r, mats));
                var swap = new Material[mats.Length];
                for (int i = 0; i < mats.Length; i++) swap[i] = house && mats[i] && !mats[i].shader.name.Contains("HubSurface") ? white : black;
                r.sharedMaterials = swap;
            }
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (c.enabled && c.renderMode == RenderMode.WorldSpace) { c.enabled = false; canvases.Add(c); }
            var data = cam.GetUniversalAdditionalCameraData(); bool post = data.renderPostProcessing; data.renderPostProcessing = false;
            var clear = cam.clearFlags; var bg = cam.backgroundColor; cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black;
            Save(cam, path);
            cam.clearFlags = clear; cam.backgroundColor = bg; data.renderPostProcessing = post;
            foreach (var (r, m) in kept) if (r) r.sharedMaterials = m;
            foreach (var c in canvases) if (c) c.enabled = true;
            Object.DestroyImmediate(white); Object.DestroyImmediate(black);
        }

        static string Path(Transform t) { var s = t.name; while (t.parent) { t = t.parent; s = t.name + "/" + s; } return s; }
    }
}
