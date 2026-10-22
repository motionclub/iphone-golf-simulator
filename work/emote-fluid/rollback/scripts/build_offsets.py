"""build_offsets.py <male|female> : per body-skin vertex the distance (bind pose, along the vertex normal) to the OUTER surface of the clothes (shirt, shorts; thick 3 mm shells), 0 where uncovered.
Writes it into data/proxy_<tag>.npz as `body_off` (the engine's obstacle = the posed body skin pushed out by this offset: a single-layer surface with consistent normals)."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts')); sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from emo_clear import vertex_normals
tag = sys.argv[sys.argv.index('--') + 1]
path = f'{HERE}/../data/proxy_{tag}.npz'
z = dict(np.load(path, allow_pickle=True))
co, tris = z['body_co'], z['body_tris']
n0 = vertex_normals(co, tris)
trees = {k: BVHTree.FromPolygons(z[k + '_co'].tolist(), z[k + '_tris'].tolist(), all_triangles=True) for k in ('shirt', 'shorts')}
off = np.zeros(len(co))
for i in range(len(co)):
    best = 0.0
    for k, tr in trees.items():
        o = Vector(co[i] + n0[i] * 1e-4); d = Vector(n0[i]); last = None
        chain = []
        for _ in range(5):
            loc, nor, fi, dist = tr.ray_cast(o, d, 0.12)
            if loc is None:
                break
            dd = (loc - Vector(co[i])).length
            if last is not None and dd - last > 0.006:
                break
            chain.append(dd); last = dd
            o = loc + d * 1e-5
        if chain:
            best = max(best, chain[-1])
    off[i] = best
cov = off > 0
print(tag, 'covered vertices %.1f%%' % (100 * cov.mean()), 'offset mm: median %.1f  p90 %.1f  max %.1f' % (1000 * np.median(off[cov]), 1000 * np.percentile(off[cov], 90), 1000 * off.max()))
z['body_off'] = off
np.savez_compressed(path, **z)
print('OFFSETS_DONE', tag)
