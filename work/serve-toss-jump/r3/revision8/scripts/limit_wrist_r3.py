"""Bound Serve wrist key rotations, preserving the exact racket contact keys.
The live trace remains the acceptance test, including longitudinal twist.
"""
import sys,numpy as np
import loco
tag=sys.argv[1];path=loco.DATA+'/gen_serve_'+tag+'.npz'
z=np.load(path);data={k:z[k] for k in z.files};q=data['quats'].copy();rig=loco.Hero(tag).rig
def angle(a,b):return np.degrees(2*np.arccos(np.clip(abs(a@b),-1,1)))
def toward(anchor,value,limit=10):
 d=angle(anchor,value)
 if d<=limit:return value
 if anchor@value<0:value=-value
 theta=np.radians(d/2);u=limit/d
 out=np.sin((1-u)*theta)/np.sin(theta)*anchor+np.sin(u*theta)/np.sin(theta)*value
 return out/np.linalg.norm(out)
for name in ['LeftHand','RightHand']:
 j=rig.idx[name];before=max(angle(a,b) for a,b in zip(q[:-1,j],q[1:,j]))
 if name=='LeftHand':
  for f in range(7,len(q)):q[f,j]=toward(q[f-1,j],q[f,j])
 else:
  # The 1.667 and 1.700 keys retain the measured strings exactly.
  for _ in range(25):
   for f in range(49,6,-1):q[f,j]=toward(q[f+1,j],q[f,j])
   for f in range(7,50):q[f,j]=toward(q[f-1,j],q[f,j])
  for f in range(52,len(q)):q[f,j]=toward(q[f-1,j],q[f,j])
 after=max(angle(a,b) for a,b in zip(q[:-1,j],q[1:,j]))
 print('WRIST_LIMIT',tag,name,round(before,3),'->',round(after,3),'degrees/key')
data['quats']=q;np.savez_compressed(path,**data)
