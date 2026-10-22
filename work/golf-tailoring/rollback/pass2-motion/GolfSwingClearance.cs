using System.Linq;
using UnityEngine;

namespace GolfArcade.Game
{
    /// Two-handed driver finish and shaft clearance around the measured head envelope.
    /// Both arms solve to one shared grip. Feet, torso turn and impact stay authored.
    public sealed class GolfSwingClearance
    {
        readonly HeroGolfer hero;
        readonly Transform head, grip;
        readonly Vector3 centre;
        readonly float radius;
        readonly Vector3 driveReleaseShaft;
        readonly (GameObject node, Vector3 end)[] clubs;
        public GolfSwingClearance(HeroGolfer hero)
        {
            this.hero = hero; head = hero.Bones["Head"]; grip = hero.Bones["Club"];
            // Authored Drive shaft at F076 (2.50 s), in model space. Anchoring the
            // direction here prevents the changing source pose from flipping the blend.
            bool female = hero.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>().female;
            driveReleaseShaft = female ? new Vector3(-.177348f, .9043239f, .38826f)
                                      : new Vector3(-.1848222f, .8964227f, .4028237f);
            var body = hero.Part("Body"); var mesh = body.sharedMesh;
            int h = System.Array.FindIndex(body.bones, b => b == head);
            var vertices = mesh.vertices; var weights = mesh.boneWeights;
            var bounds = new Bounds(); bool first = true;
            for (int i = 0; i < vertices.Length; i++)
            {
                var w = weights[i];
                if (!(w.boneIndex0 == h && w.weight0 > .6f || w.boneIndex1 == h && w.weight1 > .6f)) continue;
                var p = mesh.bindposes[h].MultiplyPoint3x4(vertices[i]);
                if (first) { bounds = new Bounds(p, Vector3.zero); first = false; } else bounds.Encapsulate(p);
            }
            centre = bounds.center;
            radius = Mathf.Max(bounds.extents.x, bounds.extents.y, bounds.extents.z) + .075f;
            clubs = hero.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r => r.name.StartsWith("CLUB_")).Select(r =>
            {
                int b = System.Array.FindIndex(r.bones, t => t == grip);
                Vector3 far = Vector3.zero;
                foreach (var v in r.sharedMesh.vertices)
                {
                    var p = r.sharedMesh.bindposes[b].MultiplyPoint3x4(v);
                    if (p.sqrMagnitude > far.sqrMagnitude) far = p;
                }
                return (r.gameObject, far);
            }).ToArray();
        }
        /// Continue the driver's release into a wrap behind the head. The authored
        /// impact is untouched; a smooth blend begins only after the arms extend through it.
        public void ApplyDriveFollowThrough(float clipTime)
        {
            float progress = Mathf.InverseLerp(2.50f, 3.02f, clipTime);
            if (progress <= 0) return;
            // Continue with momentum, then decelerate into the held finish.
            float travel = progress * (2 - progress);
            var club = clubs.FirstOrDefault(c => c.node.activeSelf);
            if (!club.node) return;
            var left = hero.Bones["LeftHand"]; var rightHand = hero.Bones["RightHand"];
            var leftUpper = hero.Bones["LeftUpperArm"]; var rightUpper = hero.Bones["RightUpperArm"];
            var across = (rightUpper.position - leftUpper.position).normalized;
            var up = hero.Root.transform.up;
            var forward = Vector3.ProjectOnPlane(head.forward, up).normalized;
            across = Vector3.ProjectOnPlane(across, forward).normalized;
            float scale = Mathf.Abs(hero.Root.transform.lossyScale.x);
            var headCentre = head.TransformPoint(centre);
            var originalGrip = grip.position; var originalRotation = grip.rotation;
            var shaft = grip.TransformVector(club.end).normalized;
            var finishShaft = (across - up * .65f - forward * .12f).normalized;
            // A spherical Bezier travels up and behind the head before the shaft
            // lowers. A shortest-rotation blend to the finish cuts through the torso.
            var releaseShaft = hero.Root.transform.TransformVector(driveReleaseShaft).normalized;
            var overheadShaft = (up * .9f + across * .35f - forward * .65f).normalized;
            var desiredShaft = SphericalArc(releaseShaft, overheadShaft, finishShaft, travel);
            var turn = Quaternion.FromToRotation(shaft, desiredShaft);

            // Carry the hands around the lead side at their radial distance from
            // the head, rather than translating them through the shoulder/chest.
            var fromHead = originalGrip - headCentre;
            var startRadial = Vector3.ProjectOnPlane(fromHead, up);
            var finishRadial = -across * (.24f * scale) - forward * ((radius + .035f) * scale);
            var radialDirection = SphericalArc(startRadial.normalized, -across, finishRadial.normalized, travel);
            float radialDistance = Mathf.Lerp(startRadial.magnitude, finishRadial.magnitude, travel);
            float height = Mathf.Lerp(Vector3.Dot(fromHead, up), .065f * scale, travel);
            var targetGrip = headCentre + radialDirection * radialDistance + up * height;
            var leftOffset = turn * (left.position - originalGrip);
            var rightOffset = turn * (rightHand.position - originalGrip);
            var leftRotation = turn * left.rotation; var rightRotation = turn * rightHand.rotation;
            float Reach(string side) => Vector3.Distance(hero.Bones[side + "UpperArm"].position, hero.Bones[side + "LowerArm"].position) + Vector3.Distance(hero.Bones[side + "LowerArm"].position, hero.Bones[side + "Hand"].position) - .002f * scale;
            float leftReach = Reach("Left"), rightReach = Reach("Right");
            // Keep one common grip inside both arm reach spheres.
            for (int i = 0; i < 8; i++)
            {
                var delta = targetGrip + leftOffset - leftUpper.position;
                if (delta.magnitude > leftReach) targetGrip -= delta.normalized * (delta.magnitude - leftReach);
                delta = targetGrip + rightOffset - rightUpper.position;
                if (delta.magnitude > rightReach) targetGrip -= delta.normalized * (delta.magnitude - rightReach);
            }
            SolveTo("Left", targetGrip + leftOffset, leftRotation);
            SolveTo("Right", targetGrip + rightOffset, rightRotation);
            grip.SetPositionAndRotation(targetGrip, turn * originalRotation);
        }

