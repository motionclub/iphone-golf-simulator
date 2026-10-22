"""Female face feature curves (plate-measured) and ear relief.  Plate px -> world with fl.* conversions.
Left eye / brow / ear are the IMAGE-LEFT ones in the front plate (x<0 in 3D is irrelevant: everything is mirrored by |x|)."""
import numpy as np
import fl
from fl import K, zrow, ycolL, MM, sstep


def catmull_closed(pts, n_per=8):
    pts = np.asarray(pts, float); n = len(pts); out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for t in np.linspace(0, 1, n_per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def catmull_open(pts, n_per=8):
    pts = np.asarray(pts, float); P = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]]); out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n_per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return np.array(out)


def resample_closed(c, n):
    seg = np.linalg.norm(np.roll(c, -1, axis=0) - c, axis=1); s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]
    pts = np.vstack([c, c[:1]]); t = np.linspace(0, L, n, endpoint=False)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(c.shape[1])], axis=1)


def resample_open(c, n):
    seg = np.linalg.norm(np.diff(c, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, c[:, k]) for k in range(c.shape[1])], axis=1)


def px_front(col, row, side=1.0):
    """front plate px -> (x, z)  (x signed: image-left feature gets x<0 when side=-1; we mostly use |x| = (CXF-col)*K)"""
    return np.stack([(fl.CXF - np.asarray(col, float)) * K * side, zrow(row)], axis=-1)


# ------------------------------------------------------------------------------------------------------------------------ eye aperture (lid margin) polygon, plate px (image-left eye)
EYE_PX = [(246.3, 172.5), (246.4, 168.5), (245.0, 164.0), (242.0, 160.8), (237.5, 158.8), (231.0, 157.9), (224.0, 157.7), (217.0, 158.2), (210.5, 159.4), (204.5, 160.9), (199.5, 162.0), (196.2, 162.8),
          (199.0, 165.4), (203.5, 168.8), (209.0, 172.0), (215.0, 174.3), (221.0, 175.8), (227.0, 176.6), (233.0, 176.4), (239.0, 175.4), (243.5, 174.2)]
EYE_OUTER = 11                      # index of the outer corner in EYE_PX
EYE_XCOMP = (0.060, 0.64)            # beyond |x|=0.070 the outer part is compressed (the plate eye wraps beyond the silhouette)
IRIS = dict(cx=(259 - 229.3) * K, cz=float(zrow(164.7)), R=10.55 * K, Rp=6.4 * K, hi=(3.2 * K, 3.9 * K, 1.6 * K))     # plate-measured: iris dia ~ 31 mm (horizontal chord 19.5 px), pupil dia ~ 20 mm, catch-light r ~ 2.4 mm up-right of the pupil     # centre |x|, z, radius, pupil radius, catch-light offset(x,z)+radius


def eye_poly(n_per=6):
    pts = np.array([px_front(c, r) for c, r in EYE_PX])                  # (|x|, z)
    pts[:, 0] = np.where(pts[:, 0] > EYE_XCOMP[0], EYE_XCOMP[0] + (pts[:, 0] - EYE_XCOMP[0]) * EYE_XCOMP[1], pts[:, 0])
    return catmull_closed(pts, n_per)


# ------------------------------------------------------------------------------------------------------------------------ brows (outer/lower edges), plate px (image-left brow): from the tail tip to the inner end
BROW_UP_PX = [(204.0, 147.8), (206.0, 144.8), (208.0, 142.2), (210.0, 140.6), (212.0, 139.6), (215.0, 138.1), (218.0, 137.1), (222.0, 136.5), (228.0, 136.3), (234.0, 137.0), (240.0, 138.6), (243.8, 140.2)]
BROW_LO_PX = [(204.0, 148.3), (208.0, 146.2), (212.0, 145.2), (216.0, 144.6), (222.0, 144.4), (228.0, 144.6), (234.0, 145.2), (240.0, 146.4), (243.8, 147.4)]


