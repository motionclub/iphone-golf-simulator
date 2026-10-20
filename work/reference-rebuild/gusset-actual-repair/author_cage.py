from pathlib import Path
import json, heapq
import numpy as np
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';G=R/'work/reference-rebuild/garment-gusset1/runtime-reviewed';report={}
for variant in ['Full','LOD']:
 p=json.loads((G/f'UnderarmGusset_Female_{variant}.json').read_text());src=np.array(p['sourceVertices']).reshape(-1,3);si=np.array(p['sourceIndices']).reshape(-1,3);sw=np.array(p['sourceWeights']).reshape(-1,3);v=(src[si]*sw[...,None]).sum(1);free=np.array(p['freeVertices']);alias=np.array(p['aliases']);tri=np.array(p['triangles']).reshape(-1,3);groups=alias.max()+1
 av=np.zeros((groups,3));av[alias]=v;af=np.zeros(groups,bool);af[alias[free]]=True;ap=av[np.where(af)[0]]
 centers=[0];dist=np.linalg.norm(ap-ap[0],axis=1)
 while dist.max()>.008:
  i=int(dist.argmax());centers.append(i);dist=np.minimum(dist,np.linalg.norm(ap-ap[i],axis=1))
 centers=ap[centers];allDistances=np.linalg.norm(v[free,None,:]-centers[None,:,:],axis=2);index=np.argsort(allDistances,axis=1)[:,:8];distance=np.take_along_axis(allDistances,index,axis=1)
 # Smooth normalized positive basis; coincidence never changes support order.
 weight=np.exp(-distance*distance/(2*.010**2));weight/=weight.sum(1)[:,None]
 edges=np.unique(np.sort(np.concatenate([alias[tri[:,[0,1]]],alias[tri[:,[1,2]]],alias[tri[:,[2,0]]]]),axis=1),axis=0);adj=[{} for _ in range(groups)]
 for a,b in edges:
  if a==b:continue
  d=float(np.linalg.norm(av[a]-av[b]));adj[a][b]=d;adj[b][a]=d
 geodesic=np.full(groups,np.inf);heap=[]
 for i in np.where(af)[0]:
  for j,d in adj[i].items():
   if not af[j] and d<geodesic[i]:geodesic[i]=d
  if np.isfinite(geodesic[i]):heapq.heappush(heap,(geodesic[i],int(i)))
 while heap:
  d,i=heapq.heappop(heap)
  if d>geodesic[i]:continue
  for j,e in adj[i].items():
   if af[j] and d+e<geodesic[j]:geodesic[j]=d+e;heapq.heappush(heap,(d+e,j))
 u=np.clip(geodesic[alias[free]]/.008,0,1);strength=u*u*(3-2*u)
 p['cageCount']=len(centers);p['cageIndices']=index.ravel().tolist();p['cageWeights']=weight.ravel().tolist();p['cageStrengths']=strength.tolist()
 (O/f'UnderarmGusset_Female_{variant}.json').write_text(json.dumps(p,separators=(',',':')));report[variant]={'controls':len(centers),'freeVertices':len(free),'maximumControlSpacingMetres':.008,'basisSigmaMetres':.010,'seamFadeMetres':.008,'allOriginalPositionsAndBindingsPreserved':True}
(O/'cage-author-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
