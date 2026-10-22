import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
sys.argv = [sys.argv[0], "--", "--scratch", R + "/work/postcard-look/v2/props/scratch"]
import bpy, numpy as np
from mathutils import Vector
import postcard_lib as P
import postcard_props_lib as PL
import postcard_props_smoke as S
S.fresh()
D = P.start("hole10_design", out_dir=R + "/work/postcard-look/v2/props/scratch/hole10")
P.build_terrain(D); P.build_play_surfaces(D)
P.build_water(D, 'WATER_LAVA', 'MAT_LAVA', shallow_material=None, foam_material=None, crest=False)
bvh, names = S.ground_bvh()
gs = PL.ground_sampler(D)
x, y = 63.467, 146.548
print("indep", S.ground_z(bvh, x, y), "PL", gs(np.array([x]), np.array([y])))
# all hits
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")):
        from mathutils.bvhtree import BVHTree
        b = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
        h = b.ray_cast(Vector((x, y, 60)), Vector((0, 0, -1)), 200)
        if h[0] is not None:
            print(o.name, h[0].z, "normal z", round(h[1].z, 3))
