"""Contact sheet of the library tufts (EEVEE, the real Look/ textures; Blender render, NOT Game view).
usage: blender -b --factory-startup --python tuft_sheet.py -- OUT.png [--kinds A,B,..]"""
import sys, os, math
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
sys.argv_backup = list(sys.argv)
import bpy
from mathutils import Vector
import postcard_props_smoke as S
import postcard_props_lib as PL
ARGS = sys.argv[sys.argv.index("--") + 1:]
out = ARGS[0]
S.fresh()
PL.write_plants_atlas()
S.setup_scene((1500, 700))
ground = S.ref_mat("REF_GROUND", (126, 140, 60), rough=0.95)
S.ref_plane("REF_G", 0, 0, 0.0, 60, 60, ground.name)
kinds = ["PLANT_TUFT_A", "PLANT_TUFT_B", "PLANT_TUFT_C", "PLANT_TUFT_D", "PLANT_TUFT_E", "PLANT_TUFT_F", "PLANT_TUFT_S", "PLANT_TUFT_T"]
cam = S.camera("CAM_T", Vector((0.0, -5.2, 1.05)), Vector((0.0, 0.0, 0.3)), lens=34)
objs, xe = S.row(kinds, -2.9, 0.0, 0.18, z=0.0, yaw=0.4, scale=1.0, cam=cam, lab=0.0)
for i, k in enumerate(kinds):
    PL.place(None, k, (-2.7 + i * 0.7, -1.2, 0.0), 1.1, 1.0, allow_low=True)
S.title(cam, "tufts A B C (old) | D E F tall | S T filler  (front row: yaw 0.4, second row: yaw 1.1)", size=0.035)
sc = bpy.context.scene
sc.camera = cam
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("wrote", out)
