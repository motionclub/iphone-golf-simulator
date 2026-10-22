"""carving of eye apertures, nostrils, mouth seam chain in chart space (vertex directions U + positions P).  All functions mutate U, P and return new F."""
import numpy as np
import fl, feat_f, carve, geo


def _surf_pts(H, xs, zs):
    P, u = H.surf_xz(xs, zs)
    return P, u


def snap_chart(H, U, P, verts, targets_xz):
    """move vertices (chart directions) so that their front-projected (x, z) equals targets; y from the surface"""
    xs = np.array([t[0] for t in targets_xz]); zs = np.array([t[1] for t in targets_xz])
    Pt, ut = H.surf_xz(xs, zs)
    for v, p, u in zip(verts, Pt, ut): U[v] = u; P[v] = p


def relax_chart(H, U, P, adj, fixed, rings=2, iters=3, lam=0.5):
    fixed = set(fixed); frontier = set(fixed); free = set()
    for _ in range(rings):
        nxt = set()
        for v in frontier:
            for w in adj[v]:
                if w not in fixed and w not in free: free.add(w); nxt.add(w)
        frontier = nxt
    free = sorted(free)
    for _ in range(iters):
        newU = {}
        for v in free:
            nb = list(adj[v]); m = U[nb].mean(axis=0); m /= np.linalg.norm(m); newU[v] = (1 - lam) * U[v] + lam * m
        for v, u in newU.items(): U[v] = u / np.linalg.norm(u)
    fr = np.array(free)
    if len(fr): P[fr] = H.phi(U[fr])
    return free


