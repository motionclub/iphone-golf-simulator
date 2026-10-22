import sys, os, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy, numpy as np
import postcard_lib as P
import postcard_look_lib as L
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
band = float(a[3])
bpy.ops.wm.open_mainfile(filepath=a[0])
PV.setup_scene()
oc = bpy.data.objects["ROCK_OUTCROP_A.000"]
me = oc.data
mw = np.array(oc.matrix_world)
names = [m.name.split(".")[0] if m else "" for m in me.materials]
i_rock, i_rough = names.index("LK_ROCK"), names.index("LK_ROUGH")
top = 5.2
n = 0
for p in me.polygons:
    zc = (mw @ np.append(np.array(p.center), 1.0))[2]
    nw = mw[:3, :3] @ np.array(p.normal); nw /= np.linalg.norm(nw)
    if p.material_index == i_rock and zc > top - band and nw[2] > 0.0:
        p.material_index = i_rough; n += 1
print("turf faces", n)
L.box_uv(oc, tile=None, object_space=True)
me.update()
cfg = json.load(open(a[1]))
sh = [s for s in cfg["shots"] if s["name"] == "hole08_arch"][0]
YD = P.YD
pos, look = sh["pos"], sh["look"]
c = PV.cam("CAM_F", (pos[0]*YD, pos[2]*YD, pos[1]*YD), (look[0]*YD, look[2]*YD, look[1]*YD), 60.0)
PV.render(c, a[2], (900, 1600), 32)
