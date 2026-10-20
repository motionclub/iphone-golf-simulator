"""Local hand rebuild: clean palm + 4 fingers + thumb on a welded wrist ring (right-hand local frame, mirrored for left).

Topology (all quads except the 48->40 weld transition):
  ring0  : existing boundary loop of the forearm (kept vertices, positions untouched)
  rings 1..8 : palm pillow, 40 verts/ring  [S_L, D1..D19, S_R, P19..P1]   (i = 0..39)
  row 8  : knuckle row; 4 fingers via slit model (each finger ring: WL, D1..D4, WR, P4..P1 = 10 verts), crotch quads
  thumb  : 3x2 quad block of the palmar-front palm removed -> 10-vertex hole loop bridged to a 10-vertex thumb tube
"""
import numpy as np
import hand_sdf as H
import hand_topo as T

P = dict(
    n_rows=10, w_ring1=-0.044, w_knuckle=0.060,
    p_exp=2.3,
    r_a=0.0125, gap=0.0025, r_n=0.0172, n_f0=-0.0182, curl=0.013, taper=0.10, h_valley=0.0065,
    f_tip=[0.154, 0.167, 0.158, 0.136],                  # finger tip w
    f_rows=[9, 10, 9, 7],
    s_cap=0.82, splay_deg=[11.0, 4.0, -3.0, -10.0],
    thumb_pts=[(0.040, -0.004, 0.036), (0.051, 0.008, 0.042), (0.059, 0.013, 0.066), (0.065, 0.021, 0.098)],
    thumb_r=(0.0185, 0.0185, 0.0165, 0.0148),                    # radius at root / mid / tip (a-dir) ; n-dir 0.92x
    thumb_rows=8, thumb_first=0.012, thumb_cap=0.80,
    hole_cols=(36, 39), hole_rows=(7, 9),
)


def A_of(w):  return np.interp(w, [-0.04, -0.02, 0.0, 0.03, 0.06], [0.0370, 0.0385, 0.0415, 0.0445, 0.0495])
def B_of(w):  return np.interp(w, [-0.04, -0.01, 0.02, 0.045, 0.06], [0.0300, 0.0285, 0.0270, 0.0195, 0.0152])
def NC_of(w): return np.interp(w, [-0.04, 0.0, 0.045, 0.06], [-0.0126, -0.0150, -0.0185, -0.0215])

WELD = dict(A=None, B=None, ca=0.0, cn=None, w=None, span=0.055, rho=None)


def ellipse_ring(w, nverts=40):
    A, B, nc = A_of(w), B_of(w), NC_of(w)
    ca = 0.0
    rho = np.ones(nverts)
    if WELD['A'] is not None:                     # blend from the actual (smoothed) weld ring shape into the palm target
        sb = smooth01((w - WELD['w']) / WELD['span'])
        A = WELD['A'] + (A - WELD['A']) * sb
        B = WELD['B'] + (B - WELD['B']) * sb
        nc = WELD['cn'] + (nc - WELD['cn']) * sb
        ca = WELD['ca'] * (1 - sb)
    t = -2 * np.pi * np.arange(nverts) / nverts
    c, s = np.cos(t), np.sin(t)
    e = 2.0 / P['p_exp']
    a = rho * A * np.sign(c) * np.abs(c) ** e
    n = nc + rho * B * np.sign(s) * np.abs(s) ** e
    return np.stack([a + ca, n], 1)


def finger_centers():
    S = 2 * P['r_a'] + P['gap']
    return [(1.5 - k) * S for k in range(4)], S


