import sys
p=sys.argv[1]; s=open(p).read()
if "HeroArmLimits" in s: print("hook already there:", p); sys.exit()
a="            try { ApplyTimed(lockWrists, freeLeftHand, gripFreedom, twoHanded); }"
assert a in s, "Apply line not found"
s=s.replace(a,"            try { ApplyTimed(lockWrists, freeLeftHand, gripFreedom, twoHanded); ArmLimits(lockWrists, freeLeftHand, gripFreedom, twoHanded); }")
b="        void ApplyTimed(bool lockWrists, bool freeLeftHand, float gripFreedom, bool twoHanded)"
assert b in s
s=s.replace(b,"""        /// ARM LIMITS 2026-11-12/13 (work/final-plan-1111/anim): the anatomical wrist and elbow rule, last, on whatever the clip, the baked
        /// track and the solve left (HeroArmLimits). A hand on the racket or club keeps its place; two hands on one grip keep their rotation
        /// too. Public for tools and the menu export, which pose clips without the rest of this pass. ARM_LIMITS=0 switches it off.
        float DepthAt(Vector3 point, float radius) => Depth(point, radius, out _);
        public void ArmLimits(bool lockWrists, bool freeLeftHand = false, float gripFreedom = 0, bool twoHanded = false)
        {
            if (!HeroArmLimits.Enabled || !look) return;
            bool left = lockWrists && !freeLeftHand, right = lockWrists, ready = clearance != null && clearance.Ready;
            if (ready) { clearance.DetectGrip(twoHanded); left = clearance.HandHolds(0); right = clearance.HandHolds(1); }
            float freedom = left && right || lockWrists ? 0 : 1;   // (a stroke keeps the racket hand exactly as the clip has it)
            int supports = ready && left && right && clearance.HeldProp != null && clearance.TwoHandGrip ? 1 - clearance.HolderSide : -1;
            // the hand that steadies the racket keeps exactly to the clip while a tennis stroke is near contact (gripFreedom 0 there) and
            // eases in away from it; in golf the club is not carried by the hands' places, so the steadying hand is always free to settle
            float supportWeight = lockWrists && !look.golfKit ? Mathf.Clamp01(gripFreedom) : 1;
            HeroArmLimits.Apply(look, left, right, freedom, freedom, ready ? DepthAt : (Func<Vector3, float, float>)null, supports, supportWeight);
        }
"""+b)
open(p,"w").write(s); print("hooked:", p)
