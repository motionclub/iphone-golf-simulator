from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/full-visual-overhaul/tennis/motion10';w.mkdir(exist_ok=True)
f=r/'Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs';s=f.read_text()
s=s.replace('''            graph.Evaluate(0);
            PostProcess(true,true);
        }
        /// Short authored''','''            graph.Evaluate(0);
            // Exact sub-step contact keeps the same guide/string solve. Its caches
            // must not become the next displayed frame's abrupt body position.
            // LateUpdate evaluates the graph again before its smooth correction.
            var visualLunge=lungeOffset;float visualCrouch=contactCrouch,visualVelocity=contactCrouchVelocity;
            int visualCrouchFrame=contactCrouchFrame,visualLungeFrame=contactLungeFrame;
            float lastRenderedCrouch=LastCrouch,lastRenderedDesired=LastDesiredCrouch;
            var renderedGuide=LastGuideGoal;float renderedAssist=LastAssistWeight;
            PostProcess(true,true);
            LastPhysicsCrouch=contactCrouch;LastPhysicsLunge=lungeOffset;
            LastPhysicsStrings=stringCentre.position;LastPhysicsTtc=actor.SignedTimeToContact;
            lungeOffset=visualLunge;contactCrouch=visualCrouch;contactCrouchVelocity=visualVelocity;
            contactCrouchFrame=visualCrouchFrame;contactLungeFrame=visualLungeFrame;
            LastCrouch=lastRenderedCrouch;LastDesiredCrouch=lastRenderedDesired;
            LastGuideGoal=renderedGuide;LastAssistWeight=renderedAssist;
            // Restoring state deliberately leaves the evaluated skeleton/socket
            // transforms intact for the game's current string-crossing test.
            PhysicsPoseRestoreError=Vector3.Distance(LastPhysicsStrings,stringCentre.position);
        }
        /// Short authored''')
s=s.replace('if (swinging && IsStroke(action)) AssistContact();','if (swinging && IsStroke(action)) AssistContact(physicsSubstep);')
s=s.replace('public float LastCrouch { get; private set; }','''public float LastCrouch { get; private set; }
        public float LastDesiredCrouch { get; private set; }
        public Vector3 RenderedLunge => lungeOffset;
        public Vector3 LastGuideGoal { get; private set; }
        public float LastAssistWeight { get; private set; }
        public float LastPhysicsCrouch { get; private set; }
        public Vector3 LastPhysicsLunge { get; private set; }
        public Vector3 LastPhysicsStrings { get; private set; }
        public float LastPhysicsTtc { get; private set; }
        public float PhysicsPoseRestoreError { get; private set; }''')
s=s.replace('''            crouchApplied=true;
            if(!Match)''','''            crouchApplied=true;LastDesiredCrouch=desired;
            if(!Match)''')
s=s.replace('''            if(contactCrouch<.001f||!hips)return;''','''            LastCrouch=contactCrouch;
            if(contactCrouch<.001f||!hips)return;''')
s=s.replace('void AssistContact()','void AssistContact(bool physicsSubstep)')
s=s.replace('''            if (w <= 0 || !Grip) return;''','''            LastAssistWeight=w;
            if (w <= 0 || !Grip) return;''')
s=s.replace('if(!Match || ttc<.025f) lungeOffset=desiredLocal;','if(!Match || (physicsSubstep&&ttc<.025f)) lungeOffset=desiredLocal;')
s=s.replace('ContactCrouch(Mathf.Min(.34f,Mathf.Max(0,low)*.9f)*(actor.SignedTimeToContact>0?1:w),ttc<.025f);','ContactCrouch(Mathf.Min(.34f,Mathf.Max(0,low)*.9f)*(actor.SignedTimeToContact>0?1:w),physicsSubstep&&ttc<.025f);')
s=s.replace('''            float armAssist = isPlayer''','''            LastGuideGoal=goal;
            float armAssist = isPlayer''')
assert 'AssistContact()' not in s
(w/'HeroTennisDriver.cs').write_text(s)
# Trace append only: preserve existing names and parser positional fields.
f=r/'Unity/Assets/Editor/MatchHeroProof.cs';s=f.read_text();s=s.replace('''{d.WeightReport().Replace(',', ';')}");''','''{d.WeightReport().Replace(',', ';')},{d.LastCrouch:0.00000},{d.LastDesiredCrouch:0.00000},{Fmt(d.RenderedLunge)},{a.Guiding},{a.ContactGuideWeight:0.00000},{Fmt(a.GuideBall)},{Fmt(d.LastGuideGoal)},{d.LastAssistWeight:0.00000},{d.LastPhysicsTtc:0.00000},{d.LastPhysicsCrouch:0.00000},{Fmt(d.LastPhysicsLunge)},{Fmt(d.LastPhysicsStrings)},{d.PhysicsPoseRestoreError:0.000000}");''')
s=s.replace('groundLift,weights";','groundLift,weights,crouch,desiredCrouch,visualLunge,guiding,guideWeight,guideBall,guideGoal,assistWeight,physicsTtc,physicsCrouch,physicsLunge,physicsStrings,physicsRestoreError";')
(w/'MatchHeroProof.cs').write_text(s)
f=r/'Unity/Assets/Editor/TennisActionFilm.cs';s=f.read_text();s=s.replace('guiding,dive,shake,flash"','guiding,dive,shake,flash,crouch,desiredCrouch,visualLungeX,visualLungeY,visualLungeZ,guideWeight,physicsTtc,physicsCrouch,physicsRestoreError"')
s=s.replace('{fx.Shake:F4},{fx.Flash:F4}");','{fx.Shake:F4},{fx.Flash:F4},{driver.LastCrouch:F5},{driver.LastDesiredCrouch:F5},{driver.RenderedLunge.x:F5},{driver.RenderedLunge.y:F5},{driver.RenderedLunge.z:F5},{driver.actor.ContactGuideWeight:F5},{driver.LastPhysicsTtc:F5},{driver.LastPhysicsCrouch:F5},{driver.PhysicsPoseRestoreError:F7}");')
(w/'TennisActionFilm.cs').write_text(s)
print('Motion10 staged: physics exact caches isolated; rendered crouch/lunge smooth throughout; diagnostic trace appended')
