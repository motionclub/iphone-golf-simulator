exec(open('work/reference-rebuild/forehand-pole1/analyze.py').read().split('rows=[]')[0])
from mathutils.bvhtree import BVHTree
from mathutils import Vector
for degree in (0,45,60,75,90,105,120):
 b=swivel(degree);bp=pose(body,b,bv);tp,ww=top_pose(b);tt=arr(can[1],'triangles',3);tr=xf(np.array(can[1]['rendererToRoot']).reshape(4,4),arr(can[1],'vertices',3));tn=arr(can[1],'normals',3)@np.array(can[1]['rendererToRoot']).reshape(4,4)[:3,:3].T;outer=(tn[:,0]*tr[:,0]+tn[:,2]*(tr[:,2]-.03))>0;torso=(tr[:,1]<1.2)&(np.abs(tr[:,0])<.23);use=tt[torso[tt].all(1)&outer[tt].all(1)];bvh=BVHTree.FromPolygons([Vector(p) for p in tp],[tuple(t) for t in use],all_triangles=True);s=[]
 for i in np.where(arm)[0]:
  p=bp[i];hit,n,_,dd=bvh.find_nearest(Vector(p));signed=float((Vector(p)-hit).dot(n));t=float((p-b[ni['RightLowerArm'],:3,3])@(H-b[ni['RightLowerArm'],:3,3])/(np.linalg.norm(H-b[ni['RightLowerArm'],:3,3])**2));
  if signed<-.002:s.append((signed*1000,t,i,bp[i].tolist(),list(hit)))
 s.sort();print(degree,len(s),'max',s[:4],'minT',min((x[1] for x in s),default=1),flush=True)
 for p in [H,H+np.array([.02,0,0]),H+np.array([0,0,.02])]:
  hit,n,_,dd=bvh.find_nearest(Vector(p));print('wrist',p.tolist(),'signed',float((Vector(p)-hit).dot(n))*1000,'near',list(hit))
