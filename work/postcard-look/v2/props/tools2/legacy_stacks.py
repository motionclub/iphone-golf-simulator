import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
for hole in ("08","09"):
    bpy.ops.wm.open_mainfile(filepath=f"{R}/work/postcard-look/baseline/blender/hole_{hole}.blend")
    for o in PL.legacy_rocks():
        me=o.data
        co=np.array([list(o.matrix_world@v.co) for v in me.vertices])
        sz=co.max(0)-co.min(0)
        if o.name.startswith("ROCK_STACK") or sz[2]>7.0 or o.name.startswith("CLIFF_ROCK"):
            if hole=="09" and not o.name.startswith("ROCK_STACK") and sz[2]<7: continue
            print(hole,o.name,me.name,len(me.vertices),"size",np.round(sz,1),"z",round(co.min(0)[2],1),round(co.max(0)[2],1),"xy",np.round((co.min(0)+co.max(0))[:2]/2,1))
