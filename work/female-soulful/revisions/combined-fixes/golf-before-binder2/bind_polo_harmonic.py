"""Garment-wide harmonic sleeve bindings: construction inputs only, no poses."""
from pathlib import Path
import json,sys,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'clothing-v2/py'))
import cv2io,glib as G
cv2io.DUMP=str(r/'dump-polo');h=cv2io.Hero('GolfKitHero_Female')
u=r/'out/GolfKitHero_Female/unity';baseline=r/'revisions/general-garment-before'
g=dict(np.load(r/'cage-prototype/unprojected-top.npz'));p=g['pos'];n=len(p)
W=np.zeros((n,len(h.body.bones)))
for k in range(4):np.add.at(W,(np.arange(n),g['bi'][:,k]),g['bw'][:,k])
torso=[h.body.bones.index(name)for name in ['Hips','Spine','Chest','UpperChest','Neck']]
# Reconstruct a torso field from torso-only source vertices. Sleeve source
# fields may contain only an arm and therefore are not valid torso anchors.
tris=g['tri'];outer=tris[(g['part']==0)&np.isin(g['panel'],[0,1,2,3])]
torso_faces=tris[(g['part']==0)&np.isin(g['panel'],[0,1])]
tree=BVHTree.FromPolygons(p.tolist(),torso_faces.tolist(),all_triangles=True)
T=W[:,torso].copy()
valid=np.flatnonzero(T.sum(1)>.00001);tree_torso=KDTree(len(valid))
for i in valid:tree_torso.insert(Vector(p[i]),int(i))
tree_torso.balance()
for i in range(n):
 if T[i].sum()>.00001:T[i]/=T[i].sum();continue
 _,j,_=tree_torso.find(Vector(p[i]))
 T[i]=W[j,torso];T[i]/=max(T[i].sum(),1e-12)
assert np.allclose(T.sum(1),1),'Every vertex needs a normalized torso field before sleeve blending'
# Shared sewing/UV positions are one graph node. All layers receive the
# resulting outer-shell field, avoiding independent lining motion.
unique,inverse=np.unique(np.round(p,5),axis=0,return_inverse=True)
edges=np.concatenate([outer[:,[0,1]],outer[:,[1,2]],outer[:,[2,0]]]);edges=np.sort(inverse[edges],axis=1)
edges=np.unique(edges[edges[:,0]!=edges[:,1]],axis=0)
src=np.r_[edges[:,0],edges[:,1]];dst=np.r_[edges[:,1],edges[:,0]]
distance=np.linalg.norm(unique[src]-unique[dst],axis=1);conductance=1/np.maximum(distance,.002)
degree=np.bincount(src,weights=conductance,minlength=len(unique))
outer_ids=np.unique(outer);nodes=np.unique(inverse[outer_ids]);result=np.zeros((len(unique),2))
for column,side in enumerate([-1,1]):
 # The stable centre/lower torso and neckline are fixed. Sleeve mouths are
 # fixed to the arm. The entire shoulder between them is solved together.
 fixed=(np.abs(unique[:,0])<.075)|(unique[:,2]<1.10)|(unique[:,2]>1.405)
 sleeve_ids=np.unique(tris[np.isin(g['panel'],[2,3])]);end_ids=sleeve_ids[(g['a_d_cuff'][sleeve_ids]<.027)&(p[sleeve_ids,0]*side>0)]
 cuff=np.isin(np.arange(len(unique)),inverse[end_ids])
 fixed|=cuff;value=np.zeros(len(unique));value[cuff]=1
 for step in range(900):
  mean=np.bincount(src,weights=conductance*value[dst],minlength=len(unique))/np.maximum(degree,1e-12)
  mean[fixed]=value[fixed];value=.15*value+.85*mean
 result[:,column]=value
# Transfer shell fields to lining and separate cuff surfaces spatially, with
# side discrimination. Both thickness surfaces share the same low-frequency field.
shell=BVHTree.FromPolygons(p.tolist(),outer.tolist(),all_triangles=True)
arm=result[inverse].copy();is_outer=np.zeros(n,bool);is_outer[outer_ids]=True
for i in np.flatnonzero(~is_outer):
 q,_,fi,_=shell.find_nearest(Vector(p[i]));t=outer[fi];near=t[np.argmin(np.linalg.norm(p[t]-np.asarray(q),axis=1))];arm[i]=arm[near]
cuff_ids=np.unique(tris[g['panel']==6]);arm[cuff_ids]=0
for column,side in enumerate([-1,1]):arm[cuff_ids[p[cuff_ids,0]*side>0],column]=1
arm=np.clip(arm,0,1);total=arm.sum(1);arm/=np.maximum(total[:,None],1)
W[:]=0;W[:,torso]=T*(1-arm.sum(1))[:,None]
for column,name in enumerate(['LeftUpperArm','RightUpperArm']):W[:,h.body.bones.index(name)]=arm[:,column]
bi,bw=G.prune(W,4);g['bi']=bi;g['bw']=bw
np.savez(u/'Kit_Top_final.npz',**g)
m=json.loads((u/'manifest.json').read_text());piece=next(x for x in m['pieces']if x['name']=='Kit_Top');palette=[h.body.bones.index(name)for name in piece['bones']]
remap=np.zeros(len(h.body.bones),int)
for i,b in enumerate(palette):remap[b]=i
with (u/'Kit_Top.bin').open('wb')as f:
 for a in [p.astype(np.float32),g['nrm'].astype(np.float32),g['uv'].astype(np.float32),remap[bi].astype(np.int32),bw.astype(np.float32),g['tri'].astype(np.int32)]:f.write(a.tobytes())
(u/'Kit_Top_shapes.bin').write_bytes(np.asarray([0,n],np.int32).tobytes());(u/'Kit_Top_correctives.json').write_text('{"anchors":[]}')
print('Harmonic field:',len(nodes),'sewn nodes;',len(edges),'edges; arm mass range',arm.min(),arm.max(),'; zero animation inputs')
