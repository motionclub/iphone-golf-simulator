"""Bind the sewn sleeve continuously between torso seam and upper-arm cuff."""
from pathlib import Path
import json,sys,numpy as np
r=Path(__file__).resolve().parent;sys.path[:0]=[str(r.parent/'clothing-v2/py')]
import cv2io,glib as G
from mathutils.bvhtree import BVHTree
from mathutils import Vector
cv2io.DUMP=str(r/'dump-polo');h=cv2io.Hero('GolfKitHero_Female');u=r/'out/GolfKitHero_Female/unity'
g=dict(np.load(u/'Kit_Top_final.npz'));p=g['pos'];n=len(p);W=np.zeros((n,len(h.body.bones)))
for k in range(4):np.add.at(W,(np.arange(n),g['bi'][:,k]),g['bw'][:,k])
original=W.copy();torso_faces=g['tri'][np.isin(g['panel'],[0,1])];torso=np.unique(torso_faces);sleeve=np.zeros(n,bool);sleeve[np.unique(g['tri'][np.isin(g['panel'],[2,3,6])])]=True
R=json.loads((r/'source/golf_sleeve_pattern.json').read_text())
# Sew the small source-pattern gap before binding. Preserve separate outside
# and lining surfaces; corresponding seam points get exactly the torso field.
vpart=np.ones(n,int)
for part in [2,0]:vpart[np.unique(g['tri'][g['part']==part])]=part
for part in [0,2]:
 faces=g['tri'][np.isin(g['panel'],[0,1])&(g['part']==part)]
 tree=BVHTree.FromPolygons(p.tolist(),faces.tolist(),all_triangles=True)
 for i in np.flatnonzero(sleeve&(vpart==part)):
  roots=np.concatenate([np.asarray(R[str(side)])[0]for side in [-1,1]])
  if np.linalg.norm(roots-p[i],axis=1).min()>.020:continue
  q,_,fi,d=tree.find_nearest(Vector(p[i]))
  if q is None or d>.012:continue
  t=faces[fi];a,b,c=p[t];v0=b-a;v1=c-a;v2=np.asarray(q)-a;aa=v0@v0;ab=v0@v1;bb=v1@v1;ac=v0@v2;bd=v1@v2;den=max(aa*bb-ab*ab,1e-20);x=(bb*ac-ab*bd)/den;y=(aa*bd-ab*ac)/den;bar=np.clip([1-x-y,x,y],0,1);bar/=bar.sum()
  p[i]=np.asarray(q);W[i]=(original[t]*bar[:,None]).sum(0)
original=W.copy()

for side in [-1,1]:
 root=np.asarray(R[str(side)])[0];delta=p[:,None]-root[None];near=np.argmin((delta*delta).sum(2),1);distance=np.linalg.norm(p-root[near],axis=1)
 closest=np.argmin(((root[:,None]-p[torso][None])**2).sum(2),1);rootW=original[torso[closest]].copy()
 # At the seam use the torso palette, never the arm-side UV duplicate.
 for j,name in enumerate(h.body.bones):
  if name not in ['Hips','Spine','Chest','UpperChest','Neck']:rootW[:,j]=0
 rootW/=np.maximum(rootW.sum(1,keepdims=True),1e-10)
 t=np.clip((distance-.020)/.055,0,1);t=t*t*(3-2*t);mask=sleeve&(p[:,0]*side>0)
 W[mask]=rootW[near[mask]]*(1-t[mask,None]);W[mask,h.body.bones.index('LeftUpperArm'if side<0 else'RightUpperArm')]+=t[mask]
 cuff=np.zeros(n,bool);cuff[np.unique(g['tri'][g['panel']==6])]=True;cuff&=p[:,0]*side>0;W[cuff]=0;W[cuff,h.body.bones.index('LeftUpperArm'if side<0 else'RightUpperArm')]=1
bi,bw=G.prune(W,4);g['bi']=bi;g['bw']=bw
# Coincident sewing/UV vertices share a binding.
_,inverse=np.unique(np.round(p,5),axis=0,return_inverse=True)
for group in range(inverse.max()+1):
 ids=np.flatnonzero(inverse==group)
 if len(ids)>1:
  w=W[ids].mean(0);W[ids]=w
bi,bw=G.prune(W,4);g['bi']=bi;g['bw']=bw
g['pos']=p
np.savez(u/'Kit_Top_final.npz',**g)
m=json.loads((u/'manifest.json').read_text());piece=next(x for x in m['pieces']if x['name']=='Kit_Top');palette=[h.body.bones.index(name)for name in piece['bones']];remap=np.zeros(len(h.body.bones),int)
for i,b in enumerate(palette):remap[b]=i
with (u/'Kit_Top.bin').open('wb')as f:
 for a in [p.astype(np.float32),g['nrm'].astype(np.float32),g['uv'].astype(np.float32),remap[bi].astype(np.int32),bw.astype(np.float32),g['tri'].astype(np.int32)]:f.write(a.tobytes())
(u/'Kit_Top_shapes.bin').write_bytes(np.asarray([0,n],np.int32).tobytes())
(u/'Kit_Top_correctives.json').write_text('{"anchors":[]}')
print('Sewn sleeve binding:',n,'vertices; no large corrective shapes')
