import sys, math
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
YD = 0.9144
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
bpy.context.view_layer.update()
for n in ("TERRAIN_NEEDLE", "FAIRWAY", "FAIRWAY_FIRSTCUT", "GREEN", "GREEN_APRON", "TEE_BOX", "BUNKER_01"):
    ob = bpy.data.objects[n]; mw = np.array(ob.matrix_world)
    V = np.array([v.co[:] for v in ob.data.vertices]) @ mw[:3, :3].T + mw[:3, 3]
    up = [p for p in ob.data.polygons if p.normal.z > 0.9]
    zs = np.array([ob.data.vertices[i].co.z for p in up for i in p.vertices])
    print(n, "n", len(V), "x", round(V[:,0].min()/YD,1), round(V[:,0].max()/YD,1), "y", round(V[:,1].min()/YD,1), round(V[:,1].max()/YD,1), "up-face z", round(zs.min(),3), round(zs.max(),3), "mats", [m.name for m in ob.data.materials if m])
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
for (x, y) in [(0,0),(0,5),(0,-4),(-6,0),(0,-6),(0,8),(0,12),(-3,3),(-5,2)]:
    ok, loc, nrm, idx, ob, _m = sc.ray_cast(dg, Vector((x*YD, y*YD, 40.0)), Vector((0, 0, -1)), distance=80.0)
    print((x,y), ob.name if ok else None, round(loc.z,3) if ok else None)
