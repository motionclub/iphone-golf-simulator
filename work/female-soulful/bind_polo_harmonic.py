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
# Panel group of every vertex: torso, left sleeve, right sleeve, collar,
# placket, cuff, button. Layers transfer weights only inside their group:
# under the arm the nearest shell face is often the OTHER panel, which tore
# sleeve linings onto the torso and torso linings onto the arm.
group_of_panel=np.array([0,0,2,1,3,4,5,6]);face_group=group_of_panel[g['panel']]
vote=np.zeros((n,7));np.add.at(vote,(tris.ravel(),np.repeat(face_group,3)),1);vgroup=vote.argmax(1)
for side,gid in [(-1,1),(1,2)]:
 # panel 2 is +x, panel 3 is -x (measured extents); keep that mapping explicit
 assert np.all(np.sign(p[np.unique(tris[face_group==gid]),0])==side),'sleeve panel side mapping changed'
# Torso field smoothing over the sewn all-layer graph. Source torso weights
# carry hard Neck/UpperChest and Voronoi steps; garment fabric bridges joints,
# so the torso field is diffused over a few centimetres (no pose inputs).
u_all,inv_all=np.unique(np.round(p,5),axis=0,return_inverse=True);inv_all=inv_all.ravel()
ea=np.sort(inv_all[np.concatenate([tris[:,[0,1]],tris[:,[1,2]],tris[:,[2,0]]])],axis=1);ea=np.unique(ea[ea[:,0]!=ea[:,1]],axis=0)
sa=np.r_[ea[:,0],ea[:,1]];da=np.r_[ea[:,1],ea[:,0]];ca=1/np.maximum(np.linalg.norm(u_all[sa]-u_all[da],axis=1),.002);dega=np.bincount(sa,weights=ca,minlength=len(u_all))
Tu=np.zeros((len(u_all),T.shape[1]));np.add.at(Tu,inv_all,T);Tu/=np.bincount(inv_all,minlength=len(u_all))[:,None]
SMOOTH_STEPS=int(__import__('os').environ.get('POLO_TORSO_SMOOTH','60'))
for step in range(SMOOTH_STEPS):
 mean=np.stack([np.bincount(sa,weights=ca*Tu[da,c],minlength=len(u_all)) for c in range(Tu.shape[1])],1)/np.maximum(dega,1e-12)[:,None]
 Tu=.5*Tu+.5*mean
T=Tu[inv_all];T/=T.sum(1,keepdims=True)
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
arm=result[inverse].copy();is_outer=np.zeros(n,bool);is_outer[outer_ids]=True
outer_group=face_group[(g['part']==0)&np.isin(g['panel'],[0,1,2,3])]
shells={k:(outer[outer_group==k],BVHTree.FromPolygons(p.tolist(),outer[outer_group==k].tolist(),all_triangles=True)) for k in (0,1,2)}
for i in np.flatnonzero(~is_outer):
 # sleeve layers follow their own sleeve shell; everything else the torso shell
 k=vgroup[i] if vgroup[i] in (1,2) else 0
 faces,tree_k=shells[k];q,_,fi,_=tree_k.find_nearest(Vector(p[i]));t=faces[fi];near=t[np.argmin(np.linalg.norm(p[t]-np.asarray(q),axis=1))];arm[i]=arm[near]
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
