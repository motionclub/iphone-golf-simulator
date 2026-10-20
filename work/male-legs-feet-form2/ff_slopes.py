"""Ring 0 (planar slice of the ORIGINAL surface just ahead of the cut loop) and its forward slopes, sampled at the polar angles of the kept loop columns."""
import numpy as np
from collections import defaultdict
from ff_common import *
from ff_build import aligned_columns, ToeRow


def slice_loop(Lc, F, region, c):
    """Intersect the (original, full) faces with the plane f = c inside the foot region; return the longest ordered closed polygon (K,3) (f=c, l, z)."""
    pts = {}; segs = []
    for fi, f in enumerate(F):
        if not region[list(f)].all():
            continue
        vals = [Lc[v, 0] - c for v in f]
        if min(vals) > 0 or max(vals) < 0:
            continue
        cross = []
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            va, vb = vals[k], vals[(k + 1) % len(f)]
            if (va < 0) != (vb < 0):
                t = va / (va - vb)
                key = (min(a, b), max(a, b))
                if key not in pts: pts[key] = Lc[a] + t * (Lc[b] - Lc[a])
                cross.append(key)
        if len(cross) == 2: segs.append((cross[0], cross[1]))
        elif len(cross) == 4: segs.append((cross[0], cross[1])); segs.append((cross[2], cross[3]))
    adj = defaultdict(list)
    for a, b in segs:
        adj[a].append(b); adj[b].append(a)
    seen = set(); best = []
    for s0 in list(adj.keys()):
        if s0 in seen: continue
        chain = [s0]; seen.add(s0); prev = None; cur = s0
        while True:
            nxt = [u for u in adj[cur] if u != prev and u not in seen]
            if not nxt: break
            prev, cur = cur, nxt[0]; chain.append(cur); seen.add(cur)
        if len(chain) > len(best): best = chain
    return np.array([pts[k] for k in best])


def polar_sample(P, lc, zc, A, B, theta):
    ang = np.arctan2((P[:, 2] - zc) / B, (P[:, 1] - lc) / A)
    o = np.argsort(ang)
    a = np.r_[ang[o] - 2 * np.pi, ang[o], ang[o] + 2 * np.pi]
    out = np.zeros((len(theta), 3))
    for k in range(3):
        v = np.r_[P[o, k], P[o, k], P[o, k]]
        out[:, k] = np.interp(theta, a, v)
    return out


def ring0_and_slopes(V, F, cut, side, frame, Pp, f1_gap=0.006, df=0.004, smooth=1):
    """returns dict(ring0 (N,3) local planar ring at f1 on the original surface, slopes (N,2) = (dl/df, dz/df), f1)"""
    Lc = to_local(V, side, frame)
    region = cut['region']
    ring = cut['ring']
    TR = ToeRow(Pp)
    info = aligned_columns(cut['Lc'][ring], TR.Kd, TR.Kp)
    Pcols = info['P'][info['cols']]                           # loop vertices used as columns (local f, l, z)
    fmax = float(info['P'][:, 0].max())
    f1 = fmax + f1_gap
    lp, zp = info['P'][:, 1], info['P'][:, 2]
    lc = 0.5 * (lp.max() + lp.min()); zc = 0.5 * (zp.max() + zp.min()); A = 0.5 * (lp.max() - lp.min()); B = 0.5 * (zp.max() - zp.min())
    theta = np.arctan2((Pcols[:, 2] - zc) / B, (Pcols[:, 1] - lc) / A)
    S0 = slice_loop(Lc, F, region, f1)
    S1 = slice_loop(Lc, F, region, f1 + df)
    assert len(S0) > 30 and len(S1) > 30, (len(S0), len(S1))
    R0 = polar_sample(S0, lc, zc, A, B, theta)
    R1 = polar_sample(S1, lc, zc, A, B, theta)
    m = (R1[:, 1:3] - R0[:, 1:3]) / df
    ker = np.array([1, 2, 3, 2, 1], float); ker /= ker.sum()
    for d_ in range(2):
        x = np.r_[m[-2:, d_], m[:, d_], m[:2, d_]]
        m[:, d_] = np.convolve(x, ker, mode='valid')
    R0[:, 0] = f1
    return dict(ring0=R0, slopes=m, f1=f1, slice_len=(len(S0), len(S1)))


def slopes_fn(V, F, cut, side, frame, Pp):
    return ring0_and_slopes(V, F, cut, side, frame, Pp)
