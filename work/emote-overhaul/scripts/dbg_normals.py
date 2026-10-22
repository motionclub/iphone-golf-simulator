import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
z = np.load(f'{HERE}/../data/proxy_{tag}.npz', allow_pickle=True)
for key in ('body', 'shirt', 'shorts'):
    co, tris = z[key + '_co'], z[key + '_tris']
    tr = BVHTree.FromPolygons(co.tolist(), tris.tolist(), all_triangles=True)
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    n = np.cross(b - a, c - a); ln = np.linalg.norm(n, axis=1); ok = ln > 1e-12
    n[ok] /= ln[ok, None]
    cen = (a + b + c) / 3
    inward = 0; tot = 0; flips = []
    rng = np.random.default_rng(1)
    idx = rng.choice(len(tris), size=min(4000, len(tris)), replace=False)
    for i in idx:
        if not ok[i]: continue
        o = Vector(cen[i] + n[i] * 2e-4); d = Vector(n[i])
        hits = 0
        for _ in range(12):
            loc, nor, fi, dist = tr.ray_cast(o, d)
            if loc is None: break
            hits += 1; o = loc + d * 1e-5
        tot += 1
        if hits % 2 == 1:
            inward += 1; flips.append(i)
    # signed volume
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6
    print(f'{tag} {key}: tris {len(tris)} sampled {tot} normals pointing INWARD (odd ray hits): {inward} = {100*inward/max(tot,1):.1f}%   signed volume {vol:.4f}')
