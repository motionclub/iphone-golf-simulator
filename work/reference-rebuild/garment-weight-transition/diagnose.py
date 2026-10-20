import pathlib,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition';D=R/'proof/reference-rebuild/character-cloth14/poses';report={}
def arr(p,k,n):return np.array(p[k],float).reshape(-1,n)
def xf(m,p):return p@m[:3,:3].T+m[:3,3]
def bary(p,tri):
 a,b,c=tri;v0=b-a;v1=c-a;v2=p-a;d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01
 if abs(den)<1e-18:return np.array([1.,0,0])
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;q=np.maximum([1-v-w,v,w],0);return q/q.sum()
for sex in ('male','female'):
 snap=json.loads((D/f'{sex}_Forehand_1.json').read_text());body,top=snap['parts'][:2];br=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'vertices',3));tr=xf(np.array(top['rendererToRoot']).reshape(4,4),arr(top,'vertices',3));bt=arr(body,'triangles',3).astype(int);bvh=BVHTree.FromPolygons([Vector(p) for p in br],[tuple(t) for t in bt],all_triangles=True);bi=arr(body,'indices',4).astype(int);bw=arr(body,'weights',4);ti=arr(top,'indices',4).astype(int);tw=arr(top,'weights',4);bs=body['bones'];ts=top['bones'];dense=np.zeros((len(br),len(ts)))
 for j in range(4):
  ids=np.array([ts.index(bs[k]) for k in bi[:,j]]);dense[np.arange(len(br)),ids]+=bw[:,j]
 td=np.zeros((len(tr),len(ts)))
 for j in range(4):td[np.arange(len(tr)),ti[:,j]]+=tw[:,j]
 def weights(q):return {ts[k]:round(float(q[k]),4) for k in np.where(q>.0005)[0]}
 samples=[]
 for action in ('Serve','Forehand'):
  for phase in (0,1,2):
   s=json.loads((D/f'{sex}_{action}_{phase}.json').read_text());b,t=s['parts'][:2];bp=xf(np.array(b['rendererToRoot']).reshape(4,4),arr(b,'posedVertices',3));tp=xf(np.array(t['rendererToRoot']).reshape(4,4),arr(t,'posedVertices',3));pv=BVHTree.FromPolygons([Vector(p) for p in bp],[tuple(v) for v in bt],all_triangles=True);rows=[]
   region=(tr[:,1]>1.065)&(tr[:,1]<(1.455 if sex=='male' else 1.415))&(abs(tr[:,0])>.075)&(abs(tr[:,0])<.32)
   for i in np.where(region)[0]:
    h,n,idx,d=pv.find_nearest(Vector(tp[i]));signed=float((Vector(tp[i])-h).dot(n))
    if signed>=-.003 or d>.05:continue
    hr,nr,tri,dr=bvh.find_nearest(Vector(tr[i]));ids=bt[tri];q=bary(np.array(hr),br[ids]);desired=q@dense[ids];rows.append({'vertex':int(i),'restRoot':tr[i].tolist(),'posedClearanceMm':signed*1000,'restSurfaceDistanceMm':dr*1000,'restSignedMm':float((Vector(tr[i])-hr).dot(nr))*1000,'currentWeights':weights(td[i]),'bodySurfaceWeights':weights(desired),'weightL1Mismatch':float(abs(td[i]-desired).sum())})
   rows.sort(key=lambda x:x['posedClearanceMm']);key=f'{sex}_{action}_{phase}';report[key]={'penetratingRegionSamples':len(rows),'worst':rows[:8]};print(key,rows[:2],flush=True)
(W/'weight-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
