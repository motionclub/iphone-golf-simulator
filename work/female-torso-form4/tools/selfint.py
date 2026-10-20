"""blender -b <blend> --python selfint.py -- out.json [zone.npz]
Exact triangle-triangle self-intersection audit of Body_F (mathutils BVHTree.overlap performs the exact isect test and skips edge-sharing pairs;
pairs that share one vertex are only reported when they really cross).  Reports the whole-mesh count and the count of pairs that touch the torso zone
(at least one triangle with a vertex in the zone mask) - the number that matters for this pass."""
import bpy, bmesh, sys, json
import numpy as np
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index('--') + 1]
zone_path = sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else None
o = bpy.data.objects['Body_F']
me = o.data
nv = len(me.vertices)
bm = bmesh.new()
bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm, epsilon=0.0)
pairs = tree.overlap(tree)
T = np.load(zone_path)['torso'] if zone_path else np.zeros(nv, bool)
tri_in_zone = np.array([any(T[v.index] for v in f.verts) for f in bm.faces])
pairs = [(a, b) for a, b in pairs if a < b]
zone_pairs = [(a, b) for a, b in pairs if tri_in_zone[a] or tri_in_zone[b]]
loc = []
for a, b in zone_pairs[:40]:
    c = sum((v.co for v in bm.faces[a].verts), bm.faces[a].verts[0].co * 0) / 3.0
    loc.append([round(c.x, 4), round(c.y, 4), round(c.z, 4)])
json.dump({'tris': len(bm.faces), 'intersecting_pairs_whole_mesh': len(pairs), 'intersecting_pairs_touching_torso_zone': len(zone_pairs), 'zone_pair_locations': loc}, open(out, 'w'), indent=1)
print('SELFINT', len(pairs), len(zone_pairs))
