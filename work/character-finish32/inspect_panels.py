import bpy,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Panels.blend'));o=bpy.data.objects['Kit_Top'];b=json.loads((w/'baseline/poses/male_intro.json').read_text())['parts'][0];bp=[Vector((-b['vertices'][i],*b['vertices'][i+1:i+3])) for i in range(0,len(b['vertices']),3)];bt=[b['triangles'][i:i+3][::-1] for i in range(0,len(b['triangles']),3)];tree=BVHTree.FromPolygons(bp,bt,all_triangles=True)
for lo,hi in [(.0,.14),(.14,.24),(.24,.4)]:
 rows=[]
 for v in o.data.vertices:
  p=v.co
  if not(lo<abs(p.x)<hi and 1.15<p.z<1.43):continue
  hit,n,fi,d=tree.find_nearest(p);rows.append([(p-hit).dot(n),v.normal.dot(n),p.x,p.y,p.z])
 a=np.array(rows);print(lo,hi,'n',len(a),'clearance',np.quantile(a[:,0],[0,.1,.5,.9,1]),'normals',np.quantile(a[:,1],[0,.1,.5,.9,1]),flush=True)
 print('insideExamples',a[np.argsort(a[:,0])[:3]].tolist(),flush=True)
