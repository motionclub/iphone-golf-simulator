from pathlib import Path
import difflib,json,hashlib
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/revision1'
p=R/'Unity/Assets/Scripts/Tennis/HeroGripPolish.cs';old=p.read_text();s=old
assert s.count('static void ApplyGolfWristRoll')==1
# Runtime audit is deliberately flag gated and includes selected/clamped rolls.
s=s.replace('''            if (Mathf.Abs(bestRoll) < .0001f) return;
''','''            if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_AUDIT") == "1")
                Debug.Log($"[GolfWristRoll] {(hero.female ? "Female" : "Male")} {(left ? "Left" : "Right")} angle={originalAngle:F3} roll={bestRoll:F3} scale={scale:F6} wristDelta={Vector3.Distance(origin + Quaternion.AngleAxis(bestRoll, axis) * (wrist-origin),wrist):F6} elbowDelta={Vector3.Distance(bestElbow,elbow):F6} axis={axis:F6}");
            if (Mathf.Abs(bestRoll) < .0001f) return;
''')
s=s.replace('''            if (Vector3.Distance(bestElbow, elbow) > limit) return;
''','''            if (Vector3.Distance(bestElbow, elbow) > limit) {
                if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_AUDIT") == "1") Debug.Log("[GolfWristRoll] final40mm elbow gate rejected");
                return;
            }
''')
key='''        static void FitDigits(MatchHeroLook hero,bool left,Vector3 origin,Vector3 axis,float radius,float padding,float proximalLimit,float distalLimit)
'''
helper='''        static void FitGolfSkinTips(MatchHeroLook hero, bool left, Vector3 origin, Vector3 axis, float scale)
        {
            var records = Rest(hero); string prefix = left ? "Left" : "Right";
            string[] joints = { "Proximal", "Intermediate", "Distal" };
            float[,] canonical = { {50,70,40}, {55,75,45}, {62,80,45}, {68,82,45} };
            string[] digits = { "Index", "Middle", "Ring", "Little" };
            float worst = 0;
            for (int digit = 0; digit < digits.Length; digit++) {
                var chain = new RestJoint[3]; bool complete = true;
                for (int j = 0; j < 3; j++) if (!records.TryGetValue(prefix+digits[digit]+joints[j],out chain[j])) { complete=false; break; }
                if (!complete) continue;
                var angles = new float[3];
                for (int j = 0; j < 3; j++) angles[j] = canonical[digit,j];
                Vector3 Tip() => chain[2].bone.TransformPoint(chain[2].tip);
                void Set(int joint, float degrees) { angles[joint]=degrees;chain[joint].bone.localRotation=chain[joint].local*Quaternion.AngleAxis(degrees,chain[joint].hinge); }
                var tip = Tip(); float along = Mathf.Clamp(Vector3.Dot(tip-origin,axis),-.065f*scale,.155f*scale);
                var radial = Vector3.ProjectOnPlane(tip-origin,axis);
                if (radial.sqrMagnitude < 1e-10f) continue;
                // Target the actual skin tip on the finite rubber grip. Existing
                // CCD's d.up surrogate cannot identify rolled distal skin pads.
                var target = origin+axis*along+radial.normalized*(.017f*scale);
                float Cost() => (Tip()-target).sqrMagnitude;
                for (int pass=0;pass<3;pass++) for (int j=2;j>=0;j--) {
                    float selected=angles[j],cost=Cost(),limit=j==0 ? 110f : j==1 ? 140f : 95f;
                    for (float degrees=0;degrees<=limit;degrees+=5) {
                        Set(j,degrees);float trial=Cost();if(trial<cost){cost=trial;selected=degrees;}
                    }
                    Set(j,selected);
                }
                // Refine the selected interval without permitting hyperextension.
                for (int pass=0;pass<2;pass++) for (int j=2;j>=0;j--) {
                    float selected=angles[j],cost=Cost(),limit=j==0 ? 110f : j==1 ? 140f : 95f;
                    float lo=Mathf.Max(0,selected-5),hi=Mathf.Min(limit,selected+5);
                    for(float degrees=lo;degrees<=hi;degrees+=1){Set(j,degrees);float trial=Cost();if(trial<cost){cost=trial;selected=degrees;}}
                    Set(j,selected);
                }
                worst=Mathf.Max(worst,Vector3.Distance(Tip(),target));
            }
            if(System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_AUDIT")=="1")
                Debug.Log($"[GolfSkinTips] {(hero.female ? "Female" : "Male")} {(left ? "Left" : "Right")} worstTargetError={worst:F6}m");
        }
'''
assert s.count(key)==1;s=s.replace(key,helper+key)
needle='''            FitDigits(hero,false,data.grip.position,along,.014f*scale,.006f*scale,35,55);
            FitDigits(hero,true,data.grip.position,along,.014f*scale,.006f*scale,35,55);'''
assert s.count(needle)==1;s=s.replace(needle,'''            if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_ROLL") == "1") {
                FitGolfSkinTips(hero, false, data.grip.position, along, scale);
                FitGolfSkinTips(hero, true, data.grip.position, along, scale);
            } else {
'''+needle+'''
            }''')
(W/'HeroGripPolish.cs').write_text(s);(W/'HeroGripPolish.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs',tofile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs')))
p=R/'Unity/Assets/Scripts/Game/GolferView.cs';old=p.read_text();s=old
needle='''                if (at is Vector3 p) bone.localPosition = p;
            }
        }
'''
assert s.count(needle)==1;s=s.replace(needle,'''                if (at is Vector3 p) bone.localPosition = p;
            }
            // Complete the golf review pose synchronously after the source clip
            // and shaft-clearance solve; scrubbing/export does not rely on LateUpdate.
            if (heroFigure != null && System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_ROLL") == "1")
                GolfArcade.Tennis.HeroGripPolish.ApplyGrip(heroFigure.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>());
        }
''')
(W/'GolferView.cs').write_text(s);(W/'GolferView.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='Unity/Assets/Scripts/Game/GolferView.cs',tofile='Unity/Assets/Scripts/Game/GolferView.cs')))
c=json.loads((W.parent/'capture-config.json').read_text());c['environment']['VISUAL_GOLF_CHARACTER_OUT']=str(R/'proof/reference-rebuild/golf-wrist29-revision1-candidate');c['matchingControl']['VISUAL_GOLF_CHARACTER_OUT']=str(R/'proof/reference-rebuild/golf-wrist29-revision1-control');c['firstTinyPass']={'VISUAL_GOLF_CHARACTER_CLUBS':'Driver','VISUAL_GOLF_CHARACTER_STAGES':'address,top'};c['note']='Incremental patches relative installed rejected wrist29 candidate. Same bounded roll, true anatomical skin-tip closure, synchronous evaluated golfer pose, explicit selected/gated-roll diagnostics; actual acceptance pending.';(W/'capture-config.json').write_text(json.dumps(c,indent=2)+'\n')
print('Staged2 incremental revision patches')
