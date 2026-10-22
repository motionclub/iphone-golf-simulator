"""Digit centre lines of the male hand from the rasterised silhouette in the hand frame (rows of constant U)."""
import sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts/dev')
from hand_raster import raster

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
d = np.load(W + 'data/male_body.npz')
co, tris = d['co'], d['tris']
sel = np.where((co[:, 0] < -0.50) & (co[:, 2] < 1.0))[0]
idx = -np.ones(len(co), int); idx[sel] = np.arange(len(sel))
keep = np.all(idx[tris] >= 0, axis=1)
T = idx[tris[keep]]
P = co[sel]
c = P.mean(0)
U_, S_, Vt = np.linalg.svd(P - c, full_matrices=False)
u, v = Vt[0], Vt[1]
if u[2] > 0: u = -u
if v[1] > 0: v = -v
p = np.cross(v, u)
Q = np.stack([(P - c) @ u, (P - c) @ v, (P - c) @ p], 1)
zb, (u0, v0, res) = raster(Q, T, res=0.0005, side=+1)
mask = np.isfinite(zb)
print('raster', mask.shape, 'u0', round(u0, 4), 'v0', round(v0, 4))
rows = {}
for U in (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.085, 0.09):
    r = int((U - u0) / res)
    row = mask[r]
    runs, s = [], None
    for j, f in enumerate(row):
        if f and s is None: s = j
        if (not f) and s is not None:
            runs.append((v0 + s * res, v0 + (j - 1) * res)); s = None
    if s is not None: runs.append((v0 + s * res, v0 + (len(row) - 1) * res))
    rows[U] = runs
    print(f'U={U:.3f}:', [(round(a, 3), round(b, 3), 'w=%.1fmm' % ((b - a) * 1000)) for a, b in runs])
