using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// HERO BUILD (2026-11-11, Adnan: "more muscular and fill their shirts out (men) and the woman anatomy with her arms"):
    /// one smooth shape field in the hero's rest pose, applied to the body AND to every garment that covers it, so the cloth follows the
    /// build underneath instead of ballooning round it.
    ///   men:   deltoid / biceps / forearm, pecs, a wider upper back and traps, a waist that tapers (the V), a fuller neck, calves
    ///   women: the arm form only (shoulder cap, upper arm, a forearm that tapers to the wrist)
    /// Positions, normals and tangents only (the field's Jacobian carries the normals); weights, UVs, blend shapes and topology are untouched.
    /// HERO_BUILD=0 switches it off; HERO_MUSCLE scales the men's torso and limb gains; HERO_ARM_GAIN scales the women's arms.
    public static class HeroBuild
    {
        public static bool On => System.Environment.GetEnvironmentVariable("HERO_BUILD") != "0";
        /// The men's arm: the even thickening of 11-11 ("fat, not defined": the forearm grew as much as the upper arm) is on its way
        /// out for the muscle model of work/final-plan-1111/phase2 (PLAN_FinalLook_Gameplay Phase 2). Until that is approved and
        /// installed this stays false, and HERO_BUILD_ARM=0 in the Editor gives the build without its arm term for comparison.
        public static bool ArmMusclesReplaceTheField => System.Environment.GetEnvironmentVariable("HERO_BUILD_ARM") == "0";
        static float Env(string k, float d) => float.TryParse(System.Environment.GetEnvironmentVariable(k), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : d;
        static float Bump(float t, float c, float w) { float x = (t - c) / w; return Mathf.Exp(-x * x); }
        static float Smooth(float a, float b, float x) { float t = Mathf.Clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); }

        sealed class Rig
        {
            public Vector3[] S = new Vector3[2], E = new Vector3[2], W = new Vector3[2], H = new Vector3[2], K = new Vector3[2], A = new Vector3[2];
            public Vector3 chest, neck, head, hips, fwd; public float half, shoulderY; public bool female;
            // the body's own displacement (hero space), sampled by the garments so cloth follows exactly what is under it
            public Vector3[] bodyP, bodyD; public Dictionary<Vector3Int, List<int>> grid;
            public const float Cell = .03f;
            public static Vector3Int Key(Vector3 p) => new Vector3Int(Mathf.FloorToInt(p.x / Cell), Mathf.FloorToInt(p.y / Cell), Mathf.FloorToInt(p.z / Cell));
            public Vector3 Sample(Vector3 p)
            {
                if (grid == null) return Vector3.zero;
                const float R = .045f; var c = Key(p); Vector3 sum = Vector3.zero; float ws = 0; int r = Mathf.CeilToInt(R / Cell);
                for (int x = -r; x <= r; x++) for (int y = -r; y <= r; y++) for (int z = -r; z <= r; z++)
                    if (grid.TryGetValue(new Vector3Int(c.x + x, c.y + y, c.z + z), out var l))
                        foreach (int i in l) { float d = (bodyP[i] - p).magnitude; if (d >= R) continue; float k = 1 - d / R; k = k * k * k; sum += bodyD[i] * k; ws += k; }
                return ws > 1e-6f ? sum / ws : Vector3.zero;
            }
        }
        static readonly Dictionary<MatchHeroLook, Rig> rigs = new();
        static readonly Dictionary<(Mesh, bool), Mesh> cache = new();

        static Rig RigOf(MatchHeroLook look)
        {
            if (rigs.TryGetValue(look, out var r)) return r;
            var body = look.body; if (!body || !body.sharedMesh) return null;
            var bones = body.bones; var binds = body.sharedMesh.bindposes; var toHero = look.transform.worldToLocalMatrix * body.transform.localToWorldMatrix;
            bool ok = true;
            Vector3 J(string name)
            {
                int i = System.Array.FindIndex(bones, b => b && b.name == name);
                if (i < 0 || i >= binds.Length) { ok = false; return Vector3.zero; }
                return toHero.MultiplyPoint3x4(binds[i].inverse.GetColumn(3));
            }
            r = new Rig { female = look.female };
            string[] side = { "Left", "Right" };
            for (int s = 0; s < 2; s++)
            {
                r.S[s] = J(side[s] + "UpperArm"); r.E[s] = J(side[s] + "LowerArm"); r.W[s] = J(side[s] + "Hand");
                r.H[s] = J(side[s] + "UpperLeg"); r.K[s] = J(side[s] + "LowerLeg"); r.A[s] = J(side[s] + "Foot");
            }
            r.chest = J("Chest"); r.neck = J("Neck"); r.head = J("Head"); r.hips = J("Hips");
            var toe = J("LeftToes"); if (!ok) { Debug.LogWarning("[HeroBuild] bones missing on " + look.name); rigs[look] = null; return null; }
            r.fwd = toe - r.A[0]; r.fwd.y = 0; r.fwd.Normalize();
            r.half = Mathf.Abs(r.S[0].x - r.S[1].x) * .5f; r.shoulderY = (r.S[0].y + r.S[1].y) * .5f;
            rigs[look] = r; return r;
        }

        /// `garment`: a kit mesh (its arm gain is a little lower than the body's, so the arm fills the sleeve).
        public static Mesh Prepare(MatchHeroLook look, SkinnedMeshRenderer smr, Mesh source, bool garment)
        {
            // HERO STUDIO 2026-11-12: his body, tops and shoes are the studio's (HeroStudio); the build below is hers, and his only with HERO_STUDIO=0
            if (HeroStudio.Enabled && look && !look.female) return HeroStudio.Override(look, smr, source);
            if (!On || !look || !smr || !source || !source.isReadable) return source;
            if (source.name.Contains("(build)")) return source;
            if (cache.TryGetValue((source, look.female), out var ready) && ready) return ready;
            var rig = RigOf(look); if (rig == null) return source;
            var bones = smr.bones; var w = source.boneWeights; var v = source.vertices; int n = v.Length;
            if (w.Length != n || bones == null) return source;
            // bone roles in THIS renderer's palette
            var role = new int[bones.Length];   // 1,2 = left/right arm  3,4 = left/right leg  5 = torso  6 = neck
            for (int b = 0; b < bones.Length; b++)
            {
                string nm = bones[b] ? bones[b].name : "";
                role[b] = nm == "LeftUpperArm" || nm == "LeftLowerArm" ? 1 : nm == "RightUpperArm" || nm == "RightLowerArm" ? 2
                        : nm == "LeftUpperLeg" || nm == "LeftLowerLeg" ? 3 : nm == "RightUpperLeg" || nm == "RightLowerLeg" ? 4
                        : nm == "Hips" || nm == "Spine" || nm == "Chest" || nm == "UpperChest" || nm == "LeftShoulder" || nm == "RightShoulder" ? 5 : nm == "Neck" ? 6 : 0;
            }
            Matrix4x4 toHero = look.transform.worldToLocalMatrix * smr.transform.localToWorldMatrix, fromHero = toHero.inverse;
            bool female = rig.female; float muscle = Env("HERO_MUSCLE", 1.2f), armGain = female ? Env("HERO_ARM_GAIN", .6f) : muscle;   // HER ARMS 2026-11-12: at 2 the forearm swelled by a third on a slim frame
            Vector3 up = Vector3.up, right = Vector3.Cross(up, rig.fwd).normalized; float cx0 = (rig.S[0].x + rig.S[1].x) * .5f;
            float waistY = Mathf.Lerp(rig.hips.y, rig.shoulderY, .34f);
            var m = new float[7];
            // every mask is geometric (distance to a limb axis, position on the torso), so the body and every garment over it get the SAME
            // displacement at the same place: cloth can neither sink into the skin nor lift off it
            float armIn = female ? .060f : .085f, armOut = female ? .100f : .130f;
            // A garment nothing on the arm wears (skirt, shorts, socks) takes no arm shape: at rest the hands hang beside the hips, and the
            // arm field reached 18 mm into her skirt and his shorts there, a dent that then stayed in the cloth when the arm moved away.
            bool armField = !garment;
            if (garment)
                for (int i = 0; i < n && !armField; i++)
                {
                    var bw = w[i];
                    float OnArm(int b, float x) => b >= 0 && b < role.Length && (role[b] == 1 || role[b] == 2) ? x : 0;
                    armField = OnArm(bw.boneIndex0, bw.weight0) + OnArm(bw.boneIndex1, bw.weight1) + OnArm(bw.boneIndex2, bw.weight2) + OnArm(bw.boneIndex3, bw.weight3) > .05f;
                }
            Vector3 Warp(Vector3 p, float[] mask)
            {
                Vector3 d = Vector3.zero;
                for (int s = 0; s < 2; s++)
                {
                    {
                        Vector3 A = rig.S[s], B = rig.E[s], C = rig.W[s];
                        float tu = Mathf.Clamp01(Vector3.Dot(p - A, B - A) / (B - A).sqrMagnitude), tl = Mathf.Clamp01(Vector3.Dot(p - B, C - B) / (C - B).sqrMagnitude);
                        Vector3 cu = A + (B - A) * tu, cl = B + (C - B) * tl; bool upper = (p - cu).sqrMagnitude <= (p - cl).sqrMagnitude;
                        Vector3 c = upper ? cu : cl; float rho = (p - c).magnitude, arm = 1 - Smooth(armIn, armOut, rho);
                        if (arm > 0 && armField && (female || !ArmMusclesReplaceTheField))
                        {
                            float g = female
                                ? (upper ? .05f + .09f * Bump(tu, .32f, .30f) - .03f * Bump(tu, .90f, .10f) : .04f + .13f * Bump(tl, .22f, .26f) - .07f * Smooth(.55f, 1f, tl) - .10f * Smooth(.92f, 1f, tl))
                                : (upper ? .065f + .115f * Bump(tu, .36f, .30f) - .02f * Bump(tu, .92f, .10f) : .07f + .12f * Bump(tl, .24f, .26f) - .07f * Smooth(.60f, 1f, tl));
                            d += (p - c) * (Mathf.Max(g, 0) * armGain * arm);
                        }
                    }
                    if (female) continue;
                    {
                        Vector3 A = rig.H[s], B = rig.K[s], C = rig.A[s];
                        float tu = Mathf.Clamp01(Vector3.Dot(p - A, B - A) / (B - A).sqrMagnitude), tl = Mathf.Clamp01(Vector3.Dot(p - B, C - B) / (C - B).sqrMagnitude);
                        Vector3 cu = A + (B - A) * tu, cl = B + (C - B) * tl; bool upper = (p - cu).sqrMagnitude <= (p - cl).sqrMagnitude;
                        Vector3 c = upper ? cu : cl; float rho = (p - c).magnitude, leg = (1 - Smooth(upper ? .115f : .075f, upper ? .155f : .105f, rho)) * Smooth(rig.A[s].y, rig.A[s].y + .06f, p.y) * (1 - Smooth(rig.H[s].y - .02f, rig.H[s].y + .04f, p.y));
                        if (leg > 0)
                        {
                            float g = upper ? .035f * Bump(tu, .40f, .32f) : .085f * Bump(tl, .27f, .22f) * (1 - Smooth(.62f, .9f, tl));
                            d += (p - c) * (g * muscle * leg);
                        }
                    }
                }
                if (female) return p + d;
                {
                    float x = p.x - cx0, y = p.y, z = Vector3.Dot(p - rig.chest, rig.fwd), ax = Mathf.Abs(x), sx = x >= 0 ? 1 : -1;
                    float torso = (1 - Smooth(rig.half * 1.00f, rig.half * 1.30f, ax)) * Smooth(rig.hips.y - .06f, rig.hips.y + .02f, y) * (1 - Smooth(rig.shoulderY + .07f, rig.shoulderY + .12f, y));
                    if (torso > 0)
                    {
                        // pecs: two soft lobes on the front of the chest
                        float pec = Bump(ax, rig.half * .50f, .072f) * Bump(y, rig.shoulderY - .100f, .058f) * Smooth(0, .05f, z);
                        d += (rig.fwd * .92f + Vector3.right * (sx * .22f)).normalized * (.016f * pec * torso * muscle);
                        // upper back and lats: wider and a little deeper across the shoulder blades
                        float band = Bump(y, rig.shoulderY - .085f, .095f);
                        d += -rig.fwd * (.008f * band * Smooth(0, .05f, -z) * torso * muscle);
                        d += Vector3.right * (sx * .010f * band * Smooth(rig.half * .35f, rig.half * .9f, ax) * torso * muscle);
                        // traps: the slope from neck to shoulder
                        d += up * (.007f * Bump(ax, rig.half * .44f, .050f) * Bump(y, rig.shoulderY + .030f, .036f) * torso * muscle);
                        // waist: drawn in toward the spine (the shirt stops ballooning over the stomach); nothing at the hips or the chest
                        Vector3 rad = new Vector3(x, 0, 0) + rig.fwd * z; float rl = rad.magnitude;
                        if (rl > 1e-4f) d += -(rad / rl) * (Mathf.Min(.013f, rl * .12f) * Bump(y, waistY, .080f) * torso * muscle);
                    }
                    Vector3 ax2 = rig.head - rig.neck; float t = Mathf.Clamp01(Vector3.Dot(p - rig.neck, ax2) / ax2.sqrMagnitude); Vector3 nc = rig.neck + ax2 * t;
                    float neck = (1 - Smooth(.070f, .100f, (p - nc).magnitude)) * (1 - Smooth(.55f, 1f, t)) * Smooth(rig.shoulderY + .02f, rig.shoulderY + .06f, y);
                    if (neck > 0) d += (p - nc) * (.07f * neck * muscle);
                }
                return p + d;
            }
            var q = new Vector3[n]; var after = new Vector3[n]; var normals = source.normals; var tangents = source.tangents;
            var newNormals = (Vector3[])normals.Clone(); var newTangents = (Vector4[])tangents.Clone();
            int moved = 0; float largest = 0; const float e = .0005f;
            for (int i = 0; i < n; i++)
            {
                for (int k = 0; k < 7; k++) m[k] = 0;
                var bw = w[i];
                void Add(int b, float x) { if (b >= 0 && b < role.Length && role[b] > 0) m[role[b]] += x; }
                Add(bw.boneIndex0, bw.weight0); Add(bw.boneIndex1, bw.weight1); Add(bw.boneIndex2, bw.weight2); Add(bw.boneIndex3, bw.weight3);
                q[i] = toHero.MultiplyPoint3x4(v[i]);
                var t = Warp(q[i], m);
                if ((t - q[i]).sqrMagnitude < 1e-12f) { after[i] = v[i]; continue; }
                moved++; largest = Mathf.Max(largest, (t - q[i]).magnitude); after[i] = fromHero.MultiplyPoint3x4(t);
                var j = Matrix4x4.identity;
                j.SetColumn(0, (Warp(q[i] + Vector3.right * e, m) - t) / e); j.SetColumn(1, (Warp(q[i] + Vector3.up * e, m) - t) / e); j.SetColumn(2, (Warp(q[i] + Vector3.forward * e, m) - t) / e);
                var heroJ = fromHero * j * toHero;
                if (i < normals.Length) newNormals[i] = heroJ.inverse.transpose.MultiplyVector(normals[i]).normalized;
                if (i < tangents.Length) { var t3 = heroJ.MultiplyVector(new Vector3(tangents[i].x, tangents[i].y, tangents[i].z)).normalized; newTangents[i] = new Vector4(t3.x, t3.y, t3.z, tangents[i].w); }
            }
            if (!garment)
            {
                // (the garments take the same geometric field as the body, so nothing samples these any more: the look-up grid over
                // them, a dictionary entry and a list per cell for 52,000 vertices on every first build, is no longer made)
                rig.bodyP = q; rig.bodyD = new Vector3[n];
                for (int i = 0; i < n; i++) rig.bodyD[i] = toHero.MultiplyPoint3x4(after[i]) - q[i];
            }
            if (moved == 0) { cache[(source, look.female)] = source; return source; }
            if (!garment && female && normals.Length == n && System.Environment.GetEnvironmentVariable("HERO_ARM_NORMALS") != "0")
            {
                // her shoulder caps and arms shaded in flat patches (stored normals): rebuild them there from the surface itself, welded by
                // position and relaxed twice over the surface, blended in by distance from the arm and the shoulder joint
                var weld = new Dictionary<Vector3Int, int>(); var group = new int[n]; int groups = 0;
                for (int i = 0; i < n; i++) { var key = new Vector3Int(Mathf.RoundToInt(after[i].x * 20000), Mathf.RoundToInt(after[i].y * 20000), Mathf.RoundToInt(after[i].z * 20000)); if (!weld.TryGetValue(key, out int g)) weld[key] = g = groups++; group[i] = g; }
                var acc = new Vector3[groups]; var nb = new List<int>[groups]; var tris = source.triangles;
                for (int t = 0; t < tris.Length; t += 3)
                {
                    int a = tris[t], b = tris[t + 1], c = tris[t + 2]; var fn = Vector3.Cross(after[b] - after[a], after[c] - after[a]);
                    foreach (int k in new[] { a, b, c }) acc[group[k]] += fn;
                    void Link(int x, int y) { (nb[x] ??= new List<int>()).Add(y); (nb[y] ??= new List<int>()).Add(x); }
                    Link(group[a], group[b]); Link(group[b], group[c]); Link(group[c], group[a]);
                }
                for (int g = 0; g < groups; g++) acc[g] = acc[g].sqrMagnitude > 1e-20f ? acc[g].normalized : Vector3.up;
                for (int pass = 0; pass < 2; pass++)
                {
                    var next = new Vector3[groups];
                    for (int g = 0; g < groups; g++) { var sum = acc[g] * 2; if (nb[g] != null) foreach (int o in nb[g]) sum += acc[o]; next[g] = sum.normalized; }
                    acc = next;
                }
                int smoothed = 0;
                for (int i = 0; i < n; i++)
                {
                    float zone = 0;
                    for (int s2 = 0; s2 < 2; s2++)
                    {
                        Vector3 A = rig.S[s2], B = rig.E[s2], C = rig.W[s2]; var p = q[i];
                        float tu = Mathf.Clamp01(Vector3.Dot(p - A, B - A) / (B - A).sqrMagnitude), tl = Mathf.Clamp01(Vector3.Dot(p - B, C - B) / (C - B).sqrMagnitude);
                        float rho = Mathf.Min((p - (A + (B - A) * tu)).magnitude, (p - (B + (C - B) * tl)).magnitude);
                        zone = Mathf.Max(zone, (1 - Smooth(.075f, .125f, rho)) * (1 - Smooth(.85f, 1f, tl) * (rho < .001f ? 0 : 1) * ((p - (B + (C - B) * tl)).magnitude <= (p - (A + (B - A) * tu)).magnitude ? 1 : 0)));
                    }
                    if (zone <= 0) continue;
                    newNormals[i] = Vector3.Slerp(newNormals[i], acc[group[i]], zone).normalized; smoothed++;
                }
                Debug.Log($"[HeroBuild] {smr.name}: shoulder and arm normals rebuilt on {smoothed} vertices");
            }
            ready = Object.Instantiate(source); ready.name = source.name + " (build)"; ready.hideFlags = HideFlags.DontSave;
            ready.vertices = after;
            if (normals.Length == n) ready.normals = newNormals;
            if (tangents.Length == n) ready.tangents = newTangents;
            ready.RecalculateBounds();
            cache[(source, look.female)] = ready;
            Debug.Log($"[HeroBuild] {smr.name} {source.name}: moved={moved}/{n} largest={largest * 1000:F1}mm {(female ? "female" : "male")}{(garment ? " garment" : "")}");
            return ready;
        }
    }
}
