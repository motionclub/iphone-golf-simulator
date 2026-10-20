from pathlib import Path
import difflib,json
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29';p=R/'Unity/Assets/Scripts/Tennis/HeroGripPolish.cs';old=p.read_text();s=old
s=s.replace('''    /// Bounded finger-only refinement on the existing Generic hierarchy. Hand/socket,
    /// racket contact, arm pose and rest matrices are never changed.''', '''    /// Shared finger refinement on the original Generic hierarchy. The golf wrist
    /// review flag permits bounded grip roll and arm pose changes; rest/rig stay exact.''')
s=s.replace('sealed class GolfGripData { public Transform grip;public SkinnedMeshRenderer[] clubs;public Vector3[] ends; }','''sealed class GolfGripData { public Transform grip;public SkinnedMeshRenderer[] clubs;public Vector3[] ends;public GolfWristResult[] wrists = new GolfWristResult[2]; }
        sealed class GolfWristResult {
            public Vector3 shoulder, elbow, wrist, grip, shaft;
            public Quaternion upperRotation, lowerRotation, handRotation;
        }''')
key='        public static void ApplyGolfGrip(MatchHeroLook hero)\n'
helper='''        // Review candidate: carry the sampled hand around the unchanged shaft,
        // preserving its cylinder contact, then solve the original two-bone arm.
        // The small shared search limits wrist and elbow translations to40mm.
        static void ApplyGolfWristRoll(MatchHeroLook hero, GolfGripData data, bool left, Vector3 axis, float scale)
        {
            if (System.Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_ROLL") != "1") return;
            var upper = hero.Bone(left ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm);
            var lower = hero.Bone(left ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
            var hand = hero.Bone(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
            var middle = Bone(hero, left, "Middle", "Proximal");
            if (!upper || !lower || !hand || !middle || scale < .0001f) return;
            var shoulder = upper.position; var wrist = hand.position; var elbow = lower.position;
            var origin = data.grip.position; var handRotation = hand.rotation;
            int side = left ? 1 : 0; var last = data.wrists[side];
            // A paused proof/locker may invoke grip repeatedly without resampling.
            // Skip the exact solved output instead of accumulating another45deg.
            if (last != null && (last.shoulder - shoulder).sqrMagnitude < 1e-12f &&
                (last.elbow - elbow).sqrMagnitude < 1e-12f && (last.wrist - wrist).sqrMagnitude < 1e-12f &&
                (last.grip - origin).sqrMagnitude < 1e-12f && (last.shaft - axis).sqrMagnitude < 1e-12f &&
                Mathf.Abs(Quaternion.Dot(last.upperRotation, upper.rotation)) > .999999f &&
                Mathf.Abs(Quaternion.Dot(last.lowerRotation, lower.rotation)) > .999999f &&
                Mathf.Abs(Quaternion.Dot(last.handRotation, handRotation)) > .999999f) return;
            var palm = (middle.position - wrist).normalized;
            float originalAngle = Vector3.Angle(wrist - elbow, palm);
            if (originalAngle <= 35f) return;
            float a = Vector3.Distance(shoulder, elbow), b = Vector3.Distance(elbow, wrist);
            if (a < .0001f || b < .0001f) return;
            float limit = .04f * scale, bestCost = originalAngle * originalAngle, bestRoll = 0;
            var bestWrist = wrist; var bestElbow = elbow;
            for (int degrees = -45; degrees <= 45; degrees++) {
                var turn = Quaternion.AngleAxis(degrees, axis);
                var target = origin + turn * (wrist - origin);
                if ((target - wrist).sqrMagnitude > limit * limit) continue;
                var forward = target - shoulder; float distance = forward.magnitude;
                if (distance >= a + b - .00001f || distance <= Mathf.Abs(a - b) + .00001f) continue;
                forward /= distance;
                float along = (a * a - b * b + distance * distance) / (2 * distance);
                float radius = Mathf.Sqrt(Mathf.Max(0, a * a - along * along));
                var centre = shoulder + forward * along;
                var pole = Vector3.ProjectOnPlane(elbow - centre, forward);
                if (pole.sqrMagnitude < 1e-10f) continue;
                var trialElbow = centre + pole.normalized * radius;
                float elbowShift = Vector3.Distance(trialElbow, elbow);
                if (elbowShift > limit) continue;
                float angle = Vector3.Angle(target - trialElbow, turn * palm);
                float cost = angle * angle + .12f * degrees * degrees + 50000f * elbowShift * elbowShift / (scale * scale);
                if (cost >= bestCost) continue;
                bestCost = cost; bestRoll = degrees; bestWrist = target; bestElbow = trialElbow;
            }
            // Fade in near comfortable wrists; activation is continuous at35deg.
            bestRoll *= Mathf.SmoothStep(0, 1, Mathf.InverseLerp(35, 50, originalAngle));
            if (Mathf.Abs(bestRoll) < .0001f) return;
            var bestTurn = Quaternion.AngleAxis(bestRoll, axis);
            bestWrist = origin + bestTurn * (wrist - origin);
            var finalAxis = bestWrist - shoulder; float finalDistance = finalAxis.magnitude;
            if (finalDistance >= a + b - .00001f || finalDistance <= Mathf.Abs(a - b) + .00001f) return;
            finalAxis /= finalDistance;
            float finalAlong = (a * a - b * b + finalDistance * finalDistance) / (2 * finalDistance);
            var finalCentre = shoulder + finalAxis * finalAlong;
            var finalPole = Vector3.ProjectOnPlane(elbow - finalCentre, finalAxis);
            if (finalPole.sqrMagnitude < 1e-10f) return;
            bestElbow = finalCentre + finalPole.normalized * Mathf.Sqrt(Mathf.Max(0, a * a - finalAlong * finalAlong));
            if (Vector3.Distance(bestElbow, elbow) > limit) return;
            var rotation = bestTurn * handRotation;
            upper.rotation = Quaternion.FromToRotation(lower.position - shoulder, bestElbow - shoulder) * upper.rotation;
            lower.rotation = Quaternion.FromToRotation(hand.position - lower.position, bestWrist - lower.position) * lower.rotation;
            hand.SetPositionAndRotation(bestWrist, rotation);
            // Club remains untouched. Existing finger closure runs after this.
            data.wrists[side] = new GolfWristResult { shoulder = upper.position, elbow = lower.position,
                wrist = hand.position, grip = origin, shaft = axis, upperRotation = upper.rotation,
                lowerRotation = lower.rotation, handRotation = hand.rotation };
        }
'''
assert s.count(key)==1;s=s.replace(key,helper+key)
needle='''            var along=data.grip.TransformVector(localAxis).normalized;
'''
assert s.count(needle)==1;s=s.replace(needle,needle+'''            ApplyGolfWristRoll(hero, data, false, along, scale);
            ApplyGolfWristRoll(hero, data, true, along, scale);
''')
(W/'HeroGripPolish.cs').write_text(s)
(W/'HeroGripPolish.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs',tofile='Unity/Assets/Scripts/Tennis/HeroGripPolish.cs')))
config=json.loads((W/'capture-config.json').read_text());config['environment'].pop('VISUAL_GOLF_WRIST_POLE',None);config['environment']['VISUAL_GOLF_WRIST_ROLL']='1';config['matchingControl']={'VISUAL_GOLF_WRIST_ROLL':'0'};config['note']='Pole-only candidate held, replaced by bounded hand-around-shaft roll plus nearest original elbow solve. Club path/contact unchanged, wrist/elbow shifts each<=40mm at unit scale; pose still needs actual art review.'
(W/'capture-config.json').write_text(json.dumps(config,indent=2)+'\n')
print('Replaced held pole patch with bounded grip-roll patch')
