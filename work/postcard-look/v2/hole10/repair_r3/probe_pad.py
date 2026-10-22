import sys, json, math
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy, numpy as np
import hole10_look as HL
ob = bpy.data.objects["TEE_BOX"]
pts = HL.pad_outline(ob)
mw = np.array(ob.matrix_world)
z = np.array([(mw @ np.array([*v.co, 1.0]))[2] for v in ob.data.vertices])
print("TEE_BOX verts", len(ob.data.vertices), "polys", len(ob.data.polygons), "z min/max", z.min(), z.max())
print("outline n", len(pts)); print(np.round(pts, 2).tolist())
for n in bpy.data.objects.keys():
    if n.startswith(("MARKER_", "BALL", "TEE_MARK")):
        o = bpy.data.objects[n]; print(n, [round(c, 3) for c in o.matrix_world.translation])
mats = [m.name if m else None for m in ob.data.materials]
print("mats", mats)
# riser faces
nz = np.array([p.normal.z for p in ob.data.polygons]); print("up faces", int((nz > .5).sum()), "side faces", int((np.abs(nz) <= .5).sum()))
