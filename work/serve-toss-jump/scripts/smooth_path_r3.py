"""Smooth the existing solved racket wrist in world space, retaining contact keys.
Only right arm rotations change. The live trace is the acceptance test.
"""
import sys,numpy as np
import loco,kin
tag=sys.argv[1];p=loco.DATA+'/gen_serve_'+tag+'.npz';z=np.load(p);data={k:z[k] for k in z.files};q=data['quats'].copy();hero=loco.Hero(tag);rig=hero.rig;S=hero.S
S.min_wrist_r=.20*S.A_arm
u,l,h=[rig.idx['Right'+n] for n in ['UpperArm','LowerArm','Hand']]
bases=np.array([[kin.quat_to_mat(v) for v in f] for f in q]);frames=[rig.fk(b,hl) for b,hl in zip(bases,data['hips'])]
path=np.array([P[h] for Q,P in frames]);old=path.copy();pins=set(range(13))|{34,50,51,52,75}
for _ in range(60):
 prev=path.copy()
 for f in range(13,75):
  if f not in pins:path[f]=.25*prev[f-1]+.5*prev[f]+.25*prev[f+1]
# Re-solve the same two arm bones with a continuously transported elbow pole.
prev_axis=None;prev_pole=None
for f,(Q,P) in enumerate(frames):
 axis=kin.unit(path[f]-P[u]);pole=P[l]-P[u];pole=kin.unit(pole-axis*(pole@axis))
 if f in pins:prev_axis=axis;prev_pole=pole;continue
 if prev_axis is not None:
  v=np.cross(prev_axis,axis);c=float(np.clip(prev_axis@axis,-1,1));K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
  if c>-.9999:pole=(np.eye(3)+K+K@K/(1+c))@prev_pole
 S.reset();ik=S._arm_ik('R',P[u],path[f],pole)
 b=bases[f].copy();desired={u:ik['Qu'],l:ik['Ql'],h:Q[h]}
 for j in [u,l,h]:
  Qn,Pn=rig.fk(b,data['hips'][f]);b[j]=rig.rel_rot[j].T@Qn[rig.parent[j]].T@desired[j];q[f,j]=kin.mat_to_quat(b[j])
 prev_axis=axis;prev_pole=kin.unit(pole-axis*(pole@axis))
for f in range(1,len(q)):
 for j in [u,l,h]:
  if q[f,j]@q[f-1,j]<0:q[f,j]*=-1
print('WORLD_HAND_SMOOTH',tag,'max raw key step',round(np.linalg.norm(np.diff(old,axis=0),axis=1).max()*1000,2),'smoothed goal',round(np.linalg.norm(np.diff(path,axis=0),axis=1).max()*1000,2),'contact unchanged',np.max(abs(q[50:53]-data['quats'][50:53])))
data['quats']=q;np.savez_compressed(p,**data)
