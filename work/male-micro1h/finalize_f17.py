"""Finalization on the graded head patch (final space): eye openings with margin loops + lid wall, eyeball / brow / lid-line / lip geometry,
loop carving by vertex-path snapping.  Pure numpy + python (no bpy needed except where noted)."""
import math, heapq
import numpy as np
import h1lib as H
import sculpt as S
from h1lib import K, zrow

mm = 0.001


# ------------------------------------------------------------------------------------------------------------------ graph helpers
def edge_graph(F, n):
    adj = [dict() for _ in range(n)]
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m])
            adj[a][b] = 1; adj[b][a] = 1
    return adj


def boundary_loops(F):
    """ordered boundary loops (list of vertex index lists) of a face list"""
    cnt = {}
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m])
            k = (min(a, b), max(a, b)); cnt[k] = cnt.get(k, 0) + 1
    bedges = [k for k, c in cnt.items() if c == 1]
    nxt = {}
    for a, b in bedges:
        nxt.setdefault(a, []).append(b); nxt.setdefault(b, []).append(a)
    seen = set(); loops = []
    for a, b in bedges:
        if (a, b) in seen:
            continue
        loop = [a]; prev, cur = a, b
        seen.add((min(a, b), max(a, b)))
        while cur != a:
            loop.append(cur)
            cand = [v for v in nxt[cur] if v != prev]
            if not cand:
                break
            nx_ = cand[0]
            seen.add((min(cur, nx_), max(cur, nx_)))
            prev, cur = cur, nx_
        loops.append(loop)
    return loops


# ------------------------------------------------------------------------------------------------------------------ eye openings
def margin_curve(side, n=96):
    """3D lid-margin curve for one eye (the lid edge lies lid_t in front of the eyeball shell). returns (n,3)"""
    poly = S.smooth_poly(S.eye_poly(), n=n)
    x = poly[:, 0] * side; z = poly[:, 1]
    lid_t = S.PRM['eye']['lid_t'] * mm
    y = S.eye_shell_y(np.abs(x), z, lid_t)
    return np.stack([x, y, z], axis=1)


def resample_closed(curve, n):
    seg = np.linalg.norm(np.roll(curve, -1, axis=0) - curve, axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]
    pts = np.vstack([curve, curve[:1]])
    t = np.linspace(0, L, n, endpoint=False)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], axis=1)


