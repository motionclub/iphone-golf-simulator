using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// EMPTY HANDS 2026-11-12 (Adnan: "they shouldn't be holding their hands like a racket is in their hand UNLESS a racket is in their
    /// hand ... especially after the emote completes"). The emotion emotes were keyed on the tennis READY stance: every clip starts and
    /// ends on READY's fingers, which are the racket grip, and the empty-handed (golf / plaza) versions kept that curl and the racket
    /// wrist. One rule for every sport: a hand closes on an item only while a visible item is in it (the tennis racket, the golf club
    /// at address, the bowling ball); any other hand takes this relaxed hand, the plaza's standing curl (IDLE HANDS 10-24), and a fist
    /// the clip makes stays a fist.
    ///   Golf: GolferView, whenever no club is shown (emotes, walk / run, the idle after an emote, spectators).
    ///   Plaza / menu: HubHeroAnimator, while an emote plays (the stand and the walk relax their own hands).
    ///   Tennis: the racket hand keeps its grip; the free hand already relaxes in HeroGripPolish.ApplyFreeHand.
    /// HERO_EMPTY_HANDS=0 (Editor) switches it off for A/B films.
    public static class HeroHands
    {
        public static bool Enabled
        {
            get
            {
#if UNITY_EDITOR
                return System.Environment.GetEnvironmentVariable("HERO_EMPTY_HANDS") != "0";
#else
                return true;
#endif
            }
        }

        static readonly string[] Fingers = { "Index", "Middle", "Ring", "Little" };
        static readonly string[] Joints = { "Proximal", "Intermediate", "Distal" };
        /// The relaxed curl of a hand in motion: the plaza walk's curl (HER HANDS 2026-11-12, approved on her walk), every finger a soft
        /// curl and the little finger the most (the standing hand's nearly straight index read as pointing in the emotes' films).
        static readonly float[] FingerMore = { .8f, 1f, 1.1f, 1.2f }, FingerFan = { .05f, 0f, -.04f, -.09f };
        const float CurlMcp = 18f, CurlPip = 30f, CurlDip = 15f;
        /// Finger closure (knuckle + middle joint bend, degrees, averaged over the four fingers) of a closed fist.
        const float FistClosure = 175f;

        sealed class Hand
        {
            public Transform hand, arm, ip, mp, lp;
            public readonly Transform[,] finger = new Transform[4, 3];
            public readonly Transform[] thumb = new Transform[3];
            public float restClosure;
            public readonly List<Transform> all = new List<Transform>();
            public Quaternion[] orig, relaxed;
        }
        static readonly Dictionary<MatchHeroLook, Hand[]> hands = new Dictionary<MatchHeroLook, Hand[]>();
        static readonly Dictionary<Transform, Vector3> tipLocal = new Dictionary<Transform, Vector3>();

        static Transform B(MatchHeroLook look, string name) =>
            System.Enum.TryParse<HumanBodyBones>(name, out var id) ? look.Bone(id) : null;

        static Hand Get(MatchHeroLook look, bool left)
        {
            if (!hands.TryGetValue(look, out var pair)) hands[look] = pair = new Hand[2];
            int s = left ? 0 : 1;
            if (pair[s] != null && pair[s].hand) return pair[s];
            string side = left ? "Left" : "Right";
            var h = new Hand
            {
                hand = B(look, side + "Hand"), arm = B(look, side + "LowerArm"),
                ip = B(look, side + "IndexProximal"), mp = B(look, side + "MiddleProximal"), lp = B(look, side + "LittleProximal")
            };
            for (int f = 0; f < 4; f++) for (int j = 0; j < 3; j++) { h.finger[f, j] = B(look, side + Fingers[f] + Joints[j]); if (h.finger[f, j]) h.all.Add(h.finger[f, j]); }
            for (int j = 0; j < 3; j++) { h.thumb[j] = B(look, side + "Thumb" + Joints[j]); if (h.thumb[j]) h.all.Add(h.thumb[j]); }
            h.orig = new Quaternion[h.all.Count]; h.relaxed = new Quaternion[h.all.Count];
            h.restClosure = RestClosure(look, h);
            return pair[s] = h;
        }

        /// The bind pose's own finger closure: the match heroes are bound in READY, so this is the racket grip's curl (fallback 110).
        static float RestClosure(MatchHeroLook look, Hand h)
        {
            var body = look.body; var mesh = body ? body.sharedMesh : null;
            if (!mesh || !h.hand) return 110f;
            var bones = body.bones; var bind = mesh.bindposes;
            Vector3 P(Transform t) { int i = System.Array.IndexOf(bones, t); return i >= 0 && i < bind.Length ? (Vector3)bind[i].inverse.GetColumn(3) : new Vector3(float.NaN, 0, 0); }
            float sum = 0; int n = 0; var hp = P(h.hand);
            for (int f = 0; f < 4; f++)
            {
                if (!h.finger[f, 0] || !h.finger[f, 1] || !h.finger[f, 2]) continue;
                Vector3 p = P(h.finger[f, 0]), m = P(h.finger[f, 1]), t = P(h.finger[f, 2]);
                if (float.IsNaN(hp.x) || float.IsNaN(p.x) || float.IsNaN(m.x) || float.IsNaN(t.x)) continue;
                sum += Vector3.Angle(p - hp, m - p) + Vector3.Angle(m - p, t - m); n++;
            }
            return n > 0 ? sum / n : 110f;
        }

        /// The hand's current finger closure, as RestClosure measures it.
        public static float Closure(MatchHeroLook look, bool left)
        {
            if (!look) return 0; var h = Get(look, left); if (!h.hand) return 0;
            float sum = 0; int n = 0;
            for (int f = 0; f < 4; f++)
            {
                Transform p = h.finger[f, 0], m = h.finger[f, 1], t = h.finger[f, 2]; if (!p || !m || !t) continue;
                sum += Vector3.Angle(p.position - h.hand.position, m.position - p.position) + Vector3.Angle(m.position - p.position, t.position - m.position); n++;
            }
            return n > 0 ? sum / n : 0;
        }

#if UNITY_EDITOR
        static readonly int LogEvery = int.TryParse(System.Environment.GetEnvironmentVariable("HERO_HANDS_LOG"), out var n) ? n : 0;
        static string Digits(Hand h)
        {
            var sb = new System.Text.StringBuilder();
            for (int f = 0; f < 4; f++) { Transform p = h.finger[f, 0], m = h.finger[f, 1], t = h.finger[f, 2]; if (!p || !m || !t) { sb.Append("- "); continue; }
                sb.Append($"{Vector3.Angle(p.position - h.hand.position, m.position - p.position):0}/{Vector3.Angle(m.position - p.position, t.position - m.position):0} "); }
            return sb.ToString();
        }
#endif
        /// Both hands empty (weight 0..1 blends in from the clip's own hand).
        public static void Empty(MatchHeroLook look, float weight)
        {
            if (!look || weight <= .001f || !Enabled) return;
            Empty(look, true, weight); Empty(look, false, weight);
        }

        /// One empty hand: the wrist kept near the forearm's line, then the fingers. The clip's closure above READY's grip curl is read as
        /// a fist being made (READY 0 .. a fist 1); at or under it the hand is relaxed.
        public static void Empty(MatchHeroLook look, bool left, float weight)
        {
            if (!look || weight <= .001f || !Enabled) return;
            var h = Get(look, left); if (!h.hand || !h.ip || !h.mp || !h.lp) return;
            KeepWristInLine(look, h, weight);
            float closure = Closure(look, left);
            float fistness = Mathf.Clamp01((closure - h.restClosure) / Mathf.Max(20f, FistClosure - h.restClosure));
            float fist = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.3f, .75f, fistness));
            const float curl = 1f;
