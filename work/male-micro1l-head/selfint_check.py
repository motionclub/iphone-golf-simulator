"""Self-intersections of Body_M (triangle pairs that intersect and share no vertex).  blender -b --python selfint_check.py -- <blend> [<blend2> ...]"""
import sys, json
import numpy as np, bpy
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
for path in argv:
    bpy.ops.wm.open_mainfile(filepath=path)
    me = bpy.data.objects['Body_M'].data
    V = [tuple(v.co) for v in me.vertices]; T = []
    for p in me.polygons:
        vs = list(p.vertices); T.append((vs[0], vs[1], vs[2]))
        if len(vs) > 3: T.append((vs[0], vs[2], vs[3]))
    bvh = BVHTree.FromPolygons(V, T)
    pairs = bvh.overlap(bvh); bad = []
    for a, b in pairs:
        if a >= b: continue
        if set(T[a]) & set(T[b]): continue
        bad.append((a, b))
    cs = [tuple(np.round(np.mean([V[i] for i in T[a]], axis=0) * 1000, 1)) for a, b in bad[:12]]
    print('SELFINT', json.dumps(dict(blend=path.split('/')[-1], pairs_no_shared_vertex=len(bad), sample_centres_mm=cs)))
