"""Retain the fixed string pose after contact while unwinding forearm roll.
Wrist joints and racket world transforms stay fixed; only rotation keys change.
"""
import sys,numpy as np,math
import loco,kin
tag=sys.argv[1];p=loco.DATA+'/gen_serve_'+tag+'.npz';z=np.load(p);data={k:z[k] for k in z.files};q=data['quats'].copy();rig=loco.Hero(tag).rig;lo=rig.idx['RightLowerArm'];hand=rig.idx['RightHand']
original=np.load(loco.DATA+'/unsmoothed_serve_'+tag+'.npz')['quats'];q[52,hand]=original[52,hand]
worst=0
for f in range(52,len(q)):
 b=np.array([kin.quat_to_mat(v) for v in q[f]]);Q,P=rig.fk(b,data['hips'][f]);hand_world=Q[hand].copy();beforeP=P[hand].copy()
 M=rig.rel_rot[hand]@b[hand];prevM=rig.rel_rot[hand]@kin.quat_to_mat(q[f-1,hand]);delta=kin.mat_to_quat(M@prevM.T)
 angle=2*math.atan2(delta[2],delta[0]);angle=(angle+math.pi)%(2*math.pi)-math.pi
 c,ss=np.cos(angle),np.sin(angle);turn=np.array([[c,0,ss],[0,1,0],[-ss,0,c]])
 newLo=Q[lo]@turn;b[lo]=rig.rel_rot[lo].T@Q[rig.parent[lo]].T@newLo
 b[hand]=rig.rel_rot[hand].T@newLo.T@hand_world
 q[f,lo]=kin.mat_to_quat(b[lo]);q[f,hand]=kin.mat_to_quat(b[hand]);_,newP=rig.fk(b,data['hips'][f]);worst=max(worst,float(np.linalg.norm(newP[hand]-beforeP)))
for f in range(1,len(q)):
 for j in [lo,hand]:
  if q[f,j]@q[f-1,j]<0:q[f,j]*=-1
print('CONTACT_HOLD',tag,'hand position residual mm',round(worst*1000,6));data['quats']=q;np.savez_compressed(p,**data)
