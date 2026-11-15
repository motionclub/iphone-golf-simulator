#!/bin/bash
# install_clone_her.sh [clone]: her walk / hands / arm fixes as patches to a PROJECT COPY (never the shared project). Idempotent.
# Each fix has an Editor switch so before and after can be filmed from one build:
#   CLEARANCE_FreeArmShare=1   the baked arm clearance at full strength again (the flared "bug" arms)
#   FEMALE_WALK_CURL=0         no relaxed finger curl while she walks
#   HERO_ARM_GAIN=2            the 11-11 forearm build
#   PLAZA_ELBOW=0              the clips' own bent elbows
#   PLAZA_WRIST=0              the clips' own dropping wrist
#   FEMALE_WRIST_TAPER=0       the 10-27 wrist (widened 22 %)
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/${1:-final-plan-dev}/Unity/Assets/Scripts
[ -d "$C" ] || { echo "no clone at $C"; exit 1; }
case "$C" in "$REPO"*) echo "refusing: that is the shared project"; exit 1;; esac
python3 - "$C" <<'PY'
import sys
c = sys.argv[1]
def patch(f, a, b):
    s = open(f).read()
    if b in s: print("already patched:", f.split("/")[-1]); return
    assert s.count(a) == 1, (f, a[:60]); open(f, "w").write(s.replace(a, b)); print("patched:", f.split("/")[-1])
T = c + "/Tennis/HeroClearanceTracks.cs"
patch(T, "        public static bool Enabled = true;\n",
"""        public static bool Enabled = true;
        /// HER WALK 2026-11-12 (Adnan: "when she walks she looks like a bug not a human"). The tracks were baked to carry every hand
        /// clear of the tennis skirt's flared hem, and the plaza plays them for every kit: both arms were held out from the body with
        /// bent elbows through the whole walk, in trousers too. An arm whose hand holds nothing now takes this share of its baked
        /// correction: enough to keep the hand off the hip and thigh, while the swing stays the clip's own. A hand on a racket or
        /// club is unchanged. CLEARANCE_FreeArmShare=1 (Editor) restores the full correction.
        public static float FreeArmShare = float.TryParse(Environment.GetEnvironmentVariable("CLEARANCE_FreeArmShare"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var fas) ? fas : .40f;
""")
patch(T, "                    if (Quaternion.Angle(d, Quaternion.identity) < .01f) continue;\n                    t.localRotation = t.localRotation * d; Applied++;\n",
"""                    if (Quaternion.Angle(d, Quaternion.identity) < .01f) continue;
                    for (int s = 0; s < 2 && FreeArmShare < 1; s++)
                        if (freeHand[s] && arm[s * 3] && (t == arm[s * 3] || t == arm[s * 3 + 1] || t == arm[s * 3].parent)) d = Quaternion.Slerp(Quaternion.identity, d, FreeArmShare);
                    t.localRotation = t.localRotation * d; Applied++;
""")
H = c + "/Hub/HubHeroAnimator.cs"
patch(H, "            if (stanceShown == PalmsOnHipsStance && stanceWeight > .99f) PalmsOnRealHips();\n",
"""            // HER HANDS 2026-11-12: walking and running, her empty hands kept the clip's fingers, straight and spread (a rake). They take
            // the same relaxed curl as the standing hand. FEMALE_WALK_CURL=0 (Editor) switches it off, a number sets the amount.
            if (look.female && actionFade < .01f && SeatWeight < .001f && RelaxWeight < .5f && !bowlClip)
            {
                float curl = float.TryParse(System.Environment.GetEnvironmentVariable("FEMALE_WALK_CURL"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var fc) ? fc : 1f;
                if (curl > 0) { CurlFingers(true, curl, WalkMore, 18f, 30f, 15f); CurlFingers(false, curl, WalkMore, 18f, 30f, 15f); }
            }
            if (stanceShown == PalmsOnHipsStance && stanceWeight > .99f) PalmsOnRealHips();
""")
patch(H, "        void CurlFingers(bool left, float curl)\n", "        /// HER HANDS 2026-11-12: the walking hand curls more evenly than the standing one (whose index stays nearly straight).\n        static readonly float[] WalkMore = { .8f, 1f, 1.1f, 1.2f };\n        void CurlFingers(bool left, float curl, float[] moreBy = null, float mcp = CurlMcp, float pip = CurlPip, float dip = CurlDip)\n")
patch(H, "                var start = (axis + across * FingerFan[k]).normalized; float more = FingerMore[k];\n                float a1 = CurlMcp * more * curl, a2 = a1 + CurlPip * more * curl, a3 = a2 + CurlDip * more * curl;\n",
         "                var start = (axis + across * FingerFan[k]).normalized; float more = (moreBy ?? FingerMore)[k];\n                float a1 = mcp * more * curl, a2 = a1 + pip * more * curl, a3 = a2 + dip * more * curl;\n")
