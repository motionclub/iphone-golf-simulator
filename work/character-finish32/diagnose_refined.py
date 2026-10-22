import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
w=Path('work/character-finish32');d=json.loads((w/'refined/poses/male_intro.json').read_text());b=d['parts'][0];t=next(p for p in d['parts'] if p['name']=='Kit_Top')
P=np.array(t['vertices']).reshape(-1,3);T=np.array(t['triangles']).reshape(-1,3);BP=np.array(b['vertices']).reshape(-1,3);BT=np.array(b['triangles']).reshape(-1,3);BWI=np.array(b['indices']).reshape(-1,4);BW=np.array(b['weights']).reshape(-1,4);WI=np.array(t['indices']).reshape(-1,4);W=np.array(t['weights']).reshape(-1,4)
rest=BVHTree.FromPolygons([Vector(p) for p in BP],BT.tolist(),all_triangles=True)
a=(abs(P[:,0])>.14)&(P[:,2]>1.15)&(P[:,2]<1.40);vid=np.flatnonzero(a);F=T[np.all(a[T],axis=1)];samples=np.concatenate([P[vid],P[F].mean(1)])
for f in [w/'collision-poses/matrices/male_SliceApproach_4.json',w/'collision-poses/matrices/male_IntroWave_4.json']:
 report=json.loads(f.read_text());parts={p['name']:p for p in report['parts']};bm=np.array(parts[b['name']]['skinMatrices']).reshape(-1,4,4);mp={n:bm[j] for j,n in enumerate(b['bones'])};tm=np.array([mp[n] for n in t['bones']]);M=(tm[WI]*W[:,:,None,None]).sum(1);BM=(bm[BWI]*BW[:,:,None,None]).sum(1);q=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];bq=np.einsum('nij,nj->ni',BM[:,:3,:3],BP)+BM[:,:3,3];tree=BVHTree.FromPolygons([Vector(p) for p in bq],BT.tolist(),all_triangles=True);rows=[]
 for k,s in enumerate(np.concatenate([q[vid],q[F].mean(1)])):
  hit,n,fi,dist=tree.find_nearest(Vector(s));signed=(Vector(s)-hit).dot(n)
  if signed<-.005:
   rp=samples[k];rh,rn,rf,rd=rest.find_nearest(Vector(rp));tri=BT[rf];bc=barycentric_transform(rh,*[Vector(BP[j]) for j in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));support=(bq[tri]*np.array(bc)[:,None]).sum(0);rows.append({'signed':signed,'rest':list(rp),'restNear':list(rh),'restDist':rd,'kind':'vertex' if k<len(vid) else 'face','ids':[int(vid[k])] if k<len(vid) else F[k-len(vid)].tolist(),'posed':list(s),'supportDistance':float(np.linalg.norm(s-support))})
 rows.sort(key=lambda r:r['signed']);print(f.name,len(rows),json.dumps(rows[:5]),flush=True)
 for row in rows[:2]:
  for v in row['ids']:print(v,[(t['bones'][j],float(a)) for j,a in zip(WI[v],W[v])])
