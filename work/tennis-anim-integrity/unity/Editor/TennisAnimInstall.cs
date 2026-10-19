#if UNITY_EDITOR
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Chat 4: ReadyIdle at 60 Hz without touching the base-model FBX (the hero meshes live in it). The approved ReadyIdle, resampled to
    /// 60 Hz in work/tennis-anim-integrity/match60, is staged under Assets/TAI_Extra/<Sex>/resampled60 (prepare_extras.sh); its clip is
    /// copied to Resources/Tennis/Performance/<Sex>_ReadyIdle60.anim, which HeroTennisDriver.ResolvePerformanceClips plays in the Ready slot.
    public static class TennisAnimInstall
    {
        /// The approved ForehandArmCorrected / BackhandArmCorrected clips key the arms at 60 Hz but keep the torso / legs they copied from
        /// the 30 Hz source at 1/30 s. Each curve with a 1/30 s gap gets the uniform Catmull-Rom midpoint of its four neighbours (the same rule
        /// as match60/resample60.py): the approved keys stay exactly where they are, the in-betweens follow the curve. Rotation curves are
        /// done per bone (x, y, z, w together, hemisphere-aligned, normalised).
        public static void Resample60ArmCorrected()
        {
            int code = 0;
            try
            {
                foreach (var sex in new[] { "Male", "Female" }) foreach (var stroke in new[] { "Forehand", "Backhand" })
                {
                    string path = $"Assets/Resources/Tennis/Performance/{sex}_{stroke}ArmCorrected.anim";
                    var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
                    var bindings = AnimationUtility.GetCurveBindings(clip);
                    var groups = bindings.GroupBy(b => (b.path, b.type, prop: b.propertyName.Contains(".") ? b.propertyName.Substring(0, b.propertyName.LastIndexOf('.')) : b.propertyName));
                    int changed = 0;
                    foreach (var g in groups)
                    {
                        var bs = g.OrderBy(b => b.propertyName).ToArray();
                        var curves = bs.Select(b => AnimationUtility.GetEditorCurve(clip, b)).ToArray();
                        var times = curves.SelectMany(c => c.keys.Select(k => Mathf.Round(k.time * 60f) / 60f)).Distinct().OrderBy(t => t).ToList();
                        if (times.Count < 2) continue;
                        bool coarse = false; for (int i = 1; i < times.Count; i++) if (times[i] - times[i - 1] > 1.5f / 60f) coarse = true;
                        if (!coarse) continue;
                        bool quat = bs.Length == 4 && bs.All(b => b.propertyName.StartsWith("m_LocalRotation"));
                        float end = times[times.Count - 1];
                        int n = Mathf.RoundToInt(end * 60f) + 1;
                        var vals = new float[n, bs.Length];
                        for (int f = 0; f < n; f++)
                        {
                            float t = f / 60f; int at = times.FindIndex(x => Mathf.Abs(x - t) < 1e-4f);
                            if (at >= 0) { for (int c = 0; c < bs.Length; c++) vals[f, c] = curves[c].Evaluate(t); continue; }
                            // between two keys 1/30 s apart: Catmull-Rom midpoint of the four surrounding keys
                            int hi = times.FindIndex(x => x > t); int lo = hi - 1;
                            float t0 = times[Mathf.Max(lo - 1, 0)], t1 = times[lo], t2 = times[hi], t3 = times[Mathf.Min(hi + 1, times.Count - 1)];
                            var p = new float[4, bs.Length];
                            for (int c = 0; c < bs.Length; c++) { p[0, c] = curves[c].Evaluate(t0); p[1, c] = curves[c].Evaluate(t1); p[2, c] = curves[c].Evaluate(t2); p[3, c] = curves[c].Evaluate(t3); }
                            if (quat) for (int k = 0; k < 4; k++) if (k != 1) { float dot = 0; for (int c = 0; c < 4; c++) dot += p[k, c] * p[1, c]; if (dot < 0) for (int c = 0; c < 4; c++) p[k, c] = -p[k, c]; }
                            float u = (t - t1) / Mathf.Max(1e-5f, t2 - t1);
                            for (int c = 0; c < bs.Length; c++)
                            {
                                float a0 = p[0, c], a1 = p[1, c], a2 = p[2, c], a3 = p[3, c];
                                vals[f, c] = .5f * ((2 * a1) + (-a0 + a2) * u + (2 * a0 - 5 * a1 + 4 * a2 - a3) * u * u + (-a0 + 3 * a1 - 3 * a2 + a3) * u * u * u);
                            }
                            if (quat) { float m = 0; for (int c = 0; c < 4; c++) m += vals[f, c] * vals[f, c]; m = Mathf.Sqrt(m); for (int c = 0; c < 4; c++) vals[f, c] /= m; }
                        }
                        for (int c = 0; c < bs.Length; c++)
                        {
                            var keys = new Keyframe[n]; for (int f = 0; f < n; f++) keys[f] = new Keyframe(f / 60f, vals[f, c]);
                            var curve = new AnimationCurve(keys);
                            for (int f = 0; f < n; f++) { AnimationUtility.SetKeyLeftTangentMode(curve, f, AnimationUtility.TangentMode.Linear); AnimationUtility.SetKeyRightTangentMode(curve, f, AnimationUtility.TangentMode.Linear); }
                            AnimationUtility.SetEditorCurve(clip, bs[c], curve);
                        }
                        changed++;
                    }
                    if (changed > 0) clip.EnsureQuaternionContinuity();
                    EditorUtility.SetDirty(clip);
                    Debug.Log($"[TAI install] {path}: {changed} curve groups re-keyed at 60 Hz");
                }
                AssetDatabase.SaveAssets();
            }
            catch (System.Exception e) { Debug.LogError("[TAI install] FAILED " + e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }

        public static void ExtractReadyIdle()
        {
            int code = 0;
            try
            {
                foreach (var sex in new[] { "Male", "Female" })
                {
                    string src = $"Assets/TAI_Extra/{sex}/resampled60/{sex}_ReadyIdle.fbx";
                    var clip = AssetDatabase.LoadAllAssetsAtPath(src).OfType<AnimationClip>().First(c => !c.name.StartsWith("__"));
                    var copy = Object.Instantiate(clip); copy.name = sex + "_ReadyIdle60";
                    var settings = AnimationUtility.GetAnimationClipSettings(copy); settings.loopTime = true; AnimationUtility.SetAnimationClipSettings(copy, settings);
                    string dst = $"Assets/Resources/Tennis/Performance/{sex}_ReadyIdle60.anim";
                    var current = AssetDatabase.LoadAssetAtPath<AnimationClip>(dst);
                    if (current) { EditorUtility.CopySerialized(copy, current); EditorUtility.SetDirty(current); } else AssetDatabase.CreateAsset(copy, dst);
                    Debug.Log($"[TAI install] {dst} len={copy.length:0.000} fps={copy.frameRate}");
                }
                AssetDatabase.SaveAssets();
            }
            catch (System.Exception e) { Debug.LogError("[TAI install] FAILED " + e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }
    }
}
#endif
