"""Digit model of a right hand taken from the MESH itself (no hand-measured constants): finger / thumb components, centre lines,
joints, a landmark hand frame and skin weights.  Pure numpy, used by the socket solve and by the finger rig.

Hand frame (right handed): u along the fingers (wrist -> tips), v across the palm towards the THUMB, p = v x u palm normal.
Landmark frame: u = wrist centre -> middle-finger MCP, v = pinky MCP -> index MCP (made orthogonal to u), p = v x u.
"""
import numpy as np
from handlib import components


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def polyline_len(P):
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def point_at(P, s_arr, s):
    """point on polyline P (cumulative arclength s_arr) at arclength s (clamped; linear extrapolation outside)."""
    if s <= 0:
        d = (P[1] - P[0]) / np.linalg.norm(P[1] - P[0])
        return P[0] + d * s
    if s >= s_arr[-1]:
        d = (P[-1] - P[-2]) / np.linalg.norm(P[-1] - P[-2])
        return P[-1] + d * (s - s_arr[-1])
    k = np.searchsorted(s_arr, s) - 1
    f = (s - s_arr[k]) / (s_arr[k + 1] - s_arr[k])
    return P[k] + f * (P[k + 1] - P[k])


def project_to_polyline(X, P, s_arr):
    """nearest point of every row of X on the polyline P extended by straight rays at both ends.
    returns arclength param s (can be <0 or >L) and distance."""
    n = len(X)
    best_d = np.full(n, np.inf)
    best_s = np.zeros(n)
    segs = list(range(len(P) - 1))
    for k in segs:
        a, b = P[k], P[k + 1]
        ab = b - a
        L = np.linalg.norm(ab)
        t = ((X - a) @ ab) / (L * L)
        lo = -np.inf if k == 0 else 0.0
        hi = np.inf if k == len(P) - 2 else 1.0
        t = np.clip(t, lo, hi)
        q = a + t[:, None] * ab
        d = np.linalg.norm(X - q, axis=1)
        better = d < best_d
        best_d = np.where(better, d, best_d)
        best_s = np.where(better, s_arr[k] + t * L, best_s)
    return best_s, best_d


def split_digits(co, adj, hand, frame0, min_comp=25, want=5):
    """lowest u level at which the hand surface graph falls apart into the 4 fingers + thumb. returns (ucut, comps) with comps
    ordered thumb, index, middle, ring, pinky (by descending mean v)."""
    c, u, v, p = frame0
    Q = (co - c) @ np.stack([u, v, p], 1)
    mask = np.zeros(len(co), bool)
    mask[hand] = True
    for ucut in np.arange(-0.06, 0.12, 0.002):
        m = mask & (Q[:, 0] > ucut)
        comps = [c_ for c_ in components(m, adj) if len(c_) >= min_comp]
        if len(comps) >= want and sorted(len(c_) for c_ in comps)[-want] >= 40:
            comps = comps[:want]
            comps.sort(key=lambda cc: -Q[cc, 1].mean())
            return float(ucut), comps
    raise RuntimeError('digits did not separate')


def digit_centreline(co, comp, palm_pt, nbins=9):
    """ordered centre line of a digit component, base -> tip, plus the digit radius."""
    X = co[comp]
    cen = X.mean(0)
    _, _, Vt = np.linalg.svd(X - cen, full_matrices=False)
    ax = Vt[0]
    if np.dot(cen - palm_pt, ax) < 0:
        ax = -ax
    t = (X - cen) @ ax
    edges = np.linspace(t.min(), t.max(), nbins + 1)
    pts = []
    for i in range(nbins):
        m = (t >= edges[i]) & (t <= edges[i + 1] + 1e-12)
        if m.sum() < 3:
            continue
        pts.append(X[m].mean(0))
    P = np.array(pts)
    # tip = farthest vertex along the axis; replace the last bin centre by the point just inside the tip
    tip = X[np.argmax(t)]
    P = np.vstack([P, cen + ax * (t.max() - 0.35 * (edges[1] - edges[0]))])
    s = polyline_len(P)
    _, d = project_to_polyline(X, P, s)
    return P, float(np.median(d)), ax, tip


