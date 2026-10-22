import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts')); sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import emo_clear as CL
a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
z = np.load(f'{HERE}/../data/proxy_{tag}.npz', allow_pickle=True)
body = CL.SkinProxy(z['body_co'], z['body_idx'], z['body_w'], z['body_tris'])
from emo_clear import vertex_normals
n0 = vertex_normals(body.co, z['body_tris'])
layers = {k: BVHTree.FromPolygons(z[k + '_co'].tolist(), z[k + '_tris'].tolist(), all_triangles=True) for k in ('shirt', 'shorts')}
rng = np.random.default_rng(3)
idx = rng.choice(len(body.co), 25, replace=False)
names = list(z['names'])
for i in idx:
    row = []
    for k, tr in layers.items():
        o = Vector(body.co[i] + n0[i] * 1e-4); d = Vector(n0[i]); hits = []
        for _ in range(4):
            loc, nor, fi, dist = tr.ray_cast(o, d, 0.12)
            if loc is None: break
            hits.append(round((loc - Vector(body.co[i])).length * 1000, 1)); o = loc + d * 1e-5
        row.append((k, hits))
    print(names[body.dom[i]], row)