def carve_eyes(P, F, wall=True, verbose=False):
    """delete faces inside each eye opening, snap the hole boundary onto the lid-margin curve (uniform spacing), and add a lid-thickness wall
    (quads from the margin loop back to the eyeball shell). returns P', F', info (loops dict side -> vertex list)"""
    P = np.array(P, float).copy(); F = [list(map(int, f)) for f in F]
    poly = S.smooth_poly(S.eye_poly())
    info = {}
    newP = [P]
    nverts = len(P)
    for side in (-1, +1):
        cen = np.array([P[f].mean(axis=0) for f in F])
        d = S.poly_dist(np.abs(cen[:, 0]), cen[:, 2], poly)
        inside = (d < -0.0004) & (np.sign(cen[:, 0]) == side) & (cen[:, 1] < -0.06)
        keep = [f for f, k in zip(F, inside) if not k]
        removed = int(inside.sum())
        # hole boundary = boundary loop that touches the removed region (loop near the eye centre)
        loops = boundary_loops(keep)
        ex, ez = side * H.LM['eye_x'], H.LM['eye_z']
        best = None
        for lp in loops:
            c = P[lp].mean(axis=0)
            dd = math.hypot(c[0] - ex, c[2] - ez)
            if dd < 0.02 and (best is None or dd < best[0]):
                best = (dd, lp)
        if best is None:
            raise RuntimeError('eye hole boundary not found')
        lp = best[1]
        mc = margin_curve(side)
        N = len(lp)
        # order the loop to match the curve orientation and start at the outer corner
        Pl = P[lp]
        # project each boundary vertex to the margin polygon parameter (xz plane)
        mxz = mc[:, [0, 2]]
        tpar = np.array([np.argmin(np.hypot(mxz[:, 0] - p[0], mxz[:, 1] - p[2])) for p in Pl])
        # rotate loop so it starts at the vertex with the smallest curve index; ensure increasing direction
        start = int(np.argmin(tpar))
        order = [(start + i) % N for i in range(N)]
        tp = tpar[order]
        if np.sum(np.diff(tp) < 0) > np.sum(np.diff(tp) > 0):
            order = [(start - i) % N for i in range(N)]
        lp_ord = [lp[i] for i in order]
        res = resample_closed(mc, N)
        # align resampled points to the loop start: find shift minimizing distance
        d0 = [np.sum(np.hypot(res[(np.arange(N) + k) % N][:, 0] - P[lp_ord][:, 0], res[(np.arange(N) + k) % N][:, 2] - P[lp_ord][:, 2])) for k in range(N)]
        k0 = int(np.argmin(d0))
        res = res[(np.arange(N) + k0) % N]
        for v, p in zip(lp_ord, res):
            P[v] = p
        if wall:
            # inner loop on the eyeball shell (touching), quads between
            inner = []
            for p in res:
                y_in = float(S.eye_shell_y(np.array([abs(p[0])]), np.array([p[2]]), 0.00005)[0])
                inner.append([p[0], y_in, p[2]])
            inner = np.array(inner)
            base = len(P)
            P = np.vstack([P, inner])
            orient = []
            for i in range(N):
                a, b = lp_ord[i], lp_ord[(i + 1) % N]
                orient.append([a, b, base + (i + 1) % N, base + i])
            # keep outward normals consistent: the wall faces point into the opening (toward the eyeball); check later via normals
            keep += orient
        info[side] = dict(removed=removed, loop=lp_ord, n=N, inner_base=(len(P) - N) if wall else None)
        try:
            adj_ = edge_graph(keep, len(P))
            relax_around(P, adj_, lp_ord, _bvh(P, [f for f in keep if len(f) >= 3 and max(f) < len(P)]), rings=4, iters=6, fixed=set(range(len(P) - (N if wall else 0), len(P))))
        except Exception as ex:
            print('eye relax skipped', ex)
        F = keep
    return P, F, info


