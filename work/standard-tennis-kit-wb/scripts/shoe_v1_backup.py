"""Court sneaker (right foot; left = mirror).  Built in a foot-aligned frame (toe along -y, heel at y ~ 0) from the foot SDF."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from kit_common import *

PS = {
    'male': dict(set='male', which=['male_authority'], h=0.0100, sole_h=0.0255, e_up=0.0115, e_sole=0.0185, sole_top=0.0045, insole_z=-0.0065,
                 z_collar_back=0.118, z_collar_side=0.101, z_collar_front=0.128, open_a=0.062, open_b=0.052, tongue_w=0.050),
    'female_auth': dict(set='female', which=['female_authority'], h=0.0090, sole_h=0.0215, e_sole=0.0155, e_up=0.0100, sole_top=0.0040, insole_z=-0.0070,
                        z_collar_back=0.100, z_collar_side=0.086, z_collar_front=0.110, open_a=0.050, open_b=0.042, tongue_w=0.038),
    'female': dict(set='female', which=['female_arms_cand'], h=0.0095, sole_h=0.0225, e_sole=0.0165, e_up=0.0105, sole_top=0.0040, insole_z=-0.0070,
                   z_collar_back=0.108, z_collar_side=0.092, z_collar_front=0.118, open_a=0.054, open_b=0.044, tongue_w=0.042),
}


def foot_frame(V, side=+1):
    """origin O (footprint centroid at z=0) and rotation R (3x3) taking world -> local so that the foot axis points to -y."""
    m = (V[:, 0] * side > 0.02) & (V[:, 2] < 0.035)
    P = V[m][:, :2]
    c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c, full_matrices=False)
    ax = vt[0]
    if ax[1] > 0:
        ax = -ax
    phi = np.arctan2(ax[0], -ax[1])            # toe-out angle (positive: toes point to +x)
    cp, sp = np.cos(phi), np.sin(phi)
    R = np.array([[cp, -sp, 0], [sp, cp, 0], [0, 0, 1.0]])   # rotate by -phi: x' = x cos - ... (applied as (p-O) @ R.T)
    # check: axis -> (0,-1)
    a2 = R[:2, :2] @ ax
    if abs(a2[0]) > 1e-6:
        R = R.T
    O = np.array([c[0], c[1], 0.0])
    return O, R, float(np.degrees(phi))



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


def smax(a, b, k):
    h = np.clip(0.5 - 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h + k * h * (1 - h)


def resample_closed(P, n):
    Pc = np.concatenate([P, P[:1]])
    seg = np.linalg.norm(np.diff(Pc, axis=0), axis=1)
    c = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, c[-1], n, endpoint=False)
    return np.stack([np.interp(t, c, Pc[:, 0]), np.interp(t, c, Pc[:, 1])], 1)


def build_sole(H, P, y_toe, y_heel, k, n_out=64, fp_pts=None):
    """explicit cup sole: smoothed hull outline offset, rounded wall, flat ledge, toe spring, bottom face. Local frame."""
    L = y_heel - y_toe
    poly = resample_closed(H, n_out)
    for _ in range(40):                                   # round the hull corners
        poly = 0.25 * np.roll(poly, 1, 0) + 0.5 * poly + 0.25 * np.roll(poly, -1, 0)
    tg = np.roll(poly, -1, 0) - np.roll(poly, 1, 0)
    nrm = np.stack([tg[:, 1], -tg[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    cen = poly.mean(0)
    if np.mean(np.einsum('ij,ij->i', nrm, poly - cen)) < 0:
        nrm = -nrm
    # smoothing cut the hull corners inwards: grow the outline until it encloses every footprint point (+2 mm)
    if fp_pts is not None:
        Hs = poly if np.cross(poly[1] - poly[0], poly[2] - poly[1]) > 0 else poly[::-1]
        d_out = sd_convex_polygon(Hs, fp_pts[:, 0][:, None, None], fp_pts[:, 1][None, :, None])
        # (diagonal of the broadcast grid = distance for each point)
        worst = float(np.max(np.diag(d_out[:, :, 0])))
        if worst > -0.002:
            poly = poly + nrm * (worst + 0.002)
    s_f = np.clip((y_heel - poly[:, 1]) / L, 0, 1.2)
    e_s = P['e_sole'] + 0.0035 * smoothstep(0.75, 1.0, s_f) + 0.0015 * smoothstep(0.1, 0.0, s_f)
    base = poly + nrm * e_s[:, None]                      # outer wall (mid height)
    z_top = P['sole_top']
    z_bot = -P['sole_h'] + 0.011 * smoothstep(0.70, 1.02, s_f) ** 2
    rows = [(-0.0045, 0.0), (-0.0015, 0.05), (0.0015, 0.17), (0.0030, 0.46), (0.0026, 0.80), (0.0010, 0.93), (-0.0018, 1.0),
            (-0.0070, 1.0), (-0.0115, 1.0), (-0.0115, 'ins')]
    V, Nn = [], []
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
    # bottom face: concentric rings toward the centroid
    ring0 = V[:n_out]
    rings = [ring0]
    cxy = ring0[:, :2].mean(0)
    for f in (0.72, 0.45, 0.20):
        r = ring0.copy()
        r[:, :2] = cxy + (ring0[:, :2] - cxy) * f
        yy = r[:, 1]
        sf = np.clip((y_heel - yy) / L, 0, 1.2)
        r[:, 2] = -P['sole_h'] + 0.011 * smoothstep(0.70, 1.02, sf) ** 2
        rings.append(r)
    base_idx = len(V)
    V = np.concatenate([V] + rings[1:])
    allr = [np.arange(n_out)] + [base_idx + q * n_out + np.arange(n_out) for q in range(len(rings) - 1)]
    for q in range(len(allr) - 1):
        for i in range(n_out):
            i2 = (i + 1) % n_out
            a, b, c, d = allr[q][i], allr[q][i2], allr[q + 1][i2], allr[q + 1][i]
            F += [(a, c, b), (a, d, c)]                      # facing down
    cidx = len(V)
    V = np.vstack([V, [[cxy[0], cxy[1], -P['sole_h'] + 0.011 * float(smoothstep(0.70, 1.02, np.clip((y_heel - cxy[1]) / L, 0, 1.2))) ** 2]]])
    last = allr[-1]
    for i in range(n_out):
        i2 = (i + 1) % n_out
        F += [(last[i], cidx, last[i2])]
    # inner top: close the top ring with a fan (hidden under the upper)
    top = (J - 1) * n_out + np.arange(n_out)
    tcen = len(V)
    V = np.vstack([V, [[cxy[0], cxy[1], z_ins]]])
    for i in range(n_out):
        i2 = (i + 1) % n_out
        F += [(top[i], top[i2], tcen)]
    F = np.array(F)
    # orient: outward = away from the solid's centroid
    cs = V.mean(0)
    fc = V[F].mean(1)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    bad = np.einsum('ij,ij->i', fn, fc - cs) < 0
    if bad.sum() > 0.5 * len(F):
        F = F[:, [0, 2, 1]]
    N = vertex_normals(V, F)
    return V, F, N


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
    # right-foot extents in the local frame
    m = (Vl[:, 0] > -0.06) & (Vl[:, 0] < 0.22) & (V0[:, 0] > 0.02) & (Vl[:, 2] < 0.25)
    ext_lo, ext_hi = Vl[m].min(0), Vl[m].max(0)
    fm = Vl[:, 2] < 0.035
    fm &= V0[:, 0] > 0.02
    y_toe, y_heel = Vl[fm, 1].min(), Vl[fm, 1].max()
    L = y_heel - y_toe
    k = L / 0.305
    if verbose:
        print(f'  foot frame: toe-out {phi:.1f} deg, L {L:.3f}, y_toe {y_toe:.3f}, y_heel {y_heel:.3f}, x ext {ext_lo[0]:.3f}..{ext_hi[0]:.3f}')
    lo = (ext_lo[0] - 0.045, y_toe - 0.06, -0.06)
    hi = (ext_hi[0] + 0.045, y_heel + 0.06, 0.215)
    g = Grid(lo, hi, P['h'])
    S = body_sdf([tree], g, band=0.10, verbose=verbose)
    X, Y, Z = g.coords()
    s_f = np.clip((y_heel - Y) / L, 0, 1.2)           # 0 at the heel .. 1 at the toe tip
    # ---- upper outer envelope
    e_up = P['e_up'] + 0.0025 * smoothstep(0.65, 0.95, s_f) * smoothstep(0.075, 0.03, Z) + 0.0015 * smoothstep(0.12, 0.0, s_f)
    Ua = gauss3(S - e_up, 0.007 / P['h'])
    Ub = gauss3(S - e_up - 0.003, 0.020 / P['h'])
    w_toe = smoothstep(0.42, 0.78, s_f)
    U = (Ua * (1 - w_toe) + Ub * w_toe).astype(np.float32)
    U = np.minimum(U, S - 0.0105)
    fp = Vl[(Vl[:, 2] < 0.03) & (V0[:, 0] > 0.02)][:, :2]
    H = convex_hull(fp)
    if np.cross(H[1] - H[0], H[2] - H[1]) < 0:
        H = H[::-1]
    E = U.astype(np.float32)
    Vq, Q = surface_nets(E, g)
    T = quads_to_tris(Vq, Q)
    Vq = taubin(Vq, T, 4)
    if verbose:
        print(f'  shoe envelope raw tris {len(T)} ({time.time()-t0:.1f}s)')
    # ---- collar funnel cut
    ankle = Vl[(Vl[:, 2] > 0.14) & (Vl[:, 2] < 0.20) & (V0[:, 0] > 0.02)]
    cA = ankle[:, :2].mean(0)
    cy0 = cA[1] - 0.004
    def cut(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        y_f = cy0 - P['open_a']                                   # front edge of the opening (vamp lies in front of this plane)
        zc = (P['z_collar_side'] + (P['z_collar_back'] - P['z_collar_side']) * smoothstep(cy0 + 0.02, cy0 + 0.065, y)
              + (P['z_collar_front'] - P['z_collar_side']) * smoothstep(cy0 - 0.01, y_f, y))
        c_open = np.minimum(y - y_f, z - zc)                      # behind the front plane and above the collar surface
        z_cap = P['z_collar_front'] + 0.02 - 0.55 * np.maximum(0.0, y_f - y)
        c_chimney = z - z_cap                                      # the shin shell in front of the opening
        c_low = 0.0035 - z                                        # the upper ends inside the sole
        return np.maximum.reduce([c_open, c_chimney, c_low])
    c = cut(Vq)
    V2, F2, _, _ = clip_mesh(Vq, T, c)
    V2, F2 = keep_largest(V2, F2)
    V2 = smooth_boundaries(V2, F2, iters=5)
    Nf = None
    res = dict(fp=fp, hull=H, V=V2, F=F2, grid=g, field=E, frame=(O, R, phi), L=L, k=k, y_toe=y_toe, y_heel=y_heel, cA=cA, cy0=cy0, y_f=cy0 - P['open_a'], params=P, tree_local=tree, Vlocal_body=Vl, F_body=F0)
    if verbose:
        print(f'  shoe shell tris {len(F2)} loops {[len(l) for l in boundary_loops(F2)]} ({time.time()-t0:.1f}s)')
    return res


def to_world(Vl, O, R):
    return Vl @ R + O          # inverse of (p-O) @ R.T


def sweep_strip(acc, path, width, thick, mat=0, tag='strip', up=None, enforce_trees=None, c_min=0.0065, sock_tree=None):
    """thick flat strip (rounded-rectangle section) swept along `path` (n,3); width(n) lateral extent along x; thickness along the path normal."""
    path = np.asarray(path, float)
    n = len(path)
    width = np.broadcast_to(np.asarray(width, float), (n,))
    tg = np.zeros_like(path)
    tg[1:-1] = path[2:] - path[:-2]
    tg[0] = path[1] - path[0]
    tg[-1] = path[-1] - path[-2]
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    lat = np.array([1.0, 0, 0])
    nrm = np.cross(lat, tg)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    # make the normal point outward (toward -y, the front of the shoe): flip if it points to +y
    flip = nrm[:, 1] > 0
    nrm[flip] *= -1
    lf = np.linspace(-0.5, 0.5, 7)
    prof = [(l, 0.0) for l in lf] + [(l, 1.0) for l in lf[::-1]]          # inner face left->right, outer face right->left (closed ring)
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
    for base, rev in ((0, False), ((n - 1) * npf, True)):
        for j in range(1, npf - 1):
            t1 = (base, base + j, base + j + 1)
            F.append(t1[::-1] if rev else t1)
    F = np.array(F)
    sec_c = V.reshape(n, npf, 3).mean(1)
    fc = V[F].mean(1)
    kk = np.minimum(F[:, 0] // npf, n - 1)
    fnrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    bad = np.einsum('ij,ij->i', fnrm, fc - sec_c[kk]) < 0
    if bad.sum() > 0.5 * len(F):
        F = F[:, [0, 2, 1]]
    if enforce_trees is not None:
        V = enforce_clearance(V, F, enforce_trees, c_min, iters=6, verbose=False)
    if sock_tree is not None:
        V = enforce_clearance(V, F, [sock_tree], 0.0025, iters=6, verbose=False)
    N = vertex_normals(V, F)
    acc.add(V, F, N, mat, tag)


def finish_shoe(res, gender, side=+1, verbose=True):
    """details on the right shoe in the local frame; returns merged (V,F,N,M,tags) in LOCAL coordinates."""
    P = res['params']
    k = res['k']
    V, F = res['V'], res['F']
    g, E = res['grid'], res['field']
    tree_body = res['tree_local']
    sock_tree = None
    sfile = f"{WORK}/data/sock{'R' if side > 0 else 'L'}_{gender}.npz"   # (gender key == file suffix: male / female / female_auth)
    if os.path.exists(sfile):
        sk = np.load(sfile)
        O_, R_, _ = res['frame']
        skV, skF = sk['V'], sk['F']
        if side < 0:
            skV, skF = skV * np.array([-1, 1, 1]), skF[:, [0, 2, 1]]
        skVl = (skV - O_) @ R_.T
        sock_tree = bvh_from(skVl, skF)
    V = enforce_clearance(V, F, [tree_body], 0.0072, iters=5, verbose=False)
    if sock_tree is not None:
        V = enforce_clearance(V, F, [sock_tree], 0.0025, iters=5, verbose=False)
        V = resolve_overlaps(V, F, [(skVl, skF)], step=0.002, iters=10, verbose=False)
    N = vertex_field_normals(g, E, V)
    acc = Acc()
    add_sheet(acc, V, F, N, 0, 'sheet')
    add_rims_and_inner(acc, V, F, N, t=0.0042, depth=0.024, piped={}, skip=lambda pts: pts[:, 2].mean() < 0.02)
    surf = Surface(V, F, g, E)
    Vs_, Fs_, Ns_ = build_sole(res['hull'], P, res['y_toe'], res['y_heel'], k, fp_pts=res['fp'])
    acc.add(Vs_, Fs_, Ns_, 0, 'sole')
    surf_sole = Surface(Vs_, Fs_)
    y_toe, y_heel, y_f, cy0 = res['y_toe'], res['y_heel'], res['y_f'], res['cy0']
    L = res['L']

    def top_z(x, y):
        l, n, idx, d = surf.tree.ray_cast([x, y, 0.4], [0, 0, -1])
        return (None if idx is None else l[2])

    # ---- instep ridge line x_r(y)
    ys = np.linspace(y_toe + 0.05 * L, y_f, 24)
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
    # ---- lace rows
    n_rows = 5
    step = 0.0195 * k
    row_y = [y_f - 0.020 * k - i * step for i in range(n_rows)]
    half = 0.0195 * k
    eye = []
    for y in row_y:
        xl, xrr = x_r(y) - half, x_r(y) + half
        pts = []
        for x in (xl, xrr):
            l, n, idx, d = surf.tree.ray_cast([x, y, 0.4], [0, 0, -1])
            pts.append(np.array(l))
        eye.append(pts)
    # eyestays (raised strips along each eyelet column)
    for col in (0, 1):
        ctrl = [np.array([e[col][0], e[col][1], 0.4]) for e in eye]
        ctrl = [np.array([ctrl[0][0], row_y[0] + 0.012 * k, 0.4])] + ctrl + [np.array([ctrl[-1][0], row_y[-1] - 0.014 * k, 0.4])]
        ribbon(acc, surf, ctrl, 0.0115 * k, 0.0013, 0, spacing=0.004, taper_end=0.006, tag='eyestay', ray=(0, 0, -1))
    # laces: criss-cross ribbons, second diagonal slightly higher so that they cross over each other
    for i in range(n_rows - 1):
        for (a, b, lift) in ((0, 1, 0.0018), (1, 0, 0.0031)):
            p0, p1 = eye[i][a], eye[i + 1][b]
            mid = (p0 + p1) / 2
            ctrl = [np.array([p0[0], p0[1], 0.4]), np.array([mid[0], mid[1], 0.4]), np.array([p1[0], p1[1], 0.4])]
            ribbon(acc, surf, ctrl, 0.0048 * k, lift, 0, spacing=0.003, taper_end=0.0, tag='lace', ray=(0, 0, -1))
    # top straight lace + eyelets
    top = eye[0]
    ribbon(acc, surf, [np.array([top[0][0], top[0][1] + 0.0, 0.4]), np.array([x_r(row_y[0]), row_y[0] + 0.001, 0.4]), np.array([top[1][0], top[1][1], 0.4])],
           0.0048 * k, 0.0022, 0, spacing=0.003, tag='lace_top', ray=(0, 0, -1))
    for pts in eye:
        for p in pts:
            _, nrm = surf.nearest(p[None, :])
            dome(acc, p + nrm[0] * 0.0006, nrm[0], 0.0034 * k, 0.0017, 0, seg=8, rings=2, tag='eyelet')
    # ---- tongue (strip standing on the vamp, in front of the shin)
    xt = x_r(y_f)
    def shin_front(z):
        l, n, idx, d = tree_body.ray_cast([xt, -0.30, z], [0, 1, 0])
        return float(l[1]) if idx is not None else cy0 - 0.066
    z_cf = P['z_collar_front']
    lz = surf.tree.ray_cast([xt, y_f - 0.052 * k, 0.4], [0, 0, -1])[0]
    path = [np.array([xt, y_f - 0.052 * k, lz[2] + 0.0012])]
    zs = [z_cf - 0.016, z_cf - 0.004, z_cf + 0.006, z_cf + 0.016]
    for z in zs:
        path.append(np.array([xt, shin_front(z) - 0.0085, z]))
    path = catmull(np.array(path), 0.004)
    wid = np.interp(np.linspace(0, 1, len(path)), [0, 1], [P['tongue_w'], P['tongue_w'] * 1.12])
    sweep_strip(acc, path, wid, 0.0042, 0, 'tongue', enforce_trees=[tree_body], c_min=0.0068, sock_tree=sock_tree)
    # ---- seams / panels (tone on tone)
    # toe cap seam
    y_cap = y_toe + 0.185 * L
    loops = slice_plane(V, F, 1, y_cap)
    if loops:
        pl = max(loops, key=len)
        pl = pl[pl[:, 2] > 0.012]
        pl = pl[np.argsort(pl[:, 0])]
        ribbon(acc, surf, pl[::max(1, len(pl) // 14)] + np.array([0, 0, 0.0]), 0.0030, 0.0009, 0, spacing=0.004, taper_end=0.006, tag='toecap')
    # heel counter seam
    y_hc = y_heel - 0.062 * k
    loops = slice_plane(V, F, 1, y_hc)
    if loops:
        pl = max(loops, key=len)
        pl = pl[pl[:, 2] > 0.020]
        pl = pl[np.argsort(pl[:, 0])]
        ribbon(acc, surf, pl[::max(1, len(pl) // 14)], 0.0030, 0.0009, 0, spacing=0.004, taper_end=0.006, tag='heelseam')
    # foxing line (just above the sole ledge)
    loops = slice_plane(V, F, 2, P['sole_top'] + 0.011)
    if loops:
        pl = max(loops, key=len)
        ribbon(acc, surf, pl[::max(1, len(pl) // 60)], 0.0030, 0.0009, 0, spacing=0.005, closed=True, tag='foxing')
    # side panel curves (lateral and medial)
    for sgn in (+1, -1):
        ctrl = [(0.0, y_f - 0.040 * k, 0.083), (0.0, y_f - 0.012 * k, 0.062), (0.0, y_f + 0.018 * k, 0.040), (0.0, y_f + 0.052 * k, 0.026)]
        ribbon(acc, surf, [np.array(c) for c in ctrl], 0.0030, 0.0009, 0, spacing=0.004, taper_end=0.008, tag='sidepanel', ray=(sgn, 0, 0))
    # ---- herringbone tread on the sole bottom (rays from below)
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
    n_ch = 10
    y0s = np.linspace(y_toe + 0.045 * k, y_heel - 0.035 * k, n_ch)
    for y0 in y0s:
        xmin, xmax = half_width(y0)
        xm = 0.5 * (xmin + xmax)
        hw = 0.5 * (xmax - xmin) - 0.020
        if hw < 0.008:
            continue
        d = 0.5 * hw * 0.9
        ctrl = [np.array([xm - hw, y0 - d, -0.2]), np.array([xm, y0 + 0.0, -0.2]), np.array([xm + hw, y0 - d, -0.2])]
        ribbon(acc, surf_sole, ctrl, 0.0058, 0.0013, 0, spacing=0.008, taper_end=0.006, tag='tread', ray=(0, 0, 1))
    Vf, Ff, Nf, Mf = acc.merged()
    tg, tn = acc.tags()
    return dict(V=Vf, F=Ff, N=Nf, M=Mf, T=tg, tagnames=tn, sheet=(V, F))


if __name__ == '__main__':
    gender = sys.argv[sys.argv.index('--') + 1]
    outs = {}
    for side, tag in ((+1, 'R'), (-1, 'L')):
        res = build_shoe(gender, side=side)
        fin = finish_shoe(res, gender, side=side)
        O, R, phi = res['frame']
        V = to_world(fin['V'], O, R)
        F = fin['F']
        N = fin['N'] @ R
        M = fin['M']
        if side < 0:
            V, F, N = V * np.array([-1, 1, 1]), F[:, [0, 2, 1]], N * np.array([-1, 1, 1])
        np.savez(f'{WORK}/data/shoe{tag}_{gender}.npz', V=V, F=F, N=N, M=M, T=fin['T'], tagnames=np.array(fin['tagnames']))
        outs[tag] = (V, F, N, M)
        print(f'  shoe[{gender}] {tag}-shoe tris {len(F)} (sheet {len(fin["sheet"][1])})')
    (Va, Fa, Na, Ma), (Vb, Fb, Nb, Mb) = outs['R'], outs['L']
    np.savez(f'{WORK}/data/shoe_{gender}.npz', V=np.concatenate([Va, Vb]), F=np.concatenate([Fa, Fb + len(Va)]), N=np.concatenate([Na, Nb]), M=np.concatenate([Ma, Mb]))
