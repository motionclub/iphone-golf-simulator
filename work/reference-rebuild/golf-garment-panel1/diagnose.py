import sys
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1')
from common import *
from mathutils import Vector
from mathutils.bvhtree import BVHTree
REPORT={}
for sex in ('Male','Female'):
 body,top,raw=source(sex);br=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'vertices',3));tr=xf(np.array(top['rendererToRoot']).reshape(4,4),arr(top,'vertices',3));bt=arr(body,'triangles',3).astype(int)
 bvh=BVHTree.FromPolygons([Vector(v) for v in br],[tuple(t) for t in bt],all_triangles=True)
 bd=dense(body,top['bones']);td=dense(top,top['bones']);rows=[]
 region=(tr[:,1]>1.05)&(tr[:,1]<(1.43 if sex=='Male' else 1.385))&(abs(tr[:,0])>.065)
 for i in np.where(region)[0]:
  h,n,idx,d=bvh.find_nearest(Vector(tr[i]));signed=float((Vector(tr[i])-h).dot(n));desired=bary(np.array(h),br[bt[idx]])@bd[bt[idx]];error=abs(td[i]-desired).sum()
  if signed<-.001 or error>.6:rows.append({'vertex':int(i),'restRoot':tr[i].tolist(),'signedRestMm':signed*1000,'weightL1Mismatch':float(error),'current':{n:float(w) for n,w in zip(top['bones'],td[i]) if w>.001},'bodySurface':{n:float(w) for n,w in zip(top['bones'],desired) if w>.001}})
 rows.sort(key=lambda r:r['signedRestMm']);report={'bindCandidates':len(rows),'worstBind':rows[:12],'fullPoses':{}}
 for path in sorted((D/'poses').glob(sex.lower()+'*.json')):
  b,t=json.loads(path.read_text())['parts'][:2];w=top_weights(sex,t);delta=np.einsum('s,sni->ni',w,raw['shapeDeltas']);pred=skin(t,arr(t,'vertices',3)+delta);actual=arr(t,'posedVertices',3)/UNITS
  bodyPred=skin(b,arr(b,'vertices',3));bodyActual=arr(b,'posedVertices',3)/UNITS
  bp=xf(np.array(b['rendererToRoot']).reshape(4,4),bodyActual);tp=xf(np.array(t['rendererToRoot']).reshape(4,4),actual);posedBVH=BVHTree.FromPolygons([Vector(v) for v in bp],[tuple(q) for q in bt],all_triangles=True)
  gaps=[]
  for i in np.where(region)[0]:
   h,n,idx,d=posedBVH.find_nearest(Vector(tp[i]));gaps.append(float((Vector(tp[i])-h).dot(n)))
  gaps=np.array(gaps);r={'topOracleMaxMm':float(np.linalg.norm(pred-actual,axis=1).max()*1000),'bodyOracleMaxMm':float(np.linalg.norm(bodyPred-bodyActual,axis=1).max()*1000),'insideSamplesBelow3mm':int((gaps<-.003).sum()),'worstSignedClearanceMm':float(gaps.min()*1000),'weightedShapes':{str(n):float(v) for n,v in zip(raw['shapeNames'],w)}}
  report['fullPoses'][path.stem]=r;print(path.stem,r['topOracleMaxMm'],r['insideSamplesBelow3mm'],r['worstSignedClearanceMm'],flush=True)
 REPORT[sex]=report
(W/'diagnosis.json').write_text(json.dumps(REPORT,indent=2)+'\n')
