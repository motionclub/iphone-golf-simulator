from pathlib import Path
import difflib,json
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/revision2';p=R/'Unity/Assets/Scripts/Tennis/HeroGripPolish.cs';old=p.read_text();s=old
assert s.count('static void FitGolfSkinTips')==1
start=s.index('        static void FitGolfSkinTips');end=s.index('        static void FitDigits',start);s=s[:start]+s[end:]
s=s.replace('''        void LateUpdate() { if (!look) look=GetComponent<MatchHeroLook>(); ApplyGrip(look); }''','''        void LateUpdate() {
            if (!look) look=GetComponent<MatchHeroLook>();
            // The review golfer evaluates grip synchronously once per source pose.
            // Re-canonicalizing digits on an already rolled hand breaks that grip.
            if (look && look.golfKit && System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_ROLL") == "1") return;
            ApplyGrip(look);
        }''')
s=s.replace('''public GolfWristResult[] wrists = new GolfWristResult[2]; }''','''public GolfWristResult[] wrists = new GolfWristResult[2];public Transform[] solvedBones;public Matrix4x4[] solvedPose; }''')
needle='''                golfData[hero]=data;
'''
replacement='''                data.solvedBones = new[] {
                    hero.Bone(HumanBodyBones.LeftUpperArm), hero.Bone(HumanBodyBones.LeftLowerArm), hero.Bone(HumanBodyBones.LeftHand),
                    hero.Bone(HumanBodyBones.RightUpperArm), hero.Bone(HumanBodyBones.RightLowerArm), hero.Bone(HumanBodyBones.RightHand), data.grip };
                golfData[hero]=data;
'''
assert s.count(needle)==1;s=s.replace(needle,replacement)
needle='''            int active=System.Array.FindIndex(data.clubs,r=>r&&r.gameObject.activeInHierarchy);if(active<0)return;
'''
replacement=needle+'''            bool wristReview = System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_ROLL") == "1";
            if (wristReview && data.solvedPose != null) {
                bool same = true;
                for (int bone=0;bone<data.solvedBones.Length && same;bone++) {
                    if (!data.solvedBones[bone]) { same=false;break; }
                    var matrix=data.solvedBones[bone].localToWorldMatrix;
                    for(int k=0;k<16;k++) if(Mathf.Abs(matrix[k]-data.solvedPose[bone][k])>1e-6f) { same=false;break; }
                }
                // Covers repeated export/sample calls too, before any digit reset.
                if(same)return;
            }
'''
assert s.count(needle)==1;s=s.replace(needle,replacement)
start=s.index('''            ApplyGolfWristRoll(hero, data, false, along, scale);''');end=s.index('''        static void FitDigits''',start)
oldsection=s[start:end]
expected='''            ApplyGolfWristRoll(hero, data, false, along, scale);
            ApplyGolfWristRoll(hero, data, true, along, scale);
            if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_ROLL") == "1") {
                FitGolfSkinTips(hero, false, data.grip.position, along, scale);
                FitGolfSkinTips(hero, true, data.grip.position, along, scale);
            } else {
            FitDigits(hero,false,data.grip.position,along,.014f*scale,.006f*scale,35,55);
            FitDigits(hero,true,data.grip.position,along,.014f*scale,.006f*scale,35,55);
            }
        }
'''
assert oldsection==expected,repr(oldsection)
new='''            // Baseline grip first, in the sampled authored hand frame.
            FitDigits(hero,false,data.grip.position,along,.014f*scale,.006f*scale,35,55);
            FitDigits(hero,true,data.grip.position,along,.014f*scale,.006f*scale,35,55);
            // Last operation is a rigid hand/subtree rotation around the real shaft.
            // Every baseline pad keeps its shaft station and cylinder radius.
            ApplyGolfWristRoll(hero, data, false, along, scale);
            ApplyGolfWristRoll(hero, data, true, along, scale);
            if(wristReview) {
                data.solvedPose ??= new Matrix4x4[data.solvedBones.Length];
                for(int bone=0;bone<data.solvedBones.Length;bone++)if(data.solvedBones[bone])data.solvedPose[bone]=data.solvedBones[bone].localToWorldMatrix;
            }
        }
'''
s=s[:start]+new+s[end:]
(W/'HeroGripPolish.cs').write_text(s);(W/'HeroGripPolish.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs',tofile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs')))
c=json.loads((W.parent/'revision1/capture-config.json').read_text());c['environment']['VISUAL_GOLF_CHARACTER_OUT']=str(R/'proof/reference-rebuild/golf-wrist29-revision2-candidate');c['matchingControl']['VISUAL_GOLF_CHARACTER_OUT']=str(R/'proof/reference-rebuild/golf-wrist29-revision2-control');c['note']='Incremental to installed revision1. Removes failed skin-tip solver; keeps existing canonical+CCD grip FIRST, rigid bounded hand roll LAST, synchronous source Evaluate, no golf review LateUpdate re-curling; complete pose guard precedes digit reset.';(W/'capture-config.json').write_text(json.dumps(c,indent=2)+'\n')
print('Staged ordering-only revision2; synchronous GolferView hook from installed revision1 retained')
