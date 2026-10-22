import sys, os, hashlib
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
bpy.ops.wm.open_mainfile(filepath=R + "/work/postcard-look/baseline/blender/hole_09.blend")
out=PL.swap_legacy_rocks(None,seed=4); bpy.context.view_layer.update()
h=hashlib.md5()
for o in sorted(out,key=lambda o:o.name): h.update(o.name.encode()); h.update(np.round(np.array(o.matrix_world),4).tobytes())
print("HASH",h.hexdigest(),len(out))
