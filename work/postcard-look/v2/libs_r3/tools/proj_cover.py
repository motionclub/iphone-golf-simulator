"""Which polygons of the .blend project onto a screen rectangle of the hole08_arch Game camera (exact projection, sub-pixel safe, front or back faces)?
usage: Blender -b --factory-startup --python proj_cover.py -- BLEND x0 y0 x1 y1 [shot]"""
import sys, os, json, math, collections
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
blend = a[0]; x0, y0, x1, y1 = [float(v) for v in a[1:5]]
shot = a[5] if len(a) > 5 else "hole08_arch"
if blend.endswith(".fbx"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=blend)
else:
    bpy.ops.wm.open_mainfile(filepath=blend)
cfg = json.load(open(REPO + "/work/postcard-look/v2/hole08/landmarks.json"))
sh = {s["name"]: s for s in cfg["shots"]}[shot]
YD = P.YD
pos, look = sh["pos"], sh["look"]
c = PV.cam("CAM_P", (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
W, H = 900, 1600
th = math.tan(c.data.angle_y / 2); tw = th * W / H
inv = c.matrix_world.inverted()
rx = (x0, x1); ry = (y0, y1)
hits = collections.Counter(); ex = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    M = inv @ ob.matrix_world
    cam = [M @ v.co for v in me.vertices]
    NEAR = 0.05
    for p in me.polygons:
        poly = [cam[i] for i in p.vertices]
        # clip against the near plane z = -NEAR (camera looks down -Z)
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            ain, bin_ = a.z < -NEAR, b.z < -NEAR
            if ain:
                out.append(a)
            if ain != bin_:
                t = (-NEAR - a.z) / (b.z - a.z)
                out.append(a + (b - a) * t)
        if len(out) < 3:
            continue
        ps = [((q.x / (-q.z) / tw * 0.5 + 0.5) * W, (0.5 - q.y / (-q.z) / th * 0.5) * H, -q.z) for q in out]
        xs = [q[0] for q in ps]; ys = [q[1] for q in ps]
        if max(xs) < rx[0] or min(xs) > rx[1] or max(ys) < ry[0] or min(ys) > ry[1]:
            continue
        w = max(xs) - min(xs); h = max(ys) - min(ys)
        key = (ob.name, p.material_index)
        hits[key] += 1
        if key not in ex or w * h < ex[key][0]:
            ex[key] = (w * h, p.index, round(w, 2), round(h, 2), round(min(q[2] for q in ps), 1), len(p.vertices))
    ev.to_mesh_clear()
for k, v in hits.most_common(40):
    print("COVER", k, v, "smallest-bbox poly (area,idx,w,h,depth,nv)", ex[k])
