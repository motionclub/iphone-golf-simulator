"""Scan a horizontal pixel line of the hole08_arch Game camera and list the faces hit (object, face idx, material, normal, uv-v range).
usage: Blender -b --factory-startup --python strand_probe.py -- BLEND y x0 x1 [step]"""
import sys, os, json, math, collections
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
blend = a[0]; y = float(a[1]); x0 = float(a[2]); x1 = float(a[3]); step = float(a[4]) if len(a) > 4 else 0.1
bpy.ops.wm.open_mainfile(filepath=blend)
cfg = json.load(open(REPO + "/work/postcard-look/v2/hole08/landmarks.json"))
sh = {s["name"]: s for s in cfg["shots"]}["hole08_arch"]
YD = P.YD
pos, look = sh["pos"], sh["look"]
c = PV.cam("CAM_P", (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
sc = bpy.context.scene
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
W, H = 900, 1600
th = math.tan(c.data.angle_y / 2); tw = th * W / H
mw = c.matrix_world.copy(); org = mw.translation.copy()
last = None
x = x0
while x <= x1:
    ndx = ((x / W) * 2 - 1) * tw; ndy = (1 - (y / H) * 2) * th
    d = (mw.to_3x3() @ Vector((ndx, ndy, -1.0))).normalized()
    ok, loc, nrm, idx, ob, _m = sc.ray_cast(dg, org, d, distance=6000)
    key = (ob.name, idx) if ok else None
    if key != last:
        if ok:
            me = ob.data; poly = me.polygons[idx]
            mat = ob.material_slots[poly.material_index].name if poly.material_index < len(ob.material_slots) else "?"
            uvl = me.uv_layers.active
            uvs = [tuple(round(v, 3) for v in uvl.data[li].uv) for li in poly.loop_indices] if uvl else []
            print("x=%.2f %s face %d mat %s nrm (%.2f %.2f %.2f) area %.4f dist %.2f verts %d uv %s" % (x, ob.name, idx, mat, nrm.x, nrm.y, nrm.z, poly.area, (loc - org).length, len(poly.vertices), uvs[:4]))
        else:
            print("x=%.2f sky" % x)
        last = key
    x += step