def brow_edges(n=24):
    up = np.array([px_front(c, r) for c, r in BROW_UP_PX]); lo = np.array([px_front(c, r) for c, r in BROW_LO_PX])
    up = resample_open(catmull_open(up, 10), n); lo = resample_open(catmull_open(lo, 10), n)
    # soft rounded inner end: the thickness closes to ~35 % over the last 14 % (plate brows end in a rounded head, not a cut)
    s = np.linspace(0.0, 1.0, n); c = 0.5 * (up + lo); h = 0.5 * (up - lo)
    cap = 1.0 - 0.65 * sstep(0.86, 1.0, s) ** 1.5
    up = c + h * cap[:, None]; lo = c - h * cap[:, None]
    return up, lo                                                          # (n,2) (|x|, z) from the tail (outer, large |x|) to the inner end


# ------------------------------------------------------------------------------------------------------------------------ nose / mouth
NOSTRIL = dict(cx=0.0128, cz=float(zrow(201.0)), rx=0.0036, rz=0.0020)
MOUTH = dict(hw=0.0354, zc=float(zrow(218.0)), zk=float(zrow(213.7)), pow=1.6, ztop=float(zrow(213.8)), ztop_k=float(zrow(213.0)))           # seam centre/corner heights, half width


# ------------------------------------------------------------------------------------------------------------------------ ear (left profile plate px) -> world (y, z)
EAR_PX = [(660, 150.4), (671.7, 153.9), (675, 161.7), (675.4, 167.5), (674.2, 173.3), (671.7, 179.2), (668.3, 185), (664.2, 191.8), (658.3, 197.0), (652.5, 200.9), (650, 202.2),
          (645.8, 199.9), (644.6, 196.0), (645, 190), (646.7, 184), (646.7, 180), (645.8, 175), (645.4, 169), (645.8, 163.3), (647.1, 158.2), (650, 153.8), (654.2, 151.0)]
EAR_DELTA = 0.0045                     # posterior root dilation: the root contour (h = 0) lies this far OUTSIDE the plate's helix outline on the back half of the ear (long soft retro-auricular slope instead of a cliff); the anterior half keeps the plate outline
EAR = dict(hf=0.0170, wall=0.0048, wall_post=0.0093, rim_amp=0.0042, rim_d=0.0034, scapha=-0.0013, scapha_d=0.0085, anti_amp=0.0029, anti_d=0.0125, concha=-0.0052,
           conch_c=(float(ycolL(657.0)), float(zrow(176.5))), conch_s=(0.0088, 0.0108), tragus=0.0034, trag_c=(float(ycolL(649.5)), float(zrow(177.5))), groove=-0.0016)


def ear_poly(n_per=5):
    pts = np.array([(float(ycolL(c)), float(zrow(r))) for c, r in EAR_PX])
    return catmull_closed(pts, n_per)


def poly_signed_dist(px, pz, poly):
    """signed distance (+ inside) of points to a closed polygon (2D arrays)"""
    px = np.asarray(px, float); pz = np.asarray(pz, float); shp = px.shape; px = px.ravel(); pz = pz.ravel()
    n = len(poly); d2 = np.full(len(px), np.inf); inside = np.zeros(len(px), bool)
    for i in range(n):
        a = poly[i]; b = poly[(i + 1) % n]; e = b - a
        t = np.clip(((px - a[0]) * e[0] + (pz - a[1]) * e[1]) / (e @ e + 1e-18), 0, 1)
        d2 = np.minimum(d2, (px - (a[0] + t * e[0])) ** 2 + (pz - (a[1] + t * e[1])) ** 2)
        cond = ((a[1] > pz) != (b[1] > pz)) & (px < (b[0] - a[0]) * (pz - a[1]) / (b[1] - a[1] + 1e-30) + a[0])
        inside ^= cond
    d = np.sqrt(d2)
    return np.where(inside, d, -d).reshape(shp)


