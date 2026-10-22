from pathlib import Path
import hashlib,json,difflib,subprocess,csv
W=Path(__file__).resolve().parents[1]; P=W.parents[1]; C=W/'UnityClone'; T=W/'r4/trial5/male'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/in-g/outputs/serve-pose-preview/palm-down'); O.mkdir(parents=True,exist_ok=True)
files=sorted(T.glob('game_*.png')); assert len(files)==61
for name,fps in [('dribble.mp4',30),('dribble_half_speed.mp4',15)]:
 subprocess.run([str(W/'scripts/enc'),str(O/name),str(fps),'960','540',*[str(p) for p in files]],check=True)
for name in ['bounce_back','bounce_game','bounce_front','bounce_side']:
 (O/(name+'.png')).write_bytes((T/('key_'+name+'.png')).read_bytes())
for name in ['TESTED_SHA256SUMS','key_frames.csv','PALM_AUDIT.json']:(O/name).write_bytes((T/name).read_bytes())
patch=[]; production={}
for name in ['HeroTennisDriver.cs','TennisGame.cs','TennisServeRoutine.cs']:
 old=P/'Unity/Assets/Scripts/Tennis'/name; new=C/'Assets/Scripts/Tennis'/name
 production[str(old)]=hashlib.sha256(old.read_bytes()).hexdigest()
 patch.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='a/Unity/Assets/Scripts/Tennis/'+name,tofile='b/Unity/Assets/Scripts/Tennis/'+name))
(O/'PREVIEW.patch').write_text(''.join(patch)); (O/'PRODUCTION_GUARD.json').write_text(json.dumps(production,indent=2))
before=(W/'r4/trial3/driver_before.cs').read_text(); after=(C/'Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text()
def method(s):
 a=s.index('        void LockFeet('); b=s.index('\n        ',s.index('\n        }',a)+10); return s[a:b]
assert method(before)==method(after),'Accepted stance changed'
(O/'REVIEW.md').write_text('Palm-down dribble revision, staged only.\n\nThe user accepted the stance and requested palm-down orientation and no ball penetration. The left hand now opens during the bounce; ball contact accounts for the actual 10 cm rendered radius and finger thickness. The accepted LockFeet method is byte-for-byte unchanged from trial2. No production files were modified. Human visual review is pending.\n')
(O/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(O.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
print(O)
