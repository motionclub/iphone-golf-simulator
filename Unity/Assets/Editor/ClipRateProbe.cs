using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Reports how densely and how smoothly an imported match clip is keyed (key spacing, tangent modes),
    /// so "does it move at 30 or 60 Hz" is a number: run with -executeMethod GolfArcade.EditorTools.ClipRateProbe.Run.
    public static class ClipRateProbe
    {
        /// Ground truth test: dense clips are thinned to every second key (30 -> 15 Hz, a harsher test than 60 vs 30), then the removed poses are rebuilt by straight lines
        /// and by ClampedAuto and compared with the real keys.
        public static void Truth()
        {
            foreach (var path in new[] { "Assets/Characters/MatchHeroes/Male/Male_Forehand.fbx", "Assets/Characters/MatchHeroes/Male/Male_Serve.fbx", "Assets/Characters/MatchHeroes/Male/Male_Emote_Spike.fbx", "Assets/Characters/MatchHeroes/Male/Male_RunForward.fbx", "Assets/Characters/MatchHeroes/Male/Male_Emote_Stomp.fbx" })
            {
                var clip = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().FirstOrDefault(c => !c.name.StartsWith("__"));
                if (!clip) continue;
                var q = new Dictionary<string, AnimationCurve[]>();
                foreach (var b in AnimationUtility.GetCurveBindings(clip))
                {
                    if (!b.propertyName.StartsWith("m_LocalRotation.")) continue;
                    if (!q.TryGetValue(b.path, out var arr)) q[b.path] = arr = new AnimationCurve[4];
                    arr["xyzw".IndexOf(b.propertyName[b.propertyName.Length - 1])] = AnimationUtility.GetEditorCurve(clip, b);
                }
                var lin = new List<float>(); var smooth = new List<float>(); int used = 0;
                foreach (var kv in q)
                {
                    var c = kv.Value; if (c.Any(x => x == null) || c[0].length < 9) continue;
                    bool dense = true; for (int i = 1; i < c[0].length; i++) if (c[0][i].time - c[0][i - 1].time > .04f) { dense = false; break; }
                    if (!dense) continue; used++;
                    var thinL = new AnimationCurve[4]; var thinS = new AnimationCurve[4];
                    for (int a = 0; a < 4; a++)
                    {
                        var kl = new List<Keyframe>(); for (int i = 0; i < c[a].length; i += 2) kl.Add(new Keyframe(c[a][i].time, c[a][i].value));
                        thinL[a] = new AnimationCurve(kl.ToArray()); thinS[a] = new AnimationCurve(kl.ToArray());
                        for (int i = 0; i < thinL[a].length; i++)
                        {
                            float sl = i + 1 < thinL[a].length ? (thinL[a][i + 1].value - thinL[a][i].value) / (thinL[a][i + 1].time - thinL[a][i].time) : 0;
                            float sp = i > 0 ? (thinL[a][i].value - thinL[a][i - 1].value) / (thinL[a][i].time - thinL[a][i - 1].time) : sl;
                            var k = thinL[a][i]; k.inTangent = sp; k.outTangent = sl; thinL[a].MoveKey(i, k);
                            AnimationUtility.SetKeyLeftTangentMode(thinS[a], i, AnimationUtility.TangentMode.ClampedAuto);
                            AnimationUtility.SetKeyRightTangentMode(thinS[a], i, AnimationUtility.TangentMode.ClampedAuto);
                        }
                    }
                    for (int i = 1; i < c[0].length; i += 2)
                    {
                        float t = c[0][i].time; var truth = new Quaternion(c[0][i].value, c[1][i].value, c[2][i].value, c[3][i].value);
                        lin.Add(Quaternion.Angle(truth, new Quaternion(thinL[0].Evaluate(t), thinL[1].Evaluate(t), thinL[2].Evaluate(t), thinL[3].Evaluate(t)).normalized));
                        smooth.Add(Quaternion.Angle(truth, new Quaternion(thinS[0].Evaluate(t), thinS[1].Evaluate(t), thinS[2].Evaluate(t), thinS[3].Evaluate(t)).normalized));
                    }
                }
                if (lin.Count == 0) { Debug.Log($"TRUTH {clip.name}: no 60 Hz bones"); continue; }
                lin.Sort(); smooth.Sort();
                Debug.Log($"TRUTH {clip.name} bones={used} removedPoses={lin.Count} | straight-line err p50={lin[lin.Count / 2]:0.000} p99={lin[(int)(lin.Count * .99f)]:0.00} max={lin[lin.Count - 1]:0.00}deg | smooth err p50={smooth[smooth.Count / 2]:0.000} p99={smooth[(int)(smooth.Count * .99f)]:0.00} max={smooth[smooth.Count - 1]:0.00}deg");
            }
        }

        /// Every installed hero clip FBX: dominant key spacing (33 ms = 30 Hz, 17 ms = 60 Hz) and the share of keys on each grid.
        public static void Survey()
        {
            foreach (var root in new[] { "Assets/Characters/MatchHeroes/Male", "Assets/Characters/MatchHeroes/Female", "Assets/Resources/HeroMoves", "Assets/Characters/GolfHeroKit" })
            {
                if (!System.IO.Directory.Exists(root)) continue;
                foreach (var path in System.IO.Directory.GetFiles(root, "*.fbx", System.IO.SearchOption.AllDirectories).OrderBy(x => x))
                {
                    var clip = AssetDatabase.LoadAllAssetsAtPath(path.Replace('\\', '/')).OfType<AnimationClip>().FirstOrDefault(c => !c.name.StartsWith("__"));
                    if (!clip || clip.length <= 0) continue;
                    int k30 = 0, k60 = 0, other = 0;
                    foreach (var b in AnimationUtility.GetCurveBindings(clip))
                    {
                        var c = AnimationUtility.GetEditorCurve(clip, b);
                        for (int i = 1; i < c.length; i++) { int ms = Mathf.RoundToInt((c[i].time - c[i - 1].time) * 1000); if (ms >= 32 && ms <= 34) k30++; else if (ms >= 16 && ms <= 17) k60++; else other++; }
                    }
                    Debug.Log($"SURVEY {path.Replace("Assets/", "")} len={clip.length:0.00}s rate={clip.frameRate} keys@33ms={k30} keys@17ms={k60} other={other}");
                }
            }
        }

        public static void Run()
        {
            foreach (var path in new[] { "Assets/Characters/MatchHeroes/Male/Male_Forehand.fbx", "Assets/Characters/MatchHeroes/Male/Male_Serve.fbx", "Assets/Characters/MatchHeroes/Male/Male_Emote_Spike.fbx", "Assets/Characters/MatchHeroes/Male/Male_Walk.fbx" })
            {
                var clip = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>().FirstOrDefault(c => !c.name.StartsWith("__"));
                if (!clip) { Debug.Log("PROBE missing " + path); continue; }
                var spacing = new SortedDictionary<int, int>(); var modes = new Dictionary<string, int>(); int curves = 0, keys = 0;
                foreach (var b in AnimationUtility.GetCurveBindings(clip))
                {
                    var c = AnimationUtility.GetEditorCurve(clip, b); curves++;
                    for (int i = 0; i < c.length; i++)
                    {
                        keys++;
                        string m = AnimationUtility.GetKeyLeftTangentMode(c, i) + "/" + AnimationUtility.GetKeyRightTangentMode(c, i);
                        modes[m] = modes.TryGetValue(m, out var n) ? n + 1 : 1;
                        if (i > 0) { int ms = Mathf.RoundToInt((c[i].time - c[i - 1].time) * 1000); spacing[ms] = spacing.TryGetValue(ms, out var k) ? k + 1 : 1; }
                    }
                }
                Mid(clip);
                Debug.Log($"PROBE {clip.name} len={clip.length:0.000}s frameRate={clip.frameRate} curves={curves} keys={keys} spacingMs={string.Join(",", spacing.OrderByDescending(p => p.Value).Take(4).Select(p => p.Key + "ms:" + p.Value))} tangents={string.Join(",", modes.Select(p => p.Key + ":" + p.Value))}");
            }
        }

        static void Mid(AnimationClip clip)
        {
            var q = new Dictionary<string, AnimationCurve[]>();
            int linear = 0, total = 0;
            foreach (var b in AnimationUtility.GetCurveBindings(clip))
            {
                var c = AnimationUtility.GetEditorCurve(clip, b);
                for (int i = 0; i + 1 < c.length; i++) { total++; float slope = (c[i + 1].value - c[i].value) / Mathf.Max(1e-6f, c[i + 1].time - c[i].time); if (Mathf.Abs(c[i].outTangent - slope) < 1e-3f * (1 + Mathf.Abs(slope))) linear++; }
                if (!b.propertyName.StartsWith("m_LocalRotation.")) continue;
                if (!q.TryGetValue(b.path, out var arr)) q[b.path] = arr = new AnimationCurve[4];
                arr["xyzw".IndexOf(b.propertyName[b.propertyName.Length - 1])] = c;
            }
            float worst = 0; string worstBone = ""; var all = new List<float>(); var played2 = new List<float>(); var lin2 = new List<float>();
            foreach (var kv in q)
            {
                var c = kv.Value; if (c.Any(x => x == null) || c[0].length < 4) continue;
                for (int i = 1; i + 2 < c[0].length; i++)
                {
                    Quaternion At(int k) => new Quaternion(c[0][k].value, c[1][k].value, c[2][k].value, c[3][k].value);
                    var p0 = At(i - 1); var p1 = At(i); var p2 = At(i + 1); var p3 = At(i + 2);
                    if (Quaternion.Dot(p0, p1) < 0) p0 = Neg(p0);
                    if (Quaternion.Dot(p2, p1) < 0) p2 = Neg(p2);
                    if (Quaternion.Dot(p3, p2) < 0) p3 = Neg(p3);
                    Vector4 a = V(p0), b = V(p1), cc = V(p2), d = V(p3);
                    var r = .5f * (2 * b + (-a + cc) * .5f + (2 * a - 5 * b + 4 * cc - d) * .25f + (-a + 3 * b - 3 * cc + d) * .125f);
                    var spline = new Quaternion(r.x, r.y, r.z, r.w).normalized;
                    float deg = Quaternion.Angle(Quaternion.Slerp(p1, p2, .5f), spline); all.Add(deg);
                    float tm = (c[0][i].time + c[0][i + 1].time) * .5f; var played = new Quaternion(c[0].Evaluate(tm), c[1].Evaluate(tm), c[2].Evaluate(tm), c[3].Evaluate(tm)).normalized;
                    played2.Add(Quaternion.Angle(played, spline)); lin2.Add(Quaternion.Angle(played, Quaternion.Slerp(p1, p2, .5f)));
                    if (deg > worst) { worst = deg; worstBone = kv.Key; }
                }
            }
            played2.Sort(); lin2.Sort(); all.Sort();
            Debug.Log($"PROBE   {clip.name} PLAYED-vs-spline p99={played2[(int)(played2.Count * .99f)]:0.00} max={played2[played2.Count - 1]:0.0}deg | PLAYED-vs-chord p99={lin2[(int)(lin2.Count * .99f)]:0.00} max={lin2[lin2.Count - 1]:0.0}deg");
            Debug.Log($"PROBE   {clip.name} linearTangents={linear}/{total} midpointOffSpline: p50={all[all.Count / 2]:0.00}deg p99={all[(int)(all.Count * .99f)]:0.00}deg max={worst:0.0}deg at {worstBone}");
        }
        static Quaternion Neg(Quaternion q) => new Quaternion(-q.x, -q.y, -q.z, -q.w);
        static Vector4 V(Quaternion q) => new Vector4(q.x, q.y, q.z, q.w);
    }
}
