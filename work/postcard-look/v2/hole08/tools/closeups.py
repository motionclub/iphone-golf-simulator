"""closeups: open a staged/dev blend and render named camera views. -- BLEND OUTDIR view1 view2 ...   views defined in VIEWS (Blender metres)."""
import sys, os, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import postcard_lib as P
import previews_lib as PV
args = sys.argv[sys.argv.index("--") + 1:]
blend, out = args[0], os.path.abspath(args[1])
names = args[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
YD = P.YD
ac = P.m(-26.7, 317.0)
VIEWS = {
    # name: (loc, look, fov_v, res)
    "arch_a": ((-4.0, 281.0, 9.0), (ac[0], ac[1], 9.0), 50, (1000, 1000)),
    "arch_b": ((-8.0, 270.0, 12.0), (ac[0], ac[1], 8.0), 50, (1000, 1000)),
    "arch_top": ((ac[0], ac[1], 40.0), (ac[0], ac[1], 5.0), 40, (1000, 1000)),
    "arch_side": ((ac[0] - 25, ac[1], 9.0), (ac[0], ac[1], 8.0), 50, (1000, 1000)),
    "fall_a": ((8.0, 240.0, 6.0), (8.0, 273.0, 3.0), 45, (1000, 1000)),
    "aerial1": ((70.0, -45.0, 62.0), (-5.0, 215.0, 3.0), 36, (1600, 900)),
    "aerial2": ((55.0, 330.0, 38.0), (-8.0, 150.0, 2.0), 40, (1600, 900)),
    "aerial3": ((-60.0, 200.0, 40.0), (8.0, 300.0, 2.0), 40, (1600, 900)),
    "tee_zoom_arch": ((0.0, -4.1, 8.4), (-24.4, 290.0, 9.0), 8, (1000, 1000)),
    "tee_cliff": ((20.0, 20.0, 14.0), (8.0, 60.0, 2.0), 50, (1200, 800)),
}
PV.setup_scene()
import json
LM = os.path.join(os.path.dirname(blend), "landmarks_check.json")
if os.path.isfile(LM):
    c_ = json.load(open(LM))["arch_camera_blender_m"]
    VIEWS["arch_landmark"] = (tuple(c_["pos"]), tuple(c_["look"]), c_["fov_v"], (900, 1600))
for n in names:
    loc, look, fov, res = VIEWS[n]
    c = PV.cam("CAM_C_" + n, loc, look, fov)
    PV.render(c, os.path.join(out, n + ".png"), res, 24)
