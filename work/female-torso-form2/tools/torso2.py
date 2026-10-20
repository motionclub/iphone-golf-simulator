"""FEMALE TORSO FORM2 core (numpy only).  Positions-only deformation of the chat-7 torso zone, built from the ORIGINAL start
(SHA 200dc3b9) so the result is a drop-in replacement of chat 7's delta.

 base      : per-ring depth remap (front wall F_w(z) at the sternum line, back base B_b(z) at the cleft line)   [chat-7 machinery]
 features  : two bust domes (front) + two glute lobes (back) as smooth height fields (relative to the base wall), fitted to
             the plate side-profile envelope; the groove between the lobes (cleft) is simply the base surface
 weights   : geodesic distance from the border vertices (neck / arms / legs), smooth-stepped; border verts never move
 everything is evaluated on a Taubin-denoised copy of the surface (the surface-nets lattice jitters +-0.5 mm).
"""
import numpy as np, sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
from pathlib import Path
from targets import curves

WD = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2')
O = np.load(WD / 'data/orig.npz')
CO0 = O['co'].astype(np.float64)
ED = O['edges']
TRI = O['tri']
ZN = np.load(WD / 'data/zone_chat7.npz')
T = ZN['torso']
N = len(CO0)
EA, EB = ED[:, 0], ED[:, 1]
DEG = np.bincount(np.r_[EA, EB], minlength=N).astype(float)


def sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sstep5(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)


def taubin(P, iters=30, lam=0.5, mu=-0.53):
    P = P.copy()
    for _ in range(iters):
        for k in (lam, mu):
            s = np.zeros_like(P)
            np.add.at(s, EA, P[EB])
            np.add.at(s, EB, P[EA])
            P = P + k * (s / np.maximum(DEG, 1)[:, None] - P)
    return P


PS = taubin(CO0)                       # denoised copy (all evaluations happen here)

# ----------------------------------------------------------------------------------------------- border + geodesic weights
BORDER = np.zeros(N, bool)
m = T[EA] & ~T[EB]
BORDER[EA[m]] = True
m = T[EB] & ~T[EA]
BORDER[EB[m]] = True
Z0 = CO0[:, 2]
CLS = np.zeros(N, int)                  # 1 legs (bottom), 2 arm junction, 3 neck/shoulder top
CLS[BORDER & (Z0 < 0.83)] = 1
CLS[BORDER & (Z0 >= 0.83) & (Z0 <= 1.30) & (np.abs(CO0[:, 0]) > 0.10)] = 2
CLS[BORDER & (Z0 > 1.30)] = 3
ZE = T[EA] & T[EB]
ZEA, ZEB = EA[ZE], EB[ZE]
ZEL = np.linalg.norm(CO0[ZEA] - CO0[ZEB], axis=1)


def geodesic_from(src_mask, max_iter=400):
    d = np.where(src_mask, 0.0, 9.0)
    for _ in range(max_iter):
        a = d[ZEA] + ZEL
        b = d[ZEB] + ZEL
        nd = d.copy()
        np.minimum.at(nd, ZEB, a)
        np.minimum.at(nd, ZEA, b)
        if np.allclose(nd, d):
            break
        d = nd
    return d


D_LEG = geodesic_from(CLS == 1)
D_ARM = geodesic_from(CLS == 2)
D_TOP = geodesic_from(CLS == 3)


def border_weight(leg=0.022, arm=0.040, top=0.040, kind=sstep):
    w = kind(D_LEG / leg) * kind(D_ARM / arm) * kind(D_TOP / top)
    return np.where(T, w, 0.0)


# ----------------------------------------------------------------------------------------------- plate targets
(FZ, F1), (BZ, B1) = curves()


def gauss1d(a, sigma, step=0.002):
    k = np.arange(-int(4 * sigma / step), int(4 * sigma / step) + 1) * step
    ker = np.exp(-0.5 * (k / sigma) ** 2)
    ker /= ker.sum()
    pad = len(k) // 2
    return np.convolve(np.pad(a, (pad, pad), mode='edge'), ker, mode='valid')


