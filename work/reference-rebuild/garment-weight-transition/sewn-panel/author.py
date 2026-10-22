import pathlib,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition/sewn-panel';D=R/'proof/reference-rebuild/character-cloth14/poses'
s=(R/'work/reference-rebuild/garment-stroke-coverage/author_stroke_envelopes.py').read_text();exec(s[s.index('def arr('):s.index('def author(')]);s=(R/'work/reference-rebuild/garment-weight-transition/author_weights.py').read_text();exec(s[s.index('def bary('):s.index('REPORT={}')])
def clip(poly,plane):
 out=[]
 for i,a in enumerate(poly):
  b=poly[(i+1)%len(poly)];da=plane(a[:3]);db=plane(b[:3]);inside=da>=-1e-9
  if inside:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*(da/(da-db)))
 return out
REPORT={}
for sex in ('Male','Female'):
 p=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text());body,canon=json.loads((D/f'{sex.lower()}_Forehand_1.json').read_text())['parts'][:2];rt=np.array(canon['rendererToRoot']).reshape(4,4);base=np.array(p['vertices']).reshape(-1,3);rest=xf(rt,base);bnames=body['bones'];names=canon['bones'];br=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'vertices',3));bnormal=arr(body,'normals',3)@np.linalg.inv(np.array(body['rendererToRoot']).reshape(4,4)[:3,:3]);bnormal/=np.maximum(np.linalg.norm(bnormal,axis=1)[:,None],1e-12);bt=arr(body,'triangles',3).astype(int);tt=arr(canon,'triangles',3).astype(int);oldI=arr(canon,'indices',4).astype(int);oldW=arr(canon,'weights',4);bw=dense(body,names);uv=arr(canon,'uv',2);topBvh=BVHTree.FromPolygons([Vector(q) for q in rest],[tuple(t) for t in tt],all_triangles=True)
 # Identify garment's connected sewn body; preserve collar/placket pieces.
 parent=np.arange(len(base));groups={}
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def join(a,b):
  a=find(a);b=find(b)
  if a!=b:parent[b]=a
 for i,q in enumerate(base):
  key=tuple(np.round(q*1e5).astype(int))
  if key in groups:join(i,groups[key])
  else:groups[key]=i
 for a,b,c in tt:join(int(a),int(b));join(int(a),int(c))
 comp=np.array([find(i) for i in range(len(base))]);labels,cnts=np.unique(comp,return_counts=True);main=labels[cnts.argmax()];sewn=comp==main
 for label in labels:
  ids=np.where(comp==label)[0];q=rest[ids];lo=q.min(0);hi=q.max(0);size=hi-lo
  if np.min(abs(q[:,0]))>(.18 if sex=='Male' else .115) and lo[1]>1.045 and hi[1]<(1.37 if sex=='Male' else 1.33) and size[1]<.14 and size[0]<.15:sewn[ids]=True
 cut=.105 if sex=='Male' else .082;low=1.11 if sex=='Male' else 1.095;high=1.47 if sex=='Male' else 1.425
 inPanel=sewn&(abs(rest[:,0])>cut)&(rest[:,1]>low)&(rest[:,1]<high);remove=inPanel[tt].any(1);keep=tt[~remove];cuffBind=rt[None]@np.linalg.inv(np.array(canon['bindposes']).reshape(-1,4,4));newPoints=[];newNormals=[];newWeights=[];newUV=[];newClearance=[];panelTris=[];source=[];weld={}
 for side,sign in (('Left',-1),('Right',1)):
  a=cuffBind[names.index(side+'UpperArm'),:3,3];b=cuffBind[names.index(side+'LowerArm'),:3,3];axis=b-a;length=np.linalg.norm(axis);direction=axis/length;limit=.58 if sex=='Male' else .62
  # Underlap at existing seam is sewn construction, not Body hiding.
  inner=cut-.027;bottom=low-.020;top=high-.010
  planes=[lambda q,s=sign:s*q[0]-inner,lambda q:q[1]-bottom,lambda q:top-q[1],lambda q,a=a,direction=direction,length=length:limit-(q-a)@direction/length]
  for face in bt:
   points=br[face];poly=[np.concatenate([points[j],np.eye(3)[j]]) for j in range(3)]
   for plane in planes:
    if len(poly)<3:break
    poly=clip(poly,plane)
   if len(poly)<3:continue
   ids=[]
   for v in poly:
    q=v[:3];baryWeights=v[3:];key=tuple(np.round(q*1e7).astype(int))
    if key not in weld:
     i=len(newPoints);weld[key]=i;normal=baryWeights@bnormal[face];normal/=max(np.linalg.norm(normal),1e-12);weight=baryWeights@bw[face];weight=np.maximum(weight,0);weight/=weight.sum();h,n,f,d=topBvh.find_nearest(Vector(q));mappedUV=bary(np.array(h),rest[tt[f]])@uv[tt[f]]
     newPoints.append(q);newNormals.append(normal);newWeights.append(weight);newUV.append(mappedUV);newClearance.append(.012);source.append({'vertices':face.tolist(),'weights':baryWeights.tolist()})
    ids.append(weld[key])
   for j in range(1,len(ids)-1):
    triangle=[ids[0],ids[j],ids[j+1]];q=np.array([newPoints[k] for k in triangle]);area=np.cross(q[1]-q[0],q[2]-q[0]);
    if np.linalg.norm(area)>1e-10:panelTris.append(triangle)
 profileN=np.array(p['normals']).reshape(-1,3)@np.linalg.inv(rt[:3,:3]);profileN/=np.maximum(np.linalg.norm(profileN,axis=1)[:,None],1e-12)
 # Explicit sewn strip: original retained cut boundary shares indices with
 # one strip edge; the other is inserted into the supporting panel boundary.
 # This avoids independent underlap edges separating when their weights differ.
 from collections import Counter
 def edgecounts(triangles):
  return Counter(tuple(sorted((int(tri[j]),int(tri[(j+1)%3])))) for tri in triangles for j in range(3))
 keptEdges=edgecounts(keep);deletedEdges=edgecounts(tt[remove]);cutEdges=[e for e,c in keptEdges.items() if c==1 and deletedEdges.get(e,0)>0]
 panelEdges=edgecounts(panelTris);sewEdges=[]
 def atCuff(q):
  side='Left' if q[0]<0 else 'Right';a=cuffBind[names.index(side+'UpperArm'),:3,3];b=cuffBind[names.index(side+'LowerArm'),:3,3];t=(q-a)@(b-a)/np.dot(b-a,b-a);return abs(t-(.58 if sex=='Male' else .62))<1e-5
 for edge,c in panelEdges.items():
  if c==1 and not (atCuff(newPoints[edge[0]]) and atCuff(newPoints[edge[1]])):sewEdges.append(edge)
 edgeSplits={};connections={};maxSewDistance=0.
 for oldIndex in sorted(set(v for edge in cutEdges for v in edge)):
  q=rest[oldIndex];best=None
  for edge in sewEdges:
   u,v=edge;a=newPoints[u];b=newPoints[v];axis=b-a;amount=float(np.clip((q-a)@axis/max(axis@axis,1e-15),0,1));point=a+axis*amount;distance=float(np.linalg.norm(q-point))
   if best is None or distance<best[0]:best=(distance,edge,amount,point)
  if best is None:continue
  distance,edge,amount,point=best;maxSewDistance=max(maxSewDistance,distance);u,v=edge
  if amount<1e-6:index=u
  elif amount>1-1e-6:index=v
  else:
   key=(edge,round(amount,7))
   existing=edgeSplits.setdefault(edge,{})
   if key[1] in existing:index=existing[key[1]]
   else:
    index=len(newPoints);normal=newNormals[u]*(1-amount)+newNormals[v]*amount;normal/=max(np.linalg.norm(normal),1e-12);newPoints.append(point);newNormals.append(normal);newWeights.append(newWeights[u]*(1-amount)+newWeights[v]*amount);newUV.append(newUV[u]*(1-amount)+newUV[v]*amount);newClearance.append(.012);source.append({'panelEdge':[int(u),int(v)],'amount':amount});existing[key[1]]=index
  connections[oldIndex]=index
 # Split boundary triangles at every strip endpoint, removing T-junctions.
 finalPanel=[]
 for triangle in panelTris:
  handled=False
  for j in range(3):
   u,v=triangle[j],triangle[(j+1)%3];edge=tuple(sorted((u,v)))
   if edge not in edgeSplits:continue
   inserts=sorted(edgeSplits[edge].items(),reverse=u>v);chain=[u]+[i for amount,i in inserts]+[v];other=triangle[(j+2)%3]
   finalPanel.extend([[chain[k],chain[k+1],other] for k in range(len(chain)-1)]);handled=True;break
  if not handled:finalPanel.append(triangle)
 panelTris=finalPanel;bridgeTris=[]
 for u,v in cutEdges:
  if u not in connections or v not in connections:continue
  a,b=connections[u]+len(base),connections[v]+len(base)
  if a==b:continue
  for triangle in ([u,v,b],[u,b,a]):
   positions=np.array([rest[k] if k<len(base) else newPoints[k-len(base)] for k in triangle]);n=np.cross(positions[1]-positions[0],positions[2]-positions[0]);target=sum(np.array(profileN[k]) if k<len(base) else newNormals[k-len(base)] for k in triangle)
   if np.linalg.norm(n)<1e-10:continue
   if n@target<0:triangle=[triangle[0],triangle[2],triangle[1]]
   bridgeTris.append(triangle)

 points=np.array(newPoints);normal=np.array(newNormals);denseWeights=np.array(newWeights);idx=np.argsort(denseWeights,axis=1)[:,::-1][:,:4];weight=np.take_along_axis(denseWeights,idx,axis=1);weight[weight<.001]=0;weight/=weight.sum(1)[:,None];local=xf(np.linalg.inv(rt),points);ln=normal@rt[:3,:3];ln/=np.maximum(np.linalg.norm(ln,axis=1)[:,None],1e-12);allBase=np.concatenate([base,local]);allNormal=np.concatenate([np.array(p['normals']).reshape(-1,3),ln]);allIds=np.concatenate([oldI,idx]);allWeights=np.concatenate([oldW,weight]);allUv=np.concatenate([uv,np.array(newUV)]);tris=np.concatenate([keep,np.array(panelTris)+len(base),np.array(bridgeTris,dtype=int).reshape(-1,3)]);clearance=np.concatenate([np.zeros(len(base)),np.array(newClearance)])
 profile=json.loads(json.dumps(p));profile['vertexCount']=len(allBase);profile['vertices']=allBase.ravel().tolist();profile['normals']=allNormal.ravel().tolist()
 for anchor in profile['anchors']:
  anchor['deltas']+=np.zeros_like(local).ravel().tolist();anchor['normalDeltas']+=np.zeros_like(local).ravel().tolist()
 data={'sex':sex,'vertexCount':len(allBase),'originalVertexCount':len(base),'vertices':allBase.ravel().tolist(),'normals':allNormal.ravel().tolist(),'uv':allUv.ravel().tolist(),'indices':allIds.ravel().tolist(),'weights':allWeights.ravel().tolist(),'triangles':tris.ravel().tolist(),'retainedTriangles':keep.ravel().tolist(),'panelTriangles':np.concatenate([np.array(panelTris)+len(base),np.array(bridgeTris,dtype=int).reshape(-1,3)]).ravel().tolist(),'clearanceMetres':clearance.tolist(),'bones':names,'bindposes':canon['bindposes'],'rendererToRoot':canon['rendererToRoot'],'sourceBodyBarycentrics':source,'removedOldGarmentTriangles':int(remove.sum()),'addedPanelTriangles':len(panelTris),'sewnBridgeTriangles':len(bridgeTris),'sewMaximumBindWidthMm':maxSewDistance*1000,'clearanceChannel':'UV3.x / TEXCOORD3.x. Existing vertices0; new panel0.012m; normalize world normal before applying world offset. Shared forward/depth/shadow deformation required.','contract':'Only old sleeve/gusset garment triangles replaced. All old vertex positions/UV/weights and10 anchor arrays kept exact; appended clean panel Body-derived bind mesh/weights gets no incompatible garment morphs. Body unchanged. Inset overlap sews onto retained central cloth.'}
 (W/f'Panel_{sex}.json').write_text(json.dumps(data,separators=(',',':')));(W/f'SleeveFit_{sex}.json').write_text(json.dumps(profile,separators=(',',':')))
 for action in ('Serve','Forehand'):
  for phase in (0,1,2):
   label=f'{sex.lower()}_{action}_{phase}';snap=json.loads((D/(label+'.json')).read_text());b,t=snap['parts'][:2];before=evaluate(p,t,canon,oldI,oldW);after=evaluate(profile,t,canon,allIds,allWeights);skin=skin_for(t,canon);mix=(skin[allIds]*allWeights[:,:,None,None]).sum(1);localN=np.einsum('nij,nj->ni',mix[:,:3,:3],allNormal);worldN=localN@np.linalg.inv(rt[:3,:3]);worldN/=np.maximum(np.linalg.norm(worldN,axis=1)[:,None],1e-12);after+=worldN*clearance[:,None];bp=xf(np.array(b['rendererToRoot']).reshape(4,4),arr(b,'posedVertices',3));pv=BVHTree.FromPolygons([Vector(v) for v in bp],[tuple(tri) for tri in bt],all_triangles=True);gaps=[]
   for q in after[len(base):]:
    h,n,j,d=pv.find_nearest(Vector(q));gaps.append(float((Vector(q)-h).dot(n)))
   gaps=np.array(gaps);metrics={'label':label,'panelInsideSamplesBeyond1mm':int((gaps<-.001).sum()),'panelMinimumSignedMm':float(gaps.min()*1000),'oldVerticesExactPoseMaxMm':float(np.linalg.norm(before-after[:len(base)],axis=1).max()*1000),'status':'SOURCE CANDIDATE; visual sewn-seam and all33 exact-motion acceptance pending'};REPORT[label]=metrics;print(metrics,flush=True);np.savez_compressed(W/(label+'.npz'),before=before,after=after,body=bp,bodyTriangles=bt,topTriangles=tris,beforeTriangles=tt,bodyRest=br,bodyIndices=arr(b,'indices',4).astype(int),bodyWeights=arr(b,'weights',4),bodyNames=np.array(b['bones']))
 print(sex,'oldTrianglesRemoved',int(remove.sum()),'newTriangles',len(panelTris),'addedVertices',len(local),flush=True)
(W/'source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
