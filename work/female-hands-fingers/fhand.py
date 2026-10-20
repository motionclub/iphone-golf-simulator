"""fhand - FEMALE hand generator (local frame: a = across the palm, +a = thumb side; n = palm normal, +n = palm side; w = along the hand).

Same construction family as the male FORM2/FORM3 generator (work/male-arms-hands-form2/hand3.py, work/male-hands-form3/hand4.py):
  weld ring (18 verts from the arm) -> palm "pillow" rings -> lobed knuckle ring -> 4 slit fingers + a thumb grown from a hole in the
  palmar-radial flank (thenar mound, smooth-union web fillet, Catmull-Rom axis with MCP / IP nodes, round pad caps).
Changes for the female hand: slender dimensions, an 18-vertex weld ring, finger-ring density parameter m (finger ring = 2m+2 verts,
palm ring = 8(m+1) verts), thumb hole addressed by w, optional neck rows for the lower (-x) wrist ring, cap rows parametrised by n_cap.

Usage:  B, info = build_hand(ring_ids, ring_L, N_existing, params)
  ring_ids : mesh vertex ids of the 18-vertex wrist weld ring;  ring_L : their local coordinates (n,3)
  returns a Builder (B.pos local positions of NEW vertices, B.faces with ids >= N for new vertices) and an info dict.
"""
import numpy as np
from femlib import smooth01, pchip, catmull, gauss, order_ring

P0 = dict(
    m=3,                                   # dorsal verts per finger ring -> finger ring 2m+2, palm ring 8(m+1)
    # ---- palm rings (absolute w from the wrist crease)
    w_rows=[0.0060, 0.0135, 0.0210, 0.0285, 0.0360, 0.0435, 0.0510, 0.0585, 0.0660, 0.0735, 0.0806],
    w_knuckle=0.0806, span=0.045, p_exp=2.3,
    A_tab=([0.0, 0.02, 0.04, 0.06, 0.0806], [0.0290, 0.0305, 0.0318, 0.0328, 0.0335]),      # palm half width (across)
    B_tab=([0.0, 0.02, 0.04, 0.06, 0.0806], [0.0285, 0.0215, 0.0150, 0.0110, 0.0088]),      # palm half thickness
    NC_tab=([0.0, 0.02, 0.04, 0.06, 0.0806], [0.0, -0.0075, -0.0125, -0.0160, -0.0185]),    # centre offset along n (negative = dorsal)
    palm_thick=0.0010, ridge=0.0016, ridge_w=(0.040, 0.0806),
    thenar=0.0065, thenar_w=(0.0, 0.026, 0.056), thenar_ang=-7 * np.pi / 4, thenar_sig=0.70, hypo=0.0025, lob_from=0.045,
    # ---- fingers
    r_a=0.0068, r_n=0.0078, gap=0.0030, n_f0=-0.0105, h_valley=0.0042,
    len_ratio=[0.90, 1.00, 0.93, 0.77], mid_tip=0.1537,        # projected tip w of the middle finger; others by ratio of (tip - w_knuckle)
    splay_deg=[5.0, 1.6, -1.8, -5.6],
    flex=[(14, 28, 16), (16, 32, 18), (18, 36, 20), (20, 38, 22)], curl=0.6,     # MCP, PIP, DIP flexion (deg) toward the palm, x curl
    s_pip=0.38, s_dip=0.71, tilt_w=0.07,
    ka=([0, 0.15, 0.38, 0.55, 0.71, 0.86, 1.0], [1.0, 0.975, 0.90, 0.83, 0.76, 0.69, 0.62]),
    kd=([0, 0.12, 0.25, 0.38, 0.55, 0.71, 0.86, 1.0], [1.0, 0.90, 0.82, 0.77, 0.71, 0.66, 0.62, 0.58]),
    kp=([0, 0.12, 0.25, 0.38, 0.55, 0.71, 0.86, 1.0], [1.0, 0.90, 0.82, 0.77, 0.71, 0.66, 0.62, 0.58]),
    bump_pip=0.30, bump_dip=0.12, bump_sig=0.055, side_swell=0.025,
    pad_tip=0.12, pad_sig=0.09, crease=0.025,
    kp_scale=1.12, len_scale=1.0, splay_scale=1.0, A_gain=1.0, B_gain=1.0, NC_gain=1.0, fing_scale=1.0, forearm_taper=-0.09, thumb_a_shift=0.0, thumb_n_shift=0.0,
    cap_len_f=1.2, cap_sym=0.6, n_cap=6,
    shaft_s=[0.10, 0.22, 0.33, 0.42, 0.52, 0.62, 0.72, 0.80],
    # ---- thumb (hole addressed by w and by column fractions of the ring)
    hole_w=(0.0210, 0.0435), hole_cols_frac=(0.80, 0.92),                 # root hole on the palmar-radial corner (ring angle ~30-70 deg)
    thumb_pts=[(0.026, 0.004, 0.030), (0.024, 0.017, 0.050), (0.028, 0.022, 0.076), (0.028, 0.027, 0.104)],
    thumb_u=[0.0, 0.18, 0.30, 0.46, 0.58, 0.66, 0.78, 0.90],
    thumb_r=[0.0092, 0.0102, 0.0103, 0.0094, 0.0088, 0.0092, 0.0082, 0.0072],
    thumb_flat=0.92, thumb_bump=0.36, thumb_first=0.012, thumb_morph=4.5, thumb_shaft=9, cap_len_t=1.2,
    thumb_follow=1.0, thumb_ref=None, root_lift=0.010, root_down=0.004, thumb_ip_bend=15.0, thumb_len_scale=1.0, thumb_r_scale=1.0, thumb_pitch=0.0, thumb_anchor=1,
    # ---- fillet / smoothing
    web_k=0.030, web_amp=1.4, web_clear=0.0012, web_clear_r=1.0,
    sm_thumb_R=0.090, sm_thumb_w=1.0, sm_palm_w=0.12, sm_fin_w=0.30, sm_tip_w=0.0, sm_iters=120, sm_rows=None, sm_freeze_w=0.0135,
)


