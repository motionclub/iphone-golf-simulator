"""Blender EEVEE preview of named Game cameras on a blend (NOT Game-view proof). usage: Blender -b --factory-startup --python prev.py -- BLEND LANDMARKS.json OUTDIR shot1 shot2 ... [--res WxH] [--samples N]
shot = a name in landmarks.json (kind address / landmark) or 'cam:x,y,z:lx,ly,lz:fov' in Blender metres."""
import sys, os, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
res = (900, 1600); samples = 24
if "--res" in a:
    i = a.index("--res"); w, h = a[i + 1].split("x"); res = (int(w), int(h)); del a[i:i + 2]
if "--samples" in a:
    i = a.index("--samples"); samples = int(a[i + 1]); del a[i:i + 2]
blend, lm, out = a[:3]; shots = a[3:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
cfg = json.load(open(lm))
LOOK = REPO + "/Unity/Assets/Resources/Course/Look/"
for im in bpy.data.images:
    if im.name.endswith(".png") and os.path.isfile(LOOK + im.name):
        im.filepath = LOOK + im.name
        im.reload()
PV.setup_scene()
class DD: play_z = 6.0
D = DD(); YD = P.YD
byname = {s["name"]: s for s in cfg["shots"]}
for n in shots:
    if n.startswith("cam:"):
        _, p, l, f = n.split(":")
        pos = tuple(float(v) for v in p.split(",")); look = tuple(float(v) for v in l.split(","))
        c = PV.cam("CAM_X", pos, look, float(f)); name = "x_" + p.replace(",", "_")
    else:
        sh = byname[n]; name = n
        if sh["kind"] == "address":
            c = PV.address_cam("CAM_F_" + n, tuple(sh["ball"]), tuple(sh["aim"]), D)
        else:
            pos, look = sh["pos"], sh["look"]
            c = PV.cam("CAM_F_" + n, (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
    PV.render(c, os.path.join(out, name + ".png"), res, samples)
    print("RENDERED", name)
