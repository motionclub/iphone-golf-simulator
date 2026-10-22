"""Straighten the jagged weld loop: slide the loop vertices along the surface tangent toward a planar ring, relax a thin band behind it (positions only)."""
import numpy as np
from collections import defaultdict
from ff_common import *


def straighten_loop(V, F, cut, side, frame, kappa=0.15, depth=3, iters=10, lam=0.45, beta=0.0):
    O, Fh, Lh, Zh = frame
    V = V.copy().astype(np.float64)
    ring = list(cut['ring'])
    Nrm = vertex_normals(V, F)
    Lc = to_local(V, side, frame)
    f = Lc[ring, 0]
    fm = f.mean()
    f2 = fm + kappa * (f - fm)
    n = Nrm[ring]
    nl = np.stack([n @ Fh, n @ Lh, n[:, 2]], 1)
    d = np.maximum(1 - nl[:, 0] ** 2, 0.15)
    ml = -nl[:, 0] * nl[:, 1] / d
    mz = -nl[:, 0] * nl[:, 2] / d
    df = (f2 - f)
    V[ring] += df[:, None] * (Fh[None, :] + ml[:, None] * Lh[None, :] + mz[:, None] * Zh[None, :])
    if beta > 0:
        # re-space the loop vertices along the (l, z) contour toward uniform spacing (twins that share a section-plane position are pulled apart)
        P3 = V[ring]
        Lc2 = to_local(P3, side, frame)
        seg = np.linalg.norm(np.roll(Lc2, -1, axis=0)[:, 1:3] - Lc2[:, 1:3], axis=1)
        u = np.r_[0.0, np.cumsum(seg)]; U = u[-1]
        ub = u[:-1]
        ubar = np.arange(len(ring)) * U / len(ring)
        smax = 0.004
        uu = ub + np.clip(beta * (ubar - ub), -smax, smax)
        # minimum spacing along the contour (twins that share a section-plane position are pulled apart); the start vertex stays put
        gap = 0.0022
        for i in range(1, len(uu)):
            uu[i] = max(uu[i], uu[i - 1] + gap)
        for i in range(len(uu) - 2, 0, -1):
            uu[i] = min(uu[i], uu[i + 1] - gap)
        uu = np.maximum.accumulate(uu)
        ext_u = np.r_[ub, U]; ext_P = np.vstack([P3, P3[:1]])
        newP = np.stack([np.interp(uu, ext_u, ext_P[:, k]) for k in range(3)], 1)
        V[ring] = newP
    # band behind the loop (kept faces only)
    kept = cut['kept']
    nb = defaultdict(set)
    for fi in np.where(kept)[0]:
        p = F[fi]
        for k in range(len(p)):
            a, b = p[k], p[(k + 1) % len(p)]
            nb[a].add(b); nb[b].add(a)
    ringset = set(ring)
    layer = set(ring); band = set()
    for dpt in range(depth):
        nxt = set()
        for v in layer:
            for u in nb[v]:
                if u not in ringset and u not in band:
                    nxt.add(u)
        band |= nxt; layer = nxt
    band = sorted(band)
    for it in range(iters):
        for sgn in (lam, -(lam + 0.02)):
            newp = V.copy()
            for v in band:
                nbrs = list(nb[v])
                newp[v] = V[v] + sgn * (V[nbrs].mean(0) - V[v])
            V = newp
    return V, dict(moved_loop=len(ring), band=len(band), max_slide_mm=float(np.abs(df).max() * 1000))