class Builder:
    def __init__(self, n_existing):
        self.N = n_existing; self.pos = []; self.faces = []
    def add(self, p):
        self.pos.append(np.asarray(p, float)); return self.N + len(self.pos) - 1
    def face(self, *ids):
        self.faces.append(tuple(int(i) for i in ids))


# ----------------------------------------------------------------------------- palm
def _tab(tab, w):
    return np.interp(w, tab[0], tab[1])


def ellipse_ring(w, P, WELD, nverts):
    A = _tab(P['A_tab'], w) * P['A_gain']
    B = (_tab(P['B_tab'], w) + P['palm_thick'] * smooth01((w - 0.03) / 0.05)) * P['B_gain']
    nc = _tab(P['NC_tab'], w) * P['NC_gain']
    ca = 0.0
    if WELD['A'] is not None:
        sb = smooth01((w - WELD['w']) / WELD['span'])
        dT = P['forearm_taper'] * (w - WELD['w'])               # the forearm keeps tapering below the ring: C1 continuity at the weld
        A_s, B_s = WELD['A'] + dT, WELD['B'] + dT
        A = A_s + (A - A_s) * sb
        B = B_s + (B - B_s) * sb
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
    LC = P['m'] + 1; NR = 8 * LC; half = 4 * LC
    ac, S = finger_centers(P)
    ra, rn, nf, hv = P['r_a'], P['r_n'], P['n_f0'], P['h_valley']
    out = np.zeros((NR, 2))
    out[0] = (ac[0] + ra, nf); out[half] = (ac[3] - ra, nf)
    phi = np.radians(-90 + (180.0 / LC) * np.arange(0, LC + 1))
    for j in range(1, half):
        k, q = divmod(j, LC)
        if q == 0:
            av = 0.5 * (ac[k - 1] + ac[k])
            out[j] = (av, nf - hv); out[NR - j] = (av, nf + hv)
        else:
            ph = phi[q]; a = ac[k] - ra * np.sin(ph)
            out[j] = (a, nf - rn * np.cos(ph)); out[NR - j] = (a, nf + rn * np.cos(ph))
    return out


