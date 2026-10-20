"""Head2: F1 analytic head with a rebuilt lower face (MicroF2).
 - r_under: underside surface z = zb0 + slope*(y-y0) + cx*x^2 (+cx4*x^4) as before but with parameters fitted to the plate under-chin line
 - r_head: smooth-min blend radius k(x) that GROWS toward the sides (chin corner R~9 mm at the midline -> soft jaw edge laterally)
 - optional extra lower-face feature displacement (cheek/jaw body fullness)"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, geo, fl
from fl import sstep
from geo import smin, smax, C


SMIN = dict(mode='quad', mul=1.0)       # lower-face smooth-min: 'quad' (F1/F2: C1 only, curvature jumps at the blend boundary), 'cubic' (C2), 'exp' (C-infinity)


def smin_exp(a, b, k):
    return np.minimum(a, b) - k * np.log1p(np.exp(-np.abs(a - b) / k))


def smin_cubic(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h ** 3 * k / 6.0


class Head2(geo.Head):
    def __init__(self, prm=None, loft=None, zmin_loft=1.395, neck_blend=(-0.075, -0.050)):
        import loftf
        super().__init__(prm, loft or loftf.Loft(zmin=zmin_loft))
        self.H_old = geo.Head(); self.neck_blend = neck_blend

    def under_z(self, P):
        """underside height at points P: new plate-line bowl for y in front, blended into the F1 plane (z = 1.4269 + 0.15 (y + 0.097) + 4.2 x^2) toward the neck so the
        neck weld region is bit-identical to F1"""
        p = self.prm['under']
        zb0, y0, sl, cx = p['zb0'], p['y0'], p['slope'], p.get('cx', 0.0); cx4 = p.get('cx4', 0.0)
        cxb = p.get('cxb', None); yf, yb = p.get('cy0', -0.09), p.get('cy1', -0.035)
        c = cx if cxb is None else cx + (cxb - cx) * sstep(yf, yb, P[:, 1])
        zn = zb0 + sl * (P[:, 1] - y0) + c * P[:, 0] ** 2 + cx4 * P[:, 0] ** 4
        if 'f1blend' in p:
            a0, a1 = p['f1blend']
            s_ = sstep(a0, a1, P[:, 1])
            zf = 1.4269 + 0.150 * (P[:, 1] + 0.097) + 4.2 * P[:, 0] ** 2
            zn = (1 - s_) * zn + s_ * zf
        return zn

    def r_under(self, u):
        p = self.prm['under']; sl = p['slope']
        if 'f1blend' in p: sl = 0.15 * 0 + sl
        def fn(P):
            return np.where(P[:, 2] > self.under_z(P), -1.0, 1.0)
        t = self._bisect(fn, u, C, 0.30, it=40)
        down = u[:, 2] - max(sl, 0.15 if 'f1blend' in p else sl) * u[:, 1] < -1e-6
        return np.where(down & (t < 0.299), t, 1e3)

    def disp(self, P, n):
        """F1 features + optional lower-face fullness bumps (self.bumps: list of dict(xc, sx, zc, sz, A) along the base normal, faded out toward the back like the other features)"""
        d = super().disp(P, n)
        for b in getattr(self, 'bumps', ()):
            x = np.abs(P[:, 0]); z = P[:, 2]; y = P[:, 1]
            face = sstep(-0.012, -0.035, y)
            d = d + face * b['A'] * np.exp(-(((x - b['xc']) / b['sx']) ** 2 + ((z - b['zc']) / b['sz']) ** 2))
        return d

    def phi(self, u, parts=True):
        """new surface in front of the neck; F1's own surface (H_old) near the neck: w = sstep(ya, yb, y_old) -> Phi_new only for y_old < ya, exactly F1 for y_old > yb"""
        Pn = super().phi(u, parts)
        if getattr(self, 'H_old', None) is None or self.neck_blend is None: return Pn
        Po = self.H_old.phi(u, parts)
        ya, yb = self.neck_blend
        w = sstep(ya, yb, Po[:, 1])[:, None]
        return (1 - w) * Pn + w * Po

    def r_head(self, u):
        p = self.prm['under']
        rl = self.r_loft(u); ru = self.r_under(u)
        if 'k1' in p:
            xa = np.abs(u[:, 0]) * np.minimum(rl, np.minimum(ru, 0.3))
            k = p['k'] + (p['k1'] - p['k']) * sstep(0.0, p.get('kx', 0.04), xa)
        else:
            k = p['k']
        if 'f1blend' in p:
            a0, a1 = p['f1blend']
            ya = C[1] + np.minimum(rl, np.minimum(ru, 0.3)) * u[:, 1]
            k = (1 - sstep(a0, a1, ya)) * k + sstep(a0, a1, ya) * 0.028
        m = SMIN['mode']
        if m == 'exp': return smin_exp(rl, ru, k * 0.3607 * SMIN['mul'])          # same peak depth at a = b as the quadratic blend (k/4 = k_e ln 2)
        if m == 'cubic': return smin_cubic(rl, ru, k * 1.5 * SMIN['mul'])          # same peak depth (k_c/6 = k/4)
        return smin(rl, ru, k)