class EarField:
    def __init__(self):
        self.poly = ear_poly()
        self.outer_z = None; self.outer_x = None; self.skull_a = None
        self.ya = self.poly[:, 0].min(); self.yp = self.poly[:, 0].max()
        self.zlo = self.poly[:, 1].min(); self.zhi = self.poly[:, 1].max()
        # per-height anterior / posterior extent of the footprint
        zz = np.linspace(self.zlo, self.zhi, 80); ya = np.full(80, np.nan); yp = np.full(80, np.nan)
        n = len(self.poly)
        for k, z in enumerate(zz):
            ys = []
            for i in range(n):
                a = self.poly[i]; b = self.poly[(i + 1) % n]
                if (a[1] - z) * (b[1] - z) < 0: ys.append(a[0] + (z - a[1]) / (b[1] - a[1]) * (b[0] - a[0]))
            if len(ys) >= 2: ya[k], yp[k] = min(ys), max(ys)
        ok = ~np.isnan(ya); self.zz = zz[ok]; self.ya_z = ya[ok]; self.yp_z = yp[ok]

    def delta_s(self, s):
        return EAR_DELTA * sstep(0.30, 0.70, s)

    def h(self, y, z):
        e = EAR
        d0 = poly_signed_dist(y, z, self.poly)
        ya = np.interp(z, self.zz, self.ya_z, left=self.ya_z[0], right=self.ya_z[-1]); yp = np.interp(z, self.zz, self.yp_z, left=self.yp_z[0], right=self.yp_z[-1])
        s = np.clip((y - ya) / np.maximum(yp - ya, 1e-4), 0, 1)
        d = d0; dd = d0 + self.delta_s(s)
        tz = np.clip((z - self.zlo) / (self.zhi - self.zlo), 0, 1)
        if self.outer_z is not None:
            hz = np.clip(np.interp(z, self.outer_z, self.outer_x) - self.skull_a(z), 0.004, 0.032) * (e['hf'] / 0.0170) * (1.0 + 0.45 * (1.0 - sstep(0.0, 0.32, tz)))
        else:
            hz = (0.0084 + 0.0120 * np.exp(-((tz - 0.62) / 0.33) ** 2)) * (e['hf'] / 0.0165)
        flap = hz * sstep(0.0, 1.0, s) ** 1.1
        ins = dd > 0
        # the narrow top and lobe rows must still reach full standoff: shorter wall ramp at both ends of the ear; long ramp on the posterior half
        wall = (e['wall'] + (e['wall_post'] - e['wall']) * sstep(0.30, 0.70, s)) * (0.62 + 0.38 * np.minimum(sstep(0.0, 0.16, tz), 1.0 - sstep(0.86, 1.0, tz)))
        env = sstep(0.0, 1.0, dd / np.maximum(wall, 1e-6))
        rim = e['rim_amp'] * np.exp(-((d - e['rim_d']) / (0.62 * e['rim_d'])) ** 2)
        sca = e['scapha'] * np.exp(-((d - e['scapha_d']) / 0.0028) ** 2)
        cy, cz = e['conch_c']; sy, sz = e['conch_s']
        uu = (y - cy) / 0.0135; vv = (z - cz) / 0.0170; rr = np.hypot(uu, vv); aa = np.arctan2(vv, uu)
        arc = sstep(np.radians(-70), np.radians(-20), aa) * (1 - sstep(np.radians(190), np.radians(240), np.where(aa < 0, aa + 2 * np.pi, aa)))
        arc = np.where(aa > np.radians(-70), np.where(aa < np.radians(190), sstep(np.radians(-70), np.radians(-10), aa), 0.0), 0.0) + 0.0
        anti = e['anti_amp'] * np.exp(-((rr - 1.0) / 0.20) ** 2) * np.clip(arc, 0, 1)
        con = e['concha'] * np.exp(-(((y - cy) / sy) ** 2 + ((z - cz) / sz) ** 2))
        ty, tz = e['trag_c']
        tra = e['tragus'] * np.exp(-(((y - ty) / 0.0030) ** 2 + ((z - tz) / 0.0040) ** 2))
        inner = np.where(ins, env * (flap + rim + sca + anti + con + tra) + (1 - env) * 0.0, 0.0)
        # retro-auricular groove outside the posterior / upper rim
        outd = np.maximum(-dd, 0.0)
        gro = e['groove'] * np.exp(-(outd / 0.0032) ** 2) * sstep(0.15, 0.5, s) * (dd < 0)
        return inner + gro
