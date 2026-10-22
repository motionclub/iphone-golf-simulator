import sys,json,numpy as np
from collections import Counter
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1');from common import *
W=R/'work/reference-rebuild/golf-garment-mask1';report={}
for sex in ('Male','Female'):
 body,top,raw=source(sex);base=arr(top,'vertices',3);rt=np.array(top['rendererToRoot']).reshape(4,4);rest=xf(rt,base);tri=arr(top,'triangles',3).astype(int);area=np.cross(rest[tri[:,1]]-rest[tri[:,0]],rest[tri[:,2]]-rest[tri[:,0]]);length=np.linalg.norm(area,axis=1);rn=area/np.maximum(length[:,None],1e-14)
 canonical={};weld=np.array([canonical.setdefault(tuple(np.round(v*1e6).astype(int)),len(canonical)) for v in base]);ctri=weld[tri];counts=Counter(tuple(sorted((int(t[j]),int(t[(j+1)%3])))) for t in ctri for j in range(3));boundary=[e for e,n in counts.items() if n==1]
 center=rest[tri].mean(1);axilla=(abs(center[:,0])>.07)&(abs(center[:,0])<(.30 if sex=='Male' else .225))&(center[:,1]>1.095)&(center[:,1]<(1.385 if sex=='Male' else 1.345));rows={}
 # Rest triangle's own normal is transformed by its mean LBS differential (not painted vertex normal).
 vf=np.zeros_like(base)
 for k in range(3):np.add.at(vf,tri[:,k],rn)
 vf/=np.maximum(np.linalg.norm(vf,axis=1)[:,None],1e-12);local=vf@rt[:3,:3]
 for path in sorted((D/'matrices').glob(sex.lower()+'*.json')):
  snap=json.loads(path.read_text());p={a['name']:a for a in snap['parts']}['Kit_Top'];m=np.array(p['skinMatrices']).reshape(-1,4,4);w=np.array(p['shapeWeights'])/100;w=w[[p['shapeNames'].index(str(n)) for n in raw['shapeNames']]]
  pose=xf(rt,skin(top,base+np.einsum('s,sni->ni',w,raw['shapeDeltas']),matrices=m));a=np.cross(pose[tri[:,1]]-pose[tri[:,0]],pose[tri[:,2]]-pose[tri[:,0]]);vi=arr(top,'indices',4).astype(int);vw=arr(top,'weights',4);blend=(m[vi,:3,:3]*vw[:,:,None,None]).sum(1);faceBlend=blend[tri].mean(1);expected=np.einsum('nij,nj->ni',faceBlend,rn@rt[:3,:3])@np.linalg.inv(rt[:3,:3]);sign=(a*expected).sum(1)
  inverted=axilla&(sign<0)&(length>1e-9)&(np.linalg.norm(a,axis=1)>1e-10);rows[path.stem]={'axillaFaces':int(axilla.sum()),'invertedAxillaFaces':int(inverted.sum()),'invertedAxillaAreaMm2':float(np.linalg.norm(a[inverted],axis=1).sum()*500000),'collapsedAxillaFaces':int((axilla&(np.linalg.norm(a,axis=1)<1e-10)).sum())}
  if path.stem in (sex.lower()+'_Driver_016',sex.lower()+'_Putter_000',sex.lower()+'_Driver_026'):
   np.savez_compressed(W/(path.stem+'_facing.npz'),vertices=pose,triangles=tri,inverted=inverted,axilla=axilla)
 wpositions=np.zeros((len(canonical),3));wpositions[weld]=rest;localBoundary=[]
 for e in boundary:
  q=wpositions[list(e)].mean(0);side='Left' if q[0]<0 else 'Right';cb=rt[None]@np.linalg.inv(arr(top,'bindposes',16).reshape(-1,4,4));pa=cb[top['bones'].index(side+'UpperArm'),:3,3];pb=cb[top['bones'].index(side+'LowerArm'),:3,3];along=(q-pa)@(pb-pa)/sum((pb-pa)**2)
  if .08<abs(q[0])<(.30 if sex=='Male' else .225) and 1.095<q[1]<(1.385 if sex=='Male' else 1.345) and along<.65:localBoundary.append({'edge':list(e),'centerRoot':q.tolist(),'alongUpperArm':float(along)})
 report[sex]={'proximalAxillaBoundaryEdges':len(localBoundary),'proximalAxillaBoundaryDetails':localBoundary,'originalVertices':len(base),'originalTriangles':len(tri),'spatiallyWeldedBoundaryEdges':len(boundary),'spatiallyWeldedNonmanifoldEdges':sum(n>2 for n in counts.values()),'samples':rows};print(sex,'boundaries',len(boundary),'nonmanifold',report[sex]['spatiallyWeldedNonmanifoldEdges'],'worst',max(rows.items(),key=lambda x:x[1]['invertedAxillaAreaMm2']),flush=True)
(W/'facing-audit.json').write_text(json.dumps(report,indent=2)+'\n')
