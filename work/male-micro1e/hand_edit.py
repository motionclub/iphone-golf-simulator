"""FINGERS: coordinate-only hand rebuild on the existing Body_M topology.

Method (no topology change):
 1. local hand frame (a', n, w); each hand vertex gets a digit label (palm / thumb / 4 fingers) from its position.
 2. finger-zone vertices get a LOFT target: the single mitten ring is split into 4 bands along a'; each band's dorsal
    and palmar vertices are mapped around its own finger tube (angle linear in band coordinate v).
 3. homotopy: vertices are pulled gradually to their loft target, projected onto their OWN digit's implicit surface
    (so there are no nearest-surface ties between fingers) and tangentially relaxed.
"""
import numpy as np
import sculpt_core as sc
import hand_sdf as H
from sculpt_core import BASE, N, sm

PRM = dict(
    band0=0.052,                # w where finger bands start
    w_s0=0.065, w_tip_blob=0.165,
    phi_in=75.0, phi_out=90.0,   # degrees
    thumb_a=0.030, thumb_n=0.0, thumb_w=(-0.012, 0.062),
    iters=220, ramp=110, pull=0.12, beta_end=0.04, tang=0.55,
    fade=(-0.035, 0.020),
    # finger cross-section (a-radius, n-radius) at base / tip, curl
    r_a=(0.0120, 0.0100), r_n=(0.0140, 0.0118),
)


def ring_A(w):
    return np.interp(w, [0.05, 0.065, 0.085, 0.10, 0.145, 0.155, 0.165, 0.175],
                     [0.0494, 0.0415, 0.0328, 0.0297, 0.0300, 0.0249, 0.0152, 0.0060])


def ring_nc(w):
    return np.interp(w, [0.0, 0.07, 0.105, 0.15, 0.17], [-0.0126, -0.0140, -0.0175, -0.0095, -0.0095])


def make_labels(L, region, side):
    lab = np.full(N, -1, np.int64)
    a, n, w = L[:, 0], L[:, 1], L[:, 2]
    lab[region] = 0
    # thumb: front-lateral palmar half of the palm bulb
    th = region & (a > PRM['thumb_a']) & (n > PRM['thumb_n']) & (w > PRM['thumb_w'][0]) & (w < PRM['thumb_w'][1])
    lab[th] = 5
    # finger bands
    fz = region & (w >= PRM['band0']) & ~th
    u = np.clip(a / ring_A(w), -0.9999, 0.9999)
    band = np.floor((u + 1.0) * 2.0).astype(int)            # 0..3 : u -1..1  -> pinky..index
    k = 3 - band                                              # 0=index .. 3=pinky
    lab[fz] = 1 + k[fz]
    return lab, u


def loft_targets(L, lab, u):
    """finger loft positions (local) for labelled finger vertices"""
    out = L.copy()
    a, n, w = L[:, 0], L[:, 1], L[:, 2]
    PR = H.PARAMS
    for kf in range(4):
        m = lab == (1 + kf)
        if not m.any():
            continue
        band_c = 0.75 - 0.5 * kf                              # u centre of this band: index .75, middle .25, ring -.25, pinky -.75
        v = (u[m] - band_c) / 0.25
        sign_n = np.where(n[m] > ring_nc(w[m]), +1.0, -1.0)    # +1 palmar, -1 dorsal
        ph_in, ph_out = np.radians(PRM['phi_in']), np.radians(PRM['phi_out'])
        phi = np.where(v < 0, ph_in * v, ph_in * v)
        if kf == 0:
            phi = np.where(v > 0, ph_out * v, ph_in * v)
        if kf == 3:
            phi = np.where(v < 0, ph_out * v, ph_in * v)
        s = np.clip((w[m] - PRM['w_s0']) / (PRM['w_tip_blob'] - PRM['w_s0']), -0.4, 1.02)
        sc_ = np.clip(s, 0, 1)
        wb, wt = PR['f_base_w'][kf], PR['f_len_tip_w'][kf]
        wp = wb + s * (wt - wb)
        ra = PRM['r_a'][0] + (PRM['r_a'][1] - PRM['r_a'][0]) * sc_
        rn = PRM['r_n'][0] + (PRM['r_n'][1] - PRM['r_n'][0]) * sc_
        rho = np.where(w[m] > 0.145, np.clip(ring_A(w[m]) / 0.0297, 0.0, 1.0), 1.0)
        nf = PR['f_n0'] + PR['f_curl'] * sc_ ** 2
        # finger axis a' (fixed) ; sin/cos of angle around the tube
        out[m, 0] = PR['f_x'][kf] + rho * ra * np.sin(phi)
        out[m, 1] = nf + sign_n * rho * rn * np.cos(phi)
        out[m, 2] = wp
    return out


def label_sdf(Lp, lab):
    """per-vertex digit SDF evaluated at local points Lp (M,3) with labels lab (M,)"""
    PR = H.PARAMS
    f = np.empty(len(Lp))
    # palm-only
    m0 = lab == 0
    if m0.any():
        f[m0] = palm_sdf(Lp[m0])
    for kf in range(4):
        m = lab == (1 + kf)
        if m.any():
            f[m] = H.smin(palm_sdf(Lp[m]), finger_sdf(Lp[m], kf), PR['k_web'])
    m5 = lab == 5
    if m5.any():
        f[m5] = H.smin(palm_sdf(Lp[m5]), H.chain(Lp[m5], PR['thumb_pts'], PR['thumb_r']), PR['k_thumb'])
    return f