ZG = np.arange(0.80, 1.372, 0.002)
TE = ED[T[EA] & T[EB]]


def section_extents(co, strip=None, zg=ZG, sel=None):
    """front (min y) / back (max y) extent of the zone edges at each z; strip=(xmin,xmax) restricts to |x| window"""
    za, zb = co[TE[:, 0], 2], co[TE[:, 1], 2]
    ya, yb = co[TE[:, 0], 1], co[TE[:, 1], 1]
    xa, xb = co[TE[:, 0], 0], co[TE[:, 1], 0]
    fe = np.full(len(zg), np.nan)
    be = np.full(len(zg), np.nan)
    for i, z in enumerate(zg):
        mk = (za - z) * (zb - z) < 0
        if not mk.any():
            continue
        t = (z - za[mk]) / (zb[mk] - za[mk])
        y = ya[mk] + t * (yb[mk] - ya[mk])
        x = xa[mk] + t * (xb[mk] - xa[mk])
        if strip is not None:
            keep = (np.abs(x) >= strip[0]) & (np.abs(x) <= strip[1])
            if not keep.any():
                continue
            y = y[keep]
        fe[i] = y.min()
        be[i] = y.max()
    return fe, be


def fillnan(a):
    a = a.copy()
    bad = np.isnan(a)
    idx = np.where(~bad)[0]
    a[bad] = np.interp(np.where(bad)[0], idx, a[idx])
    return a


# original (denoised) ring extents -> depth fraction t for every vertex
F0, B0 = section_extents(PS)
F0s, B0s = gauss1d(fillnan(F0), 0.004), gauss1d(fillnan(B0), 0.004)
TT = (PS[:, 1] - np.interp(PS[:, 2], ZG, F0s)) / np.maximum(np.interp(PS[:, 2], ZG, B0s) - np.interp(PS[:, 2], ZG, F0s), 1e-6)


def plate_front(z):
    return np.interp(z, FZ, F1)


def plate_back(z):
    return np.interp(z, BZ, B1)


_BSOFT = None


def plate_back_soft(z):
    """modelling target: plate back table with the lumbar->glute knee (z 0.92..1.05) smoothed to sigma 14 mm (table keeps +-3 mm authority)"""
    global _BSOFT
    if _BSOFT is None:
        zz = ZG
        raw = np.interp(zz, BZ, B1)
        sm = gauss1d(raw, 0.014)
        w = sstep((zz - 0.915) / 0.02) * (1 - sstep((zz - 1.04) / 0.02))
        _BSOFT = raw + w * (sm - raw)
    return np.interp(z, ZG, _BSOFT)


def gsmooth(Dv, k=6, lam=0.5, fixed=None):
    """graph diffusion of a displacement field; zero outside the zone and (optionally) pinned to zero on `fixed` vertices"""
    Dv = Dv.copy()
    for _ in range(k):
        s = np.zeros_like(Dv)
        np.add.at(s, EA, Dv[EB])
        np.add.at(s, EB, Dv[EA])
        Dv = np.where(T, (1 - lam) * Dv + lam * s / np.maximum(DEG, 1), 0.0)
        if fixed is not None:
            Dv = np.where(fixed, 0.0, Dv)
    return Dv


# =============================================================================================== design curves
def smax(a, b, k):
    h = np.clip(k - np.abs(a - b), 0, None) / k
    return np.maximum(a, b) + h * h * k / 4


def cap(rho2, c=0.35, kk=0.25):
    """sphere-cap-like bump, 1 at the centre, ~0 outside rho=sqrt(1-c^2), soft fillet of normalised width kk"""
    s = np.sqrt(np.clip(1 - rho2, 0, 1))
    g = (s - c) / (1 - c)
    return smax(g, 0.0, kk) * (rho2 < 1.6)


def knots(zk, vk, z):
    """smooth monotone-ish interpolation through knots (PCHIP-like via cosine blending of linear pieces + gaussian polish)"""
    zk = np.asarray(zk)
    vk = np.asarray(vk)
    out = np.interp(z, zk, vk)
    return out


