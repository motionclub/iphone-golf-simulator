"""Zone definition + mesh helpers (numpy only; run with Blender python3.13)."""
import numpy as np, pickle
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso')
V0 = np.load(W / 'baseline/mesh.npz')['co']; F = pickle.load(open(W / 'baseline/faces.pkl', 'rb'))
N0 = len(V0)
Z_LO = 0.7700     # crotch apex (legs fully separate below, merged above): verts z < Z_LO are LEG, never moved
Z_HI = 1.4000     # head/neck starts here: verts z >= Z_HI never moved
def xlim(z):
    """lateral zone limit: torso side + a margin inside the armpit gap below z=1.2, shoulder ball above"""
    z = np.asarray(z); return np.where(z < 1.20, 0.205, np.where(z < 1.24, 0.205 + (z - 1.20) / 0.04 * 0.075, 0.28))
def zone_mask(V=V0):
    return (V[:, 2] >= Z_LO) & (V[:, 2] < Z_HI) & (np.abs(V[:, 0]) <= xlim(V[:, 2]))
def vnormals(V, iters=0):
    n = np.zeros_like(V)
    for f in F:
        for k in range(1, len(f) - 1):
            a, b, c = V[f[0]], V[f[k]], V[f[k + 1]]; fn = np.cross(b - a, c - a)
            n[f[0]] += fn; n[f[k]] += fn; n[f[k + 1]] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    if iters:
        nb = neighbors()
        for _ in range(iters):
            m = np.zeros_like(n)
            for i, js in enumerate(nb): m[i] = n[i] + n[js].sum(0)
            n = m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)
    return n
_nb = None
def neighbors():
    global _nb
    if _nb is None:
        s = [set() for _ in range(N0)]
        for f in F:
            for k in range(len(f)):
                a, b = f[k], f[(k + 1) % len(f)]; s[a].add(b); s[b].add(a)
        _nb = [np.array(sorted(x), int) for x in s]
    return _nb
if __name__ == '__main__':
    z = zone_mask(); print('zone verts', int(z.sum()), 'of', N0)
    # apex check: components of slice near crotch
    pos = V0[z]; print('zone z', pos[:, 2].min(), pos[:, 2].max(), 'x', pos[:, 0].min(), pos[:, 0].max())
    # which verts straddle the apex: verts with |x|<0.04 and 0.74<z<0.80 -> histogram of z
    c = V0[(np.abs(V0[:, 0]) < 0.03)]
    zz = np.sort(c[(c[:, 2] > 0.70) & (c[:, 2] < 0.85), 2]); print('central-column verts z:', np.round(zz[:80], 3))
