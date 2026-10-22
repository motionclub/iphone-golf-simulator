import bpy, sys, numpy as np
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_lib as P, hole09_look as HL
D = P.start("hole09_design", out_dir="/tmp/dbg9")
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole09/stage/hole_09.blend")
D = P._ST["D"]
import importlib
ob = bpy.data.objects["TERRAIN_SPLIT"]
D.terrain = ob
mid = HL.scrub_boundary_mid(D)
print(len(mid))
for x,y,l in mid: print(round(x/0.9144,1), round(y/0.9144,1), round(l,1))
print("spine", D.SCENERY["ridge"]["spine"])
