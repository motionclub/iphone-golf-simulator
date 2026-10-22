"""Classic racket geometry generator (pure numpy, no bpy): every part is returned as (verts, faces) arrays.

Racket local frame (documented in CLASSIC_RACKET_RESULTS.md):
  origin = centre of the usable grip (palm hold point)
  +Y     = along the shaft towards the head
  +Z     = hitting-face normal (the side the palm pushes through the strings)
  +X     = Y x Z (across the face)
Units = metres.
"""
import numpy as np

P = dict(
    # overall layout along Y (grip centre = 0)
    y_butt=-0.111, y_g0=-0.099, y_g1=0.099,
    y_top=0.577,            # outer top of the head  -> length = y_top - y_butt = 0.688
    H=0.348,                # head outer height
    Wd=0.285,               # head outer width
    egg=0.060,              # head wider at the top by ~6 %
    # frame beam (head loop)
    w_f=0.024,              # in-plane (face-visible) beam width
    d_f=0.034,              # beam depth along the face normal
    sup_p=2.8,              # super-ellipse exponent of the beam section (2 = ellipse)
    n_sides=10,
    sdf_taubin=6, sdf_h=0.0015, sdf_k=0.010, sdf_k_head=0.0035, frame_target_tris=6000,
    # throat / stem
    y_apex=0.128,           # centre-line apex of the two throat arms (tangent lines meet here)
    arm_k0=0.60, arm_k2=0.030,   # Bezier handles of the throat arms (tangent-line departure, short vertical landing)
    stem_out_x=0.0165,      # outer contour of the arms lands vertically here (x) at y_arm_end
    arm_margin=0.0006, arm_w_min=0.026, arm_dz=0.0006, arm_start_scale=0.35, arm_start_len=0.12,
    win_top_x=0.036, win_top_y=0.238, win_apex_y=0.150,      # window (triangle) edge lines the arms are built to
    y_arm_end=0.120,         # arms run vertical from here down into the stem
    stem_top=0.160,         # the stem 'nose' rounds off the window apex
    stem_nose0=0.128,
    w_arm_end=0.027, d_arm_end=0.034,
    stem_hw0=0.0140, stem_hd0=0.0140,   # stem half width / half depth at the grip end
    stem_hw1=0.0165, stem_hd1=0.0165,   # ... at the arm merge
    # grip
    R_grip=0.0170,          # grip radius -> 0.034 m diameter
    R_cap=0.0190,           # butt cap max radius -> 0.038 m diameter (slightly larger than the grip)
    grip_sides=24,
    tilt_deg=7.0,
    # strings (diamond lattice as in the chosen hero pick)
    str_pitch=0.0138, str_r=0.0013, str_dz=0.0012, str_sides=6,
    str_embed=0.0035,
    # grommet collars
    grom_r0=0.0024, grom_r1=0.0016, grom_len_out=0.0020, grom_len_in=0.0010,
)


# ---------------------------------------------------------------- helpers
def superellipse(n, p):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    return np.sign(c) * np.abs(c) ** (2.0 / p), np.sign(s) * np.abs(s) ** (2.0 / p)


def _unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


def tangents(path, closed):
    path = np.asarray(path, float)
    if closed:
        T = np.roll(path, -1, axis=0) - np.roll(path, 1, axis=0)
    else:
        T = np.empty_like(path)
        T[1:-1] = path[2:] - path[:-2]
        T[0] = path[1] - path[0]
        T[-1] = path[-1] - path[-2]
    return _unit(T)


def sweep(path, half_w, half_d, n_sides, p, closed=False, caps=True):
    """Tube along a path lying (roughly) in the XY plane. half_w along the in-plane normal, half_d along Z.
    half_w/half_d: scalars or per-ring arrays. Returns verts (m*n,3), faces list of index tuples (outward winding)."""
    path = np.asarray(path, float)
    m = len(path)
    T = tangents(path, closed)
    N = np.stack([-T[:, 1], T[:, 0], np.zeros(m)], axis=1)
    N = _unit(N)
    D = np.cross(T, N)                       # (T, N, D) right handed -> D = +Z for planar paths
    cx, cz = superellipse(n_sides, p)
    hw = np.broadcast_to(np.asarray(half_w, float), (m,))
    hd = np.broadcast_to(np.asarray(half_d, float), (m,))
    V = (path[:, None, :] + N[:, None, :] * (hw[:, None, None] * cx[None, :, None])
         + D[:, None, :] * (hd[:, None, None] * cz[None, :, None]))
    verts = V.reshape(-1, 3)
    faces = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        i2 = (i + 1) % m
        for k in range(n_sides):
            k2 = (k + 1) % n_sides
            faces.append((i * n_sides + k, i * n_sides + k2, i2 * n_sides + k2, i2 * n_sides + k))
    if caps and not closed:
        faces.append(tuple(range(n_sides - 1, -1, -1)))                       # start cap
        faces.append(tuple((m - 1) * n_sides + k for k in range(n_sides)))    # end cap
    return verts, faces


