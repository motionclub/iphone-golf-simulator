import pathlib,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition';D=R/'proof/reference-rebuild/character-cloth14/poses';A=R/'proof/full-visual-overhaul/character-pass-29-art6-crafted/poses'
src=(R/'work/reference-rebuild/garment-stroke-coverage/author_stroke_envelopes.py').read_text();exec(src[src.index('def arr('):src.index('def author(')])
def bary(p,tri):
 a,b,c=tri;v0=b-a;v1=c-a;v2=p-a;d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01
 if abs(den)<1e-18:return np.array([1.,0,0])
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;q=np.maximum([1-v-w,v,w],0);return q/q.sum()
def dense(part,names):
 ids=arr(part,'indices',4).astype(int);w=arr(part,'weights',4);q=np.zeros((len(w),len(names)))
 for j in range(4):
  palette=np.array([names.index(part['bones'][k]) for k in ids[:,j]]);q[np.arange(len(w)),palette]+=w[:,j]
 return q

def skin_for(part,canon):
 rt=np.array(part['rendererToRoot']).reshape(4,4);sm=np.array(part['skinMatrices']).reshape(-1,4,4);bind=np.array(part['bindposes']).reshape(-1,4,4);world=rt[None]@sm@np.linalg.inv(bind);lookup={n:world[i] for i,n in enumerate(part['bones'])};cr=np.array(canon['rendererToRoot']).reshape(4,4);cb=np.array(canon['bindposes']).reshape(-1,4,4)
 return np.linalg.inv(cr)[None]@np.array([lookup[n] for n in canon['bones']])@cb

def mix_pose(skin,ids,weight,v,rt):
 mix=(skin[ids]*weight[:,:,None,None]).sum(1);q=np.einsum('nij,nj->ni',mix,np.column_stack([v,np.ones(len(v))]))[:,:3];return xf(rt,q),mix

def evaluate(profile,part,canon,ids,weight):
 skin=skin_for(part,canon);f=features(part);dist=np.array([np.mean((f-np.array(a['feature']))**2) for a in profile['anchors']]);confidence=1-S(.025,.30,dist.min());weights=1/np.maximum(dist,1e-8)**2;weights*=confidence/weights.sum();delta=sum(np.array(a['deltas']).reshape(-1,3)*w for a,w in zip(profile['anchors'],weights));return mix_pose(skin,ids,weight,np.array(profile['vertices']).reshape(-1,3)+delta,np.array(canon['rendererToRoot']).reshape(4,4))[0]

