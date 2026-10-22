"""Analytic face sculpt on the dense proxy (Micro1h).  All fields are functions of position on the loft-based surface, so the
same field can be evaluated on ANY vertex set (dense proxy now, graded final mesh later).  Units: metres in code, mm in tables.

Stage 1 (forward / vector fields from the base positions):  brow ridge, orbit recess, nose body + alae, malar fullness, ...
Stage 2 (along the stage-1 surface normal):                 nostril pits, lid/lip creases (second pass, uses displaced normals)
"""
import numpy as np
import h1lib as H
from h1lib import K, zrow, ycol, rowz

mm = 0.001
LN2 = np.log(2.0)


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def smax(a, b, k):
    """smooth maximum of two NON-NEGATIVE height fields: max(a,b) plus a polynomial fillet that only exists where both are positive
    (identity where either field is 0, so zero background stays exactly zero)"""
    a = np.asarray(a, float); b = np.asarray(b, float)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    gate = np.clip(np.minimum(a, b) / k, 0.0, 1.0)
    gate = gate * gate * (3 - 2 * gate)
    return np.maximum(a, b) + h * h * k * 0.25 * gate


def gg(u, q):
    """generalized gaussian half-value profile: 1 at u=0, 0.5 at |u|=1, soft tails"""
    return np.exp(-LN2 * np.abs(u) ** q)


def gg2(x, z, cx, cz, rx, rz, q=2.2):
    return np.exp(-LN2 * (np.abs((x - cx) / rx) ** q + np.abs((z - cz) / rz) ** q))


# --------------------------------------------------------------------------------------------------------------------
PRM = dict(
    # ---- nose (rows = plate rows on the head-detail panel)
    nose_rows=[158, 165, 170, 175, 180, 185, 190, 195, 198, 200, 203, 205, 207, 209, 211, 214],
    nose_H=[0.0, 0.2, 2.8, 8.0, 12.3, 16.4, 20.6, 24.1, 25.0, 24.7, 23.5, 19.1, 13.5, 8.2, 3.5, 0.0],
    nose_F=[12.0, 14.5, 16.0, 18.0, 18.8, 19.0, 18.5, 17.0, 17.0, 18.5, 20.5, 19.5, 15.0, 10.0, 7.5, 6.0],
    nose_p=[2.4, 2.4, 2.35, 2.3, 2.3, 2.3, 2.25, 2.15, 2.05, 2.0, 2.0, 2.0, 2.1, 2.2, 2.4, 2.4],
    ala=dict(cx=19.5, row=203.4, rx=9.5, rz=7.5, h=12.5, beta=0.70),
    columella=dict(row=207.0, rx=8.0, rz=5.5, A=9.0, beta=0.8),
    nostril=dict(cx=14.5, row=205.2, rx=5.6, rz=2.6, depth=3.2, q=3.0),
    # ---- orbit recess (relative to the base plane), eye centre from LM
    orbit=dict(depth=5.0, rx=26.0, rz=13.5, q=2.0, nose_clear=(8.0, 20.0)),
    # ---- brow ridge bumps: (x, z, rx, rz, h) mm; mirrored
    eye=dict(lid_t=1.4, max_depth=13.0, d0=1.0, d1=12.5, lower_line=0.9, roll_up=2.3, roll_lo=1.2, crease=1.4),
    mouth=dict(scale=1.0, seam_depth=1.8, corner_depth=1.9),
    nose_groove=1.6,
    nasolabial=dict(pts=[(26.0, 1.5370), (30.0, 1.5280), (34.0, 1.5190), (38.0, 1.5110)], depth=2.7, width=3.8),
    ear=dict(S_front=2.5, S_rear=23.5, S_pow=0.7, lobe_k=0.45, D_front=11.0, D_rear=9.5, round=1.0, helix=4.4, scapha=3.4, anti=3.2, concha=8.5,
             tragus=4.4, antitragus=3.0, lobe=1.4, blur=1.2),
    brow=[(16.0, 1.6075, 14.0, 9.5, 3.6), (32.0, 1.6125, 16.0, 10.0, 5.8), (48.0, 1.6110, 16.0, 10.0, 5.3), (63.0, 1.6040, 14.0, 9.5, 3.2)],
    glabella=dict(z=1.6010, rx=12.0, rz=8.0, h=1.4),
    # ---- cheeks
    malar=dict(x=45.0, z=1.5420, rx=25.0, rz=17.0, h=6.4),
    buccal=dict(x=50.0, z=1.5030, rx=18.0, rz=11.0, h=3.0),
)


