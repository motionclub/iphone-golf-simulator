"""Sculpting toolkit on the dumped Body_M mesh (numpy only; run with Blender's python3.13).
All operators take/return Nx3 float64 position arrays; masks are per-vertex weights in [0,1]."""
import numpy as np
from common import V0, F, N0, neighbors, vnormals, GROUPS

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0); return t * t * (3 - 2 * t)
def band(x, lo0, lo1, hi0, hi1):
    """1 inside [lo1,hi0], smooth ramps lo0->lo1 and hi0->hi1"""
    return smoothstep(lo0, lo1, x) * (1 - smoothstep(hi0, hi1, x))

_nbi = None
def _lap_ops():
    """sparse-ish neighbour structures for fast numpy Laplacian: padded index matrix"""
    global _nbi
    if _nbi is None:
        nb = neighbors(); m = max(len(a) for a in nb)
        idx = np.full((N0, m), -1, np.int64)
        for i, a in enumerate(nb): idx[i, :len(a)] = a
        cnt = np.maximum(np.array([len(a) for a in nb], float), 1.0)
        _nbi = (idx, cnt)
    return _nbi
def laplacian(V):
    idx, cnt = _lap_ops(); P = np.vstack([V, np.zeros((1, 3))])
    s = P[idx].sum(1) - (idx < 0).sum(1)[:, None] * 0.0   # padded -1 index -> last row (zeros)
    return s / cnt[:, None] - V
def taubin(V, w, iters=10, lam=0.5, mu=-0.53):
    V = V.copy()
    for _ in range(iters):
        V += lam * w[:, None] * laplacian(V)
        V += mu * w[:, None] * laplacian(V)
    return V
def diffuse_scalar(f, w, iters=20, lam=0.5):
    """smooth a per-vertex scalar field with the mesh Laplacian (weights w)"""
    idx, cnt = _lap_ops(); f = f.copy()
    for _ in range(iters):
        P = np.concatenate([f, [0.0]]); s = P[idx].sum(1) / cnt - f; f += lam * w * s
    return f
def gauss(d, s): return np.exp(-0.5 * (d / s) ** 2)

def taubin_scalar(f, w, iters=10, lam=0.5, mu=-0.53):
    """Taubin lambda|mu smoothing of a per-vertex scalar field with weights w (volume-preserving, no shrink)"""
    idx, cnt = _lap_ops(); f = f.copy()
    def lap(g):
        P = np.concatenate([g, [0.0]]); return P[idx].sum(1) / cnt - g
    for _ in range(iters):
        f += lam * w * lap(f); f += mu * w * lap(f)
    return f
