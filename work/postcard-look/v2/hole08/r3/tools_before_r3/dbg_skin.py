import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, numpy as np
import postcard_lib as P
import postcard_look_lib as L
bpy.ops.wm.open_mainfile(filepath=REPO + "/work/postcard-look/v2/hole08/scratch/dev1/dev_hole_08.blend")
D = P.start.__globals__  # noqa
from mathutils import Vector
sk = L._bvh_of(L._skin_objs()); te = L._bvh_of([bpy.data.objects["TERRAIN_NEEDLE"]])
loops = L.terrain_top_loops(type("X", (), {"terrain_name": "TERRAIN_NEEDLE", "terrain": bpy.data.objects["TERRAIN_NEEDLE"], "play_z": 6.0, "__getattr__": lambda s, k: None})())
for li, (Pl, _) in enumerate(loops):
    Pc, s, Lp, N, _ = L._loop_columns(Pl, 1.0)
    for i in range(0, len(Pc), max(1, len(Pc)//4)):
        row = []
        for z in (5.9, 5.7, 5.4, 5.0, 4.5, 4.0, 3.5, 3.0, 2.0, 1.0, 0.3):
            o = Vector((Pc[i,0]+N[i,0]*8, Pc[i,1]+N[i,1]*8, z)); d = Vector((-N[i,0], -N[i,1], 0))
            h = sk.ray_cast(o, d, 14); t = te.ray_cast(o, d, 14)
            row.append(f"{8-h[3]:.2f}" if h[0] is not None else "  - ")
            row[-1] += "/" + (f"{8-t[3]:.2f}" if t[0] is not None else " - ")
        print(li, i, " ".join(row))
