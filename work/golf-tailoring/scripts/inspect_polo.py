import bpy,bmesh,numpy as np
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath='work/golf-tailoring/export/Golf_Female_Draft.blend')
o=bpy.data.objects['Golf_Polo'];body=bpy.data.objects['Body_F'];body.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[tuple(t.vertices) for t in body.data.loop_triangles],all_triangles=True)
a=o.data.attributes['GolfOuterFace'];rows=[]
for p in o.data.polygons:
 hit=tree.find_nearest(p.center)
 rows.append([p.index,a.data[p.index].value,p.center.x,p.center.y,p.center.z,p.normal.dot(hit[1]),p.area])
x=np.array(rows);print('ATTR',[(v,int((x[:,1]==v).sum()))for v in np.unique(x[:,1])]);print('MISSED_OUTER_SHOULDER',x[(x[:,1]==0)&(x[:,5]>.7)&(x[:,4]>1.12)].shape);print('WRONG_INNER_SHOULDER',x[(x[:,1]==1)&(x[:,5]<-.7)&(x[:,4]>1.12)].shape)
print('BASISDIFF',max((v.co-o.data.shape_keys.key_blocks[0].data[v.index].co).length for v in o.data.vertices))
np.save('work/golf-tailoring/data/polo_faces.npy',x)
