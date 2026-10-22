from pathlib import Path
import json,ctypes,heapq
import numpy as np
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';G=R/'work/reference-rebuild/garment-gusset1/runtime-reviewed'
body=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/poses/female_intro.json').read_text())['parts'][0]
def arr(x,k,n):return np.asarray(x[k]).reshape(-1,n)
rt=arr(body,'rendererToRoot',4);bv=np.ascontiguousarray(arr(body,'vertices',3)@rt[:3,:3].T+rt[:3,3]);bn=np.ascontiguousarray(arr(body,'normals',3)@rt[:3,:3].T);bt=np.ascontiguousarray(arr(body,'triangles',3),np.int32);bi=arr(body,'indices',4).astype(int);bw=arr(body,'weights',4)
cl=ctypes.CDLL(str(R/'work/reference-rebuild/garment-gusset1/clearance.dylib'));cl.project.argtypes=[ctypes.c_void_p]*3+[ctypes.c_int,ctypes.c_void_p,ctypes.c_int]+[ctypes.c_void_p]*4
report={}
for variant in ['Full','LOD']:
 p=json.loads((G/f'UnderarmGusset_Female_{variant}.json').read_text());si=arr(p,'sourceIndices',3).astype(int);sw=arr(p,'sourceWeights',3);base=(arr(p,'sourceVertices',3)[si]*sw[...,None]).sum(1);normal=(arr(p,'sourceNormals',3)[si]*sw[...,None]).sum(1);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 # The authored Top and Body share the source importer axis conversion.
 v=base@rt[:3,:3].T+rt[:3,3];n=normal@rt[:3,:3].T;f=np.array(p['freeVertices']);free=np.zeros(len(v),bool);free[f]=True;alias=np.array(p['aliases']);tri=arr(p,'triangles',3).astype(int)
 pts=np.ascontiguousarray(v[f]);near=np.zeros_like(pts);nn=np.zeros_like(pts);sd=np.zeros(len(f));faces=np.zeros(len(f),np.int32)
 cl.project(bv.ctypes.data,bn.ctypes.data,bt.ctypes.data,len(bt),pts.ctypes.data,len(pts),near.ctypes.data,nn.ctypes.data,sd.ctypes.data,faces.ctypes.data)
 # Physical geodesic distance from the pinned patch boundary provides one smooth
 # authored transition. UV copies share distance, position and binding weights.
 groups=int(alias.max()+1);av=np.zeros((groups,3));av[alias]=v;af=np.zeros(groups,bool);af[alias[f]]=True;adj=[{} for _ in range(groups)]
 for a,b in np.concatenate([alias[tri[:,[0,1]]],alias[tri[:,[1,2]]],alias[tri[:,[2,0]]]]):
  if a==b:continue
  length=float(np.linalg.norm(av[a]-av[b]));adj[a][b]=length;adj[b][a]=length
 dist=np.full(groups,np.inf);heap=[]
 for i in np.where(af)[0]:
  for j,d in adj[i].items():
   if not af[j] and d<dist[i]:dist[i]=d
  if np.isfinite(dist[i]):heapq.heappush(heap,(dist[i],int(i)))
 while heap:
  d,i=heapq.heappop(heap)
  if d>dist[i]:continue
  for j,e in adj[i].items():
   if af[j] and d+e<dist[j]:dist[j]=d+e;heapq.heappush(heap,(d+e,j))
 strength=np.zeros(len(v));u=np.clip(dist[alias[f]]/.012,0,1);strength[f]=u*u*(3-2*u)
 # Nearest body triangle supplies a smooth, anatomically local skin field.
 q=bv[bt[faces]];e0=q[:,1]-q[:,0];e1=q[:,2]-q[:,0];e2=near-q[:,0];d00=(e0*e0).sum(1);d01=(e0*e1).sum(1);d11=(e1*e1).sum(1);d20=(e2*e0).sum(1);d21=(e2*e1).sum(1);den=d00*d11-d01*d01;b1=(d11*d20-d01*d21)/den;b2=(d00*d21-d01*d20)/den;bary=np.column_stack([1-b1-b2,b1,b2]);bary=np.maximum(bary,0);bary/=bary.sum(1)[:,None]
 dense=np.zeros((len(v),len(p['bones'])));oldi=arr(p,'boneIndices',4).astype(int);oldw=arr(p,'weights',4)
 for j in range(4):np.add.at(dense,(np.arange(len(v)),oldi[:,j]),oldw[:,j])
 bodydense=np.zeros((len(f),len(p['bones'])));mapping=np.array([p['bones'].index(name) for name in body['bones']])
 for corner in range(3):
  ids=bt[faces,corner]
  for j in range(4):np.add.at(bodydense,(np.arange(len(f)),mapping[bi[ids,j]]),bary[:,corner]*bw[ids,j])
 dense[f]=dense[f]*(1-strength[f,None])+bodydense*strength[f,None]
 target=near+nn*.006
 v[f]=v[f]*(1-strength[f,None])+target*strength[f,None]
 # Share physical rest positions and weights across every free UV alias.
 sums=np.zeros((groups,3));ds=np.zeros((groups,len(p['bones'])));counts=np.bincount(alias,minlength=groups);np.add.at(sums,alias,v);np.add.at(ds,alias,dense);v[f]=sums[alias[f]]/counts[alias[f],None];dense[f]=ds[alias[f]]/counts[alias[f],None]
 # Preserve intentional back-facing lining normals, but remove the unstable
 # geometric-difference heuristic from the authored outer panel.
 signs=np.where((n[f]*nn).sum(1)<0,-1,1);n[f]=n[f]*(1-strength[f,None])+nn*signs[:,None]*strength[f,None];n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
 order=np.argsort(-dense,axis=1)[:,:4];weights=np.take_along_axis(dense,order,axis=1);lost=1-weights.sum(1);weights/=weights.sum(1)[:,None];order[~free]=oldi[~free];weights[~free]=oldw[~free]
 posedbase=(v-rt[:3,3])@rt[:3,:3];panelnormal=n@rt[:3,:3];posedbase[~free]=base[~free];panelnormal[~free]=normal[~free]
 p['panelVertices']=posedbase.ravel().tolist();p['panelNormals']=panelnormal.ravel().tolist();p['panelStrengths']=strength.tolist();p['panelBoneIndices']=order.ravel().tolist();p['panelWeights']=weights.ravel().tolist()
 # Retain source topology validation and submesh parent ownership only.
 for key in ['freeVertices','aliases','contactTriangles','proxyBoneIndices','proxyBoneLocalPositions','proxyWeights','proxyRestPositions','proxyTriangles','clearance','maximumDisplacement','rayMinimum','rayMaximum','contactStep','contactIterations']:
  p.pop(key,None)
 (O/f'UnderarmGusset_Female_{variant}.json').write_text(json.dumps(p,separators=(',',':')))
 report[variant]={'vertices':len(v),'authoredPanelVertices':len(f),'bodyAssociationTriangles':len(np.unique(faces)),'maximumRestMoveMetres':float(np.linalg.norm(posedbase-base,axis=1).max()),'transitionWidthMetres':.012,'bodyNormalOffsetMetres':.006,'maximumWeightDiscardedFromFourInfluenceLimit':float(lost.max()),'pinnedVertexPositionErrorMetres':float(np.linalg.norm(posedbase[~free]-base[~free],axis=1).max())}
(O/'panel-author-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
