"""Micro1f hand generator: same topology as the Micro1e hand (hand_build.py), new positions only.

Adds: finger curl with rings that follow the bent axis, dorsal knuckle pads (MCP / PIP / DIP), palmar fingertip pads,
stronger taper, thenar eminence on the palm, thumb opposition (tip rotated toward the palm), fatter thumb root.
Topology invariants kept: n_rows / f_rows / thumb_rows / hole rows / vertex order == hand_build.py, so the face list of the
assembled body is identical to the Micro1e lock and the edit is a pure coordinate change on the current topology.
"""
import sys
from pathlib import Path
import numpy as np
E1 = Path(__file__).resolve().parents[1] / 'male-micro1e'
if str(E1) not in sys.path:
    sys.path.insert(0, str(E1))
import hand_sdf as H
import hand_topo as T
import hand_build as HB0
from hand_build import smooth01, Builder, finger_centers as _fc

P = dict(HB0.P)
P.update(
    # ---- Micro1f additions (all default to the Micro1e look when zero)
    curl2=0.0,                      # extra cubic curl of the finger axis toward the palm (+n)
    taper2=0.0,                     # extra taper
    pad_mcp=0.0, pad_pip=0.0, pad_dip=0.0,     # dorsal knuckle pad amplitudes (fraction of rn)
    pad_sig=(0.12, 0.09, 0.08), pad_s=(0.0, 0.42, 0.72),
    tip_bulb=0.0,                   # palmar fingertip pad (fraction of rn) at s≈0.80
    ridge=0.0,                      # palm dorsal knuckle ridge (m) at the finger centres, fades in over ridge_w
    ridge_w=(0.025, 0.060),
    thenar=0.0,                     # thenar eminence radial bulge (m)
    thenar_w=(-0.015, 0.020, 0.052), thenar_ang=-7 * np.pi / 4, thenar_sig=0.60,
    hypo=0.0,                       # hypothenar (pinky-side palmar) bulge (m)
    palm_thick=0.0,                 # extra palm half-thickness near the knuckles (m)
    hinge_pip=0.0, hinge_dip=0.0,   # joint bends (m of +n per unit s past the joint)
)


def gauss(s, c, sig):
    return np.exp(-((s - c) / sig) ** 2)


def A_of(w):  return HB0.A_of(w)
def B_of(w):  return HB0.B_of(w) + P['palm_thick'] * smooth01((w - 0.0) / 0.06)
def NC_of(w): return HB0.NC_of(w)


def ellipse_ring(w, nverts=40):
    W = HB0.WELD
    A, B, nc = A_of(w), B_of(w), NC_of(w)
    ca = 0.0
    if W['A'] is not None:
        sb = smooth01((w - W['w']) / W['span'])
        A = W['A'] + (A - W['A']) * sb
        B = W['B'] + (B - W['B']) * sb
        nc = W['cn'] + (nc - W['cn']) * sb
        ca = W['ca'] * (1 - sb)
    t = -2 * np.pi * np.arange(nverts) / nverts
    c, s = np.cos(t), np.sin(t)
    e = 2.0 / P['p_exp']
    a = A * np.sign(c) * np.abs(c) ** e
    n = nc + B * np.sign(s) * np.abs(s) ** e
    # thenar / hypothenar bulges: radial push in the palmar quadrants, profile along w
    w0, w1, w2 = P['thenar_w']
    prof = smooth01((w - w0) / (w1 - w0)) * (1 - smooth01((w - w1) / (w2 - w1)))
    dth = np.angle(np.exp(1j * (t - P['thenar_ang'])))
    g = np.exp(-(dth / P['thenar_sig']) ** 2) * prof
    dth2 = np.angle(np.exp(1j * (t - (-5 * np.pi / 4))))          # pinky side palmar (cos<0, sin>0)
    g2 = np.exp(-(dth2 / 0.55) ** 2) * prof
    r = np.hypot(a, n - nc)
    ux, un = a / np.maximum(r, 1e-9), (n - nc) / np.maximum(r, 1e-9)
    a = a + ux * (P['thenar'] * g + P['hypo'] * g2)
    n = n + un * (P['thenar'] * g + P['hypo'] * g2)
    return np.stack([a + ca, n], 1)


