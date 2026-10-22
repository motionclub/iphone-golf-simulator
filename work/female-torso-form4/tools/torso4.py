"""FEMALE TORSO FORM4 core (numpy only; derived from FORM3 torso3.py).  FORM4 adds: bell-profile bust domes on an UN-flattened ring, a sub-pixel plate front contour for the bust band + upper chest.
(original FORM3 header follows)
FEMALE TORSO FORM3 core (numpy only).  Positions-only deformation of the chat-7 torso zone, built from the ORIGINAL start (SHA 200dc3b9).

Lessons from FORM2 (rejected by eye): ellipsoid caps / lobe unions left flat fronts, hard shelves, a rectangular butt slab and a square cleft pit.
FORM3 design (everything is a smooth C-infinity-ish field, no footprints with walls):
  base      : chat-7 ring depth remap (front wall at the sternum line, back at the ring centre line)    [depth wins kept]
  bust      : two wide, low, soft mounds (Gaussian-type, asymmetric radii: steep lower flank = underbust crescent, long gentle upper slope)
  glutes    : the pelvis ring itself carries the round lobes; a soft V cleft is carved along the midline, the fold band comes from the
              lobe/thigh transition, the upper shelf from the plate back table.  No lobe slab, no lateral window, no pit.
  weights   : geodesic distance from the pinned border (neck / arm junction / leg tops) -> border vertices never move.
Everything is evaluated on a Taubin-denoised copy (the 13.5 mm surface-nets lattice jitters +-0.5 mm).
"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
import numpy as np
import torso2 as t2
from torso2 import (PS, CO0, T, BORDER, N, EA, EB, DEG, ZG, TT, TRI, ED, WD, D_LEG, D_ARM, D_TOP, CLS, F0s, B0s,
                    sstep, sstep5, gauss1d, gsmooth, border_weight, plate_front, plate_back, plate_back_soft,
                    section_extents, fillnan, bell, smax, smin)

XV, YV, ZV = PS[:, 0], PS[:, 1], PS[:, 2]

_FF = np.load(str(WD / 'data/plate_front_fine4.npy'))      # sub-pixel plate side contour (z, y_front), calibrated to the old table on z .95-1.15


def front_table(z, P):
    """plate front contour used as the wall envelope.  use_fine: old table below fine_z0, sub-pixel contour above fine_z1, smoothstep between."""
    old = plate_front(z)
    if not P.get('use_fine', 0):
        return old
    fine = np.interp(z, _FF[0], _FF[1])
    w = sstep((z - P['fine_z0']) / max(P['fine_z1'] - P['fine_z0'], 1e-6))
    return old + w * (fine - old)


def ssign(t, w=0.01):
    """smooth sign in (-1,1)"""
    return np.tanh(t / w)


def asym(t, lo, hi, w=0.012):
    """piecewise radius: `lo` for t<0, `hi` for t>0, C-infinity blend over +-w"""
    s = 0.5 * (1 + ssign(t, w))
    return lo + (hi - lo) * s


def gexp(r2, p=1.0):
    """generalised Gaussian exp(-(r2)^p): p=1 Gaussian, p>1 flatter top / crisper edge"""
    return np.exp(-np.power(np.maximum(r2, 0.0), p))


# ----------------------------------------------------------------------------------------------- parameters
DEFAULT3 = dict(
    # ---- wall tables
    b_rec=0.019, b_rec_dz=0.0, b_rec_wd=0.100, b_rec_wu=0.075, b_zc=1.222,          # sternum-line recession behind the plate envelope (valley between the mounds)
    mo_R=0.0, mo_xc=0.075, mo_zc=1.21, mo_sx=0.065, mo_szd=0.05, mo_szu=0.05, mo_q=1.0,
    fl_k=0.0, fl_za=1.14, fl_zb=1.30, fl_zw=0.03, fl_x1=0.085, fl_x2=0.118,
    uf_k=0.0, uf_z0=1.235, uf_z1=1.275, uf_z2=1.300, uf_zw=0.03, uf_x1=0.085, uf_x2=0.118,
    st_R3=0.0, st_zc=1.205, st_wd=0.045, st_wu=0.040, st_sx=0.030, st_q=2.0,
    pf_A=0.010, pf_x0=0.025, pf_x1=0.075, pf_x2=0.100, pf_x3=0.128, pf_z0=1.13, pf_z1=1.31, pf_zw=0.04,   # pec fill: flattens the ring curvature at |x| 0.05..0.11
    bk_z0=0.925, bk_z1=0.965,
    ramp_k=0.0, ramp_z0=1.24, ramp_z1=1.345, ramp_m0=None, ramp_mode='hermite', sp_za=1.22, sp_lam=3e-7, sp_w1=1.31, sp_w2=1.345, sp_wlo=0.08,                        # smooth Hermite ramp of the front wall from the mound's upper edge to the (original) neck base                                                       # back: original ring below z0, plate table above z1
    # ---- bust mounds (|x| mirrored): round soft discs, steeper lower flank (= underbust crescent)
    bm_xc=0.078, bm_zc=1.222, bm_sxm=0.032, bm_sxl=0.028, bm_szd=0.022, bm_szu=0.040, bm_H=0.030, bm_p=1.25, bm_tilt=0.0,
    bp_xc=0.060, bp_zc=1.262, bp_sx=0.060, bp_sz=0.045, bp_H=0.004,                 # broad pec swell (upper highlight)
    # ---- glutes: original ring + cleft funnel + lower-lobe fullness (fold crescent)
    cl_c=0.024, cl_w0=0.016, cl_wup=0.9, cl_z0=0.880, cl_z1=0.975, cl_zlo0=0.812, cl_zlo1=0.840, cl_q=1.6,
    ll_A=0.012, ll_xc=0.090, ll_sxm=0.030, ll_sxl=0.040, ll_zc=0.832, ll_szd=0.016, ll_szu=0.032, ll_zr=0.15,
    gl_H=0.0, gl_xc=0.070, gl_zc=0.870, gl_sxm=0.045, gl_sxl=0.050, gl_szd=0.035, gl_szu=0.050,
    # circular-lobe glutes (mode 'circ'): two lobes = circles in plan, centre xc(z), radius R(z)=X(z)-xc(z), apex y = plate table
    ub_A=0.0, ub_xc=0.07, ub_sx=0.055, ub_z0=0.806, ub_zr=0.020, ub_z1=0.832, ub_zw=0.030,          # underbutt fold bump (pulls the lower-lobe silhouette toward the plate's long underside slope)
    gm_R=0.0, gm_xc=0.072, gm_zc=0.868, gm_sxm=0.060, gm_sxl=0.040, gm_szd=0.05, gm_szu=0.03,
    gm='ring',                                   # 'ring' (cleft/lowlobe on the original ring) | 'circ'
    gc_x0=0.085, gc_x1=0.062, gc_z0=0.805, gc_z1=0.865, gc_top0=0.900, gc_top1=0.965,    # xc: x0 at z<=z0 -> x1 at z>=z1, merging to 0 between top0 and top1
    gc_k=0.010, gc_diff=1, gc_Rs=1.0, gc_lat0=0.040, gc_lat1=0.010, gc_wg0=0.915, gc_wg1=0.965, gc_dy=0.0,
    # ---- weights
    leg_r=0.07, arm_r=0.05, top_r=0.05, leg_f=0.020, arm_f=0.030, top_f=0.040, ksm=8, kfin=3, top_z1=1.345, top_zw=0.075,
    lf_on=1.0, lf_x0=0.10, lf_x1=0.15,
    use_fine=0, fine_z0=1.12, fine_z1=1.16, ramp_zs=1.30,
    cs_k=0, cs_w=0.035, bm_signed=0, bk_amp=0.0, bk_zc=0.872, bk_sz=0.022,
    wl_y=None, wl_z0=1.17, wl_z1=1.29, wl_k=0.004,
    rd_R=0.0, rd_x1=0.10, rd_za=1.12, rd_zb=1.30, rd_zw=0.04, rd_bell=0, rd_zc=1.20, rd_wd=0.10, rd_wu=0.11,
)


def wall3(P, dFw=None, dBb=None):
    z = ZG
    Fw = np.array([front_table(v, P) for v in z]) + P['b_rec'] * bell(z, P['b_zc'] + P['b_rec_dz'], P['b_rec_wd'], P['b_rec_wu'])
    Bo = np.interp(z, ZG, B0s)
    wbk = sstep((z - P['bk_z0']) / (P['bk_z1'] - P['bk_z0']))
    Bb = Bo + wbk * (np.array([plate_back_soft(v) for v in z]) - Bo)
    if P.get('bk_amp', 0.0):
        # FORM4 glute polish: the sub-pixel plate back contour peaks ~3 mm further back than the old table at z .86-.88
        Bb = Bb + P['bk_amp'] * np.exp(-((z - P['bk_zc']) / P['bk_sz']) ** 2)
    if P.get('wl_y') is not None:
        # FORM4: sternum wall line.  The plate silhouette in the bust band is the DOME apex line; the chest wall behind the domes is a (near-)vertical line.
        # Fw = smooth-max(Fw, wl_y) inside the window wl_z0..wl_z1 (y is negative forward, so max = the less forward of the two)
        win = sstep((z - P['wl_z0']) / 0.02) * (1 - sstep((z - P['wl_z1']) / 0.02))
        Fw = Fw + win * (smax(Fw, P['wl_y'], P.get('wl_k', 0.004)) - Fw)
    k = P.get('ramp_k', 0.0)
    if k > 0 and P.get('ramp_mode', 'hermite') == 'spline':
        # constrained smoothing-spline fit of the front wall above sp_za to the plate table: start = current wall (position+slope),
        # end = original neck ring front (position+slope) at the zone top; weights fade above sp_w1 (the plate neck is thinner than ours)
        ix = lambda zz: int(round((zz - 0.80) / 0.002))
        a, b = ix(P['sp_za']), len(z) - 1
        n = b - a + 1
        F0v = np.interp(z, ZG, F0s)
        Tg = np.array([plate_front(v) for v in z])
        wz = np.clip(1.0 - (z - P['sp_w1']) / max(P['sp_w2'] - P['sp_w1'], 1e-6), P['sp_wlo'], 1.0)
        lam = P['sp_lam']
        # unknowns Y[a+2 .. b-2]; fixed: Y[a-1], Y[a], Y[b-1], Y[b]
        m1 = (F0v[b] - F0v[b - 4]) / (4 * 0.002)
        fixed = {a - 1: Fw[a - 1], a: Fw[a], b: F0v[b], b - 1: F0v[b] - m1 * 0.002}
        idx = np.arange(a - 1, b + 1)
        N_ = len(idx)
        A = np.zeros((N_, N_)); rhs = np.zeros(N_)
        # data term
        for j, i in enumerate(idx):
            A[j, j] += wz[i]; rhs[j] += wz[i] * Tg[i]
        # smoothness term (second difference)
        for j in range(1, N_ - 1):
            v = np.zeros(N_); v[j - 1], v[j], v[j + 1] = 1, -2, 1
            A += lam / (0.002 ** 4) * 1e-8 * np.outer(v, v)
        # Dirichlet rows
        for i, val in fixed.items():
            j = i - (a - 1)
            A[j, :] = 0; A[j, j] = 1; rhs[j] = val
        Y = np.linalg.solve(A, rhs)
        ramp = Fw.copy()
        ramp[a - 1:b + 1] = Y
        Fw = np.where(z >= z[a], Fw + k * (ramp - Fw), Fw)
    elif k > 0 and P.get('ramp_mode', 'hermite') == 'slope':
        # FORM4: from z0 on the front wall eases its slope from the current (plate) slope to a constant slope m_e reached at zs, and lands exactly on the original
        # ring front at ze (the pinned neck ring):  y(z) = y0 + int slope,  slope = m0 + (m_e - m0) * sstep((z - z0) / (zs - z0));  m_e solved by bisection.
        z0, zs, ze = P['ramp_z0'], P['ramp_zs'], P['ramp_z1']
        ix = lambda zz: int(round((zz - 0.80) / 0.002))
        i0, ie = ix(z0), ix(ze)
        y0 = Fw[i0]
        m0 = P['ramp_m0'] if P.get('ramp_m0') is not None else (Fw[i0 + 3] - Fw[i0 - 3]) / (6 * 0.002)
        F0v = np.interp(z, ZG, F0s)
        yend = F0v[ie]
        zz = z[i0:ie + 1]

        def curve(me):
            sl = m0 + (me - m0) * sstep((zz - z0) / (zs - z0))
            return y0 + np.concatenate([[0.0], np.cumsum(0.5 * (sl[1:] + sl[:-1]) * 0.002)])
        lo, hi = -2.0, 3.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if curve(mid)[-1] < yend:
                lo = mid
            else:
                hi = mid
        yc = curve(0.5 * (lo + hi))
        ramp = Fw.copy()
        ramp[i0:ie + 1] = yc
        ramp[ie + 1:] = F0v[ie + 1:]
        Fw = np.where(z >= z[i0], Fw + k * (ramp - Fw), Fw)
    elif k > 0:
        z0, z1 = P['ramp_z0'], P['ramp_z1']
        ix = lambda zz: int(round((zz - 0.80) / 0.002))
        i0, i1 = ix(z0), ix(z1)
        y0 = Fw[i0]
        m0 = P['ramp_m0'] if P.get('ramp_m0') is not None else (Fw[i0 + 4] - Fw[i0 - 4]) / (8 * 0.002)
        F0v = np.interp(z, ZG, F0s)
        y1 = F0v[i1]
        m1 = (F0v[i1 + 5] - F0v[i1 - 5]) / (10 * 0.002)
        D_ = z1 - z0
        t = np.clip((z - z0) / D_, 0, 1)
        h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        ramp = h00 * y0 + h10 * D_ * m0 + h01 * y1 + h11 * D_ * m1
        ramp = np.where(z > z1, F0v, ramp)
        Fw = np.where(z >= z0, Fw + k * (ramp - Fw), Fw)
    if dFw is not None:
        Fw = Fw + dFw
    if dBb is not None:
        Bb = Bb + dBb
    i84 = int(round((0.84 - 0.80) / 0.002))
    Fw = np.where(z < 0.84, np.interp(z, [0.795, 0.84], [-0.0943, Fw[i84]]), Fw)
    return gauss1d(Fw, 0.006), gauss1d(Bb, 0.006)


# ----------------------------------------------------------------------------------------------- features (metres, +ve = outward growth)
def softplus(t, w=0.25):
    return w * np.logaddexp(0.0, t / w)


def bust_coords(x, z, C):
    """normalised elliptical footprint coords of one (|x|-mirrored) component: returns rho^2, v (vertical coord), u (horizontal)"""
    sg = C.get('sgn', None)
    if sg is None:
        dx = np.abs(x) - C['xc']                      # legacy: one component on |x| (kinks at x=0 when the medial tail crosses the centre line)
    else:
        dx = sg * x - C['xc']                         # FORM4: signed right / left dome, summed in bust_amp -> smooth sternal valley
    dz = z - C['zc']
    rot = C.get('rot', 0.0)
    if rot:
        # FORM4: rotate the footprint in PHYSICAL space (positive: the lateral end swings DOWN, the inner end up -> lower contour rises toward the sternum)
        c_, s_ = np.cos(rot), np.sin(rot)
        dx, dz = c_ * dx + s_ * dz, -s_ * dx + c_ * dz
    rz = asym(dz, C['szd'], C['szu'], 0.010)
    v = dz / rz
    tap = 1.0 + C.get('tdn', 0.0) * softplus(-v) - C.get('tup', 0.0) * softplus(v)       # teardrop: widest below the centre
    tap = np.clip(tap, 0.45, 1.8)
    sx = asym(dx, C['sxm'], C['sxl'], 0.014) * tap
    u = dx / sx
    th = C.get('tilt', 0.0)
    if th:
        # tilt the footprint: positive tilt swings the upper part toward lateral (+|x|) (teardrop pointing at the armpit)
        c_, s_ = np.cos(th), np.sin(th)
        u, v = c_ * u - s_ * v, s_ * u + c_ * v
    return u * u + v * v, v, u


def comp_amp(x, z, C):
    r2, v, u = bust_coords(x, z, C)
    if C.get('prof', 'gauss') == 'bell':
        # compact-support bell (1-rho^2)^k, C2 at the rim for k>=3: round dome, steepest flank at rho = 1/sqrt(2k-1)
        rho_ = np.sqrt(np.maximum(r2, 0.0))
        pp_ = C.get('p', 2.0)
        kk_ = C.get('k', 3.0)
        if 'p_lo' in C or 'k_lo' in C:
            # exponents blend smoothly from the lower (v<0) to the upper half: crisp lower edge / long gentle upper slope without a seam
            low = 0.5 * (1 - np.tanh(v / 0.25))
            pp_ = pp_ + (C.get('p_lo', pp_) - pp_) * low
            kk_ = kk_ + (C.get('k_lo', kk_) - kk_) * low
        m = C['H'] * np.clip(1.0 - np.power(rho_, pp_), 0.0, 1.0) ** kk_
    elif C.get('prof', 'gauss') == 'dome':
        pp = C['p']
        if 'p_lo' in C:
            low = 0.5 * (1 - np.tanh(v / 0.25))
            pp = C['p'] + (C['p_lo'] - C['p']) * low
        m = C['H'] * np.clip(1 - r2, 0, 1) ** pp
    else:
        m = C['H'] * gexp(r2, C['p'])
    gd = C.get('gd', 0.0)
    if gd:
        rho = np.sqrt(np.maximum(r2, 1e-12))
        low = 0.5 * (1 - np.tanh(v / 0.25))
        m = m - gd * np.exp(-((rho - C['gr']) / C['gw']) ** 2) * low
    return m


def bust_comps(P):
    """list of mound components; legacy single-mound keys (bm_*) are mapped to one component"""
    if P.get('bm_list'):
        return [dict(c) for c in P['bm_list']]
    return [dict(xc=P['bm_xc'], zc=P['bm_zc'], sxm=P['bm_sxm'], sxl=P['bm_sxl'], szd=P['bm_szd'], szu=P['bm_szu'], H=P['bm_H'], p=P['bm_p'],
                 prof=P.get('bm_prof', 'gauss'), tdn=P.get('bm_tdn', 0.0), tup=P.get('bm_tup', 0.0), gd=P.get('bm_gd', 0.0), gr=P.get('bm_gr', 1.12), gw=P.get('bm_gw', 0.14))]


def bust_amp(x, z, P):
    """forward growth of the mounds (sum of components, |x| mirrored) + broad pec swell.  Global fit knobs: bm_scale (x H), bm_dz (shift of every zc)"""
    sc = P.get('bm_scale', 1.0)
    dz = P.get('bm_dz', 0.0)
    tot = 0.0
    for C in bust_comps(P):
        C = dict(C)
        C['H'] = C['H'] * sc
        C['zc'] = C['zc'] + dz
        if P.get('bm_signed', 0):
            for sg in (1.0, -1.0):
                Cs = dict(C); Cs['sgn'] = sg
                tot = tot + comp_amp(x, z, Cs)
        else:
            tot = tot + comp_amp(x, z, C)
    ax = np.abs(x)
    dxp, dzp = (ax - P['bp_xc']) / P['bp_sx'], (z - P['bp_zc']) / P['bp_sz']
    return tot + P['bp_H'] * np.exp(-(dxp * dxp + dzp * dzp))


def fill_amp(x, z, P):
    """forward push of the chest wall between the sternum and the arm junction (the ring is too round there)"""
    ax = np.abs(x)
    hx = sstep5((ax - P['pf_x0']) / (P['pf_x1'] - P['pf_x0'])) * (1 - sstep5((ax - P['pf_x2']) / (P['pf_x3'] - P['pf_x2'])))
    hz = sstep5((z - P['pf_z0']) / P['pf_zw']) * (1 - sstep5((z - P['pf_z1']) / P['pf_zw']))
    return P['pf_A'] * hx * hz


def moat_amp(x, z, P):
    """wide recess (m, >=0, backward) centred on each mound (|x| mirrored): gives the mound relief without a full-width shelf"""
    R = P.get('mo_R', 0.0)
    if not R:
        return 0.0
    dxl = np.abs(x) - P['mo_xc']
    sxx = asym(dxl, P.get('mo_sxm', P['mo_sx']), P.get('mo_sxl', P['mo_sx']), 0.012)
    dx = dxl / sxx
    dz = z - P['mo_zc']
    sz = asym(dz, P['mo_szd'], P['mo_szu'], 0.010)
    return R * np.exp(-np.power(dx * dx + (dz / sz) ** 2, P.get('mo_q', 1.0)))


def sternum_amp(x, z, P):
    """x-localised recess (m, >=0, backward) of the sternal valley between the mounds: gaussian in x, bell in z"""
    R = P.get('st_R3', 0.0)
    if not R:
        return 0.0
    hz = bell(z, P['st_zc'], P['st_wd'], P['st_wu'])
    return R * hz * np.exp(-np.power(np.abs(x) / P['st_sx'], P.get('st_q', 2.0)))


def round_amp(x, z, P):
    """FORM4: backward recess (m, >=0) that grows with |x| over the bust band: turns the flat-fronted ring into a rounder plan section so the domes sit on a
    curved chest (sternum line untouched).  rd_R at |x| >= rd_x1, vertical window rd_za..rd_zb (fade rd_zw)."""
    R = P.get('rd_R', 0.0)
    if not R:
        return 0.0
    hx = sstep5(np.abs(x) / P['rd_x1'])
    if P.get('rd_bell', 0):
        hz = bell(z, P['rd_zc'], P['rd_wd'], P['rd_wu'])            # smooth bell window, no edges
    else:
        hz = sstep5((z - P['rd_za']) / P['rd_zw']) * (1 - sstep5((z - P['rd_zb']) / P['rd_zw']))
    return R * hx * hz


def cleft_amp(x, z, P):
    """backward recess (m, >=0) along the midline: soft V, widening and fading upward, fading out toward the crotch arch"""
    zc = P['cl_z0']
    amp = P['cl_c'] * (1 - sstep5((z - zc) / (P['cl_z1'] - zc))) * sstep5((z - P['cl_zlo0']) / (P['cl_zlo1'] - P['cl_zlo0']))
    w = P['cl_w0'] * (1 + P['cl_wup'] * np.clip((z - zc) / (P['cl_z1'] - zc), 0, 1.5))
    return amp * np.exp(-np.power(np.abs(x) / w, P['cl_q']))


def _xzone_table():
    import torso2 as t2
    TE_ = t2.TE
    co = PS
    a, b = co[TE_[:, 0]], co[TE_[:, 1]]
    out = np.zeros(len(ZG))
    for i, z in enumerate(ZG):
        m = (a[:, 2] - z) * (b[:, 2] - z) < 0
        if not m.any():
            out[i] = np.nan
            continue
        t = (z - a[m, 2]) / (b[m, 2] - a[m, 2])
        out[i] = np.abs(a[m, 0] + t * (b[m, 0] - a[m, 0])).max()
    return gauss1d(fillnan(out), 0.006)


XZ = _xzone_table()


def lobe_target(x, z, P, Bapex):
    """absolute back-surface y (m): the pelvis ring's back half split into two half-ellipses (plan view), lobe centres +-xc(z), lateral
    semi-axis Rx = X(z) - xc(z) (same hip extent as the ring), depth semi-axis = apex line (plate table).  xc -> 0 turns it back into the ring."""
    ax = np.abs(x)
    X = np.interp(z, ZG, XZ)
    z0, z1 = P['gc_z0'], P['gc_z1']
    xc = P['gc_x0'] + (P['gc_x1'] - P['gc_x0']) * sstep((z - z0) / (z1 - z0))
    xc = xc * (1 - sstep5((z - P['gc_top0']) / (P['gc_top1'] - P['gc_top0'])))
    Rx = np.maximum((X - xc) * P['gc_Rs'], 0.04)
    ya = np.interp(z, ZG, Bapex) + P['gc_dy']
    d1 = (ax - xc) / Rx
    d2 = (ax + xc) / Rx
    yl1 = ya * np.sqrt(np.maximum(1 - d1 * d1, 0.0))
    yl2 = ya * np.sqrt(np.maximum(1 - d2 * d2, 0.0))
    if not P.get('gc_cleft_own', 1):
        # lobe OUTER shape only: ellipse beyond the lobe centre, plateau inside (the cleft is carved separately -> clean fade)
        dd = np.maximum(ax - xc, 0.0) / Rx
        yo = ya * np.sqrt(np.maximum(1 - dd * dd, 0.0))
        d0 = ax / np.maximum(X, 0.05)
        return yo - ya * np.sqrt(np.maximum(1 - d0 * d0, 0.0)), X
    ysplit = smax(yl1, yl2, P['gc_k'])
    if P.get('gc_diff', 1):
        d0 = ax / np.maximum(X, 0.05)
        ysingle = ya * np.sqrt(np.maximum(1 - d0 * d0, 0.0))
        return ysplit - ysingle, X          # relative displacement to add on top of the ring
    return ysplit, X


def lowlobe_amp(x, z, P):
    """extra backward fullness of the lower lobes (lateral to the crotch notch): gives the fold crescent a real underside"""
    ax = np.abs(x)
    dx = ax - P['ll_xc']
    sx = asym(dx, P['ll_sxm'], P['ll_sxl'], 0.012)
    zc = P['ll_zc'] + P['ll_zr'] * np.clip(ax - 0.06, 0, None)
    dz = z - zc
    sz = asym(dz, P['ll_szd'], P['ll_szu'], 0.008)
    return P['ll_A'] * np.exp(-((dx / sx) ** 2 + (dz / sz) ** 2))


def ub_amp(x, z, P):
    """backward bump (m) on the lower buttocks, z-window starting at the floor ring: steeper underside, fold crescent moves down"""
    A = P.get('ub_A', 0.0)
    if not A:
        return 0.0
    ax = np.abs(x)
    wx = np.exp(-(((ax - P['ub_xc']) / P['ub_sx']) ** 2))
    wz = sstep5((z - P['ub_z0']) / P['ub_zr']) * (1 - sstep((z - P['ub_z1']) / P['ub_zw']))
    return A * wx * wz


def gmoat_amp(x, z, P):
    """forward recess (m, >=0) around each glute lobe (|x| mirrored): strong medially (cleft flanks) and below (underbutt), absent above
    (the lobes blend into the lumbar) and weak laterally (the hip keeps its roll-over).  all radii are gaussian sigma-like."""
    R = P.get('gm_R', 0.0)
    if not R:
        return 0.0
    ax = np.abs(x)
    dxl = ax - P['gm_xc']
    sx = asym(dxl, P['gm_sxm'], P['gm_sxl'], 0.012)
    dz = z - P['gm_zc']
    sz = asym(dz, P['gm_szd'], P['gm_szu'], 0.010)
    return R * np.exp(-((dxl / sx) ** 2 + (dz / sz) ** 2))


def lobe_amp(x, z, P):
    ax = np.abs(x)
    dx = ax - P['gl_xc']
    dz = z - P['gl_zc']
    sx = asym(dx, P['gl_sxm'], P['gl_sxl'], 0.014)
    sz = asym(dz, P['gl_szd'], P['gl_szu'], 0.010)
    return P['gl_H'] * np.exp(-((dx / sx) ** 2 + (dz / sz) ** 2))


# ----------------------------------------------------------------------------------------------- build
def build3(P=None, dFw=None, dBb=None, parts=False):
    P = {**DEFAULT3, **(P or {})}
    Fw, Bb = wall3(P, dFw, dBb)
    F1v = np.interp(ZV, ZG, Fw)
    B1v = np.interp(ZV, ZG, Bb)
    y_remap = F1v + TT * (B1v - F1v)
    wtop = sstep((P['top_z1'] - ZV) / P['top_zw'])
    Wr = border_weight(P['leg_r'], P['arm_r'], P['top_r'], kind=sstep5) * wtop
    Wf = border_weight(P['leg_f'], P['arm_f'], P['top_f'], kind=sstep5) * wtop
    ff = sstep((0.50 - TT) / 0.30)
    bf = sstep((TT - 0.50) / 0.30)
    lat = sstep((np.abs(XV) - P['lf_x0']) / (P['lf_x1'] - P['lf_x0'])) * sstep((0.985 - ZV) / 0.04) * sstep((ZV - 0.80) / 0.03) * P['lf_on']
    D_remap = gsmooth(np.where(T, Wr * (y_remap - YV) * (1 - bf * lat), 0.0), P['ksm'], fixed=BORDER)
    ufill = 0.0
    if P.get('uf_k', 0.0):
        # clamp the upper chest toward the envelope: pull the surface forward by k(z) * w(|x|) * (distance behind the envelope)
        Fz = np.interp(ZV, ZG, Fw)
        behind = np.clip((YV + D_remap) - Fz, 0.0, None)                   # >= 0 : base surface behind the envelope
        kz = P['uf_k'] * sstep5((ZV - P['uf_z0']) / (P['uf_z1'] - P['uf_z0'])) * (1 - sstep5((ZV - P['uf_z1'] - 0.0) / (P['uf_z2'] - P['uf_z1'])))
        wx = 1 - sstep5((np.abs(XV) - P['uf_x1']) / (P['uf_x2'] - P['uf_x1']))
        ufill = kz * wx * behind
    if P.get('fl_k', 0.0):
        # flatten the ring section: pull the front surface toward the envelope across |x| < fl_x1 (fading to 0 at fl_x2) in the bust band
        Fz2 = np.interp(ZV, ZG, Fw)
        behind2 = np.clip((YV + D_remap) - Fz2, 0.0, None)
        kz2 = P['fl_k'] * sstep5((ZV - P['fl_za']) / P['fl_zw']) * (1 - sstep5((ZV - P['fl_zb']) / P['fl_zw']))
        wx2 = 1 - sstep5((np.abs(XV) - P['fl_x1']) / (P['fl_x2'] - P['fl_x1']))
        ufill = ufill + kz2 * wx2 * behind2
    D_bust = np.where(T, -Wf * ff * (bust_amp(XV, ZV, P) + fill_amp(XV, ZV, P) - sternum_amp(XV, ZV, P) - moat_amp(XV, ZV, P) - round_amp(XV, ZV, P) + ufill), 0.0)
    if P['gm'] == 'circ':
        Bapex = np.array([plate_back_soft(v) for v in ZG]) + (dBb if dBb is not None else 0.0)
        yt, Xv = lobe_target(XV, ZV, P, Bapex)
        wlat = 1 - sstep5((np.abs(XV) - (Xv - P['gc_lat0'])) / (P['gc_lat0'] - P['gc_lat1']))
        wg = 1 - sstep((ZV - P['gc_wg0']) / (P['gc_wg1'] - P['gc_wg0']))
        y_base = (YV + D_remap) if not P.get('gc_diff', 1) else 0.0
        D_glu = np.where(T, Wf * bf * wlat * wg * (yt - y_base), 0.0)
        if not P.get('gc_cleft_own', 1):
            D_glu = D_glu - np.where(T, Wf * bf * cleft_amp(XV, ZV, P), 0.0)
    else:
        D_glu = np.where(T, Wf * bf * (lobe_amp(XV, ZV, P) + lowlobe_amp(XV, ZV, P) + ub_amp(XV, ZV, P) - cleft_amp(XV, ZV, P) - gmoat_amp(XV, ZV, P)), 0.0)
    kf = P['kfin']
    D_feat = (gsmooth(D_bust + D_glu, kf, fixed=BORDER) if kf > 0 else D_bust + D_glu)
    if P.get('cs_k', 0):
        # FORM4: extra smoothing confined to the sternum strip |x| < cs_w: the medial dome tails meet there; at 11 mm mesh spacing they would read as a V-crease
        Dc = gsmooth(D_feat, int(P['cs_k']), fixed=BORDER)
        wcs = sstep5(1.0 - np.abs(XV) / P['cs_w']) * (ZV > 1.10) * (ZV < 1.34)
        D_feat = D_feat + wcs * (Dc - D_feat)
    D_tot = np.where(BORDER, 0.0, D_remap + D_feat)
    Bw = sstep(np.where(T, Wr, 0.0) / 0.25)
    co = CO0.copy()
    co[:, 0] += Bw * (PS[:, 0] - CO0[:, 0])
    co[:, 2] += Bw * (PS[:, 2] - CO0[:, 2])
    co[:, 1] += Bw * (PS[:, 1] - CO0[:, 1]) + D_tot
    co = np.where(T[:, None], co, CO0)
    if parts:
        return co, dict(D_remap=D_remap, D_feat=D_feat, D_tot=D_tot, Wr=Wr, Wf=Wf, Fw=Fw, Bb=Bb, P=P)
    return co


def build_final(PC, PG, z0=0.99, z1=1.06, iters=4):
    """FORM4 final build: chest/upper zone from the FORM4 parameters PC, pelvis/glute zone from the FORM3 glute parameters PG (+ the sub-pixel back-apex nudge),
    blended smoothly in z over z0..z1 (original z).  Keeps the FORM3 glute surface free of any coupling from the chest-side parameter changes
    (ksm / arm_r / top_r diffusion reaches ~1.5 mm into the pelvis).  Border vertices are pinned (zero displacement) in both builds."""
    dFc, dBc = fit_walls(PC, iters=iters, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    coC = build3(PC, dFc, dBc)
    dFg, dBg = fit_walls(PG, iters=iters, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    coG = build3(PG, dFg, dBg)
    w = sstep((CO0[:, 2] - z0) / (z1 - z0))
    co = np.where(T[:, None], coG + w[:, None] * (coC - coG), CO0)
    return co, dict(dFc=dFc, dBc=dBc, dFg=dFg, dBg=dBg)


def sil_err(co, zlo, zhi, P=None):
    fe, be = section_extents(co)
    fe, be = fillnan(fe), fillnan(be)
    ef = np.array([plate_front(z) for z in ZG]) - fe
    eb = np.array([plate_back_soft(z) for z in ZG]) - be
    if P is not None and P.get('bk_amp', 0.0):
        eb = eb + P['bk_amp'] * np.exp(-((ZG - P['bk_zc']) / P['bk_sz']) ** 2)       # FORM4: the back silhouette TARGET carries the sub-pixel glute apex
    m = (ZG >= zlo) & (ZG <= zhi)
    return ef, eb, m


def fit_walls(P=None, iters=4, zlo=0.82, zhi=1.34, fz=(0.82, 1.12), bz=(0.82, 1.34), verbose=True, damp=0.9):
    """iterate the wall tables so the side silhouette (front min-y / back max-y over the zone) tracks the plate envelope.
    front wall only in fz (below the bust band; the mounds fit their own amplitude), back wall in bz."""
    P = {**DEFAULT3, **(P or {})}
    dF = np.zeros(len(ZG))
    dB = np.zeros(len(ZG))
    for it in range(iters):
        co = build3(P, dF, dB)
        ef, eb, _ = sil_err(co, zlo, zhi, P)
        wf = sstep((ZG - fz[0]) / 0.03) * sstep((fz[1] - ZG) / 0.03)
        wb = sstep((ZG - bz[0]) / 0.03) * sstep((bz[1] - ZG) / 0.03)
        dF = dF + damp * gauss1d(ef * wf, 0.008)
        dB = dB + damp * gauss1d(eb * wb, 0.008)
        if verbose:
            mf = (ZG >= fz[0]) & (ZG <= fz[1]); mb = (ZG >= bz[0]) & (ZG <= bz[1])
            print(f'  fit iter {it}: front rms {1000*np.sqrt((ef[mf]**2).mean()):.2f} mm  back rms {1000*np.sqrt((eb[mb]**2).mean()):.2f} mm')
    return dF, dB


def fit_bust(P=None, zr=(1.12, 1.30), scales=None, dzs=None, verbose=True):
    """grid-search the global mound scale / vertical shift so the front silhouette matches the plate over zr (wall fixed).
    returns (bm_scale, bm_dz)"""
    P = {**DEFAULT3, **(P or {})}
    scales = np.arange(0.4, 2.51, 0.1) if scales is None else scales
    dzs = np.arange(-0.012, 0.0121, 0.004) if dzs is None else dzs

    def rms(sc, dz):
        Q = {**P, 'bm_scale': float(sc), 'bm_dz': float(dz)}
        co = build3(Q)
        ef, _, m = sil_err(co, *zr)
        m = m & (ZG >= zr[0]) & (ZG <= zr[1])
        return float(np.sqrt((ef[m] ** 2).mean()))
    best = (9e9, None)
    for sc in scales:
        for dz in dzs:
            r = rms(sc, dz)
            if r < best[0]:
                best = (r, (float(sc), float(dz)))
    r0, (s0, d0) = best
    for sc in np.arange(s0 - 0.08, s0 + 0.081, 0.02):
        for dz in np.arange(d0 - 0.003, d0 + 0.0031, 0.0015):
            r = rms(sc, dz)
            if r < best[0]:
                best = (r, (float(sc), float(dz)))
    if verbose:
        print(f'  fit_bust: scale={best[1][0]:.2f}  dz={best[1][1]*1000:+.1f} mm  rms={best[0]*1000:.2f} mm')
    return best[1]


def envelope_rows(co, zs=np.arange(0.82, 1.341, 0.02)):
    fe, be = section_extents(co)
    fe, be = fillnan(fe), fillnan(be)
    out = []
    for z in zs:
        i = int(round((z - 0.80) / 0.002))
        out.append((z, fe[i], be[i], plate_front(z), plate_back(z)))
    return np.array(out)


if __name__ == '__main__':
    P = {}
    if len(sys.argv) > 1:
        P = json.load(open(sys.argv[1]))
    dF, dB = fit_walls(P)
    co = build3(P, dF, dB)
    np.save(WD / 'data/co_f3_test.npy', co)
    r = envelope_rows(co)
    print('z  front(model,plate)  back(model,plate)  [mm]')
    for z, f, b, pf, pb in r:
        print(f'{z:.2f}  {1000*f:+7.1f} {1000*pf:+7.1f}   {1000*b:+7.1f} {1000*pb:+7.1f}')