#if UNITY_EDITOR
            if (LogEvery > 0 && Time.frameCount % LogEvery == 0)
                Debug.Log($"[HeroHands] {(look.female ? "F" : "M")} {(left ? "L" : "R")} closure {closure:0} rest {h.restClosure:0} fistness {fistness:0.00} fist {fist:0.00} curl {curl:0.00} digits {Digits(h)}");
#endif
            for (int i = 0; i < h.all.Count; i++) h.orig[i] = h.all[i].localRotation;
            Curl(look, h, left, curl);
            if (fist > .001f)
            {
                for (int i = 0; i < h.all.Count; i++) { h.relaxed[i] = h.all[i].localRotation; h.all[i].localRotation = h.orig[i]; }
                MakeFist(look, h, left, Mathf.Lerp(.7f, 1f, fistness));
                for (int i = 0; i < h.all.Count; i++) h.all[i].localRotation = Quaternion.Slerp(h.relaxed[i], h.all[i].localRotation, fist);
            }
            if (weight < .999f) for (int i = 0; i < h.all.Count; i++) h.all[i].localRotation = Quaternion.Slerp(h.orig[i], h.all[i].localRotation, weight);
        }

        /// The racket wrist the empty clips kept: a free hand stays near the forearm's line (up to 15 degrees as the clip has it, a third of
        /// anything beyond), the plaza walk's rule with more room, since an emote's hand also gestures.
        static void KeepWristInLine(MatchHeroLook look, Hand h, float weight)
        {
            if (!h.arm) return;
            var fo = (h.hand.position - h.arm.position).normalized; var ha = (h.mp.position - h.hand.position).normalized;
            float w = Vector3.Angle(fo, ha); float want = w <= 15f ? w : 15f + (w - 15f) / 3f;
            if (w - want > .5f) h.hand.rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(ha, fo), (w - want) / w * weight) * h.hand.rotation;
        }

        static void Frame(Hand h, bool left, out Vector3 axis, out Vector3 across, out Vector3 palm)
        {
            axis = (h.mp.position - h.hand.position).normalized;
            across = Vector3.ProjectOnPlane(h.ip.position - h.lp.position, axis).normalized;   // toward the thumb side
            palm = left ? Vector3.Cross(across, axis) : Vector3.Cross(axis, across);           // the way the palm faces
        }

        /// The plaza's relaxed hand (HubHeroAnimator.CurlFingers, IDLE HANDS 10-24) at `curl` times its angles.
        static void Curl(MatchHeroLook look, Hand h, bool left, float curl)
        {
            Frame(h, left, out var axis, out var across, out var palm);
            Vector3 Dir(Vector3 from, float deg) => (from * Mathf.Cos(deg * Mathf.Deg2Rad) + palm * Mathf.Sin(deg * Mathf.Deg2Rad)).normalized;
            for (int k = 0; k < 4; k++)
            {
                Transform p = h.finger[k, 0], i = h.finger[k, 1], d = h.finger[k, 2]; if (!p || !i || !d) continue;
                var start = (axis + across * FingerFan[k]).normalized; float more = FingerMore[k];
                float a1 = CurlMcp * more * curl, a2 = a1 + CurlPip * more * curl, a3 = a2 + CurlDip * more * curl;
                AimBone(p, i, Dir(start, a1)); AimBone(i, d, Dir(start, a2)); AimTip(look, d, Dir(start, a3));
            }
            Transform tp = h.thumb[0], ti = h.thumb[1], td = h.thumb[2];
            if (tp && ti && td)
            {
                AimBone(tp, ti, (axis * .97f + across * .40f + palm * .32f).normalized); AimBone(ti, td, (axis * .97f + across * .34f + palm * .40f).normalized);
                AimTip(look, td, (axis * .97f + across * .28f + palm * .46f).normalized);
            }
        }

        /// The plaza's fist (HubHeroAnimator.Fist): `amount` 1 = closed, .7 = loose; the thumb across the index and middle fingers.
        static void MakeFist(MatchHeroLook look, Hand h, bool left, float amount)
        {
            Frame(h, left, out var axis, out var across, out var palm);
            Vector3 Dir(Vector3 from, float deg) => (from * Mathf.Cos(deg * Mathf.Deg2Rad) + palm * Mathf.Sin(deg * Mathf.Deg2Rad)).normalized;
            for (int k = 0; k < 4; k++)
            {
                Transform p = h.finger[k, 0], i = h.finger[k, 1], d = h.finger[k, 2]; if (!p || !i || !d) continue;
                var start = (axis + across * FingerFan[k] * .5f).normalized;
                float a1 = (70 + 6 * k) * amount, a2 = a1 + 95 * amount, a3 = a2 + 55 * amount;
                AimBone(p, i, Dir(start, a1)); AimBone(i, d, Dir(start, a2)); AimTip(look, d, Dir(start, a3));
            }
            Transform tp = h.thumb[0], ti = h.thumb[1], td = h.thumb[2];
            if (tp && ti && td)
            {
                AimBone(tp, ti, Vector3.Lerp((axis * .97f + across * .40f + palm * .32f).normalized, (axis * .55f + palm * .55f + across * .25f).normalized, amount));
                AimBone(ti, td, Vector3.Lerp((axis * .97f + across * .34f + palm * .40f).normalized, (palm * .55f - across * .65f + axis * .3f).normalized, amount));
                AimTip(look, td, Vector3.Lerp((axis * .97f + across * .28f + palm * .46f).normalized, (palm * .35f - across * .9f).normalized, amount));
            }
        }

        /// The distal bone's tip in its own space: the bind-pose vertex weighted to it that lies farthest from its head.
        static Vector3 TipLocal(MatchHeroLook look, Transform bone)
        {
            if (tipLocal.TryGetValue(bone, out var cached)) return cached;
            Vector3 result = Vector3.zero;
            var body = look.body; var mesh = body ? body.sharedMesh : null;
            if (mesh && mesh.isReadable)
            {
                int idx = System.Array.IndexOf(body.bones, bone);
                if (idx >= 0)
                {
                    var bp = mesh.bindposes; var v = mesh.vertices; var w = mesh.boneWeights; Vector3 head = bp[idx].inverse.GetColumn(3); float best = -1; Vector3 far = head;
                    for (int k = 0; k < v.Length; k++)
                    {
                        float amt = (w[k].boneIndex0 == idx ? w[k].weight0 : 0) + (w[k].boneIndex1 == idx ? w[k].weight1 : 0) + (w[k].boneIndex2 == idx ? w[k].weight2 : 0) + (w[k].boneIndex3 == idx ? w[k].weight3 : 0);
                        if (amt < .5f) continue; float d = (v[k] - head).sqrMagnitude; if (d > best) { best = d; far = v[k]; }
                    }
                    result = bp[idx].MultiplyPoint3x4(far);
                }
            }
            tipLocal[bone] = result; return result;
        }
        static void AimTip(MatchHeroLook look, Transform bone, Vector3 want)
        {
            var local = TipLocal(look, bone); if (local.sqrMagnitude < 1e-10f) return;
            var have = bone.TransformPoint(local) - bone.position; if (have.sqrMagnitude < 1e-10f) return;
            bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
        }
        static void AimBone(Transform bone, Transform child, Vector3 want)
        {
            if (!bone || !child) return;
            var have = child.position - bone.position; if (have.sqrMagnitude < 1e-8f) return;
            bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
        }
    }
}
