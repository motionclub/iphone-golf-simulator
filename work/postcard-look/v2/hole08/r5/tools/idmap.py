"""ID map of the arch / tee Game cameras: which object / material does each pixel see (Blender raycasts, coarse). usage: Blender -b --python idmap.py -- BLEND OUT_PREFIX"""
import sys, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import postcard_lib as P
blend, outp = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend)
YD = P.YD
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene
def shoot(name, loc, look, W=90, H=160, fov=60.0):
    loc, look = Vector(loc), Vector(look)
    fwd = (look - loc).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd).normalized()
    th = math.tan(math.radians(fov / 2))
    names = {}
    grid = []
    for j in range(H):
        row = []
        for i in range(W):
            x = ((i + 0.5) / W * 2 - 1) * th * W / H
            y = (1 - (j + 0.5) / H * 2) * th
            d = (fwd + right * x + up * y).normalized()
            ok, p, n, idx, ob, mw = sc.ray_cast(dg, loc, d, distance=4000)
            if ok:
                mi = ob.data.polygons[idx].material_index if ob.type == 'MESH' else 0
                mat = ob.data.materials[mi].name if ob.data.materials and mi < len(ob.data.materials) and ob.data.materials[mi] else "-"
                key = f"{ob.name}|{mat}"
            else:
                key = "sky"
            row.append(key)
        grid.append(row)
    json.dump(grid, open(f"{outp}_{name}.json", "w"))
    return grid
shoot("arch", (-9.0, 276.0, 9.48), (-26.243, 289.865, 9.8))
g = None
# tee: CameraRig.FrameAddress
import previews_lib as PV
class DD: play_z = 6.0
bx, by = P.m(0, 0); ax, ay = P.m(19, 178)
z = PV.ground_z(bx, by, 11.0)
d = Vector((ax - bx, ay - by, 0)).normalized()
ball = Vector((bx, by, z)); loc = ball - d * 4.5 * YD + Vector((0, 0, 2.4 * YD)); look = ball + d * 1.5 * YD
print("TEE CAM", tuple(loc), tuple(look), "ground z", z)
shoot("tee", loc, look)
