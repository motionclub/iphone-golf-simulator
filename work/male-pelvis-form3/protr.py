"""Nub / point / ridge detector for the crotch (front and rear):  deviation (mm, outward positive) of each vertex from a Taubin-smoothed copy of its own neighbourhood (feature scale ~ 3-4 edges = 25-35 mm removed, the 80+ mm mound / cheek shape kept).
python3 protr.py tag..."""
import sys, numpy as np
sys.path.insert(0, '.')
from common import V0, vnormals
from sculpt import taubin
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def zone(x, y, z):
    U = np.abs(V0[:, 0]); Y = V0[:, 1]; Z = V0[:, 2]
    return (1 - sstep(x[0], x[1], U)) * sstep(y[0], y[1], Y) * (1 - sstep(y[2], y[3], Y)) * sstep(z[0], z[1], Z) * (1 - sstep(z[2], z[3], Z))
ZONES = {'FRONT': dict(x=(0.05, 0.085), y=(-0.225, -0.20, -0.06, -0.03), z=(0.745, 0.76, 0.93, 0.96)),
         'REAR_CENTRE': dict(x=(0.05, 0.085), y=(0.02, 0.04, 0.135, 0.155), z=(0.745, 0.76, 0.90, 0.93))}
def run(V, iters=14):
    out = {}; N = vnormals(V)
    for nm, zc in ZONES.items():
        g = zone(**zc); Vs = taubin(V, g, iters=iters); d = ((V - Vs) * N).sum(1) * 1000
        sel = g > 0.5; idx = np.where(sel)[0]; i = idx[np.argmax(d[sel])]
        out[nm] = dict(nub_mm=round(float(d[sel].max()), 2), at_mm=[round(float(c) * 1000) for c in V[i]], dent_mm=round(float(-d[sel].min()), 2))
    return out
if __name__ == '__main__':
    for t in sys.argv[1:]:
        V = V0 if t == 'start' else np.load(f'data/V_{t}.npy'); print(t, run(V))
