"""Fast mesh-quality checks for the fit loop: dihedral angle p99/max inside the pelvis zone, rear contour error vs the plate."""
import numpy as np, sys
sys.path.insert(0, '.')
import common
from common import F, V0
_T = common._tris(); _fid = np.concatenate([[i] * (len(f) - 2) for i, f in enumerate(F)]).astype(np.int64)
from collections import defaultdict
_ef = defaultdict(list)
for fi, f in enumerate(F):
    for k in range(len(f)):
        a, b = f[k], f[(k + 1) % len(f)]; _ef[(min(a, b), max(a, b))].append(fi)
_pairs = [(e, fs) for e, fs in _ef.items() if len(fs) == 2]
_ea = np.array([p[1][0] for p in _pairs]); _eb = np.array([p[1][1] for p in _pairs]); _ev = np.array([p[0] for p in _pairs])
_zc = (V0[_ev[:, 0], 2] + V0[_ev[:, 1], 2]) / 2; _xc = np.abs(V0[_ev[:, 0], 0] + V0[_ev[:, 1], 0]) / 2
ZONE_E = (_zc >= 0.735) & (_zc <= 1.06) & (_xc <= 0.2)
def fnorm(V):
    a, b, c = V[_T[:, 0]], V[_T[:, 1]], V[_T[:, 2]]; fn = np.cross(b - a, c - a); n = np.zeros((len(F), 3)); np.add.at(n, _fid, fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
def dihedral(V):
    n = fnorm(V); return np.degrees(np.arccos(np.clip((n[_ea] * n[_eb]).sum(1), -1, 1)))
_d0 = dihedral(V0)
def stats(V):
    d = dihedral(V); return dict(p99=float(np.percentile(d[ZONE_E], 99)), max=float(d[ZONE_E].max()), p99_start=float(np.percentile(_d0[ZONE_E], 99)), new_sharp=int(((d > 40) & (_d0 < 25) & ZONE_E).sum()))
if __name__ == '__main__':
    import time; t = time.time(); print(stats(V0), round(time.time() - t, 2))
    for tag in sys.argv[1:]: print(tag, stats(np.load(f'data/V_{tag}.npy')))
