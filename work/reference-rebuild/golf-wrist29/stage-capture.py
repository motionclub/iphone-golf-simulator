from pathlib import Path
import difflib,json
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29';p=R/'Unity/Assets/Editor/VisualOverhaulGolfCharacterCapture.cs';old=p.read_text();s=old
needle='''        static IEnumerator Frames(int n){for(int i=0;i<n;i++)yield return null;}
'''
helper='''        static string WristStamp(HeroGolfer hero) {
            var text = new System.Text.StringBuilder();
            foreach (string name in new[]{"LeftUpperArm","LeftLowerArm","LeftHand","LeftMiddleProximal","RightUpperArm","RightLowerArm","RightHand","RightMiddleProximal","Club"}) {
                var b=hero.Bones[name];text.Append(name+" p="+b.position.ToString("F9")+" q="+b.rotation.ToString("F9")+"; ");
            }
            return text.ToString();
        }
'''
assert s.count(needle)==1;s=s.replace(needle,needle+helper)
s=s.replace('''                    bool shortShot=club==GolfClub.Wedge;golfer.SetClub(club,shortShot);''','''                    var clubs=Environment.GetEnvironmentVariable("VISUAL_GOLF_CHARACTER_CLUBS");
                    if(!string.IsNullOrEmpty(clubs)&&Array.IndexOf(clubs.Split(','),club.ToString())<0)continue;
                    bool shortShot=club==GolfClub.Wedge;golfer.SetClub(club,shortShot);''')
s=s.replace('''                    for(int i=0;i<times.Length;i++){
''','''                    for(int i=0;i<times.Length;i++){
                        var stages=Environment.GetEnvironmentVariable("VISUAL_GOLF_CHARACTER_STAGES");
                        if(!string.IsNullOrEmpty(stages)&&Array.IndexOf(stages.Split(','),labels[i])<0)continue;
''')
s=s.replace('''                        typeof(GolferView).GetMethod("Show",Private).Invoke(golfer,new object[]{times[i]});yield return Frames(3);''','''                        typeof(GolferView).GetMethod("Show",Private).Invoke(golfer,new object[]{times[i]});
                        if(Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_AUDIT")=="1")audit.Add(sex+"_"+club+"_"+labels[i]+" before: "+WristStamp(hero));
                        yield return Frames(3);
                        if(Environment.GetEnvironmentVariable("VISUAL_GOLF_WRIST_AUDIT")=="1")audit.Add(sex+"_"+club+"_"+labels[i]+" after: "+WristStamp(hero));''')
assert s!=old
(W/'VisualOverhaulGolfCharacterCapture.cs').write_text(s);(W/'VisualOverhaulGolfCharacterCapture.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='Unity/Assets/Editor/VisualOverhaulGolfCharacterCapture.cs',tofile='Unity/Assets/Editor/VisualOverhaulGolfCharacterCapture.cs')))
c=json.loads((W/'capture-config.json').read_text());c['environment']['VISUAL_GOLF_WRIST_AUDIT']='1';c['environment']['VISUAL_GOLF_CHARACTER_OUT']=str(R/'proof/reference-rebuild/golf-wrist29-candidate');c['matchingControl']['VISUAL_GOLF_CHARACTER_OUT']=str(R/'proof/reference-rebuild/golf-wrist29-control');(W/'capture-config.json').write_text(json.dumps(c,indent=2)+'\n')
