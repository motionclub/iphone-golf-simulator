"""Smooth the right arm's local rotations while pinning stance, fixed contact and end.
No translations, scales, left-arm or body keys change. All rotations stay unit length.
"""
import sys, json
import numpy as np
import loco, kin
tag=sys.argv[1]
p=loco.DATA+'/gen_serve_'+tag+'.npz'
z=np.load(p); data={k:z[k] for k in z.files}; q=data['quats'].copy()
np.savez_compressed(loco.DATA+'/unsmoothed_serve_'+tag+'.npz',**data)
rig=loco.Hero(tag).rig
names=['RightShoulder','RightUpperArm','RightLowerArm','RightHand']
names=[n for n in names if n in rig.idx]
ix=[rig.idx[n] for n in names]
pins=np.r_[np.arange(13),51,75]
orig=q.copy()
for _ in range(7):
    prev=q.copy()
    for f in range(13,75):
        if f==51:continue
        for j in ix:
            a=prev[f-1,j].copy();b=prev[f+1,j].copy();c=prev[f,j]
            if np.dot(a,c)<0:a=-a
            if np.dot(b,c)<0:b=-b
            v=.25*a+.5*c+.25*b
            q[f,j]=v/np.linalg.norm(v)
q[pins]=orig[pins]
data['quats']=q
np.savez_compressed(p,**data)
print('SMOOTH',tag,'7 diffusion passes',names,'contact rotation delta',float(np.max(np.abs(q[51]-orig[51]))))