# front wall (sternum line) and back base (cleft line) knot tables  (z, y_mm)  -> metres
def bell(z, zc, wd, wu):
    """smooth asymmetric bump 0..1 (1 at zc), widths wd below / wu above"""
    w = np.where(z < zc, wd, wu)
    return sstep5(1 - np.abs(z - zc) / w)


def wall_tables(P):
    """front wall (sternum line) and back base (central line) curves, metres.  = plate envelope, receded where the domes / lobes sit"""
    z = ZG
    Fw = np.array([plate_front(v) for v in z]) + P['st_R'] * bell(z, P['b_zc'], P['st_wd'], P['st_wu'])
    Bb = np.array([plate_back(v) for v in z]) - P['cl_C'] * sstep((P['cl_z1'] - z) / P['cl_w'])
    # below the lobe zone fall back to the start ring (the border ring is fixed there anyway)
    Fw = np.where(z < 0.84, np.interp(z, [0.795, 0.84], [-0.0943, plate_front(0.84)]), Fw)
    Bb = np.where(z < 0.84, np.interp(z, [0.795, 0.84], [0.0955, Bb[np.argmin(np.abs(z - 0.84))]]), Bb)
    return gauss1d(Fw, 0.006), gauss1d(Bb, 0.006)


DEFAULT = dict(
    st_R=0.009, st_wd=0.045, st_wu=0.060,
    cl_C=0.026, cl_z1=0.965, cl_w=0.070,
    # bust
    b_xc=0.082, b_zc=1.232, b_rxm=0.050, b_rxl=0.038, b_rzd=0.044, b_rzu=0.062, b_A=0.014, b_pu=1.8, b_pd=1.3, b_ps=1.8,
    fl_k=0.0, fl_x1=0.075, fl_x2=0.095, fl_x3=0.125, fl_z0=1.14, fl_z1=1.30,
    bb_dx=0.0, bb_dz=0.02, bb_rxm=0.066, bb_rxl=0.044, bb_rzd=0.062, bb_rzu=0.085, bb_A=0.010,
    # glutes
    g_xc=0.072, g_zc=0.885, g_rxm=0.080, g_rxl=0.090, g_rzd=0.078, g_rzu=0.100, g_A=0.034, g_pu=2.2, g_pd=1.2, g_ps=1.7, g_join=0.25,
    # weights
    leg_r=0.07, arm_r=0.05, top_r=0.05, leg_f=0.022, arm_f=0.015, top_f=0.040,
    ksm=8,
)


def bump(r2, p):
    return np.clip(1 - r2, 0, 1) ** p


def _pexp(dz, pu, pd, ps_=None, lat=None):
    """smooth exponent: pd below the centre (crisp edge), pu above (soft); depends on height only (no angular switches)"""
    lam = sstep((-dz + 0.012) / 0.024)
    return pu + (pd - pu) * lam


def _dome(x, z, xc, zc, rxm, rxl, rzd, rzu, A, pu, pd, ps_=None):
    """one-sided (|x|) dome field, metres: elliptical footprint with separate medial/lateral and lower/upper radii"""
    dx = np.abs(x) - xc
    rx = np.where(dx < 0, rxm, rxl)
    dz = z - zc
    rz = np.where(dz < 0, rzd, rzu)
    ux, uz = dx / rx, dz / rz
    return A * bump(ux ** 2 + uz ** 2, _pexp(dz, pu, pd))


def flat_field(x, z, P):
    """forward push of the chest wall at |x| in [x1,x2] (flattens the ring sag), fading to 0 at the arm border and at |x|=0"""
    ax = np.abs(x)
    hx = sstep5(ax / P['fl_x1']) * (1 - sstep((ax - P['fl_x2']) / (P['fl_x3'] - P['fl_x2'])))
    hz = sstep((z - P['fl_z0']) / 0.05) * (1 - sstep((z - P['fl_z1']) / 0.06))
    return P['fl_k'] * hx * hz


