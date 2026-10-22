"""Pose the independent polo using sewn sleeve curves and current skin clearance."""
from pathlib import Path
import sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path[:0]=[str(r),str(r.parent/'clothing-v2/py')]
import cv2io,glib as G
from pose_features import features
from posed_sleeves import SleeveLofts,project,frame
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-12)
cv2io.DUMP=str(r/'dump-polo');h=cv2io.Hero('GolfKitHero_Female');b=h.body
u=r/'out/GolfKitHero_Female/unity';g=np.load(u/'Kit_Top_final.npz');p=g['pos'];tri=g['tri'];n=len(p)
lofts=SleeveLofts(g,h,r)
# The lining and rolled rim inherit the outside wall's motion. Projecting both
# walls onto the skin independently collapses their thickness and opens seams.
outer=tri[g['part']==0];outer_v=np.zeros(n,bool);outer_v[outer.ravel()]=True
inner_ids=np.nonzero(~outer_v)[0];wall_index=[];wall_bary=[]
wall_tree=BVHTree.FromPolygons(p.tolist(),outer.tolist(),all_triangles=True)
for index in inner_ids:
 q,_,fi,_=wall_tree.find_nearest(Vector(p[index]));t=outer[fi];a,c,d=p[t];v0=c-a;v1=d-a;v2=np.asarray(q)-a;aa=v0@v0;ab=v0@v1;bb=v1@v1;ac=v0@v2;bd=v1@v2;den=max(aa*bb-ab*ab,1e-20);v=(bb*ac-ab*bd)/den;w=(aa*bd-ab*ac)/den;bar=np.clip([1-v-w,v,w],0,1);bar/=bar.sum();wall_index.append(t);wall_bary.append(bar)
wall_index=np.asarray(wall_index);wall_bary=np.asarray(wall_bary)
wall_point=(p[wall_index]*wall_bary[:,:,None]).sum(1);wall_frame=frame(p,wall_index);wall_offset=np.einsum('nji,nj->ni',wall_frame,p[inner_ids]-wall_point)
def thickness(target):
 result=target.copy();f=frame(target,wall_index);result[inner_ids]=(target[wall_index]*wall_bary[:,:,None]).sum(1)+np.einsum('nij,nj->ni',f,wall_offset);return result

_,inv,counts=np.unique(np.round(p,5),axis=0,return_inverse=True,return_counts=True);wtri=inv[tri]
# Neighbour smoothing acts on displacement, leaving the authored rest silhouette exact.
nb=G.neighbours(len(counts),wtri)
def weld(values):
 out=np.zeros((len(counts),3));np.add.at(out,inv,values);return out/counts[:,None]
meta=json.loads((r/'dump-arm-final/GolfKitHero_Female/hero.json').read_text())
bodyposes={}
records=[]
for c in h.clips:
 final=next(x for x in meta['clips']if x['name']==c['name']);assert c['frames']==final['frames']
 poses=np.fromfile(r/'dump-arm-final/GolfKitHero_Female'/('clip_'+final['file']+'_body.f32'),np.float32).reshape(c['frames'],-1,3)
 bones=h.clip(c['name'])[1]
 for fi in range(0,c['frames'],2):records.append((c['name'],fi,features(h,bones[fi].astype(float)),poses[fi],bones[fi].astype(float)))
# Cover the full action space, with overhead and both swing extremes as explicit anchors.
restfeature=features(h,h.rest_bones);chosen=[]
for name in ['Cheer','Drive','IronSwing']:
 entries=[i for i,x in enumerate(records)if x[0]==name]
 for frac in [.25,.5,.75]:chosen.append(entries[round((len(entries)-1)*frac)])
allf=np.asarray([x[2]for x in records]);mind=np.mean((allf-restfeature)**2,axis=1)
for i in chosen:mind=np.minimum(mind,np.mean((allf-allf[i])**2,axis=1))
while len(chosen)<72:
 i=int(np.argmax(mind))
 if i in chosen or mind[i]<.0001:break
 chosen.append(i);mind=np.minimum(mind,np.mean((allf-allf[i])**2,axis=1))
shapes=[];dnormal=[];anchors=[{'shape':'','feature':restfeature.tolist()}]
for k,record in enumerate(chosen):
 name,fi,f,bp,bones=records[record]
 skin=h.skin_matrices(bones);baseline=cv2io.lbs(p,g['bi'],g['bw'],skin)
 tree=BVHTree.FromPolygons(bp.tolist(),b.tri.tolist(),all_triangles=True)
 target=project(baseline,tree)
 target=lofts.apply(target,skin,bones,tree)
 wt=weld(target)
 for _ in range(3):
  for lam in [.5,-.52]:wt+=lam*G.umbrella(wt,nb)
 target=thickness(project(wt[inv],tree));delta=target-baseline
 A=sum(g['bw'][:,j,None,None]*skin[g['bi'][:,j],:3,:3]for j in range(4));db=np.linalg.solve(A,delta[:,:,None])[:,:,0]
 # Smooth normals across UV splits on the same sewing surface.
 wn=G.vertex_normals(weld(target),wtri)[inv];bindn=np.linalg.solve(A,wn[:,:,None])[:,:,0];bindn=unit(bindn)
 dn=bindn-g['nrm'];shapes.append(db);dnormal.append(dn);anchors.append({'shape':f'CV2_Pose{k:02d}','feature':f.tolist(),'clip':name,'frame':fi})
 print(k,name,fi,'max garment pose offset mm',round(float(np.linalg.norm(db,axis=1).max()*1000)),flush=True)
with (u/'Kit_Top_shapes.bin').open('wb')as fh:
 fh.write(np.asarray([len(shapes),n],np.int32).tobytes())
 for k,(dp,dn)in enumerate(zip(shapes,dnormal)):
  fh.write(f'CV2_Pose{k:02d}'.encode().ljust(16,b'\0'));fh.write(dp.astype(np.float32).tobytes());fh.write(dn.astype(np.float32).tobytes())
(u/'Kit_Top_correctives.json').write_text(json.dumps({'featureMode':'female-joint-frames','nearest':3,'anchors':anchors},separators=(',',':')))
np.savez(u/'correctives.npz',nearest=np.int32(3),feats=np.asarray([a['feature']for a in anchors]),shapes=np.asarray(shapes))
(r/'proof/golf-wrap-construction.json').write_text(json.dumps({'vertices':n,'anchors':len(shapes),'method':'independent garment with posed sewing-curve sleeve loft and skin clearance','neutralSourcePreserved':True,'sourceBodyModified':False},indent=2))
print('Finished',len(shapes),'garment pose shapes',flush=True)