def palm_sdf(L):
    PR = H.PARAMS
    t = np.clip((L[:, 2] - PR['palm_taper'][0]) / (PR['palm_taper'][1] - PR['palm_taper'][0]), 0, 1); t = t * t * (3 - 2 * t)
    s_a = PR['palm_taper'][2] + (1.0 - PR['palm_taper'][2]) * t
    Lp = L.copy(); Lp[:, 0] = L[:, 0] / s_a
    palm = H.sd_rbox(Lp, np.array(PR['palm_c']), np.array(PR['palm_b']), PR['palm_r']) * 0.9
    knuck = H.sd_rbox(L, np.array(PR['knuck_c']), np.array(PR['knuck_b']), PR['knuck_r'])
    return H.smin(palm, knuck, 0.012)


def finger_sdf(L, kf):
    """elliptical finger tube: scale a' offset so the cross-section becomes circular of radius r_n"""
    PR = H.PARAMS
    pts = H.finger_pts(kf, PR)
    ra0, ra1 = PRM['r_a']; rn0, rn1 = PRM['r_n']
    x0 = PR['f_x'][kf]
    k0 = rn0 / ra0
    Ls = L.copy(); Ls[:, 0] = x0 + (L[:, 0] - x0) * k0
    f = H.chain(Ls, pts, [rn0, 0.5 * (rn0 + rn1), rn1])
    return f / (0.5 * (1 + k0))


def run_side(base, side, iters=None, verbose=False):
    L0 = H.to_local(base, side)
    gx = side * base[:, 0]
    region = (gx > 0.30) & (base[:, 2] < 1.10) & (L0[:, 2] > -0.05)
    lab, u = make_labels(L0, region, side)
    loft = loft_targets(L0, lab, u)
    idx = np.where(region)[0]
    wt = sm(*PRM['fade'], L0[:, 2])
    lam = sm(PRM['band0'], 0.090, L0[:, 2])                  # loft blend over the knuckle/web zone
    isf = (lab >= 1) & (lab <= 4)
    p = L0.copy()
    iters = iters or PRM['iters']
    nb = lambda q: sc.neighbor_mean(q)
    wv = wt.copy()
    for it in range(iters):
        t = min(1.0, it / PRM['ramp'])
        beta = (1 - t) * 0.25 + t * PRM['beta_end']
        # homotopy target for finger vertices
        tgt = L0 + (t * lam)[:, None] * (loft - L0)
        mv = isf & region
        p[mv] = p[mv] + (wv[mv] * beta)[:, None] * (tgt[mv] - p[mv])
        # project onto own digit surface
        pi = p[idx]; li = lab[idx]
        hh = 1e-4
        f = label_sdf(pi, li)
        g = np.stack([label_sdf(pi + [hh, 0, 0], li) - label_sdf(pi - [hh, 0, 0], li),
                      label_sdf(pi + [0, hh, 0], li) - label_sdf(pi - [0, hh, 0], li),
                      label_sdf(pi + [0, 0, hh], li) - label_sdf(pi - [0, 0, hh], li)], 1) / (2 * hh)
        gg = np.maximum((g * g).sum(1), 1e-12)
        step = (f / gg)[:, None] * g
        pr = pi - step
        p[idx] = pi + (wv[idx] * PRM['pull'] * 2.0)[:, None] * (pr - pi) * np.clip(t * 2.0 + 0.2, 0, 1.0)
        # tangential smoothing
        L = nb(p) - p
        gn = g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)
        Lt = L[idx] - np.einsum('ij,ij->i', L[idx], gn)[:, None] * gn
        p[idx] += (wv[idx] * PRM['tang'])[:, None] * Lt
    # final snap
    pi = p[idx]; li = lab[idx]
    for _ in range(3):
        hh = 1e-4
        f = label_sdf(pi, li)
        g = np.stack([label_sdf(pi + [hh, 0, 0], li) - label_sdf(pi - [hh, 0, 0], li),
                      label_sdf(pi + [0, hh, 0], li) - label_sdf(pi - [0, hh, 0], li),
                      label_sdf(pi + [0, 0, hh], li) - label_sdf(pi - [0, 0, hh], li)], 1) / (2 * hh)
        gg = np.maximum((g * g).sum(1), 1e-12)
        pi = pi - ((f / gg)[:, None] * g) * wv[idx][:, None]
    p[idx] = pi
    out = base.copy()
    G = H.to_global(p[idx], side)
    out[idx] = base[idx] + wv[idx][:, None] * (G - base[idx])
    info = dict(side=side, n_region=int(region.sum()), labels={int(k): int((lab == k).sum()) for k in range(-1, 6)})
    return out, info


def build(overrides=None, sides=(+1, -1)):
    if overrides:
        PRM.update(overrides)
    co = BASE.copy()
    infos = []
    for s in sides:
        co, inf = run_side(co, s)
        infos.append(inf)
    return co, infos
