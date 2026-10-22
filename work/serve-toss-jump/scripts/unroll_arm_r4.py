"""Restore anatomical forearm roll; preserve joint positions and global hand pose."""
from pathlib import Path
import sys,numpy as np,json
sys.path.insert(0,str(Path(__file__).parent));import loco,kin
W=Path(loco.WORK)
for tag in ['male','female']:
 h=loco.Hero(tag);rig=h.rig;ix=rig.idx;src=W/'r3/final_candidate/data'/('gen_serve_'+tag+'.npz');z=np.load(src);d={k:z[k].copy() for k in z.files};pre=np.load(W/'r3'/('before_wrist_roll_'+tag+'.npz'))
 q=d['quats'];old=q.copy();lo=ix['LeftLowerArm'];hand=ix['LeftHand'];err=0;maxroll=0
 for f in range(len(q)):
  b=np.array([kin.quat_to_mat(v) for v in q[f]]);Q,P=rig.fk(b,d['hips'][f]);keep=Q[hand].copy();points=P.copy()
  b[lo]=kin.quat_to_mat(pre['quats'][f,lo]);Q2,P2=rig.fk(b,d['hips'][f]);b[hand]=rig.rel_rot[hand].T@Q2[lo].T@keep
  for j in [lo,hand]:q[f,j]=kin.mat_to_quat(b[j])
  _,P2=rig.fk(b,d['hips'][f]);err=max(err,float(np.linalg.norm(P2-points,axis=1).max()))
  maxroll=max(maxroll,float(np.degrees(2*np.arccos(np.clip(abs(old[f,lo]@q[f,lo]),0,1)))))
 for f in range(1,len(q)):
  for j in [lo,hand]:
   if q[f,j]@q[f-1,j]<0:q[f,j]*=-1
 np.savez_compressed(W/'data'/('gen_serve_r4_'+tag+'.npz'),**d)
 print(tag,'removed maximum fitted roll',maxroll,'joint position residual mm',err*1000)
