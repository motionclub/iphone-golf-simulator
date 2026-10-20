import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Sleeve.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;b=json.loads((w/'baseline/poses/male_intro.json').read_text())['parts'][0];bp=[Vector((-b['vertices'][i],*b['vertices'][i+1:i+3])) for i in range(0,len(b['vertices']),3)];bn=[Vector((-b['normals'][i],*b['normals'][i+1:i+3])) for i in range(0,len(b['normals']),3)];bt=[b['triangles'][i:i+3][::-1] for i in range(0,len(b['triangles']),3)];tree=BVHTree.FromPolygons(bp,bt,all_triangles=True);rows=[]
for f in m.polygons:
 hit,n,fi,dist=tree.find_nearest(f.center);bodyN=sum((bn[i] for i in bt[fi]),Vector()).normalized();rows.append([f.normal.dot(bodyN),dist,f.center.x,f.center.y,f.center.z])
a=np.array(rows);inside=(a[:,0]<-.4)&(a[:,1]<.05);print('FACES',len(a),'innerCandidate',sum(inside),'extents',a[inside,2:].min(0),a[inside,2:].max(0),'dotQuantiles',np.quantile(a[:,0],[0,.1,.25,.5,.75,.9,1]),flush=True)
for lo,hi in [(0,.13),(.13,.21),(.21,.5)]:
 use=(abs(a[:,2])>=lo)&(abs(a[:,2])<hi);print(lo,hi,'faces',sum(use),'inner',sum(inside&use),flush=True)
np.savez(w/'lining-classification.npz',rows=a,inner=inside)
