"""Cross-section x-extents (side walls) of the old left foot via horizontal ray casts.  blender -b ... --python sections.py -- <blend> <out.npz>"""
import sys, numpy as np, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['Body_M']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
keep = [f for f in bm.faces if all((v.co.z < 0.45 and v.co.x > 0.03) for v in f.verts)]
verts = [v.co.copy() for v in bm.verts]
tris = []
for f in keep:
    idx = [v.index for v in f.verts]
    for k in range(1, len(idx) - 1):
        tris.append((idx[0], idx[k], idx[k + 1]))
bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
ys = np.arange(-0.2275, 0.095, 0.0025)
zs = np.arange(0.0030, 0.200, 0.002)
XMIN = np.full((len(ys), len(zs)), np.nan); XMAX = np.full_like(XMIN, np.nan)
for a, y in enumerate(ys):
    for b, z in enumerate(zs):
        # from outside lateral toward medial (hit nearest from +x side) and from medial side
        h1 = bvh.ray_cast(Vector((0.40, y, z)), Vector((-1, 0, 0)), 1.0)
        if h1[0] is None: continue
        XMAX[a, b] = h1[0].x
        h2 = bvh.ray_cast(Vector((0.07, y, z)), Vector((1, 0, 0)), 1.0)    # from the medial/inner side outward
        if h2[0] is not None: XMIN[a, b] = h2[0].x
np.savez(out, ys=ys, zs=zs, XMIN=XMIN, XMAX=XMAX)
print('done')