# ----------------------------------------------------------------------------- fingers
def finger_profile(P, s, k):
    """lateral half width, dorsal half depth, palmar half depth at arclength fraction s (0 = knuckle ring, 1 = tip pole)"""
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
    f1, f2, f3 = [np.radians(x * P['curl']) for x in P['flex'][k]]
    s = np.linspace(0, 1, n_samples)
    tw = P['tilt_w']
    th = f1 * smooth01(s / 0.16) + f2 * smooth01((s - (P['s_pip'] - tw)) / (2 * tw)) + f3 * smooth01((s - (P['s_dip'] - tw)) / (2 * tw))
    ds = s[1] - s[0]
    dw = np.cos(th) * ds; dn = np.sin(th) * ds                     # +n = toward the palm
    w = np.r_[0, np.cumsum(0.5 * (dw[1:] + dw[:-1]))]
    n = np.r_[0, np.cumsum(0.5 * (dn[1:] + dn[:-1]))]
    return s, th, w, n


def build_fingers(B, P, kn, info):
    m = P['m']; LC = m + 1; NR = 8 * LC; NV = 2 * LC
    ac, S = finger_centers(P)
    Dr = lambda j: kn[j]
    Pr = lambda j: kn[(NR - j) % NR]
    fin_rows = {}
    n_cap = P['n_cap']
    capang = np.radians(90.0 * np.arange(1, n_cap + 1) / (n_cap + 1))
    tips = [P['w_knuckle'] + (P['mid_tip'] - P['w_knuckle']) * r * P['len_scale'] for r in P['len_ratio']]
    for k in range(4):
        Lw = tips[k] - P['w_knuckle']
        s_, th_, w_, n_ = finger_axis(P, k)
        Larc = Lw / w_[-1]
        # round cap: axial length = cap_len_f x mean(lateral half width, mean half depth) of the last shaft ring (iterate)
        s_cap = 0.9
        for _ in range(4):
            ra_c, rd_c, rp_c = finger_profile(P, s_cap, k)
            Lc = P['cap_len_f'] * 0.5 * (ra_c + 0.5 * (rd_c + rp_c))
            s_cap = 1.0 - Lc / Larc
        ra_c, rd_c, rp_c = finger_profile(P, s_cap, k)
        td_c = float(pchip(P['kd'][0], P['kd'][1], s_cap)) * P['r_n']
        dn = P['cap_sym'] * 0.5 * (rp_c - td_c)                 # pole offset toward the palm
        shaft = [s for s in P['shaft_s'] if s < s_cap - 0.03] + [s_cap]
        sv = shaft + [s_cap + (1 - s_cap) * np.sin(c_) for c_ in capang]
        capr = [1.0] * len(shaft) + [np.cos(c_) for c_ in capang]
        tan_s = np.tan(np.radians(P['splay_deg'][k] * P['splay_scale']))
        rows = []
        for mm, s in enumerate(sv):
            sc = min(s, s_cap)
            ra, rd, rp = finger_profile(P, sc, k)
            td = float(pchip(P['kd'][0], P['kd'][1], sc)) * P['r_n']
            if mm >= len(shaft):
                cr = capr[mm]
                ra = ra_c * cr; rd = rd_c * cr; rp = rp_c * cr
                td = td_c * cr + (td_c + dn) * (1.0 - cr)
            idx = np.searchsorted(s_, min(s, 1.0)); idx = min(max(idx, 1), len(s_) - 1)
            f = (min(s, 1.0) - s_[idx - 1]) / (s_[idx] - s_[idx - 1])
            th = th_[idx - 1] * (1 - f) + th_[idx] * f
            wv = Larc * (w_[idx - 1] * (1 - f) + w_[idx] * f); nv = Larc * (n_[idx - 1] * (1 - f) + n_[idx] * f)
            w = P['w_knuckle'] + wv; nD = P['n_f0'] - P['r_n'] + nv          # dorsal polyline (n, w)
            un, uw = np.cos(th), -np.sin(th)                       # unit vector toward +n (palmar) perpendicular to the tangent
            n0 = nD + td * un; wc = w + td * uw                    # ring centre sits td below the dorsal line (nail-side contour stays straight)
            ack = ac[k] + tan_s * (w - P['w_knuckle'])
            ph = np.radians(-90 + (180.0 / LC) * np.arange(1, LC))
            def pt(a_, off):
                return (a_, n0 + off * un, wc + off * uw)
            WL = B.add(pt(ack + ra, 0.0)); WR = B.add(pt(ack - ra, 0.0))
            Dq = [B.add(pt(ack - ra * np.sin(p_), -rd * np.cos(p_))) for p_ in ph]
            Pq = [B.add(pt(ack - ra * np.sin(p_), +rp * np.cos(p_))) for p_ in ph]
            rows.append([WL] + Dq + [WR] + Pq[::-1])
        wv = Larc * w_[-1]; nv = Larc * n_[-1]
        th_e = th_[-1]; un_e, uw_e = np.cos(th_e), -np.sin(th_e)
        off = td_c + dn
        C = B.add((ac[k] + tan_s * wv, P['n_f0'] - P['r_n'] + nv + off * un_e, P['w_knuckle'] + wv + off * uw_e))
        fin_rows[k] = (rows, C)
        info.setdefault('fin_s', {})[k] = (list(sv), len(shaft), float(Larc), float(s_cap))
        r1_ = rows[0]
        WL1, D1, WR1, P1 = r1_[0], r1_[1:LC], r1_[LC], r1_[LC + 1:NV][::-1]
        top = [WL1] + list(D1) + [WR1]; bot = [WL1] + list(P1) + [WR1]
        for q in range(LC):
            B.face(Dr(LC * k + q), Dr(LC * k + q + 1), top[q + 1], top[q])
            B.face(Pr(LC * k + q), Pr(LC * k + q + 1), bot[q + 1], bot[q])
        for mm in range(len(rows) - 1):
            for i in range(NV):
                i2 = (i + 1) % NV
                B.face(rows[mm][i], rows[mm][i2], rows[mm + 1][i2], rows[mm + 1][i])
        last = rows[-1]
        for i in range(LC):
            B.face(last[2 * i], last[2 * i + 1], last[(2 * i + 2) % NV], C)
    for k in range(3):
        WRk = fin_rows[k][0][0][LC]; WLk1 = fin_rows[k + 1][0][0][0]
        B.face(Dr(LC * k + LC), WRk, Pr(LC * k + LC), WLk1)
    info['fin_rows'] = fin_rows
    return fin_rows


