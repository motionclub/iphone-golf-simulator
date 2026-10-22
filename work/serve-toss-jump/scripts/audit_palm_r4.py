from pathlib import Path
import csv, json, sys
import numpy as np
p=Path(sys.argv[1]); rows=list(csv.DictReader((p/'trace.csv').open())); frames={}
for r in csv.DictReader((p/'bones.csv').open()):
 if r['stage']=='live': frames.setdefault(int(r['frame']),{})[r['bone']]=np.array([float(r[c]) for c in 'xyz'])
result=[]
for r in rows:
 if r['flow']!='PlayerServeHold' or float(r['prepare'])>.001: continue
 f=int(r['frame']); b=frames[f]; hand=b['LeftHand']; mid=b['LeftMiddleProximal']; idx=b['LeftIndexProximal']
 palm=hand*.3+mid*.7; n=-np.cross(mid-hand,idx-hand); n/=np.linalg.norm(n)
 ball=np.array([float(r['ball_'+c]) for c in 'xyz']); plane=float((ball-palm)@n)
 closest=(1e9,'')
 for name,a in b.items():
  if not name.startswith('Left') or not any(s in name for s in ('Index','Middle','Ring','Little','Thumb')): continue
  parent='LeftHand' if 'Proximal' in name else name.replace('Intermediate','Proximal').replace('Distal','Intermediate')
  if parent not in b: continue
  v=a-b[parent]; t=np.clip((ball-b[parent])@v/max(v@v,1e-12),0,1); d=float(np.linalg.norm(ball-(b[parent]+v*t)))
  if d<closest[0]: closest=(d,name)
 result.append(dict(frame=f,palmDown=float(-n[1]),planeClearance_mm=(plane-.1)*1000,nearestFingerSurface_mm=(closest[0]-.1-.008)*1000,nearestFinger=closest[1]))
out={'frames':len(result),'minimum_plane':min(result,key=lambda r:r['planeClearance_mm']),'minimum_finger':min(result,key=lambda r:r['nearestFingerSurface_mm']),'min_palmDown':min(r['palmDown'] for r in result),'samples':result}
(p/'PALM_AUDIT.json').write_text(json.dumps(out,indent=2)); print(json.dumps({k:v for k,v in out.items() if k!='samples'},indent=2))
