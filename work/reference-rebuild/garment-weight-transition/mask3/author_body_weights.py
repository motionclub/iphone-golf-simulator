from pathlib import Path
__file__=str(Path(__file__).parent/'author_local_cloth_frontcull.py');src=Path(__file__).read_text();exec(src[:src.index('regions=np.array')])
Z=W/'body-correspondent-weights';Z.mkdir(exist_ok=True)
# Weld only for classifying garment components; original indices remain untouched.
uniq,alias=np.unique(np.round(tr,5),axis=0,return_inverse=True);parent=np.arange(len(uniq))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for tri in alias[tt]:
 a=find(tri[0])
 for j in tri[1:]:
  b=find(j)
  if a!=b:parent[b]=a
labels=np.array([find(i) for i in alias]);ls,cs=np.unique(labels,return_counts=True);main=ls[cs.argmax()]
# Actual detached sleeve cuff/seam components, not an axial plane through torso.
cuffs=(labels!=main)&(abs(tr[:,0])>.10)&(tr[:,1]>1.11)&(tr[:,1]<1.23)
roi=(labels==main)&(abs(tr[:,0])>.07)&(abs(tr[:,0])<.18)&(tr[:,1]>1.10)&(tr[:,1]<1.28)
bodyRegion=(abs(rest[:,0])>.108)&(abs(rest[:,0])<.153)&(rest[:,1]>1.145)&(rest[:,1]<1.23)&(arm>.025)&(arm<.98)
bodyFaces=np.where(bodyRegion[bt].any(1))[0]
# Exact point/triangle correspondence; project to face or nearest edge as needed.
def nearest_tri(points,v,tri):
 a=v[tri[:,0]];e1=v[tri[:,1]]-a;e2=v[tri[:,2]]-a;n=np.cross(e1,e2);nn=(n*n).sum(1);d00=(e1*e1).sum(1);d01=(e1*e2).sum(1);d11=(e2*e2).sum(1);den=d00*d11-d01*d01;den=np.maximum(den,1e-24);out=[]
 for q in points:
  rel=q-a;d20=rel@e1.T if False else np.einsum('ij,ij->i',rel,e1);d21=np.einsum('ij,ij->i',rel,e2);v1=(d11*d20-d01*d21)/den;v2=(d00*d21-d01*d20)/den;bary=np.column_stack([1-v1-v2,v1,v2]);closest=a+v1[:,None]*e1+v2[:,None]*e2;valid=(bary>=0).all(1);dist=((q-closest)**2).sum(1);dist[~valid]=np.inf
  for j,k in [(0,1),(1,2),(2,0)]:
   start=v[tri[:,j]];edge=v[tri[:,k]]-start;t=np.clip(np.einsum('ij,ij->i',q-start,edge)/np.maximum((edge*edge).sum(1),1e-24),0,1);near=start+t[:,None]*edge;dd=((q-near)**2).sum(1);sel=dd<dist;dist[sel]=dd[sel];closest[sel]=near[sel];bary[sel]=0;bary[sel,j]=1-t[sel];bary[sel,k]=t[sel]
  i=dist.argmin();out.append((int(i),bary[i],float(np.sqrt(dist[i])),closest[i]))
 return out
query=np.where(roi)[0];hits=nearest_tri(tr[query],rest,bt[bodyFaces]);distance=np.array([h[2] for h in hits]);support=np.zeros(len(tr));r=np.clip((distance-.007)/.022,0,1);support[query]=1-r*r*(3-2*r)
cuffDistance=np.full(len(tr),np.inf);cuffpoints=tr[cuffs]
for ch in np.array_split(query,12):
 if len(ch):cuffDistance[ch]=np.sqrt(((tr[ch,None]-cuffpoints[None])**2).sum(2).min(1))
r=np.clip((cuffDistance-.006)/.017,0,1);support*=r*r*(3-2*r)
# Blend exact barycentric Body weights in the shared named skeleton, then retain
# Unity's four most influential bones. Full detached cuffs/collar/hem unchanged.
bdense=np.zeros((len(rest),len(top['bones'])))
for j in range(4):
 mapped=np.array([top['bones'].index(body['bones'][i]) for i in bi[:,j]]);bdense[np.arange(len(rest)),mapped]+=bw[:,j]
tdense=np.zeros((len(tr),len(top['bones'])))
for j in range(4):tdense[np.arange(len(tr)),ti[:,j]]+=tw[:,j]
desired=tdense.copy()
for i,h in zip(query,hits):desired[i]=h[1]@bdense[bt[bodyFaces[h[0]]]]
result=tdense*(1-support[:,None])+desired*support[:,None]
indices=np.argsort(-result,axis=1)[:,:4];weights=np.take_along_axis(result,indices,axis=1);weights/=weights.sum(1)[:,None]
changed=support>1e-7;indices[~changed]=ti[~changed];weights[~changed]=tw[~changed]
# Carry exact source vertex/normal basis for the existing full/LOD transfer path.
out={'vertexCount':len(tr),'vertices':profile['vertices'],'normals':profile['normals'],'bones':top['bones'],'indices':indices.ravel().tolist(),'weights':weights.ravel().tolist()};(Z/'UnderarmWeights_Female.json').write_text(json.dumps(out,separators=(',',':')));np.savez_compressed(Z/'source.npz',indices=indices,weights=weights,support=support,cuffDistance=cuffDistance)
rows=[]
for i in [10671,7883,7848,8185,10016,7528,7553]:
 rows.append({'vertex':i,'rest':tr[i].tolist(),'support':float(support[i]),'cuffDistanceMm':float(cuffDistance[i]*1000),'before':{top['bones'][int(n)]:float(w) for n,w in zip(ti[i],tw[i]) if w>.0001},'bodyTarget':{top['bones'][int(n)]:float(w) for n,w in enumerate(desired[i]) if w>.0001},'after':{top['bones'][int(n)]:float(w) for n,w in zip(indices[i],weights[i]) if w>.0001}})
report={'changedVertices':int(changed.sum()),'fullTransferVertices':int((support>.999).sum()),'sourceMainComponent':int(main),'protectedDetachedCuffVertices':int(cuffs.sum()),'protectedCuffWeightError':float(np.max(abs(weights[cuffs]-tw[cuffs]))),'restPositionError':0,'uvIndexBoneBindMatrixChange':False,'changedRestBounds':{'min':tr[changed].min(0).tolist(),'max':tr[changed].max(0).tolist()},'tracedVertices':rows};(Z/'author-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