# ----------------------------------------------------------------------------- thumb
def build_thumb(B, P, ring, hr0, hr1, c0, c1, NR, info):
    N = B.N
    top = [ring[hr0][c % NR] for c in range(c0, c1 + 1)]
    right = [ring[r][c1 % NR] for r in range(hr0 + 1, hr1 + 1)]
    bottom = [ring[hr1][c % NR] for c in range(c1 - 1, c0 - 1, -1)]
    left = [ring[r][c0 % NR] for r in range(hr1 - 1, hr0, -1)]
    loop = top + right + bottom + left
    m = len(loop); assert m % 2 == 0
    posl = lambda vid: B.pos[vid - N]
    Lp = np.array([posl(v) for v in loop])
    C_loop = Lp.mean(axis=0)
    pts = np.array(P['thumb_pts'], float).copy()
    if P['thumb_anchor']:
        pts[0] = C_loop
    info['C_loop'] = C_loop.copy()
    if P['thumb_follow'] != 0.0 and P['thumb_ref'] is not None:
        pts[1:] += P['thumb_follow'] * (C_loop - np.array(P['thumb_ref']))
    if P['root_lift'] > 0:
        # outward "root lift": an extra control point along the mean outward palm normal at the root loop, so the tube leaves the thenar bulge
        # roughly perpendicular to the surface (no oblique, folded first strip)
        nus = []
        for r, ids in ring.items():
            pr = np.array([B.pos[v - N] for v in ids]); ca = 0.5 * (pr[:, 0].max() + pr[:, 0].min()); cn = 0.5 * (pr[:, 1].max() + pr[:, 1].min())
            A_ = 0.5 * (pr[:, 0].max() - pr[:, 0].min()); B_ = 0.5 * (pr[:, 1].max() - pr[:, 1].min())
            for v in ids:
                if v in set(loop):
                    q = B.pos[v - N]; nv = np.array([(q[0] - ca) / A_ ** 2, (q[1] - cn) / B_ ** 2, 0.0]); nus.append(nv / max(np.linalg.norm(nv), 1e-9))
        nu = np.mean(nus, axis=0); nu /= max(np.linalg.norm(nu), 1e-9)
        Pb = C_loop + P['root_lift'] * nu + np.array([0.0, 0.0, P['root_down']])
        pts = np.vstack([pts[:1], Pb[None, :], pts[1:]])
        info['root_nu'] = nu
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
    psi_loop = np.arctan2((Lp - c1v) @ vv, (Lp - c1v) @ uu)
    # uniform ring angles aligned (direction + phase) with the root loop: no vertex clustering along the thumb, regular pole faces
    dsum = np.angle(np.exp(1j * np.diff(np.r_[psi_loop, psi_loop[0]]))).sum()
    dirsign = 1.0 if dsum > 0 else -1.0
    uni = dirsign * 2 * np.pi * np.arange(m) / m
    psi0 = np.angle(np.mean(np.exp(1j * (psi_loop - uni))))
    psi_uni = uni + psi0
    psi = np.angle(np.exp(1j * psi_uni))
    dk = Lp - C_loop
    n_cap = P['n_cap']
    capang = np.radians(90.0 * np.arange(1, n_cap + 1) / (n_cap + 1))
    nsh = P['thumb_shaft']
    u0 = u1
    u_cap = 0.9
    for _ in range(5):
        u_cap = 1.0 - P['cap_len_t'] * radius_at(u_cap) / tot
    us = [u0 + (u_cap - u0) * (j / max(nsh - 1, 1)) for j in range(nsh)]
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
def build_hand(ring_ids, ring_L, N_existing, params=None, w_weld_rows=None, ref_ring_L=None):
    """w_weld_rows : optional list of extra neck-row w values (below the first common row) for a ring that sits above the crease.
    ref_ring_L : local coordinates of the REFERENCE wrist ring (the +x ring, mirrored into this frame).  Every row at or below the crease is built from
    the reference ring so both hands are identical beyond the crease (mirror symmetry); the neck rows loft from this hand's own ring to it."""
    P = dict(P0); P.update(params or {})
    P['r_a'] = P['r_a'] * P['fing_scale']; P['r_n'] = P['r_n'] * P['fing_scale']
    P['thumb_r'] = [r * P['thumb_r_scale'] for r in P['thumb_r']]
    tp = [list(p) for p in P['thumb_pts']]
    for q in (1, 2, 3):
        tp[q][0] += P['thumb_a_shift']; tp[q][1] += P['thumb_n_shift']
    d3 = np.array(tp[3]) - np.array(tp[2])
    tp[3] = list(np.array(tp[2]) + d3 * P['thumb_len_scale'])
    tp[2][1] += 0.5 * P['thumb_pitch']; tp[3][1] += P['thumb_pitch']
    if P['thumb_ip_bend'] != 0:
        d1 = np.array(tp[2]) - np.array(tp[1]); d2 = np.array(tp[3]) - np.array(tp[2])
        th1 = np.arctan2(d1[1], d1[2]); L2 = np.hypot(d2[1], d2[2])
        th2n = th1 + np.radians(P['thumb_ip_bend'])
        d2n = np.array([d2[0], L2 * np.sin(th2n), L2 * np.cos(th2n)])
        tp[3] = list(np.array(tp[2]) + d2n)
    P['thumb_pts'] = [tuple(p) for p in tp]
    m = P['m']; LC = m + 1; NR = 8 * LC
    B = Builder(N_existing)
    info = dict(P=P)
    Lfull = np.zeros((max(ring_ids) + 1, 3)); Lfull[list(ring_ids)] = ring_L
    ring_o, t_c, cen, (Ar, Br) = order_ring(list(ring_ids), Lfull)
    Pw = Lfull[ring_o]
    w_real = float(Pw[:, 2].mean())
    if ref_ring_L is None:
        Pref, t_ref = Pw, t_c
    else:
        r_o, t_ref, _, _ = order_ring(list(range(len(ref_ring_L))), np.asarray(ref_ring_L, float))
        Pref = np.asarray(ref_ring_L, float)[r_o]
    ca0 = 0.5 * (np.percentile(Pref[:, 0], 97) + np.percentile(Pref[:, 0], 3))
    cn0 = 0.5 * (np.percentile(Pref[:, 1], 97) + np.percentile(Pref[:, 1], 3))
    A0 = 0.5 * (np.percentile(Pref[:, 0], 97) - np.percentile(Pref[:, 0], 3))
    B0 = 0.5 * (np.percentile(Pref[:, 1], 97) - np.percentile(Pref[:, 1], 3))
    w_weld = float(Pref[:, 2].mean())
    WELD = dict(A=A0, B=B0, ca=ca0, cn=cn0, w=w_weld, span=P['span'])
    w_rows = np.array((list(w_weld_rows) if w_weld_rows else []) + list(P['w_rows']))
    nrow = len(w_rows)
    assert abs(w_rows[-1] - P['w_knuckle']) < 1e-9
    lob = lobed_ring(P)
    ring = {}
    def periodic_poly(tc, Pc):
        tt = np.r_[tc - 1.0, tc, tc + 1.0]; Pper = np.tile(Pc, (3, 1))
        return lambda tq: np.stack([np.interp(tq, tt, Pper[:, k]) for k in range(3)], 1)
    tq = np.arange(NR) / NR
    P0r = periodic_poly(t_ref, Pref)(tq)                     # reference ring resampled at the palm-ring angles
    P0r_real = periodic_poly(t_c, Pw)(tq)                    # this hand's own ring (only differs from the reference for the -x neck)
    half = 4 * LC
    for r in range(1, nrow + 1):
        w = w_rows[r - 1]
        neck = (ref_ring_L is not None) and (w < w_weld + 0.0015) and (w_real < w_weld - 0.004)
        if neck:
            tau = smooth01((w - w_real) / (w_weld - w_real))
            xy = (1 - tau) * P0r_real[:, :2] + tau * P0r[:, :2]
            wz = (1 - tau) * (P0r_real[:, 2] + (w - w_real)) + tau * (P0r[:, 2] + (w - w_weld))
        else:
            E = ellipse_ring(w, P, WELD, NR)
            f = smooth01((w - P['lob_from']) / (P['w_knuckle'] - P['lob_from'])) ** 1.2
            if r == nrow: f = 1.0
            target = (1 - f) * E + f * lob
            sb = smooth01((w - w_weld) / P['span'])
            xy = (1 - sb) * P0r[:, :2] + sb * target
            wz = (1 - sb) * (P0r[:, 2] + (w - w_weld)) + sb * w
            if P['ridge'] > 0:
                rw = smooth01((w - P['ridge_w'][0]) / (P['ridge_w'][1] - P['ridge_w'][0]))
                ac, S = finger_centers(P)
                for i in range(1, half):
                    lobe = max(np.exp(-((xy[i, 0] - a_c) / (0.42 * S)) ** 2) for a_c in ac)
                    xy[i, 1] -= P['ridge'] * rw * lobe
        ring[r] = [B.add((xy[i, 0], xy[i, 1], wz[i])) for i in range(NR)]
    # thumb hole addressed by w and column fractions
    hw0, hw1 = P['hole_w']
    hr0 = int(np.argmin(np.abs(w_rows - hw0))) + 1; hr1 = int(np.argmin(np.abs(w_rows - hw1))) + 1
    c0 = int(round(P['hole_cols_frac'][0] * NR)); c1 = int(round(P['hole_cols_frac'][1] * NR))
    info['hole'] = (hr0, hr1, c0, c1)
    hole = set((r, i % NR) for r in range(hr0, hr1) for i in range(c0, c1))
    for r in range(1, nrow):
        for i in range(NR):
            if (r, i) in hole: continue
            i2 = (i + 1) % NR
            B.face(ring[r][i], ring[r][i2], ring[r + 1][i2], ring[r + 1][i])
    # weld bridging (ring_o has len(ring_ids) verts, ring[1] has NR verts)
    nc = len(ring_o)
    tB = np.arange(NR) / NR
    b0 = int(np.argmin(np.abs(((tB - t_c[0] + 0.5) % 1.0) - 0.5)))
    Bv = [ring[1][(b0 + k) % NR] for k in range(NR)]
    tA_u = np.r_[(t_c - t_c[0]) % 1.0, 1.0]
    tB_u = np.r_[np.array([(tB[(b0 + k) % NR] - tB[b0]) % 1.0 for k in range(NR)]), 1.0]
    a = 0; b = 0
    tol = 0.35 / NR
    while a < nc or b < NR:
        if a == nc: adv = 'b'
        elif b == NR: adv = 'a'
        else:
            ta, tb = tA_u[a + 1], tB_u[b + 1]
            adv = 'ab' if abs(ta - tb) < tol else ('a' if ta < tb else 'b')
        va, vb = ring_o[a % nc], Bv[b % NR]
        if adv == 'ab':
            B.face(va, ring_o[(a + 1) % nc], Bv[(b + 1) % NR], vb); a += 1; b += 1
        elif adv == 'a':
            B.face(va, ring_o[(a + 1) % nc], vb); a += 1
        else:
            B.face(va, Bv[(b + 1) % NR], vb); b += 1
    kn = ring[nrow]
    build_fingers(B, P, kn, info)
    build_thumb(B, P, ring, hr0, hr1, c0, c1, NR, info)
    info['ring'] = ring; info['ring_o'] = ring_o; info['w_rows'] = w_rows; info['NR'] = NR
    fillet_web(B, info)
    post_smooth(B, info, ring_ids, ring_L)
    return B, info


