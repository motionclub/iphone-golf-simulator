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
            // (Re-measured for the 2026-10-12 swing fix: work/swing-fix/scripts/release_shaft.py.)
            bool female = hero.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>().female;
            driveReleaseShaft = female ? new Vector3(-.2134009f, .8788473f, .4267172f)
                                      : new Vector3(-.2184253f, .8734274f, .4352183f);
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
        /// `weight` is how much of the pose on screen is this clip time's (a crossfade leaving the finish behind fades the wrap out with it).
        public void ApplyDriveFollowThrough(float clipTime, float weight = 1f)
        {
            float progress = Mathf.InverseLerp(2.50f, 3.02f, clipTime);
            if (progress <= 0 || weight <= 0) return;
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
            var turn = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(shaft, desiredShaft), weight);

            // Carry the hands around the lead side at their radial distance from
            // the head, rather than translating them through the shoulder/chest.
            var fromHead = originalGrip - headCentre;
            var startRadial = Vector3.ProjectOnPlane(fromHead, up);
            var finishRadial = -across * (.24f * scale) - forward * ((radius + .035f) * scale);
            var radialDirection = SphericalArc(startRadial.normalized, -across, finishRadial.normalized, travel);
            float radialDistance = Mathf.Lerp(startRadial.magnitude, finishRadial.magnitude, travel);
            float height = Mathf.Lerp(Vector3.Dot(fromHead, up), .065f * scale, travel);
            var targetGrip = Vector3.Lerp(originalGrip, headCentre + radialDirection * radialDistance + up * height, weight);
            var leftOffset = turn * (left.position - originalGrip);
            var rightOffset = turn * (rightHand.position - originalGrip);
            var leftRotation = turn * left.rotation; var rightRotation = turn * rightHand.rotation;
            float Reach(string side) => Vector3.Distance(hero.Bones[side + "UpperArm"].position, hero.Bones[side + "LowerArm"].position) + Vector3.Distance(hero.Bones[side + "LowerArm"].position, hero.Bones[side + "Hand"].position) - .002f * scale;
            float elbowBlend = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(2.50f, 2.63f, clipTime)) * weight;
            float FlexedReach(string side)
            {
                float a = Vector3.Distance(hero.Bones[side + "UpperArm"].position, hero.Bones[side + "LowerArm"].position);
                float b = Vector3.Distance(hero.Bones[side + "LowerArm"].position, hero.Bones[side + "Hand"].position);
                // Reserve enough reach for a bent elbow instead of locking the arm straight.
                float bent = Mathf.Sqrt(a*a + b*b + 2*a*b*Mathf.Cos(38*Mathf.Deg2Rad));
                return Mathf.Lerp(Reach(side), bent, elbowBlend);
            }
            float leftReach = FlexedReach("Left"), rightReach = FlexedReach("Right");
            // Keep one common grip inside both arm reach spheres.
            for (int i = 0; i < 8; i++)
            {
                var delta = targetGrip + leftOffset - leftUpper.position;
                if (delta.magnitude > leftReach) targetGrip -= delta.normalized * (delta.magnitude - leftReach);
                delta = targetGrip + rightOffset - rightUpper.position;
                if (delta.magnitude > rightReach) targetGrip -= delta.normalized * (delta.magnitude - rightReach);
            }
            SolveTo("Left", targetGrip + leftOffset, leftRotation, elbowBlend);
            SolveTo("Right", targetGrip + rightOffset, rightRotation, elbowBlend);
            grip.SetPositionAndRotation(targetGrip, turn * originalRotation);
        }

        // Move a single rigid grip along a clearance arc. The arms follow the hands, rather
        // than turning both upper arms about a shoulder-line hinge.
        Transform postSpace;
        bool postStartKnown;
        Vector3 postStart, postClub, postShaft;
        Quaternion postClubRotation;
        readonly Vector3[] postHandOffset = new Vector3[2];
        readonly Quaternion[] postHandRotation = new Quaternion[2];
        readonly Quaternion[] postUpperRotation = new Quaternion[2], postLowerRotation = new Quaternion[2], postWristRelative = new Quaternion[2];
        readonly Vector3[] postUpperVector = new Vector3[2], postLowerVector = new Vector3[2];
        readonly int[] postTransportFrame = new int[2];
        readonly float[] postTwist = new float[2], postTwistVelocity = new float[2], postTwistTarget = new float[2];
        // Slerp takes the shortest way, which flips side once the pose underneath has turned more than 180 deg away
        // from the held one (the club spun ~45 deg in one frame on the next address). Keep the side used last frame.
        readonly Quaternion[] blendRelative = new Quaternion[3]; readonly bool[] blendKnown = new bool[3];
        Quaternion Blend(Quaternion under, Quaternion over, float t, int slot)
        {
            var rel = over * Quaternion.Inverse(under);
            if (blendKnown[slot] && Quaternion.Dot(rel, blendRelative[slot]) < 0) rel = new Quaternion(-rel.x, -rel.y, -rel.z, -rel.w);
            blendRelative[slot] = rel; blendKnown[slot] = true;
            rel.ToAngleAxis(out float angle, out var axis);
            if (float.IsNaN(axis.x) || axis.sqrMagnitude < 1e-8f) return over;
            return Quaternion.AngleAxis(angle * t, axis) * under;
        }
        bool postHeld; readonly Vector3[] heldTarget = new Vector3[2]; readonly Quaternion[] heldRotation = new Quaternion[2];
        Vector3 heldClub; Quaternion heldClubRotation;
        Quaternion postTurnLocal = Quaternion.identity, postTurnBase = Quaternion.identity;
        Vector3 postDesiredLocal, postDesiredBase; int postTurnFrame = -1;
        public void CapturePostShotStart()
        {
            if (postStartKnown) return;
            postSpace = hero.Bones["Chest"];
            var left = hero.Bones["LeftHand"]; var right = hero.Bones["RightHand"];
            var centre = (left.position + right.position) * .5f;
            postStart = postSpace.InverseTransformPoint(centre);
            postClub = postSpace.InverseTransformPoint(grip.position);
            postClubRotation = Quaternion.Inverse(postSpace.rotation) * grip.rotation;
            var active = clubs.FirstOrDefault(c => c.node.activeSelf); if (!active.node) return;
            postShaft = postSpace.InverseTransformDirection(grip.TransformVector(active.end).normalized);
            postTurnLocal = postTurnBase = Quaternion.identity; postDesiredLocal = postDesiredBase = postShaft; postTurnFrame = -1;
            var sides = new[] { "Left", "Right" };
            for(int i=0;i<2;i++)
            {
                var hand=hero.Bones[sides[i]+"Hand"]; var upper=hero.Bones[sides[i]+"UpperArm"]; var elbow=hero.Bones[sides[i]+"LowerArm"];
                postHandOffset[i]=postSpace.InverseTransformDirection(hand.position-centre);
                postHandRotation[i]=Quaternion.Inverse(postSpace.rotation)*hand.rotation;
                postUpperRotation[i]=Quaternion.Inverse(postSpace.rotation)*upper.rotation;
                postLowerRotation[i]=Quaternion.Inverse(postSpace.rotation)*elbow.rotation;
                postWristRelative[i]=Quaternion.Inverse(elbow.rotation)*hand.rotation;
                postUpperVector[i]=postSpace.InverseTransformDirection(elbow.position-upper.position);
                postLowerVector[i]=postSpace.InverseTransformDirection(hand.position-elbow.position);
                postTransportFrame[i]=Time.frameCount;
                postTwist[i]=postTwistVelocity[i]=postTwistTarget[i]=0;
                restingBend[i]=Vector3.ProjectOnPlane(elbow.position-upper.position,hand.position-upper.position).normalized;
                restingBendKnown[i]=true; restingBendFrame[i]=Time.frameCount;
            }
            postStartKnown=true;
        }
        /// `weight`: progress along the lowering (0 = held finish, 1 = rest). `fade`: how much of the
        /// post-shot pose is on screen; leaving it (the next address) blends out from where the club is,
        /// rather than running the arc backwards (the club used to whip back over the shoulder).
        public void LowerPostShotGrip(float weight, float fade = 1)
        {
            if (weight <= 0 || fade <= 0 || !postStartKnown || !postSpace) return;
            var active = clubs.FirstOrDefault(c => c.node.activeSelf); if (!active.node) return;
            var left = hero.Bones["LeftHand"]; var right = hero.Bones["RightHand"];
            var lu = hero.Bones["LeftUpperArm"]; var ru = hero.Bones["RightUpperArm"];
            var middle = (lu.position + ru.position) * .5f;
            var up = (middle - hero.Bones["Hips"].position).normalized;
            var across = (ru.position - lu.position).normalized;
            var front = Vector3.Cross(across, up).normalized;
            float scale = Mathf.Abs(hero.Root.transform.lossyScale.x);
            var start = postSpace.TransformPoint(postStart);
            // 11-19 review: the hands drop out to the lead side first and finish just lead of the
            // chest line, so the shaft never has to cross in front of the face on its way down.
            var end = middle + (front * .26f - up * .30f - across * .06f) * scale;
            var c0 = start + (-across * .08f - up * .10f + front * .06f) * scale;
            var c1 = end + (front * .06f - across * .08f + up * .14f) * scale;
            float v = 1 - weight;
            var target = start * (v*v*v) + c0 * (3*v*v*weight) + c1 * (3*v*weight*weight) + end * (weight*weight*weight);
            // The hands themselves stay outside the head envelope (a half finish starts them by the chin and the
            // path drew them in); faded in over the first part so a finish already inside it does not jump.
            {
                var headCentre = head.TransformPoint(centre); var fromHead = target - headCentre;
                float keep = radius * Mathf.Abs(head.lossyScale.x) + .01f * scale;
                if (fromHead.magnitude < keep && fromHead.sqrMagnitude > 1e-8f)
                    target = Vector3.Lerp(target, headCentre + fromHead.normalized * keep, Mathf.Clamp01(weight * 8));
            }
            var shaft = postSpace.TransformDirection(postShaft).normalized;
            float length = grip.TransformVector(active.end).magnitude;
            var world = hero.Root.transform.up;
            // Rest: the club hangs out to the lead side and ahead, its head just above the turf and
            // clear of both shoes (the old rest pointed straight ahead, onto the lead foot).
            var restFlat = Vector3.ProjectOnPlane(front * .6f - across * .8f, world).normalized;
            var gripEnd = end + (postSpace.TransformPoint(postClub) - start);
            float drop = Vector3.Dot(gripEnd - hero.Root.transform.position, world) - .075f * scale;
            float pitch = Mathf.Asin(Mathf.Clamp(drop / Mathf.Max(length, .01f), .35f, .95f));
            var rest = (restFlat * Mathf.Cos(pitch) - world * Mathf.Sin(pitch)).normalized;
            // A wrapped finish (shaft behind the neck, pointing to the trail side) comes back around
            // behind the lead shoulder; a short finish lowers directly. Never over the face.
            // `away` (up, back, lead side) biases every arc off the face and keeps the midpoint stable
            // when the finish shaft and the rest are nearly opposite (a bare shaft + rest flips there).
            var away = (world * .55f - front * .55f - across * .6f).normalized;
            var mid = (shaft + rest + away * .6f).normalized;
            float wrap = Mathf.Clamp01(Vector3.Dot(shaft, across) * 1.5f + Vector3.Dot(shaft, -front));
            var control = Vector3.Slerp(mid, away, wrap).normalized;
            var offset = postSpace.TransformPoint(postClub) - start;
            var desired = ClearOfHead(target + offset, SphericalArc(shaft, control, rest, weight), length, away);
            // again from where the grip really is once the club is turned (it sits a few cm from the hands' centre)
            desired = ClearOfHead(target + Quaternion.FromToRotation(shaft, desired) * offset, desired, length, away);
            // Accumulate the club's turn frame to frame (chest space) instead of one shortest rotation
            // from the finish: on a long arc that rotation's axis swings and rolls the wrists.
            if (postTurnFrame != Time.frameCount) { postTurnBase = postTurnLocal; postDesiredBase = postDesiredLocal; postTurnFrame = Time.frameCount; }
            // ...and never faster than a relaxed hand turns the club (the arc's peak is ~2-3 deg a frame at 60 Hz).
            var desiredLocal = Vector3.RotateTowards(postDesiredBase, postSpace.InverseTransformDirection(desired), 220f * Mathf.Deg2Rad * Mathf.Clamp(Time.deltaTime, 1f / 120, .05f), 0).normalized;
            // clearance wins over the rate limit: re-clear the limited direction (no-op when it is already clear)
            desiredLocal = postSpace.InverseTransformDirection(ClearOfHead(target + Quaternion.FromToRotation(shaft, postSpace.TransformDirection(desiredLocal)) * offset, postSpace.TransformDirection(desiredLocal), length, away));
            postTurnLocal = Quaternion.FromToRotation(postDesiredBase, desiredLocal) * postTurnBase; postDesiredLocal = desiredLocal;
            var turn = postSpace.rotation * postTurnLocal * Quaternion.Inverse(postSpace.rotation);
            var clubPosition = target + turn * (postSpace.TransformPoint(postClub) - start);
            var clubRotation = turn * postSpace.rotation * postClubRotation;
            // Rigid offsets retain the palms' relative position on the shaft.
            var targets = new[] { target + turn*postSpace.TransformDirection(postHandOffset[0]), target + turn*postSpace.TransformDirection(postHandOffset[1]) };
            var rotations = new[] { turn*postSpace.rotation*postHandRotation[0], turn*postSpace.rotation*postHandRotation[1] };
            // (the gameplay root: the model under it is re-yawed when the address crossfade lands)
            var rootT = hero.Root.transform.parent ? hero.Root.transform.parent : hero.Root.transform;
            if (fade >= 1) postHeld = false;
            else if (!postHeld)
            {
                blendKnown[0] = blendKnown[1] = blendKnown[2] = false;
                // Leaving: keep the club where it is relative to the golfer (the torso under it is crossfading to
                // address, and following that turn lifted the club), then blend out to the pose underneath.
                postHeld = true;
                for (int i = 0; i < 2; i++) { heldTarget[i] = rootT.InverseTransformPoint(targets[i]); heldRotation[i] = Quaternion.Inverse(rootT.rotation) * rotations[i]; }
                heldClub = rootT.InverseTransformPoint(clubPosition); heldClubRotation = Quaternion.Inverse(rootT.rotation) * clubRotation;
            }
            if (postHeld)
            {
                for (int i = 0; i < 2; i++) { targets[i] = rootT.TransformPoint(heldTarget[i]); rotations[i] = rootT.rotation * heldRotation[i]; }
                clubPosition = rootT.TransformPoint(heldClub); clubRotation = rootT.rotation * heldClubRotation;
            }
            if (fade < 1)
            {
                targets[0] = Vector3.Lerp(left.position, targets[0], fade); targets[1] = Vector3.Lerp(right.position, targets[1], fade);
                rotations[0] = Blend(left.rotation, rotations[0], fade, 0); rotations[1] = Blend(right.rotation, rotations[1], fade, 1);
                clubPosition = Vector3.Lerp(grip.position, clubPosition, fade); clubRotation = Blend(grip.rotation, clubRotation, fade, 2);
                weight *= fade;
            }
            var sides = new[] { "Left", "Right" };
            Vector3 reachShift = Vector3.zero;
            for (int i = 0; i < 8; i++) for (int side = 0; side < 2; side++)
            {
                var upper = hero.Bones[sides[side]+"UpperArm"]; var lower = hero.Bones[sides[side]+"LowerArm"]; var hand = hero.Bones[sides[side]+"Hand"];
                float reach = Vector3.Distance(upper.position,lower.position) + Vector3.Distance(lower.position,hand.position) - .02f*scale*weight;
                var delta = targets[side] + reachShift - upper.position;
                if (delta.magnitude > reach) reachShift -= delta.normalized*(delta.magnitude-reach);
            }
            for (int side = 0; side < 2; side++)
            {
                SolveTo(sides[side], targets[side]+reachShift, rotations[side], weight, true);
            }
            clubPosition += reachShift;
            grip.SetPositionAndRotation(clubPosition, clubRotation);
            // Reuse the shared reach constraint and final safety ordering.
            RelaxPostShotElbows(weight, Vector3.zero);
        }

        // Keep the lowered two-handed grip, but let elbows settle clear of the shirt instead
        // of rigidly carrying the behind-the-head elbow plane down through the torso.
        readonly Vector3[] restingBend = new Vector3[2];
        readonly bool[] restingBendKnown = new bool[2];
        readonly int[] restingBendFrame = new int[2];
        public void ResetPostShotElbows() { restingBendKnown[0] = restingBendKnown[1] = false; postStartKnown = false; postHeld = false; }
        readonly Vector3[] restingGrip = new Vector3[2];
        readonly Quaternion[] restingHandRotation = new Quaternion[2];
        Vector3 restingClubPosition; Quaternion restingClubRotation;
        int restingGripFrame = -1;
        public void RelaxPostShotElbows(float weight, Vector3 shift, bool final = false)
        {
            if (weight <= 0 || final && restingGripFrame != Time.frameCount) return;
            var left = hero.Bones["LeftHand"]; var right = hero.Bones["RightHand"];
            var targets = final ? new[] { restingGrip[0], restingGrip[1] } : new[] { left.position, right.position };
            var clubPosition = final ? restingClubPosition : grip.position;
            var clubRotation = final ? restingClubRotation : grip.rotation;
            float scale = Mathf.Abs(hero.Root.transform.lossyScale.x);
            var sides = new[] { "Left", "Right" };
            // Constrain one shared grip inside both reach spheres, leaving elbows softly bent.
            for (int i = 0; i < 8; i++) for (int side = 0; side < 2; side++)
            {
                var upper = hero.Bones[sides[side] + "UpperArm"]; var lower = hero.Bones[sides[side] + "LowerArm"]; var hand = hero.Bones[sides[side] + "Hand"];
                float reach = Vector3.Distance(upper.position, lower.position) + Vector3.Distance(lower.position, hand.position) - .02f * scale * weight;
                var delta = targets[side] + shift - upper.position;
                if (delta.magnitude > reach) shift -= delta.normalized * (delta.magnitude - reach);
            }
            for (int side = 0; side < 2; side++)
            {
                var hand = hero.Bones[sides[side] + "Hand"];
                SolveTo(sides[side], targets[side] + shift, final ? restingHandRotation[side] : hand.rotation, Mathf.Clamp01(weight), true, final);
            }
            grip.SetPositionAndRotation(clubPosition + shift, clubRotation);
            if (!final)
            {
                restingGrip[0] = left.position; restingGrip[1] = right.position;
                restingHandRotation[0] = left.rotation; restingHandRotation[1] = right.rotation;
                restingClubPosition = grip.position; restingClubRotation = grip.rotation;
                restingGripFrame = Time.frameCount;
            }
        }

        static Vector3 SphericalArc(Vector3 start, Vector3 control, Vector3 end, float t)
        {
            return Vector3.Slerp(Vector3.Slerp(start, control, t), Vector3.Slerp(control, end, t), t).normalized;
        }

        /// The post-shot lowering runs after Apply(), so it needs its own head check: turn `shaft`
        /// (a direction from `from`) out of the cone the head envelope makes, with the same
        /// C1 feather as Apply() and a little more room, since this is a slow, close pass.
        Vector3 ClearOfHead(Vector3 from, Vector3 shaft, float length, Vector3 away)
        {
            var toHead = head.TransformPoint(centre) - from;
            float distance = toHead.magnitude, safe = (radius + .04f) * Mathf.Abs(head.lossyScale.x);
            if (distance <= safe || distance > length + safe) return shaft;
            // (asin is steep as the hands near the head; the caller rate-limits the club's turn for that)
            float angle = Vector3.Angle(toHead, shaft), cone = Mathf.Asin(Mathf.Min(.999f, safe / distance)) * Mathf.Rad2Deg;
            const float feather = 24;   // wide: a soft entry keeps the hands' turn rate low
            if (angle >= cone + feather) return shaft;
            float target = angle < cone - feather ? cone : angle + Mathf.Pow(cone + feather - angle, 2) / (4 * feather);
            // Leave the cone on the shaft's own side of the head; when the shaft points almost at the
            // head that side is undefined (it flipped frame to frame), so fade in the `away` side.
            var axisHead = toHead / distance;
            var side = Vector3.ProjectOnPlane(shaft, axisHead);
            var fallback = Vector3.ProjectOnPlane(away, axisHead).normalized;
            side += fallback * Mathf.Max(0, .35f - side.magnitude);
            if (side.sqrMagnitude < 1e-8f) return shaft;
            return (axisHead * Mathf.Cos(target * Mathf.Deg2Rad) + side.normalized * Mathf.Sin(target * Mathf.Deg2Rad)).normalized;
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

        public void SeparateHands()
        {
            var club = clubs.FirstOrDefault(c => c.node.activeSelf);
            if (!club.node) return;
            var left = hero.Bones["LeftHand"]; var right = hero.Bones["RightHand"];
            float scale = Mathf.Abs(hero.Root.transform.lossyScale.x);
            // Use the shaft's principal axis, excluding the offset club-head toe.
            var end = club.end;
            Vector3 localAxis = Mathf.Abs(end.x) > Mathf.Abs(end.y) && Mathf.Abs(end.x) > Mathf.Abs(end.z)
                ? Vector3.right * Mathf.Sign(end.x) : Mathf.Abs(end.y) > Mathf.Abs(end.z)
                ? Vector3.up * Mathf.Sign(end.y) : Vector3.forward * Mathf.Sign(end.z);
            var shaft = grip.TransformVector(localAxis).normalized;
            float along = Vector3.Dot(right.position - left.position, shaft);
            const float minimum = .072f;
            float separation = minimum * scale;
            if (Mathf.Abs(along) >= separation || Vector3.Distance(left.position, right.position) > .11f * scale) return;
            var leftRotation = left.rotation; var rightRotation = right.rotation;
            var clubPosition = grip.position; var clubRotation = grip.rotation;
            var shift = shaft * ((separation - Mathf.Abs(along)) * .5f * (along < 0 ? -1 : 1));
            // Slide along the shaft only; retain each palm’s radius and side of the grip.
            SolveTo("Left", left.position - shift, leftRotation, 1);
            SolveTo("Right", right.position + shift, rightRotation, 1);
            grip.SetPositionAndRotation(clubPosition, clubRotation);
        }
        void Solve(string side, Quaternion turn)
        {
            var hand = hero.Bones[side + "Hand"];
            var target = grip.position + turn * (hand.position - grip.position);
            var rotation = turn * hand.rotation;
            SolveTo(side, target, rotation);
        }
        Vector3 BendAroundTorso(string side, Vector3 shoulder, Vector3 wrist, Vector3 elbowCentre,
            float elbowRadius, Vector3 wristAxis, Vector3 authoredBend, float blend, bool relaxed)
        {
            var left = hero.Bones["LeftUpperArm"].position;
            var right = hero.Bones["RightUpperArm"].position;
            var shoulderMid = (left + right) * .5f;
            var pelvis = hero.Bones["Hips"].position;
            var up = (shoulderMid - pelvis).normalized;
            var across = Vector3.ProjectOnPlane(right - left, up).normalized;
            var front = Vector3.Cross(across, up).normalized;
            float scale = Mathf.Abs(hero.Root.transform.lossyScale.x);
            var torsoCentre = (pelvis + shoulderMid) * .5f;
            float width = Vector3.Distance(left, right) * .52f + .025f * scale;
            float depth = .155f * scale;
            float height = Vector3.Distance(pelvis, shoulderMid) * .5f + .075f * scale;
            var outward = side == "Left" ? -across : across;
            var preferred = Vector3.ProjectOnPlane(relaxed ? front * .5f + outward * .8f - up : front + outward * .3f + up * .3f, wristAxis).normalized;
            if (preferred.sqrMagnitude < .1f) preferred = authoredBend;
            if (relaxed) return Vector3.Slerp(authoredBend, preferred, blend).normalized;
            var reference = Vector3.Slerp(authoredBend, preferred, blend * .8f).normalized;

            float Penetration(Vector3 point)
            {
                var p = point - torsoCentre;
                float x = Vector3.Dot(p, across) / width;
                float y = Vector3.Dot(p, up) / height;
                float z = Vector3.Dot(p, front) / depth;
                float inside = Mathf.Max(0, 1 - x*x - y*y - z*z);
                return inside*inside;
            }
            float Cost(float degrees)
            {
                var direction = Quaternion.AngleAxis(degrees, wristAxis) * reference;
                var elbow = elbowCentre + direction * elbowRadius;
                float penetration = 0;
                // Both segments matter: an elbow outside the chest can still leave
                // the upper arm or forearm cutting through it.
                for (int i = 1; i <= 4; i++)
                {
                    penetration += Penetration(Vector3.Lerp(shoulder, elbow, i / 4f));
                    penetration += Penetration(Vector3.Lerp(elbow, wrist, i / 5f));
                }
                return penetration * 100 + (1-Vector3.Dot(direction, preferred))*.25f + degrees*degrees*.000006f;
            }
            float bestAngle = 0, bestCost = Cost(0);
            for (int angle = -170; angle <= 170; angle += 10)
            {
                float cost = Cost(angle);
                if (cost < bestCost) { bestCost = cost; bestAngle = angle; }
            }
            // Refine within the selected interval so elbows do not move in 10-degree steps.
            float lower = bestAngle-10, upper = bestAngle+10;
            for (int i = 0; i < 10; i++)
            {
                float a = Mathf.Lerp(lower, upper, 1f/3), b = Mathf.Lerp(lower, upper, 2f/3);
                if (Cost(a) < Cost(b)) upper = b; else lower = a;
            }
            var clearBend = Quaternion.AngleAxis((lower+upper)*.5f, wristAxis) * reference;
            return Vector3.Slerp(authoredBend, clearBend, blend).normalized;
        }

        void SolveTo(string side, Vector3 target, Quaternion rotation, float elbowBlend = 0, bool relaxed = false, bool smooth = false)
        {
            var upper = hero.Bones[side + "UpperArm"]; var lower = hero.Bones[side + "LowerArm"]; var hand = hero.Bones[side + "Hand"];
            Vector3 root = upper.position, delta = target - root;
            float a = Vector3.Distance(root, lower.position), b = Vector3.Distance(lower.position, hand.position);
            float d = Mathf.Clamp(delta.magnitude, Mathf.Abs(a-b)+.0001f, a+b-.0001f);
            var forward = delta.normalized;
            var bend = Vector3.ProjectOnPlane(lower.position-root, forward).normalized;
            if (bend.sqrMagnitude < .1f) bend = Vector3.ProjectOnPlane(upper.forward, forward).normalized;
            float along = (a*a-b*b+d*d)/(2*d);
            float elbowRadius = Mathf.Sqrt(Mathf.Max(0, a*a-along*along));
            var elbowCentre = root + forward*along;
            if (elbowBlend > 0 && elbowRadius > .0001f)
                bend = BendAroundTorso(side, root, target, elbowCentre, elbowRadius, forward, bend, elbowBlend, relaxed);
            if (smooth)
            {
                int index = side == "Left" ? 0 : 1;
                if (restingBendKnown[index]) bend = Vector3.ProjectOnPlane(Vector3.RotateTowards(restingBend[index], bend, (restingBendFrame[index] == Time.frameCount ? 0 : 180f * Mathf.Deg2Rad * Mathf.Min(Time.deltaTime, .05f)), 0), forward).normalized;
                restingBend[index] = bend; restingBendKnown[index] = true; restingBendFrame[index] = Time.frameCount;
            }
            var elbow = elbowCentre + bend*elbowRadius;
            if (smooth && postStartKnown)
            {
                // Parallel-transport the captured finish's bone frames. Reusing each freshly
                // evaluated swing frame's roll makes the shoulder/forearm torque against the IK.
                int sideIndex = side == "Left" ? 0 : 1;
                upper.rotation = Quaternion.FromToRotation(postSpace.TransformDirection(postUpperVector[sideIndex]), elbow-root) * postSpace.rotation * postUpperRotation[sideIndex];
                lower.rotation = Quaternion.FromToRotation(postSpace.TransformDirection(postLowerVector[sideIndex]), target-lower.position) * postSpace.rotation * postLowerRotation[sideIndex];
                var axis = (hand.position-lower.position).normalized;
                var neutralHand = lower.rotation * postWristRelative[sideIndex];
                var difference = rotation * Quaternion.Inverse(neutralHand);
                var axial = Vector3.Dot(new Vector3(difference.x,difference.y,difference.z),axis);
                if (postTransportFrame[sideIndex] != Time.frameCount)
                {
                    // Incremental transport has no antipodal flip when a forearm travels far
                    // from its starting direction. Keep the untwisted frame for the next tick.
                    postUpperRotation[sideIndex]=Quaternion.Inverse(postSpace.rotation)*upper.rotation;
                    postLowerRotation[sideIndex]=Quaternion.Inverse(postSpace.rotation)*lower.rotation;
                    postUpperVector[sideIndex]=postSpace.InverseTransformDirection(elbow-root);
                    postLowerVector[sideIndex]=postSpace.InverseTransformDirection(target-lower.position);
                    if (axial*axial+difference.w*difference.w > 1e-8f)
                    {
                        float raw=2*Mathf.Atan2(axial,difference.w)*Mathf.Rad2Deg;
                        postTwistTarget[sideIndex]+=Mathf.DeltaAngle(postTwistTarget[sideIndex],raw);
                    }
                    postTwist[sideIndex]=Mathf.SmoothDamp(postTwist[sideIndex],postTwistTarget[sideIndex]*.8f,ref postTwistVelocity[sideIndex],.16f,180f,Mathf.Min(Time.deltaTime,.05f));
                    postTransportFrame[sideIndex]=Time.frameCount;
                }
                lower.rotation=Quaternion.AngleAxis(postTwist[sideIndex],axis)*lower.rotation;
            }
            else
            {
                upper.rotation = Quaternion.FromToRotation(lower.position-root, elbow-root)*upper.rotation;
                lower.rotation = Quaternion.FromToRotation(hand.position-lower.position, target-lower.position)*lower.rotation;
            }
            hand.rotation = rotation;
        }
    }
}
