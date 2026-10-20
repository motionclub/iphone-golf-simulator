"""Female analytic head base ("loft") from the plate silhouettes + feature-free base planes.
Per height z the head section is two half superellipses about the vertical axis (0, yw(z)):
   back  : |x/a|^nb + |dy/b|^nb = 1      front : |x/a|^nf + |dy/f|^nf = 1
a(z) half width (front plate, ears excluded), yf(z)/yb(z) front BASE plane / back extent (profile plates; nose, lips, brow swell are features)."""
import json
import numpy as np
import fl
from fl import K, zrow, rowz, ycolL, ycolR, xcol

SIL = json.load(open(fl.W / 'data/sil.json'))


def smooth_arr(z, v, sig):
    out = np.empty_like(v)
    for i, zi in enumerate(z):
        w = np.exp(-0.5 * ((z - zi) / sig) ** 2); out[i] = (w * v).sum() / w.sum()
    return out


def plate_rows(r0=66, r1=252):
    rows = np.arange(r0, r1 + 1)
    hw = np.full(len(rows), np.nan); yf = np.full(len(rows), np.nan); yb = np.full(len(rows), np.nan)
    for i, r in enumerate(rows):
        f = SIL['front'][str(r)]; l = SIL['left'][str(r)]; rr = SIL['right'][str(r)]
        if f: hw[i] = 0.5 * (f[1] - f[0] + 1) * K
        if l and rr:
            yf[i] = 0.5 * (ycolL(l[0]) + ycolR(rr[1] + 1))
            yb[i] = 0.5 * (ycolL(l[1] + 1) + ycolR(rr[0]))
    return rows, hw, yf, yb


# half widths (mm) at ear rows where the plate hides the head side behind the ears / chin rows fused with the neck:  rows -> half width (mm)
EAR_ROWS = (152, 202)
A_EAR = [(151, 99.9), (160, 98.6), (172, 95.6), (184, 92.3), (196, 88.3), (203, 85.4)]
# base front plane (plate columns of the left profile): forehead/dome from the silhouette (rows<=122), then a vertical face plane (the brow swell, nose, lips, chin boss are features)
FRONT_BASE = [(122, 569.0), (134, 568.8), (148, 569.8), (158, 570.3), (170, 570.6), (200, 570.8), (222, 571.2), (228, 571.7), (230, 572.1), (232, 572.6), (236, 573.0), (240, 573.2), (244, 574.0), (246, 575.0), (248, 578.0), (250, 584.5)]
# nape: back extent below the occiput bend is the neck line (col 685.5 -> y)
NAPE_ROW = 212


BACK_SPLIT = 0.0013          # m per side (front/back plate compromise)


