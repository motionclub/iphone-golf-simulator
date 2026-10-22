"""quickviews: open a blend and render the standard quick views. -- BLEND OUTDIR"""
import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import previews_lib as PV
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
out = os.path.abspath(args[1]); os.makedirs(out, exist_ok=True)

class DD: play_z = 6.0
PV.setup_scene()
D = DD()
names = args[2:] or ["top", "oblique", "tee", "app"]
bx = None
for n in names:
    if n == "top":
        # shore bbox from terrain
        t = bpy.data.objects["TERRAIN_NEEDLE"]
        import numpy as np
        co = np.array([v.co[:] for v in t.data.vertices]); lo, hi = co.min(0), co.max(0)
        cx, cy = (lo[0]+hi[0])/2, (lo[1]+hi[1])/2; span = max(hi[0]-lo[0], hi[1]-lo[1])*1.15
        c = PV.cam("CAM_P_TOP", (cx, cy, 800.0), (cx, cy, 0.0), ortho=span)
        PV.render(c, os.path.join(out, "q_top.png"), (700, 1700), 16)
    elif n == "oblique":
        PV.render(bpy.data.objects["CAM_HOLE_OVERVIEW"], os.path.join(out, "q_oblique.png"), (900, 1500), 20)
    elif n == "tee":
        c = PV.address_cam("CAM_P_TEE", (0, 0), (19, 178), D); PV.render(c, os.path.join(out, "q_tee.png"), (900, 1600), 24)
    elif n == "app":
        c = PV.address_cam("CAM_P_APP", (14, 200), (-6, 340), D); PV.render(c, os.path.join(out, "q_app.png"), (900, 1600), 24)
    elif n == "mid":
        c = PV.address_cam("CAM_P_MID", (19, 178), (-6, 340), D); PV.render(c, os.path.join(out, "q_mid.png"), (900, 1600), 24)