def finger_centers():
    S = 2 * P['r_a'] + P['gap']
    return [(1.5 - k) * S for k in range(4)], S


def lobed_ring(w):
    HB0.P.update({k: P[k] for k in ('r_a', 'gap', 'r_n', 'n_f0', 'h_valley')})
    return HB0.lobed_ring(w)


def build_hand(co, F, side, w0=-0.03):
    HB0.P.update({k: v for k, v in P.items() if k in HB0.P})
    cut = T.extract_cut(co, F, side, w0)
    L = cut['L']
    ring_o, t_c, cen, (Ar, Br) = T.order_ring(cut['ring'], L)
    N = len(co)
    B = Builder(N)
    Pw = L[ring_o]
    ca0 = 0.5 * (np.percentile(Pw[:, 0], 97) + np.percentile(Pw[:, 0], 3))
    cn0 = 0.5 * (np.percentile(Pw[:, 1], 97) + np.percentile(Pw[:, 1], 3))
    A0 = 0.5 * (np.percentile(Pw[:, 0], 97) - np.percentile(Pw[:, 0], 3))
    B0 = 0.5 * (np.percentile(Pw[:, 1], 97) - np.percentile(Pw[:, 1], 3))
    HB0.WELD.update(A=A0, B=B0, ca=ca0, cn=cn0, w=float(Pw[:, 2].mean()), rho=None)
    nrow = P['n_rows']
    w_rows = np.linspace(P['w_ring1'], P['w_knuckle'], nrow)
    lob = lobed_ring(P['w_knuckle'])
    ac, S = finger_centers()
    ring = {}
    tt = np.r_[t_c - 1.0, t_c, t_c + 1.0]
    Pper = np.tile(Pw, (3, 1))
    poly = lambda tq: np.stack([np.interp(tq, tt, Pper[:, k]) for k in range(3)], 1)
    tq = np.arange(40) / 40.0
    P0 = poly(tq)
    w_weld = float(Pw[:, 2].mean())
    for r in range(1, nrow + 1):
        w = w_rows[r - 1]
        E = ellipse_ring(w)
        f = smooth01((w - 0.015) / (P['w_knuckle'] - 0.015)) ** 1.2
        if r == nrow:
            f = 1.0
        target = (1 - f) * E + f * lob
        sb = smooth01((w - w_weld) / HB0.WELD['span'])
        xy = (1 - sb) * P0[:, :2] + sb * target
        wz = (1 - sb) * (P0[:, 2] + (w - w_weld)) + sb * w
        # dorsal knuckle ridge over the metacarpal heads
        if P['ridge'] > 0:
            rw = smooth01((w - P['ridge_w'][0]) / (P['ridge_w'][1] - P['ridge_w'][0]))
            for i in range(1, 20):                       # dorsal verts
                lobe = max(np.exp(-((xy[i, 0] - a_c) / (0.42 * S)) ** 2) for a_c in ac)
                xy[i, 1] -= P['ridge'] * rw * lobe
        ids = [B.add((xy[i, 0], xy[i, 1], wz[i])) for i in range(40)]
        ring[r] = ids
    c0, c1 = P['hole_cols']
    hr0 = int(np.argmin(np.abs(w_rows - (P['thumb_pts'][0][2] - 0.0115)))) + 1
    hr0 = max(2, min(hr0, nrow - 3)); hr1 = hr0 + 2
    hole_faces = set((r, i) for r in range(hr0, hr1) for i in range(c0, c1))
    for r in range(1, nrow):
        for i in range(40):
            if (r, i) in hole_faces:
                continue
            i2 = (i + 1) % 40
            B.face(ring[r][i], ring[r][i2], ring[r + 1][i2], ring[r + 1][i])
    # weld bridging (identical to hand_build)
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
    # ---- fingers: bent axis, rings follow the tangent, knuckle pads, tip pad
    kn = ring[nrow]
    Dr = lambda j: kn[j]
    Pr = lambda j: kn[(40 - j) % 40]
    fin_rows = {}
    ps, pg = P['pad_s'], P['pad_sig']

    def srelu(x, wd):
        return wd * np.log1p(np.exp(x / wd))

    def axis(k, s, Lk):
        w = P['w_knuckle'] + s * Lk
        n = P['n_f0'] + P['curl'] * s * s + P['curl2'] * s ** 3
        n += P['hinge_pip'] * srelu(s - ps[1], 0.05) + P['hinge_dip'] * srelu(s - ps[2], 0.05)
        return n, w

    for k in range(4):
        M = P['f_rows'][k]
        Lk = P['f_tip'][k] - P['w_knuckle']
        Msh = M - 3
        sv = [P['s_cap'] * m / Msh for m in range(1, Msh + 1)]
        capang = np.radians([24.0, 48.0, 71.0])
        sv += [P['s_cap'] + (1 - P['s_cap']) * np.sin(c_) for c_ in capang]
        capr = [1.0] * Msh + [np.cos(c_) for c_ in capang]
        rows = []
        tan_s = np.tan(np.radians(P['splay_deg'][k]))
        for m, s in enumerate(sv, start=1):
            sc_ = min(s, P['s_cap'])
            taper = 1 - (P['taper'] + P['taper2']) * sc_
            rho = taper * capr[m - 1]
            n0, w = axis(k, s, Lk)
            n1, w1 = axis(k, s + 1e-3, Lk)
            tv = np.array([n1 - n0, w1 - w]); tv /= np.linalg.norm(tv)       # (dn, dw)
            u = np.array([tv[1], -tv[0]])                                      # unit vector toward +n, ⟂ tangent
            ra, rn = P['r_a'] * rho, P['r_n'] * rho
            dors = 1 + (P['pad_mcp'] * gauss(sc_, ps[0], pg[0]) + P['pad_pip'] * gauss(sc_, ps[1], pg[1]) + P['pad_dip'] * gauss(sc_, ps[2], pg[2])) * capr[m - 1]
            palm = 1 + P['tip_bulb'] * gauss(sc_, 0.80, 0.14) * capr[m - 1]
            ph = np.radians(-90 + 36 * np.arange(1, 5))
            ack = ac[k] + tan_s * (w - P['w_knuckle'])
            def pt(a_, nn):
                return (a_, n0 + nn * u[0], w + nn * u[1])
            WL = B.add(pt(ack + ra, 0.0)); WR = B.add(pt(ack - ra, 0.0))
            Dq = [B.add(pt(ack - ra * np.sin(p_), -rn * dors * np.cos(p_))) for p_ in ph]
            Pq = [B.add(pt(ack - ra * np.sin(p_), +rn * palm * np.cos(p_))) for p_ in ph]
            rows.append([WL] + Dq + [WR] + Pq[::-1])
        n0, wtip = axis(k, 1.0, Lk)
        C = B.add((ac[k] + tan_s * (wtip - P['w_knuckle']), n0, wtip))
        fin_rows[k] = (rows, C)
        r1_ = rows[0]
        WL1, D1, WR1, P1 = r1_[0], r1_[1:5], r1_[5], r1_[6:10][::-1]
        top = [WL1] + list(D1) + [WR1]
        bot = [WL1] + list(P1) + [WR1]
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
        WRk = fin_rows[k][0][0][5]
        WLk1 = fin_rows[k + 1][0][0][0]
        B.face(Dr(5 * k + 5), WRk, Pr(5 * k + 5), WLk1)
    # ---- thumb (identical construction, parameters may differ)
    rr = ring
    loop = [rr[hr0][36], rr[hr0][37], rr[hr0][38], rr[hr0][39], rr[hr0 + 1][39], rr[hr1][39], rr[hr1][38], rr[hr1][37], rr[hr1][36], rr[hr0 + 1][36]]
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
        return np.interp(u, np.linspace(0, 1, len(tr)), tr)

    u1 = P['thumb_first'] / tot
    c1, t1v = axis_at(u1)
    ref = np.array([1.0, 0.0, 0.0])

    def frame(tv):
        uu = ref - ref.dot(tv) * tv; uu /= np.linalg.norm(uu); vv = np.cross(tv, uu); return uu, vv

    uu, vv = frame(t1v)
    psi = np.arctan2((Lp - c1) @ vv, (Lp - c1) @ uu)
    thumb_rows = []
    nsh = P['thumb_rows'] - 3
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
            pos = c + rad * (np.cos(p_) * uu) + rad * P.get('thumb_flat', 0.92) * (np.sin(p_) * vv)
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
