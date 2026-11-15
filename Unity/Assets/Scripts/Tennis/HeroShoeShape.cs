using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Bald-base pass 2 (2026-10-12): the tennis shoe reads as a clean sneaker rather than a box.
    ///
    /// Garment only, once per source mesh, in the shoe's bind pose: seen from above, the toe tapers and its two front corners round off,
    /// and the heel rounds a little. The upper and the sole (both submeshes) take the same plan-view map, so they stay stacked, and no
    /// vertex moves further than its own clearance to the foot / sock inside (minus Keep), so nothing can show through. Height, UVs,
    /// weights and bind poses are unchanged; normals and tangents go through the map's Jacobian.
    public static class HeroShoeShape
    {
        static float Toe = .14f, Corner = .45f, Heel = .06f; const float Keep = .004f;
        /// HERO DEPTH (work/hero-depth-1111, clone only): the Clothing V2 shoes read as hooves (width/length .49, a blunt toe box as tall as the
        /// heel). V2 = a real sneaker last: a stronger plan taper whose tip sits toward the big toe, a toe box that drops toward the tip (the
        /// sole thins with it, the bottom stays on the ground), and rigid footwear weights (heel on the foot, not the shin).
        public static bool Depth => System.Environment.GetEnvironmentVariable("HERO_DEPTH") != "0";
        /// HERO PRESENCE (2026-11-11): cloth that keeps its shape in strong light, a firmer ground shadow, hero lighting on. HERO_PRESENCE=0 = off.
        public static bool Presence => System.Environment.GetEnvironmentVariable("HERO_PRESENCE") != "0";
        static float Drop, Medial, Flat, Waist; static bool v2;
        static float EnvF(string k, float d) => float.TryParse(System.Environment.GetEnvironmentVariable(k), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : d;
        public static Mesh PrepareV2(SkinnedMeshRenderer shoe, Transform root, bool male)
        {
            (float t, float c, float h) keep = (Toe, Corner, Heel);
            Toe = male ? .34f : .26f; Corner = .45f; Heel = .10f; Drop = male ? .36f : .30f; Medial = .08f; Flat = EnvF("HERO_SHOE_FLAT", .85f); Waist = EnvF("HERO_SHOE_WAIST", .14f); v2 = true;
            try { return Prepare(shoe, root); } finally { (Toe, Corner, Heel) = keep; v2 = false; }
        }
        static readonly Dictionary<Mesh, Mesh> cache = new();

        /// `inside`: the bind-pose renderers the shoe must keep covering (the body and this side's sock).
        public static Mesh Prepare(SkinnedMeshRenderer shoe, Transform root, params SkinnedMeshRenderer[] inside)
        {
            var source = shoe ? shoe.sharedMesh : null;
            if (!source || !source.isReadable || !root || source.name.Contains("(sneaker shape)")) return source;
            if (cache.TryGetValue(source, out var ready) && ready) return ready;
            Matrix4x4 toRoot = root.worldToLocalMatrix * shoe.transform.localToWorldMatrix, fromRoot = toRoot.inverse;
            var sv = source.vertices; int n = sv.Length; var q = new Vector3[n];
            for (int i = 0; i < n; i++) q[i] = toRoot.MultiplyPoint3x4(sv[i]);
            // plan axes: the shoe's long axis (principal direction on the ground) and its side; the toe is the end with the lower upper
            Vector2 mean = Vector2.zero; foreach (var p in q) mean += new Vector2(p.x, p.z); mean /= n;
            float cxx = 0, cxz = 0, czz = 0; foreach (var p in q) { float x = p.x - mean.x, z = p.z - mean.y; cxx += x * x; cxz += x * z; czz += z * z; }
            float angle = .5f * Mathf.Atan2(2 * cxz, cxx - czz); var along = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
            float fMin = float.MaxValue, fMax = float.MinValue; foreach (var p in q) { float f = Vector2.Dot(new Vector2(p.x, p.z) - mean, along); fMin = Mathf.Min(fMin, f); fMax = Mathf.Max(fMax, f); }
            float TopNear(float f0) { float top = float.MinValue; foreach (var p in q) { float f = Vector2.Dot(new Vector2(p.x, p.z) - mean, along); if (Mathf.Abs(f - f0) < .03f) top = Mathf.Max(top, p.y); } return top; }
            if (TopNear(fMax - .015f) > TopNear(fMin + .015f)) { along = -along; (fMin, fMax) = (-fMax, -fMin); }
            var across = new Vector2(-along.y, along.x);
            // half width along the shoe (1 cm stations), from every vertex of both submeshes
            int stations = Mathf.CeilToInt((fMax - fMin) / .01f) + 1; var half = new float[stations];
            int Station(float f) => Mathf.Clamp(Mathf.RoundToInt((f - fMin) / .01f), 0, stations - 1);
            float sMid = 0; foreach (var p in q) sMid += Vector2.Dot(new Vector2(p.x, p.z) - mean, across); sMid /= n;
            foreach (var p in q) { var d = new Vector2(p.x, p.z) - mean; int k = Station(Vector2.Dot(d, along)); half[k] = Mathf.Max(half[k], Mathf.Abs(Vector2.Dot(d, across) - sMid)); }
            // smooth the 1 cm stations (a stepped width would kink the taper between them)
            var smooth = (float[])half.Clone(); for (int k = 1; k + 1 < stations; k++) smooth[k] = Mathf.Max(half[k], .5f * (half[k - 1] + half[k + 1]));
            // IDEAL HERO: the underside of the sole per 1 cm station (the rocker curve), so V2 can lay the sole flat
            var under = new float[stations]; for (int k = 0; k < stations; k++) under[k] = float.MaxValue;
            foreach (var p in q) { int k = Station(Vector2.Dot(new Vector2(p.x, p.z) - mean, along)); under[k] = Mathf.Min(under[k], p.y); }
            { float lowest = float.MaxValue; foreach (var u in under) lowest = Mathf.Min(lowest, u); for (int k = 0; k < stations; k++) if (under[k] == float.MaxValue) under[k] = lowest;
              var u2 = (float[])under.Clone(); for (int pass = 0; pass < 3; pass++) { for (int k = 1; k + 1 < stations; k++) u2[k] = (under[k - 1] + 2 * under[k] + under[k + 1]) * .25f; under = (float[])u2.Clone(); } }
            float Under(float f) { float x = Mathf.Clamp((f - fMin) / .01f, 0, stations - 1.001f); int k = (int)x; return Mathf.Lerp(under[k], under[Mathf.Min(k + 1, stations - 1)], x - k); }
            float Half(float f) { float x = Mathf.Clamp((f - fMin) / .01f, 0, stations - 1.001f); int k = (int)x; return Mathf.Lerp(smooth[k], smooth[Mathf.Min(k + 1, stations - 1)], x - k); }
            float widest = 0; foreach (var h in smooth) widest = Mathf.Max(widest, h);
            float length = fMax - fMin, toeStart = fMax - .45f * length, heelEnd = fMin + .22f * length;
            float yMin = float.MaxValue, yMax = float.MinValue; foreach (var p in q) { yMin = Mathf.Min(yMin, p.y); yMax = Mathf.Max(yMax, p.y); }
            float medial = (mean.x < 0 ? 1 : -1) * Mathf.Sign(across.x);   // toward the other foot
            // the sole keeps its thickness (and its trim line): only what stands above it drops toward the toe
            float soleTop = yMin;
            if (v2 && source.subMeshCount > 1) { float soleMax = yMin; foreach (int k in source.GetIndices(1)) soleMax = Mathf.Max(soleMax, q[k].y); soleTop = yMin + (soleMax - yMin) * .85f; }
            float Smooth(float a, float b, float x) { float t = Mathf.Clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); }
            Vector3 Plan(Vector3 p)
            {
                var d = new Vector2(p.x, p.z) - mean; float f = Vector2.Dot(d, along), s = Vector2.Dot(d, across) - sMid;
                // measured against at least 60 % of the widest point: at the very tip the width collapses and would shear the taper
                float w = Mathf.Max(Half(f), .6f * widest), r = Mathf.Clamp01(Mathf.Abs(s) / w);
                float toe = Smooth(toeStart, fMax, f), heel = 1 - Smooth(fMin, heelEnd, f);
                float narrow = Toe * toe * toe + Heel * heel * heel;
                s *= 1 - narrow * r;                                                           // taper, strongest at the outer edge
                f -= Corner * Toe * toe * toe * r * r * (f - toeStart) * .5f;                   // pull the toe's front corners back: a round toe
                f += Corner * Heel * heel * heel * r * r * (heelEnd - f) * .5f;
                float y = p.y;
                if (v2)
                {
                    float drop = Smooth(fMax - .55f * length, fMax, f);
                    s += Medial * medial * toe * toe * widest;                                 // the tip sits toward the big toe (a left and a right shoe)
                    // a flat sole: take the rocker out of the underside, fading to nothing at the top of the sole
                    { float lift = Under(f) - yMin; if (lift > 0 && Flat > 0) { float keep = Mathf.Clamp01((p.y - Under(f)) / Mathf.Max(soleTop - yMin, .005f)); y -= lift * Flat * (1 - keep * keep); } }
                    // a waist: the inner side draws in under the arch
                    { float tt = (f - fMin) / length; float w0 = Mathf.Exp(-((tt - .45f) / .16f) * ((tt - .45f) / .16f)); if (s * medial > 0) s *= 1 - Waist * w0; }
                    if (p.y > soleTop) y = soleTop + (p.y - soleTop) * (1 - Drop * 1.35f * Mathf.Pow(drop, 1.5f)); // the toe box drops toward the tip, over a sole of full thickness
                }
                var o = mean + along * f + across * (s + sMid);
                return new Vector3(o.x, y, o.y);
            }
            // clearance to what the shoe covers, in root space
            var inner = new List<Vector3>(); float top = float.MinValue; foreach (var p in q) top = Mathf.Max(top, p.y);
            foreach (var r in inside)
            {
                if (!r || !r.sharedMesh || !r.sharedMesh.isReadable) continue;
                var m = root.worldToLocalMatrix * r.transform.localToWorldMatrix;
                foreach (var v in r.sharedMesh.vertices) { var p = m.MultiplyPoint3x4(v); if (p.y < top + .02f) inner.Add(p); }
            }
            const float cell = .02f; var grid = new Dictionary<Vector3Int, List<Vector3>>();
            Vector3Int Cell(Vector3 p) => new Vector3Int(Mathf.FloorToInt(p.x / cell), Mathf.FloorToInt(p.y / cell), Mathf.FloorToInt(p.z / cell));
            foreach (var p in inner) { var c = Cell(p); if (!grid.TryGetValue(c, out var l)) grid[c] = l = new List<Vector3>(); l.Add(p); }
            float Clearance(Vector3 p)
            {
                float best = cell * 1.5f; var c = Cell(p);
                for (int x = -1; x <= 1; x++) for (int y = -1; y <= 1; y++) for (int z = -1; z <= 1; z++)
                    if (grid.TryGetValue(new Vector3Int(c.x + x, c.y + y, c.z + z), out var l)) foreach (var o in l) best = Mathf.Min(best, (o - p).magnitude);
                return best;
            }
            // soft cap: the move eases off before it reaches the clearance (no kink where the cap starts)
            Vector3 Warp(Vector3 p, float allow) { var t = Plan(p); var d = t - p; float m = d.magnitude; if (m < 1e-7f) return t; float capped = allow * (1 - Mathf.Exp(-m / Mathf.Max(allow, 1e-5f))); return p + d * (Mathf.Min(m, capped) / m); }
            var after = new Vector3[n]; var normals = source.normals; var tangents = source.tangents;
            var newNormals = (Vector3[])normals.Clone(); var newTangents = (Vector4[])tangents.Clone();
            int moved = 0; float largest = 0, minimumJacobian = 1; const float e = .0001f;
            for (int i = 0; i < n; i++)
            {
                float allow = inner.Count > 0 ? Mathf.Max(0, Clearance(q[i]) - Keep) : v2 ? 1f : .01f;
                var w = Warp(q[i], allow);
                if ((w - q[i]).sqrMagnitude < 1e-12f) { after[i] = sv[i]; continue; }
                moved++; largest = Mathf.Max(largest, (w - q[i]).magnitude); after[i] = fromRoot.MultiplyPoint3x4(w);
                var j = Matrix4x4.identity;
                j.SetColumn(0, (Warp(q[i] + Vector3.right * e, allow) - w) / e); j.SetColumn(1, (Warp(q[i] + Vector3.up * e, allow) - w) / e); j.SetColumn(2, (Warp(q[i] + Vector3.forward * e, allow) - w) / e);
                minimumJacobian = Mathf.Min(minimumJacobian, j.determinant);
                var rootJ = fromRoot * j * toRoot;
                if (i < normals.Length) newNormals[i] = rootJ.inverse.transpose.MultiplyVector(normals[i]).normalized;
                if (i < tangents.Length) { var t3 = rootJ.MultiplyVector(new Vector3(tangents[i].x, tangents[i].y, tangents[i].z)).normalized; newTangents[i] = new Vector4(t3.x, t3.y, t3.z, tangents[i].w); }
            }
            ready = Object.Instantiate(source); ready.name = source.name + " (sneaker shape)"; ready.hideFlags = HideFlags.DontSave;
            ready.vertices = after;
            if (normals.Length == n) ready.normals = newNormals;
            if (tangents.Length == n) ready.tangents = newTangents;
            if (v2 && source.bindposes.Length == 3)
            {
                // rigid footwear rule (the female shoes' rule, work/clothing-v2/pipeline/gp/weights.py): bones = lower leg, foot, toes
                var bw = new BoneWeight[n];
                for (int i = 0; i < n; i++)
                {
                    float f = Vector2.Dot(new Vector2(q[i].x, q[i].z) - mean, along), t = (f - fMin) / length, h = q[i].y - yMin;
                    float toes = .55f * Smooth(.66f, 1f, t), shin = .85f * Smooth(.075f, .16f, h) * (1 - Smooth(.30f, .55f, t)), foot = 1 - toes - shin;
                    var w = new BoneWeight { boneIndex0 = 1, weight0 = foot };
                    if (toes > shin) { w.boneIndex1 = 2; w.weight1 = toes; w.boneIndex2 = 0; w.weight2 = shin; } else { w.boneIndex1 = 0; w.weight1 = shin; w.boneIndex2 = 2; w.weight2 = toes; }
                    bw[i] = w;
                }
                ready.boneWeights = bw;
            }
            ready.RecalculateBounds();
            cache[source] = ready;
            Debug.Log($"[HeroShoeShape] {source.name}: moved={moved}/{n} largest={largest * 1000:F1}mm minJacobian={minimumJacobian:F3} length={length * 1000:F0}mm inside={inner.Count}");
            return ready;
        }
    }
}
