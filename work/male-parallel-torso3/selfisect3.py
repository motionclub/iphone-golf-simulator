"""Self-intersection count of Body_M (BVH overlap, pairs sharing a vertex excluded), total and inside the torso zone.
blender -b --factory-startup --python selfisect3.py -- <blend> <out.json>"""
import sys, json
import numpy as np, bpy, bmesh
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; path, outj = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=path)
ob = bpy.data.objects['Body_M']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
tris = [tuple(v.index for v in f.verts) for f in bm.faces]; V = np.array([v.co[:] for v in bm.verts])
tree = BVHTree.FromBMesh(bm, epsilon=0.0); pairs = tree.overlap(tree)
bad = [(i, j) for i, j in pairs if i < j and not (set(tris[i]) & set(tris[j]))]
def in_zone(t):
    c = V[list(t)].mean(0); return 0.77 <= c[2] < 1.40 and abs(c[0]) <= 0.28
zone_bad = [(i, j) for i, j in bad if in_zone(tris[i]) or in_zone(tris[j])]
res = dict(blend=path, tris=len(tris), overlapping_pairs_nonadjacent=len(bad), overlapping_pairs_touching_torso_zone=len(zone_bad))
json.dump(res, open(outj, 'w'), indent=1); print('SELFISECT', json.dumps(res))
