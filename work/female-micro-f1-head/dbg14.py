import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo, cage, mesher, zones
d = np.load(fl.W / 'data/ring.npz'); ring_pos = d['pos']
H = geo.Head(); cg = cage.build_cage(ring_pos, geo.C, H=H)
lvl = zones.make_level_fn(H)
import collections
U, F, depth, n0 = mesher.refine(cg, H, lvl, max_level=3, verbose=False)
P = H.phi(U)
for v, p in cg['pinned'].items(): P[v] = p
cen = np.array([P[f].mean(0) for f in F]); dep = np.array(depth)
for z0 in np.arange(1.42, 1.50, 0.01):
    m = (np.abs(cen[:, 0]) < 0.03) & (cen[:, 1] < -0.08) & (cen[:, 2] >= z0) & (cen[:, 2] < z0 + 0.01)
    print(f'z {z0:.3f}', dict(collections.Counter(dep[m].tolist())))
want = lvl(cen)
m = (np.abs(cen[:, 0]) < 0.03) & (cen[:, 1] < -0.08) & (cen[:, 2] >= 1.44) & (cen[:, 2] < 1.46)
print('want in region', dict(collections.Counter(want[m].tolist())))
