import bpy, numpy as np
YD=0.9144
for n in ("TEE_BOX","FAIRWAY","FAIRWAY_FIRSTCUT","TERRAIN_CRATER","GREEN","GREEN_APRON","BUNKER_01","BUNKER_02"):
    ob=bpy.data.objects.get(n)
    if not ob: print(n,"missing"); continue
    me=ob.data
    co=np.array([ob.matrix_world@v.co for v in me.vertices])
    print(n, "verts",len(co),"polys",len(me.polygons),"z range",co[:,2].min().round(3),co[:,2].max().round(3),"x yd",(co[:,0].min()/YD).round(1),(co[:,0].max()/YD).round(1),"y yd",(co[:,1].min()/YD).round(1),(co[:,1].max()/YD).round(1), [m.name for m in me.materials], "loc",tuple(ob.location))
ob=bpy.data.objects["TEE_BOX"]
for v in ob.data.vertices[:60]:
    p=ob.matrix_world@v.co
    print(round(p.x/YD,2),round(p.y/YD,2),round(p.z,3))