def build_model(co, adj, tag, hand, frame0, mcp_extend=0.186, pip_frac=0.47, dip_frac=0.74):
    """returns (ucut, digits) - digits: thumb, index, middle, ring, pinky with component indices, centre line, radius, joints."""
    ucut, comps = split_digits(co, adj, hand, frame0)
    c0, u0, v0, p0 = frame0
    # palm reference point = centroid of hand vertices well below the cut (towards the wrist)
    Q0 = (co[hand] - c0) @ np.stack([u0, v0, p0], 1)
    palm_pt = c0 + u0 * (ucut - 0.04)
    names = ['thumb', 'index', 'middle', 'ring', 'pinky']
    digits = {}
    for nm, comp in zip(names, comps):
        P, R, ax, tip = digit_centreline(co, comp, palm_pt)
        Lc = polyline_len(P)[-1]
        # base direction from the first two thirds of the line
        k = max(2, len(P) // 3)
        dbase = P[k] - P[0]
        dbase /= np.linalg.norm(dbase)
        if nm == 'thumb':
            ext = 0.0
        else:
            ext = mcp_extend * Lc
        mcp = P[0] - dbase * ext
        line = np.vstack([mcp, P])
        s = polyline_len(line)
        L = s[-1]
        if nm == 'thumb':
            # thumb: MCP a little proximal of the web, IP at 0.56 of MCP->tip, CMC one metacarpal (0.78 x MCP->tip) proximal
            mcp = P[0] - dbase * 0.012
            line = np.vstack([mcp, P])
            s = polyline_len(line)
            L = s[-1]
            J = [point_at(line, s, -0.78 * L), mcp, point_at(line, s, 0.56 * L), point_at(line, s, L)]
            fr = [None, 0.0, 0.56, 1.0]
        else:
            J = [mcp, point_at(line, s, pip_frac * L), point_at(line, s, dip_frac * L), point_at(line, s, L)]
        digits[nm] = dict(comp=comp, line=line, s=s, L=L, R=R, J=[np.asarray(j) for j in J], dbase=dbase)
    return ucut, digits


def landmark_frame(co, hand, digits, frame0):
    c0, u0, v0, p0 = frame0
    mcp = {k: digits[k]['J'][0] for k in ('index', 'middle', 'ring', 'pinky')}
    # wrist centre: centroid of the hand-region vertices of the slab 0..8 mm below the proximal-most u of the region
    Q = (co[hand] - c0) @ u0
    wrist = co[hand][Q < Q.min() + 0.008].mean(0)
    u = mcp['middle'] - wrist
    u /= np.linalg.norm(u)
    v = mcp['index'] - mcp['pinky']
    v = v - np.dot(v, u) * u
    v /= np.linalg.norm(v)
    p = np.cross(v, u)
    return wrist, mcp['middle'].copy(), u, v, p


def finger_weights(co, hand, digits, p_hand, fingers=('index', 'middle', 'ring', 'pinky'),
                   s_a=-0.016, s_b=0.012, r_in=1.15, r_out=2.0, joint_half=0.55):
    """skin weights of the hand vertices: dict bone-name -> (len(hand),) array.  Bones: <Digit>_1.._3 for the fingers, Thumb_1.._3, Hand_R (palm).
    Weights sum to 1 on every hand vertex."""
    X = co[hand]
    n = len(X)
    W = {}
    fsum = np.zeros(n)
    sys_w = {}
    for nm in list(fingers) + ['thumb']:
        d = digits[nm]
        line, s_arr = d['line'], d['s']
        if nm == 'thumb':
            # thumb system: chain CMC -> MCP -> IP -> tip, parametrised by arclength from CMC along the (extended) thumb line
            line = np.vstack([d['J'][0], d['line']])
            s_arr = polyline_len(line)
        sp, dist = project_to_polyline(X, line, s_arr)
        R = d['R']
        g = smoothstep((r_out * R - dist) / ((r_out - r_in) * R))
        if nm == 'thumb':
            sp_cmc = 0.0
            ramp = smoothstep((sp - (sp_cmc - 0.012)) / 0.024)     # thenar skin follows the metacarpal
            g = smoothstep((2.2 * R - dist) / (1.1 * R))
        else:
            ramp = smoothstep((sp - s_a) / (s_b - s_a))            # s measured from the MCP
        f = g * ramp
        sys_w[nm] = (f, sp, line, s_arr)
        fsum += f
    scale = np.where(fsum > 1.0, 1.0 / np.maximum(fsum, 1e-9), 1.0)
    palm = 1.0 - np.minimum(fsum, 1.0)
    for nm in list(fingers) + ['thumb']:
        f, sp, line, s_arr = sys_w[nm]
        d = digits[nm]
        f = f * scale
        if nm == 'thumb':
            Js = [project_to_polyline(np.asarray(j)[None, :], line, s_arr)[0][0] for j in d['J'][:3]]   # CMC, MCP, IP params
            hw = joint_half * d['R'] * 2
            w_mcp = smoothstep((sp - Js[1] + hw) / (2 * hw))       # 0 on the metacarpal, 1 beyond MCP
            w_ip = smoothstep((sp - Js[2] + hw) / (2 * hw))
            b1 = 1 - w_mcp
            b2 = w_mcp - w_ip
            b3 = w_ip
            names = ['Thumb_1', 'Thumb_2', 'Thumb_3']
        else:
            s_pip = float(point_arc(d, 1))
            s_dip = float(point_arc(d, 2))
            hw = joint_half * d['R'] * 2
            w_pip = smoothstep((sp - s_pip + hw) / (2 * hw))
            w_dip = smoothstep((sp - s_dip + hw) / (2 * hw))
            b1 = 1 - w_pip
            b2 = w_pip - w_dip
            b3 = w_dip
            names = [f'{nm.capitalize()}_1', f'{nm.capitalize()}_2', f'{nm.capitalize()}_3']
        W[names[0]] = f * b1
        W[names[1]] = f * b2
        W[names[2]] = f * b3
    W['Hand_R'] = palm * 1.0
    tot = sum(W.values())
    for k in W:
        W[k] = W[k] / np.maximum(tot, 1e-9)
    return W


def point_arc(d, k):
    """arclength (from the MCP) of joint k of finger d."""
    _, _ = d['line'], d['s']
    s, _dist = project_to_polyline(d['J'][k][None, :], d['line'], d['s'])
    return s[0]
