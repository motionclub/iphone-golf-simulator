import sys
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1')
from common import *
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def clip(poly,plane):
 out=[]
 for i,a in enumerate(poly):
  b=poly[(i+1)%len(poly)];da=plane(a[:3]);db=plane(b[:3])
  if da>=-1e-9:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*(da/(da-db)))
 return out
REPORT={}
for sex in ('Male','Female'):
 covered,top,raw=source(sex)
 full=json.loads((R/f'proof/reference-rebuild/character-cloth14/poses/{sex.lower()}_Serve_0.json').read_text())['parts'][0]
 assert full['bones']==covered['bones'];assert full['bindposes']==covered['bindposes']
 full['rendererToRoot']=covered['rendererToRoot']
 rt=np.array(top['rendererToRoot']).reshape(4,4);brt=np.array(full['rendererToRoot']).reshape(4,4)
 base=arr(top,'vertices',3);rest=xf(rt,base);br=xf(brt,arr(full,'vertices',3));bt=arr(full,'triangles',3).astype(int);tt=arr(top,'triangles',3).astype(int)
 uv=arr(top,'uv',2);norm=arr(top,'normals',3);bn=arr(full,'normals',3)@np.linalg.inv(brt[:3,:3]);bn/=np.maximum(np.linalg.norm(bn,axis=1)[:,None],1e-12)
 oldI=arr(top,'indices',4).astype(int);oldW=arr(top,'weights',4);bw=dense(full,top['bones'])
 bvh=BVHTree.FromPolygons([Vector(q) for q in rest],[tuple(q) for q in tt],all_triangles=True)
 # Preserve the original sewn central front/back, collar and placket pieces.
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
 components=np.array([find(i) for i in range(len(base))]);labels,cnts=np.unique(components,return_counts=True);main=labels[cnts.argmax()];sewn=components==main
 for label in labels:
  ids=np.where(components==label)[0];q=rest[ids];lo=q.min(0);hi=q.max(0);size=hi-lo
  if np.min(abs(q[:,0]))>(.18 if sex=='Male' else .115) and lo[1]>1.04 and hi[1]<(1.39 if sex=='Male' else 1.35) and size[1]<.15 and size[0]<.16:sewn[ids]=True
 cut=.105 if sex=='Male' else .080;low=1.075 if sex=='Male' else 1.070;high=1.465 if sex=='Male' else 1.415
 sleeve=sewn&(abs(rest[:,0])>cut)&(rest[:,1]>low)&(rest[:,1]<high)
 waist=sewn&(rest[:,1]<1.055)
 remove=(sleeve|waist)[tt].any(1);keep=tt[~remove]
 cuffBind=rt[None]@np.linalg.inv(arr(top,'bindposes',16).reshape(-1,4,4));points=[];normal=[];weights=[];mappedUv=[];clear=[];panel=[];correspondence=[];weld={}
 def add_domain(planes,tag,allowed):
  allowedMass=bw[:,[top['bones'].index(n) for n in allowed]].sum(1)
  for face in bt:
   if allowedMass[face].min()<.80:continue
   poly=[np.concatenate([br[face[j]],np.eye(3)[j]]) for j in range(3)]
   for plane in planes:
    if len(poly)<3:break
    poly=clip(poly,plane)
   if len(poly)<3:continue
   ids=[]
   for v in poly:
    q=v[:3];baryWeights=v[3:];key=tuple(np.round(q*1e7).astype(int))
    if key not in weld:
     i=len(points);weld[key]=i;n=baryWeights@bn[face];n/=max(np.linalg.norm(n),1e-12);w=baryWeights@bw[face];w=np.maximum(w,0);w/=w.sum()
     h,_,f,_=bvh.find_nearest(Vector(q));u=bary(np.array(h),rest[tt[f]])@uv[tt[f]]
     points.append(q);normal.append(n);weights.append(w);mappedUv.append(u);clear.append(.012);correspondence.append({'vertices':face.tolist(),'weights':baryWeights.tolist(),'domain':tag})
    ids.append(weld[key])
   for j in range(1,len(ids)-1):
    tri=[ids[0],ids[j],ids[j+1]];q=np.array([points[k] for k in tri]);area=np.cross(q[1]-q[0],q[2]-q[0])
    if np.linalg.norm(area)>1e-10:panel.append(tri)
 for side,sign in (('Left',-1),('Right',1)):
  a=cuffBind[top['bones'].index(side+'UpperArm'),:3,3];b=cuffBind[top['bones'].index(side+'LowerArm'),:3,3];axis=b-a;length=np.linalg.norm(axis);direction=axis/length
  add_domain([lambda q,s=sign:s*q[0]-(cut-.030),lambda q:q[1]-(low-.025),lambda q:(high+.006)-q[1],lambda q,a=a,direction=direction,length=length:.58-(q-a)@direction/length],side,('Hips','Spine','Chest','UpperChest',side+'Shoulder',side+'UpperArm'))
 # Continuous tucked waist support: only the lower sewn shirt is replaced.
 add_domain([lambda q:q[1]-.920,lambda q:(low-.025)-q[1],lambda q:.195-abs(q[0])], 'Waist', ('Hips','Spine','Chest','UpperChest'))

 names=top['bones'];newPoints=points;newNormals=normal;newWeights=weights;newUV=mappedUv;newClearance=clear;panelTris=panel;source=correspondence;profileN=norm@np.linalg.inv(rt[:3,:3]);profileN/=np.maximum(np.linalg.norm(profileN,axis=1)[:,None],1e-12)
 # Explicit sewn strip: original retained cut boundary shares indices with
 # one strip edge; the other is inserted into the supporting panel boundary.
 # This avoids independent underlap edges separating when their weights differ.
 from collections import Counter
 def edgecounts(triangles):
  return Counter(tuple(sorted((int(tri[j]),int(tri[(j+1)%3])))) for tri in triangles for j in range(3))
 keptEdges=edgecounts(keep);deletedEdges=edgecounts(tt[remove]);cutEdges=[e for e,c in keptEdges.items() if c==1 and deletedEdges.get(e,0)>0]
 panelEdges=edgecounts(panelTris);sewEdges=[]
 def atCuff(q):
  side='Left' if q[0]<0 else 'Right';a=cuffBind[names.index(side+'UpperArm'),:3,3];b=cuffBind[names.index(side+'LowerArm'),:3,3];t=(q-a)@(b-a)/np.dot(b-a,b-a);return abs(t-.58)<1e-5
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

 points=newPoints;normal=newNormals;weights=newWeights;mappedUv=newUV;clear=newClearance;panel=panelTris;correspondence=source
 points=np.array(points);normal=np.array(normal);weights=np.array(weights);ids=np.argsort(weights,axis=1)[:,::-1][:,:4];ww=np.take_along_axis(weights,ids,axis=1);ww[ww<.001]=0;ww/=ww.sum(1)[:,None]
 local=xf(np.linalg.inv(rt),points);ln=normal@rt[:3,:3];ln/=np.maximum(np.linalg.norm(ln,axis=1)[:,None],1e-12)
 allBase=np.concatenate([base,local]);allN=np.concatenate([norm,ln]);allI=np.concatenate([oldI,ids]);allW=np.concatenate([oldW,ww]);allUV=np.concatenate([uv,np.array(mappedUv)]);tris=np.concatenate([keep,np.array(panel)+len(base),np.array(bridgeTris,dtype=int).reshape(-1,3)]);clearance=np.concatenate([np.zeros(len(base)),clear])
 deltas=np.concatenate([raw['shapeDeltas'],np.zeros((len(raw['shapeNames']),len(local),3))],axis=1)
 nd=np.concatenate([raw['shapeNormalDeltas'],np.zeros_like(deltas[:,len(base):])],axis=1) if 'shapeNormalDeltas' in raw else np.zeros_like(deltas)
 data={'sex':sex,'vertexCount':len(allBase),'originalVertexCount':len(base),'vertices':allBase.ravel().tolist(),'normals':allN.ravel().tolist(),'uv':allUV.ravel().tolist(),'indices':allI.ravel().tolist(),'weights':allW.ravel().tolist(),'triangles':tris.ravel().tolist(),'retainedTriangles':keep.ravel().tolist(),'panelTriangles':(np.array(panel)+len(base)).ravel().tolist(),'bridgeTriangles':np.array(bridgeTris,dtype=int).reshape(-1,3).ravel().tolist(),'clearanceMetres':clearance.tolist(),'bones':top['bones'],'bindposes':top['bindposes'],'rendererToRoot':top['rendererToRoot'],'sourceBodyBarycentrics':correspondence,'shapeNames':[str(n) for n in raw['shapeNames']],'shapeDeltas':deltas.reshape(len(deltas),-1).tolist(),'shapeNormalDeltas':nd.reshape(len(nd),-1).tolist(),'name':sex+' golf polo (sport tailoring) (axilla weight field) (sewn supported panels)','removedOldGarmentTriangles':int(remove.sum()),'addedPanelTriangles':len(panel),'clearanceChannel':'SetUVs(3, Vector4(clearanceMetres,0,0,0)); TEXCOORD3.x <=.012 metres. _PanelClearanceScale=1.0936. Original vertices0.','contract':'Retain exact original central torso/collar/placket geometry, UVs, weights and all7 GolfFit morphs; replace old sleeve/side gusset and hem triangles with Body-supported panels sewn to retained old garment edges through shared-index bridge strips, matching 53-bone rig, no incompatible local old morphs. Production Body and gameplay remain unchanged. The old/new seam is a connected indexed triangle strip rather than independent underlap surfaces.'}
 (W/f'Panel_{sex}.json').write_text(json.dumps(data,separators=(',',':')))
 np.savez_compressed(W/f'{sex}_candidate.npz',vertices=allBase,normals=allN,indices=allI,weights=allW,uv=allUV,triangles=tris,panelTriangles=np.array(panel)+len(base),clearance=clearance,shapeDeltas=deltas,shapeNormalDeltas=nd,fullBodyVertices=arr(full,'vertices',3),fullBodyTriangles=bt,fullBodyIndices=arr(full,'indices',4).astype(int),fullBodyWeights=arr(full,'weights',4),fullBodyNormals=arr(full,'normals',3),rendererToRoot=rt,bodyRendererToRoot=brt)
 report={'oldTriangles':len(tt),'removedTriangles':int(remove.sum()),'retainedTriangles':len(keep),'addedTriangles':len(panel),'addedVertices':len(local),'bridgeTriangles':len(bridgeTris),'cutEdges':len(cutEdges),'connectedCutVertices':len(connections),'maxSewDistanceMm':maxSewDistance*1000,'fullBodyBindExact':True,'allOldVerticesUVWeightsShapesRetainedExact':True,'samples':{}}
 for path in sorted((D/'matrices').glob(sex.lower()+'*.json')):
  sample=json.loads(path.read_text());parts={p['name']:p for p in sample['parts']};mp=parts['Kit_Top'];m=np.array(mp['skinMatrices']).reshape(-1,4,4);bmat=np.array(parts['Body']['skinMatrices']).reshape(-1,4,4)
  sw=np.array(mp['shapeWeights'])/100.;order=[mp['shapeNames'].index(str(n)) for n in raw['shapeNames']];sw=sw[order]
  oldPose=skin(top,base+np.einsum('s,sni->ni',sw,raw['shapeDeltas']),matrices=m);after=skin(top,allBase+np.einsum('s,sni->ni',sw,deltas),allI,allW,m)
  pn=skin_normals(top,allN,allI,allW,m)@np.linalg.inv(rt[:3,:3]);pn/=np.maximum(np.linalg.norm(pn,axis=1)[:,None],1e-12);after=xf(rt,after)+pn*clearance[:,None]
  bp=xf(brt,skin(full,arr(full,'vertices',3),matrices=bmat));pv=BVHTree.FromPolygons([Vector(q) for q in bp],[tuple(t) for t in bt],all_triangles=True);gaps=[]
  for q in after[len(base):]:
   h,n,j,d=pv.find_nearest(Vector(q));gaps.append(float((Vector(q)-h).dot(n)))
  gaps=np.array(gaps);area=np.cross(after[tris[:,1]]-after[tris[:,0]],after[tris[:,2]]-after[tris[:,0]])
  report['samples'][path.stem]={'time':sample['time'],'panelInsideBeyond3mm':int((gaps<-.003).sum()),'panelMinimumSignedMm':float(gaps.min()*1000),'panelDegenerateFacesBelow1e-10':int((np.linalg.norm(area[len(keep):],axis=1)<1e-10).sum()),'retainedPoseMaxErrorMm':float(np.linalg.norm(xf(rt,oldPose)-after[:len(base)],axis=1).max()*1000)}
  # Keep all310 source frames for independent source proof and montage.
  np.savez_compressed(W/(path.stem+'.npz'),before=xf(rt,oldPose),after=after,body=bp,bodyTriangles=bt,topTriangles=tris,beforeTriangles=tt,panelTriangles=np.array(panel)+len(base))
 worst=max(report['samples'].items(),key=lambda p:p[1]['panelInsideBeyond3mm']);report['worst']=worst;REPORT[sex]=report
 print(sex,'added',len(local),len(panel),'worst',worst,flush=True)
(W/'source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
