import sys, os
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_lib as P, postcard_look_lib as L
D = P.start("hole09_design", out_dir="/tmp/x")  # only to get design; purge scene! so reload blend after
blend = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=blend)
D.terrain = bpy.data.objects["TERRAIN_SPLIT"]
P._ST["D"] = D
def bvh_of(obs):
    V, F = [], []
    for o in obs:
        W, ls, lt, lv, mi, pn = L._mesh_arrays(o)
        base = len(V); V += [tuple(p) for p in W.tolist()]
        F += [[base + int(v) for v in lv[a:a + n]] for a, n in zip(ls.tolist(), lt.tolist())]
    return BVHTree.FromPolygons(V, F)
sk = bvh_of([o for o in bpy.data.objects if o.name.startswith("ROCK_SKIN")])
tb = L._terrain_bvh(D)
loops = L.terrain_top_loops(D)
fails = []
tot = 0
for Pl, _ in loops:
    Pc, s, Lp, N, _ = L._loop_columns(Pl, 1.0)
    for i in range(0, len(Pc), 2):
        for z in (0.5, 1.5, 2.5, 3.5, 4.5, 5.3):
            o = Vector((Pc[i,0] + N[i,0]*12, Pc[i,1] + N[i,1]*12, z)); d = Vector((-N[i,0], -N[i,1], 0))
            hs = sk.ray_cast(o, d, 40); hw = tb.ray_cast(o, d, 40)
            if hw[0] is None: continue
            tot += 1
            if hs[0] is None or hs[3] > hw[3] + 1e-4:
                fails.append((round(s[i],1), z, round(Pc[i,0],1), round(Pc[i,1],1), round(hw[3]-12,2), None if hs[0] is None else round(hs[3]-12,2)))
print("tested", tot, "fails", len(fails))
for f in fails[:60]: print(f)