def lobed_ring(w):
    """40-vertex lobed ring layout at knuckle (positions (a', n)); index i as in palm ring"""
    ac, S = finger_centers()
    ra, rn, nf, hv = P['r_a'], P['r_n'], P['n_f0'], P['h_valley']
    out = np.zeros((40, 2))
    out[0] = (ac[0] + ra, nf)                              # S_L
    out[20] = (ac[3] - ra, nf)                             # S_R
    phi = np.radians(-90 + 36 * np.arange(0, 6))           # q=0..5
    for j in range(1, 20):
        k, q = divmod(j, 5)
        if q == 0:                                         # valley column between finger k-1 and k
            av = 0.5 * (ac[k - 1] + ac[k])
            out[j] = (av, nf - hv); out[40 - j] = (av, nf + hv)
        else:
            ph = phi[q]
            a = ac[k] - ra * np.sin(ph)
            out[j] = (a, nf - rn * np.cos(ph)); out[40 - j] = (a, nf + rn * np.cos(ph))
    return out


def smooth01(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


class Builder:
    def __init__(self, n_existing):
        self.N = n_existing
        self.pos = []            # new vertex local positions
        self.faces = []
    def add(self, p):
        self.pos.append(np.asarray(p, float)); return self.N + len(self.pos) - 1
    def face(self, *ids):
        self.faces.append(tuple(int(i) for i in ids))


def build_hand(co, F, side, w0=-0.03):
    cut = T.extract_cut(co, F, side, w0)
    L = cut['L']
    ring_o, t_c, cen, (Ar, Br) = T.order_ring(cut['ring'], L)
    N = len(co)
    B = Builder(N)
    Pw = L[ring_o]
    ca0 = float(np.median(Pw[:, 0])) * 0 + 0.5 * (np.percentile(Pw[:, 0], 97) + np.percentile(Pw[:, 0], 3))
    cn0 = 0.5 * (np.percentile(Pw[:, 1], 97) + np.percentile(Pw[:, 1], 3))
    A0 = 0.5 * (np.percentile(Pw[:, 0], 97) - np.percentile(Pw[:, 0], 3))
    B0 = 0.5 * (np.percentile(Pw[:, 1], 97) - np.percentile(Pw[:, 1], 3))
    ang = np.arctan2((Pw[:, 1] - cn0) / B0, (Pw[:, 0] - ca0) / A0)
    rr = np.sqrt(((Pw[:, 0] - ca0) / A0) ** 2 + ((Pw[:, 1] - cn0) / B0) ** 2)
    th = (-ang) % (2 * np.pi)
    o = np.argsort(th); th, rr = th[o], rr[o]
    tq = 2 * np.pi * np.arange(40) / 40
    rho_i = np.interp(tq, np.r_[th - 2 * np.pi, th, th + 2 * np.pi], np.r_[rr, rr, rr])
    # circular smoothing (window 5)
    k = np.array([1, 2, 3, 2, 1], float); k /= k.sum()
    rho_i = np.convolve(np.r_[rho_i[-2:], rho_i, rho_i[:2]], k, mode='valid')
    WELD.update(A=A0, B=B0, ca=ca0, cn=cn0, w=float(Pw[:, 2].mean()), rho=rho_i)
    nrow = P['n_rows']
    w_rows = np.linspace(P['w_ring1'], P['w_knuckle'], nrow)
    lob = lobed_ring(P['w_knuckle'])
    # ---- palm rings 1..n : start FOLLOWING the actual (jagged) weld ring polygon, relax into the smooth palm shape
    ring = {}
    tt = np.r_[t_c - 1.0, t_c, t_c + 1.0]
    Pper = np.tile(Pw, (3, 1))
    poly = lambda tq: np.stack([np.interp(tq, tt, Pper[:, k]) for k in range(3)], 1)
    tq = np.arange(40) / 40.0
    P0 = poly(tq)                                       # (40,3) ring-0 polygon resampled at the palm-ring parameters
    w_weld = float(Pw[:, 2].mean())
    for r in range(1, nrow + 1):
        w = w_rows[r - 1]
        E = ellipse_ring(w)
        f = smooth01((w - 0.015) / (P['w_knuckle'] - 0.015)) ** 1.2
        if r == nrow: f = 1.0
        target = (1 - f) * E + f * lob
        sb = smooth01((w - w_weld) / WELD['span'])
        xy = (1 - sb) * P0[:, :2] + sb * target
        wz = (1 - sb) * (P0[:, 2] + (w - w_weld)) + sb * w
        ids = [B.add((xy[i, 0], xy[i, 1], wz[i])) for i in range(40)]
        ring[r] = ids
    # ---- thumb hole: drop palmar-front block (cols i=36..39, rows 2..4)
    c0, c1 = P['hole_cols']
    hr0 = int(np.argmin(np.abs(w_rows - (P['thumb_pts'][0][2] - 0.0115)))) + 1      # palm row whose w is ~1.2 cm proximal of the thumb root axis point
    hr0 = max(2, min(hr0, nrow - 3)); hr1 = hr0 + 2
    hole_faces = set()
    for r in range(hr0, hr1):
        for i in range(c0, c1):
            hole_faces.add((r, i))
    # ---- palm faces
    for r in range(1, nrow):
        for i in range(40):
            if (r, i) in hole_faces:
                continue
            i2 = (i + 1) % 40
            B.face(ring[r][i], ring[r][i2], ring[r + 1][i2], ring[r + 1][i])
    # ---- weld bridging ring0 (ordered, N_c verts) -> ring1 (40)
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
    # ---- fingers (slit model)
    ac, S = finger_centers()
    kn = ring[nrow]
    Dr = lambda j: kn[j]                      # j=0..20
    Pr = lambda j: kn[(40 - j) % 40]          # j=0..20 (0->S_L i=0 , 20 -> S_R i=20)
    fin_rows = {}
    for k in range(4):
        M = P['f_rows'][k]
        Lk = P['f_tip'][k] - P['w_knuckle']
        Msh = M - 3                                                # shaft rings ; + 3 cap rings ; + centre
        sv = [P['s_cap'] * m / Msh for m in range(1, Msh + 1)]
        capang = np.radians([24.0, 48.0, 71.0])
        sv += [P['s_cap'] + (1 - P['s_cap']) * np.sin(c_) for c_ in capang]
        capr = [1.0] * Msh + [np.cos(c_) for c_ in capang]
        svals = np.array(sv)
        rows = []
        for m, s in enumerate(svals, start=1):
            taper = 1 - P['taper'] * min(s, P['s_cap'])
            rho = taper * capr[m - 1]
            w = P['w_knuckle'] + s * Lk
            nf = P['n_f0'] + P['curl'] * s * s
            ra, rn = P['r_a'] * rho, P['r_n'] * rho
            ph = np.radians(-90 + 36 * np.arange(1, 5))
            ack = ac[k] + np.tan(np.radians(P['splay_deg'][k])) * (w - P['w_knuckle'])      # fingers fan open (real gaps)
            WL = B.add((ack + ra, nf, w)); WR = B.add((ack - ra, nf, w))
            Dq = [B.add((ack - ra * np.sin(p_), nf - rn * np.cos(p_), w)) for p_ in ph]
            Pq = [B.add((ack - ra * np.sin(p_), nf + rn * np.cos(p_), w)) for p_ in ph]
            rows.append([WL] + Dq + [WR] + Pq[::-1])           # 10-ring order
        wtip = P['w_knuckle'] + Lk
        C = B.add((ac[k] + np.tan(np.radians(P['splay_deg'][k])) * (wtip - P['w_knuckle']), P['n_f0'] + P['curl'], wtip))
        fin_rows[k] = (rows, C)
        # knuckle row -> first finger ring
        r1_ = rows[0]
        WL1, D1, WR1, P1 = r1_[0], r1_[1:5], r1_[5], r1_[6:10][::-1]   # P1 index q=1..4
        top = [WL1] + list(D1) + [WR1]
        bot = [WL1] + list(P1) + [WR1]
        for q in range(5):
            B.face(Dr(5 * k + q), Dr(5 * k + q + 1), top[q + 1], top[q])
            B.face(Pr(5 * k + q), Pr(5 * k + q + 1), bot[q + 1], bot[q])
        # tube rows
        for m in range(len(rows) - 1):
            for i in range(10):
                i2 = (i + 1) % 10
                B.face(rows[m][i], rows[m][i2], rows[m + 1][i2], rows[m + 1][i])
        # cap fan
        last = rows[-1]
        for i in range(5):
            B.face(last[2 * i], last[2 * i + 1], last[(2 * i + 2) % 10], C)
    # crotch quads
    for k in range(3):
        WRk = fin_rows[k][0][0][5]
        WLk1 = fin_rows[k + 1][0][0][0]
        B.face(Dr(5 * k + 5), WRk, Pr(5 * k + 5), WLk1)
    # ---- thumb
    rr = ring
    loop = [rr[hr0][36], rr[hr0][37], rr[hr0][38], rr[hr0][39], rr[hr0 + 1][39], rr[hr1][39], rr[hr1][38], rr[hr1][37], rr[hr1][36], rr[hr0 + 1][36]]
    # positions of the loop vertices (local)
    posl = lambda vid: B.pos[vid - N]
    Lp = np.array([posl(v) for v in loop])
    pts = np.array(P['thumb_pts'], float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); cum = np.r_[0, np.cumsum(seg)]; tot = cum[-1]
    def axis_at(u):
        d = u * tot
        k = min(np.searchsorted(cum, d, side='right') - 1, len(seg) - 1)
        f = (d - cum[k]) / seg[k]
        return pts[k] * (1 - f) + pts[k + 1] * f, (pts[k + 1] - pts[k]) / seg[k]
    def radius_at(u):
        tr = P['thumb_r']
        xs = np.linspace(0, 1, len(tr))
        return np.interp(u, xs, tr)
    u1 = P['thumb_first'] / tot
    c1, t1v = axis_at(u1)
    ref = np.array([1.0, 0.0, 0.0])
    def frame(tv):
        uu = ref - ref.dot(tv) * tv; uu /= np.linalg.norm(uu); vv = np.cross(tv, uu); return uu, vv
    uu, vv = frame(t1v)
    psi = np.arctan2((Lp - c1) @ vv, (Lp - c1) @ uu)
    # ensure monotonic cyclic order: unwrap
    thumb_rows = []
    nsh = P['thumb_rows'] - 3                                   # shaft rings ; + 3 cap rings ; + tip vertex
    u0 = P['thumb_first'] / tot
    u_cap = P['thumb_cap']
    us = [u0 + (u_cap - u0) * (m / max(nsh - 1, 1)) ** 0.95 for m in range(nsh)]
    capang = np.radians([24.0, 48.0, 71.0])
    us += [u_cap + (1 - u_cap) * np.sin(c_) for c_ in capang]
    capr = [1.0] * nsh + [np.cos(c_) for c_ in capang]
    for m, u in enumerate(us):
        c, tv = axis_at(min(u, 0.999)); uu, vv = frame(tv)
        rad = radius_at(min(u, u_cap)) * capr[m]
        ring_ids = []
        for k in range(10):
            p_ = psi[k]
            pos = c + rad * (np.cos(p_) * uu) + rad * 0.92 * (np.sin(p_) * vv)
            ring_ids.append(B.add(pos))
        thumb_rows.append(ring_ids)
    for k in range(10):
        k2 = (k + 1) % 10
        B.face(loop[k], loop[k2], thumb_rows[0][k2], thumb_rows[0][k])
    for m in range(len(thumb_rows) - 1):
        for k in range(10):
            k2 = (k + 1) % 10
            B.face(thumb_rows[m][k], thumb_rows[m][k2], thumb_rows[m + 1][k2], thumb_rows[m + 1][k])
    Ct = B.add(axis_at(1.0)[0])
    last = thumb_rows[-1]
    for i in range(5):
        B.face(last[2 * i], last[2 * i + 1], last[(2 * i + 2) % 10], Ct)
    return dict(builder=B, cut=cut, ring_o=ring_o, loop=loop)
