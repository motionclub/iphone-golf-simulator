"""Vertical ray-cast height field of the old left foot (and right, mirrored check).  blender -b ... --python heightfield.py -- <blend> <out.npz>"""
import sys, numpy as np, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['Body_M']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
res = {}
for side, sgn in (('L', 1), ('R', -1)):
    # keep only faces of this foot/leg: all verts z<0.45 and sgn*x>0.05
    keep = [f for f in bm.faces if all((v.co.z < 0.45 and sgn * v.co.x > 0.03) for v in f.verts)]
    verts = [v.co.copy() for v in bm.verts]
    tris = []
    for f in keep:
        idx = [v.index for v in f.verts]
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
    xs = np.arange(0.10, 0.31, 0.002) if sgn > 0 else np.arange(-0.31, -0.09, 0.002)
    ys = np.arange(-0.24, 0.10, 0.002)
    H = np.full((len(xs), len(ys)), np.nan); Hlow = np.full((len(xs), len(ys)), np.nan)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            hit = bvh.ray_cast(Vector((x, y, 0.40)), Vector((0, 0, -1)), 1.0)
            if hit[0] is not None:
                H[i, j] = hit[0].z
                # lowest hit: cast upward from below
                hit2 = bvh.ray_cast(Vector((x, y, -0.05)), Vector((0, 0, 1)), 1.0)
                if hit2[0] is not None: Hlow[i, j] = hit2[0].z
    res['xs' + side] = xs; res['ys'] = ys; res['H' + side] = H; res['Hlow' + side] = Hlow
    print(side, 'height field done', np.isfinite(H).sum())
np.savez(out, **res)
