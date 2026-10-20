"""Female head surface function Phi: ray-chart from a centre C inside the skull.
 r(u)  = smax( smin(r_loft(u), r_under(u)), r_neck(u) )   (smooth union of loft/jaw underside/neck column)
 P(u)  = C + r(u) u + feature displacement along the loft normal  (+ ear / neck-ring corrections)"""
import json
import numpy as np
import fl, loftf, feat_f
from fl import MM, K, zrow, rowz, ycolL, ycolR, xcol, sstep

C = np.array([0.0, -0.010, 1.575])
NECK_Y0 = 0.006

# ---------------------------------------------------------------------------------------------------------------- helpers
def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def g2(x, s):
    return np.exp(-(x / s) ** 2)


def bell(t):
    """compact smooth bell on |t|<1"""
    t = np.clip(np.abs(t), 0.0, 1.0)
    return (1 - t * t) ** 2


EAR_SPLIT = 0.018


class Head:
    def __init__(self, prm=None, loft=None):
        self.L = loft or loftf.Loft()
        self.prm = dict(DEFAULT_PRM)
        if prm: self.prm.update(prm)
        p = self.prm
        # neck column built DIRECTLY from the 30 collar ring vertices: radius rho(theta, z) about the centre (0, yc(z)); at the collar it is the periodic
        # interpolation of the ring radii, blending upward to a smooth (low-harmonic) fit with the plate taper
        rp = np.load(fl.W / 'data/ring.npz')['pos']
        self.nk_yc0 = float(rp[:, 1].mean())
        th = np.arctan2(rp[:, 1] - self.nk_yc0, rp[:, 0]); rr = np.hypot(rp[:, 0], rp[:, 1] - self.nk_yc0); o = np.argsort(th)
        self.rg_th = th[o]; self.rg_r = rr[o]
        # smooth fit: mean + 2 harmonics
        A = [np.ones_like(self.rg_th)]
        for h in (1, 2, 3): A += [np.cos(h * self.rg_th), np.sin(h * self.rg_th)]
        A = np.stack(A, 1); self.rg_coef = np.linalg.lstsq(A, self.rg_r, rcond=None)[0]
        self.nk_z = np.array([1.30, 1.40, 1.425, 1.45, 1.60])
        self.nk_sc = np.array([1.02, 1.0, 0.945, 0.925, 0.922])
        self.nk_yc = np.array([self.nk_yc0, self.nk_yc0, self.nk_yc0 + 0.0008, self.nk_yc0 + 0.0012, self.nk_yc0 + 0.0012])
        self.ring_delta = None
        self.ear = feat_f.EarField()
        # ear standoff from the plate: outer x(z) of the front silhouette at the ear rows (rows 150..203) minus the local skull half width
        sil = json.load(open(fl.W / 'data/sil.json'))['front']
        rr = np.arange(150, 204); ox = np.array([0.5 * (sil[str(r)][1] - sil[str(r)][0] + 1) * K for r in rr]); oz = fl.zrow(rr)
        o = np.argsort(oz); oz, ox = oz[o], ox[o]
        sg = 0.0045 / K                                                    # Gaussian sigma 4.5 mm (~3 plate rows) in rows
        kr = int(np.ceil(3 * sg)); kk = np.exp(-0.5 * (np.arange(-kr, kr + 1) / sg) ** 2); kk /= kk.sum()
        ox = np.convolve(np.pad(ox, kr, mode='edge'), kk, mode='valid')
        ox = ox - EAR_SPLIT * ox                                              # the bald BACK figure's ears are ~4 % narrower than the front figure's: split the difference
        self.ear.outer_z = oz; self.ear.outer_x = ox
        self.ear.skull_a = lambda z: 0.975 * self.L.at(np.asarray(z, float))['a']
        pc = fl.W / 'data/prof_corr.json'
        self.prof_corr = json.load(open(pc)) if pc.exists() else None

    def rho_ring(self, th):
        th = np.asarray(th, float)
        t = np.concatenate([self.rg_th - 2 * np.pi, self.rg_th, self.rg_th + 2 * np.pi]); r = np.concatenate([self.rg_r] * 3)
        return np.interp(th, t, r)

    def rho_smooth(self, th):
        th = np.asarray(th, float); A = [np.ones_like(th)]
        for h in (1, 2, 3): A += [np.cos(h * th), np.sin(h * th)]
        return np.stack(A, -1) @ self.rg_coef

    def rho(self, th, z, ring=True):
        z = np.asarray(z, float)
        sc = np.interp(z, self.nk_z, self.nk_sc)
        if not ring: return self.rho_smooth(th) * sc
        b = sstep(1.402, 1.426, z)
        return ((1 - b) * self.rho_ring(th) + b * self.rho_smooth(th)) * sc

    def neck_implicit(self, P):
        z = P[:, 2]; yc = np.interp(z, self.nk_z, self.nk_yc)
        dy = P[:, 1] - yc; th = np.arctan2(dy, P[:, 0])
        return np.hypot(P[:, 0], dy) / self.rho(th, z, ring=False) - 1.0

    @staticmethod
    def _bisect(fn, u, C, tmax, it=44):
        lo = np.zeros(len(u)); hi = np.full(len(u), tmax)
        for _ in range(it):
            mid = 0.5 * (lo + hi)
            inside = fn(C[None, :] + mid[:, None] * u) < 0
            lo = np.where(inside, mid, lo); hi = np.where(inside, hi, mid)
        return 0.5 * (lo + hi)

    def r_loft(self, u):
        return self._bisect(self.L.implicit, u, C, 0.30)

    def r_neck(self, u):
        # column exists only below the head: the ray exit of the column, capped at z<=1.60
        def fn(P):
            F = self.neck_implicit(P)
            return np.where(P[:, 2] > 1.60, 1.0, F)
        # a ray starting inside the column exits through its side (bisect finds the exit because it is convex along the ray)
        return self._bisect(fn, u, C, 0.30)

    def r_under(self, u):
        """ray distance to the jaw underside surface z = zb0 + slope*(y-y0) + cx*x^2  (rises toward the sides: U-shaped chin from the front)"""
        p = self.prm['under']
        zb0, y0, sl, cx = p['zb0'], p['y0'], p['slope'], p.get('cx', 0.0)
        def fn(P):
            return np.where(P[:, 2] > zb0 + sl * (P[:, 1] - y0) + cx * P[:, 0] ** 2, -1.0, 1.0)      # inside (above the surface) = negative
        t = self._bisect(fn, u, C, 0.30, it=40)
        down = u[:, 2] - sl * u[:, 1] < -1e-6
        return np.where(down & (t < 0.299), t, 1e3)

    def r_head(self, u):
        p = self.prm
        return smin(self.r_loft(u), self.r_under(u), p['under']['k'])

    def r_base(self, u):
        p = self.prm
        rh = self.r_head(u)
        rn = self.r_neck(u)
        return smax(rh, rn, p['neck_k'])

    def neck_wall_point(self, R, z):
        """point of the neck column at height z with the same azimuth as the collar vertex R"""
        th = np.arctan2(R[1] - self.nk_yc0, R[0]); z = np.asarray(z, float)
        r = self.rho(np.full(z.shape, th), z); yc = np.interp(z, self.nk_z, self.nk_yc)
        return np.stack([r * np.cos(th), yc + r * np.sin(th), z], axis=-1)

    def loft_normal(self, P, h=0.0006):
        n = np.zeros_like(P)
        for i in range(3):
            d = np.zeros(3); d[i] = h
            n[:, i] = self.L.implicit(P + d) - self.L.implicit(P - d)
        nn = np.linalg.norm(n, axis=1, keepdims=True)
        return n / np.maximum(nn, 1e-12)

    # ---------------------------------------------------------------------------------------------------------------- features
    def disp(self, P, n):
        """feature displacement (metres) along the normal at base points P (N,3)"""
        p = self.prm
        x = np.abs(P[:, 0]); z = P[:, 2]; y = P[:, 1]
        d = np.zeros(len(P))
        face = sstep(-0.012, -0.035, y)                                  # 1 on the front, 0 on the back
        # brow swell
        b = p['brow']
        d += face * b['amp'] * g2(z - b['z'], b['sz']) * (1.0 - sstep(b['x0'], b['x1'], x))
        # cheeks
        c = p['cheek']
        d += face * c['amp'] * np.exp(-(((x - c['x']) / c['sx']) ** 2 + ((z - c['z']) / c['sz']) ** 2))
        # nose (profile curve along z, lateral bell)
        nz = np.array(p['nose']['prof']); w = np.interp(z, p['nose']['wz'], p['nose']['w'])
        zz = rowz_to_z(nz[:, 0]); o = np.argsort(zz)
        prof = np.interp(z, zz[o], (nz[:, 1] * MM)[o], left=0.0, right=0.0)
        d += face * prof * nose_lat(x / w)
        # lips
        lp = p['lips']
        up = lp['up_amp'] * g2(z - lp['up_z'], lp['up_sz']) * bell(x / lp['up_hw'])
        lo = lp['lo_amp'] * g2(z - lp['lo_z'], lp['lo_sz']) * bell(x / lp['lo_hw'])
        d += face * (up + lo)
        zs = self.seam_z(x)
        d -= face * lp['seam_amp'] * g2(z - zs, lp['seam_w']) * (1.0 - sstep(lp['seam_hw'] - 0.004, lp['seam_hw'], x))
        d -= face * lp['ml_amp'] * g2(z - lp['ml_z'], lp['ml_w']) * bell(x / lp['lo_hw'])
        if self.prof_corr:
            d += face * np.interp(z, self.prof_corr['z'], self.prof_corr['dy']) * np.exp(-(x / 0.030) ** 2)
        nz = p['nostril']
        d -= face * nz['amp'] * np.exp(-(((x - nz['cx']) / nz['rx']) ** 2 + ((z - nz['cz']) / nz['rz']) ** 2))
        return d

    def seam_z(self, x):
        s = self.prm['lips']
        t = np.clip(np.abs(x) / s['seam_hw'], 0, 1)
        return s['seam_zc'] + (s['seam_zk'] - s['seam_zc']) * t ** s['seam_pow']

    # ---------------------------------------------------------------------------------------------------------------- Phi
    def phi(self, u, parts=True):
        u = np.asarray(u, float)
        r = self.r_base(u)
        P0 = C[None, :] + r[:, None] * u
        if not parts:
            return P0
        n = self.loft_normal(P0)
        P = P0 + self.disp(P0, n)[:, None] * n
        if 'ear' in self.prm.get('parts', ('ear',)):
            ax = np.abs(P0[:, 0])
            near = (ax > 0.07) & (P0[:, 1] > -0.02) & (P0[:, 1] < 0.055) & (P0[:, 2] > 1.48) & (P0[:, 2] < 1.60)
            if near.any():
                h = self.ear.h(P0[near, 1], P0[near, 2])
                P[near, 0] += np.sign(P0[near, 0]) * h
        return P

    def _surf_xz_raw(self, x, z, iters=34, ylo=-0.20, yhi=0.02):
        """surface point (skin, base+features+ear) on the RAY-CHART line (x, y, z): y found by bisection on the ray-chart inside/outside test.
        NOTE: Phi displaces along the normal, so the returned point generally has (x, z) different from the request (tangential part of the displacement)."""
        x = np.asarray(x, float).ravel(); z = np.asarray(z, float).ravel()
        lo = np.full(len(x), ylo); hi = np.full(len(x), yhi)          # lo: outside (in front of the face), hi: inside
        for _ in range(iters):
            y = 0.5 * (lo + hi)
            Q = np.stack([x, y, z], -1); d = Q - C[None, :]; rq = np.linalg.norm(d, axis=1); u = d / rq[:, None]
            P = self.phi(u); rs = np.linalg.norm(P - C[None, :], axis=1)
            inside = rq < rs
            hi = np.where(inside, y, hi); lo = np.where(inside, lo, y)
        y = 0.5 * (lo + hi)
        Q = np.stack([x, y, z], -1); d = Q - C[None, :]; u = d / np.linalg.norm(d, axis=1, keepdims=True)
        return self.phi(u), u

    def surf_xz(self, x, z, iters=34, ylo=-0.20, yhi=0.02, exact=True, passes=7, tol=2e-7):
        """surface point whose FRONT PROJECTION is exactly (x, z): fixed-point iteration on the request (the displacement moves the point tangentially
        relative to the ray from C, up to ~5 mm on the lips / nose, so one raw bisection lands off the requested (x, z))"""
        x = np.asarray(x, float).ravel(); z = np.asarray(z, float).ravel()
        qx, qz = x.copy(), z.copy()
        for k in range(passes if exact else 1):
            P, u = self._surf_xz_raw(qx, qz, iters, ylo, yhi)
            if not exact: break
            ex = np.clip(x - P[:, 0], -0.004, 0.004); ez = np.clip(z - P[:, 2], -0.008, 0.008)
            if max(np.abs(ex).max(), np.abs(ez).max()) < tol: break
            qx = qx + ex; qz = qz + ez
        return P, u


