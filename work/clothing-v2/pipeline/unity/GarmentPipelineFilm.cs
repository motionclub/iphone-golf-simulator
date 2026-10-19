using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// GARMENT PIPELINE live check: films clips on the hero exactly as the game builds it (prefab / golfer, MatchHeroLook materials, garment
    /// correctives, skin cover, every runtime pose fix per frame like LateUpdate) with the game's character / cloth shaders at 1920x1080,
    /// from a three-quarter camera that orbits slowly so front, side and back are seen. Batch mode WITH graphics, muted.
    /// Env: GP_OUT (abs dir), GP_HEROES, GP_CLIPS (comma list of clip names per hero, matched by suffix), GP_STEP (s, default 0.1).
    public static class GarmentPipelineFilm
    {
        public static int LastCode;   // for GarmentPipelineBatch (GP_NOEXIT=1: several tools in one Editor session)

        public static void Run()
        {
            int code = 0; EditorUtility.audioMasterMute = true;
            try
            {
                string outRoot = Environment.GetEnvironmentVariable("GP_OUT");
                float step = float.TryParse(Environment.GetEnvironmentVariable("GP_STEP"), out var s) ? s : .1f;
                var want = (Environment.GetEnvironmentVariable("GP_CLIPS") ?? "").Split(',').Where(c => c.Length > 0).ToArray();
                foreach (var id in (Environment.GetEnvironmentVariable("GP_HEROES") ?? "MatchHero_Male").Split(','))
                    Film(id, Path.Combine(outRoot, id), want, step);
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            LastCode = code;
            if (Application.isBatchMode && Environment.GetEnvironmentVariable("GP_NOEXIT") != "1") EditorApplication.Exit(code);
        }

        static void Film(string id, string dir, string[] want, float step)
        {
            Directory.CreateDirectory(dir);
            bool golf = id.StartsWith("GolfKit"), female = id.EndsWith("Female");
            GameObject root = golf ? HeroGolfer.Build(null, new HeroLook { Female = female, Haircut = (int)HeroGolfer.Haircut.Bald, Skin = female ? new Color(.953f, .855f, .788f) : new Color(.949f, .816f, .686f), HairColor = new Color(.35f, .25f, .18f) }).Root
                : (GameObject)Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Tennis/Customization/Player" + (female ? "Female" : "Male") + ".prefab"));
            try
            {
                root.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
                var driver = root.GetComponent<HeroTennisDriver>(); if (driver) driver.ResolvePerformanceClips();
                var look = root.GetComponent<MatchHeroLook>();
                typeof(MatchHeroLook).GetMethod("OwnMaterials", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(look, null);
                if (!look.GetComponent<HeroGripPolish>()) look.gameObject.AddComponent<HeroGripPolish>().look = look;
                KitV2PoseCorrectives.Attach(look);
                var clips = (golf ? Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(female)).ToList() : driver.slots.Where(x => x.clip).Select(x => x.clip).Distinct().ToList());
                clips.AddRange(Resources.LoadAll<AnimationClip>("HeroMoves/" + (female ? "Female" : "Male")));
                var pick = want.Length > 0 ? want.Select(w => clips.FirstOrDefault(c => c.name.EndsWith(w))).Where(c => c).ToList() : clips.Take(5).ToList();
                var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
                var camGo = new GameObject("FilmCam"); var cam = camGo.AddComponent<Camera>(); cam.targetTexture = rt; cam.fieldOfView = 28;
                cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.80f, .83f, .86f);
                var lightGo = new GameObject("FilmKey"); var key = lightGo.AddComponent<Light>(); key.type = LightType.Directional; key.intensity = 1.25f; key.shadows = LightShadows.Soft;
                lightGo.transform.rotation = Quaternion.Euler(42, -35, 0);
                RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = new Color(.62f, .66f, .72f); RenderSettings.ambientEquatorColor = new Color(.48f, .48f, .50f); RenderSettings.ambientGroundColor = new Color(.30f, .28f, .26f);
                // GP_LOOK=target: the reference hues the hero turnaround uses for proofs (navy trims), applied after the materials exist
                if (Environment.GetEnvironmentVariable("GP_LOOK") == "target")
                    typeof(HeroTurnaround).GetMethod("ApplyTargetLook", BindingFlags.Static | BindingFlags.NonPublic)?.Invoke(null, new object[] { id, look });
                // GP_SHOE_TRIM=<hex>: the shoe trim colour for proofs (the reference look leaves golf shoes on the default trim)
                var shoeTrim = Environment.GetEnvironmentVariable("GP_SHOE_TRIM");
                if (!string.IsNullOrEmpty(shoeTrim) && ColorUtility.TryParseHtmlString("#" + shoeTrim, out var st))
                    foreach (var r in root.GetComponentsInChildren<Renderer>(true))
                        if (r.name.StartsWith("Kit_Shoe"))
                            foreach (var m in r.materials) if (m && m.HasProperty("_TrimColor")) m.SetColor("_TrimColor", st);
                var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
                var hips = look.Bone(HumanBodyBones.Hips);
                // GP_SWATCHES="hex,hex,...": COLOURS gate - every swatch on shirt + lower through the game's own SetKit, mid-frame of the first
                // clip, front + back (GP_VIEWS), so construction / shading read in light, dark and saturated colours
                var swatches = (Environment.GetEnvironmentVariable("GP_SWATCHES") ?? "").Split(',').Where(x => x.Length > 0).ToArray();
                if (swatches.Length > 0 && pick.Count > 0)
                {
                    var views0 = (Environment.GetEnvironmentVariable("GP_VIEWS") ?? "0,180").Split(',').Where(v => v.Length > 0).Select(float.Parse).ToArray();
                    foreach (var sw in swatches)
                    {
                        look.SetKit(sw, sw, "FFFFFF");
                        pick[0].SampleAnimation(root, 0f);                    // ready stance (frame 0), with every runtime pose fix like the film loop
                        if (look.golfKit) HeroGripPolish.ApplyGolfGrip(look); else HeroGripPolish.ApplyGrip(look);
                        look.body.GetComponent<HeroArmSkinning>()?.Apply();
                        root.GetComponent<HeroShoulderDeformation>()?.Apply();
                        root.GetComponent<KitV2PoseCorrectives>()?.Apply();
                        root.GetComponent<GarmentPoseCorrectives>()?.Apply();
                        var right0 = look.Bone(HumanBodyBones.RightUpperLeg).position - look.Bone(HumanBodyBones.LeftUpperLeg).position;
                        var fwd0 = Vector3.Cross(right0, Vector3.up); float face0 = Mathf.Atan2(fwd0.x, fwd0.z) * Mathf.Rad2Deg;
                        var c0 = hips.position + Vector3.up * .25f;
                        foreach (var v in views0)
                        {
                            cam.transform.position = c0 + Quaternion.Euler(6, face0 + v, 0) * new Vector3(0, 0, 2.2f); cam.transform.LookAt(c0); cam.Render();
                            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); tex.Apply(); RenderTexture.active = null;
                            File.WriteAllBytes(Path.Combine(dir, $"swatch_{sw}_v{v:000}.jpg"), tex.EncodeToJPG(90));
                        }
                    }
                    Debug.Log($"[GP-FILM] {id} swatches: {swatches.Length}");
                    pick = new List<AnimationClip>();      // swatch mode only
                }
                foreach (var clip in pick)
                {
                    int n = Mathf.Max(2, Mathf.CeilToInt(clip.length / step) + 1);
                    for (int f = 0; f < n; f++)
                    {
                        float t = clip.length * f / (n - 1);
                        clip.SampleAnimation(root, t);
                        if (look.golfKit) HeroGripPolish.ApplyGolfGrip(look); else HeroGripPolish.ApplyGrip(look);
                        look.body.GetComponent<HeroArmSkinning>()?.Apply();
                        root.GetComponent<HeroShoulderDeformation>()?.Apply();
                        root.GetComponent<KitV2PoseCorrectives>()?.Apply();
                        root.GetComponent<GarmentPoseCorrectives>()?.Apply();
                        string focus = Environment.GetEnvironmentVariable("GP_FOCUS") ?? "";
                        bool feet = focus == "feet", torso = focus == "torso";
                        var lf = look.Bone(HumanBodyBones.LeftFoot); var rf = look.Bone(HumanBodyBones.RightFoot); var chest = look.Bone(HumanBodyBones.Chest);
                        var c = feet ? (lf.position + rf.position) * .5f + Vector3.up * .06f : torso && chest ? chest.position + Vector3.down * .08f : hips.position + Vector3.up * .05f;
                        float dist = feet ? 1.9f : torso ? 1.55f : 3.4f;
                        // GP_VIEWS="0,90,180,45": fixed azimuths relative to the hero's facing, one image each (rip gate: front/side/back/3-4);
                        // default: one slowly orbiting view per frame
                        var views = (Environment.GetEnvironmentVariable("GP_VIEWS") ?? "").Split(',').Where(v => v.Length > 0).Select(float.Parse).ToArray();
                        var right = look.Bone(HumanBodyBones.RightUpperLeg).position - look.Bone(HumanBodyBones.LeftUpperLeg).position;
                        var fwd = Vector3.Cross(right, Vector3.up); float facing = Mathf.Atan2(fwd.x, fwd.z) * Mathf.Rad2Deg;   // hero's facing from the hips
                        var azs = views.Length > 0 ? views.Select(v => facing + v).ToArray() : new[] { 35f + 360f * f / n };
                        for (int vi = 0; vi < azs.Length; vi++)
                        {
                            cam.transform.position = c + Quaternion.Euler(feet ? 14 : 8, azs[vi], 0) * new Vector3(0, 0, dist);
                            cam.transform.LookAt(c);
                            cam.Render();
                            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); tex.Apply(); RenderTexture.active = null;
                            string tag = views.Length > 0 ? $"_v{views[vi]:000}" : "";
                            File.WriteAllBytes(Path.Combine(dir, $"{clip.name}_{f:000}{tag}.jpg"), tex.EncodeToJPG(90));
                        }
                    }
                    Debug.Log($"[GP-FILM] {id} {clip.name}: {n} frames");
                }
                Object.DestroyImmediate(camGo); Object.DestroyImmediate(lightGo); rt.Release();
            }
            finally { Object.DestroyImmediate(root); }
        }
    }
}
