"""Blender EEVEE previews (NOT Game view): tee (CameraRig geometry), arch landmark, approach. usage: Blender -b --factory-startup --python prev.py -- BLEND OUT_DIR [tee arch approach pathball ...] """
import sys, os, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import postcard_lib as P
import previews_lib as PV
import hole08_look as K
a = sys.argv[sys.argv.index("--") + 1:]
blend, out = a[0], a[1]; which = a[2:] or ["tee", "arch", "approach"]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
PV.setup_scene()
YD = P.YD
tag = os.path.basename(os.path.dirname(blend)) or "x"
if "tee" in which:
    cam, look, b = K.tee_cam()
    PV.render(PV.cam("CAM_tee", cam, look, 60.0), os.path.join(out, f"tee_{tag}.png"), (900, 1600), 32)
if "arch" in which:
    PV.render(PV.cam("CAM_arch", (-9.0, 276.0, 9.48), (-26.243, 289.865, 9.8), 60.0), os.path.join(out, f"arch_{tag}.png"), (900, 1600), 32)
if "approach" in which:
    cam, look, b = K.tee_cam(ball=(19.0, 178.0), aim=(-6.0, 340.0), ground_z=6.14)
    PV.render(PV.cam("CAM_app", cam, look, 60.0), os.path.join(out, f"approach_{tag}.png"), (900, 1600), 32)
if "pathball" in which:
    bx, by = K.PATHBALL_YD
    cam, look, b = K.tee_cam(ball=(bx, by), aim=(19.0, 178.0), ground_z=6.14)
    PV.render(PV.cam("CAM_pb", cam, look, 60.0), os.path.join(out, f"pathball_{tag}.png"), (900, 1600), 32)
