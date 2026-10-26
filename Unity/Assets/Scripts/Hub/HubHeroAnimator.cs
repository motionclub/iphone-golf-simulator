using System.Collections.Generic;
using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace GolfArcade.Hub
{
    /// Plays the match hero's own clips in the plaza: Idle, Walk and RunForward by ground speed (the planted foot moves at the hero's
    /// speed: clip rate = speed / the clip's planted-foot speed, the numbers ServeAndFeetWire measured into HeroTennisDriver), and
    /// any emote or intro clip as a one-shot. The prefab's HeroTennisDriver is left unbuilt: it is a puppet of a TennisActor and
    /// the plaza has none. The garment correctives the driver runs after each pose run here too, so the kit deforms the same way.
    [DefaultExecutionOrder(900)]
    public sealed class HubHeroAnimator : MonoBehaviour
    {
        public MatchHeroLook look;
        public float walkClipSpeed = 1.25f, runClipSpeed = 3.25f;
        /// Clips run on game time instead of unscaled time (bowling: its proof films step a fixed capture clock;
        /// the plaza keeps unscaled time because a match loading behind it pauses Time.timeScale).
        public bool GameTime;
        /// Planted-foot speeds of the standard Walk / Run cycles at 1x (work/emote-standard/scripts/gait.py: 2 x 0.64 m per 1.067 s, 2 x 1.167 m per 0.667 s).
        public const float StandardWalkSpeed = 1.2f, StandardRunSpeed = 3.5f;
        /// Ground speeds where the legs hand over from the walk to the run (both clips at their matched rate in between).
        public const float WalkTop = 1.75f, RunFrom = 2.55f;

        enum Slot { Idle, Walk, Run, Action }
        PlayableGraph graph; AnimationMixerPlayable mixer;
        AnimationClipPlayable idle, walk, run, action;
        float idleLen, walkLen, runLen, actionLen; double idleT, walkT, runT, actionT;
        float wIdle = 1, wWalk, wRun, wAction, actionFade;
        readonly Dictionary<string, AnimationClip> clips = new Dictionary<string, AnimationClip>();
        string playing; bool actionLoops;
        Transform[] toes = new Transform[2]; float toeRest; readonly Vector3[] lastToe = new Vector3[2];
        HeroPoseSafety safety;

        public float Speed { get; private set; }
        /// Diagnostics: the leg blend actually applied this frame (idle, walk, run, action).
        public Vector4 Weights => new Vector4(wIdle, wWalk, wRun, actionFade);
        public string Playing => playing;
        public bool ActionActive => playing != null;
        /// Diagnostics for the FEET gate: the fastest planted toe this frame (m/s), 0 when no toe is planted.
        public float PlantedToeSpeed { get; private set; }
        public IEnumerable<string> Emotes => clips.Keys;

        public static HubHeroAnimator Attach(GameObject hero)
        {
            var look = hero.GetComponent<MatchHeroLook>();
            var driver = hero.GetComponent<HeroTennisDriver>();
            if (!look || !look.animator) return null;
            var a = hero.AddComponent<HubHeroAnimator>(); a.look = look;
            // IDLE HANDS 10-24: the plaza hero holds nothing (the racket's renderers are hidden, but its grip transform still rides in the right
            // hand), so the match grip pass must not run here: it wrapped the right fingers round the invisible handle (the male claw, the
            // female thumb-index pinch) and re-curled the left from the cupped bind pose (her hook), after this stand had relaxed them.
            var grip = hero.GetComponent<HeroGripPolish>(); if (grip) grip.enabled = false;
            a.CaptureRest();   // the prefab's bind pose, before any clip has posed it
            AnimationClip idleClip = null, walkClip = null, runClip = null;
            if (driver)
            {
                driver.enabled = false;
                driver.ResolvePerformanceClips();
                a.walkClipSpeed = driver.walkClipSpeed; a.runClipSpeed = driver.runClipSpeed;
                foreach (var s in driver.slots)
                {
                    if (!s.clip) continue;
                    switch (s.id)
                    {
                        case HeroTennisDriver.Clip.Idle: idleClip = s.clip; break;
                        case HeroTennisDriver.Clip.Ready: if (!idleClip) idleClip = s.clip; break;
                        case HeroTennisDriver.Clip.Walk: walkClip = s.clip; break;
                        case HeroTennisDriver.Clip.RunForward: runClip = s.clip; break;
                        default:
                            if (HeroTennisDriver.IsEmote(s.id) || s.id == HeroTennisDriver.Clip.CelebratePoint || s.id == HeroTennisDriver.Clip.MatchWin)
                                a.clips[s.id.ToString()] = s.clip;
                            break;
                    }
                }
            }
            // EMOTE STANDARD: the plaza walks / runs on the standard empty-handed locomotion cycles and plays the empty-handed
            // versions of the emotion set (the plaza hero carries no racket); Resources/HeroMoves/<Sex>/ (Walk, Run, Emote_*).
            foreach (var c in Resources.LoadAll<AnimationClip>("HeroMoves/" + (look.female ? "Female" : "Male")))
            {
                if (c.name.StartsWith("__preview__")) continue;
                if (c.name == "Walk") { walkClip = c; a.walkClipSpeed = StandardWalkSpeed; }
                else if (c.name == "Run") { runClip = c; a.runClipSpeed = StandardRunSpeed; }
                else if (c.name.StartsWith("Emote_")) a.clips[c.name.Replace("_", "")] = c;
                else if (c.name.StartsWith("Bowl_")) a.clips[c.name.Replace("_", "")] = c;   // BOWLING ANIMATION: authored bowling set (BowlingClips)
            }
            a.Build(idleClip, walkClip, runClip);
            return a;
        }

        // ---- the plaza stance: the clips' idle is the tennis ready crouch, so standing still blends to a relaxed pose built from the
        // hero's own bind pose (straight legs, upright spine), with the arms hanging and the elbows soft, plus breathing and a slow
        // weight shift. Only the idle share of the blend is relaxed, so walking and running stay exactly as authored.
        readonly List<(Transform bone, Quaternion rot, Vector3 pos)> rest = new List<(Transform, Quaternion, Vector3)>();
        readonly Dictionary<Transform, Quaternion> relaxed = new Dictionary<Transform, Quaternion>();
        Transform hipsBone, spineBone, chestBone, headBone; Vector3 hipsRest, hipsRelaxed, hipsSeated;
        readonly Dictionary<Transform, Quaternion> seated = new Dictionary<Transform, Quaternion>();
        /// Sit on a bench (a bay): blends to the seated pose in about half a second. The hips sit `SeatHeight` above the feet.
        public bool Seated;
        public float SeatWeight { get; private set; }
        public const float SeatHeight = .56f;
        public float RelaxWeight { get; private set; }
        void CaptureRest()
        {
            var seen = new HashSet<Transform>();
            for (var b = HumanBodyBones.Hips; b < HumanBodyBones.LastBone; b++)
            {
                var t = look.Bone(b); if (!t || !seen.Add(t)) continue;
                rest.Add((t, t.localRotation, t.localPosition)); relaxed[t] = t.localRotation;
            }
            hipsBone = look.Bone(HumanBodyBones.Hips); spineBone = look.Bone(HumanBodyBones.Spine); chestBone = look.Bone(HumanBodyBones.Chest) ?? spineBone; headBone = look.Bone(HumanBodyBones.Head);
            if (hipsBone) hipsRest = hipsBone.localPosition;
            BuildRelaxedPose();
            foreach (var r in rest) relaxed[r.bone] = r.bone.localRotation;
            if (hipsBone) hipsRelaxed = hipsBone.localPosition;
            BuildSeatedPose();
            foreach (var r in rest) seated[r.bone] = r.bone.localRotation;
            if (hipsBone) hipsSeated = hipsBone.localPosition;
            foreach (var r in rest) { r.bone.localRotation = r.rot; r.bone.localPosition = r.pos; }
        }
        /// Poses the skeleton (from the prefab's ready stance) into a relaxed stand, bone by bone in world space: spine upright, head
        /// level, legs under the hips with flat feet (the hips drop or rise so the ankles stay at their height), arms hanging with soft elbows.
        void BuildRelaxedPose()
        {
            var root = transform; Vector3 up = root.up, fwd = root.forward, right = root.right;
            Transform B(HumanBodyBones b) => look.Bone(b);
            void Aim(Transform bone, Transform child, Vector3 want)
            {
                if (!bone || !child) return;
                var have = child.position - bone.position; if (have.sqrMagnitude < 1e-8f) return;
                bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
            }
            var lAnkle = B(HumanBodyBones.LeftFoot); var rAnkle = B(HumanBodyBones.RightFoot);
            float ankleY = lAnkle && rAnkle ? Mathf.Min(lAnkle.position.y, rAnkle.position.y) : 0;
            // spine chain upright, a touch of forward lean in the chest
            Aim(B(HumanBodyBones.Spine), B(HumanBodyBones.Chest) ?? B(HumanBodyBones.Neck), up);
            Aim(B(HumanBodyBones.Chest), B(HumanBodyBones.UpperChest) ?? B(HumanBodyBones.Neck), up + fwd * .04f);
            if (B(HumanBodyBones.UpperChest)) Aim(B(HumanBodyBones.UpperChest), B(HumanBodyBones.Neck), up + fwd * .04f);
            Aim(B(HumanBodyBones.Neck), B(HumanBodyBones.Head), up + fwd * .1f);
            var head = B(HumanBodyBones.Head);
            if (head) { var f = Vector3.ProjectOnPlane(head.forward, up); if (f.sqrMagnitude > 1e-6f) head.rotation = Quaternion.FromToRotation(f.normalized, fwd) * head.rotation; head.rotation = Quaternion.AngleAxis(9f, right) * head.rotation; }
            // legs: thigh and shin straight down (feet a little apart), then the feet flat and pointing forward, slightly out
            foreach (var (ul, ll, ft, toe, side) in new[] { (HumanBodyBones.LeftUpperLeg, HumanBodyBones.LeftLowerLeg, HumanBodyBones.LeftFoot, HumanBodyBones.LeftToes, -1f), (HumanBodyBones.RightUpperLeg, HumanBodyBones.RightLowerLeg, HumanBodyBones.RightFoot, HumanBodyBones.RightToes, 1f) })
            {
                Aim(B(ul), B(ll), -up + right * side * .04f + fwd * .015f);
                Aim(B(ll), B(ft), -up + fwd * -.02f);
                var foot = B(ft); var t = B(toe);
                if (foot && t) { var d = t.position - foot.position; var flat = Vector3.ProjectOnPlane(fwd + right * side * .12f, up).normalized * d.magnitude; flat.y = d.y; Aim(foot, t, flat); }
            }
            // keep the ankles where they were (the straight legs are longer than the crouch)
            float nowY = lAnkle && rAnkle ? Mathf.Min(lAnkle.position.y, rAnkle.position.y) : 0;
            if (hipsBone) hipsBone.position += up * (ankleY - nowY);
            // arms hang: upper arm down, just clear of the torso, forearm a touch forward and IN toward the thigh, hand in line
            // (MENU HERO 10-19, Adnan "arms stuck out": was upper .2 out, forearm .1 out + .3 forward, which flared the hands away from the body;
            // Switch Sports / Fall Guys stand with the hands by the thighs, work/menu-hero/REFERENCES.md)
            // IDLE HANDS 10-24 (Adnan "they act as if they are holding something"): the forearms hung .16 forward, which put the hands in
            // front of the thighs as if carrying something; they now hang almost straight, so the hands sit beside the thighs (work/idle-hands-20261024)
            foreach (var (ua, la, hd, mid, side) in new[] { (HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand, HumanBodyBones.LeftMiddleProximal, -1f), (HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand, HumanBodyBones.RightMiddleProximal, 1f) })
            {
                Aim(B(ua), B(la), -up + right * side * .13f + fwd * UpperArmForward);
                Aim(B(la), B(hd), -up - right * side * .02f + fwd * ForearmForward);
                // a straight wrist (both heroes; 10-19 female only, the male's bent wrist read as a hook)
                if (B(hd) && B(la)) Aim(B(hd), B(mid), (B(hd).position - B(la).position).normalized);
                // palm toward the thigh: roll the hand so its knuckle line (little -> index) points forward. The thumb's root was used before,
                // but it sits on the palm side of the wrist, so the roll left the palm turned back.
                var hand = B(hd); var m = B(mid);
                var ip = B(side < 0 ? HumanBodyBones.LeftIndexProximal : HumanBodyBones.RightIndexProximal); var lp = B(side < 0 ? HumanBodyBones.LeftLittleProximal : HumanBodyBones.RightLittleProximal);
                if (hand && m && ip && lp)
                {
                    var axis = (m.position - hand.position).normalized;
                    var t0 = Vector3.ProjectOnPlane(ip.position - lp.position, axis); var t1 = Vector3.ProjectOnPlane(fwd - right * side * PalmTurnIn, axis);
                    if (t0.sqrMagnitude > 1e-8f && t1.sqrMagnitude > 1e-8f) hand.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(t0, t1, axis), axis) * hand.rotation;
                }
                RelaxFingers(side < 0);
            }
        }
        /// The hanging arm (IDLE HANDS 10-24): forward share of the upper arm and forearm aims, and how far the knuckle line turns in from
        /// straight forward (palm a little toward the back of the thigh, as a relaxed arm hangs).
        const float UpperArmForward = -.1f, ForearmForward = .05f, PalmTurnIn = .12f;

        /// A standing hand (10-19, Adnan "her hands are all over the place"): the bind pose keeps the racket-grip curl of the ready stance, so
        /// the relaxed hands showed fingers bunched into a claw / a pinched O (worse on the smaller female hand). The fingers instead fall
        /// together in a soft curl toward the palm (each joint a little more than the one before, the little finger the most) with the thumb
        /// resting along the side of the index finger.
        /// IDLE HANDS 10-24 (both heroes now): the curl is built in the hand's own frame (its axis to the middle knuckle, the knuckle line,
        /// the palm normal from the hand's handedness) rather than from world down / forward / toward the thigh, which no longer matched
        /// the hand once the wrist followed the forearm: the fingers curled partly sideways (the female's cupped hook) and the index
        /// met the thumb (her pinch).
        void RelaxFingers(bool left)
        {
            string side = left ? "Left" : "Right";
            Transform Bn(string n) => look.Bone((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), side + n));
            var hand = Bn("Hand"); var ip = Bn("IndexProximal"); var mp = Bn("MiddleProximal"); var lp = Bn("LittleProximal");
            if (!hand || !ip || !mp || !lp) return;
            var axis = (mp.position - hand.position).normalized;
            var across = Vector3.ProjectOnPlane(ip.position - lp.position, axis).normalized;   // toward the thumb side
            var palm = left ? Vector3.Cross(across, axis) : Vector3.Cross(axis, across);       // the way the palm faces
            Vector3 Dir(Vector3 from, float deg) => (from * Mathf.Cos(deg * Mathf.Deg2Rad) + palm * Mathf.Sin(deg * Mathf.Deg2Rad)).normalized;
            for (int k = 0; k < Fingers.Length; k++)
            {
                var p = Bn(Fingers[k] + "Proximal"); var i = Bn(Fingers[k] + "Intermediate"); var d = Bn(Fingers[k] + "Distal");
                if (!p || !i || !d) continue;
                // loosely together: a small fan about the middle finger, then each joint a little more than the one before
                var start = (axis + across * FingerFan[k]).normalized; float more = FingerMore[k];
                float a1 = CurlMcp * more, a2 = a1 + CurlPip * more, a3 = a2 + CurlDip * more;
                AimBone(p, i, Dir(start, a1)); AimBone(i, d, Dir(start, a2));
                AimTip(d, Dir(start, a3));   // the tip has no child bone: its real tip (bind-pose farthest vertex) is aimed, so the rest pose's own fingertip hook does not add to the curl
            }
            var tp = Bn("ThumbProximal"); var ti = Bn("ThumbIntermediate"); var td = Bn("ThumbDistal");
            if (tp && ti && td)
            {
                // 10-19 r4 (Adnan: "the thumb shouldn't cross the palm, it should align like the rest of the fingers, when people walk or run their thumbs are out"):
                // IDLE HANDS 10-24: the thumb's root sits on the palm side of the index knuckle, so the thumb stays on the palm side all the way down
                // (beside the near-straight index, a little out from it): a thumb aimed down the hand's middle crossed the curled index and met its
                // tip, an "O" seen from the front (a pinch)
                AimBone(tp, ti, (axis * .97f + across * .40f + palm * .32f).normalized); AimBone(ti, td, (axis * .97f + across * .34f + palm * .40f).normalized);
                AimTip(td, (axis * .97f + across * .28f + palm * .46f).normalized);
            }
        }
        static readonly string[] Fingers = { "Index", "Middle", "Ring", "Little" };
        /// IDLE HANDS 10-24: the relaxed curl (degrees per joint, scaled per finger: the little finger curls the most) and the fan toward the thumb side.
        static readonly float[] FingerMore = { .35f, .8f, 1.05f, 1.2f }, FingerFan = { .05f, 0f, -.04f, -.09f };
        const float CurlMcp = 10f, CurlPip = 20f, CurlDip = 12f;
        readonly Dictionary<Transform, Vector3> tipLocal = new Dictionary<Transform, Vector3>();
        /// The distal bone's tip in its own space: the bind-pose vertex weighted to it that lies farthest from its head.
        Vector3 TipLocal(Transform bone)
        {
            if (tipLocal.TryGetValue(bone, out var cached)) return cached;
            Vector3 result = Vector3.zero;
            var body = look.body; var mesh = body ? body.sharedMesh : null;
            if (mesh && mesh.isReadable)
            {
                var pal = body.bones; int idx = System.Array.IndexOf(pal, bone);
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
        void AimTip(Transform bone, Vector3 want)
        {
            var local = TipLocal(bone); if (local.sqrMagnitude < 1e-10f) return;
            var have = bone.TransformPoint(local) - bone.position; if (have.sqrMagnitude < 1e-10f) return;
            bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
        }
        static void AimBone(Transform bone, Transform child, Vector3 want)
        {
            if (!bone || !child) return;
            var have = child.position - bone.position; if (have.sqrMagnitude < 1e-8f) return;
            bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
        }

        /// From the relaxed stand: hips down onto a bench, thighs forward, shins down, a slight lean, forearms resting on the thighs.
        void BuildSeatedPose()
        {
            var root = transform; Vector3 up = root.up, fwd = root.forward, right = root.right;
            Transform B(HumanBodyBones b) => look.Bone(b);
            void Aim(Transform bone, Transform child, Vector3 want)
            {
                if (!bone || !child) return;
                var have = child.position - bone.position; if (have.sqrMagnitude < 1e-8f) return;
                bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
            }
            var lHip = B(HumanBodyBones.LeftUpperLeg);
            if (hipsBone && lHip) hipsBone.position += up * (root.position.y + SeatHeight - lHip.position.y) - fwd * .02f;
            Aim(B(HumanBodyBones.Spine), B(HumanBodyBones.Chest) ?? B(HumanBodyBones.Neck), up + fwd * .16f);
            foreach (var (ul, ll, ft, toe, side) in new[] { (HumanBodyBones.LeftUpperLeg, HumanBodyBones.LeftLowerLeg, HumanBodyBones.LeftFoot, HumanBodyBones.LeftToes, -1f), (HumanBodyBones.RightUpperLeg, HumanBodyBones.RightLowerLeg, HumanBodyBones.RightFoot, HumanBodyBones.RightToes, 1f) })
            {
                Aim(B(ul), B(ll), fwd - up * .08f + right * side * .14f);
                Aim(B(ll), B(ft), -up + fwd * .1f);
                var foot = B(ft); var t = B(toe);
                if (foot && t) { var d = t.position - foot.position; var flat = Vector3.ProjectOnPlane(fwd + right * side * .1f, up).normalized * d.magnitude; flat.y = d.y; Aim(foot, t, flat); }
            }
            foreach (var (ua, la, hd, mid, side) in new[] { (HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand, HumanBodyBones.LeftMiddleProximal, -1f), (HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand, HumanBodyBones.RightMiddleProximal, 1f) })
            {
                Aim(B(ua), B(la), -up + fwd * .45f + right * side * .14f);
                Aim(B(la), B(hd), fwd - up * .35f - right * side * .08f);
                Aim(B(hd), B(mid), fwd - up * .3f);
            }
        }

        /// The sway frequencies of the stand (Hz): breathing, the slow weight shift, the head turn.
        float breatheHz = .23f, shiftHz = .07f, headHz = .9f / (2 * Mathf.PI);

        /// MENU HERO (work/menu-hero): the clip the stand is built on (the plaza's Idle / Ready).
        public AnimationClip IdleClip { get; private set; }
        /// MENU HERO: the whole relaxed stand (weight 1) on the pose the hierarchy is in now, for the phone menu's lobby export
        /// (MatchHeroLockerExport bakes it into its "relaxed" clip, so the phone stands exactly as the plaza does). Each sway is
        /// rounded to whole cycles of `loop` seconds so the baked clip loops without a seam.
        public void PoseRelaxed(float time, float loop)
        {
            float b = breatheHz, s = shiftHz, h = headHz;
            float Round(float hz) => Mathf.Max(1, Mathf.Round(hz * loop)) / loop;
            breatheHz = Round(b); shiftHz = Round(s); headHz = Round(h);
            Relax(1, time);
            breatheHz = b; shiftHz = s; headHz = h;
        }

        static bool IsFinger(string n) => n.Contains("Thumb") || n.Contains("Index") || n.Contains("Middle") || n.Contains("Ring") || n.Contains("Little");
        /// The fingers take the soft relaxed pose at this weight whatever the legs do (standing, walking, running): the plaza hero holds nothing, so
        /// the clips' racket-grip curl must not show (female since 10-19, both heroes since IDLE HANDS 10-24). Emotes and intros (actionFade) keep their own hands.
        float FingerWeight(float w) => Mathf.Max(w, 1 - actionFade);
        void Relax(float w, float time)
        {
            float wf = FingerWeight(w);
            RelaxWeight = w; if (w <= .001f && wf <= .001f) return;
            foreach (var r in rest)
            {
                float k = IsFinger(r.bone.name) ? wf : w; if (k <= .001f) continue;
                r.bone.localRotation = Quaternion.Slerp(r.bone.localRotation, relaxed[r.bone], k);
                if (r.bone == hipsBone) r.bone.localPosition = Vector3.Lerp(r.bone.localPosition, hipsRelaxed, w);
            }
            // breathing and a slow weight shift (in the hero's own frame, small)
            float breathe = Mathf.Sin(time * Mathf.PI * 2 * breatheHz), shift = Mathf.Sin(time * Mathf.PI * 2 * shiftHz);
            if (chestBone) chestBone.rotation = Quaternion.AngleAxis(breathe * 1.1f * w, transform.right) * chestBone.rotation;
            if (spineBone) spineBone.rotation = Quaternion.AngleAxis(shift * 1.6f * w, transform.forward) * spineBone.rotation;
            if (hipsBone) { hipsBone.position += transform.right * shift * .012f * w; hipsBone.rotation = Quaternion.AngleAxis(-shift * 1.4f * w, transform.forward) * hipsBone.rotation; }
            if (headBone) headBone.rotation = Quaternion.AngleAxis(Mathf.Sin(time * Mathf.PI * 2 * headHz) * 3f * w, Vector3.up) * headBone.rotation;
        }
        float relaxTime;

        void Build(AnimationClip idleClip, AnimationClip walkClip, AnimationClip runClip)
        {
            IdleClip = idleClip;
            look.animator.applyRootMotion = false;
            graph = PlayableGraph.Create(name + " plaza");
            graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
            mixer = AnimationMixerPlayable.Create(graph, 4);
            AnimationClipPlayable Make(AnimationClip c, Slot slot, out float len)
            {
                len = c ? Mathf.Max(.01f, c.length) : 1;
                if (!c) return default;
                var p = AnimationClipPlayable.Create(graph, c); p.SetApplyFootIK(false); p.SetSpeed(0);
                graph.Connect(p, 0, mixer, (int)slot); return p;
            }
            idle = Make(idleClip, Slot.Idle, out idleLen);
            walk = Make(walkClip ? walkClip : idleClip, Slot.Walk, out walkLen);
            run = Make(runClip ? runClip : walkClip, Slot.Run, out runLen);
            AnimationPlayableOutput.Create(graph, "Hub hero", look.animator).SetSourcePlayable(mixer);
            mixer.SetInputWeight(0, 1);
            toes[0] = look.Bone(HumanBodyBones.LeftToes) ?? look.Bone(HumanBodyBones.LeftFoot);
            toes[1] = look.Bone(HumanBodyBones.RightToes) ?? look.Bone(HumanBodyBones.RightFoot);
            // rest height of a planted toe: evaluate the idle pose once
            graph.Evaluate(0);
            toeRest = Mathf.Min(Local(toes[0]).y, Local(toes[1]).y);
            foreach (var smr in look.GetComponentsInChildren<SkinnedMeshRenderer>(true)) { smr.updateWhenOffscreen = true; smr.quality = SkinQuality.Bone4; }
        }
        Vector3 Local(Transform t) => t ? transform.InverseTransformPoint(t.position) : Vector3.zero;

        /// Play an emote / intro by clip id name ("EmoteSpike", "IntroWave"...). Moving cancels it.
        public bool Play(string clipId, bool loop = false, float startAt = 0)
        {
            if (!graph.IsValid() || !clips.TryGetValue(clipId, out var clip)) return false;
            // BOWLING ANIMATION: a clip started while another action is in full effect keeps the blend (clips that branch from each other
            // are identical up to the branch, so switching mid-clip at `startAt` must not dip back to the legs)
            float keepFade = actionFade;   // (also while an action is still fading out)
            if (action.IsValid()) { graph.Disconnect(mixer, (int)Slot.Action); action.Destroy(); }
            action = AnimationClipPlayable.Create(graph, clip); action.SetApplyFootIK(false); action.SetSpeed(0);
            graph.Connect(action, 0, mixer, (int)Slot.Action);
            actionLen = Mathf.Max(.05f, clip.length); actionT = Mathf.Clamp(startAt, 0, actionLen); playing = clipId; actionLoops = loop; actionFade = keepFade;
            return true;
        }
        /// True when this hero has the clip with that id ("EmoteSpike", "BowlShot"...).
        public bool Has(string clipId) => clips.ContainsKey(clipId);
        /// Seconds into the playing action (0 when none).
        public float ActionTime => playing != null ? (float)actionT : 0;
        public void Stop() { playing = null; }

        /// Called by HubPlayer every frame after it moved the hero; the pose is evaluated in LateUpdate, after the Animator's own pass.
        public void Tick(float speed, float dt) { Speed = speed; }

        void LateUpdate()
        {
            float dt = GameTime ? Time.deltaTime : Time.unscaledDeltaTime, speed = Speed;
            if (!graph.IsValid() || dt <= 0) return;
            if (playing != null && speed > .4f) playing = null;   // walking away ends an emote
            // the leg blend by speed: idle -> walk (matched) -> run (matched)
            float tWalk = Mathf.InverseLerp(.05f, .35f, speed), tRun = Mathf.InverseLerp(WalkTop, RunFrom, speed);
            float targetIdle = 1 - tWalk, targetWalk = tWalk * (1 - tRun), targetRun = tWalk * tRun;
            float k = 1 - Mathf.Exp(-dt / .06f);
            wIdle = Mathf.Lerp(wIdle, targetIdle, k); wWalk = Mathf.Lerp(wWalk, targetWalk, k); wRun = Mathf.Lerp(wRun, targetRun, k);
            // clip clocks: idle at 1x; walk and run at the rate that keeps the planted foot still at this speed
            idleT = (idleT + dt) % idleLen;
            float walkRate = Mathf.Clamp(speed / walkClipSpeed, .45f, 1.6f), runRate = Mathf.Clamp(speed / runClipSpeed, .6f, 1.45f);
            walkT = (walkT + dt * walkRate) % walkLen;
            runT = (runT + dt * runRate) % runLen;
            // one-shot action on top (full body: emotes own the feet)
            actionFade = Mathf.MoveTowards(actionFade, playing != null ? 1 : 0, dt / (playing != null ? .15f : .2f));
            if (playing != null)
            {
                actionT += dt;
                if (actionT >= actionLen) { if (actionLoops) actionT %= actionLen; else { actionT = actionLen; playing = null; } }
            }
            float sum = Mathf.Max(1e-4f, wIdle + wWalk + wRun), legs = 1 - actionFade;
            if (idle.IsValid()) { idle.SetTime(idleT); mixer.SetInputWeight((int)Slot.Idle, legs * wIdle / sum); }
            if (walk.IsValid()) { walk.SetTime(walkT); mixer.SetInputWeight((int)Slot.Walk, legs * wWalk / sum); }
            if (run.IsValid()) { run.SetTime(runT); mixer.SetInputWeight((int)Slot.Run, legs * wRun / sum); }
            if (action.IsValid()) { action.SetTime(actionT); mixer.SetInputWeight((int)Slot.Action, actionFade); }
            graph.Evaluate(0);
            relaxTime += dt;
            Relax((1 - actionFade) * wIdle / sum, relaxTime);
            SeatWeight = Mathf.MoveTowards(SeatWeight, Seated ? 1 : 0, dt / .45f);
            if (SeatWeight > .001f)
            {
                float sit = Mathf.SmoothStep(0, 1, SeatWeight);
                foreach (var r in rest)
                {
                    r.bone.localRotation = Quaternion.Slerp(r.bone.localRotation, seated[r.bone], sit);
                    if (r.bone == hipsBone) r.bone.localPosition = Vector3.Lerp(r.bone.localPosition, hipsSeated, sit);
                }
            }
            // BOWLING ANIMATION: the authored bowling clips carry their own foot plants and the slide (the hips travel inside the clip), so the pin stays out of them
            bool bowlClip = playing != null && playing.StartsWith("Bowl");
            if (bowlClip) { var lp = transform.localPosition; transform.localPosition = new Vector3(0, lp.y, 0); }
            else if (SeatWeight < .001f) PinPlantedFoot(dt); else { var lp = transform.localPosition; transform.localPosition = Vector3.MoveTowards(lp, new Vector3(0, lp.y, 0), dt); }
            // HAND CLEARANCE (work/hand-clearance): hands and forearms out of the body and the clothes, as in tennis and golf
            if (safety == null) { safety = new HeroPoseSafety(look); safety.UseGraph(graph); }   // + the baked corrections of the clips playing
            // MENU HERO: standing still, the relaxed stand replaces the Idle clip's arms, so the Idle clip's baked racket-arm correction must not
            // ride on it (it pushed the right arm out, 10-19); the residual solve still keeps the hands out of the body and the kit
            bool keepTracks = HeroClearanceTracks.Enabled; if (RelaxWeight > .5f) HeroClearanceTracks.Enabled = false;
            try { safety.Apply(false); } finally { HeroClearanceTracks.Enabled = keepTracks; }
            // the same garment passes the match driver runs after every pose
            look.body?.GetComponent<HeroArmSkinning>()?.Apply();
            look.GetComponent<HeroGarmentPoseCorrectives>()?.Apply();
            look.GetComponent<TailoredPoloDeformation>()?.Apply();
            MeasureToes(dt);
        }

        // ---- planted-foot pin: turning on the spot or speeding up from a stand rotates / pushes the body about its root, which drags
        // a planted foot across the floor. While a toe is down, the model is shifted under the capsule so that toe stays where it
        // landed; the shift drains back slower than the slide threshold (and fast while no foot is down), never more than 0.3 m.
        readonly Vector3[] anchor = new Vector3[2]; readonly bool[] pinned = new bool[2];
        public const float PinDrain = .10f, PinDrainAirborne = .9f, PinMax = .3f;
        void PinPlantedFoot(float dt)
        {
            int foot = -1; float lowest = .015f;
            for (int f = 0; f < 2; f++)
            {
                if (!toes[f]) continue;
                float h = Local(toes[f]).y - toeRest;
                if (h < .015f) { if (!pinned[f]) { pinned[f] = true; anchor[f] = toes[f].position; } if (h < lowest) { lowest = h; foot = f; } }
                else pinned[f] = false;
            }
            var offset = transform.localPosition; offset.y = 0;
            if (foot >= 0)
            {
                var err = toes[foot].position - anchor[foot]; err.y = 0;
                transform.position -= err;
                offset = transform.localPosition; offset.y = 0;
            }
            // drain the shift back under the capsule
            float drain = (foot >= 0 ? PinDrain : PinDrainAirborne) * dt;
            offset = Vector3.MoveTowards(offset, Vector3.zero, drain);
            if (offset.magnitude > PinMax) offset = offset.normalized * PinMax;
            var lp = transform.localPosition; transform.localPosition = new Vector3(offset.x, lp.y, offset.z);
            for (int f = 0; f < 2; f++) if (pinned[f] && toes[f]) { if (f != foot) anchor[f] = toes[f].position; else anchor[f] = toes[f].position; }
        }

        void MeasureToes(float dt)
        {
            PlantedToeSpeed = 0; if (dt <= 0) return;
            for (int f = 0; f < 2; f++)
            {
                var t = toes[f]; if (!t) continue; var p = t.position;
                float h = Local(t).y - toeRest; var d = p - lastToe[f]; d.y = 0;
                if (h < .015f && lastToe[f] != Vector3.zero) PlantedToeSpeed = Mathf.Max(PlantedToeSpeed, d.magnitude / dt);
                lastToe[f] = p;
            }
        }
        /// After a teleport (door, quick travel) the toes jumped: forget their last positions.
        /// Jump straight to the seated pose (a respawn on a bench).
        public void SnapSeat() { SeatWeight = Seated ? 1 : 0; }
        public void ResetFootTracking() { lastToe[0] = lastToe[1] = Vector3.zero; pinned[0] = pinned[1] = false; var lp = transform.localPosition; transform.localPosition = new Vector3(0, lp.y, 0); }

        void OnDestroy() { if (graph.IsValid()) graph.Destroy(); }
    }
}
