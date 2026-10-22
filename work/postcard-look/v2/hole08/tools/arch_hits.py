"""arch_hits: which object / material the arch-frame rays hit in a region. usage: Blender -b --factory-startup --python arch_hits.py -- BLEND x0 x1 y0 y1"""
import sys, collections
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
import hole08_look as K
x0, x1, y0, y1 = [int(a) for a in args[1:5]]
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
cam, look = Vector(K.ARCH_CAM["pos"]), Vector(K.ARCH_CAM["look"])
cnt = collections.Counter()
for px in range(x0, x1 + 1, 6):
    for py in range(y0, y1 + 1, 6):
        d = K._cam_ray(cam, look, px, py, 900, 1600, K.ARCH_CAM["fov"])
        ok, loc, n, idx, ob, _m = sc.ray_cast(dg, cam, d, distance=900.0)
        if not ok or ob is None:
            cnt[("sky/water", "")] += 1
            continue
        me = ob.data
        mat = me.materials[me.polygons[idx].material_index].name.split(".")[0] if me.materials and me.materials[me.polygons[idx].material_index] is not None else ""
        cnt[(ob.name.split(".")[0], mat)] += 1
tot = sum(cnt.values())
for k, v in cnt.most_common(12):
    print(f"HITS {k} {v / tot:.1%}")