def revolve_profile(rings, sides, tilt=None, close_axis_top=None, close_axis_bottom=None):
    """Surface of revolution around Y. rings = list of (y, r). tilt = optional per-ring (tilt_tan) so the ring's y gets
    + tilt_tan * r * sin(theta). Optional axis closing vertices (y) at top/bottom (single pole vertex)."""
    th = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    verts, faces = [], []
    for j, (y, r) in enumerate(rings):
        tt = 0.0 if tilt is None else tilt[j]
        for k in range(sides):
            verts.append((r * np.cos(th[k]), y + tt * r * np.sin(th[k]), r * np.sin(th[k])))
    # NOTE: the ring plane is built in (x, z) with the axis along Y
    for j in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((j * sides + k, j * sides + k2, (j + 1) * sides + k2, (j + 1) * sides + k))
    n0 = len(verts)
    if close_axis_top is not None:
        verts.append((0.0, close_axis_top, 0.0))
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((n0, k2, k))
        n0 += 1
    if close_axis_bottom is not None:
        verts.append((0.0, close_axis_bottom, 0.0))
        base = (len(rings) - 1) * sides
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((n0, base + k, base + k2))
    return np.array(verts, float), faces


# ---------------------------------------------------------------- head curve
def head_xy(t, a, b, yc, egg):
    x = a * np.cos(t) * (1.0 + egg * np.sin(t))
    y = yc + b * np.sin(t)
    return np.stack([x, y], axis=-1)


def head_deriv(t, a, b, yc, egg, h=1e-5):
    return (head_xy(t + h, a, b, yc, egg) - head_xy(t - h, a, b, yc, egg)) / (2 * h)


def offset_curve(t, a, b, yc, egg, off):
    C = head_xy(t, a, b, yc, egg)
    d = head_deriv(t, a, b, yc, egg)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    # CCW curve: outward normal = (dy, -dx)
    n = np.stack([d[:, 1], -d[:, 0]], axis=-1)
    return C + n * off


def solve_head(p=P):
    """Centre-line ellipse parameters so that the OUTER extents are exactly H x Wd."""
    b = p['H'] / 2 - p['w_f'] / 2
    yc = p['y_top'] - p['H'] / 2
    t = np.linspace(0, 2 * np.pi, 4001)
    lo, hi = 0.05, 0.2
    for _ in range(60):
        a = 0.5 * (lo + hi)
        outer = offset_curve(t, a, b, yc, p['egg'], p['w_f'] / 2)
        wmax = np.abs(outer[:, 0]).max() * 2
        if wmax > p['Wd']:
            hi = a
        else:
            lo = a
    return a, b, yc


def tangent_point_to(Apt, a, b, yc, egg, side=+1):
    """Parameter t of the lower tangent point on the centre-line curve for lines through Apt (side +1 = right/x>0)."""
    ts = np.linspace(-np.pi / 2 + 0.02, -0.02, 4000) if side > 0 else np.linspace(-np.pi + 0.02, -np.pi / 2 - 0.02, 4000)
    C = head_xy(ts, a, b, yc, egg)
    d = head_deriv(ts, a, b, yc, egg)
    cr = d[:, 0] * (Apt[1] - C[:, 1]) - d[:, 1] * (Apt[0] - C[:, 0])
    idx = np.where(np.sign(cr[:-1]) != np.sign(cr[1:]))[0]
    if len(idx) == 0:
        raise RuntimeError('no tangent point')
    i = idx[0]
    return ts[i] - cr[i] * (ts[i + 1] - ts[i]) / (cr[i + 1] - cr[i])


def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * (t ** 2) * p2 + (t ** 3) * p3


# ---------------------------------------------------------------- parts

