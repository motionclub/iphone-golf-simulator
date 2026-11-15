using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// ARM LIMITS (2026-11-12, work/final-plan-1111/anim; Adnan: "it's like her wrist is permanently broken. first we need to fix
    /// that, then rework the animations"). The clips were keyed on a rig with no hand to look at, and 91 of 107 take the hand more
    /// than 60 degrees off the forearm's line. This is the last step of the shared pose pass (HeroPoseSafety.Apply: tennis, golf,
    /// plaza, bowling), so every clip and blend gets one anatomical rule instead of 107 re-keyed clips:
    ///   the wrist: how far the hand's axis (wrist to middle knuckle) leaves the forearm's line, split into flexion (toward the
    ///     palm), extension, and deviation toward the thumb or the little finger, each with its own limit; a soft knee below it.
    ///   an EMPTY hand turns back about the wrist to the limit.
    ///   a hand ON a racket or club keeps its place and its rotation (the strings and the club face stay where the game put them):
    ///     the ELBOW swivels about the shoulder-wrist line to the place where the forearm lines up best with the hand, and only
    ///     what is left over, and only as far as the caller allows (away from contact), turns the hand.
    ///   the elbow never folds past its own limit on an empty arm.
    /// ARM_LIMITS=0 switches it off; ARM_LIMIT_<Name>=<number> overrides a number (Editor and tools).
    public static class HeroArmLimits
    {
        static float Tune(string name, float value)
        {
            var s = Environment.GetEnvironmentVariable("ARM_LIMIT_" + name);
            return s != null && float.TryParse(s, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : value;
        }
        public static bool Enabled = Environment.GetEnvironmentVariable("ARM_LIMITS") != "0";
        // degrees: an empty hand (a relaxed range, well inside what the joint can do) and a hand on a grip (what the joint can do)
        public static readonly float FreeFlex = Tune("FreeFlex", 40), FreeExt = Tune("FreeExt", 35), FreeRadial = Tune("FreeRadial", 14), FreeUlnar = Tune("FreeUlnar", 24), FreeKnee = Tune("FreeKnee", .5f);
        public static readonly float GripFlex = Tune("GripFlex", 60), GripExt = Tune("GripExt", 55), GripRadial = Tune("GripRadial", 20), GripUlnar = Tune("GripUlnar", 35), GripKnee = Tune("GripKnee", .7f);
        // a hand that steadies the racket or club but does not carry it (the ready cradle, the top hand of a two-handed grip)
        public static readonly float SupportFlex = Tune("SupportFlex", 42), SupportExt = Tune("SupportExt", 38), SupportRadial = Tune("SupportRadial", 16), SupportUlnar = Tune("SupportUlnar", 26), SupportKnee = Tune("SupportKnee", .5f);
        public static readonly float SupportMax = Tune("SupportMax", 50), GraspDepth = Tune("GraspDepth", .02f), SupportRate = Tune("SupportRate", 7);
        public static readonly float MaxSwivel = Tune("MaxSwivel", 26), SwivelCost = Tune("SwivelCost", .25f), LiftCost = Tune("LiftCost", 12), TurnRate = Tune("TurnRate", 4), SwivelRate = Tune("SwivelRate", 14), HandShare = Tune("HandShare", .6f);
        public static readonly float ElbowMax = Tune("ElbowMax", 142);

        /// What the pass did to one arm this frame (the probe and the tests read it).
        public struct Report
        {
            public int frame, kind; public bool holds;
            public float wristBefore, flexBefore, devBefore, wristAfter, flexAfter, devAfter, elbowBefore, elbowAfter, swivel, limit;
            public Quaternion upperBefore, lowerBefore, handBefore;
        }
        sealed class State { public readonly float[] swivel = new float[2], turn = new float[2], support = new float[2], free = new float[2]; public int frame = -100; public readonly Report[] report = new Report[2]; }
        static readonly Dictionary<MatchHeroLook, State> states = new Dictionary<MatchHeroLook, State>();
        public static bool TryReport(MatchHeroLook look, int side, out Report r)
        {
            r = default; if (!look || !states.TryGetValue(look, out var s)) return false; r = s.report[side]; return r.frame == Time.frameCount;
        }

        struct Frame { public Vector3 ax, ac, pn; }
        static bool HandFrame(Transform hand, Transform ip, Transform mp, Transform lp, bool left, out Frame f)
        {
            f = default; var ax = mp.position - hand.position; if (ax.sqrMagnitude < 1e-10f) return false; f.ax = ax.normalized;
            var ac = Vector3.ProjectOnPlane(ip.position - lp.position, f.ax); if (ac.sqrMagnitude < 1e-10f) return false; f.ac = ac.normalized;   // toward the thumb
            f.pn = left ? Vector3.Cross(f.ac, f.ax) : Vector3.Cross(f.ax, f.ac);                                                                 // the way the palm faces
            return true;
        }
        /// The wrist's bend for a forearm direction `fo` against a hand frame: the whole angle, flexion (+ toward the palm), deviation
        /// (+ toward the thumb), and the limit in that direction.
        static readonly float[][] Limits = { new[] { FreeFlex, FreeExt, FreeRadial, FreeUlnar, FreeKnee }, new[] { GripFlex, GripExt, GripRadial, GripUlnar, GripKnee }, new[] { SupportFlex, SupportExt, SupportRadial, SupportUlnar, SupportKnee } };
        const int Free = 0, Grip = 1, Support = 2;
        static float Wrist(Vector3 fo, in Frame h, int kind, out float flex, out float dev, out float limit)
        {
            float x = -Vector3.Dot(fo, h.ac), y = -Vector3.Dot(fo, h.pn), z = Vector3.Dot(fo, h.ax);
            float theta = Mathf.Acos(Mathf.Clamp(z, -1, 1)) * Mathf.Rad2Deg;
            flex = Mathf.Atan2(y, z) * Mathf.Rad2Deg; dev = Mathf.Atan2(x, z) * Mathf.Rad2Deg;
            var L = Limits[kind]; float a = x >= 0 ? L[2] : L[3], b = y >= 0 ? L[0] : L[1];
            float m = Mathf.Sqrt(x * x + y * y);
            if (m < 1e-5f) { limit = Mathf.Max(a, b); return theta; }
            float cx = x / m, cy = y / m;
            limit = 1f / Mathf.Sqrt(cx * cx / (a * a) + cy * cy / (b * b));
            return theta;
        }
        /// Unchanged up to knee x limit, then easing onto the limit (never past it).
        static float Soft(float theta, float limit, float knee)
        {
            float k = limit * knee; if (theta <= k) return theta;
            float room = Mathf.Max(1e-3f, limit - k);
            return k + room * (1 - Mathf.Exp(-(theta - k) / room));
        }

        /// holdsLeft / holdsRight: the hand is on a racket, club or ball (its rotation is the game's). freedom 0..1: how much of what the
        /// elbow could not fix such a hand may still turn (0 at a contact or in a two-handed grip). depth: the body's clearance
        /// test for a point (metres inside, 0 outside), so a swivelled elbow never goes into the trunk; null = no test.
        /// supports: -1, or the side (0 left, 1 right) whose hand only steadies the grip: it turns about what it grasps and its arm follows.
        public static void Apply(MatchHeroLook look, bool holdsLeft, bool holdsRight, float freedomLeft, float freedomRight, Func<Vector3, float, float> depth = null, int supports = -1, float supportWeight = 1)
        {
            if (!Enabled || !look) return;
            if (!states.TryGetValue(look, out var st)) { if (states.Count > 32) Prune(); states[look] = st = new State(); }
            int frame = Time.frameCount; float dt = Application.isPlaying && frame == st.frame + 1 ? Mathf.Max(Time.deltaTime, 1e-4f) : 0;
            bool again = Application.isPlaying && frame == st.frame;   // (in the Editor every sample of a tool or an export is its own pose) st.frame = frame;
            for (int s = 0; s < 2; s++)
            {
                bool left = s == 0, holds = left ? holdsLeft : holdsRight; float freedom = Mathf.Clamp01(left ? freedomLeft : freedomRight);
                var up = look.Bone(left ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm); var lo = look.Bone(left ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
                var hand = look.Bone(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
                var ip = look.Bone(left ? HumanBodyBones.LeftIndexProximal : HumanBodyBones.RightIndexProximal); var mp = look.Bone(left ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
                var lp = look.Bone(left ? HumanBodyBones.LeftLittleProximal : HumanBodyBones.RightLittleProximal);
                if (!up || !lo || !hand || !ip || !mp || !lp || !HandFrame(hand, ip, mp, lp, left, out var hf)) continue;
                Vector3 S = up.position, E = lo.position, W = hand.position; var fo = W - E; if (fo.sqrMagnitude < 1e-10f) continue; fo.Normalize();
                var rep = new Report { frame = frame, holds = holds, upperBefore = up.rotation, lowerBefore = lo.rotation, handBefore = hand.rotation };
                int kind = !holds ? Free : s == supports ? Support : Grip;
                rep.wristBefore = Wrist(fo, hf, kind, out rep.flexBefore, out rep.devBefore, out rep.limit); rep.kind = kind;
                rep.elbowBefore = Vector3.Angle(E - S, W - E);
                float knee = Limits[kind][4];

                // a steadying hand: it turns about the middle of what it grasps (the fingers stay where they are, the wrist end swings
                // into the forearm's line) and the arm is solved again to the wrist's new place. Eased in and out (the hand comes onto
                // the racket and leaves it over a few frames), so the arm never jumps when the grip changes.
                float supW = Mathf.Clamp01(supportWeight);   // (0 at a tennis contact: both hands stay exactly on the racket where the clip has them)
                float sup = again ? st.support[s] : dt > 0 ? Mathf.MoveTowards(st.support[s], kind == Support ? supW : 0, dt * SupportRate) : kind == Support ? supW : 0;
                if (kind == Support) sup = Mathf.Min(sup, supW);
                st.support[s] = sup;
                // how much of the empty hand's wrist correction is in: eased too, so a hand that lets go of the racket or club (and one that
                // takes it) changes over a few frames, not in one
                float fw = again ? st.free[s] : dt > 0 ? Mathf.MoveTowards(st.free[s], kind == Free ? 1 : kind == Grip ? 0 : st.free[s], dt * SupportRate) : kind == Grip ? 0 : 1;
                st.free[s] = fw;
                if (sup > .001f)
                {
                    float turned = 0, kneeS = Limits[Support][4];
                    for (int it = 0; it < 3; it++)
                    {
                        if (!HandFrame(hand, ip, mp, lp, left, out hf)) break;
                        W = hand.position; fo = (W - lo.position).normalized;
                        float theta = Wrist(fo, hf, Support, out _, out _, out float limit), want = Soft(theta, limit, kneeS);
                        float turn = Mathf.Min(theta - want, SupportMax - turned) * sup; if (turn < .5f) break;
                        var q = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(hf.ax, fo), turn / theta);
                        var grasp = mp.position + hf.pn * GraspDepth; var rot = q * hand.rotation; var to = grasp + q * (W - grasp);
                        HeroPoseSafety.Solve(up, lo, hand, to); hand.rotation = rot; turned += turn;
                    }
                    rep.swivel = turned; S = up.position; E = lo.position; W = hand.position; fo = (W - E).normalized; HandFrame(hand, ip, mp, lp, left, out hf);
                }
                if (!holds)
                {
                    // an empty arm: the elbow's own limit first (the forearm turns back about the hinge), then the hand about the wrist
                    if (rep.elbowBefore > ElbowMax)
                    {
                        var hinge = Vector3.Cross(E - S, W - E);
                        if (hinge.sqrMagnitude > 1e-10f) { lo.rotation = Quaternion.AngleAxis(-(rep.elbowBefore - ElbowMax), hinge.normalized) * lo.rotation; W = hand.position; fo = (W - E).normalized; HandFrame(hand, ip, mp, lp, left, out hf); }
                    }
                    float theta = Wrist(fo, hf, Free, out _, out _, out float limit), want = Soft(theta, limit, knee);
                    if (theta - want > .25f && fw > .001f) hand.rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(hf.ax, fo), (theta - want) / theta * fw) * hand.rotation;
                    st.swivel[s] = dt > 0 ? Mathf.Lerp(st.swivel[s], 0, 1 - Mathf.Exp(-dt * SwivelRate)) : 0; st.turn[s] = 0;
                }
                else if (kind == Support)
                {
                    st.swivel[s] = 0; st.turn[s] = 0;
                    // while the steadying rule eases in, the rest of the bend is taken at the wrist (as the empty hand had it a frame ago)
                    if (sup < .999f && supW > .001f)
                    {
                        float theta = Wrist(fo, hf, Support, out _, out _, out float limit), want = Soft(theta, limit, Limits[Support][4]);
                        if (theta - want > .25f) hand.rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(hf.ax, fo), (theta - want) / theta * (1 - sup) * fw * supW) * hand.rotation;
                    }
                }
                else
                {
                    // a hand on a grip: the elbow goes round the shoulder-wrist line to where the forearm lines up best with the hand
                    var axis = W - S; float d = axis.magnitude; float target = 0; var upAxis = look.transform.up;
                    if (d > 1e-4f)
                    {
                        axis /= d; var c = S + axis * Vector3.Dot(E - S, axis); var e0 = E - c;
                        if (e0.sqrMagnitude > 1e-8f)
                        {
                            float Cost(float phi)
                            {
                                var e = c + Quaternion.AngleAxis(phi, axis) * e0; var f = (W - e).normalized;
                                float th = Wrist(f, hf, Grip, out _, out _, out float lim); float over = Mathf.Max(0, th - lim * knee);
                                float cost = over * over + SwivelCost * phi * phi;
                                if (depth != null && phi != 0) { float dep = Mathf.Max(depth(e, .035f), depth((e + W) * .5f, .03f)) * 100; cost += dep * dep * 60; }
                                // the elbow does not climb: above the clip's own height it costs, and more so near or over the shoulder
                                float lift = (Vector3.Dot(e - E, upAxis) - 0f) * 100; if (lift > 0) { float high = Mathf.Clamp01((Vector3.Dot(e - S, upAxis) + .12f) / .12f); cost += lift * lift * LiftCost * (.25f + high); }
                                return cost;
                            }
                            float best = Cost(0), step = 4;
                            for (float phi = -MaxSwivel; phi <= MaxSwivel + .01f; phi += step) { if (Mathf.Abs(phi) < .01f) continue; float cst = Cost(phi); if (cst < best - 1e-3f) { best = cst; target = phi; } }
                            for (int it = 0; it < 3; it++) { step *= .5f; foreach (float phi in new[] { target - step, target + step }) { if (Mathf.Abs(phi) > MaxSwivel) continue; float cst = Cost(phi); if (cst < best - 1e-3f) { best = cst; target = phi; } } }
                        }
                        float use = again ? st.swivel[s] : dt > 0 ? Mathf.Lerp(st.swivel[s], target, 1 - Mathf.Exp(-dt * SwivelRate)) : target;
                        st.swivel[s] = use;
                        if (Mathf.Abs(use) > .05f) { var keep = hand.rotation; up.rotation = Quaternion.AngleAxis(use, axis) * up.rotation; hand.rotation = keep; }
                    }
                    if (sup <= .001f) rep.swivel = st.swivel[s];
                    // what the elbow could not fix: the hand itself turns (the racket with it), eased in and out, never in a stroke
                    st.turn[s] = again ? st.turn[s] : dt > 0 ? Mathf.MoveTowards(st.turn[s], freedom, dt * TurnRate) : freedom;
                    if (st.turn[s] > .001f)
                    {
                        E = lo.position; fo = (hand.position - E).normalized; HandFrame(hand, ip, mp, lp, left, out hf);
                        float theta = Wrist(fo, hf, Grip, out _, out _, out float limit), want = Soft(theta, limit, knee);
                        float turn = (theta - want) * HandShare * st.turn[s];
                        if (turn > .25f) hand.rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(hf.ax, fo), turn / theta) * hand.rotation;
                    }
                }
                if (HandFrame(hand, ip, mp, lp, left, out hf))
                {
                    fo = (hand.position - lo.position).normalized;
                    rep.wristAfter = Wrist(fo, hf, kind, out rep.flexAfter, out rep.devAfter, out _);
                    rep.elbowAfter = Vector3.Angle(lo.position - up.position, hand.position - lo.position);
                }
                st.report[s] = rep;
            }
        }

        static void Prune()
        {
            var dead = new List<MatchHeroLook>(); foreach (var k in states.Keys) if (!k) dead.Add(k);
            foreach (var k in dead) states.Remove(k);
        }
    }
}
