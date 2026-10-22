using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// GARMENT PIPELINE: several pipeline steps in ONE Editor session (each Editor start costs 3-5 GB and minutes on the shared Mac).
    /// Env: GP_STEPS (comma list, in order) of
    ///   cv2      ClothingV2Install for brand-new meshes (CV2_SRC, CV2_HEROES), called without its own Exit
    ///   install  GarmentPipelineInstall (GP_INSTALL_OUT = the pipeline out/ dir, GP_INSTALL_HEROES)
    ///   perf     GarmentPipelinePerf    (GP_PERF_OUT, GP_PERF_HEROES)
    ///   film     GarmentPipelineFilm    (GP_FILM_OUT, GP_FILM_HEROES, GP_CLIPS, GP_STEP, GP_FOCUS, GP_LOOK)
    /// Batch mode with graphics, muted. Exits non-zero at the first failing step.
    public static class GarmentPipelineBatch
    {
        static string Env(string k) => Environment.GetEnvironmentVariable(k);

        public static void Run()
        {
            int code = 0; EditorUtility.audioMasterMute = true;
            Environment.SetEnvironmentVariable("GP_NOEXIT", "1");
            try
            {
                foreach (var step in (Env("GP_STEPS") ?? "install,perf").Split(',').Select(s => s.Trim()).Where(s => s.Length > 0))
                {
                    var t0 = DateTime.Now; Debug.Log("[GP-BATCH] step " + step);
                    string sub = null; string st = step;
                    if (step.StartsWith("film@")) { sub = step.Substring(5); st = "film"; }      // film@<label>: a film into GP_FILM_OUT/<label> (before/after in one session)
                    switch (st)
                    {
                        case "cv2": code = ClothingV2(); break;
                        case "install": code = Step("INSTALL", () => { GarmentPipelineInstall.Run(); return GarmentPipelineInstall.LastCode; }); break;
                        case "perf": code = Step("PERF", () => { GarmentPipelinePerf.Run(); return GarmentPipelinePerf.LastCode; }); break;
                        case "film": code = Step("FILM", () => {
                            if (sub != null) Environment.SetEnvironmentVariable("GP_OUT", Path.Combine(Env("GP_FILM_OUT"), sub));
                            Environment.SetEnvironmentVariable("GP_SWATCHES", sub != null && sub.StartsWith("swatch") ? Env("GP_SWATCH_LIST") : null);   // film@swatch: COLOURS gate
                            GarmentPipelineFilm.Run(); return GarmentPipelineFilm.LastCode; }); break;
                        default: throw new ArgumentException("unknown GP_STEPS step " + step);
                    }
                    Debug.Log($"[GP-BATCH] step {step} -> {code} in {(DateTime.Now - t0).TotalSeconds:0} s");
                    if (code != 0) break;
                }
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            EditorApplication.Exit(code);
        }

        /// the step's own env (GP_OUT / GP_HEROES) comes from GP_<STEP>_OUT / GP_<STEP>_HEROES
        static int Step(string key, Func<int> run)
        {
            Environment.SetEnvironmentVariable("GP_OUT", Env("GP_" + key + "_OUT"));
            Environment.SetEnvironmentVariable("GP_HEROES", Env("GP_" + key + "_HEROES"));
            return run();
        }

        /// ClothingV2Install.Run without its Exit: its maps + per-hero mesh/prefab install, by reflection (the tool is shared, not edited here)
        static int ClothingV2()
        {
            var t = typeof(ClothingV2Install);
            const BindingFlags S = BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public;
            var log = new StringBuilder();
            string only = Env("CV2_HEROES");
            t.GetMethod("InstallMaps", S).Invoke(null, new object[] { only, log });
            var heroes = (Array)t.GetField("Heroes", S).GetValue(null);
            var install = t.GetMethod("Install", S);
            foreach (var h in heroes)
            {
                var ft = h.GetType();
                string hero = (string)ft.GetField("Item1").GetValue(h), prefab = (string)ft.GetField("Item2").GetValue(h), mat = (string)ft.GetField("Item3").GetValue(h);
                if (string.IsNullOrEmpty(only) || only.Split(',').Contains(hero)) log.Append((string)install.Invoke(null, new object[] { hero, prefab, mat }));
            }
            AssetDatabase.SaveAssets();
            string src = Env("CV2_SRC");
            if (!string.IsNullOrEmpty(src)) File.WriteAllText(Path.Combine(src, "install_report.txt"), log.ToString());
            Debug.Log("[ClothingV2] " + log);
            return 0;
        }
    }
}