def ray_polygon_hit(o, d, poly):
    """Distance t>0 along ray o + t d to the first polygon edge hit (inf if none)."""
    best = 1e9
    n = len(poly)
    for i in range(n):
        a_ = poly[i]
        e = poly[(i + 1) % n] - a_
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-14:
            continue
        w_ = a_ - o
        t = (w_[0] * e[1] - w_[1] * e[0]) / den
        u = (w_[0] * d[1] - w_[1] * d[0]) / den
        if t > 1e-6 and 0.0 <= u <= 1.0 and t < best:
            best = t
    return best

def frame_paths(p=P, n_head=360):
    """Centre-line paths of the frame tubes: list of dict(name, path (m,2), hw, hd, closed). Planar (z=0)."""
    a, b, yc = solve_head(p)
    egg = p['egg']
    out = []
    th = np.linspace(0, 2 * np.pi, n_head, endpoint=False)
    hp = head_xy(th, a, b, yc, egg)
    out.append(dict(name='head', path=hp, hw=np.full(n_head, p['w_f'] / 2), hd=np.full(n_head, p['d_f'] / 2), closed=True))
    # throat arms: built from their OUTER contour (tangent to the outer head oval, landing vertically on the stem);
    # the centre line is that contour shifted inward by half the (varying) width.
    S_out = np.array([p['stem_out_x'], p['y_arm_end']])
    opening = inner_polygon(p)
    tt = np.linspace(-np.pi / 2 + 0.02, -0.02, 6000)
    sm = lambda e0, e1, x: (lambda q: q * q * (3 - 2 * q))(np.clip((x - e0) / (e1 - e0), 0, 1))
    arms = []
    for side in (+1, -1):
        sgn = side
        if side > 0:
            tsel, S = tt, S_out
        else:
            tsel, S = -np.pi - tt, np.array([-S_out[0], S_out[1]])
        O = offset_curve(tsel, a, b, yc, egg, p['w_f'] / 2)
        dO = head_deriv(tsel, a, b, yc, egg)
        cr = dO[:, 0] * (S[1] - O[:, 1]) - dO[:, 1] * (S[0] - O[:, 0])
        idx = np.where(np.sign(cr[:-1]) != np.sign(cr[1:]))[0]
        i = idx[0]
        frac = -cr[i] / (cr[i + 1] - cr[i])
        T_out = O[i] + frac * (O[i + 1] - O[i])
        td = tsel[i] + frac * (tsel[i + 1] - tsel[i])
        dirA = S - T_out
        L = np.linalg.norm(dirA)
        dirA /= L
        P1 = T_out + dirA * (p['arm_k0'] * L)
        P2 = S + np.array([0.0, 1.0]) * p['arm_k2']
        outer = bezier(T_out, P1, P2, S, 200)
        seg = np.linalg.norm(np.diff(outer, axis=0), axis=1)
        sa = np.concatenate([[0], np.cumsum(seg)])
        ns = int(sa[-1] / 0.0085) + 2
        su = np.linspace(0, sa[-1], ns)
        op = np.stack([np.interp(su, sa, outer[:, 0]), np.interp(su, sa, outer[:, 1])], axis=1)
        u = su / sa[-1]
        d = p['d_f'] - p['arm_dz'] + (p['d_arm_end'] - p['d_f']) * sm(0.0, 0.8, u)
        tg = tangents(np.concatenate([op, np.zeros((len(op), 1))], axis=1), False)[:, :2]
        nrm_in = np.stack([-tg[:, 1], tg[:, 0]], axis=1)
        flip = np.sign(-sgn * nrm_in[:, 0])
        nrm_in *= np.where(flip == 0, 1, flip)[:, None]
        w_max = np.array([ray_polygon_hit(op[k], nrm_in[k], opening) for k in range(len(op))])
        A_w = np.array([0.0, p['win_apex_y']])
        dl = np.array([sgn * p['win_top_x'], p['win_top_y'] - p['win_apex_y']])
        dl /= np.linalg.norm(dl)
        w_line = np.empty(len(op))
        for k in range(len(op)):
            M = np.array([[nrm_in[k, 0], -dl[0]], [nrm_in[k, 1], -dl[1]]])
            try:
                t_, q_ = np.linalg.solve(M, A_w - op[k])
            except np.linalg.LinAlgError:
                t_, q_ = 1e9, 0
            w_line[k] = t_ if (t_ > 0 and q_ > -0.02) else p['w_arm_end']
        w = np.clip(w_line, p['arm_w_min'], 1.0)
        w = np.minimum(w, np.maximum(w_max - p['arm_margin'], p['w_f']))
        w = p['w_f'] + (w - p['w_f']) * sm(0.0, 0.14, u)
        w = np.convolve(np.pad(w, 2, mode='edge'), np.ones(5) / 5, mode='valid')
        g = p['arm_start_scale'] + (1 - p['arm_start_scale']) * sm(0.0, p['arm_start_len'], u)
        w = w * g
        d = d * g
        w = np.convolve(np.pad(w, 4, mode='edge'), np.ones(9) / 9, mode='valid')
        cl = op + nrm_in * (w / 2)[:, None]
        for _ in range(3):                                   # light fairing of the centre line (ends fixed)
            cl[1:-1] = 0.25 * cl[:-2] + 0.5 * cl[1:-1] + 0.25 * cl[2:]
        tail_n = 3
        tail = np.stack([np.full(tail_n, cl[-1, 0]), np.linspace(cl[-1, 1], cl[-1, 1] - 0.015, tail_n + 1)[1:]], axis=1)
        cl = np.concatenate([cl, tail], axis=0)
        w = np.concatenate([w, np.full(tail_n, w[-1])])
        d = np.concatenate([d, np.full(tail_n, d[-1])])
        out.append(dict(name='arm_R' if side > 0 else 'arm_L', path=cl, hw=w / 2, hd=d / 2, closed=False))
        arms.append(dict(t_dep=float(td), T_out=T_out.tolist(), S=S.tolist(),
                         half_angle_deg=float(np.degrees(np.arctan2(abs(S[0] - T_out[0]), T_out[1] - S[1])))))
    # stem: from inside the grip up under the window apex
    y0, y1 = p['y_g1'] - 0.0015, p['stem_top']
    ys = np.linspace(y0, y1, 12)
    u = np.clip((ys - p['y_g1']) / (p['stem_top'] - p['y_g1']), 0, 1)
    hw = p['stem_hw0'] + (p['stem_hw1'] - p['stem_hw0']) * u ** 1.2
    hd = p['stem_hd0'] + (p['stem_hd1'] - p['stem_hd0']) * u ** 1.2
    out.append(dict(name='stem', path=np.stack([np.zeros_like(ys), ys], axis=1), hw=hw, hd=hd, closed=False))
    return out, dict(a=a, b=b, yc=yc, arms=arms)


