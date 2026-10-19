"""Fair only the axilla connector. The biceps surface is fixed to preserve arm volume."""
from pathlib import Path
import sys,json,numpy as np
from mathutils import Matrix
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'clothing-v2/py'))
import cv2io,glib as G
cv2io.DUMP=str(root/'dump-arm-volume');h=cv2io.Hero('GolfKitHero_Female' if '--golf' in sys.argv else 'MatchHero_Female');p=h.body.pos
_,inv,counts=np.unique(np.round(p,5),axis=0,return_inverse=True,return_counts=True);n=len(counts)
def weld(x):
 a=np.zeros((n,3));np.add.at(a,inv,x);return a/counts[:,None]
def sm(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
rp=weld(p);tri=inv[h.body.tri];nb=G.neighbours(n,tri)
ci=h.body.bones.index('Chest');ui=[h.body.bones.index(s+'UpperArm')for s in ['Left','Right']];li=[h.body.bones.index(s+'LowerArm')for s in ['Left','Right']]
def quat(b,side):
 q=Matrix(b[ci,:3,:3]).to_quaternion().inverted()@Matrix(b[ui[side],:3,:3]).to_quaternion();return np.array([q.x,q.y,q.z,q.w])
def angle(b,side):
 d=np.linalg.inv(h.rest_bones[ci])[:3,:3]@(h.rest_bones[li[side],:3,3]-h.rest_bones[ui[side],:3,3]);d/=np.linalg.norm(d)
 v=np.linalg.inv(b[ci])[:3,:3]@(b[li[side],:3,3]-b[ui[side],:3,3]);v/=np.linalg.norm(v);return float(np.degrees(np.arccos(np.clip(d@v,-1,1))))
frames={c['name']:h.clip(c['name'])for c in h.clips}
records=[];deltas=[];normald=[]
for side in [0,1]:
 sign=np.sign(h.body.bind[ui[side]].__array__()[:3,3][0])
 # Read the shoulder's bind position rather than assuming left is positive.
 sign=np.sign(np.linalg.inv(h.body.bind[ui[side]])[0,3])
 boundary=.130+(.105-.130)*np.clip((rp[:,2]-1.18)/(.19),0,1)
 field=sm(.085,.105,sign*rp[:,0])*(1-sm(boundary-.004,boundary+.009,sign*rp[:,0]))*sm(1.10,1.16,rp[:,2])*(1-sm(1.315,1.365,rp[:,2]))*(1-sm(.065,.10,np.abs(rp[:,1]-.005)))
 candidates=[]
 for name,(bf,bones) in frames.items():
  for fi in range(len(bf)):
   b=bones[fi].astype(float);e=angle(b,side)
   if e>55:candidates.append((name,fi,quat(b,side),e))
 chosen=[]
 # Include the visibly problematic overhead celebration before covering other reaches.
 joy=[x for x in candidates if 'JumpJoy' in x[0]]
 if joy:chosen=[max(joy,key=lambda x:x[3])]
 elif candidates:chosen=[max(candidates,key=lambda x:x[3])]
 else:continue
 while len(chosen)<12:
  dist=[min(1-float(x[2]@y[2])**2 for y in chosen)for x in candidates];j=int(np.argmax(dist))
  if dist[j]<.003:break
  chosen.append(candidates[j])
 for name,fi,q,e in chosen:
  posed=frames[name][0][fi].astype(float);bones=frames[name][1][fi].astype(float);base=weld(posed);target=base.copy()
  for _ in range(16):target+=.45*G.umbrella(target,nb)*field[:,None]
  d=(target-base);length=np.linalg.norm(d,axis=1);d*=np.minimum(1,.012/np.maximum(length,1e-12))[:,None]
  dp=d[inv];targetFull=posed+dp
  skin=h.skin_matrices(bones);A=np.zeros((len(p),3,3))
  for k in range(4):A+=h.body.bw[:,k,None,None]*skin[h.body.bi[:,k],:3,:3]
  u,s,vt=np.linalg.svd(A)
  inverse=np.einsum('nij,nj,nkj->nik',vt.transpose(0,2,1),s/(s*s+.01**2),u)
  db=np.einsum('nij,nj->ni',inverse,dp)
  db*=np.minimum(1,.020/np.maximum(np.linalg.norm(db,axis=1),1e-12))[:,None]
  dn=G.vertex_normals(targetFull,h.body.tri)-G.vertex_normals(posed,h.body.tri)
  dn=np.einsum("nij,nj->ni",inverse,dn);dn[np.linalg.norm(db,axis=1)<1e-6]=0
  deltas.append(db);normald.append(dn);records.append(dict(side=side,rotation=q.tolist(),clip=name,frame=fi,elevation=e))
  print(side,name,fi,round(e),'posed move mm',round(float(np.linalg.norm(dp,axis=1).max()*1000)),flush=True)
  if len(records)==1:
   np.savez(root/'out/shoulder-preview.npz',before=posed,after=targetFull,tri=h.body.tri)
active=np.nonzero(np.max(np.linalg.norm(np.array(deltas),axis=2),axis=0)>1e-6)[0]
folder=root/'out'/('shoulder-golf' if h.golf else 'shoulder');folder.mkdir(exist_ok=True)
with (folder/'FemaleShoulderFit.bytes').open('wb')as f:
 f.write(np.array([len(p),len(active),len(records)],np.int32).tobytes());f.write(active.astype(np.int32).tobytes())
 for dp,dn in zip(deltas,normald):f.write(dp[active].astype(np.float32).tobytes());f.write(dn[active].astype(np.float32).tobytes())
(folder/'FemaleShoulderFit.json').write_text(json.dumps({'anchors':records},separators=(',',':')))
print('Finished',len(records),'shapes;',len(active),'sparse vertices')
