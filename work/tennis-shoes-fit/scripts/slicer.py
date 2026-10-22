"""numpy plane slicer (closed loops of z = const)."""
import numpy as np, sys
np.set_printoptions(precision=4, suppress=True, linewidth=200)

def slice_loops(V, F, z):
    """closed polylines of the plane z=const (numpy only; chains by shared edge keys)."""
    d = V[:, 2] - z
    s = d[F]
    pos = s >= 0
    cnt = pos.sum(1)
    sel = np.nonzero((cnt == 1) | (cnt == 2))[0]
    segs = []
    for ti in sel:
        tri = F[ti]
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ia, ib = tri[a], tri[b]
            if (d[ia] >= 0) != (d[ib] >= 0):
                t = d[ia] / (d[ia] - d[ib])
                p = V[ia] + t * (V[ib] - V[ia])
                key = (ia, ib) if ia < ib else (ib, ia)
                pts.append((key, p))
        if len(pts) == 2:
            segs.append((pts[0][0], pts[0][1], pts[1][0], pts[1][1]))
    adj, pt = {}, {}
    for ka, pa, kb, pb in segs:
        adj.setdefault(ka, []).append(kb); adj.setdefault(kb, []).append(ka)
        pt[ka] = pa; pt[kb] = pb
    seen, loops = set(), []
    for k0 in adj:
        if k0 in seen: continue
        chain = [k0]; seen.add(k0); cur = k0; prev = None
        while True:
            nxt = [k for k in adj[cur] if k != prev and k not in seen]
            if not nxt: break
            prev, cur = cur, nxt[0]; chain.append(cur); seen.add(cur)
        loops.append(np.array([pt[k] for k in chain]))
    return loops

def area(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))