def bust_field(x, z, P):
    core = _dome(x, z, P['b_xc'], P['b_zc'], P['b_rxm'], P['b_rxl'], P['b_rzd'], P['b_rzu'], P['b_A'], P['b_pu'], P['b_pd'], P['b_ps'])
    base = _dome(x, z, P['b_xc'] + P['bb_dx'], P['b_zc'] + P['bb_dz'], P['bb_rxm'], P['bb_rxl'], P['bb_rzd'], P['bb_rzu'], P['bb_A'], 2.0, 2.0, 2.0)
    return core + base


def smin(a, b, k):
    h = np.clip(k - np.abs(a - b), 0, None) / k
    return np.minimum(a, b) - h * h * k / 4


def glute_field(x, z, P):
    dz = z - P['g_zc']
    rz = np.where(dz < 0, P['g_rzd'], P['g_rzu'])
    d1 = (x - P['g_xc']) / np.where((x - P['g_xc']) < 0, P['g_rxm'], P['g_rxl'])
    d2 = (x + P['g_xc']) / np.where((x + P['g_xc']) < 0, P['g_rxl'], P['g_rxm'])
    zt = (dz / rz) ** 2
    r2 = smin(d1 ** 2 + zt, d2 ** 2 + zt, P['g_join'])
    p = _pexp(dz, P['g_pu'], P['g_pd'])
    return P['g_A'] * bump(r2, p)


# =============================================================================================== ellipsoid features (absolute coordinates)
def smax3(a, b, k):
    return smax(a, b, k)


def ellipsoid_y(x, z, xc, zc, Rxm, Rxl, Rzd, Rzu, Ry, ya, sign):
    """surface y of a half-ellipsoid (sign=+1 back lobe, -1 front dome) with its apex (xc,zc) at |y|=|ya|; +/-inf outside footprint.
    returns y, valid-mask.  Horizontal radius Rxm (toward the midline) / Rxl (lateral); vertical Rzd (below) / Rzu (above)."""
    dx = np.abs(x) - xc
    Rx = np.where(dx < 0, Rxm, Rxl)
    dz = z - zc
    Rz = np.where(dz < 0, Rzd, Rzu)
    rad = 1 - (dx / Rx) ** 2 - (dz / Rz) ** 2
    ok = rad > 0
    yc = ya - sign * Ry
    y = yc + sign * Ry * np.sqrt(np.clip(rad, 0, None))
    return y, ok


def lobe_union_y(x, z, P):
    """back: two lobe ellipsoids (|x| symmetric -> each vertex sees the nearer lobe; the far lobe only matters across the midline)"""
    outs = []
    for sx in (-1, 1):
        xx = x * sx
        dx = xx - P['g_xc']                                   # signed offset from this lobe's centre
        Rx = np.where(dx < 0, P['g_Rxm'], P['g_Rxl'])
        dz = z - P['g_zc']
        Rz = np.where(dz < 0, P['g_Rzd'], P['g_Rzu'])
        rad = 1 - (dx / Rx) ** 2 - (dz / Rz) ** 2
        yc = P['g_ya'] - P['g_Ry']
        y = np.where(rad > 0, yc + P['g_Ry'] * np.sqrt(np.clip(rad, 0, None)), -9.0)
        outs.append(y)
    return outs


def dome_rel(x, z, P):
    """wall-relative dome: offset (m, negative = forward) of the cap surface from the local wall; +9 outside the footprint.
    cap height above the wall = b_Ry*sqrt(rad) - b_e (apex height A = b_Ry - b_e)"""
    dx = np.abs(x) - P['b_xc']
    Rx = np.where(dx < 0, P['b_Rxm'], P['b_Rxl'])
    dz = z - P['b_zc']
    Rz = np.where(dz < 0, P['b_Rzd'], P['b_Rzu'])
    rad = 1 - (dx / Rx) ** 2 - (dz / Rz) ** 2
    return np.where(rad > 0, P['b_e'] - P['b_Ry'] * np.sqrt(np.clip(rad, 0, None)), 9.0)


