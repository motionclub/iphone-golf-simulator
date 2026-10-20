import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "work/postcard-look/review_ground/smoke_hole08/smoke_hole08.blend"))
GP = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")
def tree(obs):
    V, F = [], []
    for o in obs:
        mw = o.matrix_world
        b = len(V)
        V += [tuple(mw @ v.co) for v in o.data.vertices]
        F += [[b + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(V, F)
g = tree([o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(GP)])
paths = [o for o in bpy.data.objects if o.name.startswith("DRESS_PATH")]
p = tree(paths)
W = np.array([tuple(o.matrix_world @ v.co) for o in paths for v in o.data.vertices])
xs = np.arange(W[:, 0].min(), W[:, 0].max(), 0.1); ys = np.arange(W[:, 1].min(), W[:, 1].max(), 0.1)
dz = []
for x in xs:
    for y in ys:
        hp = p.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1)), 40)
        if hp[0] is None or hp[1].z < 0.5: continue
        hg = g.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1)), 40)
        if hg[0] is None: continue
        dz.append(hp[0].z - hg[0].z)
dz = np.array(dz)
D = 0.12 / 1.0936
print(f"PATH over collider: {len(dz)} samples at 0.1 m ({len(dz)*0.01:.0f} m2); dz median {np.median(dz):.3f} m, max {dz.max():.3f}; "
      f"ball diameter {D:.3f} m: > half the ball hidden (dz > {D/2:.3f}) on {100*(dz > D/2).mean():.1f}% of the path area, fully hidden on {100*(dz > D).mean():.1f}%")