class Loft:
    def __init__(self, nf=None, nb=None, tf=0.545, zmin=1.4235, r_bot=0.0):
        rows, hw, yf, yb = plate_rows()
        # --- half width
        a = hw.copy()
        er = [r for r in rows if EAR_ROWS[0] <= r <= EAR_ROWS[1]]
        a_ear = np.interp(rows, [r for r, _ in A_EAR], [v for _, v in A_EAR]) * 1e-3
        for i, r in enumerate(rows):
            if EAR_ROWS[0] <= r <= EAR_ROWS[1]: a[i] = a_ear[i]
        # --- front base plane
        yfb = yf.copy()
        fr = np.array([r for r, _ in FRONT_BASE], float); fc = np.array([c for _, c in FRONT_BASE])
        sel = rows >= 122
        yfb[sel] = ycolL(np.interp(rows[sel], fr, fc))
        # --- back
        ybk = yb.copy()
        ybk[rows >= NAPE_ROW] = np.minimum(ybk[rows >= NAPE_ROW], float(ycolL(685.8)))
        z = zrow(rows)[::-1].copy()                        # ascending z
        a = a[::-1]; yfb = yfb[::-1]; ybk = ybk[::-1]
        ok = ~(np.isnan(a) | np.isnan(yfb) | np.isnan(ybk))
        z, a, yfb, ybk = z[ok], a[ok], yfb[ok], ybk[ok]
        # smooth in squared variables (sqrt-like dome behaviour), sigma ~ 3 mm kills the 1-px silhouette quantisation
        a = np.sqrt(np.maximum(smooth_arr(z, a ** 2, 0.0030), 0)); YC = 0.003
        yfb = YC - np.sqrt(np.maximum(smooth_arr(z, (YC - yfb) ** 2, 0.0035), 0)); ybk = YC + np.sqrt(np.maximum(smooth_arr(z, (ybk - YC) ** 2, 0.0035), 0))
        zk = np.arange(zmin, fl.ZTOP + 1e-9, 0.0005)
        self.zk = zk
        self.a = np.interp(zk, z, a); self.yf = np.interp(zk, z, yfb); self.yb = np.interp(zk, z, ybk)
        cp = fl.W / 'data/a_corr.json'
        if cp.exists():
            cj = json.load(open(cp)); self.a = self.a + np.interp(zk, cj['z'], cj['da'])
        # the plates disagree: the bald BACK figure's head is ~3-4 % narrower than the FRONT figure's (female_body_bald.jpg): split the difference so both silhouettes stay <= 5 %
        self.a = self.a - BACK_SPLIT * fl.sstep(1.440, 1.500, zk)
        D = self.yb - self.yf
        self.f = tf * D; self.b = D - self.f; self.yw = self.yf + self.f
        nfk = nf or [(1.42, 2.1), (1.47, 2.2), (1.50, 2.6), (1.53, 3.0), (1.56, 3.0), (1.59, 2.8), (1.62, 2.5), (1.66, 2.3), (1.7039, 2.1)]
        nbk = nb or [(1.42, 2.2), (1.55, 2.2), (1.7039, 2.0)]
        nj = fl.W / 'data/n_knots.json'                                       # optional override of the cross-section exponents (egg-shaped sections)
        if nj.exists() and not nf and not nb:
            j = json.load(open(nj)); nfk = [tuple(v) for v in j['nf']]; nbk = [tuple(v) for v in j['nb']]
        self.nf = np.interp(zk, [z_ for z_, _ in nfk], [v for _, v in nfk]); self.nb = np.interp(zk, [z_ for z_, _ in nbk], [v for _, v in nbk])
        # rounded closing of the dome: width -> 0 exactly at the top
        t = np.clip((fl.ZTOP - zk) / 0.0018, 0.0, 1.0)
        top = np.sqrt(1 - (1 - t) ** 2)
        self.a *= top; self.f *= top; self.b *= top

    def at(self, z):
        zz = np.clip(z, self.zk[0], self.zk[-1])
        return {key: np.interp(zz, self.zk, getattr(self, key)) for key in ('a', 'yf', 'yb', 'yw', 'f', 'b', 'nf', 'nb')}

    def radius(self, theta, z):
        p = self.at(z); c = np.cos(theta); s = np.sin(theta)
        front = s < 0
        sd = np.where(front, p['f'], p['b']); n = np.where(front, p['nf'], p['nb'])
        a = np.maximum(p['a'], 1e-6); sd = np.maximum(sd, 1e-6)
        return (np.abs(c / a) ** n + np.abs(s / sd) ** n) ** (-1.0 / n)

    def point(self, theta, z):
        p = self.at(z); r = self.radius(theta, z)
        return np.stack([r * np.cos(theta), p['yw'] + r * np.sin(theta), z], axis=-1)

    def implicit(self, P):
        z = P[:, 2]; p = self.at(z)
        dy = P[:, 1] - p['yw']; front = dy < 0
        sd = np.maximum(np.where(front, p['f'], p['b']), 1e-6); n = np.where(front, p['nf'], p['nb'])
        a = np.maximum(p['a'], 1e-6)
        F = np.abs(P[:, 0] / a) ** n + np.abs(dy / sd) ** n - 1.0
        return np.where(z > fl.ZTOP, 1.0 + (z - fl.ZTOP) * 100, np.where(z < self.zk[0], 1.0 + (self.zk[0] - z) * 100, F))


def preview_mesh(loft, nz=None, ns=128, z0=1.43):
    zs = np.linspace(z0, fl.ZTOP - 0.0003, nz or 140)
    th = np.linspace(-np.pi, np.pi, ns, endpoint=False)
    V = []; F = []
    for z in zs:
        V.append(loft.point(th, np.full(ns, z)))
    V = np.concatenate(V)
    for i in range(len(zs) - 1):
        for j in range(ns):
            a = i * ns + j; b = i * ns + (j + 1) % ns; c = (i + 1) * ns + (j + 1) % ns; d = (i + 1) * ns + j
            F.append([a, b, c, d])
    top = len(V); V = np.vstack([V, [0, float(loft.at(np.array([fl.ZTOP]))['yw'][0]), fl.ZTOP]])
    base = (len(zs) - 1) * ns
    for j in range(ns): F.append([base + j, base + (j + 1) % ns, top])
    return V, F


def save_npz(path, V, F):
    off = np.concatenate([[0], np.cumsum([len(f) for f in F])]); flat = np.concatenate([np.asarray(f, np.int64) for f in F])
    np.savez(path, V=V, F=flat, Foff=off)
