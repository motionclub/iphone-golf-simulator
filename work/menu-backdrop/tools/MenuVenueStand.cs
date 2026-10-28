using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Bowling;
using GolfArcade.Profile;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// Menu backdrop study v2 (the plaza menu hero, standing straight and facing the camera, placed in each venue).
    /// Menu backdrop study (clone only): the hero standing in each real venue, framed like a menu hero shot (16:9, long lens, hero on the
    /// right third, 3/4 to camera) from four sides. Per shot: _full (as rendered), _bg (hero hidden) and _matte (hero only, alpha).
    /// MV_OUT = output folder; MV_ONLY = comma list of venue keys to limit the run.
    public class MenuVenueStand
    {
        [Serializable] public class LightPreset
        {
            public string venue; public Color sunColor; public float sunIntensity, shadowStrength; public Vector3 sunDirCam;
            public int ambientMode; public Color ambientSky, ambientEquator, ambientGround; public float ambientIntensity;
            public float fov, distance, eye, lookHeight;
        }
        static string Dir => Environment.GetEnvironmentVariable("MV_OUT");
        static readonly (string sport, string venue)[] Venues =
        {
            ("tennis", "resort"), ("tennis", "skyscraper"), ("tennis", "volcano"),
            ("golf", "cliffside"), ("golf", "wildisles"), ("golf", "magma"),
            ("bowling", "club"), ("bowling", "neon"), ("bowling", "tiki"), ("bowling", "magma"),
        };
        static IEnumerable<string> Keys => Venues.Select(v => v.sport + ":" + v.venue);
        GameObject host;
        [TearDown] public void Clean() { Time.timeScale = 1; if (host) Object.DestroyImmediate(host); }

        /// The lowest point of the posed skinned meshes (the soles), from baked vertices: renderer bounds are loose and sink the hero.
        static float Sole(IEnumerable<SkinnedMeshRenderer> skins)
        {
            float low = float.PositiveInfinity; var mesh = new Mesh();
            foreach (var s in skins)
            {
                if (!s || !s.sharedMesh) continue;
                s.BakeMesh(mesh, true);
                var m = Matrix4x4.TRS(s.transform.position, s.transform.rotation, Vector3.one);
                foreach (var v in mesh.vertices) low = Mathf.Min(low, m.MultiplyPoint3x4(v).y);
            }
            Object.Destroy(mesh);
            return low;
        }
        static IEnumerator Wait(float s) { for (float t = 0; t < s; t += Time.unscaledDeltaTime) yield return null; }

        [UnityTest, Timeout(900000)] public IEnumerator Shoot([ValueSource(nameof(Keys))] string key)
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("MV_OUT not set"); yield break; }
            var only = Environment.GetEnvironmentVariable("MV_ONLY");
            if (!string.IsNullOrEmpty(only) && !only.Split(',').Contains(key.Split(':')[1]) && !only.Split(',').Contains(key)) { Assert.Ignore("skipped"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            var sport = key.Split(':')[0]; var venue = key.Split(':')[1];
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            var msg = new NativeSportsSession.Message { version = 1, session = "menu-venue-" + venue, action = "start", sport = sport, leader = true, playerName = "Adnan", female = false, touch = true,
                shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", intros = "none", bigMoments = false, holeFlyover = false, tips = false, mode = sport == "tennis" ? "training" : "" };
            if (sport == "golf") msg.course = venue; else msg.venue = venue;
            bridge.Receive(JsonUtility.ToJson(msg));
            for (int i = 0; i < 2400 && !bridge.Ready; i++) yield return null;
            yield return Wait(4f);
            var log0 = new List<string>();
            HeroGarmentLOD.ForceFullDetail = true;
            if (sport == "golf")
            {
                var g = Object.FindFirstObjectByType<GolfGame>();
                var golfer = (GolferView)typeof(GolfGame).GetField("golfer", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).GetValue(g);
                var move = Environment.GetEnvironmentVariable("MV_GOLF_MOVE") ?? "Wave";
                
            }
            yield return Wait(float.TryParse(Environment.GetEnvironmentVariable("MV_POSE_WAIT"), out var pw) ? pw : 1.2f);

            var log = new List<string> { $"{key}: ready={bridge.Ready} scene={SceneManager.GetActiveScene().name}" }; log.AddRange(log0);
            var cam = Camera.main ?? Object.FindObjectsByType<Camera>(FindObjectsSortMode.None).OrderByDescending(c => c.depth).FirstOrDefault();
            Assert.IsNotNull(cam, "no camera");
            // the hero: the match hero nearest the gameplay camera, else the golfer
            var roots = Object.FindObjectsByType<MatchHeroLook>(FindObjectsSortMode.None).Select(l => l.transform).Where(t => t.gameObject.activeInHierarchy).ToList();
            if (roots.Count == 0) roots = Object.FindObjectsByType<GolferView>(FindObjectsSortMode.None).Select(g => g.transform).Where(t => t.gameObject.activeInHierarchy).ToList();
            Assert.IsTrue(roots.Count > 0, "no hero in " + key);
            var hero = roots.OrderBy(t => (t.position - cam.transform.position).sqrMagnitude).First();
            var renderers = hero.GetComponentsInChildren<Renderer>().Where(r => r.enabled && r.gameObject.activeInHierarchy).ToList();
            var skins = renderers.OfType<SkinnedMeshRenderer>().ToList(); foreach (var s in skins) s.updateWhenOffscreen = true;
            var b = renderers[0].bounds; foreach (var r in renderers) b.Encapsulate(r.bounds);
            float floor = b.min.y; float height = Mathf.Clamp(skins.Where(r => !r.name.Contains("Racket") && !r.name.StartsWith("CLUB")).Select(r => r.bounds.max.y).DefaultIfEmpty(floor + 1.75f).Max() - floor, 1.3f, 1.95f);
            var hips = skins.Select(r => r.rootBone).FirstOrDefault(t => t);
            var centre = hips ? new Vector3(hips.position.x, floor, hips.position.z) : new Vector3(hero.position.x, floor, hero.position.z);
            log.Add($"hero {hero.name} at {centre} h={height:F2} renderers={renderers.Count} cam={cam.name}");

            // the game's own overlays off: every canvas; world-space HUD renderers are listed in the log for a follow-up filter
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            var hide = Environment.GetEnvironmentVariable("MV_HIDE");
            if (!string.IsNullOrEmpty(hide))
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    foreach (var h in hide.Split(',')) if (h.Length > 0 && r.name.IndexOf(h, StringComparison.OrdinalIgnoreCase) >= 0 && !renderers.Contains(r)) r.enabled = false;
            float ground = Sole(skins); if (float.IsInfinity(ground)) ground = floor;
            centre.y = ground;
            log.Add($"ground (gameplay soles) {ground:F3}, bounds floor {floor:F3}");
            // the gameplay props round the spot go too (the held ball, aim guides, contact shadows): anything near the hero that is not scenery
            int hidden = 0;
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || renderers.Contains(r)) continue;
                var c = r.bounds.center; var flat = new Vector2(c.x - centre.x, c.z - centre.z);
                bool near = flat.magnitude < 2.2f && c.y < centre.y + 2.6f && r.bounds.size.magnitude < 4f && !r.isPartOfStaticBatch && !r.gameObject.isStatic;
                bool named = r.name.IndexOf("Contact shadow", StringComparison.OrdinalIgnoreCase) >= 0 || r.name.IndexOf("Aim", StringComparison.Ordinal) >= 0 || r.name.IndexOf("Guide", StringComparison.OrdinalIgnoreCase) >= 0;
                if (near || named) { r.forceRenderingOff = true; hidden++; log.Add("hid prop " + r.name); }
            }
            hero.gameObject.SetActive(false);   // the gameplay hero steps out (its LOD would undo a forceRenderingOff)
            var prefab = TennisCustomization.HeroBase(false);
            Assert.IsNotNull(prefab, "menu hero prefab");
            var root = new GameObject("Menu hero root"); root.transform.position = centre;   // like HubPlayer: the animator pins the feet to local zero
            var go = Object.Instantiate(prefab, root.transform, false); go.name = "Menu hero";
            go.transform.localPosition = Vector3.zero;
            var mlook = go.GetComponent<MatchHeroLook>();
            HeroAccessories.For(mlook).SetCarry(true, "racket_back");
            if (mlook.racketGrip) foreach (var r in mlook.racketGrip.GetComponentsInChildren<Renderer>(true)) r.enabled = false;
            mlook.SetSkin(HeroKit.Hex(HeroKit.SkinHex[2]));
            mlook.SetKit("E8505B", "24345E", "FFFFFF");
            var anim = HubHeroAnimator.Attach(go); anim.GameTime = true;
            anim.SetStance(GolfArcade.Hub.Menu.MenuStage.SlotStance[0]);   // the menu line-up stance (MenuStage.Pose, slot 0)
            HeroGarmentLOD.ForceFullDetail = true;
            yield return Wait(2f);
            hero = root.transform;
            // stand the menu hero's soles on the venue floor
            float sole = Sole(go.GetComponentsInChildren<SkinnedMeshRenderer>().Where(s => s.enabled && s.gameObject.activeInHierarchy && !s.name.Contains("Racket")));
            if (!float.IsInfinity(sole)) root.transform.position += Vector3.up * (ground - sole + .004f);
            log.Add($"menu hero sole {sole:F3} -> lifted {ground - sole + .004f:F3}");
            renderers = go.GetComponentsInChildren<Renderer>().Where(r => r.enabled && r.gameObject.activeInHierarchy).ToList();
            foreach (var s in renderers.OfType<SkinnedMeshRenderer>()) s.updateWhenOffscreen = true;
            height = 1.75f;
            log.Add($"menu hero renderers={renderers.Count}");
            Time.timeScale = .0001f;   // not 0: HubHeroAnimator skips its pose (the relaxed stand) when dt is 0
            yield return null;

            const int W = 1920, H = 1080; const float Fov = 32f, Dist = 4.7f;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = 4 }; rt.Create();
            var tex = new Texture2D(W, H, TextureFormat.RGBA32, false);
            var data = cam.GetUniversalAdditionalCameraData();
            var toCam0 = cam.transform.position - centre; toCam0.y = 0; float baseYaw = Mathf.Atan2(toCam0.x, toCam0.z) * Mathf.Rad2Deg;
            var keepRot = hero.rotation;
            var yaws = new Dictionary<string, int> { { "resort", 35 }, { "skyscraper", 35 }, { "volcano", 35 }, { "cliffside", 180 }, { "wildisles", 180 }, { "magma", sport == "golf" ? 35 : 0 }, { "tiki", 180 } };
            foreach (int yaw in new[] { yaws.TryGetValue(venue, out var yv) ? yv : 0 })
            {
                float a = (baseYaw + yaw) * Mathf.Deg2Rad;
                var dir = new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a));
                var right = Vector3.Cross(Vector3.up, -dir).normalized;   // screen right as seen from the camera
                var camPos = centre + dir * Dist + Vector3.up * .95f;
                var look = centre + Vector3.up * 1.0f;   // centred, the whole body and the floor under the feet in frame
                var faceCam = Quaternion.LookRotation(new Vector3(dir.x, 0, dir.z));
                hero.rotation = faceCam;
                string id = $"{sport}-{venue}_y{(yaw + 360) % 360:000}";

                void Place() { cam.transform.position = camPos; cam.transform.rotation = Quaternion.LookRotation(look - camPos); cam.fieldOfView = Fov; cam.nearClipPlane = .05f; }
                void Grab(string file, bool png)
                {
                    Place(); cam.targetTexture = rt; cam.Render(); cam.targetTexture = null;
                    RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
                    File.WriteAllBytes(Path.Combine(Dir, file), png ? tex.EncodeToPNG() : tex.EncodeToJPG(90));
                }
                for (int w = 0; w < 3; w++) { Place(); hero.rotation = faceCam; yield return null; }
                hero.rotation = faceCam;
                Grab(id + "_full.jpg", false);
                foreach (var r in renderers) r.forceRenderingOff = true;
                Grab(id + "_bg.jpg", false);
                // the plate MenuBackdrop shows: no post here, the menu camera's own grade runs once over plate and hero alike
                { bool keep = data.renderPostProcessing; data.renderPostProcessing = false; Grab(id + "_raw.png", true); data.renderPostProcessing = keep; }
                foreach (var r in renderers) r.forceRenderingOff = false;
                var layers = renderers.Select(r => r.gameObject.layer).ToList();
                foreach (var r in renderers) r.gameObject.layer = 30;
                int mask = cam.cullingMask; var flags = cam.clearFlags; var bgc = cam.backgroundColor; bool post = data.renderPostProcessing;
                cam.cullingMask = 1 << 30; cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(0, 0, 0, 0); data.renderPostProcessing = false;
                Grab(id + "_matte.png", true);
                cam.cullingMask = mask; cam.clearFlags = flags; cam.backgroundColor = bgc; data.renderPostProcessing = post;
                for (int i = 0; i < renderers.Count; i++) renderers[i].gameObject.layer = layers[i];
                log.Add($"{id}: cam {camPos}");
                // the venue's light, camera-relative, for MenuBackdrop to light the live menu hero the same way
                var sun = RenderSettings.sun ? RenderSettings.sun : Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Where(l => l.type == LightType.Directional && l.isActiveAndEnabled).OrderByDescending(l => l.intensity).FirstOrDefault();
                Place();
                var preset = new LightPreset
                {
                    venue = sport + "-" + venue,
                    sunColor = sun ? sun.color : Color.white, sunIntensity = sun ? sun.intensity : 1, shadowStrength = sun ? sun.shadowStrength : .8f,
                    sunDirCam = sun ? cam.transform.InverseTransformDirection(sun.transform.forward) : new Vector3(.3f, -.6f, .7f),
                    ambientMode = (int)RenderSettings.ambientMode, ambientSky = RenderSettings.ambientSkyColor, ambientEquator = RenderSettings.ambientEquatorColor,
                    ambientGround = RenderSettings.ambientGroundColor, ambientIntensity = RenderSettings.ambientIntensity,
                    fov = Fov, distance = Dist, eye = .95f, lookHeight = 1.0f,
                };
                File.WriteAllText(Path.Combine(Dir, id + "_light.json"), JsonUtility.ToJson(preset, true));
            }
            hero.rotation = keepRot;
            // what else draws near the hero (world-space HUD candidates)
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                if (r.enabled && !renderers.Contains(r) && (r.bounds.center - centre).magnitude < 4f) log.Add("near: " + r.name + " (" + r.GetType().Name + ")");
            File.WriteAllLines(Path.Combine(Dir, $"{sport}-{venue}_log.txt"), log);
            rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-venue-" + venue, action = "end" }));
            Time.timeScale = 1; yield return Wait(.5f);
        }
    }
}
