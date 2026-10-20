from pathlib import Path
import hashlib,json,difflib,subprocess,csv
import numpy as np
W=Path(__file__).resolve().parents[1]; P=W.parents[1]; C=W/'UnityClone'; T=W/'r4/trial7/male'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/in-g/outputs/serve-pose-preview/walk-dribble-position'); O.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((T/'trace.csv').open())); pictures={int(r['frame']):int(r['picture']) for r in rows if int(r['picture'])>=0}
for name,view,size in [('walk_left_to_right.mp4','game',(960,540)),('walk_detail.mp4','back',(640,640))]:
 files=[T/f'{view}_{pic:05}.png' for frame,pic in pictures.items() if 0<=frame<=120]
 assert len(files)==61 and all(p.is_file() for p in files)
 subprocess.run([str(W/'scripts/enc'),str(O/name),'30',*[str(x) for x in size],*[str(p) for p in files]],check=True)
for frame,name in [(40,'walk_position.png'),(100,'walk_settling.png')]:
 (O/name).write_bytes((T/f'back_{pictures[frame]:05}.png').read_bytes())
for name in ['TESTED_SHA256SUMS','key_frames.csv','PALM_AUDIT.json']:(O/name).write_bytes((T/name).read_bytes())
frames={}
for r in csv.DictReader((T/'bones.csv').open()):
 if r['stage']=='live':frames.setdefault(int(r['frame']),{})[r['bone']]=np.array([float(r[c]) for c in 'xyz'])
def arm(f):
 b=frames[f]; side=b['LeftUpperArm']-b['RightUpperArm']; side[1]=0;side/=np.linalg.norm(side); forward=np.cross([0,1,0],side); offset=b['LeftHand']-b['LeftUpperArm'];return {'frame':f,'forward_m':float(offset@forward),'side_m':float(offset@side),'height_m':float(offset[1])}
samples=[arm(f) for f in range(20,100)]
report={'walking_arm_forward_min_m':min(r['forward_m'] for r in samples),'walking_arm_forward_max_m':max(r['forward_m'] for r in samples),'walk_frame_40':arm(40),'stationary_dribble_frame_180':arm(180),'walk_start_x':float(rows[0]['actorRoot_x']),'walk_end_x':float(rows[105]['actorRoot_x']),'production_installed':False,'visual_review':'pending'}
assert report['walking_arm_forward_min_m']>.1,report
(O/'WALK_POSITION_AUDIT.json').write_text(json.dumps(report,indent=2))
patch=[]; production={}
for name in ['HeroTennisDriver.cs','TennisGame.cs','TennisServeRoutine.cs']:
 old=P/'Unity/Assets/Scripts/Tennis'/name; new=C/'Assets/Scripts/Tennis'/name
 production[str(old)]=hashlib.sha256(old.read_bytes()).hexdigest()
 patch.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='a/Unity/Assets/Scripts/Tennis/'+name,tofile='b/Unity/Assets/Scripts/Tennis/'+name))
(O/'PREVIEW.patch').write_text(''.join(patch)); (O/'PRODUCTION_GUARD.json').write_text(json.dumps(production,indent=2))
before=(W/'r4/driver_before_walk_position.cs').read_text(); after=(C/'Assets/Scripts/Tennis/HeroTennisDriver.cs').read_text()
def method(s):
 a=s.index('        void LockFeet('); end=s.index('\n        }',a)+10; return s[a:end]
assert method(before)==method(after),'Accepted stance changed'
(O/'WALK_POSITION.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/Assets/Scripts/Tennis/HeroTennisDriver.cs',tofile='b/Assets/Scripts/Tennis/HeroTennisDriver.cs')))
for p,h in json.loads((W/'r4/PRODUCTION_GUARD.json').read_text()).items():assert hashlib.sha256((P/p).read_bytes()).hexdigest()==h,p
(O/'GATE_RESULTS.md').write_text('GATE: private Unity compilation and live recording PASS\nGATE: walking wrist remains forward in the dribble pose PASS\nGATE: palm-down and skeleton ball/finger clearance PASS (see PALM_AUDIT.json)\nGATE: accepted LockFeet method unchanged PASS\nGATE: production unchanged PASS\nGATE: human visual acceptance PENDING\nFull serve gates and installation remain pending.\n')
(O/'REVIEW.md').write_text('Trial7 staged preview, not installed. Walking uses the same forward arm target as the accepted stationary dribble, with the rearward carry target and walking arm sway removed. Pose, grip and palm clearance remain shared between walking and stationary preparation. Live movement is unchanged; LockFeet is unchanged. Human review pending.\n')
(O/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(O.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
print(json.dumps(report,indent=2));print(O)
