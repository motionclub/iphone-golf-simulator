"""experiment: dev build with the tee box left as the library made it (LK_GREEN). Blender -b --factory-startup --python tee_variant.py -- OUTDIR"""
import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
import postcard_lib as P
import hole08_build as B
import hole08_look as K
K.TEE_BOX_CROSS_MOWN = False
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1]); os.makedirs(OUT, exist_ok=True)
D = P.start("hole08_design", out_dir=OUT)
P.build_terrain(D); B.weld_terrain(D); B.fix_overhangs(D); B.split_deep_band(D)
P.build_play_surfaces(D); P.build_water(D); B.tidy_all_flat(D); B.trim_lip_off_green(D); P.build_gameplay(D)
P.build_cameras_and_light(D, overview_rot_deg=B.OVERVIEW_ROT)
info = K.look_pass(D)
print("TEE_BOX mats", [m.name for m in bpy.data.objects["TEE_BOX"].data.materials])
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "dev_hole_08.blend"))
