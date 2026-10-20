exec(open('work/reference-rebuild/forehand-pole1/analyze.py').read().split('rows=[]')[0])
from mathutils.bvhtree import BVHTree
from mathutils import Vector
b=swivel(60);bp=pose(body,b,bv);tp,ww=top_pose(b);p=can[1];tt=arr(p,'triangles',3);tv=arr(p,'vertices',3);tid=arr(p,'indices',4).astype(int);tw=arr(p,'weights',4);trt=np.array(p['rendererToRoot']).reshape(4,4);tr=xf(trt,tv);skeleton=b@np.array(p['bindposes']).reshape(-1,4,4);mix=np.sum(skeleton[tid]*tw[:,:,None,None],axis=1)
# Closed body oracle; limit queries to cloth near the posed forearm. Pull toward torso center.
allbt=arr(body,'triangles',3);armMass=(weights*np.isin(ids,[ni['RightLowerArm'],ni['RightHand']])).sum(1);armtri=allbt[(armMass[allbt]>.45).all(1)];bvh=BVHTree.FromPolygons([Vector(x) for x in bp],[tuple(t) for t in armtri],all_triangles=True)
E=b[ni['RightLowerArm'],:3,3];seg=H-E;st=np.clip((tp-E)@seg/(seg@seg),0,1);dist=np.linalg.norm(tp-(E+st[:,None]*seg),axis=1);eligible=(tr[:,0]>.06)&(tr[:,1]>.86)&(tr[:,1]<1.19)&(tr[:,2]>.025)&(dist<.095)
center=(b[ni['Spine'],:3,3]+b[ni['Chest'],:3,3])*.5;inside=[];disp=np.zeros_like(tp)
for i in np.where(eligible)[0]:
 p0=tp[i];nearest,n,_,dd=bvh.find_nearest(Vector(p0));signed=float((Vector(p0)-nearest).dot(n));
 if signed<.004 and dd<.075:
  direction=np.array([center[0]-p0[0],0,center[2]-p0[2]]);direction/=np.linalg.norm(direction);chosen=0
  for d in np.arange(.001,.0501,.001):
   candidate=p0+direction*d;hit,normal,_,distance=bvh.find_nearest(Vector(candidate));sd=float((Vector(candidate)-hit).dot(normal))
   if sd>.004:chosen=d;break
  if chosen:disp[i]=direction*chosen;inside.append((int(i),float(signed),chosen))
# Smooth maximum field with compact radial support to preserve a continuous mesh. Same coordinates get equal displacement.
from mathutils.kdtree import KDTree
kd=KDTree(len(tp))
for i,pos in enumerate(tp):kd.insert(Vector(pos),i)
kd.balance();smoothDisp=disp.copy()
for i,_,d in inside:
 for _,j,distance in kd.find_range(Vector(tp[i]),.04):
  if not eligible[j]:continue
  amount=d*(1-smooth(0,.04,distance));direction=np.array([center[0]-tp[j,0],0,center[2]-tp[j,2]]);direction/=np.linalg.norm(direction)
  if amount>np.linalg.norm(smoothDisp[j]):smoothDisp[j]=direction*amount
local=np.linalg.solve(mix[:,:3,:3],smoothDisp[...,None])[...,0];after=tp+smoothDisp
np.savez_compressed(W/'swivel_60_fit.npz',body=bp,bodyTriangles=bt,top=after,topTriangles=tt,bones=b,bodyRest=br)
changed=np.where(np.linalg.norm(local,axis=1)>.000001)[0];profile={'vertexCount':len(tv),'indices':changed.tolist(),'deltas':local[changed].ravel().tolist(),'contract':'Male ForehandOpen only; authored against +60 degree elbow swivel at .53333 seconds. Existing source positions/weights/UVs unchanged; garment-only waist recess. Drive by same bounded contact window, never body masking.'};(W/'MaleForehandOpenWaist.json').write_text(json.dumps(profile,separators=(',',':')))
print('affected',len(changed),'maximum world mm',np.linalg.norm(smoothDisp,axis=1).max()*1000,'maximum local mm',np.linalg.norm(local,axis=1).max()*1000,'source inside',len(inside));print('bounds rest',tr[changed].min(0),tr[changed].max(0))