def dome_union_y(x, z, P):
    dx = np.abs(x) - P['b_xc']
    Rx = np.where(dx < 0, P['b_Rxm'], P['b_Rxl'])
    dz = z - P['b_zc']
    Rz = np.where(dz < 0, P['b_Rzd'], P['b_Rzu'])
    rad = 1 - (dx / Rx) ** 2 - (dz / Rz) ** 2
    yc = P['b_ya'] + P['b_Ry'] + P['b_tilt'] * dz
    return np.where(rad > 0, yc - P['b_Ry'] * np.sqrt(np.clip(rad, 0, None)), 9.0)


def wall_tables2(P):
    z = ZG
    Fw = np.array([plate_front(v) for v in z]) + P['st_R'] * bell(z, P['b_zc'], P['st_wd'], P['st_wu'])
    Bb = np.array([plate_back_soft(v) for v in z]) - P['gr_C'] * sstep((P['gr_z1'] - z) / P['gr_w'])
    Fw = np.where(z < 0.84, np.interp(z, [0.795, 0.84], [-0.0943, plate_front(0.84)]), Fw)
    Bb = np.where(z < 0.84, np.interp(z, [0.795, 0.84], [0.0955, Bb[np.argmin(np.abs(z - 0.84))]]), Bb)
    return gauss1d(Fw, 0.006), gauss1d(Bb, 0.006)


DEFAULT2 = dict(
    st_R=0.012, st_wd=0.045, st_wu=0.060,
    gr_C=0.028, gr_z1=0.950, gr_w=0.060,
    b_xc=0.074, b_Rxm=0.058, b_Rxl=0.052, b_zc=1.222, b_Rzd=0.052, b_Rzu=0.075, b_Ry=0.050, b_ya=-0.1315, b_k=0.014,
    g_xc=0.072, g_Rxm=0.085, g_Rxl=0.078, g_zc=0.875, g_Rzd=0.082, g_Rzu=0.122, g_Ry=0.0765, g_ya=0.1165, g_k=0.012,
    leg_r=0.07, arm_r=0.05, top_r=0.05, leg_f=0.022, arm_f=0.025, top_f=0.040, ksm=8, kfin=2,
    top_z1=1.345, top_zw=0.075, g_ktop=0.030, g_kz0=0.90, b_on=1.0, g_on=1.0, lf_on=1.0, lf_x0=0.10, lf_x1=0.15,
    b_tilt=0.0, b_rel=0, b_e=0.020, kfin_b=None, kfin_g=None, g_lat0=0.0, g_lat1=0.0,
)


