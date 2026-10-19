using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// GARMENT PIPELINE PERF gate: per hero, the CPU cost of GarmentPoseCorrectives.Apply (features + RBF + SetBlendShapeWeight) over clip
    /// frames, and the 1920x1080 render time of the hero with the pose correctives live vs all weights zero (same frames, same camera).
    /// Batch mode WITH graphics (Metal), muted. Env: GP_OUT (abs dir for perf.json), GP_HEROES.
    public static class GarmentPipelinePerf
    {
        static readonly string[] AllHeroes = { "MatchHero_Male", "MatchHero_Female", "GolfKitHero_Male", "GolfKitHero_Female" };

        public static int LastCode;   // for GarmentPipelineBatch (GP_NOEXIT=1: several tools in one Editor session)

        public static void Run()
        {
            int code = 0; EditorUtility.audioMasterMute = true;
            var lines = new List<string>();
            try
            {
                string filter = Environment.GetEnvironmentVariable("GP_HEROES");
                foreach (var id in string.IsNullOrEmpty(filter) ? AllHeroes : filter.Split(',')) lines.Add(Measure(id));
                File.WriteAllText(Path.Combine(Environment.GetEnvironmentVariable("GP_OUT"), "perf.json"), "[\n" + string.Join(",\n", lines) + "\n]");
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            LastCode = code;
            if (Application.isBatchMode && Environment.GetEnvironmentVariable("GP_NOEXIT") != "1") EditorApplication.Exit(code);
        }

        static GameObject Build(string id, out List<AnimationClip> clips)
        {
            bool golf = id.StartsWith("GolfKit"), female = id.EndsWith("Female");
            GameObject root;
            if (golf) root = HeroGolfer.Build(null, new HeroLook { Female = female, Haircut = (int)HeroGolfer.Haircut.Bald, Skin = new Color(.95f, .82f, .69f), HairColor = new Color(.35f, .25f, .18f) }).Root;
            else root = (GameObject)Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Tennis/Customization/Player" + (female ? "Female" : "Male") + ".prefab"));
            root.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            var driver = root.GetComponent<HeroTennisDriver>(); if (driver) driver.ResolvePerformanceClips();
            var look = root.GetComponent<MatchHeroLook>();
            typeof(MatchHeroLook).GetMethod("OwnMaterials", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(look, null);
            KitV2PoseCorrectives.Attach(look);
            clips = golf ? Resources.LoadAll<AnimationClip>(HeroGolfer.PathFor(female)).Where(c => !c.name.StartsWith("__")).ToList() : driver.slots.Where(s => s.clip).Select(s => s.clip).Distinct().ToList();
            return root;
        }

        static string Measure(string id)
        {
            var root = Build(id, out var clips);
            try
            {
                var gp = root.GetComponent<GarmentPoseCorrectives>();
                var shapes = root.GetComponentsInChildren<SkinnedMeshRenderer>().Where(r => r.name.StartsWith("Kit_") && r.sharedMesh && r.sharedMesh.blendShapeCount > 0).ToArray();
                int nshape = shapes.Sum(r => Enumerable.Range(0, r.sharedMesh.blendShapeCount).Count(i => r.sharedMesh.GetBlendShapeName(i).StartsWith("GP_Pose")));
                var frames = new List<(AnimationClip c, float t)>();
                foreach (var c in clips.Take(12)) for (int i = 0; i < 25; i++) frames.Add((c, c.length * i / 24f));
                // CPU: the driver
                var sw = new Stopwatch(); double cpu = 0; int n = 0;
                if (gp)
                {
                    foreach (var (c, t) in frames) { c.SampleAnimation(root, t); sw.Restart(); gp.Apply(); sw.Stop(); cpu += sw.Elapsed.TotalMilliseconds; n++; }
                    cpu /= Math.Max(1, n);
                }
                // GPU: 1920x1080 render with the shapes live vs zero
                var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
                var cam = new GameObject("PerfCam").AddComponent<Camera>(); cam.targetTexture = rt; cam.fieldOfView = 30;
                cam.transform.position = new Vector3(0, 1.0f, 3.2f); cam.transform.LookAt(new Vector3(0, .9f, 0));
                var tex = new Texture2D(8, 8, TextureFormat.RGBA32, false);
                double Render(bool live)
                {
                    double tot = 0; int m = 0;
                    for (int k = 0; k < 2; k++)
                        foreach (var (c, t) in frames)
                        {
                            c.SampleAnimation(root, t);
                            if (live && gp) gp.Apply(); else foreach (var r in shapes) for (int i = 0; i < r.sharedMesh.blendShapeCount; i++) if (r.sharedMesh.GetBlendShapeName(i).StartsWith("GP_Pose")) r.SetBlendShapeWeight(i, 0);
                            sw.Restart(); cam.Render(); RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, 8, 8), 0, 0); tex.Apply(); RenderTexture.active = null; sw.Stop();
                            if (k == 1) { tot += sw.Elapsed.TotalMilliseconds; m++; }
                        }
                    return tot / Math.Max(1, m);
                }
                double off = Render(false), on = Render(true), off2 = Render(false);
                Object.DestroyImmediate(cam.gameObject); rt.Release();
                string s = $"{{\"hero\":\"{id}\",\"gp_shapes\":{nshape},\"driver_ms\":{cpu:F4},\"render1080_ms_off\":{(off + off2) / 2:F3},\"render1080_ms_on\":{on:F3},\"frames\":{frames.Count}}}";
                Debug.Log("[GP-PERF] " + s);
                return s;
            }
            finally { Object.DestroyImmediate(root); }
        }
    }
}