def front_mask(P):
    return sstep(-0.025, -0.075, P[:, 1])


def cap(x, z, cx, cz, rx, rz, A, beta=0.7):
    """forward 'cap' dome: A*(1-r^2)^beta inside the elliptical footprint (r<1), 0 outside"""
    r2 = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
    return A * np.maximum(1.0 - r2, 0.0) ** beta


def nose_forward(P, prm):
    """nose block: swept half-superellipse sections.  centre-line H(z) from the profile plate, foot half width F(z) from the plate's
    luminance profiles, section exponent p(z) (2 = half ellipse); smooth union (fillet) with the face plane; columella cap."""
    x = np.abs(P[:, 0]); z = P[:, 2]; zr = rowz(z)
    rows = np.array(prm['nose_rows'], float)
    Hz = np.interp(zr, rows, prm['nose_H']) * mm
    F = np.interp(zr, rows, prm['nose_F']) * mm
    p = np.interp(zr, rows, prm['nose_p'])
    u = np.clip(x / np.maximum(F, 1e-6), 0.0, 1.0)
    Hb = Hz * (1.0 - u ** p) ** (1.0 / p)
    cc = prm['columella']
    Hc = cap(x, z, 0.0, float(zrow(cc['row'])), cc['rx'] * mm, cc['rz'] * mm, cc['A'] * mm, cc['beta'])
    a = prm['ala']
    Ha = cap(x, z, a['cx'] * mm, float(zrow(a['row'])), a['rx'] * mm, a['rz'] * mm, a['h'] * mm, a['beta'])
    return smax(smax(Hb, Hc, 0.003), Ha, 0.004)


def orbit_recess(P, prm):
    """backward displacement (m, positive = into the head) of the eye socket bowl"""
    o = prm['orbit']
    x = np.abs(P[:, 0]); z = P[:, 2]
    ex = H.LM['eye_x']; ez = H.LM['eye_z']
    r = o['depth'] * mm * gg2(x, z, ex, ez, o['rx'] * mm, o['rz'] * mm, o['q'])
    nc = o['nose_clear']
    return r * sstep(nc[0] * mm, nc[1] * mm, x)


def brow_forward(P, prm):
    x = np.abs(P[:, 0]); z = P[:, 2]
    out = np.zeros(len(P))
    for (bx, bz, rx, rz, h) in prm['brow']:
        out = smax(out, h * mm * gg2(x, z, bx * mm, bz, rx * mm, rz * mm, 2.4), 0.003)
    g = prm['glabella']
    out = smax(out, g['h'] * mm * gg2(x, z, 0.0, g['z'], g['rx'] * mm, g['rz'] * mm, 2.2), 0.003)
    return out


def malar_forward(P, prm):
    m = prm['malar']; b = prm['buccal']
    x = np.abs(P[:, 0]); z = P[:, 2]
    out = m['h'] * mm * gg2(x, z, m['x'] * mm, m['z'], m['rx'] * mm, m['rz'] * mm, 2.2)
    out = out + b['h'] * mm * gg2(x, z, b['x'] * mm, b['z'], b['rx'] * mm, b['rz'] * mm, 2.2) * sstep(1.470, 1.490, z)
    return out