def build_frame(p=P):
    """Swept-tube version of the frame (debug / fallback): list of (name, verts, faces)."""
    paths, info = frame_paths(p)
    parts = []
    for t in paths:
        pts = t['path']
        if t['closed']:
            pts = pts[::4]
            hw, hd = t['hw'][::4], t['hd'][::4]
        else:
            hw, hd = t['hw'], t['hd']
        path3 = np.concatenate([pts, np.zeros((len(pts), 1))], axis=1)
        v, f = sweep(path3, hw, hd, p['n_sides'], p['sup_p'], closed=t['closed'])
        parts.append((t['name'], v, f))
    return parts, info


def build_frame_sdf(p=P, h=0.0015, k=0.008, verbose=True):
    """SDF smooth-union of the frame tubes -> (V (n,3), tris (m,3), normals (n,3)) with analytic SDF normals."""
    import sdf_tools as S
    paths, info = frame_paths(p)
    grid = S.Grid((-0.1515, 0.072, -0.0215), (0.1515, 0.590, 0.0215), h)      # x nodes symmetric about 0
    fields = {}
    for t in paths:
        fields[t['name']] = S.tube_field(grid, t['path'], t['hw'], t['hd'], p['sup_p'], closed=t['closed'], chunk=3000)
    k1, k2 = p['sdf_k_head'], p['sdf_k']
    A = S.smin(fields['arm_R'], fields['arm_L'], k2)
    A = S.smin(A, fields['stem'], k2)
    F = S.smin(fields['head'], A, k1)
    V, Q = S.surface_nets(F, grid)
    T = S.quads_to_tris(V, Q)
    V = S.taubin(V, T, iters=p['sdf_taubin'])
    # pull the vertices back onto the iso-surface (two Newton steps along the gradient)
    for _ in range(2):
        d = S.sample(F, grid, V)
        g = S.gradient(F, grid, V)
        gl = np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
        V = V - (d[:, None] * g / gl / gl) * 1.0 * gl
    info['grid'] = (grid.n.tolist(), h)
    info['F'] = F
    info['gridobj'] = grid
    return V, T, info


