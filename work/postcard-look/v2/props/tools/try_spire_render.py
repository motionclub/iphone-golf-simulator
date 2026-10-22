import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
sys.argv = [sys.argv[0], "--", "--scratch", R + "/work/postcard-look/v2/props/scratch"]
import bpy, numpy as np
from mathutils import Vector
import postcard_props_smoke as S
import postcard_props_lib as PL
S.fresh()
S.setup_scene((1200, 560))
water = S.ref_mat("REF_WATER", (36, 104, 168), rough=0.15)
S.ref_plane("REF_WATER_B", 0, 0, 0.0, 400, 400, water.name)
kinds = ["ROCK_SEASTACK_A", "ROCK_SEASTACK_B", "ROCK_SEASTACK_C", "ROCK_SPIRE_A"]
for i, k in enumerate(kinds):
    PL.place(None, k, (i * 14 - 21, 0, 0), 0.3 + i)
S.ref_figure(-25, -8, 0.0)
az = float(os.environ.get("AZ", "0"))
cam = S.camera("CAM", Vector((0, -60, 12)), Vector((0, 0, 9)), lens=34)
bpy.context.scene.camera = cam
out = R + "/work/postcard-look/v2/props/scratch/spire_%s.png" % os.environ.get("TAG", "a")
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.context.scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("wrote", out)
