"""Blender EEVEE previews of the staged hole 8 from the Game cameras (NOT Game-view proof). usage: Blender -b --factory-startup --python final_previews.py -- STAGED.blend OUT_DIR LANDMARKS.json"""
import sys, os, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import postcard_lib as P
import previews_lib as PV
blend, out, lm = sys.argv[sys.argv.index("--") + 1:][:3]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
cfg = json.load(open(lm))
PV.setup_scene()
class DD: play_z = 6.0
D = DD()
YD = P.YD
for sh in cfg["shots"]:
    n = sh["name"]
    if sh["kind"] == "address":
        # round 5: the CameraRig.FrameAddress geometry with the ball resting on the real ground (TEE_BOX top at the tee, the 6.14 m fairway plate elsewhere); the old address_cam found 6.14
        # at the tee (a ray through a mesh vertex slipped under the tee box) and put the preview camera 10 cm too low
        import hole08_look as K
        cam_, look_, _b = K.tee_cam(ball=tuple(float(v) for v in sh["ball"]), aim=tuple(float(v) for v in sh["aim"]), ground_z=None if tuple(sh["ball"]) == (0, 0) else 6.14)
        c = PV.cam("CAM_F_" + n, cam_, look_, 60.0)
    else:
        pos, look = sh["pos"], sh["look"]
        # Unity world yards (x, y up, z down the hole) -> Blender metres (x, y = z_unity, z = y_unity)
        c = PV.cam("CAM_F_" + n, (pos[0] * YD, pos[2] * YD, pos[1] * YD), (look[0] * YD, look[2] * YD, look[1] * YD), sh.get("fov", 60.0))
    PV.render(c, os.path.join(out, n + "_blender.png"), (900, 1600), 32)
# aerials (like the stills) and the library overview
VIEWS = {
    "aerial_all": ((70.0, -45.0, 62.0), (-5.0, 215.0, 3.0), 36),
    "aerial_green": ((-60.0, 200.0, 40.0), (8.0, 300.0, 2.0), 40),
    "aerial_mid": ((55.0, 330.0, 38.0), (-8.0, 150.0, 2.0), 40),
    "aerial_tee": ((20.0, 20.0, 14.0), (8.0, 60.0, 2.0), 50),
}
for n, (loc, look, fov) in VIEWS.items():
    c = PV.cam("CAM_F_" + n, loc, look, fov)
    PV.render(c, os.path.join(out, n + "_blender.png"), (1600, 900) if n != "aerial_tee" else (1200, 800), 32)
PV.render(bpy.data.objects["CAM_HOLE_OVERVIEW"], os.path.join(out, "overview_blender.png"), (900, 1800), 24)