# ======================================================================================================================
# EYES: opening polygon (plate), eyeball ellipsoid, funnel recess whose floor follows the eyeball shell
# ======================================================================================================================
EYE_UP = [(168.7, 56.2), (165.4, 50.4), (163.8, 43.9), (163.1, 36.0), (164.4, 28.2), (166.6, 23.0), (169.6, 19.7)]       # (row, dx mm) outer->inner
EYE_LO = [(169.6, 19.7), (171.2, 23.0), (172.6, 28.2), (173.4, 36.0), (172.9, 43.9), (171.3, 50.4), (168.7, 56.2)]       # inner->outer


def eye_poly():
    """closed almond polygon (x>0 side), metres: columns (x, z)"""
    pts = [(dx * mm, float(zrow(r))) for r, dx in EYE_UP + EYE_LO[1:-1]]
    return np.array(pts)


def smooth_poly(poly, n=96):
    """resample the closed polygon with a periodic cubic (Catmull-Rom) to a smooth outline"""
    m = len(poly); out = []
    for i in range(m):
        p0, p1, p2, p3 = poly[(i - 1) % m], poly[i], poly[(i + 1) % m], poly[(i + 2) % m]
        for t in np.linspace(0, 1, n // m + 1, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)


def poly_dist(x, z, poly, nearest=False):
    """signed distance (m) from (x,z) to the closed polygon: negative inside. nearest=True also returns the nearest polygon point"""
    px = np.asarray(poly)[:, 0]; pz = np.asarray(poly)[:, 1]
    n = len(px); d2 = np.full(x.shape, np.inf)
    nx = np.zeros(x.shape); nz = np.zeros(x.shape)
    inside = np.zeros(x.shape, bool)
    for i in range(n):
        j = (i + 1) % n
        ax, az, bx, bz = px[i], pz[i], px[j], pz[j]
        ex, ez = bx - ax, bz - az
        t = np.clip(((x - ax) * ex + (z - az) * ez) / (ex * ex + ez * ez + 1e-18), 0, 1)
        qx, qz = ax + t * ex, az + t * ez
        dd = (x - qx) ** 2 + (z - qz) ** 2
        upd = dd < d2
        d2 = np.where(upd, dd, d2); nx = np.where(upd, qx, nx); nz = np.where(upd, qz, nz)
        cond = ((az > z) != (bz > z)) & (x < (bx - ax) * (z - az) / (bz - az + 1e-18) + ax)
        inside ^= cond
    d = np.sqrt(d2)
    sd = np.where(inside, -d, d)
    return (sd, nx, nz) if nearest else sd


EYEBALL = dict(cx=0.0373, cy=-0.1134, cz=None, ax=0.0195, ay=0.0120, az=0.0120)     # cz = LM eye_z


def eye_shell_y(x, z, t=0.0):
    """eyeball ellipsoid front surface (y), extended outside its footprint by clamping; t = outward lid thickness (m)"""
    e = EYEBALL
    cz = H.LM['eye_z']
    q = ((x - e['cx']) / (e['ax'] + t)) ** 2 + ((z - cz) / (e['az'] + t)) ** 2
    qc = np.minimum(q, 0.985)
    return e['cy'] - (e['ay'] + t) * np.sqrt(1.0 - qc)


def eye_funnel(P, prm):
    """backward displacement (m) forming the deep-set socket.  The depth is decided at the NEAREST MARGIN POINT (shell + lid
    thickness - base) and then decays outward, so the skin hugs the eyeball at the margin and climbs out of the socket beyond it."""
    o = prm['eye']
    x = np.abs(P[:, 0]); z = P[:, 2]; y0 = P[:, 1]
    poly = smooth_poly(eye_poly())
    d, qx, qz = poly_dist(x, z, poly, nearest=True)
    shell = eye_shell_y(qx, qz, o['lid_t'] * mm)
    depth = np.clip(shell - y0, 0.0, o['max_depth'] * mm)
    fall = 1.0 - sstep(o['d0'] * mm, o['d1'] * mm, np.maximum(d, 0.0))
    return depth * fall


def lid_roll(P, prm):
    """forward (m) lid thickness: a soft roll just outside the upper and lower margins (upper thicker)"""
    o = prm['eye']
    x = np.abs(P[:, 0]); z = P[:, 2]
    poly = smooth_poly(eye_poly())
    d, qx, qz = poly_dist(x, z, poly, nearest=True)
    above = (z - qz) > -0.0004
    up = o['roll_up'] * mm * np.exp(-((d - 2.8 * mm) / (2.2 * mm)) ** 2)
    lo = o['roll_lo'] * mm * np.exp(-((d - 2.2 * mm) / (1.9 * mm)) ** 2)
    r = np.where(above, up, lo) * (d > 0)
    # fade toward the inner/outer corners
    tcorner = sstep(19.7 * mm, 26.0 * mm, x) * (1 - sstep(52.0 * mm, 58.0 * mm, x))
    return r * (0.35 + 0.65 * tcorner)


def lid_crease(P, prm):
    """thin groove (m, positive = into the head) at the upper-lid crease + soft lower-lid line"""
    o = prm['eye']
    x = np.abs(P[:, 0]); z = P[:, 2]
    xs = np.array([19.7, 28.0, 36.0, 44.0, 52.0, 58.0]) * mm
    zs = np.array([1.5985, 1.5990, 1.5970, 1.5950, 1.5925, 1.5890])
    zc = np.interp(x, xs, zs)
    g = o['crease'] * mm * np.exp(-((z - zc) / (1.6 * mm)) ** 2) * sstep(17 * mm, 22 * mm, x) * (1 - sstep(56 * mm, 64 * mm, x))
    zl = np.interp(x, [19.7 * mm, 36 * mm, 56 * mm], [1.5700, 1.5675, 1.5705])
    g2 = o['lower_line'] * mm * np.exp(-((z - zl) / (2.2 * mm)) ** 2) * sstep(20 * mm, 26 * mm, x) * (1 - sstep(52 * mm, 60 * mm, x))
    return g + g2


# ======================================================================================================================
# MOUTH / CHIN / NASOLABIAL
# ======================================================================================================================
def seam_z(x):
    """mouth seam height vs |x| (smile: centre low, corners up)"""
    c = float(zrow(227.8)); cor = float(zrow(224.0))
    u = np.clip(np.abs(x) / (36.3 * mm), 0, 1.15)
    return c + (cor - c) * u ** 4.5


MOUTH_ROWS = [205, 211, 216, 220, 222, 224, 226.2, 228, 230.5, 233, 236, 239, 243, 248, 252, 258, 262]
MOUTH_H = [0.0, 6.7, 6.9, 7.0, 6.8, 5.0, 2.9, 3.8, 5.3, 4.8, 2.0, -1.5, 0.4, 1.3, 1.6, 1.2, 0.8]          # forward of the face plane at x=0 (profile plate)
MOUTH_W = [20.0, 22.0, 26.0, 30.0, 33.0, 36.0, 38.0, 36.5, 32.0, 28.0, 25.0, 24.0, 22.0, 21.0, 20.0, 19.0, 18.0]


def mouth_forward(P, prm):
    """lips / philtrum / chin boss: centre profile from the plate, width tapering, shifted along the smile arc"""
    m = prm['mouth']
    x = np.abs(P[:, 0]); z = P[:, 2]
    shift = seam_z(x) - seam_z(np.zeros(1))[0]                     # corners up
    rows_eq = rowz(z - shift)
    Hm = np.interp(rows_eq, MOUTH_ROWS, MOUTH_H) * mm * m['scale']
    Wm = np.interp(rows_eq, MOUTH_ROWS, MOUTH_W) * mm
    u = np.clip(x / Wm, 0.0, 1.0)
    T = (1.0 - u ** 2.4) ** (1.0 / 2.4)
    out = Hm * T
    # chin lock: nothing below z = 1.470
    out = out * sstep(1.466, 1.476, z)
    ph = -0.8 * mm * np.exp(-((x) / (2.6 * mm)) ** 2) * sstep(1.5198, 1.5290, z) * (1 - sstep(1.5290, 1.5320, z))
    return out + ph


def mouth_pits(P, prm):
    """stage-2 (along normals): seam groove + corner dimples, positive = into the head"""
    m = prm['mouth']
    x = np.abs(P[:, 0]); z = P[:, 2]
    zs = seam_z(x)
    seam = m['seam_depth'] * mm * np.exp(-((z - zs) / (1.1 * mm)) ** 2) * (1 - sstep(34 * mm, 40 * mm, x))
    cor = m['corner_depth'] * mm * gg2(x, z, 37.0 * mm, float(zrow(224.0)), 3.2 * mm, 3.0 * mm, 2.0)
    return seam + cor


def nose_groove(P, prm):
    """alar / nasofacial groove just outside the nose foot (stage 2, positive = into the head)"""
    x = np.abs(P[:, 0]); z = P[:, 2]; zr = rowz(z)
    rows = np.array(prm['nose_rows'], float)
    F_ = np.interp(zr, rows, prm['nose_F']) * mm
    d = x - (F_ + 1.2 * mm)
    g = prm['nose_groove'] * mm * np.exp(-(d / (2.3 * mm)) ** 2) * sstep(1.526, 1.538, z) * (1 - sstep(1.552, 1.566, z))
    return g


def nasolabial(P, prm):
    n = prm['nasolabial']
    x = np.abs(P[:, 0]); z = P[:, 2]
    pts = np.array(n['pts']) * np.array([mm, 1.0])                    # (x mm -> m, z m)
    d = np.full(len(P), np.inf)
    for i in range(len(pts) - 1):
        ax, az = pts[i]; bx, bz = pts[i + 1]
        ex, ez = bx - ax, bz - az
        t = np.clip(((x - ax) * ex + (z - az) * ez) / (ex * ex + ez * ez), 0, 1)
        d = np.minimum(d, np.hypot(x - (ax + t * ex), z - (az + t * ez)))
    return n['depth'] * mm * np.exp(-(d / (n['width'] * mm)) ** 2)


# ======================================================================================================================
# EARS: standing flap + anatomy, placed in the side view (y,z) from the profile plate; displacement is outward (+x for x>0)
# ======================================================================================================================
EAR_OUTLINE = [(651.5, 156.8), (660.5, 158.8), (666.0, 165.0), (669.6, 175.0), (671.0, 183.0), (670.0, 190.5), (666.5, 197.5), (661.0, 203.5),
               (655.0, 208.5), (648.0, 212.0), (642.0, 212.6), (638.0, 209.5), (636.4, 204.0), (636.8, 196.0), (637.8, 188.0), (640.0, 180.0),
               (642.0, 172.0), (645.0, 164.0), (648.0, 159.2)]
EAR_HELIX_INNER = [(646, 163), (655, 163), (662, 168), (665, 176), (665, 186), (662, 195), (656, 202), (649, 206)]
EAR_ANTI = [(648.5, 198.5), (649.5, 189), (653, 179), (654, 172.5)]
EAR_ANTI_UP1 = [(654, 172.5), (650, 166.5)]
EAR_ANTI_UP2 = [(654, 172.5), (659.5, 168.5)]


def _yz(col, row):
    return float(ycol(col)), float(zrow(row))


def ear_poly():
    return smooth_poly(np.array([_yz(c, r) for c, r in EAR_OUTLINE]), n=120)


def seg_dist(a_, b_, pts):
    ex, ez = b_[0] - a_[0], b_[1] - a_[1]
    t = np.clip(((pts[0] - a_[0]) * ex + (pts[1] - a_[1]) * ez) / (ex * ex + ez * ez + 1e-18), 0, 1)
    return np.hypot(pts[0] - (a_[0] + t * ex), pts[1] - (a_[1] + t * ez))


def polyline_dist(y, z, line):
    pts = [_yz(c, r) for c, r in line]
    d = np.full(y.shape, np.inf)
    for i in range(len(pts) - 1):
        d = np.minimum(d, seg_dist(pts[i], pts[i + 1], (y, z)))
    return d


def _ear_yz(yy, zz, e):
    """ear displacement (m) as a function of side-view position only (y,z)"""
    poly = ear_poly()
    d_in = -poly_dist(yy, zz, poly)                       # >0 inside
    yf, yr = float(ycol(637.0)), float(ycol(669.7))
    S_ = (e['S_front'] + (e['S_rear'] - e['S_front']) * sstep(yf, yr, yy) ** e['S_pow']) * mm
    S_ = S_ * (e['lobe_k'] + (1 - e['lobe_k']) * sstep(1.529, 1.548, zz))
    D = (e['D_front'] + (e['D_rear'] - e['D_front']) * sstep(-0.025, 0.0, yy)) * mm
    t = np.clip(d_in / D, 0, 1)
    w = np.sqrt(np.maximum(1.0 - (1.0 - t) ** 2, 0.0)) ** e['round']         # rounded (quarter-circle-like) rolled rim
    base = S_ * w
    ins = sstep(0.0, 2.0 * mm, d_in)
    wh = sstep(float(ycol(639.0)), float(ycol(645.0)), yy)
    helix = e['helix'] * mm * np.exp(-((d_in - 3.2 * mm) / (3.0 * mm)) ** 2) * wh
    scapha = -e['scapha'] * mm * np.exp(-((d_in - 8.8 * mm) / (2.8 * mm)) ** 2) * wh
    dA = np.minimum(polyline_dist(yy, zz, EAR_ANTI), np.minimum(polyline_dist(yy, zz, EAR_ANTI_UP1), polyline_dist(yy, zz, EAR_ANTI_UP2)))
    anti = e['anti'] * mm * np.exp(-(dA / (3.6 * mm)) ** 2) * sstep(0.0, 3.0 * mm, d_in)
    cy, cz = _yz(647.5, 189.5)
    r2 = ((yy - cy) / (8.2 * mm)) ** 2 + ((zz - cz) / (11.5 * mm)) ** 2
    concha = -e['concha'] * mm * np.maximum(1 - r2, 0.0) ** 1.6
    ty, tz = _yz(640.2, 184.5)
    tragus = e['tragus'] * mm * np.exp(-(((yy - ty) / (3.4 * mm)) ** 2 + ((zz - tz) / (3.8 * mm)) ** 2))
    ay_, az_ = _yz(642.5, 197.5)
    antit = e['antitragus'] * mm * np.exp(-(((yy - ay_) / (3.4 * mm)) ** 2 + ((zz - az_) / (3.2 * mm)) ** 2))
    ly, lz = _yz(646.0, 205.5)
    lobe = e['lobe'] * mm * np.exp(-(((yy - ly) / (7.0 * mm)) ** 2 + ((zz - lz) / (6.5 * mm)) ** 2))
    relief = (helix + scapha + anti + concha + tragus + antit + lobe) * ins
    return np.where(d_in > -0.003, base + relief, 0.0)


_EAR_GRID = {}


def blur2d(a, sig_px):
    k = int(max(1, round(sig_px * 3)))
    xs = np.arange(-k, k + 1); g = np.exp(-0.5 * (xs / sig_px) ** 2); g /= g.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), g, mode='valid'), 0, a)
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), g, mode='valid'), 1, a)
    return a


