import sys
p=sys.argv[1]; s=open(p).read()
if "ARM LIMITS" in s: print("export hook already there:", p); sys.exit()
a="            if (clip.name != RelaxedName) HeroGripPolish.ApplyGrip(root.GetComponent<MatchHeroLook>());   // the plaza's relaxed stand carries no racket grip"
assert a in s, "SamplePose grip line not found"
s=s.replace(a,"""            // ARM LIMITS 2026-11-13 (work/final-plan-1111/anim): the game ends its pose pass with the anatomical wrist / elbow rule (HeroPoseSafety,
            // HeroArmLimits); the menus get the same on every clip frame, before the finger polish as in the game. ARM_LIMITS=0 = without.
            if (clip.name != RelaxedName) ArmLimitsFor(root)?.ArmLimits(true);
"""+a)
b="        static Transform FindBone(Transform root, string name) =>"
assert b in s
s=s.replace(b,"""        static readonly Dictionary<GameObject, HeroPoseSafety> armLimits = new Dictionary<GameObject, HeroPoseSafety>();
        static HeroPoseSafety ArmLimitsFor(GameObject root)
        {
            if (!HeroArmLimits.Enabled || !root) return null;
            if (armLimits.TryGetValue(root, out var s) && s != null) return s;
            var look = root.GetComponent<MatchHeroLook>(); if (!look) return null;
            if (armLimits.Count > 16) armLimits.Clear();
            return armLimits[root] = new HeroPoseSafety(look);
        }
"""+b)
open(p,"w").write(s); print("export hooked:", p)
