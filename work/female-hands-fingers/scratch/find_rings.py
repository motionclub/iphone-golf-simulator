import numpy as np, sys
from collections import defaultdict
D = np.load('data/mesh_start.npz')
V = D['V'].astype(np.float64); cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
polys = [tuple(int(x) for x in cv[s:s+t]) for s, t in zip(ls, lt)]
print('V', V.shape, 'z range', V[:,2].min(), V[:,2].max(), 'x range', V[:,0].min(), V[:,0].max(), 'y range', V[:,1].min(), V[:,1].max())
# vertices that share exact z with >= 12 others and |x|>0.15 -> candidate planar rings
for side in (+1, -1):
    m = (side * V[:, 0] > 0.15) & (V[:, 2] > 0.60) & (V[:, 2] < 0.95)
    idx = np.nonzero(m)[0]
    zs = np.round(V[idx, 2], 6)
    u, c = np.unique(zs, return_counts=True)
    big = [(float(a), int(b)) for a, b in zip(u, c) if b >= 10]
    print('side', side, 'n verts in box', len(idx), 'planar z levels (>=10 verts):', big)
