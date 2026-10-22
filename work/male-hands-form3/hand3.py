"""hand3 - new male hand generator (right-hand local frame a', n, w; the left hand is mirrored by the caller).

Same overall construction as the Micro1e/f hand (weld ring -> palm pillow rings -> lobed knuckle ring -> 4 slit fingers + thumb
on a hole in the palmar-radial flank) but with redesigned fingers (taper, joint bumps, pad tips, relaxed flexion) and a redesigned
thumb (bigger hole / root loop, Catmull-Rom axis, metacarpal -> MCP -> IP -> pad-tip radius profile).

Usage:  B, info = build_hand(ring_ids, ring_L, N_existing, params)
  ring_ids : existing mesh vertex ids of the 42-vertex wrist weld ring (connectivity order)
  ring_L   : their local coordinates (n,3)
  returns a Builder (new vertex local positions B.pos, faces B.faces with ids >= N for new vertices) and an info dict with the roles.
"""
import numpy as np
from hlib import smooth01, order_ring

P0 = dict(
    # ---- palm rings
    w_rows=[-0.044, -0.0325, -0.021, -0.0115, -0.004, 0.003, 0.010, 0.017, 0.024, 0.031, 0.039, 0.049, 0.060],
    w_knuckle=0.060, p_exp=2.3, span=0.055,
    palm_thick=0.0020, ridge=0.0035, ridge_w=(0.025, 0.060),
    thenar=0.0090, thenar_w=(-0.015, 0.020, 0.052), thenar_ang=-7 * np.pi / 4, thenar_sig=0.70, hypo=0.0035,
    # ---- fingers
    r_a=0.0124, r_n=0.0155, gap=0.0034, n_f0=-0.0182, h_valley=0.0065,
    f_tip=[0.154, 0.170, 0.158, 0.136],
    splay_deg=[7.0, 2.3, -2.6, -8.0],
    flex=[(0, 4, 3), (0, 5, 4), (0, 6, 5), (0, 7, 5)],     # MCP, PIP, DIP flexion (deg) toward the palm
    s_pip=0.38, s_dip=0.71, tilt_w=0.07,
    ka=([0, 0.15, 0.38, 0.55, 0.71, 0.86, 1.0], [1.0, 0.975, 0.90, 0.82, 0.75, 0.68, 0.62]),
    kd=([0, 0.12, 0.25, 0.38, 0.55, 0.71, 0.86, 1.0], [1.0, 0.90, 0.82, 0.77, 0.71, 0.66, 0.62, 0.58]),
    kp=([0, 0.12, 0.25, 0.38, 0.55, 0.71, 0.86, 1.0], [1.0, 0.90, 0.82, 0.77, 0.71, 0.66, 0.62, 0.58]),
    bump_pip=0.075, bump_dip=0.065, bump_sig=0.055, side_swell=0.03,
    pad_tip=0.14, pad_sig=0.09, crease=0.03,
    kp_scale=1.15, flex_scale=2.0, mcp_flex=2.5, len_scale=1.03, splay_scale=0.7, thumb_r_scale=1.06, thumb_len_scale=0.95, thumb_pitch=-0.004, thumb_ip_bend=15.0,
    cap_len=1.2, cap_flat=0.86, cap_c=0.55, cap_angles=(10.0, 22.0, 36.0, 52.0, 68.0, 82.0),
    shaft_s=[0.07, 0.15, 0.23, 0.31, 0.38, 0.45, 0.53, 0.62, 0.71, 0.78, 0.85],
    # ---- thumb
    hole_cols=(34, 39), hole_rows=(6, 10),            # palm ring row indices (1-based) bounding the hole, columns mod 40
    thumb_pts=[(0.038, 0.002, 0.019), (0.051, 0.016, 0.034), (0.057, 0.027, 0.063), (0.057, 0.036, 0.089)],
    thumb_u=[0.0, 0.18, 0.30, 0.46, 0.58, 0.66, 0.78, 0.90],       # radius nodes along the arclength (MCP ~0.28, IP ~0.65)
    thumb_r=[0.0135, 0.0150, 0.0152, 0.0138, 0.0130, 0.0135, 0.0121, 0.0106],   # half width at the nodes
    thumb_flat=0.92, thumb_bump=0.06, thumb_first=0.006, thumb_morph=2.5, thumb_rows=17, thumb_cap=0.90,
    thumb_anchor=1,
    # ---- post smoothing (Taubin) : (radius around the thumb root, weight palm, weight finger root rows, iterations)
    web_k=0.028, web_amp=1.6, web_clear=0.0015, web_clear_r=1.0,
    sm_thumb_R=0.055, sm_thumb_w=1.0, sm_palm_w=0.12, sm_fin_w=0.30, sm_tip_w=1.0, sm_iters=45,
)


