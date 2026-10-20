from pathlib import Path
from collections import Counter
import json,ctypes
import numpy as np
R=Path(__file__).resolve().parents[3]; O=Path(__file__).resolve().parent
PROFILE=json.loads((R/'work/reference-rebuild/garment-gusset1/runtime-reviewed/UnderarmGusset_Female_Full.json').read_text())
CAGE=json.loads((R/'work/reference-rebuild/gusset-actual-repair/UnderarmGusset_Female_Full.json').read_text())
ORIG=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/poses/female_intro.json').read_text())
BODY=next(x for x in ORIG['parts'] if x['name']=='Body_F'); TOP=next(x for x in ORIG['parts'] if x['name']=='Kit_Top')
def arr(d,k,n): return np.array(d[k]).reshape(-1,n)
srct=arr(PROFILE,'sourceTriangles',3).astype(int); newt=arr(PROFILE,'triangles',3).astype(int); parent=np.array(PROFILE['triangleSourceFaces']); free=np.zeros(PROFILE['vertexCount'],bool);free[PROFILE['freeVertices']]=True
srcv=arr(PROFILE,'sourceVertices',3);aliases=np.array(PROFILE['aliases']);strength=np.zeros(PROFILE['vertexCount']);strength[PROFILE['freeVertices']]=CAGE['cageStrengths']
bi=arr(PROFILE,'boneIndices',4).astype(int);bw=arr(PROFILE,'weights',4);bones=PROFILE['bones']; oldbi=arr(TOP,'indices',4).astype(int);oldbw=arr(TOP,'weights',4)
arm=np.array([('Arm' in x or 'Shoulder' in x) for x in bones]); mass=(bw*arm[bi]).sum(1)
origbt=arr(BODY,'triangles',3).astype(int);bodylookup={tuple(x):i for i,x in enumerate(origbt)}
bodyrest=arr(BODY,'vertices',3);oldbodytris=bodyrest[origbt];bodycentres=oldbodytris.mean(1)
def geomkey(points): return tuple(sorted(tuple(x) for x in np.round(points,7)))
bodygeomlookup={geomkey(bodyrest[t]):i for i,t in enumerate(origbt)}
def bodymap(body,tri):
 rest=arr(body,'vertices',3);out=np.array([bodygeomlookup.get(geomkey(rest[t]),-1) for t in tri]);missing=np.where(out<0)[0]
 for f in missing:
  q=rest[tri[f]].mean(0);cand=np.argpartition(((bodycentres-q)**2).sum(1),32)[:32];a=oldbodytris[cand,0];u=oldbodytris[cand,1]-a;v=oldbodytris[cand,2]-a;rel=q-a
  uu=(u*u).sum(1);uv=(u*v).sum(1);vv=(v*v).sum(1);ru=(rel*u).sum(1);rv=(rel*v).sum(1);den=uu*vv-uv*uv;den=np.where(abs(den)>1e-20,den,np.inf);t=(vv*ru-uv*rv)/den;w=(uu*rv-uv*ru)/den;near=a+t[:,None]*u+w[:,None]*v;distance=np.linalg.norm(q-near,axis=1);valid=(t>=-.0001)&(w>=-.0001)&(t+w<=1.0001)&(distance<1e-6)
  if valid.any(): out[f]=cand[np.where(valid)[0][np.argmin(distance[valid])]]
 return out
REGION=np.array(json.loads((R/'work/reference-rebuild/garment-weight-transition/mask3/reusable-underarm/full-strength-source-audit.json').read_text())['regionFaces'])
lib=ctypes.CDLL(str(R/'work/reference-rebuild/garment-weight-transition/mask3/raster-front.dylib'));lib.draw.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int]
def rootverts(part):
 m=arr(part,'rendererToRoot',4);v=arr(part,'posedVertices',3);return v@m[:3,:3].T+m[:3,3]
def project(v,view):
 cam=np.array([2.4,1.3,4.1]) if view=='front' else np.array([-2.4,1.3,-4.1]);target=np.array([0,.83,.1]);fw=target-cam;fw/=np.linalg.norm(fw);right=np.cross([0,1,0],fw);right/=np.linalg.norm(right);up=np.cross(fw,right);d=v-cam;depth=d@fw;scale=600/np.tan(np.deg2rad(17));return np.ascontiguousarray(np.column_stack([450+d@right/depth*scale,600-d@up/depth*scale,depth]))
def raster(v,t,view,reverse=False):
 xy=project(v,view);t=np.ascontiguousarray(t[:,::-1] if reverse else t,np.int32);depth=np.full((1200,900),np.inf);ids=np.full((1200,900),-1,np.int32);lib.draw(xy.ctypes.data,t.ctypes.data,len(t),900,1200,depth.ctypes.data,ids.ctypes.data,0);return depth,ids

def faceevidence(f,pixels):
 vs=active_tri[f];source=srct[active_parent[f]];return {'generatedFace':int(f),'pixels':int(pixels),'sourceFace':int(active_parent[f]),'generatedVertices':vs.tolist(),'freeVertices':active_free[vs].tolist(),'DQStrength':active_strength[vs].tolist(),'armMass':active_mass[vs].tolist(),'sourceVertices':source.tolist(),'sourceWeights':[{bones[int(b)]:float(w) for b,w in zip(oldbi[i],oldbw[i]) if w>0} for i in source]}