def inner_polygon(p=P, n=720):
    a, b, yc = solve_head(p)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return offset_curve(t, a, b, yc, p['egg'], -p['w_f'] / 2)       # inner edge of the frame at the mid-plane


def clip_line_convex(poly, p0, d):
    """Intersection parameters (t_in, t_out) of the line p0 + t d with a convex polygon (n,2), or None."""
    t_in, t_out = -1e9, 1e9
    n = len(poly)
    # polygon is CCW; inward normal of edge i = left of edge direction
    for i in range(n):
        a_ = poly[i]
        e = poly[(i + 1) % n] - a_
        nn = np.array([-e[1], e[0]])
        nn /= np.linalg.norm(nn)
        den = np.dot(nn, d)
        num = np.dot(nn, a_ - p0)
        if abs(den) < 1e-12:
            if num > 0:
                return None
            continue
        t = num / den
        if den > 0:           # entering
            t_in = max(t_in, t)
        else:
            t_out = min(t_out, t)
        if t_in > t_out:
            return None
    return t_in, t_out


def build_strings(p=P):
    poly = inner_polygon(p)
    cy = 0.5 * (poly[:, 1].max() + poly[:, 1].min())
    s = p['str_pitch']
    parts_v, parts_f = [], []
    gv, gf = [], []
    cnt = 0
    ends = []
    kmax = int(0.40 / s)
    cx, cz = superellipse(p['str_sides'], 2.0)
    for fam, (dx, dy, zl) in enumerate(((1, 1, +1), (1, -1, -1))):
        d = np.array([dx, dy], float) / np.sqrt(2)
        nrm = np.array([-d[1], d[0]])
        for k in range(-kmax, kmax + 1):
            o = k * s
            p0 = np.array([0.0, cy]) + nrm * o
            r = clip_line_convex(poly, p0, d)
            if r is None or (r[1] - r[0]) < 0.012:
                continue
            ta, tb = r[0] - p['str_embed'], r[1] + p['str_embed']
            A = p0 + d * ta
            B = p0 + d * tb
            z = zl * p['str_dz']
            # tube along A->B, round section (hex) in the plane perpendicular to d (axes: Z and in-plane normal)
            nz = np.array([nrm[0], nrm[1], 0.0])
            zz = np.array([0.0, 0.0, 1.0])
            ring = lambda P2: np.array([[P2[0], P2[1], z]]) + p['str_r'] * (cx[:, None] * nz[None, :] + cz[:, None] * zz[None, :])
            vv = np.concatenate([ring(A), ring(B)], axis=0)
            n = p['str_sides']
            ff = []
            for kk in range(n):
                k2 = (kk + 1) % n
                ff.append((kk, k2, n + k2, n + kk))
            ff.append(tuple(range(n - 1, -1, -1)))
            ff.append(tuple(n + kk for kk in range(n)))
            parts_f.append([tuple(i + cnt for i in f_) for f_ in ff])
            parts_v.append(vv)
            cnt += len(vv)
            # grommet collars at both inner-edge intersections
            for tt, sgn in ((r[0], -1.0), (r[1], +1.0)):
                E = p0 + d * tt                                        # on the inner edge at mid-plane
                axis3 = np.array([d[0], d[1], 0.0]) * (-sgn)           # pointing inwards (towards the opening)
                base3 = np.array([E[0], E[1], z]) - axis3 * p['grom_len_in']
                top3 = np.array([E[0], E[1], z]) + axis3 * p['grom_len_out']
                u1 = nz
                u2 = zz
                bring = base3 + p['grom_r0'] * (cx[:, None] * u1[None, :] + cz[:, None] * u2[None, :])
                tring = top3 + p['grom_r1'] * (cx[:, None] * u1[None, :] + cz[:, None] * u2[None, :])
                vv2 = np.concatenate([bring, tring], axis=0)
                ff2 = []
                for kk in range(n):
                    k2 = (kk + 1) % n
                    ff2.append((kk, k2, n + k2, n + kk))
                ff2.append(tuple(n + kk for kk in range(n)))
                gf.append([tuple(i + cnt for i in f_) for f_ in ff2])
                gv.append(vv2)
                cnt += len(vv2)
                ends.append((E, z))
    allv = np.concatenate(parts_v + gv, axis=0)
    allf = [f_ for fl in (parts_f + gf) for f_ in fl]
    return allv, allf, dict(n_strings=len(parts_v), n_grommets=len(gv), cy=cy)