class Builder:
    def __init__(self, n_existing):
        self.N = n_existing; self.pos = []; self.faces = []
    def add(self, p):
        self.pos.append(np.asarray(p, float)); return self.N + len(self.pos) - 1
    def face(self, *ids):
        self.faces.append(tuple(int(i) for i in ids))


def gauss(x, c, s):
    return np.exp(-((x - c) / s) ** 2)


def pchip(xk, yk, x):
    """monotone cubic (Fritsch-Carlson) interpolation, numpy only"""
    xk = np.asarray(xk, float); yk = np.asarray(yk, float); x = np.asarray(x, float)
    h = np.diff(xk); d = np.diff(yk) / h; n = len(xk); m = np.zeros(n)
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    def endslope(h0, h1, d0, d1):
        sl = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        if np.sign(sl) != np.sign(d0): sl = 0.0
        elif np.sign(d0) != np.sign(d1) and abs(sl) > 3 * abs(d0): sl = 3 * d0
        return sl
    m[0] = endslope(h[0], h[1], d[0], d[1]) if n > 2 else d[0]
    m[-1] = endslope(h[-1], h[-2], d[-1], d[-2]) if n > 2 else d[-1]
    idx = np.clip(np.searchsorted(xk, x) - 1, 0, n - 2)
    t = (x - xk[idx]) / h[idx]
    return (2 * t ** 3 - 3 * t ** 2 + 1) * yk[idx] + (t ** 3 - 2 * t ** 2 + t) * h[idx] * m[idx] + (-2 * t ** 3 + 3 * t ** 2) * yk[idx + 1] + (t ** 3 - t ** 2) * h[idx] * m[idx + 1]


# ----------------------------------------------------------------------------- palm
def A_of(w):  return np.interp(w, [-0.04, -0.02, 0.0, 0.03, 0.06], [0.0370, 0.0385, 0.0415, 0.0445, 0.0495])
def B_of(w, P):  return np.interp(w, [-0.04, -0.01, 0.02, 0.045, 0.06], [0.0300, 0.0285, 0.0270, 0.0195, 0.0152]) + P['palm_thick'] * smooth01(w / 0.06)
def NC_of(w): return np.interp(w, [-0.04, 0.0, 0.045, 0.06], [-0.0126, -0.0150, -0.0185, -0.0215])


def ellipse_ring(w, P, WELD, nverts=40):
    A, B, nc = A_of(w), B_of(w, P), NC_of(w)
    ca = 0.0
    if WELD['A'] is not None:
        sb = smooth01((w - WELD['w']) / P['span'])
        A = WELD['A'] + (A - WELD['A']) * sb
        B = WELD['B'] + (B - WELD['B']) * sb
        nc = WELD['cn'] + (nc - WELD['cn']) * sb
        ca = WELD['ca'] * (1 - sb)
    t = -2 * np.pi * np.arange(nverts) / nverts
    c, s = np.cos(t), np.sin(t)
    e = 2.0 / P['p_exp']
    a = A * np.sign(c) * np.abs(c) ** e
    n = nc + B * np.sign(s) * np.abs(s) ** e
    w0, w1, w2 = P['thenar_w']
    prof = smooth01((w - w0) / (w1 - w0)) * (1 - smooth01((w - w1) / (w2 - w1)))
    dth = np.angle(np.exp(1j * (t - P['thenar_ang'])))
    g = np.exp(-(dth / P['thenar_sig']) ** 2) * prof
    dth2 = np.angle(np.exp(1j * (t - (-5 * np.pi / 4))))
    g2 = np.exp(-(dth2 / 0.55) ** 2) * prof
    r = np.hypot(a, n - nc)
    ux, un = a / np.maximum(r, 1e-9), (n - nc) / np.maximum(r, 1e-9)
    a = a + ux * (P['thenar'] * g + P['hypo'] * g2)
    n = n + un * (P['thenar'] * g + P['hypo'] * g2)
    return np.stack([a + ca, n], 1)


def finger_centers(P):
    S = 2 * P['r_a'] + P['gap']
    return [(1.5 - k) * S for k in range(4)], S