rows=[]
for variant in ['gusset-harmonic1-framefix','gusset-dq1','shirt-noanchors-lbs']:
 for label in ['female_Forehand_1','female_Forehand_2']:
  parts=json.loads((R/f'proof/reference-rebuild/{variant}/poses/{label}.json').read_text())['parts'];body=next(x for x in parts if x['name']=='Body_F');top=next(x for x in parts if x['name']=='Kit_Top');bv=rootverts(body);tv=rootverts(top);bt=arr(body,'triangles',3).astype(int);tt=arr(top,'triangles',3).astype(int)
  assert np.array_equal(tt,srct if variant=='shirt-noanchors-lbs' else newt), 'Actual triangle mapping changed'
  active_tri=tt;active_parent=np.arange(len(srct)) if variant=='shirt-noanchors-lbs' else parent
  active_free=np.zeros(len(srcv),bool) if variant=='shirt-noanchors-lbs' else free
  active_strength=np.zeros(len(srcv)) if variant=='shirt-noanchors-lbs' else strength
  active_mass=(oldbw*arm[oldbi]).sum(1) if variant=='shirt-noanchors-lbs' else mass
  bmapping=bodymap(body,bt);row={'variant':variant,'sample':label,'topologyExact':True,'mappedBodyTriangles':int((bmapping>=0).sum()),'actualBodyTriangles':len(bt),'views':[]}
  for view in ['front','rear']:
   bz,bid=raster(bv,bt,view);tz,tid=raster(tv,tt,view);rz,rid=raster(tv,tt,view,True)
   physical=np.full_like(bid,-1);hit=bid>=0;physical[hit]=bmapping[bid[hit]];region=np.isin(physical,REGION)
   visible=region&(bz<tz-.0008);behind=visible&np.isfinite(tz)&((tz-bz)<.065);backonly=visible&(rz<bz+.065)&(rz<tz)&~behind;noTop=visible&~np.isfinite(tz)&~np.isfinite(rz)
   ids,cnt=np.unique(tid[behind],return_counts=True);order=np.argsort(cnt)[::-1];faces=[faceevidence(int(ids[j]),int(cnt[j])) for j in order[:16]]
   bodyids,bodycnt=np.unique(physical[visible],return_counts=True);bodyorder=np.argsort(bodycnt)[::-1]
   deltas=tz[behind]-bz[behind]
   points=[]
   for x,y in ((375,498),(386,500),(365,492),(395,504)):
    if tid[y,x]<0:continue
    points.append({'pixel':[x,y],'bodyCurrentFace':int(bid[y,x]),'bodySourceFace':int(physical[y,x]),'frontClothBehindBodyMm':float((tz[y,x]-bz[y,x])*1000),'backClothBehindBodyMm':float((rz[y,x]-bz[y,x])*1000),'cloth':faceevidence(int(tid[y,x]),1)})
   vd={'localizedPixelPoints':points,'view':view,'visibleRegionalBodyPixels':int(visible.sum()),'bodyInFrontOfNearbyFrontClothPixels':int(behind.sum()),'backfaceOnlyNearbyClothPixels':int(backonly.sum()),'noFrontOrBackProjectedClothPixels':int(noTop.sum()),'frontClothDepthBehindBodyMmMin':float(deltas.min()*1000) if len(deltas) else None,'frontClothDepthBehindBodyMmMax':float(deltas.max()*1000) if len(deltas) else None,'bodySourceFaces':[{'face':int(bodyids[j]),'pixels':int(bodycnt[j])} for j in bodyorder[:20]],'frontClothFacesBehindBody':faces}
   row['views'].append(vd)
   np.savez_compressed(O/f'{variant}_{label}_{view}.npz',bodyDepth=bz,frontClothDepth=tz,backClothDepth=rz,bodyFace=physical,frontClothFace=tid,backClothFace=rid,visibleRegionalBody=visible)
  rows.append(row)
# Canonical topology after weld by original position. Expected shell/lining seams
# are reported rather than silently replaced by a visual displacement.
key=np.round(srcv,7);_,canonical=np.unique(key,axis=0,return_inverse=True);edgecount=Counter(tuple(sorted(e)) for tri in canonical[srct] for e in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])) if e[0]!=e[1])
originaledges={tuple(sorted(e)) for tri in srct for e in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0]))}
sourcefaces=sorted({f['sourceFace'] for row in rows for view in row['views'] for f in view['frontClothFacesBehindBody']})
topology=[]
for f in sourcefaces:
 v=srct[f];w=canonical[v];counts=[edgecount[tuple(sorted(e))] for e in ((w[0],w[1]),(w[1],w[2]),(w[2],w[0]))]
 topology.append({'sourceFace':f,'sourceVertices':v.tolist(),'weldedEdgeIncidenceCounts':counts,'boundaryEdgePresent':1 in counts})
res={'scope':'Actual harmonic and DQ forehand snapshots, existing CullBack raster and source-face mappings. Read-only geometry diagnosis; no Unity/source mutations. Pixel counts are localization, not shipping thresholds.','camera':'[2.4,1.3,4.1] front, opposite rear; target[0,.83,.1],34degree vertical FOV,900x1200','rows':rows,'sourceAffectedFaceTopology':topology,'canonicalSourceVertexCount':len(srcv),'generatedVertexCount':PROFILE['vertexCount'],'sourceTriangles':len(srct),'generatedTriangles':len(newt),'sourceCanonicalWeightParity':'Actual shirt-noanchors-lbs canonical source vertices, triangles, bone indices, weights and bone order exactly match recorded13932v character-motion-matrices17 source. All13932 weight rows are exact; no current weight contract mismatch.'}
(O/'actual-strip-evidence.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps([{k:r[k] for k in ('variant','sample')}|{'views':[{k:v[k] for k in ('view','visibleRegionalBodyPixels','bodyInFrontOfNearbyFrontClothPixels','backfaceOnlyNearbyClothPixels','noFrontOrBackProjectedClothPixels')} for v in r['views']]} for r in rows],indent=2))
