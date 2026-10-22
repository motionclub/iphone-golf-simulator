import json,numpy as np
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29';O=W/'revision2'
def qmat(q):
 x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def turn(axis,angle):
 x,y,z=axis;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);a=np.radians(angle);return np.eye(3)+np.sin(a)*K+(1-np.cos(a))*(K@K)
def solve(S,E,H,P,C,axis):
 P=P/np.linalg.norm(P);a=np.linalg.norm(E-S);b=np.linalg.norm(H-E);angle=np.degrees(np.arccos(np.clip((H-E)@P/b,-1,1)))
 if angle<=35:return 0.,H,E,angle
 deg=np.arange(-45,46);T=np.array([turn(axis,d) for d in deg]);targets=C+np.einsum('nij,j->ni',T,H-C);F=targets-S;D=np.linalg.norm(F,axis=1);F/=D[:,None];along=(a*a-b*b+D*D)/(2*D);centre=S+F*along[:,None];pole=E-centre;pole-=F*np.einsum('ij,ij->i',pole,F)[:,None];pn=np.linalg.norm(pole,axis=1);trial=centre+pole/np.maximum(pn[:,None],1e-20)*np.sqrt(np.maximum(0,a*a-along*along))[:,None];shift=np.linalg.norm(trial-E,axis=1);angles=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',targets-trial,np.einsum('nij,j->ni',T,P))/b,-1,1)));cost=angles**2+.12*deg**2+50000*shift**2;valid=(np.linalg.norm(targets-H,axis=1)<=.04)&(D<a+b-.00001)&(D>abs(a-b)+.00001)&(pn>1e-5)&(shift<=.04);cost[~valid]=np.inf;i=np.argmin(cost);selected=float(deg[i]) if cost[i]<angle*angle else 0.;u=np.clip((angle-35)/15,0,1);selected*=u*u*(3-2*u)
 if abs(selected)<1e-4:return 0.,H,E,angle
 T=turn(axis,selected);target=C+T@(H-C);F=target-S;D=np.linalg.norm(F);F/=D;along=(a*a-b*b+D*D)/(2*D);centre=S+F*along;pole=E-centre;pole-=F*(pole@F);pn=np.linalg.norm(pole)
 if D>=a+b-.00001 or D<=abs(a-b)+.00001 or pn<1e-5:return 0.,H,E,angle
 trial=centre+pole/pn*np.sqrt(max(0,a*a-along*along))
 if np.linalg.norm(trial-E)>.04:return 0.,H,E,angle
 return selected,target,trial,angle
report=[]
for sex in ('Male','Female'):
 d=json.loads((R/f'work/reference-rebuild/original-native-adoption1/export/GolfKitHero_{sex}.json').read_text());r=d['rig'];names=r['bones'];raw=(W/f'{sex}.rig.raw').read_bytes()
 for c in r['clips']:
  if not c['id'].startswith('golf'):continue
  tracks=np.frombuffer(raw,'<f4',c['frames']*r['trackCount']*10,c['offset']).reshape(c['frames'],r['trackCount'],10).astype(float);times=np.array(c['times']);club=names.index('Club')
  for side in ('Left','Right'):
   ids=[names.index(side+s) for s in ('UpperArm','LowerArm','Hand','MiddleProximal')]
   def evaluate(t):
    C=t[club,:3];axis=qmat(t[club,3:7])@np.array([0.,0.,1.]);axis/=np.linalg.norm(axis);S,E,H,M=t[ids,:3];return solve(S,E,H,M-H,C,axis)
   out=[evaluate(t) for t in tracks];roll=np.array([v[0] for v in out]);wrist=np.array([v[1] for v in out]);elbow=np.array([v[2] for v in out]);original=np.array([v[3] for v in out]);ws=wrist-tracks[:,ids[2],:3];es=elbow-tracks[:,ids[1],:3];jumps=np.linalg.norm(np.diff(ws,axis=0),axis=1)*1000;ejumps=np.linalg.norm(np.diff(es,axis=0),axis=1)*1000;rd=np.abs(np.diff(roll));worst=np.argsort(jumps)[-4:][::-1];probes=[]
   # Evaluate both sides of quantized decision boundaries at 1e-7 seconds.
   for idx in worst:
    lo,hi=0.,1.;base=roll[idx]
    def lerp(u):
     t=tracks[idx]*(1-u)+tracks[idx+1]*u
     for bone in (club,):
      q1=tracks[idx,bone,3:7];q2=tracks[idx+1,bone,3:7];q2=q2 if q1@q2>=0 else -q2;q=q1*(1-u)+q2*u;t[bone,3:7]=q/np.linalg.norm(q)
     return t
    # Focus a boundary between two differently quantized selected outputs.
    for _ in range(28):
     mid=(lo+hi)/2
     if abs(evaluate(lerp(mid))[0]-base)<1e-3:lo=mid
     else:hi=mid
    width=1e-7/max(times[idx+1]-times[idx],1e-12);a=max(0,hi-width);b=min(1,hi+width);oa=evaluate(lerp(a));ob=evaluate(lerp(b));ha=lerp(a)[ids[2],:3];hb=lerp(b)[ids[2],:3];ea=lerp(a)[ids[1],:3];eb=lerp(b)[ids[1],:3]
    probes.append({'sourceTime':float(times[idx]+hi*(times[idx+1]-times[idx])),'rollStepDegrees':abs(ob[0]-oa[0]),'correctionStepMm':float(np.linalg.norm((ob[1]-hb)-(oa[1]-ha))*1000),'elbowCorrectionStepMm':float(np.linalg.norm((ob[2]-eb)-(oa[2]-ea))*1000)})
   row={'sex':sex,'clip':c['id'],'side':side,'frames':c['frames'],'activeFrames':int(np.count_nonzero(roll)),'maxSourceIntervalSec':float(np.diff(times).max()),'maxNeighborRollChangeDegrees':float(rd.max()),'maxNeighborWristCorrectionChangeMm':float(jumps.max()),'maxNeighborElbowCorrectionChangeMm':float(ejumps.max()),'maxWristShiftMm':float(np.linalg.norm(ws,axis=1).max()*1000),'maxElbowShiftMm':float(np.linalg.norm(es,axis=1).max()*1000),'thresholdSamples35to50':int(((original>35)&(original<50)).sum()),'boundaryProbes':probes};report.append(row)
(O/'dense-continuity.json').write_text(json.dumps({'status':'SOURCE_CONTINUITY_REVIEW_NOT_RUNTIME_PASS','source':'accepted pre-roll adaptive native source track; all recorded samples; model metre scale','tracks':report,'note':'Sub-frame probes interpolate recorded world positions and Club rotation. Measures candidate correction separately from existing source motion. Quantized roll, feasibility gates, and final 40mm rejection may create discontinuities; appearance gate separate.'},indent=2)+'\n')
print(json.dumps({'tracks':len(report),'samples':sum(v['frames'] for v in report),'maxNeighborRollChangeDegrees':max(v['maxNeighborRollChangeDegrees'] for v in report),'maxNeighborCorrectionChangeMm':max(v['maxNeighborWristCorrectionChangeMm'] for v in report),'maxBoundaryCorrectionStepMm':max(x['correctionStepMm'] for v in report for x in v['boundaryProbes'])},indent=2))