REPORT={}
for sex in ('Male','Female'):
 p=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text());b,t=json.loads((D/f'{sex.lower()}_Forehand_1.json').read_text())['parts'][:2];rt=np.array(t['rendererToRoot']).reshape(4,4);base=np.array(p['vertices']).reshape(-1,3);rest=xf(rt,base);br=xf(np.array(b['rendererToRoot']).reshape(4,4),arr(b,'vertices',3));bt=arr(b,'triangles',3).astype(int);tt=arr(t,'triangles',3).astype(int);names=t['bones'];oldIds=arr(t,'indices',4).astype(int);oldW=arr(t,'weights',4);old=dense(t,names);body=dense(b,names);bvh=BVHTree.FromPolygons([Vector(q) for q in br],[tuple(tri) for tri in bt],all_triangles=True)
 groups={};group=np.array([groups.setdefault(tuple(np.round(q*1e5).astype(int)),len(groups)) for q in base]);count=len(groups);adj=[set() for _ in range(count)]
 for tri in group[tt]:
  for i in tri:adj[i].update(int(j) for j in tri if j!=i)
 component=np.arange(count)
 def find(i):
  while component[i]!=i:component[i]=component[component[i]];i=component[i]
  return i
 for i,neigh in enumerate(adj):
  for j in neigh:
   a,c=find(i),find(j)
   if a!=c:component[c]=a
 comp=np.array([find(i) for i in range(count)]);label,cnt=np.unique(comp,return_counts=True);main=label[cnt.argmax()];allowed=(comp[group]==main)
 # Existing independent sewn cuffs are included, collar/placket excluded.
 for id in label:
  verts=np.where(comp[group]==id)[0];q=rest[verts];lo=q.min(0);hi=q.max(0);size=hi-lo
  if np.min(abs(q[:,0]))>(.18 if sex=='Male' else .115) and lo[1]>1.045 and hi[1]<(1.37 if sex=='Male' else 1.33) and size[1]<.14 and size[0]<.15:allowed[verts]=True
 x=abs(rest[:,0]);y=rest[:,1]
 field=S(.075 if sex=='Male' else .055,.13 if sex=='Male' else .105,x)*(1-S(.29 if sex=='Male' else .225,.34 if sex=='Male' else .285,x))*S(1.075 if sex=='Male' else 1.055,1.135 if sex=='Male' else 1.115,y)*(1-S(1.375 if sex=='Male' else 1.31,1.455 if sex=='Male' else 1.41,y))*allowed
 field[(y>(1.39 if sex=='Male' else 1.34))&(x<.135)]=0
 proposed=old.copy();bodyDist=np.zeros(len(base))
 for i in np.where(field>1e-6)[0]:
  h,n,tri,dist=bvh.find_nearest(Vector(rest[i]));bodyDist[i]=dist;ids=bt[tri];bw=bary(np.array(h),br[ids])@body[ids];proposed[i]=old[i]*(1-field[i])+bw*field[i]
 # Coincident UV aliases share one physical influence field.
 size=np.bincount(group);average=np.zeros((count,len(names)));np.add.at(average,group,proposed);average/=size[:,None];proposed=average[group]
 order=np.argsort(proposed,axis=1)[:,::-1][:,:4];weight=np.take_along_axis(proposed,order,axis=1);weight[weight<.001]=0;weight/=weight.sum(1)[:,None];changed=field>1e-6;order[~changed]=oldIds[~changed];weight[~changed]=oldW[~changed];new=dense({**t,'indices':order.ravel().tolist(),'weights':weight.ravel().tolist()},names)
 # Rebase existing ten source controls against the new garment weights.
 # Their full posed surfaces and normals remain exact at authored poses.
 staged=json.loads(json.dumps(p));anchorAudit=[]
 for anchor,target in zip(p['anchors'],staged['anchors']):
  path=A/(anchor['shape']+'.json');part=json.loads(path.read_text())['parts'][1];skin=skin_for(part,t);oldTarget,m0=mix_pose(skin,oldIds,oldW,base+np.array(anchor['deltas']).reshape(-1,3),rt);_,m1=mix_pose(skin,order,weight,base,rt);local=xf(np.linalg.inv(rt),oldTarget);newTarget=np.einsum('nij,nj->ni',np.linalg.inv(m1),np.column_stack([local,np.ones(len(local))]))[:,:3];delta=newTarget-base;delta[~changed]=np.array(anchor['deltas']).reshape(-1,3)[~changed];target['deltas']=delta.ravel().tolist()
  oldNormals=np.array(p['normals']).reshape(-1,3)+np.array(anchor['normalDeltas']).reshape(-1,3);posedN=np.einsum('nij,nj->ni',m0[:,:3,:3],oldNormals);newN=np.einsum('nij,nj->ni',np.linalg.inv(m1[:,:3,:3]),posedN);dn=newN-np.array(p['normals']).reshape(-1,3);dn[~changed]=np.array(anchor['normalDeltas']).reshape(-1,3)[~changed];target['normalDeltas']=dn.ravel().tolist();q,_=mix_pose(skin,order,weight,base+delta,rt);anchorAudit.append({'shape':anchor['shape'],'posedPositionErrorMm':float(np.linalg.norm(q-oldTarget,axis=1).max()*1000)})
 data={'vertexCount':len(base),'bones':names,'baseVertices':p['vertices'],'field':field.tolist(),'indices':order.ravel().tolist(),'weights':weight.ravel().tolist(),'changedVertices':int(changed.sum()),'maximumWeightL1Change':float(abs(new-old).sum(1).max()),'outsideWeightsExact':bool(np.array_equal(weight[~changed],oldW[~changed]) and np.array_equal(order[~changed],oldIds[~changed])),'anchorRebaseAudit':anchorAudit,'contract':'Apply after current sleeve/axilla preparation on exact indexed Top basis. Existing Body and rest geometry untouched. Ten existing targets are rebased; no new anchors.'}
 (W/f'Weights_{sex}.json').write_text(json.dumps(data,separators=(',',':')));(W/f'SleeveFit_{sex}.json').write_text(json.dumps(staged,separators=(',',':')))
 rows=[]
 for action in ('Serve','Forehand'):
  for phase in (0,1,2):
   label=f'{sex.lower()}_{action}_{phase}';snap=json.loads((D/(label+'.json')).read_text());body,part=snap['parts'][:2];before=evaluate(p,part,t,oldIds,oldW);after=evaluate(staged,part,t,order,weight);bp=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'posedVertices',3));vbh=BVHTree.FromPolygons([Vector(v) for v in bp],[tuple(tri) for tri in bt],all_triangles=True)
   selected=np.where(changed)[0];signed=[]
   for q in (before,after):
    gaps=[]
    for i in selected:
     h,n,j,d=vbh.find_nearest(Vector(q[i]));gaps.append(float((Vector(q[i])-h).dot(n)))
    signed.append(np.array(gaps))
   _,a0=geom_normals(before,tt);_,a1=geom_normals(after,tt);flips=(np.linalg.norm(a0,axis=1)>1e-7)&((a0*a1).sum(1)<0);m={'label':label,'beforeInsideSamples':int((signed[0]<-.003).sum()),'afterInsideSamples':int((signed[1]<-.003).sum()),'beforeMinMm':float(signed[0].min()*1000),'afterMinMm':float(signed[1].min()*1000),'triangleOrientationChanges':int(flips.sum()),'outsidePoseErrorMm':float(np.linalg.norm(before[~changed]-after[~changed],axis=1).max()*1000),'maxMovementMm':float(np.linalg.norm(before-after,axis=1).max()*1000)};REPORT[label]=m;print(m,flush=True);np.savez_compressed(W/(label+'.npz'),before=before,after=after,body=bp,bodyTriangles=bt,topTriangles=tt,baseRoot=rest,bodyRest=br,bodyIndices=arr(b,'indices',4).astype(int),bodyWeights=arr(b,'weights',4),bodyNames=np.array(b['bones']))
 print(sex,'weights',data['changedVertices'],data['maximumWeightL1Change'],'anchorRebaseMax',max(v['posedPositionErrorMm'] for v in anchorAudit),flush=True)
(W/'source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
