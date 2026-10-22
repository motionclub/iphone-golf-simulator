import sys, os, math
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
import numpy as np
import bpy
from mathutils import Vector
import postcard_props_smoke as S
import postcard_props_lib as PL
import postcard_lib as P
out = sys.argv[sys.argv.index("--") + 1]
YD = P.YD
# --- shrubs with / without tufts
S.fresh(); PL.write_plants_atlas()
S.setup_scene((1500, 620))
g = S.ref_mat("REF_GROUND", (126, 140, 60), rough=0.95)
S.ref_plane("REF_G", 0, 0, 0.0, 60, 60, g.name)
cam = S.camera("CAM_S", Vector((0.0, -9.5, 2.2)), Vector((0.0, 0.0, 0.5)), lens=32)
shr = []
for i, k in enumerate(("PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C")):
    shr.append(PL.place(None, k, (-5.0 + i * 2.6, 0.0, 0.0), 0.3 + i, 1.2, allow_low=True))
    shr.append(PL.place(None, k, (1.4 + i * 2.6, 0.0, 0.0), 0.3 + i, 1.2, allow_low=True))
# the right three get tufts: tuftify with a fake D-less call: D only used for place parent -> pass None
r = PL.tuftify_shrubs(None, [o for o in shr if o.location.x > 0], seed=3)
S.title(cam, "shrubs A B C: plain (left)  vs  tuftify_shrubs (right, +%d tufts, %d tris)" % (len(r["objs"]), r["tris"]), size=0.04)
sc = bpy.context.scene; sc.camera = cam
sc.render.filepath = os.path.join(out, "shrubs_tuftified.png")
bpy.ops.render.render(write_still=True)
print("wrote", sc.render.filepath)
# --- sea stack crowns with / without tufts, at the tee distance and close
S.fresh(); PL.write_plants_atlas()
S.setup_scene((1500, 700))
water = S.ref_mat("REF_WATER", (36, 104, 168), rough=0.15)
S.ref_plane("REF_WATER_S", 0, 0, 0.0, 800, 800, water.name)
st = []
for i, k in enumerate(("ROCK_SEASTACK_A", "ROCK_SEASTACK_B", "ROCK_SEASTACK_D", "ROCK_SEASTACK_A", "ROCK_SEASTACK_B", "ROCK_SEASTACK_D")):
    st.append(PL.place(None, k, (-30 + i * 12.0, 0.0, 0.0), 0.4 + i, 1.0))
PL.tuftify_crowns(None, st[3:], seed=2)
cam = S.camera("CAM_C", Vector((0.0, -70.0, 14.0)), Vector((0.0, 0.0, 11.0)), lens=34)
S.title(cam, "sea stacks A B D: plain crowns (left 3) vs tuftify_crowns (right 3)", size=0.04)
sc = bpy.context.scene; sc.camera = cam
sc.render.filepath = os.path.join(out, "crowns_tuftified.png")
bpy.ops.render.render(write_still=True)
print("wrote", sc.render.filepath)