patch(H, "            // HER HANDS 2026-11-12: walking and running, her empty hands kept the clip's fingers",
"""            // THE ELBOW 2026-11-12 (Adnan: "there's a clear break where her arm is bending downwards"): the Walk and Run clips carry the
            // arms like a jogger's, the elbow bent about 52 degrees the whole way round (46 to 61). His baked clearance happens to
            // straighten his to about 30; hers stays near 50, and on a slim arm that reads as a break. A free arm's elbow is eased
            // into a walking range (about 18 on the back swing, 29 at the front; his a little straighter) by turning the forearm about the elbow's own hinge.
            // PLAZA_ELBOW=0 (Editor) switches it off.
            if (!bowlClip && System.Environment.GetEnvironmentVariable("PLAZA_ELBOW") != "0")
            {
                float ease = Mathf.Clamp01(1 - RelaxWeight) * Mathf.Clamp01(1 - actionFade) * (SeatWeight < .001f ? 1 : 0);
                for (int s = 0; s < 2 && ease > .001f; s++)
                {
                    var ua = look.Bone(s == 0 ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm); var la = look.Bone(s == 0 ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
                    var hd = look.Bone(s == 0 ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand); if (!ua || !la || !hd) continue;
                    var up = (la.position - ua.position).normalized; var fo = (hd.position - la.position).normalized; float bend = Vector3.Angle(up, fo);
                    float want = look.female ? Mathf.Clamp(12f + (bend - 44f) * .45f, 10f, bend) : Mathf.Clamp(12f + (bend - 35f) * .7f, 10f, bend);   // (her clearance leaves her elbow about 10 degrees more bent than his: one range for both, about 12 to 19)
                    var hinge = Vector3.Cross(up, fo);
                    if (bend - want > .5f && hinge.sqrMagnitude > 1e-8f) la.rotation = Quaternion.AngleAxis(-(bend - want) * ease, hinge.normalized) * la.rotation;
                    // THE WRIST 2026-11-12 (Adnan: "it's like her wrist is permanently broken"): in the Walk and Run clips the hand drops
                    // away from the forearm's line at the front of every swing (9 to 36 degrees and back, each stride, both heroes;
                    // her hand is also built 23 degrees off her forearm's line at rest, his 1). A free hand keeps to the forearm's
                    // line: up to 8 degrees as the clip has it, a fifth of anything beyond.
                    var mid = look.Bone(s == 0 ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
                    if (mid && System.Environment.GetEnvironmentVariable("PLAZA_WRIST") != "0")
                    {
                        var fo2 = (hd.position - la.position).normalized; var ha = (mid.position - hd.position).normalized; float w = Vector3.Angle(fo2, ha);
                        float wantW = w <= 8f ? w : 8f + (w - 8f) * .2f;
                        if (w - wantW > .5f) hd.rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.FromToRotation(ha, fo2), (w - wantW) / w * ease) * hd.rotation;
                    }
                }
            }
            // HER HANDS 2026-11-12: walking and running, her empty hands kept the clip's fingers""")
S = c + "/Tennis/HeroHandShape.cs"
patch(S, "    float[] sl={1,1.06f,1.22f*.97f,1.22f,1.10f,1.00f,1,1};\n    float[] sd={1,.95f,.86f,.86f,.86f,.82f,.88f,1};\n",
"""    // HER WRIST 2026-11-12 (Adnan, after the walk fixes: "the male arm looks perfect but girl's still lacking"). Measured against his:
    // the 10-27 reshape widened her wrist by 22 %, to 7.1 cm, as wide as his (6.9) on a forearm two thirds the size (8.1 against
    // 12.5 cm), so her forearm never narrowed into a wrist (wrist / palm .91 where his is .57) and the hand read as stuck on the
    // end of a rod. The forearm now tapers into a flat oval wrist narrower than the palm. FEMALE_WRIST_TAPER=0 (Editor) = the 10-27 numbers.
    float[] sl={1,1.06f,1.22f*.97f,1.22f,1.10f,1.00f,1,1};
    float[] sd={1,.95f,.86f,.86f,.86f,.82f,.88f,1};
    if(Environment.GetEnvironmentVariable("FEMALE_WRIST_TAPER")!="0"){sl=new[]{1,.97f,.89f,.88f,1.14f,1.06f,1,1};sd=new[]{1,.93f,.76f,.72f,.78f,.80f,.88f,1};}
""")
B = c + "/Tennis/HeroBuild.cs"
patch(B, 'armGain = female ? Env("HERO_ARM_GAIN", 2f) : muscle;', 'armGain = female ? Env("HERO_ARM_GAIN", .6f) : muscle;   // HER ARMS 2026-11-12: at 2 the forearm swelled by a third on a slim frame')
PY