def lobed_ring(P):
    ac, S = finger_centers(P)
    ra, rn, nf, hv = P['r_a'], P['r_n'], P['n_f0'], P['h_valley']
    out = np.zeros((40, 2))
    out[0] = (ac[0] + ra, nf); out[20] = (ac[3] - ra, nf)
    phi = np.radians(-90 + 36 * np.arange(0, 6))
    for j in range(1, 20):
        k, q = divmod(j, 5)
        if q == 0:
            av = 0.5 * (ac[k - 1] + ac[k])
            out[j] = (av, nf - hv); out[40 - j] = (av, nf + hv)
        else:
            ph = phi[q]; a = ac[k] - ra * np.sin(ph)
            out[j] = (a, nf - rn * np.cos(ph)); out[40 - j] = (a, nf + rn * np.cos(ph))
    return out


# ----------------------------------------------------------------------------- fingers
def finger_profile(P, s, k):
    """lateral half width, dorsal half depth, palmar half depth at arclength fraction s (0 = knuckle ring, 1 = tip pole) for the shaft"""
    ta = float(pchip(P['ka'][0], P['ka'][1], s))
    td = float(pchip(P['kd'][0], P['kd'][1], s))
    tp = float(pchip(P['kp'][0], P['kp'][1], s)) * (1 + (P['kp_scale'] - 1) * smooth01(s / 0.25))
    bp, bd, sg = P['bump_pip'], P['bump_dip'], P['bump_sig']
    dors = 1 + bp * gauss(s, P['s_pip'], sg) + bd * gauss(s, P['s_dip'], sg)
    side = 1 + P['side_swell'] * (gauss(s, P['s_pip'], sg * 1.1) + gauss(s, P['s_dip'], sg * 1.1))
    palm = 1 + P['pad_tip'] * gauss(s, 0.86, P['pad_sig']) + 0.035 * gauss(s, 0.20, 0.07) + 0.03 * gauss(s, 0.54, 0.06) \
        - P['crease'] * (gauss(s, P['s_pip'], 0.035) + gauss(s, P['s_dip'], 0.035))
    return P['r_a'] * ta * side, P['r_n'] * td * dors, P['r_n'] * tp * palm


def finger_axis(P, k, n_samples=400):
    """(n, w) polyline of the finger axis with joint flexion, returns arclength-parametrised callable data"""
    f1, f2, f3 = [np.radians(x * P['flex_scale']) if i > 0 else np.radians(x) for i, x in enumerate(P['flex'][k])]
    s = np.linspace(0, 1, n_samples)
    tw = P['tilt_w']
    th = f1 * smooth01(s / 0.16) + f2 * smooth01((s - (P['s_pip'] - tw)) / (2 * tw)) + f3 * smooth01((s - (P['s_dip'] - tw)) / (2 * tw))
    ds = s[1] - s[0]
    dw = np.cos(th) * ds; dn = np.sin(th) * ds                     # +n = toward the palm
    w = np.r_[0, np.cumsum(0.5 * (dw[1:] + dw[:-1]))]
    n = np.r_[0, np.cumsum(0.5 * (dn[1:] + dn[:-1]))]
    return s, th, w, n


