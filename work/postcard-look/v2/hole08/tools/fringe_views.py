"""fringe_views: Blender EEVEE close views of the Needle fringe (NOT Game view) + a JSON of the fringe / tuft positions.
usage: Blender -b --factory-startup --python fringe_views.py -- BLEND OUTDIR [view ...]"""
import sys, os, math, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import numpy as np
from mathutils import Vector
import postcard_lib as P
import previews_lib as PV
args = sys.argv[sys.argv.index("--") + 1:]
blend, out = args[0], os.path.abspath(args[1])
names = args[2:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
YD = P.YD
PV.setup_scene()


def yd(x, d, z=0.0):
    return (x * YD, d * YD, z)


VIEWS = {
    # name: (loc, look, fov_v, res)   (metres, Blender frame x right, y down the hole, z up)
    "top_all": None,
    "tee_rim_low": (yd(-8.0, -6.0, 8.0), yd(-14.0, 22.0, 6.0), 55, (1200, 800)),
    "tee_rim_right": (yd(11.0, -6.0, 8.2), yd(14.5, 25.0, 6.0), 55, (1200, 800)),
    "mid_rim_left": (yd(-9.0, 160.0, 8.0), yd(-12.0, 195.0, 6.0), 55, (1200, 800)),
    "mid_rim_right": (yd(28.0, 160.0, 8.0), yd(28.0, 195.0, 6.0), 55, (1200, 800)),
    "green_rim": (yd(-14.0, 292.0, 8.5), yd(-16.0, 330.0, 6.0), 55, (1200, 800)),
    "green_apron": (yd(-6.0, 296.0, 7.5), yd(-6.0, 330.0, 6.2), 50, (1200, 800)),
}
sel = names or list(VIEWS)
for n in sel:
    v = VIEWS[n]
    if v is None:
        t = bpy.data.objects.get("TERRAIN_NEEDLE")
        co = np.array([vv.co[:] for vv in t.data.vertices]); lo, hi = co.min(0), co.max(0)
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.1
        c = PV.cam("CAM_F_TOP", (cx, cy, 800.0), (cx, cy, 0.0), ortho=span)
        PV.render(c, os.path.join(out, "top_all.png"), (700, 1700), 24)
        json.dump(dict(cx=cx, cy=cy, span=span, res=[700, 1700]), open(os.path.join(out, "top_all.json"), "w"))
        continue
    loc, look, fov, res = v
    c = PV.cam("CAM_F_" + n, loc, look, fov)
    PV.render(c, os.path.join(out, n + ".png"), res, 24)
# fringe positions for overlays
pts = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith("PLANT_TUFT") and "lk_fringe" in o.keys():
        pts.append((o.location.x, o.location.y, o.data.name))
json.dump(pts, open(os.path.join(out, "fringe_pts.json"), "w"))
print("FRINGE_PTS", len(pts))
