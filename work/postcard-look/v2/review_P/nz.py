import sys, os, math, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
hole=os.environ["HOLE"]
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
rep=[]
PL.swap_legacy_rocks(None, basalt=(hole=="10"), seed=int(os.environ.get("SEED","1")), report=rep)
for r in rep:
    if r["n"][2]>1 or r["instances"]>1: print("HOLE",hole,r["legacy"],"box",r["box"],"kind",r["kind"],"n",r["n"],"scale",r["scale"],"err",r["err"])