def build_fingers(B, P, kn, info):
    ac, S = finger_centers(P)
    Dr = lambda j: kn[j]
    Pr = lambda j: kn[(40 - j) % 40]
    fin_rows = {}
    for k in range(4):
        Lw = P['f_tip'][k] - P['w_knuckle']                          # target tip w distance from the knuckle ring
        s_, th_, w_, n_ = finger_axis(P, k)
        Larc = Lw / w_[-1]                                           # arclength so the tip lands at f_tip
        tip_r = P['r_a'] * P['ka'][1][-1]
        s_cap = 1.0 - P['cap_len'] * tip_r / Larc
        shaft = [s for s in P['shaft_s'] if s < s_cap - 0.02] + [s_cap]
        capang = np.radians(P['cap_angles'])
        sv = shaft + [s_cap + (1 - s_cap) * np.sin(c_) for c_ in capang]
        capr = [1.0] * len(shaft) + [np.cos(c_) for c_ in capang]
        tan_s = np.tan(np.radians(P['splay_deg'][k]))
        rows = []
        for m, s in enumerate(sv):
            sc = min(s, s_cap)
            ra, rd, rp = finger_profile(P, sc, k)           # rd, rp: dorsal / palmar half depth (bumps and pads included)
            td = float(pchip(P['kd'][0], P['kd'][1], sc)) * P['r_n']          # taper-only half depth (no bumps)
            if m >= len(shaft):                                    # cap rows: flatter dorsal side (nail), rounder pad
                cr = capr[m]
                ra *= cr; rd *= cr * P['cap_flat'] ** (1 - cr); rp *= cr ** 0.9
                td = td * (P['cap_c'] + (1 - P['cap_c']) * cr) ; rd = min(rd, 1e9)
            idx = np.searchsorted(s_, min(s, 1.0)); idx = min(max(idx, 1), len(s_) - 1)
            f = (min(s, 1.0) - s_[idx - 1]) / (s_[idx] - s_[idx - 1])
            th = th_[idx - 1] * (1 - f) + th_[idx] * f
            wv = Larc * (w_[idx - 1] * (1 - f) + w_[idx] * f); nv = Larc * (n_[idx - 1] * (1 - f) + n_[idx] * f)
            w = P['w_knuckle'] + wv; nD = P['n_f0'] - P['r_n'] + nv          # dorsal polyline (n, w)
            un, uw = np.cos(th), -np.sin(th)                       # unit vector toward +n (palmar) perpendicular to the tangent
            # ring centre sits td below the dorsal line so the nail-side contour stays straight; bumps add outward
            n0 = nD + td * un; wc = w + td * uw
            ack = ac[k] + tan_s * (w - P['w_knuckle'])
            ph = np.radians(-90 + 36 * np.arange(1, 5))
            def pt(a_, off):
                return (a_, n0 + off * un, wc + off * uw)
            WL = B.add(pt(ack + ra, 0.0)); WR = B.add(pt(ack - ra, 0.0))
            Dq = [B.add(pt(ack - ra * np.sin(p_), -rd * np.cos(p_))) for p_ in ph]
            Pq = [B.add(pt(ack - ra * np.sin(p_), +rp * np.cos(p_))) for p_ in ph]
            rows.append([WL] + Dq + [WR] + Pq[::-1])
        # pole: the cap rows converge onto the dorsal polyline, so the pole sits on it
        wv = Larc * w_[-1]; nv = Larc * n_[-1]
        td_end = P['r_n'] * P['kd'][1][-1]
        C = B.add((ac[k] + tan_s * wv, P['n_f0'] - P['r_n'] + nv + P['cap_c'] * td_end, P['w_knuckle'] + wv))
        fin_rows[k] = (rows, C)
        r1_ = rows[0]
        WL1, D1, WR1, P1 = r1_[0], r1_[1:5], r1_[5], r1_[6:10][::-1]
        top = [WL1] + list(D1) + [WR1]; bot = [WL1] + list(P1) + [WR1]
        for q in range(5):
            B.face(Dr(5 * k + q), Dr(5 * k + q + 1), top[q + 1], top[q])
            B.face(Pr(5 * k + q), Pr(5 * k + q + 1), bot[q + 1], bot[q])
        for m in range(len(rows) - 1):
            for i in range(10):
                i2 = (i + 1) % 10
                B.face(rows[m][i], rows[m][i2], rows[m + 1][i2], rows[m + 1][i])
        last = rows[-1]
        for i in range(5):
            B.face(last[2 * i], last[2 * i + 1], last[(2 * i + 2) % 10], C)
    for k in range(3):
        WRk = fin_rows[k][0][0][5]; WLk1 = fin_rows[k + 1][0][0][0]
        B.face(Dr(5 * k + 5), WRk, Pr(5 * k + 5), WLk1)
    info['fin_rows'] = fin_rows
    return fin_rows


