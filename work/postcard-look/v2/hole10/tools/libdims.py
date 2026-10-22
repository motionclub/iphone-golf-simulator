import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy
import postcard_props_lib as PL
PL.ensure_library()
rep = PL.library_report()
for k in sorted(rep):
    if "BASALT" in k or "WALL" in k or "SEASTACK" in k or "AGAVE" in k or "SPIRE" in k or "SMOKE" in k or "SHRUB" in k or "TUFT" in k or "FLOWER" in k:
        ob = bpy.data.objects[k]
        mn, mx = PL.lib_bbox(k)
        print(k, rep[k], tuple(round(v,1) for v in (mx-mn)), "z", round(mn.z,1), round(mx.z,1))
