from pathlib import Path
import difflib,hashlib,json
r=Path.cwd();w=r/'work/reference-rebuild/golf-wrist29/authored-preservation';p='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs';old=(r/p).read_text();s=old
needle='''                    hero.Bone(HumanBodyBones.RightUpperArm), hero.Bone(HumanBodyBones.RightLowerArm), hero.Bone(HumanBodyBones.RightHand), data.grip };'''
assert s.count(needle)==1
s=s.replace(needle,needle+'''
                // The sampler can rewrite digit channels while the arm is unchanged.
                // Cache the complete grip output, not only its seven rigid anchors.
                var complete = new System.Collections.Generic.List<Transform>(data.solvedBones);
                foreach(bool left in new[]{false,true})
                    foreach(string digit in new[]{"Thumb","Index","Middle","Ring","Little"})
                        foreach(string joint in new[]{"Proximal","Intermediate","Distal"}) {
                            var bone=Bone(hero,left,digit,joint);if(bone)complete.Add(bone);
                        }
                data.solvedBones=complete.ToArray();''')
needle='''            // Authored golf keys bend every joint about +localX, but intermediate and
            // distal rolls differ. Reconstruct the same curl amounts on the measured
            // original bind hinges before bounded cylinder-contact refinement.
            CanonicalGolfFingers(hero);'''
assert s.count(needle)==1
s=s.replace(needle,'''            // Preserve the actual sampled clip's proximal fan and curl. The source
            // authors this fan to match each hand's shaft orientation; canonical
            // rest curls discard it. Legacy output keeps its existing refinement.
            if(!wristReview)CanonicalGolfFingers(hero);''')
needle='''            // Baseline grip first, in the sampled authored hand frame.
            FitDigits(hero,false,data.grip.position,along,.014f*scale,.006f*scale,35,55);
            FitDigits(hero,true,data.grip.position,along,.014f*scale,.006f*scale,35,55);'''
assert s.count(needle)==1
s=s.replace(needle,'''            if(!wristReview) {
                FitDigits(hero,false,data.grip.position,along,.014f*scale,.006f*scale,35,55);
                FitDigits(hero,true,data.grip.position,along,.014f*scale,.006f*scale,35,55);
            }''')
s=s.replace('''            // Every baseline pad keeps its shaft station and cylinder radius.''','''            // Every authored pad keeps its shaft station and cylinder radius.''')
(w/'HeroGripPolish.cs').write_text(s);(w/'HeroGripPolish.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=p,tofile=p)))
(w/'source-contract.json').write_text(json.dumps({'status':'FINGER_ONLY_SOURCE_CONTRACT_STAGED_WRIST_CONTINUITY_BLOCKED','sourceSHA256':hashlib.sha256(s.encode()).hexdigest(),'baselineSHA256':hashlib.sha256(old.encode()).hexdigest(),'incrementalTo':'installed revision2','legacyFlag0':'CanonicalGolfFingers and FitDigits unchanged','candidateFlag1':'Actual source digit locals untouched; rigid Hand subtree carry only; source Evaluate synchronous and LateUpdate skips;37-transform output guard','noRenderUntil':'Astra continuous-review math proof and root integration','productionWrites':False},indent=2)+'\n')
print('Staged authored digit preservation only; inherited wrist search is rejected, awaiting Astra')
