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
        readonly Transform[][] fingerSamples = new Transform[2][];
        Vector3 chestForward = Vector3.forward;
        public float ResidualDepth { get; private set; }
        public int VolumeCount => volumes.Count;
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
            fingerSamples[0] = new[] { look.Bone(HumanBodyBones.LeftMiddleProximal), look.Bone(HumanBodyBones.LeftMiddleDistal), look.Bone(HumanBodyBones.LeftIndexDistal), look.Bone(HumanBodyBones.LeftLittleDistal) };
            fingerSamples[1] = new[] { look.Bone(HumanBodyBones.RightMiddleProximal), look.Bone(HumanBodyBones.RightMiddleDistal), look.Bone(HumanBodyBones.RightIndexDistal), look.Bone(HumanBodyBones.RightLittleDistal) };
            var skin = look.body;
            if (!skin || !skin.sharedMesh || !skin.sharedMesh.isReadable) return;
            var mesh = skin.sharedMesh; var vertices = mesh.vertices;
            var weights = mesh.boneWeights; var bind = mesh.bindposes;
            var palette = skin.bones;
            int chestIndex = Array.FindIndex(palette, b => b && b.name == "Chest");
            if (chestIndex >= 0) chestForward = bind[chestIndex].MultiplyVector(new Vector3(0, -1, 0)).normalized;
            // Arm-volume supports encode torso influence too. Ignoring that mass
            // produced a narrow chest proxy with holes at the female armholes.
            var supportA=new int[palette.Length];var supportB=new int[palette.Length];var supportT=new float[palette.Length];
            for(int i=0;i<palette.Length;i++) {
                supportA[i]=supportB[i]=i;
                string n=palette[i]?palette[i].name:"";
                if(!n.StartsWith("ArmBlend_"))continue;
                var parts=n.Split('_');supportA[i]=int.Parse(parts[1]);supportB[i]=int.Parse(parts[2]);supportT[i]=int.Parse(parts[3])/8f;
            }
            float Influence(int bone,int target)=>(supportA[bone]==target?1-supportT[bone]:0)+(supportB[bone]==target?supportT[bone]:0);
            foreach (var name in new[] { "Hips", "Spine", "Chest", "UpperChest", "Neck", "Head" })
            {
                int index = Array.FindIndex(skin.bones, b => b && b.name == name);
                if (index < 0) continue;
                Bounds bounds = default; int count = 0;
                for (int i = 0; i < vertices.Length; i++)
                {
                    var w = weights[i];
                    float amount = Influence(w.boneIndex0, index) * w.weight0 + Influence(w.boneIndex1, index) * w.weight1
                        + Influence(w.boneIndex2, index) * w.weight2 + Influence(w.boneIndex3, index) * w.weight3;
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
            // The skirt has a wider envelope than skin at hip height. Keep idle
            // hands and a travelling grip outside the garment as well as the body.
            if(look.female && look.kitV2 && !look.golfKit) {
                int h=Array.FindIndex(palette,b=>b&&b.name=="Hips");
                if(h>=0) {
                    var r=new Vector3(.22f,.155f,.14f);var bounds=new Bounds(bind[h].MultiplyPoint3x4(new Vector3(0,0,.82f)),Vector3.zero);
                    for(int x=-1;x<=1;x+=2)for(int y=-1;y<=1;y+=2)for(int z=-1;z<=1;z+=2)
                        bounds.Encapsulate(bind[h].MultiplyPoint3x4(new Vector3(x*r.x,y*r.y,.82f+z*r.z)));
                    volumes.Add(new Volume{bone=palette[h],centre=bounds.center,radius=bounds.extents});
                }
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
                float d = Depth(Vector3.Lerp(shoulder, elbow, k / 5f), .043f, out _);
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
        public void Apply(bool lockWrists, bool freeLeftHand = false, float gripFreedom = 0, bool twoHanded = false)
        {
            ResidualDepth = 0;
            Refresh();
            if(lockWrists && twoHanded && look.female && !look.golfKit) BalanceUnderGrip();
            SolveArm(false, lockWrists && !freeLeftHand); SolveArm(true, lockWrists);
            if (!lockWrists || freeLeftHand) NudgeGrips(false, false, .10f);
            if (!lockWrists) NudgeGrips(true, false, .10f);
            else if (gripFreedom > 0) NudgeGrips(true, twoHanded, .10f * Mathf.Clamp01(gripFreedom));
            if (!lockWrists) ClearRacket();
            ResidualDepth = MeasureArmDepth();
        }

        // A low two-hand stroke needs room in front of the skirt. A small
        // weight shift makes that room without moving the racket contact or feet.
        void BalanceUnderGrip()
        {
            var hips=look.Bone(HumanBodyBones.Hips);
            var ru=look.Bone(HumanBodyBones.RightUpperArm);var rl=look.Bone(HumanBodyBones.RightLowerArm);var rh=look.Bone(HumanBodyBones.RightHand);
            var lu=look.Bone(HumanBodyBones.LeftUpperArm);var ll=look.Bone(HumanBodyBones.LeftLowerArm);var lh=look.Bone(HumanBodyBones.LeftHand);
            var rlu=look.Bone(HumanBodyBones.RightUpperLeg);var rll=look.Bone(HumanBodyBones.RightLowerLeg);var rf=look.Bone(HumanBodyBones.RightFoot);
            var llu=look.Bone(HumanBodyBones.LeftUpperLeg);var lll=look.Bone(HumanBodyBones.LeftLowerLeg);var lf=look.Bone(HumanBodyBones.LeftFoot);
            float right=Depth(rh.position,.05f,out var push);float left=Depth(lh.position,.05f,out var other);
            if(left>right)push=other;if(Mathf.Max(left,right)<.003f)return;
            var shift=Vector3.ClampMagnitude(Vector3.ProjectOnPlane(-push,look.transform.up),.06f);
            shift-=look.transform.up*Mathf.Min(.008f,shift.sqrMagnitude/.8f);
            bool Fits(Transform upper,Transform lower,Transform end)=>Vector3.Distance(upper.position+shift,end.position)<Vector3.Distance(upper.position,lower.position)+Vector3.Distance(lower.position,end.position)-.00002f;
            for(int i=0;i<10&&(!Fits(ru,rl,rh)||!Fits(lu,ll,lh)||!Fits(rlu,rll,rf)||!Fits(llu,lll,lf));i++)shift*=.5f;
            if(shift.sqrMagnitude<1e-8f)return;
            var joints=new[]{ru,rl,rh,lu,ll,lh,rlu,rll,rf,llu,lll,lf};var rotations=new Quaternion[joints.Length];
            for(int i=0;i<joints.Length;i++)rotations[i]=joints[i].localRotation;
            var hipPosition=hips.localPosition;var rp=rh.position;var lp=lh.position;var rfp=rf.position;var lfp=lf.position;
            var rr=rh.rotation;var lr=lh.rotation;var rfr=rf.rotation;var lfr=lf.rotation;
            float before=ArmCost(ru.position,rl.position,rp)+ArmCost(lu.position,ll.position,lp);
            hips.position+=shift;
            Solve(ru,rl,rh,rp);rh.rotation=rr;Solve(lu,ll,lh,lp);lh.rotation=lr;
            Solve(rlu,rll,rf,rfp);rf.rotation=rfr;Solve(llu,lll,lf,lfp);lf.rotation=lfr;
            Refresh();
            float after=ArmCost(ru.position,rl.position,rh.position)+ArmCost(lu.position,ll.position,lh.position);
            if(after>=before){hips.localPosition=hipPosition;for(int i=0;i<joints.Length;i++)joints[i].localRotation=rotations[i];Refresh();}
        }

        // Elbow swivelling alone cannot solve a wrist target buried behind the
        // chest. Away from impact, carry the whole grip a bounded distance out.
        // Two-handed strokes share exactly the same translation on both wrists.
        void NudgeGrips(bool right, bool both, float limit)
        {
            var upper = look.Bone(right ? HumanBodyBones.RightUpperArm : HumanBodyBones.LeftUpperArm);
            var lower = look.Bone(right ? HumanBodyBones.RightLowerArm : HumanBodyBones.LeftLowerArm);
            var hand = look.Bone(right ? HumanBodyBones.RightHand : HumanBodyBones.LeftHand);
            if (!upper || !lower || !hand) return;
            var otherUpper = look.Bone(HumanBodyBones.LeftUpperArm);
            var otherLower = look.Bone(HumanBodyBones.LeftLowerArm);
            var otherHand = look.Bone(HumanBodyBones.LeftHand);
            var origin = hand.position; var otherOrigin = otherHand.position;
            var rotation = hand.rotation; var otherRotation = otherHand.rotation;
            float HandCost(bool rightHand) {
                float cost=0;
                foreach(var finger in fingerSamples[rightHand?1:0])if(finger){float d=Depth(finger.position,.023f,out _);cost+=d*d;}
                return cost;
            }
            float Cost() => ArmCost(upper.position, lower.position, hand.position) + HandCost(right)
                + (both ? ArmCost(otherUpper.position, otherLower.position, otherHand.position)+HandCost(false) : 0);
            Vector3 Push(Transform u, Transform l, Transform h) {
                float worst = 0; var result = Vector3.zero;
                for (int k=2;k<=10;k++) {
                    Vector3 p = k<=5 ? Vector3.Lerp(u.position,l.position,k/5f) : Vector3.Lerp(l.position,h.position,(k-5)/5f);
                    float d = Depth(p,k<=5?.043f:.032f,out var push);
                    if (d>worst) {worst=d;result=push;}
                }
                foreach(var finger in fingerSamples[h==look.Bone(HumanBodyBones.RightHand)?1:0])if(finger) {
                    float d=Depth(finger.position,.023f,out var push);if(d>worst){worst=d;result=push;}
                }
                return result;
            }
            for(int pass=0;pass<5;pass++) {
                float before=Cost();if(before<.0000005f)break;
                var push=Push(upper,lower,hand);
                if(both){var p=Push(otherUpper,otherLower,otherHand);if(p.sqrMagnitude>push.sqrMagnitude)push=p;}
                var shift=Vector3.ClampMagnitude(hand.position-origin+push*1.5f,limit);
                bool Reachable(Transform u,Transform l,Transform h,Vector3 target) {
                    float a=Vector3.Distance(u.position,l.position),b=Vector3.Distance(l.position,h.position),d=Vector3.Distance(u.position,target);
                    return d<=a+b+.000001f && d>=Mathf.Abs(a-b);
                }
                for(int i=0;i<10 && (!Reachable(upper,lower,hand,origin+shift) || both&&!Reachable(otherUpper,otherLower,otherHand,otherOrigin+shift));i++)shift*=.5f;
                var u0=upper.rotation;var l0=lower.rotation;var ou0=otherUpper.rotation;var ol0=otherLower.rotation;
                Solve(upper,lower,hand,origin+shift);hand.rotation=rotation;SolveArm(right,true);
                if(both){Solve(otherUpper,otherLower,otherHand,otherOrigin+shift);otherHand.rotation=otherRotation;SolveArm(false,true);}
                if(Cost()>=before) {
                    upper.rotation=u0;lower.rotation=l0;hand.rotation=rotation;
                    if(both){otherUpper.rotation=ou0;otherLower.rotation=ol0;otherHand.rotation=otherRotation;}
                    break;
                }
            }
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
                    float behind = chest ? Mathf.Max(0, -Vector3.Dot(e - chest.position, chest.TransformDirection(chestForward))) : 0;
                    return ArmCost(shoulder, e, wrist) * 100000f + behind * behind + angle * angle * .000001f;
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
