"""mesh surgery helpers (numpy / python):  boundary loops, face removal, loop snapping, path carving, Laplacian relaxation."""
import heapq
import numpy as np


def edge_adj(F, n):
    adj = [dict() for _ in range(n)]
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); adj[a][b] = 1; adj[b][a] = 1
    return adj


def boundary_loops(F):
    cnt = {}
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); k = (min(a, b), max(a, b)); cnt[k] = cnt.get(k, 0) + 1
    be = [k for k, c in cnt.items() if c == 1]
    nxt = {}
    for a, b in be: nxt.setdefault(a, []).append(b); nxt.setdefault(b, []).append(a)
    seen = set(); loops = []
    for a, b in be:
        if (a, b) in seen: continue
        loop = [a]; prev, cur = a, b; seen.add((min(a, b), max(a, b)))
        while cur != a:
            loop.append(cur)
            cand = [v for v in nxt[cur] if v != prev]
            if not cand: break
            nx = cand[0]; seen.add((min(cur, nx), max(cur, nx))); prev, cur = cur, nx
        loops.append(loop)
    return loops


def face_centers(P, F):
    return np.array([P[f].mean(axis=0) for f in F])


def resample_closed3(curve, n):
    seg = np.linalg.norm(np.roll(curve, -1, axis=0) - curve, axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    pts = np.vstack([curve, curve[:1]]); t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], axis=1)


def snap_loop(P, loop, target):
    """assign target (closed 3D curve) to the ordered vertex loop: resample to len(loop), choose start/direction minimising the displacement"""
    n = len(loop); res = resample_closed3(target, n); L = P[loop]
    best = None
    for rev in (False, True):
        R = res[::-1] if rev else res
        for k in range(n):
            R2 = np.roll(R, -k, axis=0); e = np.sum(np.linalg.norm(R2 - L, axis=1) ** 2)
            if best is None or e < best[0]: best = (e, R2)
    for v, p in zip(loop, best[1]): P[v] = p
    return best[0] / n


def relax(P, adj, fixed, rings=3, iters=6, lam=0.5, region=None):
    """Laplacian relax of vertices within `rings` edge-rings of the fixed set (fixed stay)"""
    fixed = set(fixed); frontier = set(fixed); free = set()
    for _ in range(rings):
        nxt = set()
        for v in frontier:
            for w in adj[v]:
                if w not in fixed and w not in free: free.add(w); nxt.add(w)
        frontier = nxt
    free = sorted(free)
    for _ in range(iters):
        newP = {}
        for v in free:
            nb = list(adj[v]); newP[v] = P[v] * (1 - lam) + lam * P[nb].mean(axis=0)
        for v, p in newP.items(): P[v] = p
    return free


def dijkstra_path(P, adj, src, dst, cost_fn=None):
    dist = {src: 0.0}; prev = {}; pq = [(0.0, src)]
    while pq:
        d, v = heapq.heappop(pq)
        if v == dst: break
        if d > dist.get(v, 1e18): continue
        for w in adj[v]:
            c = np.linalg.norm(P[v] - P[w]) * (1.0 if cost_fn is None else cost_fn(w))
            nd = d + c
            if nd < dist.get(w, 1e18): dist[w] = nd; prev[w] = v; heapq.heappush(pq, (nd, w))
    path = [dst]
    while path[-1] != src: path.append(prev[path[-1]])
    return path[::-1]


def curve_chain(P, adj, curve, tol=0.004, closed=False, cand=None, cols=(0, 1, 2)):
    """vertex chain (ordered, edge-connected) following a 3D polyline: nearest vertex per sample + shortest edge paths in between."""
    cand = np.arange(len(P)) if cand is None else np.asarray(cand)
    cols = list(cols); Pc = P[:, cols]
    keys = []
    for q in curve:
        d = np.linalg.norm(Pc[cand] - q, axis=1); i = int(cand[np.argmin(d)])
        if d.min() < tol and (not keys or keys[-1] != i): keys.append(i)
    chain = [keys[0]]
    pts = list(keys[1:]) + ([keys[0]] if closed else [])
    cv = np.asarray(curve)[:, :len(cols)] if np.asarray(curve).shape[1] != len(cols) else np.asarray(curve)
    nseg = len(cv)
    def dist_curve(i):
        q = Pc[i]; d = 1e18
        for j in range(nseg - 1 + (1 if closed else 0)):
            a = cv[j]; b = cv[(j + 1) % nseg]; e = b - a; t = np.clip(np.dot(q - a, e) / (e @ e + 1e-18), 0, 1); d = min(d, np.linalg.norm(q - (a + t * e)))
        return d
    cache = {}
    def cost(w):
        if w not in cache: cache[w] = 1.0 + 6.0 * dist_curve(w) / max(tol, 1e-6)
        return cache[w]
    for k in pts:
        if k == chain[-1]: continue
        seg = dijkstra_path(P, adj, chain[-1], k, cost_fn=cost)
        chain += seg[1:]
    return chain


def project_to_polyline(p, poly, closed=False):
    best = (1e18, None)
    n = len(poly); rng = range(n) if closed else range(n - 1)
    for i in rng:
        a = poly[i]; b = poly[(i + 1) % n]; e = b - a
        t = np.clip(np.dot(p - a, e) / (e @ e + 1e-18), 0, 1); q = a + t * e; d = np.linalg.norm(p - q)
        if d < best[0]: best = (d, q)
    return best


def compact(P, F, keep_extra=()):
    """drop unreferenced vertices; returns P2, F2, old->new map (-1 for dropped)"""
    used = np.zeros(len(P), bool)
    for f in F: used[list(f)] = True
    for k in keep_extra: used[k] = True
    new = -np.ones(len(P), int); new[used] = np.arange(used.sum())
    return P[used], [[int(new[v]) for v in f] for f in F], new


def taubin(P, adj, idx, iters=5, lam=0.5, mu=-0.53, fixed=()):
    """Taubin smoothing (non-shrinking) of vertices idx (others untouched); neighbours outside idx act as anchors"""
    idx = [int(i) for i in idx if int(i) not in set(fixed)]
    for _ in range(iters):
        for factor in (lam, mu):
            newP = {}
            for v in idx:
                nb = list(adj[v])
                if not nb: continue
                newP[v] = P[v] + factor * (P[nb].mean(axis=0) - P[v])
            for v, p in newP.items(): P[v] = p
