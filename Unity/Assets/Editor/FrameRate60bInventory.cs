using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// FRAME_RATE_60B inventory: every AnimationClip in the project with its key density, so "is it 60 Hz" is a number per clip.
    /// A curve that really moves (range > 1e-4) and is keyed mostly every 33 ms plays at 30 Hz; a clip is "60" when it has none.
    /// Shipped = under a Resources folder, or a dependency of a build scene or of anything under Resources.
    /// -executeMethod GolfArcade.EditorTools.FrameRate60bInventory.Run   (FR60B_OUT = csv path)
    public static class FrameRate60bInventory
    {
        public static void Run()
        {
            string output = System.Environment.GetEnvironmentVariable("FR60B_OUT") ?? "FrameRate60bInventory.csv";
            var roots = new List<string>();
            roots.AddRange(EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path));
            foreach (var guid in AssetDatabase.FindAssets("", new[] { "Assets" }))
            {
                string p = AssetDatabase.GUIDToAssetPath(guid);
                if (p.Contains("/Resources/") && !AssetDatabase.IsValidFolder(p)) roots.Add(p);
            }
            var shipped = new HashSet<string>(AssetDatabase.GetDependencies(roots.ToArray(), true));
            var sb = new StringBuilder();
            sb.AppendLine("path,clip,length_s,clip_frameRate,take_sampleRate,keys_total,gaps,gaps_17ms,gaps_33ms,max_gap_ms,animated_curves,moving_curves_at_30hz,grid,shipped,legacy,loop");
            foreach (var path in AssetDatabase.FindAssets("t:AnimationClip", new[] { "Assets" }).Select(AssetDatabase.GUIDToAssetPath).Distinct().OrderBy(p => p))
            {
                var takes = new Dictionary<string, float>();
                if (AssetImporter.GetAtPath(path) is ModelImporter mi && mi.importedTakeInfos != null)
                    foreach (var t in mi.importedTakeInfos) takes[t.name] = t.sampleRate;
                foreach (var clip in AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>())
                {
                    if (clip.name.StartsWith("__preview__")) continue;
                    int keys = 0, gaps = 0, g17 = 0, g33 = 0, animated = 0, at30 = 0; float maxGap = 0;
                    foreach (var b in AnimationUtility.GetCurveBindings(clip))
                    {
                        var c = AnimationUtility.GetEditorCurve(clip, b);
                        if (c == null) continue;
                        keys += c.length;
                        bool moves = false; int c17 = 0, c33 = 0; float lo = float.MaxValue, hi = float.MinValue;
                        for (int i = 0; i < c.length; i++) { lo = Mathf.Min(lo, c[i].value); hi = Mathf.Max(hi, c[i].value); }
                        for (int i = 1; i < c.length; i++)
                        {
                            if (Mathf.Abs(c[i].value - c[0].value) > 1e-5f) moves = true;
                            float dt = c[i].time - c[i - 1].time; gaps++; maxGap = Mathf.Max(maxGap, dt);
                            float g = dt * 60f; if (Mathf.Abs(g - 1) < .08f) c17++; else if (Mathf.Abs(g - 2) < .08f) c33++;
                        }
                        g17 += c17; g33 += c33;
                        if (moves) animated++;
                        if (hi - lo > 1e-4f && c33 > c17) at30++;
                    }
                    string grid = animated == 0 ? "static" : at30 == 0 ? "60" : g17 > 0 ? "mixed" : "30";
                    takes.TryGetValue(clip.name, out float take);
                    sb.AppendLine(string.Join(",", path, clip.name.Contains(",") ? "\"" + clip.name + "\"" : clip.name, clip.length.ToString("0.000"), clip.frameRate.ToString("0"), take.ToString("0"),
                        keys, gaps, g17, g33, (maxGap * 1000).ToString("0"), animated, at30, grid, shipped.Contains(path) ? "1" : "0", clip.legacy ? "1" : "0", clip.isLooping ? "1" : "0"));
                }
            }
            File.WriteAllText(output, sb.ToString());
            Debug.Log("FR60B inventory -> " + output);
        }
    }
}