def nose_lat(t):
    t = np.clip(np.abs(t), 0.0, 1.0)
    return (1 - t * t) ** 1.35


def bell_flat(t):
    t = np.clip(np.abs(t), 0.0, 1.0)
    return (1 - t ** 3) ** 2


def rowz_to_z(rows):
    return zrow(np.asarray(rows, float))[::-1] if False else zrow(np.asarray(rows, float))


DEFAULT_PRM = dict(
    under=dict(zb0=1.4269, y0=-0.097, slope=0.150, k=0.028, cx=4.2),
    neck_k=0.004,
    nostril=dict(amp=0.0, cx=0.0128, rx=0.0042, cz=float(zrow(201.0)), rz=0.0026),
    brow=dict(amp=0.0030, z=1.595, sz=0.0078, x0=0.045, x1=0.085),
    cheek=dict(amp=0.0042, x=0.060, sx=0.024, z=1.522, sz=0.022),
    nose=dict(
        # (plate row, forward mm over the base plane)
        prof=[(160, 0.0), (165, 0.0), (170, 1.5), (175, 4.6), (180, 11.5), (185, 19.2), (188, 23.0), (191, 25.0), (193.5, 24.6), (196, 21.5), (199, 13.8), (200.5, 10.8), (202, 7.7), (203.5, 5.4), (205.5, 2.0), (208, 0.0)],
        wz=[1.40, 1.4925, 1.51, 1.52, 1.53, 1.54, 1.548, 1.565, 1.60], w=[0.0235, 0.0235, 0.0230, 0.0218, 0.0192, 0.0160, 0.0138, 0.0132, 0.0132]),
    lips=dict(up_amp=0.0075, up_z=1.4880, up_sz=0.0052, up_hw=0.030, lo_amp=0.0050, lo_z=1.4672, lo_sz=0.0052, lo_hw=0.026,
              seam_amp=0.0003, seam_w=0.0020, seam_hw=0.0355, seam_zc=float(zrow(218.0)), seam_zk=float(zrow(213.7)), seam_pow=1.6, ml_amp=0.0012, ml_z=1.4575, ml_w=0.0035),
)


def sphere_grid(nth=180, nph=120):
    """uniform lat-long directions about +z (phi from the top)"""
    th = np.linspace(-np.pi, np.pi, nth, endpoint=False)
    ph = np.linspace(0.004, np.pi - 0.004, nph)
    T, Pp = np.meshgrid(th, ph)
    u = np.stack([np.sin(Pp) * np.cos(T), np.sin(Pp) * np.sin(T), np.cos(Pp)], axis=-1).reshape(-1, 3)
    return u, nth, nph
