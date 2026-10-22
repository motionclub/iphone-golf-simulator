"""Hand cut extraction + mesh assembly utilities (topology side of the local hand rebuild)."""
import numpy as np
from collections import defaultdict
import hand_sdf as H


def _boundary(F, kept):
    ec = defaultdict(list)
    for fi in np.where(kept)[0]:
        f = F[fi]
        for k in range(4):
            a, b = int(f[k]), int(f[(k + 1) % 4])
            ec[(min(a, b), max(a, b))].append(fi)
    bedges = [e for e, v in ec.items() if len(v) == 1]
    verts = set(v for e in bedges for v in e)
    cnt = defaultdict(int)
    for fi in np.where(kept)[0]:
        for v in F[fi]:
            if int(v) in verts:
                cnt[int(v)] += 1
    adj = defaultdict(list)
    for a, b in bedges:
        adj[a].append(b); adj[b].append(a)
    return bedges, verts, cnt, adj


def extract_cut(co, F, side, w0=-0.055, peel=8):
    """Cut the hand off at w>=w0, then PEEL boundary faces at sharp corners (vertices with a single kept face) until the
    wrist boundary is a straight-ish simple loop.  Returns dict(L, Hmask(free vertices), removed, kept, ring)."""
    L = H.to_local(co, side)
    gx = side * co[:, 0]
    Hs = (gx > 0.30) & (co[:, 2] < 1.10) & (L[:, 2] >= w0)
    rem = Hs[F].any(axis=1)
    kept = ~rem
    for it in range(peel):
        bedges, verts, cnt, adj = _boundary(F, kept)
        corners = set(v for v in verts if cnt[v] == 1)
        if not corners:
            break
        trial = kept.copy()
        for fi in np.where(kept)[0]:
            if any(int(v) in corners for v in F[fi]):
                trial[fi] = False
        b2, v2, c2, a2 = _boundary(F, trial)
        if not all(len(v) == 2 for v in a2.values()):      # would pinch the loop: stop peeling
            break
        kept = trial
    bedges, verts, cnt, adj = _boundary(F, kept)
    assert all(len(v) == 2 for v in adj.values()), 'boundary is not a simple loop'
    start = next(iter(adj))
    ring = [start]; prev = None; cur = start
    while True:
        nxt = [v for v in adj[cur] if v != prev]
        nxt = nxt[0] if prev is not None else adj[cur][0]
        if nxt == start:
            break
        ring.append(nxt); prev, cur = cur, nxt
    assert len(ring) == len(adj), (len(ring), len(adj))
    used = np.zeros(len(co), bool)
    used[F[kept].ravel()] = True
    free = (~used) & ((gx > 0.20) | True)
    # only vertices that belonged to the hand/forearm cut region may be freed
    assert (free & ~(Hs | (gx > 0.30))).sum() == 0
    return dict(L=L, Hmask=free, removed=~kept, kept=kept, ring=ring)


def order_ring(ring, L, front_first=True):
    """keep the boundary loop's CONNECTIVITY order; choose direction (dorsal-first) and start vertex (nearest the +a' equator).
    returns ordered vertex id list, monotonic t in [0,1) per vertex, centre, (A,B)."""
    ring = list(ring)
    P = L[ring]
    c = P.mean(axis=0)
    A = 0.5 * (P[:, 0].max() - P[:, 0].min()); B = 0.5 * (P[:, 1].max() - P[:, 1].min())
    ang = np.arctan2((P[:, 1] - c[1]) / B, (P[:, 0] - c[0]) / A)
    # net winding direction of the connectivity order in the (a', n) plane
    d = np.diff(np.r_[ang, ang[0]]); d = (d + np.pi) % (2 * np.pi) - np.pi
    if d.sum() > 0:                      # ang increasing -> toward +n (palmar first); we want dorsal first (ang decreasing)
        ring = ring[::-1]; ang = ang[::-1]
    # start at the vertex with the smallest t = (-ang/2pi) mod 1 (just dorsal of the +a' equator)
    t = (-ang / (2 * np.pi)) % 1.0
    k0 = int(np.argmin(t))
    ring = ring[k0:] + ring[:k0]; t = np.r_[t[k0:], t[:k0]]
    t = (t - t[0]) % 1.0
    t = np.maximum.accumulate(t)         # enforce monotonic along the connectivity order
    return ring, t, c, (A, B)


def orient_consistently(faces, fixed_faces):
    """faces: list of tuples (new). fixed_faces: array (K,4) with trusted orientation. Returns oriented list (flips as needed)."""
    from collections import deque
    allf = [tuple(f) for f in fixed_faces] + [tuple(f) for f in faces]
    nfix = len(fixed_faces)
    # edge -> list of (face index, direction)
    edges = defaultdict(list)
    for fi, f in enumerate(allf):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            edges[(min(a, b), max(a, b))].append((fi, a, b))
    flipped = [False] * len(allf)
    visited = [False] * len(allf)
    q = deque()
    for fi in range(nfix):
        visited[fi] = True
    # seed BFS with fixed faces adjacent to new faces
    seeds = set()
    for e, lst in edges.items():
        if any(fi >= nfix for fi, _, _ in lst):
            for (fi, a, b) in lst:
                if fi < nfix:
                    seeds.add(fi)
    q = deque(sorted(seeds))
    # BFS over all faces (fixed faces are never flipped)
    seen_q = set(q)
    while q:
        fi = q.popleft()
        f = allf[fi]
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            if flipped[fi]:
                a, b = b, a                      # effective direction of an already-flipped face
            e = (min(a, b), max(a, b))
            for (fj, c, d) in edges[e]:
                if fj == fi:
                    continue
                # orientation of neighbor edge as stored (after possible flip)
                if visited[fj]:
                    continue
                # consistent orientation: neighbor should traverse edge in opposite direction (b->a)
                cj, dj = (d, c) if flipped[fj] else (c, d)
                if (cj, dj) == (a, b):
                    flipped[fj] = True
                visited[fj] = True
                if fj not in seen_q:
                    seen_q.add(fj); q.append(fj)
    out = []
    for fi in range(nfix, len(allf)):
        f = allf[fi]
        out.append(tuple(reversed(f)) if flipped[fi] else f)
    return out, visited


def check_manifold(faces):
    """faces: list of tuples. returns (n_edges, n_boundary, n_nonmanifold, n_bad_orient)"""
    e = defaultdict(list)
    for f in faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e[(min(a, b), max(a, b))].append((a, b))
    bnd = sum(1 for v in e.values() if len(v) == 1)
    nm = sum(1 for v in e.values() if len(v) > 2)
    bad = sum(1 for v in e.values() if len(v) == 2 and v[0] == v[1])
    return len(e), bnd, nm, bad
