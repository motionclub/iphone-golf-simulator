"""Court sneaker v2 (low-top, chunky cupsole) - built per foot in a foot-aligned local frame (toe = -y, heel = +y, sole plane z = 0).

Upper   : per-z-slice convex hulls of the foot (a "last"): smooth toe box, no toe bumps, flat insole, then offset + collar/throat cut.
Sole    : explicit cup sole (hull outline + small lip, near-vertical wall, rounded top edge, toe spring, herringbone tread).
Details : padded collar roll + collar stitch, tongue, 5 lace rows with eyestays/eyelets, toe cap, quarter + heel counter seams, heel tab.
No logos, no stripes, no text.  Left shoe = right pipeline on the mirrored body (so each foot gets its own fit).
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from kit_common import *

PS = {
    'male': dict(set='male', which=['male_authority'], h=0.0090, sole_h=0.0285, sole_top=0.0045, insole_z=-0.0065, z_top=0.215,
                 e_up=0.0112, e_toe=0.0030, e_heel=0.0015, e_toe_up=0.0100, lip=0.0042, z_w=0.040,
                 z_collar_side=0.088, z_collar_back=0.106, z_collar_front=0.118, open_a=0.062, open_b=0.052, tongue_w=0.050, n_rows=5,
                 collar_r=0.0050, tab_h=0.012, u_drop=0.014),
    'female': dict(set='female', which=['female_arms_cand'], h=0.0085, sole_h=0.0245, sole_top=0.0040, insole_z=-0.0070, z_top=0.185,
                   e_up=0.0105, e_toe=0.0026, e_heel=0.0013, e_toe_up=0.0085, lip=0.0038, z_w=0.032,
                   z_collar_side=0.078, z_collar_back=0.093, z_collar_front=0.104, open_a=0.054, open_b=0.044, tongue_w=0.042, n_rows=5,
                   collar_r=0.0044, tab_h=0.010, u_drop=0.011),
    'female_auth': dict(set='female', which=['female_authority'], h=0.0085, sole_h=0.0235, sole_top=0.0040, insole_z=-0.0070, z_top=0.185,
                        e_up=0.0102, e_toe=0.0024, e_heel=0.0012, e_toe_up=0.0080, lip=0.0036, z_w=0.030,
                        z_collar_side=0.076, z_collar_back=0.091, z_collar_front=0.101, open_a=0.050, open_b=0.042, tongue_w=0.038, n_rows=5,
                        collar_r=0.0042, tab_h=0.009, u_drop=0.010),
}
SOLE_LIFT = {'male': 0.0285, 'female': 0.0245, 'female_auth': 0.0235}
SHOE_WALL = 0.0036


# ------------------------------------------------------------------------------------------------ 2D helpers
def convex_hull(pts):
    pts = sorted(set(map(tuple, np.round(pts, 5).tolist())))
    if len(pts) <= 2:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def sd_convex_polygon(H, X, Y):
    """signed distance (negative inside) of a CCW convex polygon H (n,2) at grid points X (nx,1,1), Y (1,ny,1) -> (nx,ny,1)."""
    px = np.broadcast_to(X, (X.shape[0], Y.shape[1], 1)).astype(np.float64)
    py = np.broadcast_to(Y, (X.shape[0], Y.shape[1], 1)).astype(np.float64)
    n = len(H)
    d = np.full(px.shape, 1e9)
    inside = np.ones(px.shape, bool)
    for i in range(n):
        a, b = H[i], H[(i + 1) % n]
        e = b - a
        L2 = e @ e
        t = np.clip(((px - a[0]) * e[0] + (py - a[1]) * e[1]) / L2, 0, 1)
        dx = px - (a[0] + t * e[0])
        dy = py - (a[1] + t * e[1])
        d = np.minimum(d, np.sqrt(dx * dx + dy * dy))
        inside &= ((e[0] * (py - a[1]) - e[1] * (px - a[0])) >= 0)
    return np.where(inside, -d, d).astype(np.float32)


def resample_closed(P, n):
    Pc = np.concatenate([P, P[:1]])
    seg = np.linalg.norm(np.diff(Pc, axis=0), axis=1)
    c = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, c[-1], n, endpoint=False)
    return np.stack([np.interp(t, c, Pc[:, a]) for a in range(Pc.shape[1])], 1)


def gauss_axis(F, sigma_vox, axis):
    if sigma_vox <= 0:
        return F
    k, r = gauss_kernel(sigma_vox)
    pad = [(0, 0)] * 3
    pad[axis] = (r, r)
    Pp = np.pad(F, pad, mode='edge')
    acc = np.zeros_like(F)
    for j, w in enumerate(k):
        sl = [slice(None)] * 3
        sl[axis] = slice(j, j + F.shape[axis])
        acc += w * Pp[tuple(sl)]
    return acc


def foot_frame(V, side=+1):
    """origin O (footprint centroid at z=0) and rotation R taking world -> local so that the foot axis points to -y."""
    m = (V[:, 0] * side > 0.02) & (V[:, 2] < 0.035)
    P = V[m][:, :2]
    c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c, full_matrices=False)
    ax = vt[0]
    if ax[1] > 0:
        ax = -ax
    phi = np.arctan2(ax[0], -ax[1])
    cp, sp = np.cos(phi), np.sin(phi)
    R = np.array([[cp, -sp, 0], [sp, cp, 0], [0, 0, 1.0]])
    a2 = R[:2, :2] @ ax
    if abs(a2[0]) > 1e-6:
        R = R.T
    O = np.array([c[0], c[1], 0.0])
    return O, R, float(np.degrees(phi))


def to_world(Vl, O, R):
    return Vl @ R + O          # inverse of (p-O) @ R.T


# ------------------------------------------------------------------------------------------------ sole
def build_sole(H, P, y_toe, y_heel, k, n_out=64, fp_pts=None):
    """explicit cup sole: smoothed hull outline offset, rounded wall, flat ledge, toe spring, bottom face. Local frame."""
    L = y_heel - y_toe
    cxy0 = H.mean(0)

    def e_of_y(y):
        sf = np.clip((y_heel - y) / L, 0, 1.2)
        return P['e_up'] + P['lip'] + P['e_toe'] * smoothstep(0.60, 0.98, sf) + P['e_heel'] * smoothstep(0.10, 0.0, sf)
    nd = 360
    th = 2 * np.pi * np.arange(nd) / nd
    dirs = np.stack([np.cos(th), np.sin(th)], 1)
    lo_r, hi_r = np.zeros(nd), np.full(nd, 0.35)
    for _ in range(34):
        mid = 0.5 * (lo_r + hi_r)
        pts = cxy0 + dirs * mid[:, None]
        Fv = np.diag(sd_convex_polygon(H, pts[:, 0][:, None, None], pts[:, 1][None, :, None])[:, :, 0]) - e_of_y(pts[:, 1])
        inside = Fv < 0
        lo_r = np.where(inside, mid, lo_r)
        hi_r = np.where(inside, hi_r, mid)
    dense = cxy0 + dirs * (0.5 * (lo_r + hi_r))[:, None]
    poly = resample_closed(dense, n_out)
    for _ in range(2):
        poly = 0.25 * np.roll(poly, 1, 0) + 0.5 * poly + 0.25 * np.roll(poly, -1, 0)
    tg = np.roll(poly, -1, 0) - np.roll(poly, 1, 0)
    nrm = np.stack([tg[:, 1], -tg[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    cen = poly.mean(0)
    if np.mean(np.einsum('ij,ij->i', nrm, poly - cen)) < 0:
        nrm = -nrm
    s_f = np.clip((y_heel - poly[:, 1]) / L, 0, 1.2)
    e_s = np.zeros(n_out)                                   # the outline above already contains the offset
    base = poly + nrm * e_s[:, None]
    z_top = P['sole_top']
    z_bot = -P['sole_h'] + 0.012 * smoothstep(0.66, 1.02, s_f) ** 2          # toe spring
    rows = [(-0.0050, 0.0), (-0.0018, 0.04), (0.0010, 0.15), (0.0028, 0.42), (0.0030, 0.72), (0.0016, 0.90), (-0.0010, 0.985),
            (-0.0042, 1.0), (-0.0058, 1.0), (-0.0058, 'ins')]
    V = []
    J = len(rows)
    z_ins = P['insole_z']
    for off, t in rows:
        for i in range(n_out):
            xy = base[i] + nrm[i] * off
            z = z_ins if t == 'ins' else z_bot[i] * (1 - t) + z_top * t
            V.append((xy[0], xy[1], z))
    V = np.array(V)
    F = []
    for j in range(J - 1):
        for i in range(n_out):
            i2 = (i + 1) % n_out
            a, b, c, d = j * n_out + i, j * n_out + i2, (j + 1) * n_out + i2, (j + 1) * n_out + i
            F += [(a, b, c), (a, c, d)]
    ring0 = V[:n_out]
    rings = [ring0]
    cxy = ring0[:, :2].mean(0)
    for f in (0.72, 0.45, 0.20):
        r = ring0.copy()
        r[:, :2] = cxy + (ring0[:, :2] - cxy) * f
        sf = np.clip((y_heel - r[:, 1]) / L, 0, 1.2)
        r[:, 2] = -P['sole_h'] + 0.012 * smoothstep(0.66, 1.02, sf) ** 2
        rings.append(r)
    base_idx = len(V)
    V = np.concatenate([V] + rings[1:])
    allr = [np.arange(n_out)] + [base_idx + q * n_out + np.arange(n_out) for q in range(len(rings) - 1)]
    for q in range(len(allr) - 1):
        for i in range(n_out):
            i2 = (i + 1) % n_out
            a, b, c, d = allr[q][i], allr[q][i2], allr[q + 1][i2], allr[q + 1][i]
            F += [(a, c, b), (a, d, c)]
    cidx = len(V)
    sfc = float(np.clip((y_heel - cxy[1]) / L, 0, 1.2))
    V = np.vstack([V, [[cxy[0], cxy[1], -P['sole_h'] + 0.012 * float(smoothstep(0.66, 1.02, sfc)) ** 2]]])
    last = allr[-1]
    for i in range(n_out):
        i2 = (i + 1) % n_out
        F += [(last[i], cidx, last[i2])]
    top = (J - 1) * n_out + np.arange(n_out)
    tcen = len(V)
    V = np.vstack([V, [[cxy[0], cxy[1], z_ins]]])
    for i in range(n_out):
        i2 = (i + 1) % n_out
        F += [(top[i], top[i2], tcen)]
    F = np.array(F)
    cs = V.mean(0)
    fc = V[F].mean(1)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    bad = np.einsum('ij,ij->i', fn, fc - cs) < 0
    if bad.sum() > 0.5 * len(F):
        F = F[:, [0, 2, 1]]
    N = vertex_normals(V, F)
    return V, F, N


# ------------------------------------------------------------------------------------------------ upper
def layer_hulls(Vl, F0, zs, xr, yr, z_w=0.040):
    hulls = []
    last = None
    for z in zs:
        pts = []
        for Pp in slice_plane(Vl, F0, 2, float(z)):
            if len(Pp) < 4:
                continue
            c = Pp.mean(0)
            if xr[0] <= c[0] <= xr[1] and yr[0] <= c[1] <= yr[1]:
                pts.append(Pp[:, :2])
        if pts:
            H = convex_hull(np.concatenate(pts))
            if len(H) >= 3:
                if np.cross(H[1] - H[0], H[2] - H[1]) < 0:
                    H = H[::-1]
                last = H
        hulls.append(last)
    first = next(h for h in hulls if h is not None)
    hulls = [h if h is not None else first for h in hulls]
    # vertical lower upper: below z_w every layer includes the (wider) layers above it up to z_w
    iw = int(np.argmin(np.abs(np.asarray(zs) - z_w)))
    acc_pts = hulls[iw].copy()
    for kk in range(iw - 1, -1, -1):
        acc_pts = np.concatenate([acc_pts, hulls[kk]])
        H = convex_hull(acc_pts)
        if np.cross(H[1] - H[0], H[2] - H[1]) < 0:
            H = H[::-1]
        hulls[kk] = H
        acc_pts = H
    return hulls


def build_shoe(gender, side=+1, verbose=True):
    P = PS[gender]
    t0 = time.time()
    bodies = load_set(P['set'], which=P['which'])
    if side < 0:                                   # left shoe = right-foot pipeline on the mirrored body
        for b in bodies:
            b['V'] = b['V'] * np.array([-1, 1, 1])
            b['F'] = b['F'][:, [0, 2, 1]]
            b['tree'] = bvh_from(b['V'], b['F'])
    b = bodies[0]
    V0, F0 = b['V'], b['F']
    O, R, phi = foot_frame(V0, +1)
    Vl = (V0 - O) @ R.T
    tree = bvh_from(Vl, F0)
    m = (Vl[:, 0] > -0.06) & (Vl[:, 0] < 0.22) & (V0[:, 0] > 0.02) & (Vl[:, 2] < 0.25)
    ext_lo, ext_hi = Vl[m].min(0), Vl[m].max(0)
    fm = (Vl[:, 2] < 0.035) & (V0[:, 0] > 0.02)
    y_toe, y_heel = Vl[fm, 1].min(), Vl[fm, 1].max()
    L = y_heel - y_toe
    k = L / 0.305
    if verbose:
        print(f'  foot frame: toe-out {phi:.1f} deg, L {L:.3f}, y_toe {y_toe:.3f}, y_heel {y_heel:.3f}, x ext {ext_lo[0]:.3f}..{ext_hi[0]:.3f}')
    lo = (ext_lo[0] - 0.05, y_toe - 0.06, -0.06)
    hi = (ext_hi[0] + 0.05, y_heel + 0.06, P['z_top'])
    g = Grid(lo, hi, P['h'])
    X, Y, Z = g.coords()
    zs = lo[2] + P['h'] * np.arange(g.n[2])
    hulls = layer_hulls(Vl, F0, zs, (lo[0], hi[0]), (lo[1], hi[1]), z_w=P['z_w'])
    D = np.empty(tuple(g.n), np.float32)
    for kk, H in enumerate(hulls):
        D[:, :, kk] = sd_convex_polygon(H, X, Y)[:, :, 0]
    s_f = np.clip((y_heel - Y) / L, 0, 1.2)
    e_xy = P['e_up'] + P['e_toe'] * smoothstep(0.60, 0.98, s_f) + P['e_heel'] * smoothstep(0.10, 0.0, s_f)
    e_up_z = P['e_toe_up'] * smoothstep(0.62, 0.95, s_f) * smoothstep(0.012, 0.030, Z) * smoothstep(0.080, 0.050, Z)      # tall toe box
    U = (D - e_xy - e_up_z).astype(np.float32)
    U = gauss_axis(U, 0.011 / P['h'], 2)
    Ua = gauss3(U, 0.0045 / P['h'])
    Ub = gauss3(U, 0.016 / P['h'])                              # heavy blur in the toe region: round plan view, no square corners
    w_toe = smoothstep(0.50, 0.82, s_f)
    U = (Ua * (1 - w_toe) + Ub * w_toe).astype(np.float32)
    fp = Vl[(Vl[:, 2] < P['z_w'] + 0.012) & (V0[:, 0] > 0.02)][:, :2]
    H0 = convex_hull(fp)
    if np.cross(H0[1] - H0[0], H0[2] - H0[1]) < 0:
        H0 = H0[::-1]
    S = body_sdf([tree], g, band=0.10, verbose=False)          # keep a minimum clearance from the real foot
    U = np.minimum(U, S - (P['e_up'] - 0.0004)).astype(np.float32)
    Vq, Q = surface_nets(U, g)
    T = quads_to_tris(Vq, Q)
    Vq = taubin(Vq, T, 4)
    if verbose:
        print(f'  shoe envelope raw tris {len(T)} ({time.time()-t0:.1f}s)')
    ankle = Vl[(Vl[:, 2] > 0.14) & (Vl[:, 2] < 0.20) & (V0[:, 0] > 0.02)]
    cA = ankle[:, :2].mean(0)
    cy0 = cA[1] - 0.004

    def cut(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        y_f = cy0 - P['open_a']
        zc = (P['z_collar_side'] + (P['z_collar_back'] - P['z_collar_side']) * smoothstep(cy0 + 0.02, cy0 + 0.065, y)
              + (P['z_collar_front'] - P['z_collar_side']) * smoothstep(cy0 - 0.01, y_f, y))
        zc = zc - P['u_drop'] * smoothstep(cy0 + 0.005, cy0 + 0.050, y) * smoothstep(0.010, 0.040, np.abs(x - cA[0]))
        c_open = np.minimum(y - y_f, z - zc)
        z_cap = P['z_collar_front'] + 0.02 + 1.2 * np.maximum(0.0, (y_f - 0.035) - y)      # trims the shin shell only; never the toe box
        c_chimney = z - z_cap
        c_low = 0.0035 - z                                        # the upper ends inside the sole
        return np.maximum.reduce([c_open, c_chimney, c_low])
    c = cut(Vq)
    V2, F2, _, _ = clip_mesh(Vq, T, c)
    V2, F2 = keep_largest(V2, F2)
    V2 = smooth_boundaries(V2, F2, iters=6)
    res = dict(fp=fp, hull=H0, V=V2, F=F2, grid=g, field=U, frame=(O, R, phi), L=L, k=k, y_toe=y_toe, y_heel=y_heel, cA=cA, cy0=cy0,
               y_f=cy0 - P['open_a'], params=P, tree_local=tree, Vlocal_body=Vl, F_body=F0)
    if verbose:
        print(f'  shoe shell tris {len(F2)} loops {[len(l) for l in boundary_loops(F2)]} ({time.time()-t0:.1f}s)')
    return res


# ------------------------------------------------------------------------------------------------ strips / rolls
def sweep_strip(acc, path, width, thick, mat=0, tag='strip', enforce_trees=None, c_min=0.0065, sock_tree=None, round_edges=0.55, end_round=0.0, face_y=-1.0):
    """padded strip swept along `path` (n,3); width along x; thickness along the path normal; edges rounded; optional rounded end."""
    path = np.asarray(path, float)
    n = len(path)
    width = np.broadcast_to(np.asarray(width, float), (n,)).copy()
    if end_round > 0:
        s = np.linspace(0, 1, n)
        w_end = np.sqrt(np.clip(1.0 - np.clip((s - (1 - end_round)) / end_round, 0, 1) ** 2, 0.04, 1.0))
        width *= w_end
    tg = np.zeros_like(path)
    tg[1:-1] = path[2:] - path[:-2]
    tg[0] = path[1] - path[0]
    tg[-1] = path[-1] - path[-2]
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    lat = np.array([1.0, 0, 0])
    nrm = np.cross(lat, tg)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    flip = (nrm[:, 1] * face_y) < 0
    nrm[flip] *= -1
    lf = np.linspace(-0.5, 0.5, 7)
    hh = 1.0 - (1.0 - round_edges) * (np.abs(lf) * 2) ** 3
    prof = [(l, 0.0) for l in lf] + [(l, h_) for l, h_ in zip(lf[::-1], hh[::-1])]
    npf = len(prof)
    V = []
    for i in range(n):
        for l, tf in prof:
            V.append(path[i] + lat * l * width[i] + nrm[i] * tf * thick)
    V = np.array(V)
    F = []
    for i in range(n - 1):
        for j in range(npf):
            j2 = (j + 1) % npf
            a, b, c, d = i * npf + j, (i + 1) * npf + j, (i + 1) * npf + j2, i * npf + j2
            F += [(a, b, c), (a, c, d)]
    F = np.array(F)
    sec_c = V.reshape(n, npf, 3).mean(1)
    fc = V[F].mean(1)
    kk = np.minimum(F[:, 0] // npf, n - 1)
    fnrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    if np.einsum('ij,ij->i', fnrm, fc - sec_c[kk]).sum() < 0:         # the (path x profile) grid has one uniform winding: flip it once, globally
        F = F[:, [0, 2, 1]]
    # end caps: fan from a centre vertex (a fan from a corner of the straight bottom row is zero-area and leaves T-junctions).  The winding is taken
    # from the body's own directed edges (each shared edge must be traversed in the opposite direction), so it is consistent by construction.
    body_dir = set()
    for f in F.tolist():
        body_dir.update(((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
    Vc = [V]
    cap_faces = []
    nvt = len(V)
    for base in (0, (n - 1) * npf):
        ctr = V[base:base + npf].mean(0)
        ci = nvt
        nvt += 1
        Vc.append(ctr[None, :])
        for j in range(npf):
            x, y = base + j, base + (j + 1) % npf
            cap_faces.append([ci, x, y] if (y, x) in body_dir else [ci, y, x])
    V = np.concatenate(Vc)
    F = np.concatenate([F, np.array(cap_faces)])
    if enforce_trees is not None:
        V = enforce_clearance(V, F, enforce_trees, c_min, iters=6, verbose=False)
    if sock_tree is not None:
        V = enforce_clearance(V, F, [sock_tree], 0.0025, iters=6, verbose=False)
    N = vertex_normals(V, F)
    acc.add(V, F, N, mat, tag)


def add_roll(acc, V, F, loop, radius, mat=0, tag='roll', sides=6, spacing=0.0075, out_shift=0.25):
    """padded rolled edge: tube of `radius` along a boundary loop (centre pushed slightly outward along the sheet normal)."""
    P0 = V[loop]
    seglen = np.linalg.norm(np.diff(np.vstack([P0, P0[:1]]), axis=0), axis=1).sum()
    P = resample_closed(P0, max(16, int(seglen / spacing)))
    surf_tmp = Surface(V, F)
    loc, nrm = surf_tmp.nearest(P)
    n = len(P)
    tg = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    cen = P + nrm * (out_shift * radius)
    Vt, Nt = [], []
    for i in range(n):
        a = np.cross(tg[i], nrm[i])
        a /= np.linalg.norm(a)
        bvec = np.cross(tg[i], a)
        for s in range(sides):
            ang = 2 * np.pi * s / sides
            d = a * np.cos(ang) + bvec * np.sin(ang)
            Vt.append(cen[i] + d * radius)
            Nt.append(d)
    Vt = np.array(Vt)
    Nt = np.array(Nt)
    Ft = []
    for i in range(n):
        i2 = (i + 1) % n
        for s in range(sides):
            s2 = (s + 1) % sides
            Ft += [(i * sides + s, i2 * sides + s, i2 * sides + s2), (i * sides + s, i2 * sides + s2, i * sides + s2)]
    Ft = np.array(Ft)
    sec_c = Vt.reshape(n, sides, 3).mean(1)
    fc = Vt[Ft].mean(1)
    kk = Ft[:, 0] // sides
    fn = np.cross(Vt[Ft[:, 1]] - Vt[Ft[:, 0]], Vt[Ft[:, 2]] - Vt[Ft[:, 0]])
    bad = np.einsum('ij,ij->i', fn, fc - sec_c[kk]) < 0
    if bad.sum() > 0.5 * len(Ft):
        Ft = Ft[:, [0, 2, 1]]
    acc.add(Vt, Ft, Nt, mat, tag)
    return P


# ------------------------------------------------------------------------------------------------ finishing
def finish_shoe(res, gender, side=+1, verbose=True):
    """details on the shoe in the local frame; returns merged (V,F,N,M,tags) in LOCAL coordinates."""
    P = res['params']
    k = res['k']
    V, F = res['V'], res['F']
    g, E = res['grid'], res['field']
    tree_body = res['tree_local']
    sock_tree = None
    sfile = f"{WORK}/data/sock{'R' if side > 0 else 'L'}_{gender}.npz"
    if os.path.exists(sfile):
        sk = np.load(sfile)
        O_, R_, _ = res['frame']
        skV, skF = sk['V'], sk['F']
        if side < 0:
            skV, skF = skV * np.array([-1, 1, 1]), skF[:, [0, 2, 1]]
        skVl = (skV - O_) @ R_.T
        sock_tree = bvh_from(skVl, skF)
    V = enforce_clearance(V, F, [tree_body], P['e_up'] - 0.0030, iters=5, verbose=False)
    if sock_tree is not None:
        V = enforce_clearance(V, F, [sock_tree], 0.0025 + SHOE_WALL, iters=8, verbose=False)       # outer face >= sock + 2.5 mm + wall  ->  inner wall >= 2.5 mm off the sock
        V = resolve_overlaps(V, F, [(skVl, skF)], step=0.002, iters=10, verbose=False)
    N = vertex_field_normals(g, E, V)
    acc = Acc()
    loops = boundary_loops(F)
    # closed upper: outer sheet + 3.6 mm inner wall + bullnose rims on every opening (the lower edge is buried in the sole)
    add_closed_shell(acc, V, F, N, SHOE_WALL, 0, tag='sheet')
    surf = Surface(V, F, g, E)
    Vs_, Fs_, Ns_ = build_sole(res['hull'], P, res['y_toe'], res['y_heel'], k, fp_pts=res['fp'])
    acc.add(Vs_, Fs_, Ns_, 0, 'sole')
    surf_sole = Surface(Vs_, Fs_)
    y_toe, y_heel, y_f, cy0 = res['y_toe'], res['y_heel'], res['y_f'], res['cy0']
    L = res['L']
    cl = [l for l in loops if V[l][:, 2].mean() >= 0.02]
    for l in cl:                                                            # padded collar roll along the opening edge
        add_roll(acc, V, F, l, P['collar_r'], 0, 'collar_roll')
    if cl:                                                                  # collar stitch (tone on tone) below the roll
        Pc = resample_closed(V[cl[0]], 56) - np.array([0, 0, 0.0085])
        ribbon(acc, surf, Pc, 0.0022, 0.0006, 0, spacing=0.009, closed=True, tag='collar_stitch')

    def top_z(x, y):
        l, n, idx, d = surf.tree.ray_cast([x, y, 0.4], [0, 0, -1])
        return (None if idx is None else l[2])

    ys = np.linspace(y_toe + 0.05 * L, y_f, 24)                             # instep ridge line x_r(y)
    xr = []
    for y in ys:
        best = (-1, 0.0)
        for x in np.linspace(-0.045, 0.045, 31):
            z = top_z(x, y)
            if z is not None and z > best[0]:
                best = (z, x)
        xr.append(best[1])
    xr = np.array(xr)
    xr = np.convolve(np.pad(xr, 3, mode='edge'), np.ones(7) / 7, mode='valid')
    x_r = lambda y: float(np.interp(y, ys, xr))
    n_rows = P['n_rows']                                                    # lace rows
    step = 0.0195 * k
    row_y = [y_f - 0.018 * k - i * step for i in range(n_rows)]
    half = 0.0195 * k
    eye = []
    for y in row_y:
        pts = []
        for x in (x_r(y) - half, x_r(y) + half):
            l, n, idx, d = surf.tree.ray_cast([x, y, 0.4], [0, 0, -1])
            pts.append(np.array(l))
        eye.append(pts)
    for col in (0, 1):
        ctrl = [np.array([e[col][0], e[col][1], 0.4]) for e in eye]
        ctrl = [np.array([ctrl[0][0], row_y[0] + 0.012 * k, 0.4])] + ctrl + [np.array([ctrl[-1][0], row_y[-1] - 0.014 * k, 0.4])]
        ribbon(acc, surf, ctrl, 0.0115 * k, 0.0013, 0, spacing=0.0075, taper_end=0.006, tag='eyestay', ray=(0, 0, -1))
    for i in range(n_rows - 1):
        for (a, b, lift) in ((0, 1, 0.0018), (1, 0, 0.0031)):
            p0, p1 = eye[i][a], eye[i + 1][b]
            mid = (p0 + p1) / 2
            ctrl = [np.array([p0[0], p0[1], 0.4]), np.array([mid[0], mid[1], 0.4]), np.array([p1[0], p1[1], 0.4])]
            ribbon(acc, surf, ctrl, 0.0050 * k, lift, 0, spacing=0.0075, taper_end=0.0, tag='lace', ray=(0, 0, -1))
    top = eye[0]
    ribbon(acc, surf, [np.array([top[0][0], top[0][1], 0.4]), np.array([x_r(row_y[0]), row_y[0] + 0.001, 0.4]), np.array([top[1][0], top[1][1], 0.4])],
           0.0050 * k, 0.0022, 0, spacing=0.0075, tag='lace_top', ray=(0, 0, -1))
    for pts in eye:
        for p in pts:
            _, nrm = surf.nearest(p[None, :])
            dome(acc, p + nrm[0] * 0.0006, nrm[0], 0.0034 * k, 0.0017, 0, seg=6, rings=1, tag='eyelet')
    # padded tongue standing up between the quarters (rounded top)
    xt = x_r(y_f)

    def shin_front(z):
        l, n, idx, d = tree_body.ray_cast([xt, -0.30, z], [0, 1, 0])
        return float(l[1]) if idx is not None else cy0 - 0.066
    z_cf = P['z_collar_front']
    lz = surf.tree.ray_cast([xt, y_f - 0.050 * k, 0.4], [0, 0, -1])[0]
    path = [np.array([xt, y_f - 0.050 * k, lz[2] + 0.0012])]
    for z in [z_cf - 0.016, z_cf - 0.002, z_cf + 0.010, z_cf + 0.021]:
        path.append(np.array([xt, shin_front(z) - 0.0085, z]))
    path = catmull(np.array(path), 0.005)
    wid = np.interp(np.linspace(0, 1, len(path)), [0, 1], [P['tongue_w'], P['tongue_w'] * 1.20])
    sweep_strip(acc, path, wid, 0.0060, 0, 'tongue', enforce_trees=[tree_body], c_min=0.0068, sock_tree=sock_tree, end_round=0.22)
    # heel tab (pull loop) rising above the collar at the back: placed from the real back surface of the sock / leg at each height
    zb = P['z_collar_back']
    cx = res['cA'][0]
    ref_tree = sock_tree if sock_tree is not None else tree_body

    def back_y(z):
        l, n, idx, d = ref_tree.ray_cast([cx, 0.40, z], [0, -1, 0])
        return float(l[1]) if idx is not None else res['cA'][1] + 0.05
    tz = [zb - 0.018, zb - 0.006, zb + 0.004, zb + P['tab_h']]
    tab = np.array([[cx, back_y(z) + 0.0042, z] for z in tz])
    tab = catmull(tab, 0.004)
    sweep_strip(acc, tab, 0.016 * k, 0.0040, 0, 'heel_tab', enforce_trees=[tree_body], c_min=0.0062, sock_tree=sock_tree, end_round=0.30, face_y=+1.0)
    # panel seams (tone on tone; deliberately NOT parallel stripes)
    y_cap = y_toe + 0.185 * L
    for loopP in slice_plane(V, F, 1, y_cap)[:1]:
        pl = loopP[loopP[:, 2] > 0.012]
        pl = pl[np.argsort(pl[:, 0])]
        ribbon(acc, surf, pl[::max(1, len(pl) // 14)], 0.0030, 0.0009, 0, spacing=0.0075, taper_end=0.006, tag='toecap')
    y_hc = y_heel - 0.062 * k
    for loopP in slice_plane(V, F, 1, y_hc)[:1]:
        pl = loopP[loopP[:, 2] > 0.020]
        pl = pl[np.argsort(pl[:, 0])]
        ribbon(acc, surf, pl[::max(1, len(pl) // 14)], 0.0030, 0.0009, 0, spacing=0.0075, taper_end=0.006, tag='heelseam')
    for loopP in slice_plane(V, F, 2, P['sole_top'] + 0.011)[:1]:
        ribbon(acc, surf, loopP[::max(1, len(loopP) // 52)], 0.0030, 0.0009, 0, spacing=0.0085, closed=True, tag='foxing')
    for sgn in (+1, -1):          # one curved quarter seam per side (from the last lace row down toward the sole)
        ctrl = [(0.0, row_y[-1] + 0.004 * k, 0.075), (0.0, row_y[-1] + 0.030 * k, 0.050), (0.0, row_y[-1] + 0.062 * k, 0.034), (0.0, row_y[-1] + 0.092 * k, 0.024)]
        ribbon(acc, surf, [np.array(c) for c in ctrl], 0.0030, 0.0009, 0, spacing=0.0075, taper_end=0.008, tag='quarter', ray=(sgn, 0, 0))
    # herringbone tread (rays from below onto the sole bottom)
    H = res['hull']

    def half_width(y):
        xs = []
        n = len(H)
        for i in range(n):
            a, b = H[i], H[(i + 1) % n]
            if (a[1] - y) * (b[1] - y) < 0:
                t = (y - a[1]) / (b[1] - a[1])
                xs.append(a[0] + t * (b[0] - a[0]))
        return (min(xs), max(xs)) if len(xs) >= 2 else (0.0, 0.0)
    n_ch = 9
    y0s = np.linspace(y_toe + 0.045 * k, y_heel - 0.035 * k, n_ch)
    for y0 in y0s:
        xmin, xmax = half_width(y0)
        xm = 0.5 * (xmin + xmax)
        hw = 0.5 * (xmax - xmin) - 0.020
        if hw < 0.008:
            continue
        d = 0.5 * hw * 0.9
        ctrl = [np.array([xm - hw, y0 - d, -0.2]), np.array([xm, y0 + 0.0, -0.2]), np.array([xm + hw, y0 - d, -0.2])]
        ribbon(acc, surf_sole, ctrl, 0.0058, 0.0013, 0, spacing=0.0085, taper_end=0.006, tag='tread', ray=(0, 0, 1))
    out = finalize_acc(acc)
    out['sheet'] = (V, F)
    return out


if __name__ == '__main__':
    gender = sys.argv[sys.argv.index('--') + 1]
    for side, tag in ((+1, 'R'), (-1, 'L')):
        res = build_shoe(gender, side=side)
        fin = finish_shoe(res, gender, side=side)
        O, R, phi = res['frame']
        fin['V'] = to_world(fin['V'], O, R)
        fin['LN'] = fin['LN'] @ R
        if side < 0:
            fin = mirror_part(fin)
        topo = mesh_topology(fin['V'], fin['F'])
        fin['topo'] = topo
        save_part(f'{WORK}/data/shoe{tag}_{gender}.npz', fin)
        json.dump(dict(tris=int(len(fin['F'])), topo=topo, sheet_tris=int(len(fin['sheet'][1]))), open(f'{WORK}/data/shoe{tag}_{gender}_info.json', 'w'), indent=1)
        print(f'  shoe[{gender}] {tag}-shoe tris {len(fin["F"])} (sheet {len(fin["sheet"][1])}) topo {topo}')