# ----------------------------------------------------------------------------- thumb
def catmull(pts, n=240):
    """open Catmull-Rom spline through pts, returns dense polyline"""
    pts = np.asarray(pts, float)
    ext = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]])
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for t in np.linspace(0, 1, n // (len(pts) - 1), endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return np.array(out)


def build_thumb(B, P, ring, hr0, hr1, c0, c1, info):
    N = B.N
    nc = (c1 - c0); nr = (hr1 - hr0)
    top = [ring[hr0][c % 40] for c in range(c0, c1 + 1)]
    right = [ring[r][c1 % 40] for r in range(hr0 + 1, hr1 + 1)]
    bottom = [ring[hr1][c % 40] for c in range(c1 - 1, c0 - 1, -1)]
    left = [ring[r][c0 % 40] for r in range(hr1 - 1, hr0, -1)]
    loop = top + right + bottom + left
    m = len(loop); assert m % 2 == 0
    posl = lambda vid: B.pos[vid - N]
    Lp = np.array([posl(v) for v in loop])
    C_loop = Lp.mean(axis=0)
    pts = np.array(P['thumb_pts'], float).copy()
    if P['thumb_anchor']:
        pts[0] = C_loop
    dense = catmull(pts, 360)
    seg = np.linalg.norm(np.diff(dense, axis=0), axis=1); cum = np.r_[0, np.cumsum(seg)]; tot = cum[-1]

    def axis_at(u):
        d = np.clip(u, 0, 1) * tot
        k = min(np.searchsorted(cum, d, side='right') - 1, len(seg) - 1)
        f = (d - cum[k]) / seg[k]
        c = dense[k] * (1 - f) + dense[k + 1] * f
        tv = dense[min(k + 2, len(dense) - 1)] - dense[max(k - 1, 0)]
        return c, tv / np.linalg.norm(tv)

    def radius_at(u):
        return float(pchip(P['thumb_u'], P['thumb_r'], min(max(u, P['thumb_u'][0]), P['thumb_u'][-1])))

    ref = np.array([1.0, 0.0, 0.0])
    def frame(tv):
        uu = ref - ref.dot(tv) * tv; uu /= np.linalg.norm(uu); vv = np.cross(tv, uu); return uu, vv

    u1 = P['thumb_first'] / tot
    c1v, t1v = axis_at(u1)
    uu, vv = frame(t1v)
    psi = np.arctan2((Lp - c1v) @ vv, (Lp - c1v) @ uu)
    dk = Lp - C_loop
    nsh = P['thumb_rows'] - len(P['cap_angles'])
    u0 = u1; u_cap = P['thumb_cap']
    us = [u0 + (u_cap - u0) * (j / max(nsh - 1, 1)) for j in range(nsh)]
    capang = np.radians(P['cap_angles'])
    us += [u_cap + (1 - u_cap) * np.sin(c_) for c_ in capang]
    capr = [1.0] * nsh + [np.cos(c_) for c_ in capang]
    tm = P['thumb_morph']
    thumb_rows = []; thumb_centers = []
    for j, u in enumerate(us):
        c, tv = axis_at(min(u, 0.999)); uu, vv = frame(tv); thumb_centers.append(c)
        rad = radius_at(min(u, u_cap)) * capr[j]
        bump = 1 + P['thumb_bump'] * gauss(min(u, u_cap), 0.64, 0.055)
        g = smooth01(j / tm) if tm > 0 else 1.0
        ids = []
        for k in range(m):
            p_ = psi[k]
            circ = rad * bump * (np.cos(p_) * uu) + rad * bump * P['thumb_flat'] * (np.sin(p_) * vv)
            pos = c + (1 - g) * dk[k] + g * circ
            ids.append(B.add(pos))
        thumb_rows.append(ids)
    for k in range(m):
        k2 = (k + 1) % m
        B.face(loop[k], loop[k2], thumb_rows[0][k2], thumb_rows[0][k])
    for j in range(len(thumb_rows) - 1):
        for k in range(m):
            k2 = (k + 1) % m
            B.face(thumb_rows[j][k], thumb_rows[j][k2], thumb_rows[j + 1][k2], thumb_rows[j + 1][k])
    Ct = B.add(axis_at(1.0)[0])
    last = thumb_rows[-1]
    for i in range(m // 2):
        B.face(last[2 * i], last[2 * i + 1], last[(2 * i + 2) % m], Ct)
    info['thumb_rows'] = thumb_rows; info['thumb_loop'] = loop; info['thumb_tip'] = Ct; info['thumb_centers'] = thumb_centers
    info['thumb_axis'] = (dense, cum)


# ----------------------------------------------------------------------------- whole hand
def build_hand(ring_ids, ring_L, N_existing, params=None):
    P = dict(P0); P.update(params or {})
    P['f_tip'] = [P['w_knuckle'] + (t - P['w_knuckle']) * P['len_scale'] for t in P['f_tip']]
    P['splay_deg'] = [a * P['splay_scale'] for a in P['splay_deg']]
    P['flex'] = [(f[0] + P['mcp_flex'], f[1], f[2]) for f in P['flex']]
    P['thumb_r'] = [r * P['thumb_r_scale'] for r in P['thumb_r']]
    tp = [list(p) for p in P['thumb_pts']]
    d3 = np.array(tp[3]) - np.array(tp[2])
    tp[3] = list(np.array(tp[2]) + d3 * P['thumb_len_scale'])
    tp[2][1] += 0.5 * P['thumb_pitch']; tp[3][1] += P['thumb_pitch']
    if P['thumb_ip_bend'] != 0:
        d1 = np.array(tp[2]) - np.array(tp[1]); d2 = np.array(tp[3]) - np.array(tp[2])
        th1 = np.arctan2(d1[1], d1[2]); th2 = np.arctan2(d2[1], d2[2]) ; L2 = np.hypot(d2[1], d2[2])
        th2n = th1 + np.radians(P['thumb_ip_bend'])
        d2n = np.array([d2[0], L2 * np.sin(th2n), L2 * np.cos(th2n)])
        tp[3] = list(np.array(tp[2]) + d2n)
    P['thumb_pts'] = [tuple(p) for p in tp]
    B = Builder(N_existing)
    info = dict(P=P)
    ring_o_idx = list(range(len(ring_ids)))
    # order the weld ring (positions given in local coords, ids = mesh vertex ids)
    Lfull = np.zeros((max(ring_ids) + 1, 3)); Lfull[ring_ids] = ring_L
    ring_o, t_c, cen, (Ar, Br) = order_ring(list(ring_ids), Lfull)
    Pw = Lfull[ring_o]
    ca0 = 0.5 * (np.percentile(Pw[:, 0], 97) + np.percentile(Pw[:, 0], 3))
    cn0 = 0.5 * (np.percentile(Pw[:, 1], 97) + np.percentile(Pw[:, 1], 3))
    A0 = 0.5 * (np.percentile(Pw[:, 0], 97) - np.percentile(Pw[:, 0], 3))
    B0 = 0.5 * (np.percentile(Pw[:, 1], 97) - np.percentile(Pw[:, 1], 3))
    WELD = dict(A=A0, B=B0, ca=ca0, cn=cn0, w=float(Pw[:, 2].mean()))
    w_rows = np.array(P['w_rows']); nrow = len(w_rows)
    assert abs(w_rows[-1] - P['w_knuckle']) < 1e-9
    lob = lobed_ring(P)
    ring = {}
    tt = np.r_[t_c - 1.0, t_c, t_c + 1.0]
    Pper = np.tile(Pw, (3, 1))
    poly = lambda tq: np.stack([np.interp(tq, tt, Pper[:, k]) for k in range(3)], 1)
    tq = np.arange(40) / 40.0
    P0r = poly(tq)
    w_weld = float(Pw[:, 2].mean())
    for r in range(1, nrow + 1):
        w = w_rows[r - 1]
        E = ellipse_ring(w, P, WELD)
        f = smooth01((w - 0.015) / (P['w_knuckle'] - 0.015)) ** 1.2
        if r == nrow: f = 1.0
        target = (1 - f) * E + f * lob
        sb = smooth01((w - w_weld) / P['span'])
        xy = (1 - sb) * P0r[:, :2] + sb * target
        wz = (1 - sb) * (P0r[:, 2] + (w - w_weld)) + sb * w
        if P['ridge'] > 0:
            rw = smooth01((w - P['ridge_w'][0]) / (P['ridge_w'][1] - P['ridge_w'][0]))
            ac, S = finger_centers(P)
            for i in range(1, 20):
                lobe = max(np.exp(-((xy[i, 0] - a_c) / (0.42 * S)) ** 2) for a_c in ac)
                xy[i, 1] -= P['ridge'] * rw * lobe
        ring[r] = [B.add((xy[i, 0], xy[i, 1], wz[i])) for i in range(40)]
    c0, c1 = P['hole_cols']; hr0, hr1 = P['hole_rows']
    hole = set((r, i % 40) for r in range(hr0, hr1) for i in range(c0, c1))
    for r in range(1, nrow):
        for i in range(40):
            if (r, i) in hole: continue
            i2 = (i + 1) % 40
            B.face(ring[r][i], ring[r][i2], ring[r + 1][i2], ring[r + 1][i])
    # weld bridging
    nc = len(ring_o)
    tB = np.arange(40) / 40.0
    b0 = int(np.argmin(np.abs(((tB - t_c[0] + 0.5) % 1.0) - 0.5)))
    Bv = [ring[1][(b0 + k) % 40] for k in range(40)]
    tA_u = np.r_[(t_c - t_c[0]) % 1.0, 1.0]
    tB_u = np.r_[np.array([(tB[(b0 + k) % 40] - tB[b0]) % 1.0 for k in range(40)]), 1.0]
    a = 0; b = 0
    while a < nc or b < 40:
        if a == nc: adv = 'b'
        elif b == 40: adv = 'a'
        else:
            ta, tb = tA_u[a + 1], tB_u[b + 1]
            adv = 'ab' if abs(ta - tb) < 0.010 else ('a' if ta < tb else 'b')
        va, vb = ring_o[a % nc], Bv[b % 40]
        if adv == 'ab':
            B.face(va, ring_o[(a + 1) % nc], Bv[(b + 1) % 40], vb); a += 1; b += 1
        elif adv == 'a':
            B.face(va, ring_o[(a + 1) % nc], vb); a += 1
        else:
            B.face(va, Bv[(b + 1) % 40], vb); b += 1
    kn = ring[nrow]
    build_fingers(B, P, kn, info)
    build_thumb(B, P, ring, hr0, hr1, c0, c1, info)
    info['ring'] = ring; info['ring_o'] = ring_o; info['w_rows'] = w_rows
    fillet_web(B, info)
    post_smooth(B, info, ring_ids, ring_L)
    return B, info



# ----------------------------------------------------------------------------- web / root fillet
def fillet_web(B, info):
    """Smooth-union style fillet between the palm and the thumb: every palm / thumb vertex within k of the other part is pushed along the
    bisector of the two outward normals by (k/4) h^2, h = max(1 - d/k, 0)  (polynomial smooth-min offset).  Rounds the web crotch and swells the root."""
    P = info['P']; k = P['web_k']
    if k <= 0: return
    N = B.N; pos = np.array(B.pos)
    ring = info['ring']; w_rows = info['w_rows']
    if P.get('web_clear', 0) > 0:
        dense, cum = info['thumb_axis']; tot = cum[-1]
        hr0_, hr1_ = P['hole_rows']; c0_, c1_ = P['hole_cols']
        loopset = set(v - N for v in info['thumb_loop'])
        for r, ids in ring.items():
            if r < hr1_ - 1: continue
            for i, v in enumerate(ids):
                q = pos[v - N]
                if (v - N) in loopset: continue
                d = np.linalg.norm(dense - q, axis=1); kk = int(d.argmin()); u = cum[kk] / tot
                rad = float(pchip(P['thumb_u'], P['thumb_r'], min(max(u, P['thumb_u'][0]), P['thumb_u'][-1]))) * P['web_clear_r']
                sd = d[kk] - rad
                if sd < P['web_clear']:
                    dirv = q - dense[kk]; dirv /= max(np.linalg.norm(dirv), 1e-9)
                    pos[v - N] = dense[kk] + dirv * (rad + P['web_clear'])
        for i in range(len(pos)): B.pos[i] = pos[i]
        pos = np.array(B.pos)
    # palm vertices + analytic outward normals (ellipse gradient about the ring centre at that w)
    pal_i = []; pal_n = []
    hr0, hr1 = P['hole_rows']; c0, c1 = P['hole_cols']
    hole_int = set((r, i % 40) for r in range(hr0 + 1, hr1) for i in range(c0 + 1, c1))
    for r, ids in ring.items():
        if r < 3 or r >= len(w_rows): continue
        ca = 0.5 * (max(pos[v - N][0] for v in ids) + min(pos[v - N][0] for v in ids))
        cn = 0.5 * (max(pos[v - N][1] for v in ids) + min(pos[v - N][1] for v in ids))
        A_ = 0.5 * (max(pos[v - N][0] for v in ids) - min(pos[v - N][0] for v in ids)); B_ = 0.5 * (max(pos[v - N][1] for v in ids) - min(pos[v - N][1] for v in ids))
        for i, v in enumerate(ids):
            if (r, i) in hole_int: continue
            p = pos[v - N]; nv = np.array([(p[0] - ca) / A_ ** 2, (p[1] - cn) / B_ ** 2, 0.0]); nv /= max(np.linalg.norm(nv), 1e-9)
            pal_i.append(v - N); pal_n.append(nv)
    pal_i = np.array(pal_i); pal_n = np.array(pal_n)
    # thumb vertices + normals
    th_i = []; th_n = []
    for j, ids in enumerate(info['thumb_rows']):
        c = info['thumb_centers'][j]
        for v in ids:
            d_ = pos[v - N] - c; th_i.append(v - N); th_n.append(d_ / max(np.linalg.norm(d_), 1e-9))
    th_i = np.array(th_i); th_n = np.array(th_n)
    # shared loop vertices also count as thumb surface (normal = palm normal there)
    loop = [v - N for v in info['thumb_loop']]
    new = pos.copy()
    # palm -> thumb
    Pp = pos[pal_i]; Tt = pos[th_i]
    D = np.linalg.norm(Pp[:, None, :] - Tt[None, :, :], axis=2)
    j = D.argmin(1); d = D[np.arange(len(pal_i)), j]
    h = np.clip(1 - d / k, 0, 1)
    dirv = pal_n + th_n[j]; nrm = np.linalg.norm(dirv, axis=1, keepdims=True)
    dirv = np.where(nrm > 0.35, dirv / np.maximum(nrm, 1e-9), pal_n)
    off = (P['web_amp'] * k / 4.0) * h * h
    # only the distal / palmar side of the root and the web: weight by how far the palm vertex lies from the loop proximal edge
    for a_, v in enumerate(pal_i):
        if v in set(loop) and False: pass
    new[pal_i] += dirv * off[:, None]
    # thumb -> palm (first rows only)
    m = np.array([int(vid_row) for vid_row in range(len(th_i))])
    Dt = np.linalg.norm(Tt[:, None, :] - Pp[None, :, :], axis=2)
    jj = Dt.argmin(1); dd = Dt[np.arange(len(th_i)), jj]
    hh = np.clip(1 - dd / k, 0, 1)
    dirt = th_n + pal_n[jj]; nt = np.linalg.norm(dirt, axis=1, keepdims=True)
    dirt = np.where(nt > 0.35, dirt / np.maximum(nt, 1e-9), th_n)
    offt = (P['web_amp'] * k / 4.0) * hh * hh
    new[th_i] += dirt * offt[:, None]
    for i in range(len(pos)): B.pos[i] = new[i]

# ----------------------------------------------------------------------------- smoothing
def post_smooth(B, info, ring_ids, ring_L):
    """Taubin smoothing of the new shell with the weld ring fixed. Weights: strong around the thumb root (rounds the loop polygon,
    fills the web crotch), light on the palm and the first finger rows, zero on the tips."""
    P = info['P']
    if P['sm_iters'] <= 0: return
    N = B.N
    pos = np.array(B.pos)
    n = len(pos)
    # edges among new vertices; edges to the fixed weld ring act as anchors
    ring_set = {int(v): i for i, v in enumerate(ring_ids)}
    E = set(); anch = {}
    for f in B.faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            if a >= N and b >= N: E.add((min(a, b) - N, max(a, b) - N))
            elif a >= N and b in ring_set: anch.setdefault(a - N, set()).add(b)
            elif b >= N and a in ring_set: anch.setdefault(b - N, set()).add(a)
    E = np.array(sorted(E))
    ringpos = {int(v): ring_L[i] for i, v in enumerate(ring_ids)}
    # weights
    wgt = np.zeros(n)
    ring = info['ring']
    for r, ids in ring.items():
        for v in ids: wgt[v - N] = P['sm_palm_w'] * (1.0 if r > 1 else 0.6)
    cl = np.array([B.pos[v - N] for v in info['thumb_loop']]).mean(0)
    for j, ids in enumerate(info['thumb_rows']):
        for v in ids:
            wgt[v - N] = 0.0
    tpos = pos.copy()
    # thumb root zone by distance (palm + thumb vertices)
    d = np.linalg.norm(pos - cl, axis=1)
    zone = np.clip(1 - d / P['sm_thumb_R'], 0, 1); zone = zone * zone * (3 - 2 * zone)
    thumb_ids = set(v - N for ids in info['thumb_rows'] for v in ids)
    palm_ids = set(v - N for ids in ring.values() for v in ids)
    fin_ids = set()
    for k, (rows, C) in info['fin_rows'].items():
        for m, ids in enumerate(rows):
            for v in ids: fin_ids.add(v - N)
    for i in range(n):
        if i in palm_ids or i in thumb_ids:
            wgt[i] = max(wgt[i], P['sm_thumb_w'] * zone[i])
    # thumb tube beyond the root: light smoothing of the first rows only
    for j, ids in enumerate(info['thumb_rows']):
        fade = max(0.0, 1 - j / 6.0)
        for v in ids: wgt[v - N] = max(wgt[v - N], 0.7 * fade * (1 if j < 6 else 0))
    for k, (rows, C) in info['fin_rows'].items():
        for m, ids in enumerate(rows[:3]):
            for v in ids: wgt[v - N] = max(wgt[v - N], P['sm_fin_w'] * (1 - m / 3.0))
        for ids in rows[-(len(P['cap_angles']) + 1):]:
            for v in ids: wgt[v - N] = max(wgt[v - N], P['sm_tip_w'])
        wgt[C - N] = max(wgt[C - N], P['sm_tip_w'])
    deg = np.bincount(E.ravel(), minlength=n).astype(float)
    anchor_sum = np.zeros((n, 3)); anchor_cnt = np.zeros(n)
    for i, S in anch.items():
        for v in S: anchor_sum[i] += ringpos[v]; anchor_cnt[i] += 1
    deg_t = deg + anchor_cnt
    w_ = wgt[:, None]
    def lap(q):
        s_ = np.zeros_like(q)
        np.add.at(s_, E[:, 0], q[E[:, 1]]); np.add.at(s_, E[:, 1], q[E[:, 0]])
        s_ = s_ + anchor_sum
        return s_ / np.maximum(deg_t, 1)[:, None] - q
    p = pos.copy()
    lam, mu = 0.5, -0.53
    for _ in range(P['sm_iters']):
        p = p + lam * w_ * lap(p)
        p = p + mu * w_ * lap(p)
    for i in range(n): B.pos[i] = p[i]
    info['smooth_w'] = wgt
