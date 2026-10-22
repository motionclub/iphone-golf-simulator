from pathlib import Path
R=Path.cwd();p=R/'Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs';s=p.read_text()
# Both physics substep and regular Update paths capture the actually held pose before
# assigning the new stroke state. No authoritative actor timer/clip anchor changes.
s=s.replace('''                swingClip = Playable(StrokeClip()); action = swingClip; actionActive = true;
''','''                swingClip = Playable(StrokeClip()); BeginSwingTime(swingClip,actor.SignedTimeToContact);
                action = swingClip; actionActive = true;
''',1)
s=s.replace('''                swingStartTtc = Mathf.Max(actor.SignedTimeToContact, .05f);
''','',1)
s=s.replace('''if (!wasSwinging || !actionActive || action != c) { lead = Mathf.Lerp(lead, Mathf.Clamp(ttc, .15f, .9f), .5f); action = c; actionActive = true; juiceActive = false; swingStartTtc = Mathf.Max(ttc, .05f); }''','''if (!wasSwinging || !actionActive || action != c) { BeginSwingTime(c,ttc); lead = Mathf.Lerp(lead, Mathf.Clamp(ttc, .15f, .9f), .5f); action = c; actionActive = true; juiceActive = false; }''',1)
s=s.replace('''        float swingStartTtc = .3f;
''','''        float swingStartTtc = .3f, swingStartBase;
        void BeginSwingTime(Clip next,float ttc)
        {
            swingStartTtc=Mathf.Max(ttc,.05f);int i=(int)next;
            float held=Match && actionActive && action==next && !followThrough
                ? Mathf.Clamp(actionTime,0,contact[i]) : Mathf.Max(0,contact[i]-swingStartTtc);
            // StrokeTime applies Tempo about the contact anchor. Undo it once here
            // so u=0 is the exact visible held preparation rather than a new clip pose.
            swingStartBase=contact[i]+(held-contact[i])/Mathf.Max(.01f,Tempo);
        }
''',1)
s=s.replace('''                return Mathf.Clamp(contact[i] - swingStartTtc * (1 - Mathf.Pow(u, SwingEaseNow)), 0, length[i]);''','''                return Match ? Mathf.Lerp(swingStartBase,contact[i],Mathf.Pow(u,SwingEaseNow))
                    : Mathf.Clamp(contact[i] - swingStartTtc * (1 - Mathf.Pow(u, SwingEaseNow)), 0, length[i]);''',1)
# Preserve correct frozen Generic foot axes instead of assuming bone +Z is the shoe heading.
s=s.replace('''foot.rotation=Quaternion.Slerp(footRotation,Quaternion.LookRotation(actor.transform.forward,Vector3.up),reach*.82f);''','''foot.rotation=Quaternion.Slerp(footRotation,Quaternion.AngleAxis(side*66*reach,actor.transform.forward)*footRotation,reach*.82f);''',1)
s=s.replace('''hand.rotation=Quaternion.Slerp(rot,Quaternion.LookRotation(actor.transform.forward,Vector3.up)*Quaternion.Euler(90,0,0),brace*.7f);''','''hand.rotation=Quaternion.AngleAxis(22*brace,actor.transform.right)*rot;''',1)
s=s.replace('toBall+transform.TransformVector(lungeOffset)','toBall+actor.transform.TransformVector(lungeOffset)',1)
(R/'work/full-visual-overhaul/tennis/HeroTennisDriver.cs.stage7').write_text(s)
print('staged held-pose stroke continuity and bone-axis preserving dive orientation')
