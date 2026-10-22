import sys, os, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy, numpy as np
import postcard_lib as P
import postcard_look_lib as L
import postcard_props_lib as PL
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
PV.setup_scene()
class DD: play_z = 6.0; number = 8
D = DD()
oc = bpy.data.objects["ROCK_OUTCROP_A.000"]
me = oc.data
print("outcrop mesh", me.name, len(me.polygons), [m.name if m else None for m in me.materials], dict(me.items()) if hasattr(me,'items') else None)
for k in me.keys(): print("  prop", k, me[k])
mw = np.array(oc.matrix_world)
print("scale", np.linalg.svd(mw[:3,:3], compute_uv=False))
hi = bpy.data.materials["LK_CLIFF"]; lo = bpy.data.materials["LK_CLIFF_DARK"]
names = [m.name.split(".")[0] if m else "" for m in me.materials]
for m in (hi, lo):
    if m.name not in [x.name for x in me.materials if x]:
        me.materials.append(m)
names = [m.name.split(".")[0] if m else "" for m in me.materials]
i_hi, i_lo, i_rock = names.index("LK_CLIFF"), names.index("LK_CLIFF_DARK"), names.index("LK_ROCK")
n = 0
for p in me.polygons:
    if p.material_index == i_rock:
        zc = (mw @ np.append(np.array(p.center), 1.0))[2]
        p.material_index = i_lo if zc < 1.2 else i_hi
        n += 1
print("re-materialled", n)
L.box_uv(oc, tile=None, object_space=True)
me.update()
cfg = json.load(open(a[1]))
sh = [s for s in cfg["shots"] if s["name"] == "hole08_arch"][0]
YD = P.YD
pos, look = sh["pos"], sh["look"]
c = PV.cam("CAM_F", (pos[0]*YD, pos[2]*YD, pos[1]*YD), (look[0]*YD, look[2]*YD, look[1]*YD), 60.0)
PV.render(c, a[2], (900, 1600), 32)
