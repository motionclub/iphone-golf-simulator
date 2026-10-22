"""Retain the Ready palm orientation through live carry-to-windup blending.
Only LeftHand rotation keys change. Wrist joint positions remain unchanged.
"""
import sys,math,json
from pathlib import Path
import numpy as np
import loco,kin

T=sys.argv[1];p=Path(loco.DATA)/('gen_serve_'+T+'.npz');z=np.load(p);d={k:z[k] for k in z.files};q=d['quats'].copy();r=loco.Hero(T).rig;h=r.idx['LeftHand'];world=[]
for f in range(76):
 b=np.array([kin.quat_to_mat(v) for v in q[f]]);Q,P=r.fk(b,d['hips'][f]);world.append(kin.mat_to_quat(Q[h]))
def slerp(a,b,u):
 if a@b<0:b=-b
 c=np.clip(a@b,-1,1)
 if c>.9995:
  v=a*(1-u)+b*u;return v/np.linalg.norm(v)
 t=np.arccos(c);return (a*np.sin((1-u)*t)+b*np.sin(u*t))/np.sin(t)
ready=world[6];err=0
for f in range(7,31):
 u=max(0,min(1,(f-21)/9));u=u*u*(3-2*u);target=slerp(ready,world[f],u);b=np.array([kin.quat_to_mat(v) for v in q[f]]);Q,P=r.fk(b,d['hips'][f]);old=P[h].copy();b[h]=r.rel_rot[h].T@Q[r.parent[h]].T@kin.quat_to_mat(np.array(target));q[f,h]=kin.mat_to_quat(b[h]);_,P2=r.fk(b,d['hips'][f]);err=max(err,np.linalg.norm(P2[h]-old))
for f in range(1,76):
 if q[f,h]@q[f-1,h]<0:q[f,h]*=-1
d['quats']=q;np.savez_compressed(p,**d);print('STEADY_LEFT_PALM',T,'joint residual mm',err*1000)
