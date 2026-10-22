import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
def vol(params, side=+1):
    Vn, polys, si = asm3.assemble(params, verbose=False); m = si[side]['mapping']; info = si[side]['info']
    Lp = lambda v: to_local(Vn[[m[v]]].astype(float), side)[0]
    ws = []; As = []
    for r, ids in sorted(info['ring'].items()):
        pts = np.array([Lp(v) for v in ids if v in m])
        # ring polygon in (a', n) ordered by angle about its centroid (rows through the thumb hole have missing verts -> use convex hull area as a robust cross-section)
        from itertools import combinations
        P = pts[:, :2]; hull = []
        def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
        pts_s = sorted(map(tuple, P)); lower = []
        for p in pts_s:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
            lower.append(p)
        upper = []
        for p in reversed(pts_s):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
            upper.append(p)
        hull = lower[:-1] + upper[:-1]; h = np.array(hull)
        A = 0.5 * abs(np.dot(h[:, 0], np.roll(h[:, 1], -1)) - np.dot(h[:, 1], np.roll(h[:, 0], -1)))
        ws.append(pts[:, 2].mean()); As.append(A)
    ws = np.array(ws); As = np.array(As); msk = ws >= -0.044 - 1e-4
    return float(np.trapezoid(As[msk], ws[msk]) * 1e9), ws, As