def ear_field(P, prm):
    """outward displacement magnitude (m) at positions P; evaluated on a 0.4 mm (y,z) grid, blurred, bilinear-sampled"""
    e = prm['ear']
    key = repr(sorted((k, v) for k, v in e.items()))
    if key not in _EAR_GRID:
        res = 0.0004
        ys = np.arange(-0.050, 0.030, res); zs = np.arange(1.505, 1.615, res)
        Y, Z = np.meshgrid(ys, zs, indexing='ij')
        G = _ear_yz(Y.ravel(), Z.ravel(), e).reshape(Y.shape)
        if e.get('blur', 0) > 0:
            G = blur2d(G, e['blur'] * mm / res)
        _EAR_GRID[key] = (ys, zs, G, res)
    ys, zs, G, res = _EAR_GRID[key]
    ax = np.abs(P[:, 0]); y = P[:, 1]; z = P[:, 2]
    region = (ax > 0.055) & (y > ys[0]) & (y < ys[-1] - res) & (z > zs[0]) & (z < zs[-1] - res)
    out = np.zeros(len(P))
    idx = np.where(region)[0]
    fy = (y[idx] - ys[0]) / res; fz = (z[idx] - zs[0]) / res
    iy = np.floor(fy).astype(int); iz = np.floor(fz).astype(int); ty_ = fy - iy; tz_ = fz - iz
    g00 = G[iy, iz]; g10 = G[iy + 1, iz]; g01 = G[iy, iz + 1]; g11 = G[iy + 1, iz + 1]
    out[idx] = (g00 * (1 - ty_) * (1 - tz_) + g10 * ty_ * (1 - tz_) + g01 * (1 - ty_) * tz_ + g11 * ty_ * tz_)
    return out


