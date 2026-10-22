"""Clean analytic head base ("loft") built from the plate silhouettes + remap of any head-surface point set onto it.

Per height z the head section is two half superellipses about the vertical axis (0, yw(z)):
   back half  : |x/a|^nb + |dy/b|^nb = 1     (ellipse, nb ~ 2: top-down plate)
   front half : |x/a|^nf + |dy/f|^nf = 1     (squarish forehead/face front, nf ~ 3 at the cranium)
a(z) half width (front plate, ears excluded)      yb(z) back extent, yf(z) front extent (profile plate; BASE plane: no brow/nose/lips)
Radial form (closed): r(theta) = (|cos/a|^n + |sin/s|^n)^(-1/n), s = f on the face side, b on the back.
Remap:  z <= ZSPH : horizontal radial (keeps z, so landmark rows stay put)
        z >  ZSPH : spherical about C=(0,yw(ZSPH),ZSPH) with ray/loft intersection (avoids the flat apex of a z-preserving map)
"""
import numpy as np
import h1lib as H
from h1lib import K, TOP, zrow, rowz

WID_FROM_BACK = 0.40          # widest point sits at this fraction of the depth from the back (top-down plate)
ZSPH = 1.655                  # above this the remap is spherical


def _smooth(z, v, sig):
    out = np.empty_like(v)
    for i, zi in enumerate(z):
        w = np.exp(-0.5 * ((z - zi) / sig) ** 2)
        out[i] = (w * v).sum() / w.sum()
    return out


# hand-checked half widths WITHOUT ears (rows -> half width mm) from plates/sil.json + front grid (head side line at the ear rows)
HW_ANCHOR = [(76, 0.0), (80, 31.3), (86, 46.3), (92, 56.1), (98, 63.9), (104, 70.5), (110, 74.4), (116, 78.3), (122, 80.9),
             (128, 82.9), (134, 84.2), (140, 84.8), (146, 85.0), (152, 85.0), (158, 84.6), (172, 82.0), (186, 80.6), (200, 79.6),
             (214, 78.9), (222, 77.6), (230, 75.0), (238, 71.0), (246, 69.0), (256, 68.6), (270, 68.6)]


def build_knots(**kw):
    pe = H.plate_extents()
    rows = pe['rows']; zr = pe['z']; yf = pe['yf'].copy(); yb = pe['yb'].copy()
    ok = ~np.isnan(yf) & ~np.isnan(yb)
    # BASE front plane: forehead plate down to row 130, then one smooth plane (brow ridge / nose / lips / chin boss are features)
    yfb = np.interp(rows, [80, 100, 120, 130, 140, 160, 200, 252, 270],
                    [np.nan_to_num(yf[rows == 80][0]), yf[rows == 100][0], yf[rows == 120][0], yf[rows == 130][0], -0.1448, -0.1462, -0.1470, -0.1475, -0.1460])
    z = zr[ok]; order = np.argsort(z)
    z = z[order]; yfb = yfb[ok][order]; ybk = yb[ok][order]
    ar = np.array([r for r, _ in HW_ANCHOR], float); av = np.array([v for _, v in HW_ANCHOR]) / 1000.0
    a = np.interp(rowz(z), ar, av) if False else np.interp(rowz(z), ar, av)
    yfb = _smooth(z, yfb, 0.0045); ybk = _smooth(z, ybk, 0.0035); a = _smooth(z, a, 0.0030)
    zk = np.arange(1.440, TOP + 1e-9, 0.0005)
    a_i = np.interp(zk, z, a); yf_i = np.interp(zk, z, yfb); yb_i = np.interp(zk, z, ybk)
    # cranium = ellipsoid above its equator (plate: hw 85 mm, depth/2 ~104.5 mm, vertical semi-axis 85 mm; fits rows 80..130 within ~1 mm)
    R_E = 0.085; DH = 0.1045; ZEQ = TOP - R_E
    cen = 0.5 * (np.interp(ZEQ, z, yfb) + np.interp(ZEQ, z, ybk))
    s_ = np.clip((zk - ZEQ) / R_E, 0.0, 1.0); q = np.sqrt(np.maximum(1 - s_ ** 2, 0.0))
    a_e = 0.0850 * q; yf_e = cen - DH * q; yb_e = cen + DH * q
    t = np.clip((zk - (ZEQ - 0.012)) / 0.012, 0, 1); t = t * t * (3 - 2 * t)      # blend data -> ellipsoid over the 12 mm below the equator
    a_i = (1 - t) * a_i + t * a_e; yf_i = (1 - t) * yf_i + t * yf_e; yb_i = (1 - t) * yb_i + t * yb_e
    D = yb_i - yf_i
    b_i = WID_FROM_BACK * D; f_i = D - b_i
    yw_i = yb_i - b_i
    nf_i = np.interp(zk, [1.45, 1.50, 1.55, 1.57, 1.585, 1.60, 1.62, 1.66, 1.705], kw.get('nf', [1.9, 1.9, 2.2, 2.3, 2.05, 2.05, 2.1, 2.05, 2.05]))
    nb_i = np.interp(zk, [1.45, 1.55, 1.65, 1.705], [2.2, 2.1, 2.0, 2.0])
    nf_i = _smooth(zk, nf_i, 0.006); nb_i = _smooth(zk, nb_i, 0.006)
    return dict(z=zk, a=a_i, yf=yf_i, yb=yb_i, yw=yw_i, f=f_i, b=b_i, nf=nf_i, nb=nb_i)


