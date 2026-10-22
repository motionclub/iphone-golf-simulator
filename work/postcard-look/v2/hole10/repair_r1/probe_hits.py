import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
YD=0.9144
dg=bpy.context.evaluated_depsgraph_get()
for (x,y) in ((0,0),(0.5,2.0),(0,5.0),(0,5.6),(0,6.5),(3,3),(0,-2)):
    o=Vector((x*YD,y*YD,60)); hits=[]
    # use scene.ray_cast
    cur=o
    for k in range(12):
        ok,loc,nrm,idx,ob,mat=bpy.context.scene.ray_cast(dg,cur,Vector((0,0,-1)),distance=200)
        if not ok: break
        hits.append((ob.name,round(loc.z,3)))
        cur=loc-Vector((0,0,0.002))
    print((x,y),hits)
