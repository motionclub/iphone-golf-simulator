"""Human-requested side-on stagger and natural dribble, private preview only."""
from pathlib import Path
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-toss-jump';C=W/'UnityClone'
p=C/'Assets/Scripts/Tennis/HeroTennisDriver.cs';s=p.read_text()
a=s.index('        void LockFeet(float dt)');b=s.index('        static float ClearScale',a);m=s[a:b]
needle='            // The authored Serve owns'
insertion='''            // A platform serve has a front left foot and a rear right foot.
            // Keep the pelvis side-on through the ritual, then release the turn
            // into the authored drive. Each leg has its own plant and knee plane.
            float stanceAlign = authoredServe ? 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(ServeTrophyT, 1.57f, (float)actionTime)) : 0;
            if (stanceAlign > 0)
            {
                var right = Vector3.ProjectOnPlane(Bone(HumanBodyBones.RightUpperLeg).position - Bone(HumanBodyBones.LeftUpperLeg).position, actor.transform.up);
                float turn = Vector3.SignedAngle(right, -actor.transform.forward, actor.transform.up);
                hips.rotation = Quaternion.AngleAxis(turn * stanceAlign, actor.transform.up) * hips.rotation;
            }
            void SolvePlant(Transform up, Transform lo, Transform end, Vector3 target, Vector3 forward)
            {
                float l1 = Vector3.Distance(up.position, lo.position), l2 = Vector3.Distance(lo.position, end.position);
                Vector3 dir = (target - up.position).normalized;
                float d = Mathf.Clamp(Vector3.Distance(target, up.position), Mathf.Abs(l1 - l2) + .001f, l1 + l2 - .001f);
                var pole = Vector3.ProjectOnPlane(forward, dir).normalized;
                if (pole.sqrMagnitude < .0001f) return;
                float along = (l1*l1 - l2*l2 + d*d)/(2*d), height = Mathf.Sqrt(Mathf.Max(0, l1*l1 - along*along));
                Vector3 knee = up.position + dir*along + pole*height;
                up.rotation = Quaternion.FromToRotation(lo.position-up.position, knee-up.position)*up.rotation;
                lo.rotation = Quaternion.FromToRotation(end.position-lo.position, up.position+dir*d-lo.position)*lo.rotation;
            }
'''
assert needle in m;m=m.replace(needle,insertion+needle,1)
old='                        lockPos[f] = foot.position; stepFrom[f] = toe.position;'
new='''                        var anchor = actor.transform.TransformPoint(new Vector3(f == 0 ? .14f : -.14f, 0, f == 0 ? .25f : -.25f));
                        lockPos[f] = new Vector3(anchor.x, foot.position.y, anchor.z);
                        float toeYaw = (f == 0 ? 45 : 80) * Mathf.Deg2Rad;
                        var toeForward = actor.transform.TransformDirection(new Vector3(Mathf.Sin(toeYaw), 0, Mathf.Cos(toeYaw)));
                        stepFrom[f] = lockPos[f] + toeForward * Vector3.Distance(foot.position, toe.position);'''
assert old in m;m=m.replace(old,new,1)
old='                TwoBone(upper, lower, foot, target);'
new='''                if (authoredServe && locked[f]) SolvePlant(upper, lower, foot, target, Flat(stepFrom[f] - lockPos[f]));
                else TwoBone(upper, lower, foot, target);'''
assert old in m;m=m.replace(old,new,1);s=s[:a]+m+s[b:]
s=s.replace('            carryTravel = -actor.transform.right;', '            carryTravel = carry ? -actor.transform.right : forward;')
s=s.replace('                Vector3 fingers = carryTravel;', '                Vector3 fingers = (carryTravel - Vector3.up * .75f).normalized;')
old='''                hand.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(gripNormal, Vector3.ProjectOnPlane(view, fingers).normalized, fingers), fingers) * hand.rotation;'''
new='''                // Palm down for the push/catch; no camera-facing wrist inversion.
                var palmDown = Vector3.ProjectOnPlane(-Vector3.up, fingers).normalized;
                hand.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(gripNormal, palmDown, fingers), fingers) * hand.rotation;'''
assert old in s;s=s.replace(old,new,1)
s=s.replace('                float clearRoll = opponentServer ?', '                float clearRoll = false ?')
s=s.replace('            if (pre && prepare <= .001f) gripOffset = (carryTravel * .5f + normal * .8660254f).normalized * .034f;', '            if (pre && prepare <= .001f) gripOffset = Vector3.down * .034f;')
s=s.replace('            Vector3 offset = pre && prepare <= .001f ? -normal * .03f :', '            Vector3 offset = pre && prepare <= .001f ? Vector3.up * .034f :')
s=s.replace('            if (pre && prepare <= .001f) wanted = lowWrist;', '''            if (pre && prepare <= .001f)
            {
                wanted = lowWrist;
                if (!carry) wanted.y += wantedPalm.y - TennisServeRoutine.Hold(actor).y;
            }''')
s=s.replace('side * .9f + forward * .4f - Vector3.up * .15f', 'side * .25f + forward * .1f - Vector3.up * .85f')
p.write_text(s)
p=C/'Assets/Editor/ServeJumpProof.cs';s=p.read_text();s=s.replace('bool picture = frame % 2 == 0 && Env("SJ_CAPTURE", "1") == "1";', 'bool picture = frame % 2 == 0 && Env("SJ_CAPTURE", "1") == "1" && Env("SJ_KEY_ONLY", "0") != "1";');p.write_text(s)
(W/'r4/LockFeet_trial.cs.txt').write_text(m)
print('Applied side-on stagger, independent knee planes, palm-down dribble and forward ball-side trial inside private clone.')