def poly_param(poly, pts):
    """arc-length parameter (and distance) of the projections of pts (m,2) onto the closed polygon poly (n,2)"""
    n = len(poly); seg = np.linalg.norm(np.roll(poly, -1, axis=0) - poly, axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    out = np.zeros(len(pts)); dist = np.zeros(len(pts))
    for i, p in enumerate(pts):
        best = (1e18, 0.0)
        for j in range(n):
            a = poly[j]; e = poly[(j + 1) % n] - a; t = np.clip(np.dot(p - a, e) / (e @ e + 1e-18), 0, 1); q = a + t * e; d = np.linalg.norm(p - q)
            if d < best[0]: best = (d, cum[j] + t * seg[j])
        dist[i] = best[0]; out[i] = best[1]
    return out, dist, cum[-1]


def poly_at(poly, s):
    n = len(poly); seg = np.linalg.norm(np.roll(poly, -1, axis=0) - poly, axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); L = cum[-1]
    s = np.mod(s, L); j = np.clip(np.searchsorted(cum, s, side='right') - 1, 0, n - 1); t = (s - cum[j]) / np.maximum(seg[j], 1e-18)
    return poly[j] + t[:, None] * (poly[(j + 1) % n] - poly[j])


def assign_loop(H, U, P, loop, curve_xz, side):
    """loop: ordered vertex ids around a hole; curve_xz: closed (|x|, z) polygon.  Each vertex is projected on the polygon, the parameters are made
    uniform (arc-length equalised), and the vertex is moved (in chart space) onto the polygon point."""
    n = len(loop)
    pts = np.column_stack([np.abs(P[loop, 0]), P[loop, 2]])
    s, dist, L = poly_param(curve_xz, pts)
    ds = np.diff(np.concatenate([s, s[:1]])); ds = (ds + L / 2) % L - L / 2          # wrapped increments
    sign = 1.0 if ds.sum() > 0 else -1.0
    steps = np.abs(ds) if sign > 0 else np.abs(ds)
    cum = np.concatenate([[0], np.cumsum(np.abs(ds))[:-1]])
    tot = np.abs(ds).sum()                                                           # ~ L when the loop winds once
    st = s[0] + sign * (np.arange(n) / n) * L
    q = poly_at(curve_xz, st)
    snap_chart(H, U, P, loop, [(side * a, b) for a, b in q])
    return float(np.sqrt(np.mean(dist ** 2)))


def carve_hole(H, U, P, F, poly_xz, side, label, shrink=0.0003, ycut=-0.02):
    """delete faces whose centre lies inside the polygon (front projection) and snap the new boundary loop onto the polygon"""
    cen = carve.face_centers(P, F)
    d = feat_f.poly_signed_dist(np.abs(cen[:, 0]), cen[:, 2], poly_xz)
    inside = (d > shrink) & (np.sign(cen[:, 0]) == side) & (cen[:, 1] < ycut)
    F2 = [f for f, k in zip(F, inside) if not k]
    loops = carve.boundary_loops(F2)
    c0 = np.array([np.mean(poly_xz[:, 0]) * side, 0, np.mean(poly_xz[:, 1])])
    best = None
    for lp in loops:
        if len(lp) < 6: continue
        m = P[lp]; dd = abs(np.hypot(m[:, 0].mean() - c0[0], m[:, 2].mean() - c0[2]))
        if best is None or dd < best[0]: best = (dd, lp)
    lp = best[1]
    rms = assign_loop(H, U, P, lp, poly_xz, side)
    return F2, lp, int(inside.sum()), rms


# ------------------------------------------------------------------------------------------------------------------------ open chains (mouth seam / lip borders / ear loops)
def poly_param_open(poly, pts):
    n = len(poly); seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    out = np.zeros(len(pts)); dist = np.zeros(len(pts))
    for i, p in enumerate(pts):
        best = (1e18, 0.0)
        for j in range(n - 1):
            a = poly[j]; e = poly[j + 1] - a; t = np.clip(np.dot(p - a, e) / (e @ e + 1e-18), 0, 1); q = a + t * e; d = np.linalg.norm(p - q)
            if d < best[0]: best = (d, cum[j] + t * seg[j])
        dist[i] = best[0]; out[i] = best[1]
    return out, dist, cum[-1]


def poly_at_open(poly, s):
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.clip(s, 0, cum[-1]); j = np.clip(np.searchsorted(cum, s, side='right') - 1, 0, len(poly) - 2); t = (s - cum[j]) / np.maximum(seg[j], 1e-18)
    return poly[j] + t[:, None] * (poly[j + 1] - poly[j])


def snap_chart_yz(H, U, P, verts, targets_yz, side):
    """move vertices (chart directions) so that the BASE surface point has the given (y, z): used for the ear (x-displacement keeps y,z)"""
    yz = np.array(targets_yz); n = len(yz)
    lo = np.full(n, 0.03); hi = np.full(n, 0.16)
    for _ in range(30):
        x = 0.5 * (lo + hi); Q = np.stack([side * x, yz[:, 0], yz[:, 1]], 1); d = Q - geo.C[None, :]; rq = np.linalg.norm(d, axis=1); u = d / rq[:, None]
        rs = np.linalg.norm(H.phi(u, parts=False) - geo.C[None, :], axis=1)
        inside = rq < rs; lo = np.where(inside, x, lo); hi = np.where(inside, hi, x)
    x = 0.5 * (lo + hi); Q = np.stack([side * x, yz[:, 0], yz[:, 1]], 1); d = Q - geo.C[None, :]; u = d / np.linalg.norm(d, axis=1, keepdims=True)
    Pn = H.phi(u)
    for v, p, uu in zip(verts, Pn, u): U[v] = uu; P[v] = p


def assign_chain(H, U, P, chain, curve2d, closed, space, side=1):
    """snap an ordered vertex chain onto a 2D curve ((|x|,z) front chart: space='xz', (y,z) ear chart: space='yz'); parameters are equalised along the chain"""
    n = len(chain)
    if space == 'xz': pts = np.column_stack([np.abs(P[chain, 0]), P[chain, 2]])
    elif space == 'xzs': pts = np.column_stack([P[chain, 0], P[chain, 2]])
    else: pts = np.column_stack([P[chain, 1], P[chain, 2]])
    if closed:
        s, dist, L = poly_param(curve2d, pts)
        ds = np.diff(np.concatenate([s, s[:1]])); ds = (ds + L / 2) % L - L / 2; sign = 1.0 if ds.sum() > 0 else -1.0
        st = s[0] + sign * (np.arange(n) / n) * L; q = poly_at(curve2d, st)
    else:
        s, dist, L = poly_param_open(curve2d, pts)
        if s[0] > s[-1]: sgn = -1.0
        else: sgn = 1.0
        st = np.linspace(s[0], s[-1], n); q = poly_at_open(curve2d, st)
    if space == 'xz': snap_chart(H, U, P, chain, [(sx * a, b) for sx, (a, b) in zip(np.sign(P[chain, 0] + 1e-12), q)])
    elif space == 'xzs': snap_chart(H, U, P, chain, [(a, b) for a, b in q])
    else: snap_chart_yz(H, U, P, chain, [(a, b) for a, b in q], side)
    return float(np.sqrt(np.mean(dist ** 2)))


def make_chain(H, U, P, F, curve3d, tol, cand_mask, closed=False):
    adj = carve.edge_adj(F, len(P))
    cand = np.where(cand_mask)[0]
    return carve.curve_chain(P, adj, curve3d, tol=tol, closed=closed, cand=cand), adj


def snap_chain_3d(H, U, P, chain, curve3d, closed=False):
    """snap an ordered chain onto a 3D polyline lying on the skin: equalise arc-length parameters, move each vertex (chart direction) to the curve point"""
    n = len(chain)
    seg = np.linalg.norm(np.diff(curve3d, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); Ltot = cum[-1]
    s = np.zeros(n)
    for i, v in enumerate(chain):
        best = (1e18, 0.0)
        for j in range(len(curve3d) - 1):
            a = curve3d[j]; e = curve3d[j + 1] - a; t = np.clip(np.dot(P[v] - a, e) / (e @ e + 1e-18), 0, 1); d = np.linalg.norm(P[v] - (a + t * e))
            if d < best[0]: best = (d, cum[j] + t * seg[j])
        s[i] = best[1]
    if s[0] > s[-1]: s = s[::-1]; chain = chain[::-1]
    st = np.linspace(s[0], s[-1], n)
    q = np.stack([np.interp(st, cum, curve3d[:, k]) for k in range(3)], axis=1)
    d = q - geo.C[None, :]; u = d / np.linalg.norm(d, axis=1, keepdims=True)
    Pn = H.phi(u)
    for v, p, uu in zip(chain, Pn, u): U[v] = uu; P[v] = p
    return float(np.sqrt(np.mean((s - st) ** 2)))