# ----------------------------------------------------------------------------- web / root fillet
def fillet_web(B, info):
    """Smooth-union style fillet between the palm and the thumb: palm / thumb vertices within k of the other part are pushed along the
    bisector of the two outward normals by (amp k/4) h^2, h = max(1 - d/k, 0).  Rounds the web crotch and swells the root."""
    P = info['P']; k = P['web_k']
    if k <= 0: return
    N = B.N; pos = np.array(B.pos)
    ring = info['ring']; w_rows = info['w_rows']
    hr0, hr1, c0, c1 = info['hole']
    if P.get('web_clear', 0) > 0:
        dense, cum = info['thumb_axis']; tot = cum[-1]
        loopset = set(v - N for v in info['thumb_loop'])
        for r, ids in ring.items():
            if r < hr1 - 1: continue
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
    NR = info['NR']
    pal_i = []; pal_n = []
    hole_int = set((r, i % NR) for r in range(hr0 + 1, hr1) for i in range(c0 + 1, c1))
    for r, ids in ring.items():
        if w_rows[r - 1] < 0.020 or r >= len(w_rows): continue
        ca = 0.5 * (max(pos[v - N][0] for v in ids) + min(pos[v - N][0] for v in ids))
        cn = 0.5 * (max(pos[v - N][1] for v in ids) + min(pos[v - N][1] for v in ids))
        A_ = 0.5 * (max(pos[v - N][0] for v in ids) - min(pos[v - N][0] for v in ids)); B_ = 0.5 * (max(pos[v - N][1] for v in ids) - min(pos[v - N][1] for v in ids))
        for i, v in enumerate(ids):
            if (r, i) in hole_int: continue
            p = pos[v - N]; nv = np.array([(p[0] - ca) / A_ ** 2, (p[1] - cn) / B_ ** 2, 0.0]); nv /= max(np.linalg.norm(nv), 1e-9)
            pal_i.append(v - N); pal_n.append(nv)
    pal_i = np.array(pal_i); pal_n = np.array(pal_n)
    th_i = []; th_n = []
    for j, ids in enumerate(info['thumb_rows']):
        c = info['thumb_centers'][j]
        for v in ids:
            d_ = pos[v - N] - c; th_i.append(v - N); th_n.append(d_ / max(np.linalg.norm(d_), 1e-9))
    th_i = np.array(th_i); th_n = np.array(th_n)
    new = pos.copy()
    Pp = pos[pal_i]; Tt = pos[th_i]
    D = np.linalg.norm(Pp[:, None, :] - Tt[None, :, :], axis=2)
    j = D.argmin(1); d = D[np.arange(len(pal_i)), j]
    h = np.clip(1 - d / k, 0, 1)
    dirv = pal_n + th_n[j]; nrm = np.linalg.norm(dirv, axis=1, keepdims=True)
    dirv = np.where(nrm > 0.35, dirv / np.maximum(nrm, 1e-9), pal_n)
    off = (P['web_amp'] * k / 4.0) * h * h
    new[pal_i] += dirv * off[:, None]
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
    """Taubin smoothing of the new shell with the weld ring fixed: strong around the thumb root (rounds the loop polygon, fills the web
    crotch), light on the palm and the first finger rows, zero on the tips."""
    P = info['P']
    if P['sm_iters'] <= 0: return
    N = B.N
    pos = np.array(B.pos); n = len(pos)
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
    wgt = np.zeros(n)
    ring = info['ring']
    for r, ids in ring.items():
        for v in ids: wgt[v - N] = P['sm_palm_w'] * (1.0 if r > 1 else 0.6)
        if P['sm_rows'] is not None and r <= len(P['sm_rows']):
            for v in ids: wgt[v - N] = max(wgt[v - N], P['sm_rows'][r - 1])
    cl = np.array([B.pos[v - N] for v in info['thumb_loop']]).mean(0)
    for j, ids in enumerate(info['thumb_rows']):
        for v in ids: wgt[v - N] = 0.0
    d = np.linalg.norm(pos - cl, axis=1)
    zone = np.clip(1 - d / P['sm_thumb_R'], 0, 1); zone = zone * zone * (3 - 2 * zone)
    thumb_ids = set(v - N for ids in info['thumb_rows'] for v in ids)
    palm_ids = set(v - N for ids in ring.values() for v in ids)
    for i in range(n):
        if i in palm_ids or i in thumb_ids:
            wgt[i] = max(wgt[i], P['sm_thumb_w'] * zone[i])
    for j, ids in enumerate(info['thumb_rows']):
        fade = max(0.0, 1 - j / 6.0)
        for v in ids: wgt[v - N] = max(wgt[v - N], 0.7 * fade * (1 if j < 6 else 0))
    for k, (rows, C) in info['fin_rows'].items():
        for mm, ids in enumerate(rows[:3]):
            for v in ids: wgt[v - N] = max(wgt[v - N], P['sm_fin_w'] * (1 - mm / 3.0))
        if P['sm_tip_w'] > 0:
            for ids in rows[-(P['n_cap'] + 1):]:
                for v in ids: wgt[v - N] = max(wgt[v - N], P['sm_tip_w'])
            wgt[C - N] = max(wgt[C - N], P['sm_tip_w'])
    # rows next to the weld (and any neck rows) are not smoothed: they are constructed identically for both hands, so the smoothing field starts from the same state (mirror symmetry)
    for r, ids in ring.items():
        if info['w_rows'][r - 1] <= P['sm_freeze_w'] + 1e-9:
            for v in ids: wgt[v - N] = 0.0
    deg = np.bincount(E.ravel(), minlength=n).astype(float)
    anchor_sum = np.zeros((n, 3)); anchor_cnt = np.zeros(n)
    for i, S_ in anch.items():
        for v in S_: anchor_sum[i] += ringpos[v]; anchor_cnt[i] += 1
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
