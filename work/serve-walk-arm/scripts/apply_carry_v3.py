from pathlib import Path
import sys
repo=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
base=(repo/'work/serve-walk-arm/rollback/Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text()
base=base.replace('if (Match) BuildServeRitualPoints();','if (Match) { BuildServeRitualPoints(); BuildMatchWalkCarry(); }')
a='''            if (Match) return tossPoints != null ? Quaternion.Euler(0, serveYaw + walkYaw, 0) * tossPoints[Mathf.Clamp(k, 0, 2)] : (Vector3?)null;   // read off the Serve clip's tossing hand (BuildServeRitualPoints)'''
b='''            if (Match)
            {
                if (tossPoints == null) return null;
                if (k == 0)
                {
                    UpdateMatchWalkCarry();
                    if (matchCarryT > .001f)
                    {
                        float w = Mathf.SmoothStep(0, 1, matchCarryT);
                        // Follow the outside/front of the body during the turn, rather than
                        // interpolating a chord from the serve's opposite-side hold through it.
                        Vector3 hold = tossPoints[0], carry = matchWalkCarry;
                        float gait = valid[(int)Clip.Walk] ? (float)time[(int)Clip.Walk] / length[(int)Clip.Walk] * Mathf.PI * 2 : 0;
                        carry.z += .035f * Mathf.Sin(gait);
                        float angle = Mathf.LerpAngle(Mathf.Atan2(hold.x, hold.z) * Mathf.Rad2Deg,
                            Mathf.Atan2(carry.x, carry.z) * Mathf.Rad2Deg, w) * Mathf.Deg2Rad;
                        float radius = Mathf.Lerp(new Vector2(hold.x, hold.z).magnitude, new Vector2(carry.x, carry.z).magnitude, w);
                        Vector3 ball = new Vector3(Mathf.Sin(angle) * radius, Mathf.Lerp(hold.y, carry.y, w), Mathf.Cos(angle) * radius);
                        ball = ClearMatchCarryBall(ball);
                        float yawTo = WalkMode() && Moving() > .25f ? Mathf.Atan2(actor.Speed, actor.ForwardSpeed) * Mathf.Rad2Deg : 0;
                        float yaw = Mathf.MoveTowardsAngle(walkYaw, yawTo, Time.deltaTime * 420f);
                        return Quaternion.Euler(0, yaw, 0) * ball;
                    }
                }
                return Quaternion.Euler(0, serveYaw + walkYaw, 0) * tossPoints[Mathf.Clamp(k, 0, 2)];
            }'''
assert a in base
base=base.replace(a,b)
a='''            Vector3 goal = ball + Vector3.up * (bouncing ? .045f : -.045f);
            var hr = hand.rotation;
            TwoBone(up, lo, hand, Vector3.Lerp(hand.position, hand.position + (goal - palm), tossWeight));'''
b='''            float carrying = Match ? Mathf.SmoothStep(0, 1, matchCarryT) : 0;
            Vector3 goal = ball + Vector3.up * (bouncing ? Mathf.Lerp(.045f, .02f, carrying) : -.045f);
            var hr = hand.rotation;
            Vector3 wristGoal = Vector3.Lerp(hand.position, hand.position + (goal - palm), tossWeight);
            if (carrying > .001f) MatchCarryArm(up, lo, hand, wristGoal, carrying);
            else TwoBone(up, lo, hand, wristGoal);'''
assert a in base
base=base.replace(a,b)
needle='''        static readonly Vector3 CarryPoint = new Vector3(-.3f, .66f, .08f);'''
insert='''        // Match-only walking carry. The installed match clips use the left tossing arm;
        // keep their planted serve untouched, including the current left-handed visual mapping.
        Vector3 matchWalkCarry; float matchCarryT; int matchCarryFrame = -1;
        void BuildMatchWalkCarry()
        {
            int walk = (int)Clip.Walk; if (!valid[walk]) { matchWalkCarry = new Vector3(-.36f, .8f, .1f); return; }
            for (int k = 0; k < Count; k++) if (valid[k]) { mixer.SetInputWeight(k, k == walk ? 1 : 0); playables[k].SetTime(k == walk ? length[walk] * .25f : 0); }
            graph.Evaluate(0);
            var up = Bone(HumanBodyBones.LeftUpperArm); var lo = Bone(HumanBodyBones.LeftLowerArm);
            var hand = Bone(HumanBodyBones.LeftHand); var mid = Bone(HumanBodyBones.LeftMiddleProximal);
            Vector3 palm = transform.InverseTransformPoint(mid ? Vector3.Lerp(hand.position, mid.position, .7f) : hand.position);
            Vector3 shoulder = transform.InverseTransformPoint(up.position);
            float span = Vector3.Distance(up.position, lo.position) + Vector3.Distance(lo.position, hand.position);
            // Use the Walk hand's palm offset and the real limb length. Lower the wrist with
            // a soft bend, and move it out from the hip; never scale or lengthen the bones.
            float palmY = palm.y - transform.InverseTransformPoint(hand.position).y;
            matchWalkCarry = new Vector3(Mathf.Min(palm.x, shoulder.x - .15f), shoulder.y - span * .91f + palmY - .02f, Mathf.Max(.28f, palm.z));
        }
        void UpdateMatchWalkCarry()
        {
            if (matchCarryFrame == Time.frameCount) return; matchCarryFrame = Time.frameCount;
            bool movingCarry = actor.PrepareServe && actor.PrepareAmount <= .001f && !actor.Swinging && Moving() > .2f;
            matchCarryT = Mathf.MoveTowards(matchCarryT, movingCarry ? 1 : 0, Time.deltaTime / .30f);
        }
        Vector3 ClearMatchCarryBall(Vector3 local)
        {
            Vector3 h = transform.InverseTransformPoint(Bone(HumanBodyBones.Hips).position);
            Vector3 s = transform.InverseTransformPoint(Bone(HumanBodyBones.Spine).position);
            Vector3 c = transform.InverseTransformPoint(Bone(HumanBodyBones.Chest).position);
            // These conservative envelopes guard the goal only during the carry/turn blend.
            // Their outcome is checked against BakeMesh, not counted as mesh proof.
            for (int pass = 0; pass < 2; pass++)
            {
                local = OutsideCarryCapsule(local, h, s, .17f + TennisRules.BallRadius);
                local = OutsideCarryCapsule(local, s, c, .17f + TennisRules.BallRadius);
                foreach (var leg in new[] { HumanBodyBones.LeftUpperLeg, HumanBodyBones.RightUpperLeg })
                {
                    var thigh = Bone(leg); var knee = Bone(leg == HumanBodyBones.LeftUpperLeg ? HumanBodyBones.LeftLowerLeg : HumanBodyBones.RightLowerLeg);
                    local = OutsideCarryCapsule(local, transform.InverseTransformPoint(thigh.position), transform.InverseTransformPoint(knee.position), .1f + TennisRules.BallRadius);
                }
            }
            return local;
        }
        static Vector3 OutsideCarryCapsule(Vector3 p, Vector3 a, Vector3 b, float radius)
        {
            Vector3 axis = b - a; float t = axis.sqrMagnitude > 1e-8f ? Mathf.Clamp01(Vector3.Dot(p - a, axis) / axis.sqrMagnitude) : 0;
            Vector3 centre = a + axis * t, away = p - centre;
            return away.sqrMagnitude >= radius * radius ? p : centre + (away.sqrMagnitude > 1e-8f ? away.normalized : Vector3.forward) * radius;
        }
        void MatchCarryArm(Transform up, Transform lo, Transform hand, Vector3 target, float carry)
        {
            float upper = Vector3.Distance(up.position, lo.position), lower = Vector3.Distance(lo.position, hand.position);
            Vector3 delta = target - up.position;
            float d = Mathf.Clamp(delta.magnitude, Mathf.Abs(upper - lower) + .001f, upper + lower - .001f);
            Vector3 direction = delta.normalized;
            Vector3 authoredPole = Vector3.ProjectOnPlane(lo.position - up.position, direction).normalized;
            Vector3 side = Vector3.ProjectOnPlane(up.position - Bone(HumanBodyBones.RightUpperArm).position, Vector3.up).normalized;
            Vector3 forward = Vector3.Cross(Vector3.up, side);
            Vector3 outsidePole = Vector3.ProjectOnPlane(side * .9f + forward * .4f - Vector3.up * .15f, direction).normalized;
            Vector3 pole = outsidePole;
            if (pole.sqrMagnitude < 1e-6f) pole = outsidePole;
            float along = (upper * upper - lower * lower + d * d) / (2 * d);
            Vector3 elbow = up.position + direction * along + pole.normalized * Mathf.Sqrt(Mathf.Max(0, upper * upper - along * along));
            up.rotation = Quaternion.FromToRotation(lo.position - up.position, elbow - up.position) * up.rotation;
            lo.rotation = Quaternion.FromToRotation(hand.position - lo.position, up.position + direction * d - lo.position) * lo.rotation;
        }
'''
assert needle in base
base=base.replace(needle,insert+'\n'+needle)
target=Path(sys.argv[1])/'Assets/Scripts/Tennis/HeroTennisDriver.cs'
target.write_text(base)
print(target)
