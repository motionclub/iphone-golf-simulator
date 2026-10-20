"""Implicit bi-Laplacian (thin-plate) fairing of a region of the Body_M mesh.  numpy only.

minimise   1/2 sum_i m_i |v_i - v_i^cur|^2  +  1/2 sum_k w_k |(L v)_k|^2          (v_i = current positions, L = uniform graph Laplacian)
over the FREE vertices (every vertex with weight g_i > g_min); all other vertices stay fixed.  w_k = tau * g_k  (g in [0,1] smooth mask), m_i = 1.
Solved densely:  (I + A^T W A) x = v_cur - A^T W B   with A = L[R,Fr], B = L[R,fixed] v_fixed.

Properties: removes creases / kinks / flaps of wavelength < ~ (tau)^(1/4) edge lengths, no per-iteration shrink bookkeeping (no Taubin lambda|mu tuning), unconditionally stable,
fixed vertices outside the mask keep the surface welded to the rest of the body, tangential spacing is evened out as a side effect (uniform Laplacian).
"""
import numpy as np
from common import neighbors

_NB = None
def _nb():
    global _NB
    if _NB is None: _NB = neighbors()
    return _NB

def fair(V, g, tau=10.0, g_min=0.02, return_info=False):
    """V (n,3) current positions, g (n,) weights in [0,1].  Returns new positions (same array for vertices outside the mask)."""
    nb = _nb(); n = len(V)
    Fr = np.where(g > g_min)[0]; m = len(Fr)
    if m == 0: return V.copy()
    pos = -np.ones(n, np.int64); pos[Fr] = np.arange(m)
    isfree = pos >= 0
    # rows: all vertices k with w_k>0 whose closed neighbourhood touches a free vertex
    rows = []
    for k in range(n):
        if g[k] <= 0: continue
        if isfree[k] or isfree[nb[k]].any(): rows.append(k)
    rows = np.array(rows, np.int64); r = len(rows)
    A = np.zeros((r, m)); B = np.zeros((r, 3))
    for ri, k in enumerate(rows):
        d = len(nb[k]); coef = {k: 1.0}
        for j in nb[k]: coef[j] = coef.get(j, 0.0) - 1.0 / d
        for j, c in coef.items():
            if isfree[j]: A[ri, pos[j]] += c
            else: B[ri] += c * V[j]
    w = tau * g[rows]
    AW = A.T * w[None, :]
    M = np.eye(m) + AW @ A
    rhs = V[Fr] - AW @ B
    X = np.linalg.solve(M, rhs)
    out = V.copy(); out[Fr] = X
    if return_info: return out, dict(free=int(m), rows=int(r))
    return out

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0); return t * t * (3 - 2 * t)
def box_mask(V0, x=(0.0, 0.07, 0.10), y=(-0.20, -0.17, 0.085, 0.115), z=(0.715, 0.73, 0.80, 0.83)):
    """smooth box weight on ORIGINAL coordinates: |x| ramps x[1]->x[2] to 0, y ramps y0->y1 up and y2->y3 down, z likewise"""
    U = np.abs(V0[:, 0]); Y = V0[:, 1]; Z = V0[:, 2]
    gx = 1 - smoothstep(x[1], x[2], U)
    gy = smoothstep(y[0], y[1], Y) * (1 - smoothstep(y[2], y[3], Y))
    gz = smoothstep(z[0], z[1], Z) * (1 - smoothstep(z[2], z[3], Z))
    return gx * gy * gz
