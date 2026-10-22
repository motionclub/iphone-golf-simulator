import pathlib,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition/bind-panel';D=R/'proof/reference-rebuild/character-cloth14/poses'
src=(R/'work/reference-rebuild/garment-weight-transition/author_weights.py').read_text();exec(src[src.index('def bary('):src.index('REPORT={}')]);src=(R/'work/reference-rebuild/garment-stroke-coverage/author_stroke_envelopes.py').read_text();exec(src[src.index('def arr('):src.index('def author(')])
REPORT={}
for sex in ('Male','Female'):
 profile=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text());body,canon=json.loads((D/f'{sex.lower()}_Forehand_1.json').read_text())['parts'][:2];rt=np.array(canon['rendererToRoot']).reshape(4,4);base=np.array(profile['vertices']).reshape(-1,3);rest=xf(rt,base);br=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'vertices',3));bt=arr(body,'triangles',3).astype(int);tt=arr(canon,'triangles',3).astype(int);bodyNormals,_=geom_normals(br,bt);names=canon['bones'];oldIds=arr(canon,'indices',4).astype(int);oldW=arr(canon,'weights',4);old=dense(canon,names);bw=dense(body,names);bvh=BVHTree.FromPolygons([Vector(v) for v in br],[tuple(t) for t in bt],all_triangles=True)
 groups={};group=np.array([groups.setdefault(tuple(np.round(q*1e5).astype(int)),len(groups)) for q in base]);count=len(groups);adj=[set() for _ in range(count)]
 for tri in group[tt]:
  for i in tri:adj[i].update(int(j) for j in tri if j!=i)
 parent=np.arange(count)
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,js in enumerate(adj):
  for j in js:
   a,c=find(i),find(j)
   if a!=c:parent[c]=a
 comp=np.array([find(i) for i in range(count)]);labels,cnts=np.unique(comp,return_counts=True);main=labels[cnts.argmax()];allowed=comp[group]==main
 for id in labels:
  vertices=np.where(comp[group]==id)[0];q=rest[vertices];lo=q.min(0);hi=q.max(0);size=hi-lo
  if np.min(abs(q[:,0]))>(.18 if sex=='Male' else .115) and lo[1]>1.045 and hi[1]<(1.37 if sex=='Male' else 1.33) and size[1]<.14 and size[0]<.15:allowed[vertices]=True
 x=abs(rest[:,0]);y=rest[:,1];arms=[names.index(n) for n in ('LeftShoulder','LeftUpperArm','LeftLowerArm','RightShoulder','RightUpperArm','RightLowerArm')];armMass=old[:,arms].sum(1)
 cuff=S(.15,.50,armMass);gusset=S(.12 if sex=='Male' else .085,.16 if sex=='Male' else .11,x)*(1-S(1.28 if sex=='Male' else 1.235,1.36 if sex=='Male' else 1.315,y))*S(1.12 if sex=='Male' else 1.10,1.165 if sex=='Male' else 1.14,y)
 field=np.maximum(cuff,gusset)*S(.085 if sex=='Male' else .06,.135 if sex=='Male' else .11,x)*(1-S(.30 if sex=='Male' else .23,.35 if sex=='Male' else .29,x))*S(1.09 if sex=='Male' else 1.07,1.15 if sex=='Male' else 1.125,y)*(1-S(1.385 if sex=='Male' else 1.32,1.46 if sex=='Male' else 1.415,y))*allowed
 field[(y>(1.39 if sex=='Male' else 1.34))&(x<.135)]=0
 newRoot=rest.copy();weights=old.copy();attachment=[]
 for i in np.where(field>1e-6)[0]:
  h,n,tri,d=bvh.find_nearest(Vector(rest[i]));ids=bt[tri];baryWeights=bary(np.array(h),br[ids]);normal=baryWeights@bodyNormals[ids];normal/=max(np.linalg.norm(normal),1e-12);signed=(rest[i]-np.array(h))@normal;gap=np.clip(signed,.009,.025);target=np.array(h)+normal*gap;newRoot[i]=rest[i]*(1-field[i])+target*field[i];desired=baryWeights@bw[ids];weights[i]=old[i]*(1-field[i])+desired*field[i];attachment.append({'garmentVertex':int(i),'bodyTriangle':int(tri),'barycentric':baryWeights.tolist(),'clearance':float(gap)})
 # Bind correspondence is authored once; no motion-space projection.
 size=np.bincount(group);averaged=np.zeros((count,3));mapped=np.zeros((count,len(names)));np.add.at(averaged,group,newRoot);np.add.at(mapped,group,weights);averaged/=size[:,None];mapped/=size[:,None];newRoot=averaged[group];weights=mapped[group]
 changed=field>1e-6;order=np.argsort(weights,axis=1)[:,::-1][:,:4];nw=np.take_along_axis(weights,order,axis=1);nw[nw<.001]=0;nw/=nw.sum(1)[:,None];order[~changed]=oldIds[~changed];nw[~changed]=oldW[~changed];newRoot[~changed]=rest[~changed];newBase=xf(np.linalg.inv(rt),newRoot);newBase[~changed]=base[~changed]
 restNormal,_=geom_normals(newRoot,tt);localNormal=restNormal@rt[:3,:3];localNormal/=np.maximum(np.linalg.norm(localNormal,axis=1)[:,None],1e-12);localNormal[~changed]=np.array(profile['normals']).reshape(-1,3)[~changed]
 staged=json.loads(json.dumps(profile));staged['vertices']=newBase.ravel().tolist();staged['normals']=localNormal.ravel().tolist()
 for a in staged['anchors']:
  delta=np.array(a['deltas']).reshape(-1,3);nd=np.array(a['normalDeltas']).reshape(-1,3);delta*=1-field[:,None];nd*=1-field[:,None];a['deltas']=delta.ravel().tolist();a['normalDeltas']=nd.ravel().tolist()
 _,oldArea=geom_normals(rest,tt);_,newArea=geom_normals(newRoot,tt);restFlip=(np.linalg.norm(oldArea,axis=1)>1e-7)&((oldArea*newArea).sum(1)<0)
 data={'vertexCount':len(base),'bones':names,'oldBaseVertices':profile['vertices'],'vertices':staged['vertices'],'normals':staged['normals'],'indices':order.ravel().tolist(),'weights':nw.ravel().tolist(),'field':field.tolist(),'changedVertices':int(changed.sum()),'bindMaxMovementMm':float(np.linalg.norm(rest-newRoot,axis=1).max()*1000),'restOrientationChanges':int(restFlip.sum()),'bodyAttachments':attachment,'contract':'Refit shortened sleeve/gusset bind positions and weights together after existing prep; suppress incompatible old sleeve deltas in precisely the same field. Collar/placket/central torso unchanged. Original rig, Body, topology and UVs unchanged.'}
 (W/f'Panel_{sex}.json').write_text(json.dumps(data,separators=(',',':')));(W/f'SleeveFit_{sex}.json').write_text(json.dumps(staged,separators=(',',':')))
 for action in ('Serve','Forehand'):
  for phase in (0,1,2):
   label=f'{sex.lower()}_{action}_{phase}';snap=json.loads((D/(label+'.json')).read_text());b,t=snap['parts'][:2];before=evaluate(profile,t,canon,oldIds,oldW);after=evaluate(staged,t,canon,order,nw);bp=xf(np.array(b['rendererToRoot']).reshape(4,4),arr(b,'posedVertices',3));pv=BVHTree.FromPolygons([Vector(v) for v in bp],[tuple(tri) for tri in bt],all_triangles=True);signed=[]
   for q in (before,after):
    gaps=[]
    for i in np.where(changed)[0]:
     h,n,j,d=pv.find_nearest(Vector(q[i]));gaps.append(float((Vector(q[i])-h).dot(n)))
    signed.append(np.array(gaps))
   _,a0=geom_normals(before,tt);_,a1=geom_normals(after,tt);metrics={'label':label,'beforeInsideSamples':int((signed[0]<-.003).sum()),'afterInsideSamples':int((signed[1]<-.003).sum()),'beforeMinMm':float(signed[0].min()*1000),'afterMinMm':float(signed[1].min()*1000),'outsidePoseErrorMm':float(np.linalg.norm(before[~changed]-after[~changed],axis=1).max()*1000),'newDegenerateTriangles':int(((np.linalg.norm(a0,axis=1)>1e-9)&(np.linalg.norm(a1,axis=1)<1e-10)).sum())};REPORT[label]=metrics;print(metrics,flush=True);np.savez_compressed(W/(label+'.npz'),before=before,after=after,body=bp,bodyTriangles=bt,topTriangles=tt,baseRoot=rest,bodyRest=br,bodyIndices=arr(b,'indices',4).astype(int),bodyWeights=arr(b,'weights',4),bodyNames=np.array(b['bones']))
 print(sex,'refit',data['changedVertices'],data['bindMaxMovementMm'],'restOrientationChanges',data['restOrientationChanges'],flush=True)
(W/'source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
