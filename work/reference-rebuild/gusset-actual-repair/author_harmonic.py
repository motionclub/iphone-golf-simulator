from pathlib import Path
from collections import defaultdict
import json,time
import numpy as np
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';G=R/'work/reference-rebuild/garment-gusset1/runtime-reviewed';reports={}
for variant in ['Full','LOD']:
 p=json.loads((G/f'UnderarmGusset_Female_{variant}.json').read_text());src=np.array(p['sourceVertices']).reshape(-1,3);si=np.array(p['sourceIndices']).reshape(-1,3);sw=np.array(p['sourceWeights']).reshape(-1,3);v=(src[si]*sw[...,None]).sum(1);free=np.array(p['freeVertices']);alias=np.array(p['aliases']);physical=np.zeros((alias.max()+1,3));physical[alias]=v;representative=np.zeros(alias.max()+1,int)
 for i in range(len(alias)-1,-1,-1):representative[alias[i]]=i
 tri=np.array(p['contactTriangles']).reshape(-1,3);t=alias[tri];edges=defaultdict(list)
 for i,f in enumerate(t):
  for k in range(3):edges[tuple(sorted((f[k],f[(k+1)%3])))].append(i)
 adj=defaultdict(set)
 for fs in edges.values():
  if len(fs)==2:adj[fs[0]].add(fs[1]);adj[fs[1]].add(fs[0])
 seen=set();components=[]
 for i in range(len(t)):
  if i in seen:continue
  q=[i];seen.add(i);comp=[]
  while q:
   j=q.pop();comp.append(j)
   for z in adj[j]:
    if z not in seen:seen.add(z);q.append(z)
  components.append(comp)
 components.sort(key=lambda c:min(np.unique(t[c])))
 coords={};bubbles={};bycomponent={};details={};frameNormals={};allboundary=[];boundaryStarts=[0];boundaryEdges=[];edgeStarts=[0];frameA=[];frameB=[];rows=[];reconstructed=v.copy()
 for c,fs in enumerate(components):
  nodes=np.unique(t[fs]);group=set(fs);ce=[e for e,fl in edges.items() if any(f in group for f in fl)];boundary=sorted(set(q for e in ce if len([f for f in edges[e] if f in group])==1 for q in e));inside=[int(i) for i in nodes if i not in boundary];ni=len(inside);nb=len(boundary);ii={i:j for j,i in enumerate(inside)};ib={i:j for j,i in enumerate(boundary)};A=np.zeros((ni,ni));B=np.zeros((ni,nb));
  for a,b in ce:
   w=1/max(float(np.linalg.norm(physical[a]-physical[b])),1e-5)
   for i,j in [(a,b),(b,a)]:
    if i not in ii:continue
    A[ii[i],ii[i]]+=w
    if j in ii:A[ii[i],ii[j]]-=w
    else:B[ii[i],ib[j]]+=w
  H=np.linalg.solve(A,B);H=np.maximum(H,0);H/=H.sum(1)[:,None];bubble=np.linalg.solve(A,np.ones(ni));bubble/=bubble.max()
  for j,i in enumerate(inside):coords[i]=H[j];bubbles[i]=float(bubble[j]);bycomponent[i]=c
  allboundary.extend(representative[boundary].tolist());boundaryStarts.append(len(allboundary))
  recon=H@physical[boundary]
  directed=[]
  for e in ce:
   fl=[f for f in edges[e] if f in group]
   if len(fl)!=1:continue
   f=t[fl[0]]
   for k in range(3):
    if tuple(sorted((f[k],f[(k+1)%3])))==e:directed.append((int(f[k]),int(f[(k+1)%3])))
  normal=np.zeros(3)
  for a,b in directed:normal+=np.cross(physical[a],physical[b])
  normal/=np.linalg.norm(normal)
  cloud=physical[boundary];dd=np.linalg.norm(cloud[:,None,:]-cloud[None,:,:],axis=2);aa,bb=np.unravel_index(dd.argmax(),dd.shape);a=boundary[aa];b=boundary[bb];axis=physical[b]-physical[a];axis-=normal*(axis@normal);axis/=np.linalg.norm(axis);second=np.cross(normal,axis);frame=np.column_stack([axis,second,normal]);frameA.append(int(representative[a]));frameB.append(int(representative[b]))
  for a,b in directed:boundaryEdges.extend([int(representative[a]),int(representative[b])])
  edgeStarts.append(len(boundaryEdges))
  normsum=np.zeros_like(physical);facearea=np.cross(physical[t[fs,1]]-physical[t[fs,0]],physical[t[fs,2]]-physical[t[fs,0]])
  for k in range(3):np.add.at(normsum,t[fs,k],facearea)
  normsum/=np.maximum(np.linalg.norm(normsum,axis=1)[:,None],1e-12)
  for j,i in enumerate(inside):
   details[i]=(physical[i]-recon[j])@frame
   frameNormals[i]=normsum[i]@frame
   reconstructed[alias==i]=recon[j]+frame@details[i]
  rows.append({'component':c,'triangles':len(fs),'boundaryAliases':nb,'interiorAliases':ni,'maxRestRebuildMoveMetres':float(np.linalg.norm(recon-physical[inside],axis=1).max()),'positiveCoordinateMinimum':float(H.min())})
 offsets=[0];weights=[];component=[];bubble=[]
 for i in free:
  a=int(alias[i]);weights.extend(coords[a]);offsets.append(len(weights));component.append(bycomponent[a]);bubble.append(bubbles[a])
 p['panelBoundaryEdges']=boundaryEdges;p['panelEdgeStarts']=edgeStarts;p['panelFrameA']=frameA;p['panelFrameB']=frameB;p['harmonicDetail']=np.array([details[int(alias[i])] for i in free]).ravel().tolist();p['harmonicNormals']=np.array([frameNormals[int(alias[i])] for i in free]).ravel().tolist();p['panelBoundaryIndices']=allboundary;p['panelBoundaryStarts']=boundaryStarts;p['harmonicOffsets']=offsets;p['harmonicWeights']=weights;p['harmonicComponents']=component;p['harmonicBubble']=bubble;p['panelCount']=len(components)
 (O/f'UnderarmGusset_Female_{variant}.json').write_text(json.dumps(p,separators=(',',':')))
 np.savez_compressed(O/f'harmonic-{variant}.npz',reconstructed=reconstructed,triangles=tri,components=np.array(component),free=free,bubble=np.array(bubble))
 old=np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]]);new=np.cross(reconstructed[tri[:,1]]-reconstructed[tri[:,0]],reconstructed[tri[:,2]]-reconstructed[tri[:,0]]);dot=(old*new).sum(1);flip=(dot<0)&(np.linalg.norm(old,axis=1)>1e-8)
 reports[variant]={'components':rows,'freeVertices':len(free),'boundarySamples':len(allboundary),'storedCoordinates':len(weights),'restOrientationReversals':int(flip.sum()),'minOldNewNormalCosine':float((dot/np.maximum(np.linalg.norm(old,axis=1)*np.linalg.norm(new,axis=1),1e-20)).min())};print(variant,json.dumps(reports[variant]),flush=True)
(O/'harmonic-author-report.json').write_text(json.dumps(reports,indent=2))