# ------------------------------------------------------------------------------------------------------------------ eyeball geometry
def eyeball_mesh(side, n_phi=32, ring_mm=(0.0, 2.2, 4.2, 5.0, 6.0, 6.8, 7.6, 8.8, 9.8), n_out=4, n_back=3):
    """front polar patch (circle rings through pupil/iris/limbal, then rings out to the ellipsoid equator) + small back cap.
    returns V, F, mat (per face: 0 sclera, 1 iris, 2 pupil, 3 limbal(dark iris edge))"""
    e = S.EYEBALL
    cz = H.LM['eye_z']
    cxs = side * e['cx']
    ax, ay, az = e['ax'], e['ay'], e['az']
    ix, iz = side * H.LM['eye_x'], H.LM['eye_z'] + 0.0012               # iris centre (plate: pupil centre ~1.2 mm above the eye-line landmark)
    V = []; rings = []
    phi = np.linspace(0, 2 * math.pi, n_phi, endpoint=False)

    def on_shell(dx, dz):
        q = (dx / ax) ** 2 + (dz / az) ** 2
        q = np.minimum(q, 1.0)
        return np.stack([cxs + dx, e['cy'] - ay * np.sqrt(1 - q), cz + dz], axis=-1)
    # iris ring centre offset: patch centred on the iris axis (iris centre), expressed relative to the ellipsoid centre
    ox, oz = ix - cxs, iz - cz
    first = None
    for r in ring_mm:
        rr = r * mm
        if rr == 0.0:
            V.append(on_shell(np.array([ox]), np.array([oz]))[0]); rings.append([len(V) - 1]); continue
        ids = []
        for p in phi:
            V.append(on_shell(np.array([ox + rr * math.cos(p)]), np.array([oz + rr * math.sin(p)]))[0]); ids.append(len(V) - 1)
        rings.append(ids)
    # outer rings: from the last circle radius to the ellipsoid footprint (q=1) along each angle
    r0 = ring_mm[-1] * mm
    for k in range(1, n_out + 1):
        ids = []
        for p in phi:
            dirx, dirz = math.cos(p), math.sin(p)
            # footprint radius along this direction from the iris centre: solve ((ox+r dirx)/ax)^2+((oz+r dirz)/az)^2 = 1
            A = (dirx / ax) ** 2 + (dirz / az) ** 2; B = 2 * (ox * dirx / ax ** 2 + oz * dirz / az ** 2); C = (ox / ax) ** 2 + (oz / az) ** 2 - 1.0
            rmax = (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)
            rr = r0 + (rmax - r0) * (k / n_out) ** 0.9
            V.append(on_shell(np.array([ox + rr * dirx]), np.array([oz + rr * dirz]))[0]); ids.append(len(V) - 1)
        rings.append(ids)
    # back cap: rings shrinking toward a pole behind
    last = rings[-1]
    for k in range(1, n_back + 1):
        t = k / n_back
        ids = []
        for i in last:
            p = np.array(V[i])
            c = np.array([cxs, e['cy'], cz])
            q = c + (p - c) * math.cos(t * math.pi / 2)
            q[1] = e['cy'] + ay * math.sin(t * math.pi / 2)
            V.append(tuple(q)); ids.append(len(V) - 1)
        rings.append(ids)
    # everything outside the opening polygon retreats behind the skin (the lateral part of the ellipsoid would otherwise poke through the temple skin)
    Va = np.array(V); dpoly = S.poly_dist(np.abs(Va[:, 0]), Va[:, 2], S.smooth_poly(S.eye_poly()))
    Va[:, 1] += 0.014 * S.sstep(0.0, 0.0035, np.maximum(dpoly, 0.0))
    V = [tuple(v) for v in Va]
    pole = len(V); V.append((cxs, e['cy'] + ay, cz))
    F = []; mat = []
    # centre fan
    c0 = rings[0][0]
    for j in range(n_phi):
        F.append([c0, rings[1][j], rings[1][(j + 1) % n_phi]]); mat.append(2)
    r_list = list(ring_mm)
    for k in range(1, len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        if k + 1 < len(r_list):
            outer = r_list[k + 1]
            m = 2 if outer <= 4.2 else (1 if outer <= 6.8 else (3 if outer <= 7.6 else 0))
        else:
            m = 0
        for j in range(n_phi):
            F.append([a[j], a[(j + 1) % n_phi], b[(j + 1) % n_phi], b[j]]); mat.append(m)
    for j in range(n_phi):
        F.append([rings[-1][j], rings[-1][(j + 1) % n_phi], pole]); mat.append(0)
    # catchlight disc (same screen offset on both eyes: +1.3 mm right, +3.7 mm up from the iris centre), lifted 0.05 mm
    cdx, cdz = 1.4 * mm, 3.6 * mm
    base_i = len(V)
    V.append(tuple(on_shell(np.array([ox + cdx]), np.array([oz + cdz]))[0] + np.array([0, -0.00005, 0])))
    n_c = 10
    for j in range(n_c):
        p = 2 * math.pi * j / n_c
        pt = on_shell(np.array([ox + cdx + 1.7 * mm * math.cos(p)]), np.array([oz + cdz + 1.7 * mm * math.sin(p)]))[0] + np.array([0, -0.00005, 0])
        V.append(tuple(pt))
    for j in range(n_c):
        F.append([base_i, base_i + 1 + j, base_i + 1 + (j + 1) % n_c]); mat.append(4)
    return np.array(V), F, mat


# ======================================================================================================================
# LOOP CARVING by vertex-path snapping  (loops = real edge chains of the mesh lying on the feature curves)
# ======================================================================================================================
def _bvh(P, F):
    from mathutils.bvhtree import BVHTree
    tris = []
    for f in F:
        tris.append((int(f[0]), int(f[1]), int(f[2])))
        if len(f) > 3:
            tris.append((int(f[0]), int(f[2]), int(f[3])))
    return BVHTree.FromPolygons([tuple(v) for v in P], tris)


def _poly_len_params(curve):
    seg = np.linalg.norm(np.diff(curve, axis=0), axis=1)
    return np.concatenate([[0], np.cumsum(seg)])


def _project_to_polyline(pt, curve):
    """nearest point on polyline curve (M,2) to pt (2,) -> (distance, param s along the polyline, point)"""
    best = (1e9, 0.0, curve[0]); s0 = 0.0
    for i in range(len(curve) - 1):
        a, b = curve[i], curve[i + 1]
        e = b - a; L2 = float(e @ e)
        t = 0.0 if L2 < 1e-18 else float(np.clip(((pt - a) @ e) / L2, 0, 1))
        q = a + t * e
        d = float(np.hypot(*(pt - q)))
        if d < best[0]:
            best = (d, s0 + t * math.sqrt(L2), q)
        s0 += math.sqrt(L2)
    return best


def relax_around(P, adj, loop, bvh, rings=4, iters=8, w0=0.6, fixed=None):
    """tangential smoothing of the vertices within `rings` edge-steps of the loop (loop vertices fixed), each iteration projected back
    onto the pre-snap surface so the sculpted form is kept"""
    loop_set = set(loop)
    fixed = set(fixed or []) | loop_set
    levels = [set(loop)]
    seen = set(loop)
    for r in range(rings):
        nxt = set()
        for v in levels[-1]:
            for w in adj[v]:
                if w not in seen:
                    seen.add(w); nxt.add(w)
        levels.append(nxt)
    group = [v for lv in levels[1:] for v in lv if v not in fixed]
    for it in range(iters):
        upd = {}
        for v in group:
            nb = list(adj[v])
            q = (1 - w0) * P[v] + w0 * P[nb].mean(axis=0)
            hit = bvh.find_nearest(tuple(q))
            if hit[0] is not None:
                q = np.array(hit[0])
            upd[v] = q
        for v, q in upd.items():
            P[v] = q


def carve_curve(P, F, curve, plane='xz', closed=False, search=0.0045, spacing=None, lam=2.5, cand_mask=None, relax=2, bvh=None, adj=None, fixed=None, snap=True):
    """curve: (M,2) polyline in the chosen plane ('xz': coords (x,z), third axis y ; 'yz': coords (y,z), third axis x).
    Finds the vertex path hugging the curve, snaps it uniformly onto the curve, relaxes neighbours.  Returns (path, P) (P modified in place).
    cand_mask: bool array of allowed vertices."""
    ia, ib, ic = (0, 2, 1) if plane == 'xz' else (1, 2, 0)      # plane axes, third axis
    n = len(P)
    if adj is None:
        adj = edge_graph(F, n)
    curve = np.asarray(curve, float)
    if closed:
        curve = np.vstack([curve, curve[:1]])
    clen = _poly_len_params(curve)[-1]
    # candidate vertices: near the curve
    uv = P[:, [ia, ib]]
    dist = np.full(n, 1e9)
    for i in range(len(curve) - 1):
        a, b = curve[i], curve[i + 1]
        e = b - a; L2 = float(e @ e) + 1e-18
        t = np.clip(((uv - a) @ e) / L2, 0, 1)
        q = a + t[:, None] * e
        dist = np.minimum(dist, np.hypot(uv[:, 0] - q[:, 0], uv[:, 1] - q[:, 1]))
    cand = dist < search
    if cand_mask is not None:
        cand &= cand_mask
    cidx = np.where(cand)[0]
    if len(cidx) == 0:
        return [], P
    cset = set(int(i) for i in cidx)
    # seeds: nearest candidate to samples spaced ~ spacing along the curve
    step = spacing or 0.0024
    ns = max(3, int(clen / step))
    seeds = []
    kd_uv = uv[cidx]
    for s in np.linspace(0, clen, ns, endpoint=not closed):
        pt = np.array([np.interp(s, _poly_len_params(curve), curve[:, 0]), np.interp(s, _poly_len_params(curve), curve[:, 1])])
        j = int(cidx[np.argmin(np.hypot(kd_uv[:, 0] - pt[0], kd_uv[:, 1] - pt[1]))])
        if not seeds or seeds[-1] != j:
            seeds.append(j)
    if closed and seeds[0] != seeds[-1]:
        seeds.append(seeds[0])
    # shortest paths between consecutive seeds
    path = [seeds[0]]
    for a, b in zip(seeds[:-1], seeds[1:]):
        if a == b:
            continue
        pq = [(0.0, a)]; best = {a: 0.0}; prev = {}
        found = False
        while pq:
            d, u = heapq.heappop(pq)
            if u == b:
                found = True; break
            if d > best.get(u, 1e9):
                continue
            for v in adj[u]:
                if v not in cset:
                    continue
                w = float(np.linalg.norm(P[u] - P[v])) + lam * dist[v]
                nd = d + w
                if nd < best.get(v, 1e9):
                    best[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
        if not found:
            continue
        seg = [b]
        while seg[-1] != a:
            seg.append(prev[seg[-1]])
        seg = seg[::-1][1:]
        path.extend(seg)
    # dedupe (keep first occurrence), drop immediate repeats
    out = []; seen = set()
    for v in path:
        if v in seen:
            continue
        seen.add(v); out.append(v)
    path = out
    if len(path) < 3:
        return path, P
    if not snap:
        return path, P
    # parameters along the curve, monotonic, then uniform reparameterisation
    prm = []
    for v in path:
        d, s, q = _project_to_polyline(P[v, [ia, ib]], curve)
        prm.append(s)
    prm = np.maximum.accumulate(np.array(prm))
    if closed:
        s_new = np.linspace(0, clen, len(path), endpoint=False)
    else:
        s_new = np.linspace(prm[0], prm[-1], len(path))
    cpar = _poly_len_params(curve)
    if bvh is None:
        bvh = _bvh(P, F)
    bvh0 = bvh
    from mathutils import Vector
    newpos = []
    for v, s in zip(path, s_new):
        u = np.interp(s, cpar, curve[:, 0]); w = np.interp(s, cpar, curve[:, 1])
        p0 = P[v].copy()
        # third coordinate from the surface at (u,w): ray along the third axis from outside
        o = np.array([0.0, 0.0, 0.0]); o[ia] = u; o[ib] = w
        d = np.zeros(3)
        if ic == 1:
            o[ic] = -1.0; d[ic] = 1.0
        else:
            o[ic] = (1.0 if p0[ic] > 0 else -1.0); d[ic] = -o[ic]
        hit = bvh.ray_cast(Vector(o.tolist()), Vector(d.tolist()), 3.0)
        pos = p0.copy(); pos[ia] = u; pos[ib] = w
        if hit[0] is not None:
            pos[ic] = hit[0][ic]
        newpos.append(pos)
    for v, p in zip(path, newpos):
        P[v] = p
    relax_around(P, adj, path, bvh0, rings=4, iters=8, fixed=fixed)
    return path, P


def mirror_curve(curve):
    c = np.array(curve, float).copy(); c[:, 0] *= -1
    return c


def _ear_curves():
    """ear loop curves in the (y,z) plane (metres): attach outline (closed), helix crest (open), concha rim (closed)"""
    ctrl = np.array([S._yz(c, r) for c, r in S.EAR_OUTLINE])
    n = len(ctrl)
    attach = S.smooth_poly(ctrl, n=100)
    # helix crest: control points from the root (index n-2) over the top (0,1,...) down to the lobe (index 10), inset 3.4 mm
    cen = ctrl.mean(axis=0)
    idx = [n - 2, n - 1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    pts = []
    for i in idx:
        p = ctrl[i]; prev = ctrl[(i - 1) % n]; nxt = ctrl[(i + 1) % n]
        t = nxt - prev; t /= np.linalg.norm(t) + 1e-18
        nrm = np.array([-t[1], t[0]])
        if np.dot(nrm, cen - p) < 0: nrm = -nrm                        # inward
        pts.append(p + nrm * 3.4 * mm)
    pts = np.array(pts)
    seg = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    tt = np.linspace(0, seg[-1], 40)
    helix = np.stack([np.interp(tt, seg, pts[:, 0]), np.interp(tt, seg, pts[:, 1])], axis=1)
    cy, cz = S._yz(647.5, 189.5)
    th = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    concha = np.stack([cy + 8.2 * mm * np.cos(th), cz + 11.5 * mm * np.sin(th)], axis=1)
    return attach, helix, concha


def carve_all(P, F, loops_in=None, verbose=False):
    """carve the mandatory loops; returns (P, loops dict name -> vertex list)"""
    from proxy import vertex_normals
    P = np.array(P, float)
    n = len(P)
    adj = edge_graph(F, n)
    bvh = _bvh(P, F)
    N = vertex_normals(P, F)
    loops = dict(loops_in or {})
    fixed = set()
    front = P[:, 1] < -0.10
    # ---- mouth seam (open) and lip outline (closed)
    xs = np.linspace(-0.0385, 0.0385, 40)
    seam = np.stack([xs, S.seam_z(np.abs(xs))], axis=1)
    path, P = carve_curve(P, F, seam, 'xz', closed=False, cand_mask=front, search=0.0042, spacing=0.0024, bvh=bvh, adj=adj, fixed=fixed)
    loops['mouth_seam'] = path
    fixed |= set(path)
    ub = []; lb = []
    for u in np.linspace(-1, 1, 30):
        x = u * 0.0340
        z0 = float(S.seam_z(np.array([abs(x)]))[0])
        ub.append((x, z0 + 0.0062 * max(0.0, 1 - abs(x / 0.036) ** 2.4) ** (1 / 2.4)))
        lb.append((x, z0 - 0.0094 * max(0.0, 1 - abs(x / 0.0325) ** 2.2) ** (1 / 2.2)))
    path, P = carve_curve(P, F, np.array(ub), 'xz', closed=False, cand_mask=front, search=0.0038, spacing=0.0024, lam=4.0, bvh=bvh, adj=adj, fixed=fixed)
    loops['mouth_lip_upper'] = path
    fixed |= set(path)
    path, P = carve_curve(P, F, np.array(lb), 'xz', closed=False, cand_mask=front, search=0.0038, spacing=0.0024, lam=4.0, bvh=bvh, adj=adj, fixed=fixed)
    loops['mouth_lip_lower'] = path
    fixed |= set(path)
    # ---- nostril rims
    nz = float(H.zrow(S.PRM['nostril']['row'])); nx = S.PRM['nostril']['cx'] * mm
    th = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    for sd, nm in ((-1, 'L'), (1, 'R')):
        ell = np.stack([sd * (nx + 5.6 * mm * np.cos(th)), nz + 2.7 * mm * np.sin(th)], axis=1)
        path, P = carve_curve(P, F, ell, 'xz', closed=True, cand_mask=front & (np.abs(P[:, 0]) < 0.03), search=0.0028, spacing=0.0013, lam=3.5, bvh=bvh, adj=adj, fixed=fixed)
        loops['nostril_' + nm] = path
        fixed |= set(path)
    # ---- ears
    attach, helix, concha = _ear_curves()
    for sd, nm in ((-1, 'L'), (1, 'R')):
        sidemask = (np.sign(P[:, 0]) == sd) & (np.abs(P[:, 0]) > 0.06)
        for key, curve, closed, sp in (('ear_attach_', attach, True, 0.0026), ('helix_', helix, False, 0.0024), ('concha_', concha, True, 0.0022)):
            path, P = carve_curve(P, F, curve, 'yz', closed=closed, cand_mask=sidemask, search=0.0040, spacing=sp, bvh=bvh, adj=adj, fixed=fixed)
            loops[key + nm] = path
            fixed |= set(path)
    # ---- jaw -> ear (chin underside border, up the jaw angle to the ear lobe)
    jaw = np.array([(0.014, 1.4575), (0.030, 1.4592), (0.046, 1.4640), (0.060, 1.4720), (0.068, 1.4830), (0.0715, 1.4970), (0.0735, 1.5110), (0.0765, 1.5260)])
    for sd, nm in ((-1, 'L'), (1, 'R')):
        c = jaw.copy(); c[:, 0] *= sd
        mask = (np.sign(P[:, 0]) == sd) & (P[:, 1] < 0.0) & (np.abs(N[:, 1]) < 0.92)
        path, P = carve_curve(P, F, c, 'xz', closed=False, cand_mask=mask, search=0.0050, spacing=0.0030, bvh=bvh, adj=adj, fixed=fixed, snap=False)
        loops['jaw_ear_' + nm] = path
        fixed |= set(path)
    if verbose:
        for k, v in loops.items(): print('loop', k, len(v))
    return P, loops
