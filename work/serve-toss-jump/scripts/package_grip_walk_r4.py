from pathlib import Path
import hashlib,json,difflib,subprocess,csv
W=Path(__file__).resolve().parents[1]; P=W.parents[1]; C=W/'UnityClone'; T=W/'r4/trial6/male'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/in-g/outputs/serve-pose-preview/grip-and-walk'); O.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((T/'trace.csv').open())); pictures={int(r['frame']):int(r['picture']) for r in rows if int(r['picture'])>=0}
def encode(name,view,start,end,fps,size):
 files=[T/f'{view}_{pic:05}.png' for frame,pic in pictures.items() if start<=frame<=end]
 assert files and all(p.is_file() for p in files)
 subprocess.run([str(W/'scripts/enc'),str(O/name),str(fps),*[str(x) for x in size],*[str(p) for p in files]],check=True)
encode('dribble_half_speed.mp4','back',140,260,15,(640,640))
encode('walk_left_to_right.mp4','game',0,120,30,(960,540))
encode('walk_detail.mp4','back',0,120,30,(640,640))
for frame,name in [(180,'ball_held.png'),(200,'ball_in_flight.png')]:
 (O/name).write_bytes((T/f'back_{pictures[frame]:05}.png').read_bytes())
for name in ['TESTED_SHA256SUMS','key_frames.csv','PALM_AUDIT.json']:(O/name).write_bytes((T/name).read_bytes())
patch=[]; production={}
for name in ['HeroTennisDriver.cs','TennisGame.cs','TennisServeRoutine.cs']:
 old=P/'Unity/Assets/Scripts/Tennis'/name; new=C/'Assets/Scripts/Tennis'/name
 production[str(old)]=hashlib.sha256(old.read_bytes()).hexdigest()
 patch.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='a/Unity/Assets/Scripts/Tennis/'+name,tofile='b/Unity/Assets/Scripts/Tennis/'+name))
(O/'PREVIEW.patch').write_text(''.join(patch)); (O/'PRODUCTION_GUARD.json').write_text(json.dumps(production,indent=2))
before=(W/'r4/driver_before_grip.cs').read_text(); after=(C/'Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text()
def method(s):
 a=s.index('        void LockFeet('); end=s.index('\n        }',a)+10; return s[a:end]
assert method(before)==method(after),'Accepted stance changed'
walk=[r for r in rows if int(r['frame'])<=105]
(O/'WALK_AUDIT.json').write_text(json.dumps({'first_x':float(walk[0]['actorRoot_x']),'last_x':float(walk[-1]['actorRoot_x']),'distance_m':float(walk[-1]['actorRoot_x'])-float(walk[0]['actorRoot_x']),'motion':'Actual pre-serve approach captured at 60 Hz; no pose or movement overrides.'},indent=2))
(O/'REVIEW.md').write_text('Trial6 staged preview, not installed. Fingers cup the ball while possessed and open during bounce flight, with an 80 ms blend and radius/finger clearance preserved. The accepted LockFeet method is unchanged. The walk is the actual live-game pre-serve approach, moving left to right in gameplay coordinates; the detail view tracks the actor. Human visual review remains pending.\n')
(O/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(O.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
print(O)
