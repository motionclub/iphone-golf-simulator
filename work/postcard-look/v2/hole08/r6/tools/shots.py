"""Blender EEVEE previews of chosen shots from the Game cameras (NOT Game view). -- BLEND OUT_DIR LANDMARKS.json [shot names...]"""
import sys, os, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import previews_lib as PV
a = sys.argv[sys.argv.index("--") + 1:]
blend, out, lm = a[:3]
want = a[3:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
cfg = json.load(open(lm))
PV.setup_scene()
YD = P.YD
import hole08_look as K
for sh in cfg["shots"]:
    n = sh["name"]
    if want and n not in want:
        continue
    if sh["kind"] == "address":
        cam_, look_, _b = K.tee_cam(ball=tuple(float(v) for v in sh["ball"]), aim=tuple(float(v) for v in sh["aim"]), ground_z=None if tuple(sh["ball"]) == (0, 0) else 6.14)
        c = PV.cam("CAM_F_" + n, cam_, look_, 60.0)
    else:
        pos, look = sh["pos"], sh["look"]
        c = PV.cam("CAM_F_" + n, (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
    PV.render(c, os.path.join(out, n + "_blender.png"), (900, 1600), 32)
print("done")