def stage2(P1, F, prm, parts):
    """displacements along the stage-1 surface normal (nostril pits, mouth seam, nasolabial fold, lid creases)"""
    import proxy as PX
    info = {}
    P1 = np.asarray(P1, float)
    fr = front_mask(P1)
    if 'nose' in parts:
        N1 = PX.vertex_normals(P1, F)
        n = prm['nostril']
        x = np.abs(P1[:, 0]); z = P1[:, 2]
        pit = n['depth'] * mm * gg2(x, z, n['cx'] * mm, float(zrow(n['row'])), n['rx'] * mm, n['rz'] * mm, n['q']) * fr
        P1 = P1 - N1 * pit[:, None]
        info['pit_max_mm'] = float(pit.max() * 1000)
    if 'mouth' in parts or 'eye' in parts:
        N2 = PX.vertex_normals(P1, F)
        pits = np.zeros(len(P1))
        if 'mouth' in parts:
            pits += mouth_pits(P1, prm) * fr + nasolabial(P1, prm) * fr + nose_groove(P1, prm) * fr
        if 'eye' in parts:
            pits += lid_crease(P1, prm) * fr
        P1 = P1 - N2 * pits[:, None]
    return P1, info


def apply(P, N, prm=None, parts=('nose', 'orbit', 'brow', 'cheek', 'eye', 'mouth', 'ear'), F=None):
    prm = {**PRM, **(prm or {})}
    P = np.asarray(P, float).copy()
    fr = front_mask(P)
    fwd = np.zeros(len(P))
    info = {}
    if 'nose' in parts:
        h = nose_forward(P, prm); fwd += h; info['nose_max_mm'] = float(h.max() * 1000)
    if 'orbit' in parts:
        r = orbit_recess(P, prm); fwd -= r; info['orbit_max_mm'] = float(r.max() * 1000)
    if 'eye' in parts:
        r = eye_funnel(P, prm); fwd -= r; info['eye_max_mm'] = float(r.max() * 1000)
        fwd += lid_roll(P, prm)
    if 'mouth' in parts:
        m_ = mouth_forward(P, prm); fwd += m_; info['mouth_max_mm'] = float(m_.max() * 1000)
    if 'brow' in parts:
        b = brow_forward(P, prm); fwd += b; info['brow_max_mm'] = float(b.max() * 1000)
    if 'cheek' in parts:
        c = malar_forward(P, prm); fwd += c; info['malar_max_mm'] = float(c.max() * 1000)
    P1 = P.copy()
    P1[:, 1] -= fwd * fr
    if 'ear' in parts:
        ef = ear_field(P1, prm)
        P1[:, 0] += np.sign(P1[:, 0]) * ef
        info['ear_max_mm'] = float(ef.max() * 1000)
    if F is not None:
        P1, info2 = stage2(P1, F, prm, parts)
        info.update(info2)
    return P1, info
