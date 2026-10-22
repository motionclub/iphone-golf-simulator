import bpy, numpy as np, sys
from mathutils import Vector
for n in ("TERRAIN_NEEDLE","FAIRWAY","FAIRWAY_FIRSTCUT","GREEN","GREEN_APRON","TEE_BOX","BUNKER_01","BUNKER_01_LIP","DRESS_PATH_01","DRESS_PATH_02"):
    ob=bpy.data.objects.get(n)
    if ob is None: print(n,"missing"); continue
    me=ob.data
    co=np.array([v.co[:] for v in me.vertices])
    print(n, len(me.vertices), len(me.polygons), "z %.3f..%.3f"%(co[:,2].min(),co[:,2].max()), "x %.2f..%.2f y %.2f..%.2f"%(co[:,0].min(),co[:,0].max(),co[:,1].min(),co[:,1].max()), [m.name if m else None for m in me.materials])