        static Vector3 SphericalArc(Vector3 start, Vector3 control, Vector3 end, float t)
        {
            return Vector3.Slerp(Vector3.Slerp(start, control, t), Vector3.Slerp(control, end, t), t).normalized;
        }

        public void Apply()
        {
            foreach (var club in clubs)
            {
                if (!club.node.activeSelf) continue;
                Vector3 shaft = grip.TransformVector(club.end), toHead = head.TransformPoint(centre) - grip.position;
                float length = toHead.magnitude, safe = radius * Mathf.Abs(head.lossyScale.x);
                if (length <= safe || length > shaft.magnitude + safe) return;
                float angle = Vector3.Angle(toHead, shaft), cone = Mathf.Asin(safe / length) * Mathf.Rad2Deg;
                const float feather = 12;
                if (angle >= cone + feather) return;
                // C1-continuous approach to the exclusion cone, with positive clearance inside it.
                float target = angle < cone - feather ? cone : angle + Mathf.Pow(cone + feather - angle, 2) / (4 * feather);
                var axis = Vector3.Cross(toHead, shaft);
                if (axis.sqrMagnitude < .00001f) axis = Vector3.Cross(toHead, head.forward);
                var turn = Quaternion.AngleAxis(target - angle, axis.normalized);
                Solve("Left", turn); Solve("Right", turn);
                grip.rotation = turn * grip.rotation;
                return;
            }
        }
        void Solve(string side, Quaternion turn)
        {
            var hand = hero.Bones[side + "Hand"];
            var target = grip.position + turn * (hand.position - grip.position);
            var rotation = turn * hand.rotation;
            SolveTo(side, target, rotation);
        }
        void SolveTo(string side, Vector3 target, Quaternion rotation)
        {
            var upper = hero.Bones[side + "UpperArm"]; var lower = hero.Bones[side + "LowerArm"]; var hand = hero.Bones[side + "Hand"];
            Vector3 root = upper.position, delta = target - root;
            float a = Vector3.Distance(root, lower.position), b = Vector3.Distance(lower.position, hand.position);
            float d = Mathf.Clamp(delta.magnitude, Mathf.Abs(a-b)+.0001f, a+b-.0001f);
            var forward = delta.normalized;
            var bend = Vector3.ProjectOnPlane(lower.position-root, forward).normalized;
            if (bend.sqrMagnitude < .1f) bend = Vector3.ProjectOnPlane(upper.forward, forward).normalized;
            float along = (a*a-b*b+d*d)/(2*d);
            var elbow = root + forward*along + bend*Mathf.Sqrt(Mathf.Max(0,a*a-along*along));
            upper.rotation = Quaternion.FromToRotation(lower.position-root, elbow-root)*upper.rotation;
            lower.rotation = Quaternion.FromToRotation(hand.position-lower.position, target-lower.position)*lower.rotation;
            hand.rotation = rotation;
        }
    }
}