def build2(P=None, return_parts=False):
    P = {**DEFAULT2, **(P or {})}
    Fw, Bb = wall_tables2(P)
    zv, yv, xv = PS[:, 2], PS[:, 1], PS[:, 0]
    F1v = np.interp(zv, ZG, Fw)
    B1v = np.interp(zv, ZG, Bb)
    y_remap = F1v + TT * (B1v - F1v)
    wtop = sstep((P['top_z1'] - zv) / P['top_zw'])
    Wr = border_weight(P['leg_r'], P['arm_r'], P['top_r'], kind=sstep5) * wtop
    Wf = border_weight(P['leg_f'], P['arm_f'], P['top_f'], kind=sstep5) * wtop
    ff = sstep((0.50 - TT) / 0.30)
    bf = sstep((TT - 0.50) / 0.30)
    # the back remap lowers the central line (cleft); toward the hip sides keep the original ring so the lobes merge with the hips
    lat = sstep((np.abs(xv) - P['lf_x0']) / (P['lf_x1'] - P['lf_x0'])) * sstep((0.985 - zv) / 0.04) * sstep((zv - 0.80) / 0.03) * P['lf_on']
    D_remap = gsmooth(np.where(T, Wr * (y_remap - yv) * (1 - bf * lat), 0.0), P['ksm'], fixed=BORDER)
    y1 = yv + D_remap                                      # base surface (denoised + remapped)
    kz = P['g_k'] + (P['g_ktop'] - P['g_k']) * sstep((zv - P['g_kz0']) / 0.05)      # softer blend at the upper rim
    LL, LR = lobe_union_y(xv, zv, P)
    yb = smax(smax(y1, LL, kz), LR, kz)
    yd = y1 + dome_rel(xv, zv, P) if P['b_rel'] else dome_union_y(xv, zv, P)
    yf = smin(y1, yd, P['b_k'])
    glat = 1.0 - sstep5((np.abs(xv) - P['g_lat0']) / (P['g_lat1'] - P['g_lat0'])) if P['g_lat1'] > P['g_lat0'] else 1.0      # lateral window: lobes end before the hip roll-over
    D_glu = np.where(T, Wf * P['g_on'] * bf * glat * (yb - y1), 0.0)
    D_bus = np.where(T, Wf * P['b_on'] * ff * (yf - y1), 0.0)
    D_feat = D_glu + D_bus
    kb = P['kfin_b'] if P['kfin_b'] is not None else P['kfin']
    kg = P['kfin_g'] if P['kfin_g'] is not None else P['kfin']
    D_tot = D_remap + (gsmooth(D_bus, kb, fixed=BORDER) if kb > 0 else D_bus) + (gsmooth(D_glu, kg, fixed=BORDER) if kg > 0 else D_glu)
    D_tot = np.where(BORDER, 0.0, D_tot)
    Bw = sstep(np.where(T, Wr, 0.0) / 0.25)
    co = CO0.copy()
    co[:, 0] += Bw * (PS[:, 0] - CO0[:, 0])
    co[:, 2] += Bw * (PS[:, 2] - CO0[:, 2])
    co[:, 1] += Bw * (PS[:, 1] - CO0[:, 1]) + D_tot
    co = np.where(T[:, None], co, CO0)
    if return_parts:
        return co, dict(D_remap=D_remap, D_feat=D_feat, D_tot=D_tot, Wr=Wr, Wf=Wf, Bw=Bw, P=P, Fw=Fw, Bb=Bb, y1=y1)
    return co


# =============================================================================================== build
def build(P=None, return_parts=False):
    P = {**DEFAULT, **(P or {})}
    Fw, Bb = wall_tables(P)
    zv = PS[:, 2]
    yv = PS[:, 1]
    xv = PS[:, 0]
    F1v = np.interp(zv, ZG, Fw)
    B1v = np.interp(zv, ZG, Bb)
    y_remap = F1v + TT * (B1v - F1v)
    Wr = border_weight(P['leg_r'], P['arm_r'], P['top_r'])
    Wf = border_weight(P['leg_f'], P['arm_f'], P['top_f'])
    D_remap = gsmooth(np.where(T, Wr * (y_remap - yv), 0.0), P['ksm'])
    # front/back selectors from the depth fraction
    ff = sstep((0.50 - TT) / 0.30)
    bf = sstep((TT - 0.50) / 0.30)
    D_bust = -ff * (bust_field(xv, zv, P) + flat_field(xv, zv, P))           # forward = -y
    D_glute = +bf * glute_field(xv, zv, P)         # backward = +y
    D_feat = np.where(T, Wf * (D_bust + D_glute), 0.0)
    Bw = sstep(np.where(T, Wr, 0.0) / 0.25)
    co = CO0.copy()
    co[:, 0] += Bw * (PS[:, 0] - CO0[:, 0])
    co[:, 2] += Bw * (PS[:, 2] - CO0[:, 2])
    co[:, 1] += Bw * (PS[:, 1] - CO0[:, 1]) + D_remap + D_feat
    co = np.where(T[:, None], co, CO0)
    if return_parts:
        return co, dict(D_remap=D_remap, D_feat=D_feat, Wr=Wr, Wf=Wf, Bw=Bw, P=P, Fw=Fw, Bb=Bb)
    return co


def envelope_report(co, label=''):
    fe, be = section_extents(co)
    fe, be = fillnan(fe), fillnan(be)
    rows = []
    for z in np.arange(0.80, 1.34, 0.02):
        i = int(round((z - 0.80) / 0.002))
        rows.append((z, fe[i], be[i], plate_front(z), plate_back(z)))
    r = np.array(rows)
    return r
