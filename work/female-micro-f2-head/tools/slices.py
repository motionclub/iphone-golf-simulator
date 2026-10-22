"""horizontal and sagittal/coronal slices of a mesh npz -> polylines (numpy). 
slice_z(V,F,z) -> list of closed/open polylines (n,3) ;  slice_plane(axis,val)"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, meshlib as ml

def slice_axis(V, T, axis, val):
    """T: (m,4) fan triangles. returns segments (k,2,3)"""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    da, db, dc = a[:, axis] - val, b[:, axis] - val, c[:, axis] - val
    segs = []
    for (p, q, r, dp, dq, dr) in ((a, b, c, da, db, dc),):
        pass
    P = np.stack([a, b, c], 1); D = np.stack([da, db, dc], 1)
    out = []
    for e0, e1 in ((0, 1), (1, 2), (2, 0)):
        pass
    cnt = (D > 0).sum(1)
    sel = np.where((cnt == 1) | (cnt == 2))[0]
    for i in sel:
        pts = []
        for e0, e1 in ((0, 1), (1, 2), (2, 0)):
            d0, d1 = D[i, e0], D[i, e1]
            if (d0 > 0) != (d1 > 0):
                t = d0 / (d0 - d1); pts.append(P[i, e0] + t * (P[i, e1] - P[i, e0]))
        if len(pts) == 2: out.append(pts)
    return np.array(out)

def chain(segs, tol=1e-7):
    """join segments into polylines"""
    if len(segs) == 0: return []
    key = lambda p: tuple(np.round(p / tol).astype(np.int64))
    nxt = {}
    for k, (p, q) in enumerate(segs):
        nxt.setdefault(key(p), []).append((k, 0)); nxt.setdefault(key(q), []).append((k, 1))
    used = np.zeros(len(segs), bool); polys = []
    for s in range(len(segs)):
        if used[s]: continue
        used[s] = True; line = [segs[s][0], segs[s][1]]
        for direction in (1, 0):
            while True:
                end = line[-1] if direction == 1 else line[0]
                cand = [(k, e) for (k, e) in nxt.get(key(end), []) if not used[k]]
                if not cand: break
                k, e = cand[0]; used[k] = True
                newp = segs[k][1 - e]
                if direction == 1: line.append(newp)
                else: line.insert(0, newp)
        polys.append(np.array(line))
    return polys
