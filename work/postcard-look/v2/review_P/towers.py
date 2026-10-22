import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
for k in ["ROCK_WALL_BASALT_S","ROCK_WALL_BASALT_M","ROCK_WALL_BASALT_L","ROCK_BASALT_E","ROCK_BASALT_F","ROCK_BASALT_A"]:
    me=PL.library_object(k).data
    sizes=collections=None
    import collections
    cnt=collections.Counter(len(p.vertices) for p in me.polygons)
    tops=[p for p in me.polygons if p.normal.z>0.7]
    hex_tops=[p for p in tops if len(p.vertices)==6]
    zs=sorted({round(p.center.z,1) for p in tops})
    side=[p for p in me.polygons if abs(p.normal.z)<0.3]
    areas=sum(p.area for p in me.polygons if abs(p.normal.z)<0.3)/sum(p.area for p in me.polygons)
    co=np.array([v.co[:] for v in me.vertices]); 
    print(k,"polysizes",dict(cnt),"tops",len(tops),"hextops",len(hex_tops),"distinct top z",len(zs),"vert area frac %.2f"%areas,"bbox",np.round(co.max(0)-co.min(0),1))
