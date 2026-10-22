"""What does the Game camera see at pixels (x0..x1, y0..y1) of a 900x1600 frame? usage: Blender -b --factory-startup --python pixel_probe.py -- BLEND LANDMARKS.json SHOT x0 y0 x1 y1 [step]
Casts a dense grid of rays through the pixel rectangle (y down from the top) and counts first hits per object."""
import sys, os, json, math, collections
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
blend, lm, shot = a[:3]
x0, y0, x1, y1 = [float(v) for v in a[3:7]]
step = float(a[7]) if len(a) > 7 else 0.25
bpy.ops.wm.open_mainfile(filepath=blend)
cfg = json.load(open(lm))
sh = {s["name"]: s for s in cfg["shots"]}[shot]
YD = P.YD
class DD: play_z = 6.0
D = DD()
if sh["kind"] == "address":
    c = PV.address_cam("CAM_P", tuple(sh["ball"]), tuple(sh["aim"]), D)
else:
    pos, look = sh["pos"], sh["look"]
    c = PV.cam("CAM_P", (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
sc = bpy.context.scene
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
W, H = 900, 1600
fy = c.data.angle_y
th = math.tan(fy / 2)
tw = th * W / H
mw = c.matrix_world.copy()
org = mw.translation.copy()
print('CAM', tuple(round(v,2) for v in org), 'fwd', tuple(round(v,3) for v in (mw.to_3x3() @ Vector((0,0,-1)))), 'fov', math.degrees(fy))
cnt = collections.Counter(); ex = {}
y = y0
while y <= y1:
    x = x0
    while x <= x1:
        ndx = ((x / W) * 2 - 1) * tw
        ndy = (1 - (y / H) * 2) * th
        d = (mw.to_3x3() @ Vector((ndx, ndy, -1.0))).normalized()
        ok, loc, nrm, idx, ob, _m = sc.ray_cast(dg, org, d, distance=6000)
        if ok:
            cnt[ob.name] += 1
            if 'DUMPOBJ' in os.environ and ob.name.startswith(os.environ['DUMPOBJ']): print('DUMP', ob.name, x, y, round((loc-org).length,2))
            if ob.name not in ex:
                ex[ob.name] = (round((loc - org).length, 2), tuple(round(v, 2) for v in loc), idx)
        else:
            cnt["<sky>"] += 1
        x += step
    y += step
for k, v in cnt.most_common(30):
    print("HIT", k, v, ex.get(k))
