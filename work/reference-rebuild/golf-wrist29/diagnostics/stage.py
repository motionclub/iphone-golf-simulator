from pathlib import Path
import difflib,json,hashlib
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29'
p=R/'Unity/Assets/Scripts/Tennis/HeroGripPolish.cs';s=p.read_text();old=s
key='        public static void ApplyGolfGrip(MatchHeroLook hero)\n'
helper='''        // Review-only candidate: use the existing elbow circle to reduce wrist
        // folding while pinning the authored hand/club contact frames exactly.
        // Static rig animation only; geometry, weights and bind matrices do not change.
        static void ApplyGolfWristPole(MatchHeroLook hero, bool left)
        {
            if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_POLE") != "1") return;
            var upper = hero.Bone(left ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm);
            var lower = hero.Bone(left ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
            var hand = hero.Bone(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
            var middle = Bone(hero, left, "Middle", "Proximal");
            if (!upper || !lower || !hand || !middle) return;
            var shoulder = upper.position; var wrist = hand.position; var elbow = lower.position;
            var palm = (middle.position - wrist).normalized;
            float upperLength = Vector3.Distance(shoulder, elbow), lowerLength = Vector3.Distance(elbow, wrist);
            var axis = wrist - shoulder; float distance = axis.magnitude;
            if (distance < .0001f || upperLength < .0001f || lowerLength < .0001f) return;
            axis /= distance;
            // Avoid singular/folded chains; never shorten limbs or move the grip
            // to make an unreachable pole solution appear valid.
            if (distance >= upperLength + lowerLength - .00001f || distance <= Mathf.Abs(upperLength - lowerLength) + .00001f) return;
            const float preferredAngle = 45f;
            float currentAngle = Vector3.Angle(wrist - elbow, palm);
            if (currentAngle <= preferredAngle + .02f) return;
            float along = (upperLength * upperLength - lowerLength * lowerLength + distance * distance) / (2 * distance);
            float radius = Mathf.Sqrt(Mathf.Max(0, upperLength * upperLength - along * along));
            if (radius < .0001f) return;
            var centre = shoulder + axis * along;
            var original = (elbow - centre).normalized;
            var preferred = Vector3.ProjectOnPlane(-palm, axis).normalized;
            if (preferred.sqrMagnitude < .5f || Vector3.Dot(original, preferred) < -.9995f) return;
            var optimum = centre + preferred * radius;
            if (Vector3.Angle(wrist - optimum, palm) >= currentAngle - .02f) return;
            // Take the smallest pole movement attaining45deg. If the fixed grip
            // cannot attain it, choose the true optimum, preserving reach.
            float lo = 0, hi = 1;
            if (Vector3.Angle(wrist - optimum, palm) < preferredAngle)
                for (int iteration = 0; iteration < 24; iteration++) {
                    float at = (lo + hi) * .5f;
                    var trial = centre + Vector3.Slerp(original, preferred, at) * radius;
                    if (Vector3.Angle(wrist - trial, palm) > preferredAngle) lo = at; else hi = at;
                }
            var desiredElbow = centre + Vector3.Slerp(original, preferred, hi) * radius;
            var rotation = hand.rotation;
            upper.rotation = Quaternion.FromToRotation(lower.position - shoulder, desiredElbow - shoulder) * upper.rotation;
            lower.rotation = Quaternion.FromToRotation(hand.position - lower.position, wrist - lower.position) * lower.rotation;
            // Preserve the complete sampled grip frame and all descendant digits.
            hand.SetPositionAndRotation(wrist, rotation);
        }
'''
assert s.count(key)==1;s=s.replace(key,helper+key)
needle='''            CanonicalGolfFingers(hero);
'''
assert s.count(needle)==1;s=s.replace(needle,'''            ApplyGolfWristPole(hero, false);
            ApplyGolfWristPole(hero, true);
'''+needle)
(W/'HeroGripPolish.cs').write_text(s)
(W/'HeroGripPolish.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs',tofile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs')))
p=R/'Unity/Assets/Editor/VisualOverhaulGolfCharacterCapture.cs';s=p.read_text();old=s
s=s.replace('''                    bool shortShot=club==GolfClub.Wedge;golfer.SetClub(club,shortShot);''','''                    var clubs = Environment.GetEnvironmentVariable("VISUAL_GOLF_CHARACTER_CLUBS");
                    if (!string.IsNullOrEmpty(clubs) && !clubs.Split(',').Contains(club.ToString())) continue;
                    bool shortShot=club==GolfClub.Wedge;golfer.SetClub(club,shortShot);''')
s=s.replace('''                    for(int i=0;i<times.Length;i++){
''','''                    for(int i=0;i<times.Length;i++){
                        var stages = Environment.GetEnvironmentVariable("VISUAL_GOLF_CHARACTER_STAGES");
                        if (!string.IsNullOrEmpty(stages) && !stages.Split(',').Contains(labels[i])) continue;
''')
assert s!=old
(W/'VisualOverhaulGolfCharacterCapture.cs').write_text(s)
(W/'VisualOverhaulGolfCharacterCapture.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='Unity/Assets/Editor/VisualOverhaulGolfCharacterCapture.cs',tofile='Unity/Assets/Editor/VisualOverhaulGolfCharacterCapture.cs')))
report={'status':'SOURCE_CANDIDATE_ONLY_ACTUAL_REQUIRED','sourceSHA256':hashlib.sha256((R/'Unity/Assets/Scripts/Tennis/HeroGripPolish.cs').read_bytes()).hexdigest(),'productionWrites':False,'GPU':False,'environment':{'VISUAL_GOLF_WRIST_POLE':'1','VISUAL_GOLF_CHARACTER_CLUBS':'Driver,Putter','VISUAL_GOLF_CHARACTER_STAGES':'address,contact,top','VISUAL_ORIGINAL_SEAM':'1','VISUAL_ORIGINAL_BLINK':'1','VISUAL_CHARACTER_NORMALS':'continuous','VISUAL_CHARACTER_SKIN_FINISH':'1','VISUAL_UNDERARM_GUSSET':'0','VISUAL_UNDERARM_FIT':'0'},'method':'GolfArcade.EditorTools.VisualOverhaulGolfCharacterCapture.Run','matchingControl':{'VISUAL_GOLF_WRIST_POLE':'0'},'firstTinyPass':{'VISUAL_GOLF_CHARACTER_CLUBS':'Driver','VISUAL_GOLF_CHARACTER_STAGES':'address,top'},'note':'Use existing root capture_queue output configuration. Editor filtering alone adds no runtime change. First review both sexes front/back/grip before five-family sweep.'}
(W/'capture-config.json').write_text(json.dumps(report,indent=2)+'\n')
print('Staged2patches; no production edits')