class Loft:
    def __init__(self, knots=None, **kw):
        self.k = knots or build_knots(**kw)

    def at(self, z):
        k = self.k
        zz = np.clip(z, k['z'][0], k['z'][-1])
        return {key: np.interp(zz, k['z'], k[key]) for key in ('a', 'yf', 'yb', 'yw', 'f', 'b', 'nf', 'nb')}

    def radius(self, theta, z):
        p = self.at(z)
        c = np.cos(theta); s = np.sin(theta)
        front = s < 0
        sd = np.where(front, p['f'], p['b']); n = np.where(front, p['nf'], p['nb'])
        a = np.maximum(p['a'], 1e-5)
        t1 = np.abs(c / a) ** n; t2 = np.abs(s / sd) ** n
        return (t1 + t2) ** (-1.0 / n)

    def implicit(self, P):
        """F(P) = (|x/a|^n + |dy/s|^n) - 1 : <0 inside, >0 outside (per-z superellipse)"""
        z = P[:, 2]; p = self.at(z)
        dy = P[:, 1] - p['yw']
        front = dy < 0
        sd = np.where(front, p['f'], p['b']); n = np.where(front, p['nf'], p['nb'])
        a = np.maximum(p['a'], 1e-5)
        F = np.abs(P[:, 0] / a) ** n + np.abs(dy / sd) ** n - 1.0
        return np.where(z > TOP, 1.0 + (z - TOP) * 100, F)

    def point(self, theta, z):
        p = self.at(z)
        r = self.radius(theta, z)
        return np.stack([r * np.cos(theta), p['yw'] + r * np.sin(theta), z], axis=-1)


def weight(z, lo0=1.470, lo1=1.495):
    t = np.clip((z - lo0) / (lo1 - lo0), 0, 1)
    return t * t * (3 - 2 * t)


def remap(P, loft, w=None):
    """returns (new points, r_old, r_loft). Horizontal radial map for z<=ZSPH (blend w(z) toward the existing surface below 1.495),
    spherical (ray vs loft) map above."""
    P = np.asarray(P, float)
    out = P.copy()
    z = P[:, 2]
    low = z <= ZSPH
    # ---- horizontal radial
    Pl = P[low]; zl = Pl[:, 2]
    p = loft.at(zl)
    dx = Pl[:, 0]; dy = Pl[:, 1] - p['yw']
    theta = np.arctan2(dy, dx); rp = np.hypot(dx, dy)
    rl = loft.radius(theta, zl)
    ww = weight(zl) if w is None else w[low]
    r2 = (1 - ww) * rp + ww * rl
    out[low, 0] = r2 * np.cos(theta)
    out[low, 1] = p['yw'] + r2 * np.sin(theta)
    rp_all = np.zeros(len(P)); rl_all = np.zeros(len(P)); rp_all[low] = rp; rl_all[low] = rl
    # ---- spherical for the dome
    hi = ~low
    if hi.any():
        C = np.array([0.0, float(loft.at(np.array([ZSPH]))['yw'][0]), ZSPH])
        Ph = P[hi]
        u = Ph - C; d = np.linalg.norm(u, axis=1); u = u / np.maximum(d[:, None], 1e-9)
        lo = np.zeros(len(Ph)); hi_r = np.full(len(Ph), 0.30)
        for _ in range(48):
            mid = 0.5 * (lo + hi_r)
            Fm = loft.implicit(C + mid[:, None] * u)
            inside = Fm < 0
            lo = np.where(inside, mid, lo); hi_r = np.where(inside, hi_r, mid)
        rho = 0.5 * (lo + hi_r)
        out[hi] = C + rho[:, None] * u
        rp_all[hi] = d; rl_all[hi] = rho
    return out, rp_all, rl_all
