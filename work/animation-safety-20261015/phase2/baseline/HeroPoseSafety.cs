using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Bone-local exclusion volumes measured from this hero's skin. A kinematic
    /// post-animation solve: physics colliders alone cannot constrain keyed bones.
    public sealed class HeroPoseSafety
    {
        struct Volume { public Transform bone; public Vector3 centre, radius, scale; public Matrix4x4 world, inverse; }
        readonly List<Volume> volumes = new();
        readonly MatchHeroLook look;
        readonly List<Vector3> racketPoints = new();
        Vector3[] racketWorldPoints;
        public float ResidualDepth { get; private set; }
        public int VolumeCount => volumes.Count;
        public void RelaxWaveWrist()
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

        public HeroPoseSafety(MatchHeroLook look)
        {
            this.look = look;
            var skin = look.body;
            if (!skin || !skin.sharedMesh || !skin.sharedMesh.isReadable) return;
            var mesh = skin.sharedMesh; var vertices = mesh.vertices;
            var weights = mesh.boneWeights; var bind = mesh.bindposes;
            foreach (var name in new[] { "Hips", "Spine", "Chest", "UpperChest", "Neck", "Head" })
            {
                int index = Array.FindIndex(skin.bones, b => b && b.name == name);
                if (index < 0) continue;
                Bounds bounds = default; int count = 0;
                for (int i = 0; i < vertices.Length; i++)
                {
                    var w = weights[i];
                    float amount = (w.boneIndex0 == index ? w.weight0 : 0) + (w.boneIndex1 == index ? w.weight1 : 0)
                        + (w.boneIndex2 == index ? w.weight2 : 0) + (w.boneIndex3 == index ? w.weight3 : 0);
                    if (amount < .35f) continue;
                    var p = bind[index].MultiplyPoint3x4(vertices[i]);
                    if (count++ == 0) bounds = new Bounds(p, Vector3.zero); else bounds.Encapsulate(p);
                }
                if (count < 8) continue;
                // The ellipsoid follows the anatomical segment, including its
                // garment allowance. Head padding also protects a fitted visor.
                var padding = Vector3.one * (name == "Head" ? .025f : .012f);
                volumes.Add(new Volume { bone = skin.bones[index], centre = bounds.center,
                    radius = Vector3.Max(bounds.extents, Vector3.one * .025f) + padding });
            }
            if (look.racketGrip)
                foreach (var filter in look.racketGrip.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (!filter.sharedMesh || !filter.sharedMesh.isReadable || filter.name.Contains("Collider")) continue;
                    var points = filter.sharedMesh.vertices;
                    var matrix = look.racketGrip.worldToLocalMatrix * filter.transform.localToWorldMatrix;
                    for (int i = 0; i < points.Length; i += Mathf.Max(1, points.Length / 24))
                        racketPoints.Add(matrix.MultiplyPoint3x4(points[i]));
                }
            racketWorldPoints = new Vector3[racketPoints.Count];
            Refresh();
        }

        public void Refresh()
        {
            for (int i = 0; i < volumes.Count; i++)
            {
                var v = volumes[i]; v.world = v.bone.localToWorldMatrix;
                v.inverse = v.bone.worldToLocalMatrix; v.scale = v.bone.lossyScale;
                volumes[i] = v;
            }
        }

        public float Depth(Vector3 point, float radius, out Vector3 push)
        {
            float deepest = 0; push = Vector3.zero;
            foreach (var volume in volumes)
            {
                var matrix = volume.world;
                var p = volume.inverse.MultiplyPoint3x4(point) - volume.centre;
                var scale = volume.scale;
                var r = volume.radius + new Vector3(radius / Mathf.Max(.0001f, Mathf.Abs(scale.x)),
                    radius / Mathf.Max(.0001f, Mathf.Abs(scale.y)), radius / Mathf.Max(.0001f, Mathf.Abs(scale.z)));
                float n = new Vector3(p.x / r.x, p.y / r.y, p.z / r.z).magnitude;
                if (n >= 1) continue;
                var direction = n > .0001f ? p / n : Vector3.forward * r.z;
                var displacement = matrix.MultiplyVector(direction - p);
                float depth = displacement.magnitude;
                if (depth > deepest) { deepest = depth; push = displacement; }
            }
            return deepest;
        }

        float ArmCost(Vector3 shoulder, Vector3 elbow, Vector3 wrist)
        {
            float cost = 0;
            for (int k = 2; k <= 5; k++)
            {
                float d = Depth(Vector3.Lerp(shoulder, elbow, k / 5f), .035f, out _);
                cost += d * d;
            }
            for (int k = 1; k <= 5; k++)
            {
                float d = Depth(Vector3.Lerp(elbow, wrist, k / 5f), .032f, out _);
                cost += d * d;
            }
            return cost;
        }

        public float MeasureArmDepth()
        {
            Refresh();
            float depth = 0;
            foreach (bool right in new[] { false, true })
            {
                var upper = look.Bone(right ? HumanBodyBones.RightUpperArm : HumanBodyBones.LeftUpperArm);
                var lower = look.Bone(right ? HumanBodyBones.RightLowerArm : HumanBodyBones.LeftLowerArm);
                var hand = look.Bone(right ? HumanBodyBones.RightHand : HumanBodyBones.LeftHand);
                if (upper && lower && hand) depth = Mathf.Max(depth, Mathf.Sqrt(ArmCost(upper.position, lower.position, hand.position)));
            }
            return depth;
        }

        /// Locked wrists preserve the two-hand grip and the exact string contact.
        /// Elbows can still swivel around that fixed shoulder-to-wrist axis.
        public void Apply(bool lockWrists)
        {
            ResidualDepth = 0;
            Refresh();
            SolveArm(false, lockWrists); SolveArm(true, lockWrists);
            if (!lockWrists) ClearRacket();
        }

        void ClearRacket()
        {
            var hand = look.Bone(HumanBodyBones.RightHand); var grip = look.racketGrip;
            if (!hand || !grip || racketPoints.Count == 0 || Vector3.Distance(hand.position, grip.position) > .145f) return;
            // Rotate the held prop with its hand. Released props retain their authored
            // throw/drop trajectory. No socket offset or grip separation is introduced.
            var origin = hand.position; var initial = hand.rotation;
            for (int i = 0; i < racketPoints.Count; i++) racketWorldPoints[i] = grip.TransformPoint(racketPoints[i]) - origin;
            float Cost(Quaternion turn)
            {
                float cost = 0;
                foreach (var p in racketWorldPoints)
                {
                    float d = Depth(origin + turn * p, .008f, out _);
                    cost += d * d;
                }
                return cost;
            }
            float bestCost = Cost(Quaternion.identity);
            if (bestCost < .000001f) return;
            var best = Quaternion.identity;
            foreach (var axis in new[] { look.transform.right, look.transform.up, look.transform.forward })
                for (int angle = -70; angle <= 70; angle += 10)
                {
                    var turn = Quaternion.AngleAxis(angle, axis);
                    float cost = Cost(turn) + angle * angle * .000000002f;
                    if (cost < bestCost) { bestCost = cost; best = turn; }
                }
            hand.rotation = best * initial;
        }

        void SolveArm(bool right, bool locked)
        {
            var upper = look.Bone(right ? HumanBodyBones.RightUpperArm : HumanBodyBones.LeftUpperArm);
            var lower = look.Bone(right ? HumanBodyBones.RightLowerArm : HumanBodyBones.LeftLowerArm);
            var hand = look.Bone(right ? HumanBodyBones.RightHand : HumanBodyBones.LeftHand);
            if (!upper || !lower || !hand) return;
            var rotation = hand.rotation;
            var wrist = hand.position;
            if (!locked)
            {
                for (int pass = 0; pass < 3; pass++)
                {
                    if (Depth(wrist, .045f, out var push) <= .001f) break;
                    wrist += push;
                }
                Solve(upper, lower, hand, wrist);
            }
            var shoulder = upper.position; var elbow = lower.position;
            wrist = hand.position;
            var axis = (wrist - shoulder).normalized;
            float before = ArmCost(shoulder, elbow, wrist);
            if (before > .000001f)
            {
                float Cost(float angle)
                {
                    var e = shoulder + Quaternion.AngleAxis(angle, axis) * (elbow - shoulder);
                    var chest = look.Bone(HumanBodyBones.Chest);
                    float behind = chest ? Mathf.Max(0, -Vector3.Dot(e - chest.position, look.transform.forward)) : 0;
                    return ArmCost(shoulder, e, wrist) + behind * behind * .1f + angle * angle * .000000002f;
                }
                float best = 0, value = Cost(0);
                for (int a = -170; a <= 170; a += 10)
                { float c = Cost(a); if (c < value) { value = c; best = a; } }
                float lo = best - 10, hi = best + 10;
                for (int i = 0; i < 8; i++)
                { float a = Mathf.Lerp(lo, hi, 1f / 3), b = Mathf.Lerp(lo, hi, 2f / 3); if (Cost(a) < Cost(b)) hi = b; else lo = a; }
                var target = shoulder + Quaternion.AngleAxis((lo + hi) * .5f, axis) * (elbow - shoulder);
                upper.rotation = Quaternion.FromToRotation(elbow - shoulder, target - shoulder) * upper.rotation;
                lower.rotation = Quaternion.FromToRotation(hand.position - lower.position, wrist - lower.position) * lower.rotation;
            }
            hand.rotation = rotation;
            ResidualDepth = Mathf.Max(ResidualDepth, Mathf.Sqrt(ArmCost(upper.position, lower.position, hand.position)));
        }

        public static void Solve(Transform upper, Transform lower, Transform hand, Vector3 target)
        {
            var root = upper.position; var delta = target - root;
            float a = Vector3.Distance(root, lower.position), b = Vector3.Distance(lower.position, hand.position);
            float d = Mathf.Clamp(delta.magnitude, Mathf.Abs(a - b) + .00001f, a + b - .00001f);
            if (d < .0001f) return;
            var axis = delta.normalized;
            var pole = Vector3.ProjectOnPlane(lower.position - root, axis).normalized;
            if (pole.sqrMagnitude < .1f) pole = Vector3.ProjectOnPlane(upper.forward, axis).normalized;
            float along = (a * a - b * b + d * d) / (2 * d);
            var elbow = root + axis * along + pole * Mathf.Sqrt(Mathf.Max(0, a * a - along * along));
            upper.rotation = Quaternion.FromToRotation(lower.position - root, elbow - root) * upper.rotation;
            lower.rotation = Quaternion.FromToRotation(hand.position - lower.position, target - lower.position) * lower.rotation;
        }
    }
}
