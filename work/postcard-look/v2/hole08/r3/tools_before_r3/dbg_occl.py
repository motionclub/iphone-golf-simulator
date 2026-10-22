import sys, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import postcard_lib as P
bpy.ops.wm.open_mainfile(filepath=REPO + "/work/postcard-look/v2/hole08/scratch/seed5/hole_08.blend")
import hole08_look as K
YD = P.YD
cam = Vector((0.0, -4.5 * YD, 6.24 + 2.4 * YD))
arch = [o for o in bpy.data.objects if o.name.startswith("DRESS_ARCH")][0]
AV = K.world_verts([arch]); AV = AV[AV[:, 2] > 6.2]
print("arch verts", len(AV), "bbox", AV.min(0), AV.max(0))
allobs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("ROCK_", "DRESS_", "PLANT_")) and not o.name.startswith(("ROCK_SKIN","DRESS_ARCH","DRESS_PATH")) and o.visible_get() is not None and not any(c.name=="ASSET_LIBRARY" for c in o.users_collection)]
print(len(allobs))
bv = K.bvh_of_objects(allobs)
from collections import Counter
cnt = Counter()
tot = 0
idxs = np.linspace(0, len(AV) - 1, 150).astype(int)
for i in idxs:
    x, y, z = AV[i]; d = Vector((x, y, z)) - cam
    h = bv.ray_cast(cam, d.normalized(), d.length - 0.05)
    tot += 1
    if h[0] is not None: cnt["hit"] += 1
print("hidden", cnt, "of", tot)
# which object blocks: per-object bvh
for o in allobs:
    b1 = K.bvh_of_objects([o]); n = 0
    for i in idxs:
        x, y, z = AV[i]; d = Vector((x, y, z)) - cam
        if b1.ray_cast(cam, d.normalized(), d.length - 0.05)[0] is not None: n += 1
    if n: print(o.name, n)