def grip_profile(p=P):
    """(y, r, distance-below-top) rings of the tape-wrapped sleeve, from the grip top down to y_g0."""
    R = p['R_grip']
    top, bot = p['y_g1'], p['y_g0']
    prof = [(0.0000, -0.0004), (0.0010, 0.0002), (0.0030, 0.0006), (0.0055, 0.0006), (0.0062, -0.0004)]   # top cuff
    pitch = 0.0215
    d0 = 0.0062
    while d0 + pitch < (top - bot) - 0.0035:
        prof += [(d0 + 0.0012, 0.0001), (d0 + 0.0035, 0.0003), (d0 + 0.0180, 0.0003), (d0 + 0.0200, 0.0000), (d0 + pitch, -0.0006)]
        d0 += pitch
    prof += [(d0 + 0.0012, 0.0001), (d0 + 0.0030, 0.0002), ((top - bot) - 0.0006, -0.0003)]
    return [(top - dd, R + dr, dd) for dd, dr in prof]


def build_grip(p=P):
    """Tape-wrapped sleeve (the 'grip', usable length y_g0..y_g1, diameter 2*R_grip) as a surface of revolution."""
    sides = p['grip_sides']
    top, bot = p['y_g1'], p['y_g0']
    prof = grip_profile(p)
    tilt = np.tan(np.radians(p['tilt_deg']))
    span = top - bot
    rings, tl = [], []
    for (y, r, dd) in prof:
        k = np.clip((dd - 0.0062) / 0.006, 0, 1) * np.clip((span - dd - 0.003) / 0.012, 0, 1)
        k = k * k * (3 - 2 * k)
        rings.append((y, r))
        tl.append(tilt * k)
    v, f = revolve_profile(rings, sides, tilt=tl, close_axis_top=top, close_axis_bottom=bot)
    return v, f, dict(rings=len(rings))


def build_butt_cap(p=P):
    """Black butt cap: slightly larger than the grip (R_cap), rounded, with a recessed disc end."""
    R, Rc, yb, bot = p['R_grip'], p['R_cap'], p['y_butt'], p['y_g0']
    rings = [(bot + 0.0018, R + 0.0006), (bot + 0.0004, R + 0.0016), (bot - 0.0016, Rc - 0.0004), (bot - 0.0040, Rc),
             (yb + 0.0075, Rc), (yb + 0.0040, Rc - 0.0010), (yb + 0.0012, Rc - 0.0034), (yb, Rc - 0.0060),
             (yb, Rc - 0.0082), (yb + 0.0010, Rc - 0.0086)]
    v, f = revolve_profile(rings, p['grip_sides'], tilt=None, close_axis_top=bot + 0.0018, close_axis_bottom=yb + 0.0010)
    return v, f


def build_collider(p=P):
    """Low-poly collision proxy: shaft capsule + flat oval prism over the head (disclosed, optional)."""
    verts, faces = [], []
    # capsule (8 sides) along Y from butt to the throat
    sides = 8
    th = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    ys = [p['y_butt'], p['y_butt'] + 0.012, 0.150, 0.236]
    rs = [0.012, 0.0190, 0.0190, 0.0150]
    for y, r in zip(ys, rs):
        for k in range(sides):
            verts.append((r * np.cos(th[k]), y, r * np.sin(th[k])))
    for j in range(len(ys) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((j * sides + k, j * sides + k2, (j + 1) * sides + k2, (j + 1) * sides + k))
    base = len(verts)
    faces.append(tuple(range(sides - 1, -1, -1)))
    faces.append(tuple((len(ys) - 1) * sides + k for k in range(sides)))
    # head prism: 16-gon of the OUTER head outline (offset), thickness d_f
    a, b, yc = solve_head(p)
    t = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    outer = offset_curve(t, a, b, yc, p['egg'], p['w_f'] / 2)
    hz = p['d_f'] / 2
    n0 = len(verts)
    for z in (-hz, hz):
        for q in outer:
            verts.append((q[0], q[1], z))
    n = len(outer)
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((n0 + k, n0 + k2, n0 + n + k2, n0 + n + k))
    faces.append(tuple(n0 + k for k in range(n - 1, -1, -1)))
    faces.append(tuple(n0 + n + k for k in range(n)))
    return np.array(verts, float), faces
