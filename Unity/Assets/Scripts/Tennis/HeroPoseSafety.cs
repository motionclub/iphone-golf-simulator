using System;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// The post-animation pose pass every hero pipeline calls (tennis HeroTennisDriver, golf GolferView, plaza
    /// HubHeroAnimator). Since 2026-10-17 (work/hand-clearance) its clearance is the general HeroClearance solver:
    /// a collision proxy fitted from the skinned body and the worn garments, and an arm/grip IK that keeps hands,
    /// forearms and the held racket/club out of both. The callers' flags map onto how far each hand may travel.
    public sealed class HeroPoseSafety
    {
        readonly MatchHeroLook look;
        public readonly HeroClearance clearance;
        public float ResidualDepth { get; private set; }
        public int VolumeCount => clearance != null && clearance.Ready ? clearance.proxy.capsules.Count(c => c != null) : 0;
        public void LimitWaveWristFlexion()
        {
            var hand = look.Bone(HumanBodyBones.LeftHand);
            var lower = look.Bone(HumanBodyBones.LeftLowerArm);
            var middle = look.Bone(HumanBodyBones.LeftMiddleProximal);
            if (!hand || !lower || !middle) return;
            var palm = middle.position - hand.position;
            var forearm = hand.position - lower.position;
            float angle = Vector3.Angle(palm, forearm);
            // Keep pronation/supination authored, but prevent the palm folding
            // back across the wrist. This is only for waving, not floor bracing.
            const float limit = 55;
            if (angle > limit)
                hand.rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(palm, forearm), (angle - limit) / angle) * hand.rotation;
        }
        public void RelaxWaveWrist()
        {
            LimitWaveWristFlexion();
            var hand=look.Bone(HumanBodyBones.LeftHand);var lower=look.Bone(HumanBodyBones.LeftLowerArm);var middle=look.Bone(HumanBodyBones.LeftMiddleProximal);
            if(!hand||!lower||!middle)return;
            var palm=middle.position-hand.position;var forearm=hand.position-lower.position;
            var index = look.Bone(HumanBodyBones.LeftIndexProximal);
            var little = look.Bone(HumanBodyBones.LeftLittleProximal);
            if (!index || !little) return;
            palm = (middle.position-hand.position).normalized;
            var normal = Vector3.Cross(index.position-little.position,palm).normalized;
            var facing = Vector3.ProjectOnPlane(look.transform.forward,palm).normalized;
            if (facing.sqrMagnitude < .1f) return;
            // Share palm presentation between forearm roll and wrist rotation.
            // This avoids an inward-facing wave and concentrates less twist at
            // the wrist seam. Bone lengths and the waving fingers stay intact.
            float raised = Mathf.SmoothStep(0,1,Mathf.InverseLerp(.04f,.18f,Vector3.Dot(hand.position-lower.position,look.transform.up)));
            float roll = Mathf.Clamp(Vector3.SignedAngle(normal,facing,palm),-60,60)*raised;
            var target = Quaternion.AngleAxis(roll,palm)*hand.rotation;
            lower.rotation = Quaternion.AngleAxis(roll*.5f,forearm.normalized)*lower.rotation;
            hand.rotation = target;
        }

        public HeroPoseSafety(MatchHeroLook look)
        {
            this.look = look;
            if (!look || !look.body || !look.body.sharedMesh || !look.body.sharedMesh.isReadable) return;
            // in the game the proxy is fitted on a worker thread (no load hitch); tools and tests fit at once
            clearance = new HeroClearance(look, background: Application.isPlaying);
        }

        /// Bake-first (HeroClearanceTracks): the hero's playable graph, so the baked correction of whatever clips it plays is
        /// applied before the residual solve. Callers set it once after building their graph (layerAffects: the graph's layer
        /// masks, null = every layer drives every bone).
        public HeroClearanceTracks.Player Tracks { get; private set; }
        public void UseGraph(UnityEngine.Playables.PlayableGraph graph, Func<int, Transform, bool> layerAffects = null)
        {
            if (!look) return;
            var lib = HeroClearanceTracks.For(look.female, look.golfKit);
            if (lib == null) { Tracks = null; return; }
            Tracks = new HeroClearanceTracks.Player(HeroClearanceTracks.RootOf(look), lib) { graph = graph, layerAffects = layerAffects };
            Tracks.SetArms(look.Bone(HumanBodyBones.LeftUpperArm), look.Bone(HumanBodyBones.LeftLowerArm), look.Bone(HumanBodyBones.LeftHand),
                           look.Bone(HumanBodyBones.RightUpperArm), look.Bone(HumanBodyBones.RightLowerArm), look.Bone(HumanBodyBones.RightHand));
            if (clearance != null) clearance.Residual = true;
        }

        int lastFrame = int.MinValue; float lastDt;
        /// The whole pass last call (track + residual solve), ms: the COST gate's number.
        public double LastMs { get; private set; }
        /// Diagnostics / A-B only (HeroClearanceFilm.GolfFirstShot FILM_CLEARANCE=0): the whole pass off.
        public static bool Disabled;
        static readonly System.Diagnostics.Stopwatch timer = new System.Diagnostics.Stopwatch();
        /// lockWrists: the hands hold the racket / club where the clip put it (contact, a grip); they may still move
        /// `gripFreedom` (0..1) of the full travel. freeLeftHand: the left hand is free while the right is locked
        /// (serve toss). twoHanded: both hands are on the racket (also detected from the pose).
        public void Apply(bool lockWrists, bool freeLeftHand = false, float gripFreedom = 0, bool twoHanded = false)
        {
            ResidualDepth = 0; if (Disabled) { LastMs = 0; return; } timer.Restart();
            try { ApplyTimed(lockWrists, freeLeftHand, gripFreedom, twoHanded); }
            finally { timer.Stop(); LastMs = timer.Elapsed.TotalMilliseconds; }
        }
        void ApplyTimed(bool lockWrists, bool freeLeftHand, float gripFreedom, bool twoHanded)
        {
            var q = new HeroClearance.Request
            {
                travelRight = lockWrists ? Mathf.Clamp01(gripFreedom) : 1,
                travelLeft = !lockWrists || freeLeftHand ? 1 : Mathf.Clamp01(gripFreedom),
                twoHanded = twoHanded,
            };
            Tracks?.Apply(q.travelLeft, q.travelRight);
            if (clearance == null) return;
            // a pure baked clip: already cleared offline against the real meshes; the residual solve only runs on blends
            if (Tracks != null && Tracks.Coverage > .999f) { clearance.Reset(); return; }
            // continuous playback smooths; a diagnostic sample (edit mode, a jump) solves from scratch
            float dt = 0;
            if (Application.isPlaying)
            {
                int frame = Time.frameCount;
                clearance.BeginFrame(frame);
                if (frame == lastFrame) dt = lastDt;   // the same frame's pose evaluated again
                else { dt = frame == lastFrame + 1 ? Mathf.Max(Time.deltaTime, 1e-4f) : 0; lastDt = dt; lastFrame = frame; }
            }
            if (dt <= 0) clearance.Reset();
            clearance.Solve(q, dt);
            ResidualDepth = clearance.ResidualDepth;
        }

        public void Refresh() => clearance?.proxy.Refresh();
        /// Deepest proxy violation of the hands and forearms now (m).
        public float MeasureArmDepth() { if (clearance == null) return 0; clearance.proxy.Refresh(); return clearance.Measure(false); }
        /// Depth of a point (with a radius) inside the body + garments proxy, arms excluded.
        public float Depth(Vector3 point, float radius, out Vector3 push)
        {
            push = Vector3.zero; if (clearance == null) return 0;
            float deepest = 0;
            foreach (var c in clearance.proxy.capsules)
            {
                if (c == null || c.part == HeroClearanceProxy.Part.UpperArm || c.part == HeroClearanceProxy.Part.Forearm || c.part == HeroClearanceProxy.Part.Hand || c.part == HeroClearanceProxy.Part.Finger) continue;
                float d = HeroClearanceProxy.Depth(c, point, true, out var n) + radius;
                if (d > deepest) { deepest = d; push = n * d; }
            }
            return deepest;
        }

        /// The bend direction for a two-bone chain whose upper segment (length a) is `toJoint`, bending about `hinge`, reaching
        /// along `axis`. The joint goes where it moves least (its old position projected onto the new axis) when that is well
        /// defined and on the hinge's side; for a nearly straight limb (a tiny projection that would change side with any small
        /// move) the hinge decides (axis x hinge), so the joint never flips.
        public static Vector3 Pole(Vector3 toJoint, Vector3 hinge, Vector3 axis, float a)
        {
            var pole = Vector3.ProjectOnPlane(toJoint, axis);
            bool steady = pole.sqrMagnitude > a * a * .09f && (hinge.sqrMagnitude < 1e-12f || Vector3.Dot(Vector3.Cross(pole, axis), hinge) > 0);
            if (!steady && hinge.sqrMagnitude > 1e-12f) pole = Vector3.Cross(axis, hinge);
            return pole.sqrMagnitude > 1e-12f ? pole.normalized : Vector3.zero;
        }

        /// Keeps an elbow within maxDeg of a reference elbow plane about the shoulder-wrist line (the hand's position and rotation
        /// unchanged): a continuous clamp, so it never jumps to the other side (a flip is > 90). False when nothing was needed.
        public static bool ClampSwivel(Transform upper, Transform lower, Transform hand, Vector3 hingeRef, float maxDeg = 80)
        {
            var S = upper.position; var W = hand.position; var axis = W - S; if (axis.sqrMagnitude < 1e-8f) return false; axis.Normalize();
            var hinge = Vector3.Cross(lower.position - S, W - lower.position);
            var h0 = Vector3.ProjectOnPlane(hingeRef, axis);
            if (h0.sqrMagnitude < 1e-10f || hinge.sqrMagnitude < 1e-10f) return false;
            if (Vector3.Angle(lower.position - S, W - lower.position) < 20) return false;   // nearly straight: no hinge to keep
            float phi = Vector3.SignedAngle(h0, hinge, axis);
            if (Mathf.Abs(phi) <= maxDeg) return false;
            var r = hand.rotation; upper.rotation = Quaternion.AngleAxis(Mathf.Sign(phi) * maxDeg - phi, axis) * upper.rotation; hand.rotation = r;
            return true;
        }
        /// hinge: the bend side to keep (e.g. the game's own elbow plane); default: the chain's current one.
        public static void Solve(Transform upper, Transform lower, Transform hand, Vector3 target, Vector3 hinge = default)
        {
            var root = upper.position; var delta = target - root;
            float a = Vector3.Distance(root, lower.position), b = Vector3.Distance(lower.position, hand.position);
            float d = Mathf.Clamp(delta.magnitude, Mathf.Abs(a - b) + .00001f, a + b - .00001f);
            if (d < .0001f) return;
            var axis = delta.normalized;
            var pole = Pole(lower.position - root, hinge.sqrMagnitude > 1e-12f ? hinge : Vector3.Cross(lower.position - root, hand.position - lower.position), axis, a);
            if (pole.sqrMagnitude < 1e-12f) pole = Vector3.ProjectOnPlane(upper.forward, axis).normalized;
            float along = (a * a - b * b + d * d) / (2 * d);
            var elbow = root + axis * along + pole * Mathf.Sqrt(Mathf.Max(0, a * a - along * along));
            upper.rotation = Quaternion.FromToRotation(lower.position - root, elbow - root) * upper.rotation;
            lower.rotation = Quaternion.FromToRotation(hand.position - lower.position, target - lower.position) * lower.rotation;
        }
    }
}
