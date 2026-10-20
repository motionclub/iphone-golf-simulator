"""Fit an authored forearm-roll correction to the measured live wrist twists.
Hand world rotations and all joint positions are retained; live proof accepts it.
"""
import sys,csv,json,math
from pathlib import Path
import numpy as np
import loco,kin
from metrics_r3 import qm,qi,quat,point,rotate
tag=sys.argv[1];directory=Path(sys.argv[2]);path=Path(loco.DATA)/('gen_serve_'+tag+'.npz');z=np.load(path);data={k:z[k] for k in z.files};q=data['quats'].copy();rig=loco.Hero(tag).rig
rows=list(csv.DictReader((directory/'trace.csv').open()));entry=next(i for i,r in enumerate(rows) if r['state'].startswith('Serve'));end=next(i for i in range(entry+1,len(rows)) if not rows[i]['state'].startswith('Serve'));rows=rows[entry:end];bones={}
for r in csv.DictReader((directory/'bones.csv').open()):
 if r['stage']=='live' and entry<=int(r['frame'])<end:bones.setdefault(int(r['frame']),{})[r['bone']]=r
constraints=[]
def weights(t):
 f=np.clip(t*30,0,75);lo=int(np.floor(f));hi=min(75,lo+1);a=np.zeros(76);a[lo]+=1-(f-lo);a[hi]+=f-lo;return a
for a,b in zip(rows,rows[1:]):
 if float(b['clipTime'])<.25 or float(a['clipTime'])<.25:continue
 prev,now=bones[int(a['frame'])],bones[int(b['frame'])];fore,hand='LeftLowerArm','LeftHand'
 q0=qm(qi(quat(prev[fore])),quat(prev[hand]));q1=qm(qi(quat(now[fore])),quat(now[hand]));delta=qm(q1,qi(q0));axis=rotate(qi(quat(now[fore])),point(now[hand])-point(now[fore]));axis/=np.linalg.norm(axis)
 deg=math.degrees(2*math.atan2(delta[:3]@axis,delta[3]));deg=(deg+180)%360-180
 coeff=weights(float(b['clipTime']))-weights(float(a['clipTime']));coeff[:8]=0
 constraints.append((coeff,deg,int(b['frame']),float(b['clipTime'])))
theta=np.zeros(76);limit=10
for _ in range(2000):
 worst=0
 for a,d,f,t in constraints:
  residual=d-a@theta;excess=residual-np.clip(residual,-limit,limit);norm=a@a
  worst=max(worst,abs(excess))
  if norm>1e-9:theta+=a*excess/norm
 if worst<.001:break
lo=rig.idx['LeftLowerArm'];hand=rig.idx['LeftHand'];position_error=0
for f,angle in enumerate(theta):
 b=np.array([kin.quat_to_mat(v) for v in q[f]]);Q,P=rig.fk(b,data['hips'][f]);keep=Q[hand].copy();old=P[hand].copy();c,s=np.cos(np.radians(-angle)),np.sin(np.radians(-angle));turn=np.array([[c,0,s],[0,1,0],[-s,0,c]])
 newLo=Q[lo]@turn;b[lo]=rig.rel_rot[lo].T@Q[rig.parent[lo]].T@newLo;b[hand]=rig.rel_rot[hand].T@newLo.T@keep
 q[f,lo]=kin.mat_to_quat(b[lo]);q[f,hand]=kin.mat_to_quat(b[hand]);_,P2=rig.fk(b,data['hips'][f]);position_error=max(position_error,float(np.linalg.norm(P2[hand]-old)))
for f in range(1,76):
 for j in [lo,hand]:
  if q[f,j]@q[f-1,j]<0:q[f,j]*=-1
np.savez_compressed(Path(loco.WORK)/'r3'/('before_wrist_roll_'+tag+'.npz'),**data)
data['quats']=q;np.savez_compressed(path,**data)
report=dict(inputTrace=str(directory),predictedMaxDegrees=max(abs(d-a@theta) for a,d,f,t in constraints),thetaDegrees=theta.tolist(),positionResidual_mm=position_error*1000,measuredWorst=max((dict(degrees=abs(d),signed=d,frame=f,clipTime=t) for a,d,f,t in constraints),key=lambda r:r['degrees']))
(Path(loco.WORK)/'r3'/('wrist_roll_fit_'+tag+'.json')).write_text(json.dumps(report,indent=2));print('WRIST_ROLL_FIT',tag,report['measuredWorst'],'predicted',report['predictedMaxDegrees'],'hand position residual mm',report['positionResidual_mm'])
