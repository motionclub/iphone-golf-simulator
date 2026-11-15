using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// HERO DEPTH (work/hero-depth-1111, clone only): the female arms are two straight tubes (half-width ~4 cm the whole length), so every
    /// bent elbow reads as a stick insect's. A form pass in the bind pose, arms only: each arm vertex moves along its radius from the
    /// shoulder-elbow / elbow-wrist axis by a smooth profile (deltoid and biceps swell, a slight neck above the elbow, a forearm belly
    /// that tapers to the wrist). It fades with the arm's own skin weight, so the shoulder seam and the hand do not move. Positions only.
    public static class HeroArmForm
    {
        static readonly Dictionary<Mesh, Mesh> cache = new();
        static float Bump(float t, float c, float w) { float x = (t - c) / w; return Mathf.Exp(-x * x); }
        static float Smooth(float a, float b, float x) { float t = Mathf.Clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); }
        static float Env(string k, float d) => float.TryParse(System.Environment.GetEnvironmentVariable(k), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : d;

        public static Mesh Prepare(SkinnedMeshRenderer body)
        {
            var source = body ? body.sharedMesh : null;
            if (!source || !source.isReadable) return source;
            if (cache.TryGetValue(source, out var ready) && ready) return ready;
            var bones = body.bones; var binds = source.bindposes; var weights = source.boneWeights; var v = source.vertices;
            float gain = Env("HERO_ARM_GAIN", 2f);
            var after = (Vector3[])v.Clone(); int moved = 0; float largest = 0;
            foreach (string side in new[] { "Left", "Right" })
            {
                int iu = System.Array.FindIndex(bones, b => b && b.name == side + "UpperArm"), il = System.Array.FindIndex(bones, b => b && b.name == side + "LowerArm"), ih = System.Array.FindIndex(bones, b => b && b.name == side + "Hand");
                if (iu < 0 || il < 0 || ih < 0) { Debug.LogWarning($"[HeroArmForm] {side} arm bones not found"); continue; }
                Vector3 A = binds[iu].inverse.GetColumn(3), B = binds[il].inverse.GetColumn(3), C = binds[ih].inverse.GetColumn(3);
                for (int i = 0; i < v.Length; i++)
                {
                    var w = weights[i]; float wu = 0, wl = 0;
                    void Add(int b, float x) { if (b == iu) wu += x; else if (b == il) wl += x; }
                    Add(w.boneIndex0, w.weight0); Add(w.boneIndex1, w.weight1); Add(w.boneIndex2, w.weight2); Add(w.boneIndex3, w.weight3);
                    float arm = wu + wl; if (arm < .05f) continue;
                    // the nearer of the two segments
                    Vector3 p = v[i];
                    float tu = Mathf.Clamp01(Vector3.Dot(p - A, B - A) / (B - A).sqrMagnitude), tl = Mathf.Clamp01(Vector3.Dot(p - B, C - B) / (C - B).sqrMagnitude);
                    Vector3 cu = A + (B - A) * tu, cl = B + (C - B) * tl; bool upper = (p - cu).sqrMagnitude <= (p - cl).sqrMagnitude;
                    Vector3 centre = upper ? cu : cl; float t = upper ? tu : tl;
                    float g = upper ? .05f + .09f * Bump(t, .32f, .30f) - .03f * Bump(t, .90f, .10f)
                                    : .04f + .13f * Bump(t, .22f, .26f) - .07f * Smooth(.55f, 1f, t);
                    float mask = Smooth(.25f, .85f, arm);
                    var d = (p - centre) * (g * gain * mask);
                    if (d.sqrMagnitude < 1e-12f) continue;
                    after[i] = p + d; moved++; largest = Mathf.Max(largest, d.magnitude);
                }
            }
            ready = Object.Instantiate(source); ready.name = source.name + " (arm form)"; ready.hideFlags = HideFlags.DontSave;
            ready.vertices = after; ready.RecalculateBounds();
            cache[source] = ready;
            Debug.Log($"[HeroArmForm] {source.name}: moved={moved} largest={largest * 1000:F1}mm");
            return ready;
        }
    }
}
