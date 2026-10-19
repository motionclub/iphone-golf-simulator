"""
build_karst.py — distant tower-karst islands for the resort tennis venue.

Deterministic (seeded) headless Blender build:
  numpy signed-distance field (lobes + ledges + tidal notch + flutes/strata/canopy)
  -> OpenVDB level set -> high-res mesh (>=150k tris/island, albedo+mask as vertex colours)
  -> quadric decimate -> low-poly game mesh (trimmed at z=-5 m)
  -> shared UV atlas (4096x2048, weighted texel density, >=8 px gaps)
  -> Cycles bakes high->low: albedo (emission, no lighting), AO (only-local AO node), tangent normal (OpenGL +Y)
  -> numpy hole check + dilation -> Karst_Albedo.png (RGB albedo, A=AO), Karst_Normal.png
  -> KarstIslands.fbx (Unity axes) + stats.json
  -> previews rendered from the exported FBX + PNGs only (Nishita sky, turquoise sea).

Run (see README.md):
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python build_karst.py -- [--stage all|build|preview|dev] [--fast]
"""
import bpy, bmesh, sys, os, json, math, time, argparse
import numpy as np
import openvdb as vdb

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20261017
ATLAS_W, ATLAS_H = 4096, 2048
T0 = time.time()


def log(*a):
    print("[karst %7.1fs]" % (time.time() - T0), *a, flush=True)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=["all", "build", "preview", "dev"])
    ap.add_argument("--fast", action="store_true", help="coarse voxels (dev only)")
    ap.add_argument("--only", default="", help="comma list of object names (dev only)")
    ap.add_argument("--scratch", default=os.path.join(HERE, "_scratch"))
    ap.add_argument("--exposure", type=float, default=-3.0)
    ap.add_argument("--res", default="960x540")
    ap.add_argument("--preview-samples", type=int, default=48)
    ap.add_argument("--sun-az", type=float, default=215.0)
    ap.add_argument("--tele", default="Karst_00")
    ap.add_argument("--force-preview", action="store_true")
    return ap.parse_args(argv)


# ----------------------------------------------------------------------------------------------
# noise
# ----------------------------------------------------------------------------------------------
class GNoise:
    """3D gradient (Perlin-style) noise on a 64^3 hashed lattice, random rotation + offset per instance."""

    def __init__(self, seed, N=64):
        rng = np.random.default_rng(seed)
        g = rng.normal(size=(N ** 3, 3)).astype(np.float32)
        g /= np.linalg.norm(g, axis=1, keepdims=True)
        self.gx, self.gy, self.gz = g[:, 0].copy(), g[:, 1].copy(), g[:, 2].copy()
        self.N, self.M = N, N - 1
        q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        self.R = q.astype(np.float32)
        self.off = rng.uniform(0, 64, 3).astype(np.float32)

    def __call__(self, x, y, z, rotate=True):
        if rotate:
            R = self.R
            X = R[0, 0] * x + R[0, 1] * y + R[0, 2] * z + self.off[0]
            Y = R[1, 0] * x + R[1, 1] * y + R[1, 2] * z + self.off[1]
            Z = R[2, 0] * x + R[2, 1] * y + R[2, 2] * z + self.off[2]
        else:
            X, Y, Z = x + self.off[0], y + self.off[1], z + self.off[2]
        xi = np.floor(X); yi = np.floor(Y); zi = np.floor(Z)
        xf = (X - xi).astype(np.float32); yf = (Y - yi).astype(np.float32); zf = (Z - zi).astype(np.float32)
        xi = xi.astype(np.int32); yi = yi.astype(np.int32); zi = zi.astype(np.int32)
        u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
        v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
        w = zf * zf * zf * (zf * (zf * 6 - 15) + 10)
        M, N = self.M, self.N
        res = None
        cx = [(xi & M), ((xi + 1) & M)]
        cy = [(yi & M) * N, ((yi + 1) & M) * N]
        cz = [(zi & M) * (N * N), ((zi + 1) & M) * (N * N)]
        vals = {}
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    idx = cx[dx] + cy[dy] + cz[dz]
                    vals[(dx, dy, dz)] = (np.take(self.gx, idx) * (xf - dx) + np.take(self.gy, idx) * (yf - dy)
                                          + np.take(self.gz, idx) * (zf - dz))
        x00 = vals[(0, 0, 0)] + u * (vals[(1, 0, 0)] - vals[(0, 0, 0)])
        x10 = vals[(0, 1, 0)] + u * (vals[(1, 1, 0)] - vals[(0, 1, 0)])
        x01 = vals[(0, 0, 1)] + u * (vals[(1, 0, 1)] - vals[(0, 0, 1)])
        x11 = vals[(0, 1, 1)] + u * (vals[(1, 1, 1)] - vals[(0, 1, 1)])
        y0 = x00 + v * (x10 - x00)
        y1 = x01 + v * (x11 - x01)
        res = (y0 + w * (y1 - y0)) * 1.5
        return res


class NoiseBank:
    def __init__(self, seed):
        self.seed = seed
        self.cache = {}

    def g(self, key):
        if key not in self.cache:
            self.cache[key] = GNoise(self.seed * 7919 + hash_str(key))
        return self.cache[key]

    def fbm(self, key, x, y, z, lam, octaves=3, gain=0.5, sz=1.0):
        """fbm with base wavelength lam (m); sz stretches z wavelength (sz>1 = vertically elongated)."""
        tot = 0.0
        amp = 1.0
        norm = 0.0
        f = 1.0 / lam
        for o in range(octaves):
            n = self.g("%s/%d" % (key, o))
            tot = tot + amp * n(x * f, y * f, z * (f / sz))
            norm += amp
            amp *= gain
            f *= 2.0
        return tot / norm

    def ridged(self, key, x, y, z, lam, octaves=2, gain=0.5, sz=1.0):
        tot = 0.0
        amp = 1.0
        norm = 0.0
        f = 1.0 / lam
        for o in range(octaves):
            n = self.g("%s/%d" % (key, o))
            tot = tot + amp * (1.0 - np.abs(n(x * f, y * f, z * (f / sz))))
            norm += amp
            amp *= gain
            f *= 2.0
        return tot / norm

    def crowns(self, key, x, y, z, cell, flat=0.0):
        """Tree-crown domes from a jittered 2D cell grid (xy). Returns (height 0..1, cell id 0..1)."""
        rng = np.random.default_rng(self.seed * 31 + hash_str(key))
        T = 4096
        Jx = rng.uniform(0.1, 0.9, T).astype(np.float32)
        Jy = rng.uniform(0.1, 0.9, T).astype(np.float32)
        Rr = rng.uniform(0.6, 1.0, T).astype(np.float32)
        Rr2 = Rr * Rr
        Hh = rng.uniform(0.6, 1.0, T).astype(np.float32)
        Id = rng.uniform(0, 1, T).astype(np.float32)
        # small z-dependent shear so stacked ledges do not share one pattern
        px = x / cell + z * (0.37 / cell)
        py = y / cell - z * (0.23 / cell)
        ix = np.floor(px).astype(np.int32); iy = np.floor(py).astype(np.int32)
        best = np.zeros(px.shape, np.float32)
        bid = np.zeros(px.shape, np.float32)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cx, cy = ix + dx, iy + dy
                h = ((cx * 73856093) ^ (cy * 19349663)) & (T - 1)
                ddx = px - (cx + np.take(Jx, h)); ddy = py - (cy + np.take(Jy, h))
                d2 = (ddx * ddx + ddy * ddy) / np.take(Rr2, h)
                hv = np.sqrt(np.maximum(0.0, 1.0 - d2)) * np.take(Hh, h)
                upd = hv > best
                best = np.where(upd, hv, best)
                bid = np.where(upd, np.take(Id, h), bid)
        return best, bid


def hash_str(s):
    h = 2166136261
    for c in s.encode():
        h = ((h ^ c) * 16777619) & 0xFFFFFFFF
    return h % 1000003


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


# ----------------------------------------------------------------------------------------------
# island specification
# ----------------------------------------------------------------------------------------------
class Lobe:
    def __init__(self, cx, cy, a, b, rot, n, H, capf=0.75, capp=2.2, taper=0.06, anoise=0.08, seed=0, kind="tower"):
        self.cx, self.cy, self.a, self.b, self.rot, self.n, self.H = cx, cy, a, b, rot, n, H
        self.capf, self.capp, self.taper, self.anoise, self.kind = capf, capp, taper, anoise, kind
        self.lx, self.ly = 0.0, 0.0      # lean: centre shift per metre of height
        rng = np.random.default_rng(seed)
        ks = np.arange(2, 33)
        self.hk = ks
        self.hc = (rng.normal(size=len(ks)) * (ks ** -1.0)).astype(np.float32)
        self.hp = rng.uniform(0, 2 * np.pi, len(ks)).astype(np.float32)
        self.rbar = math.sqrt(a * b)

    def q(self, x, y):
        c, s = math.cos(self.rot), math.sin(self.rot)
        u = (x - self.cx) * c + (y - self.cy) * s
        v = -(x - self.cx) * s + (y - self.cy) * c
        n = self.n
        qq = (np.abs(u / self.a) ** n + np.abs(v / self.b) ** n) ** (1.0 / n)
        th = np.arctan2(v / self.b, u / self.a)
        ang = np.zeros_like(th)
        for k, cc, pp in zip(self.hk, self.hc, self.hp):
            ang = ang + cc * np.sin(k * th + pp)
        return (qq / (1.0 + self.anoise * ang * 2.2)).astype(np.float32)

    def s(self, z):
        H = self.H
        if self.kind == "cone":
            return np.clip(1.0 - z / H, 0.0, None)
        zc = self.capf * H
        sw = 1.0 - self.taper * np.clip(z, 0, None) / H
        swc = 1.0 - self.taper * zc / H
        t = np.clip((z - zc) / (H - zc), 0.0, 1.0)
        dome = swc * np.maximum(0.0, 1.0 - t ** self.capp) ** (1.0 / self.capp)
        return np.where(z < zc, sw, dome)

    def field(self, q, z):
        f = (q - self.s(z)) * self.rbar
        return np.maximum(f, z - self.H)


class Island:
    """A karst island: tower lobes (+knobs), cone aprons, beach cones, ledges, notch, detail params."""

    def __init__(self, name, seed, voxel, weight=1.0, ridge=False):
        self.name, self.seed, self.voxel, self.weight, self.ridge = name, seed, voxel, weight, ridge
        self.rng = np.random.default_rng(seed)
        self.towers, self.aprons, self.beaches = [], [], []
        self.ledges = []   # (z, depth, width, mask_lambda, mask_bias)
        self.notch = 0.0
        self.nb = NoiseBank(seed)
        self.k_tower = 14.0
        self.detail_scale = 1.0

    # --- building helpers -------------------------------------------------------------------
    def tower(self, cx, cy, a, b, H, rot=None, n=None, capf=None, capp=None, taper=None, anoise=None, knobs=0):
        r = self.rng
        rot = r.uniform(0, np.pi) if rot is None else rot
        n = r.uniform(2.1, 3.0) if n is None else n
        if capf is None:   # dome height as a fraction of the lobe radius -> broad vegetated caps
            capf = float(np.clip(1.0 - r.uniform(0.5, 0.85) * min(a, b) / H, 0.3, 0.78))
        capp = r.uniform(1.6, 2.2) if capp is None else capp
        taper = r.uniform(0.05, 0.2) if taper is None else taper
        anoise = r.uniform(0.06, 0.10) if anoise is None else anoise
        L = Lobe(cx, cy, a, b, rot, n, H, capf, capp, taper, anoise, seed=int(r.integers(1 << 30)))
        self.towers.append(L)
        for _ in range(knobs):
            ang = r.uniform(0, 2 * np.pi)
            rr = r.uniform(0.0, 0.6)
            kx = cx + math.cos(ang) * rr * a * 0.85
            ky = cy + math.sin(ang) * rr * b * 0.85
            ka = r.uniform(0.2, 0.38) * min(a, b) + 9
            kb = ka * r.uniform(0.65, 1.0)
            zc = capf * H
            dome_h = zc + (H - zc) * (1 - min(rr * 1.05, 0.99) ** capp) ** (1 / capp)
            kH = dome_h + r.uniform(0.12, 0.35) * (H - zc) + r.uniform(4, 16)
            self.towers.append(Lobe(kx, ky, ka, kb, r.uniform(0, np.pi), r.uniform(2.0, 2.6), kH,
                                    capf=r.uniform(0.5, 0.72), capp=r.uniform(1.6, 2.2), taper=r.uniform(0.0, 0.12),
                                    anoise=0.12, seed=int(r.integers(1 << 30))))
        return L

    def spire(self, cx, cy, a, H, lean=(0.0, 0.0), knobs=1):
        L = self.tower(cx, cy, a, a * self.rng.uniform(0.75, 0.95), H, n=2.3, taper=0.12, knobs=0,
                       capf=float(np.clip(1.0 - 0.9 * a / H, 0.5, 0.85)))
        L.lx, L.ly = lean
        for _ in range(knobs):   # knob riding on the leaning summit
            k = Lobe(cx + self.rng.uniform(-0.2, 0.2) * a, cy, a * 0.45, a * 0.4, self.rng.uniform(0, np.pi),
                     2.2, H + self.rng.uniform(6, 16), capf=0.6, capp=1.9, taper=0.05, anoise=0.1,
                     seed=int(self.rng.integers(1 << 30)))
            k.lx, k.ly = lean
            self.towers.append(k)
        return L

    def apron(self, cx, cy, a, b, H, rot=None):
        rot = self.rng.uniform(0, np.pi) if rot is None else rot
        L = Lobe(cx, cy, a, b, rot, 2.0, H, anoise=0.14, seed=int(self.rng.integers(1 << 30)), kind="cone")
        self.aprons.append(L)

    def beach(self, cx, cy, a, b, rot, H=3.2):
        L = Lobe(cx, cy, a, b, rot, 2.0, H, anoise=0.05, seed=int(self.rng.integers(1 << 30)), kind="cone")
        self.beaches.append(L)

    def bounds(self):
        xs, ys = [], []
        for L in self.towers + self.aprons + self.beaches:
            R = max(L.a, L.b) * 1.4
            xs += [L.cx - R, L.cx + R]; ys += [L.cy - R, L.cy + R]
        H = max(L.H for L in self.towers)
        m = 24.0
        return (min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m, -8.0, H + 30.0)

    # --- fields -----------------------------------------------------------------------------
    def _lobe_q(self, L, X, Y):
        """grid mode (X:(nx,1,1), Y:(1,ny,1)): crop to the lobe's xy influence box."""
        lean = L.lx != 0.0 or L.ly != 0.0
        if X.ndim == 3:
            R = max(L.a, L.b) * 1.45 + 45.0
            if lean:
                R += math.hypot(L.lx, L.ly) * L.H
            xs, ys = X[:, 0, 0], Y[0, :, 0]
            i0, i1 = np.searchsorted(xs, L.cx - R), np.searchsorted(xs, L.cx + R)
            j0, j1 = np.searchsorted(ys, L.cy - R), np.searchsorted(ys, L.cy + R)
            if i1 <= i0 or j1 <= j0:
                return None
            sl = (slice(i0, i1), slice(j0, j1))
            if lean:
                return sl, (X[sl[0]], Y[:, sl[1]])
            return sl, L.q(X[sl[0]], Y[:, sl[1]])
        if lean:
            return None, (X, Y)
        return None, L.q(X, Y)

    def precompute(self, X, Y):
        P = {"qt": [self._lobe_q(L, X, Y) for L in self.towers],
             "qa": [self._lobe_q(L, X, Y) for L in self.aprons],
             "qb": [self._lobe_q(L, X, Y) for L in self.beaches]}
        Z0 = np.zeros_like(X + Y)
        led = []
        for (lz, dep, wid, lam, bias) in self.ledges:
            m = self.nb.fbm("ledge%.0f" % lz, X + Z0, Y + Z0, Z0 + lz, lam, 3)
            off = self.nb.fbm("ledgez%.0f" % lz, X + Z0, Y + Z0, Z0, 150.0, 2) * 22.0
            led.append((sstep(-0.05, 0.25, m + bias).astype(np.float32), (lz + off).astype(np.float32)))
        P["ledge"] = led
        if self.notch > 0:
            m = self.nb.fbm("notch", X + Z0, Y + Z0, Z0, 90.0, 3)
            P["notch"] = sstep(-0.25, 0.15, m).astype(np.float32)
        P["shape"] = np.broadcast_shapes(np.shape(X + Y), (1,))
        P["grid"] = np.ndim(X) == 3
        return P

    def _union(self, lst, lobes, z, shape, k):
        if shape is None:   # point mode
            f = None
            for L, (sl, q) in zip(lobes, lst):
                if isinstance(q, tuple):
                    q = L.q(q[0] - L.lx * z, q[1] - L.ly * z)
                g = L.field(q, z)
                f = g if f is None else (smin(f, g, k) if k > 0 else np.minimum(f, g))
            return f
        f = np.full(shape, 250.0, np.float32)
        for L, item in zip(lobes, lst):
            if item is None:
                continue
            sl, q = item
            if isinstance(q, tuple):
                q = L.q(q[0] - L.lx * z, q[1] - L.ly * z)
            g = L.field(q, z)
            sub = f[sl[0], sl[1], :]
            f[sl[0], sl[1], :] = smin(sub, g, k) if k > 0 else np.minimum(sub, g)
        return f

    def base(self, P, z):
        grid = P["grid"]
        shape = (P["shape"][0], P["shape"][1], np.shape(z)[-1]) if grid else None
        ft = self._union(P["qt"], self.towers, z, shape, self.k_tower)
        for (lz, dep, wid, lam, bias), (m, zoff) in zip(self.ledges, P["ledge"]):
            ft = ft + dep * sstep(zoff, zoff + wid, z) * m
        if self.notch > 0:
            ft = ft + self.notch * P["notch"] * np.exp(-((z - 1.0) / 1.9) ** 2)
        f = ft
        fa = self._union(P["qa"], self.aprons, z, shape, 0) if self.aprons else None
        if fa is not None:
            f = smin(f, fa, 16.0)
        fb = self._union(P["qb"], self.beaches, z, shape, 0) if self.beaches else None
        if fb is not None:
            f = smin(f, fb, 5.0)
        f = np.maximum(f, -8.0 - z + 1.0)    # close the bottom at z=-7
        return f.astype(np.float32), ft, fa, fb

    # masks shared by geometry + albedo
    def hmax(self):
        return max(L.H for L in self.towers)

    def jungle(self, x, y, z, nz):
        """0..1 canopy cover: gentle/medium slopes + hanging bands on cliffs (more near the top and
        under ledges) + small shrub pockets. Cliffs show through in vertical bands."""
        nb = self.nb
        zr = np.clip(z / self.hmax(), 0.0, 1.0)
        zon = sstep(1.5, 5.0, z)
        up = sstep(0.20, 0.50, nz) * zon
        steep = 1.0 - sstep(0.20, 0.50, nz)
        st = nb.fbm("strip", x, y, z, 30.0, 2, sz=4.0) + 0.25 * nb.fbm("strip2", x, y, z, 9.0, 1, sz=3.0)
        spill = 0.0
        if self.ledges:
            Z0 = np.zeros_like(x)
            for (lz, dep, wid, lam, bias) in self.ledges:
                m = sstep(-0.05, 0.25, nb.fbm("ledge%.0f" % lz, x, y, Z0 + lz, lam, 3) + bias)
                zo = lz + nb.fbm("ledgez%.0f" % lz, x, y, Z0, 150.0, 2) * 22.0
                spill = np.maximum(spill, m * sstep(zo - 55.0, zo - 8.0, z) * (z < zo + wid + 4))
        thr = 0.30 - 0.42 * sstep(0.25, 0.85, zr) - 0.30 * spill
        strip = sstep(thr - 0.12, thr + 0.08, st) * steep * sstep(8.0, 22.0, z)
        pk = nb.fbm("pocket", x, y, z, 9.0, 2, sz=1.6)
        pocket = sstep(0.30, 0.52, pk) * steep * sstep(4.0, 10.0, z)
        vegn = nb.fbm("vegedge", x, y, z, 22.0, 2) * 0.22
        up = np.clip(up + vegn * (up > 0.02), 0.0, 1.0)
        return np.clip(np.maximum(np.maximum(up, strip), pocket), 0.0, 1.0)

    def detail(self, x, y, z, nx, ny, nz):
        """Signed outward displacement in metres at surface points with base normal n."""
        nb = self.nb
        S = self.detail_scale
        steep = 1.0 - sstep(0.36, 0.70, nz)
        # big buttresses / alcoves (vertically elongated) – everywhere
        d = 9.0 * S * nb.fbm("alcove", x, y, z, 60.0 * S, 2, sz=2.4)
        # erosion flutes (sharp ridges, vertical)
        fl = nb.ridged("flute", x, y, z, 11.0 * S, 2, gain=0.55, sz=6.0) - 0.62
        d = d + steep * 3.2 * S * fl
        # strata: warped horizontal bands
        warp = nb.fbm("strwarp", x, y, z, 60.0, 2) * 6.0
        ph = (z + warp) / (8.5 * S)
        tri = np.abs((ph - np.floor(ph)) - 0.5) * 2.0
        d = d + steep * 0.9 * S * (sstep(0.55, 0.8, tri) - 0.5)
        # blocky rubble / general roughness
        d = d + 1.4 * S * nb.fbm("rough", x, y, z, 14.0 * S, 2)
        # canopy: thickness + clumpy crowns (crowns only evaluated where there is vegetation)
        veg = self.jungle(x, y, z, nz)
        vi = np.nonzero(veg > 0.01)[0]
        if len(vi):
            c1, _ = nb.crowns("crownA", x[vi], y[vi], z[vi], 10.0 * S, flat=0.3)
            c2, _ = nb.crowns("crownB", x[vi], y[vi], z[vi], 4.5 * S, flat=0.3)
            d[vi] += veg[vi] * (1.3 + 4.0 * c1 + 1.4 * c2) * S
        return d.astype(np.float32)


def make_islands(fast=False):
    vm = 2.2 if fast else 1.0
    isl = []
    # ---- Karst_00: broad hero massif, several summits, vegetated west slope + south beach (Phi-Phi like)
    I = Island("Karst_00", SEED + 0, 1.6 * vm, weight=1.0)
    I.tower(-40, 0, 175, 130, 340, rot=0.3, knobs=6)
    I.k_tower = 20.0
    I.tower(150, -30, 120, 100, 280, rot=-0.2, knobs=4)
    I.tower(-230, 60, 110, 90, 230, knobs=3)
    I.tower(-330, 10, 80, 70, 150, knobs=2)
    I.tower(40, 140, 100, 80, 250, knobs=3)
    I.tower(270, 30, 75, 65, 170, knobs=2)
    I.apron(-290, -60, 190, 120, 95, rot=0.3)
    I.apron(-40, -100, 260, 110, 60, rot=0.1)
    I.beach(-60, -190, 230, 60, 0.1)
    I.ledges = [(85, 24, 26, 130, 0.1), (185, 20, 22, 100, 0.0)]
    I.notch = 3.5
    isl.append(I)
    # ---- Karst_01: tall sentinel tower with side buttresses, notched all round
    I = Island("Karst_01", SEED + 1, 1.3 * vm, weight=1.0)
    I.tower(0, 0, 120, 100, 300, rot=0.6, n=2.6, taper=0.04, knobs=5)
    I.tower(70, 55, 70, 60, 220, knobs=2)
    I.tower(-75, -35, 60, 50, 150, knobs=2)
    I.apron(40, 90, 130, 80, 45)
    I.spire(-130, 40, 42, 205, lean=(-0.12, 0.05))
    I.ledges = [(120, 16, 18, 70, 0.0)]
    I.notch = 4.5
    isl.append(I)
    # ---- Karst_02: long multi-peak island with beach cove
    I = Island("Karst_02", SEED + 2, 1.45 * vm, weight=0.95)
    I.tower(-230, 0, 95, 80, 245, rot=0.1, knobs=3)
    I.tower(-90, 25, 90, 85, 205, knobs=2)
    I.tower(55, -10, 100, 90, 270, knobs=4)
    I.tower(205, 15, 85, 75, 170, knobs=2)
    I.tower(300, -5, 55, 50, 120, knobs=1)
    I.spire(360, 40, 30, 135, lean=(0.09, 0.03))
    I.apron(-20, 70, 260, 70, 45, rot=0.05)
    I.beach(-150, -105, 150, 40, 0.05)
    I.ledges = [(80, 22, 24, 100, 0.1), (160, 16, 18, 90, -0.05)]
    I.notch = 3.8
    isl.append(I)
    # ---- Karst_03: dome cluster with vegetated slopes to the water
    I = Island("Karst_03", SEED + 3, 1.3 * vm, weight=0.85)
    I.tower(-50, -20, 115, 95, 225, capf=0.5, capp=1.7, knobs=4)
    I.k_tower = 26.0
    I.tower(80, 30, 90, 80, 185, knobs=3)
    I.tower(-10, 95, 75, 65, 150, knobs=2)
    I.apron(0, 0, 190, 160, 60)
    I.ledges = [(95, 20, 22, 80, 0.05)]
    I.notch = 3.0
    isl.append(I)
    # ---- Karst_04: small double stack (sea pillars joined at the base)
    I = Island("Karst_04", SEED + 4, 1.05 * vm, weight=0.8)
    I.tower(-30, 0, 60, 50, 160, rot=0.3, n=2.6, taper=0.05, knobs=3)
    I.spire(52, 12, 42, 128, lean=(0.11, 0.02), knobs=1)
    I.ledges = [(70, 12, 14, 45, 0.0)]
    I.notch = 4.0
    isl.append(I)
    # ---- Karst_05: jagged mid island with pinnacles and a small beach
    I = Island("Karst_05", SEED + 5, 1.35 * vm, weight=0.9)
    I.tower(-110, 0, 105, 90, 285, knobs=6)
    I.tower(40, 30, 95, 80, 235, knobs=4)
    I.tower(160, -20, 70, 60, 175, knobs=3)
    I.tower(-20, -70, 60, 50, 140, knobs=2)
    I.spire(250, 10, 40, 190, lean=(0.10, -0.04))
    I.spire(-210, -40, 34, 150, lean=(-0.08, -0.06))
    I.apron(-60, 70, 220, 90, 55, rot=0.1)
    I.beach(60, -120, 110, 30, -0.15)
    I.ledges = [(90, 22, 24, 80, 0.05), (175, 16, 18, 70, 0.0)]
    I.notch = 3.5
    isl.append(I)
    # ---- ridges: long, low, layered far ranges
    for ri, (L, seed_off) in enumerate(((2400.0, 10), (1800.0, 11))):
        I = Island("Karst_Ridge_%d" % ri, SEED + seed_off, 3.0 * vm, weight=0.32, ridge=True)
        r = I.rng
        x = -L / 2
        while x < L / 2:
            a = r.uniform(70, 150); H = r.uniform(70, 125)
            I.tower(x, r.uniform(-30, 30), a, a * r.uniform(0.6, 0.9), H, capf=r.uniform(0.45, 0.65),
                    capp=r.uniform(1.7, 2.2), knobs=int(r.integers(1, 3)))
            x += a * r.uniform(1.1, 1.6)
        x = -L / 2 + 100
        while x < L / 2 - 100:
            a = r.uniform(90, 180); H = r.uniform(120, 195)
            I.tower(x, r.uniform(130, 220), a, a * r.uniform(0.6, 0.9), H, capf=r.uniform(0.45, 0.65),
                    capp=r.uniform(1.7, 2.2), knobs=int(r.integers(1, 3)))
            x += a * r.uniform(1.2, 1.7)
        I.k_tower = 30.0
        I.ledges = [(55, 10, 10, 150, 0.0)]
        I.notch = 2.5
        I.detail_scale = 1.6
        isl.append(I)
    return isl


# ----------------------------------------------------------------------------------------------
# SDF -> mesh
# ----------------------------------------------------------------------------------------------
def build_high(I, slab=20):
    h = I.voxel
    x0, x1, y0, y1, z0, z1 = I.bounds()
    nx, ny, nz = int((x1 - x0) / h) + 1, int((y1 - y0) / h) + 1, int((z1 - z0) / h) + 1
    xs = (x0 + np.arange(nx) * h).astype(np.float32)
    ys = (y0 + np.arange(ny) * h).astype(np.float32)
    zs = (z0 + np.arange(nz) * h).astype(np.float32)
    X = xs[:, None, None]; Y = ys[None, :, None]
    P = I.precompute(X, Y)
    B = 3.0 * h
    band = 22.0 * I.detail_scale
    grid = vdb.FloatGrid(B)
    nband = 0
    for k0 in range(0, nz, slab):
        k1 = min(nz, k0 + slab)
        ka, kb = max(0, k0 - 1), min(nz, k1 + 1)
        Z = zs[ka:kb][None, None, :]
        f, _, _, _ = I.base(P, Z)
        gx, gy, gz = np.gradient(f, h)
        sl = slice(k0 - ka, k0 - ka + (k1 - k0))
        f = f[:, :, sl]; gx = gx[:, :, sl]; gy = gy[:, :, sl]; gz = gz[:, :, sl]
        gl = np.sqrt(gx * gx + gy * gy + gz * gz) + 1e-6
        fn = f / np.clip(gl, 0.35, 1.6)
        out = np.where(fn > 0, B, -B).astype(np.float32)
        m = (fn > -band * 0.55) & (fn < band * 0.8)
        if m.any():
            ii, jj, kk = np.nonzero(m)
            px = xs[ii]; py = ys[jj]; pz = zs[k0 + kk]
            g = gl[m]
            d = I.detail(px, py, pz, gx[m] / g, gy[m] / g, gz[m] / g)
            v = fn[m] - d
            v = np.maximum(v, -8.0 - pz + 1.0)
            out[m] = np.clip(v, -B, B)
            nband += m.sum()
        grid.copyFromArray(np.ascontiguousarray(out), ijk=(0, 0, k0), tolerance=0.0)
    grid.prune(0.0)
    pts, tris, quads = grid.convertToPolygons(isovalue=0.0, adaptivity=0.0)
    V = (pts.astype(np.float64) * h + np.array([x0, y0, z0])).astype(np.float32)
    quads = np.asarray(quads, np.int64)
    V, quads, ndrop = keep_main_components(V, quads)
    if ndrop:
        log("%s: dropped %d small disconnected pieces" % (I.name, ndrop))
    log("%s: grid %dx%dx%d h=%.2f band pts %.1fM -> %d verts %d quads %d tris" %
        (I.name, nx, ny, nz, h, nband / 1e6, len(V), len(quads), len(tris)))
    return V, np.asarray(quads, np.int32), np.zeros((0, 3), np.int32)


def keep_main_components(V, Q, min_frac=0.02):
    n = len(V)
    e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]]])
    lab = np.arange(n)
    for _ in range(5000):
        m = np.minimum(lab[e[:, 0]], lab[e[:, 1]])
        old = lab.copy()
        np.minimum.at(lab, e[:, 0], m)
        np.minimum.at(lab, e[:, 1], m)
        lab = lab[lab]
        if (lab == old).all():
            break
    u, c = np.unique(lab, return_counts=True)
    keep_l = u[c >= min_frac * n]
    keepv = np.isin(lab, keep_l)
    keepq = keepv[Q[:, 0]]
    remap = np.cumsum(keepv) - 1
    return V[keepv], remap[Q[keepq]].astype(np.int32), len(u) - len(keep_l)


def mesh_from_np(name, V, quads, tris):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    loops = np.concatenate([quads.ravel(), tris.ravel()]).astype(np.int32)
    nq, nt = len(quads), len(tris)
    me.loops.add(len(loops))
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(nq + nt)
    starts = np.concatenate([np.arange(nq) * 4, nq * 4 + np.arange(nt) * 3]).astype(np.int32)
    me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    return me


def link_obj(name, me, coll=None):
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


# ----------------------------------------------------------------------------------------------
# albedo + masks on the high-res vertices
# ----------------------------------------------------------------------------------------------
def srgb2lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


PAL = {k: srgb2lin(v) for k, v in {
    "cream": (0.89, 0.83, 0.71), "grey": (0.74, 0.72, 0.67), "warm": (0.91, 0.79, 0.61),
    "ochre": (0.80, 0.55, 0.28), "orange": (0.83, 0.48, 0.22), "dark": (0.33, 0.32, 0.30),
    "black": (0.13, 0.13, 0.12), "wet": (0.20, 0.19, 0.17), "sand": (0.92, 0.88, 0.77),
    "g0": (0.22, 0.38, 0.15), "g1": (0.30, 0.46, 0.18), "g2": (0.18, 0.32, 0.14), "g3": (0.38, 0.52, 0.21),
    "g4": (0.26, 0.42, 0.21), "crev": (0.09, 0.17, 0.08)}.items()}


def mix(a, b, t):
    t = np.asarray(t, np.float32)[..., None]
    return a * (1 - t) + b * t


def vertex_albedo(I, V, Nrm):
    """Returns (rgb linear Nx3, mask Nx4: R=veg, G=sand, B=rockStreak, A=1)."""
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    nb = I.nb
    # smooth base normal from the analytic base field
    e = 2.5
    P = I.precompute(x, y)
    f0 = I.base(P, z)[0]
    Pxp = I.precompute(x + e, y); Pxm = I.precompute(x - e, y)
    Pyp = I.precompute(x, y + e); Pym = I.precompute(x, y - e)
    gx = (I.base(Pxp, z)[0] - I.base(Pxm, z)[0])
    gy = (I.base(Pyp, z)[0] - I.base(Pym, z)[0])
    gz = (I.base(P, z + e)[0] - I.base(P, z - e)[0])
    gl = np.sqrt(gx * gx + gy * gy + gz * gz) + 1e-6
    bnz = gz / gl
    _, ft, fa, fb = I.base(P, z)
    S = I.detail_scale
    veg = I.jungle(x, y, z, bnz)
    # the true (detailed) normal also feeds vegetation: flat spots on the fine surface get shrubs
    fnz = Nrm[:, 2]
    veg = np.clip(np.maximum(veg, sstep(0.75, 0.92, fnz) * sstep(6.0, 12.0, z) * 0.9), 0, 1)
    # sand on beaches
    sand = np.zeros_like(z)
    if fb is not None:
        others = ft if fa is None else np.minimum(ft, fa)
        sand = sstep(1.5, -1.0, fb - others + 0.0) * sstep(4.2, 2.6, z)
        sand = np.maximum(sand, sstep(3.5, 1.0, fb) * sstep(4.0, 2.8, z) * (fb < others + 3))
        veg = veg * (1 - sand)
    # ---- rock colour
    lv = nb.fbm("rockcol", x, y, z, 40.0, 3, sz=2.0)
    rock = mix(PAL["cream"], PAL["grey"], sstep(-0.3, 0.5, lv))
    rock = mix(rock, PAL["warm"], sstep(0.1, 0.6, nb.fbm("rockwarm", x, y, z, 70.0, 2, sz=1.5)) * 0.45)
    # streaks below vegetation: distance to the next vegetated point above (3D column grid)
    below = veg_above_distance(V, veg > 0.5, cell=4.0)
    run = np.exp(-below / 55.0) * (below < 120)
    sv = nb.fbm("streakA", x, y, z, 5.0, 2, sz=9.0)
    sv2 = nb.fbm("streakB", x, y, z, 7.0, 2, sz=8.0)
    sw = nb.fbm("streakC", x, y, z, 14.0, 2, sz=6.0)
    dark = np.clip(sstep(-0.05, 0.4, sv) * (0.45 + 0.9 * run) + sstep(0.25, 0.6, sw) * 0.45, 0, 1)
    ochm = sstep(-0.1, 0.35, nb.fbm("ochmask", x, y, z, 70.0, 2, sz=1.5))
    ochre = np.clip(sstep(-0.1, 0.4, sv2) * (0.2 + 0.8 * ochm) + 0.35 * ochm, 0, 1)
    rock = mix(rock, PAL["ochre"], ochre * 0.75)
    # overhang undersides = fresh orange rock
    over = sstep(-0.1, -0.45, fnz) * sstep(3.0, 8.0, z)
    rock = mix(rock, PAL["orange"], over * 0.7)
    rock = mix(rock, PAL["dark"], dark * 0.85)
    rock = mix(rock, PAL["black"], sstep(0.45, 0.85, dark * run) * 0.75)
    # black streaks running down from overhangs
    below_o = veg_above_distance(V, over > 0.4, cell=4.0)
    blk = np.exp(-below_o / 35.0) * (below_o < 90) * sstep(-0.1, 0.35, sv)
    rock = mix(rock, PAL["black"], np.clip(blk, 0, 1) * 0.8)
    # dark wet band in the tidal notch
    rock = mix(rock, PAL["wet"], sstep(4.8, 1.2, z))
    # ---- vegetation colour: per-crown tone + darker crevices
    c1 = np.zeros_like(z); id1 = np.zeros_like(z); c2 = np.zeros_like(z); id2 = np.zeros_like(z)
    vi = np.nonzero(veg > 0.005)[0]
    if len(vi):
        c1[vi], id1[vi] = nb.crowns("crownA", x[vi], y[vi], z[vi], 10.0 * S, flat=0.3)
        c2[vi], id2[vi] = nb.crowns("crownB", x[vi], y[vi], z[vi], 4.5 * S, flat=0.3)
    tones = np.stack([PAL["g0"], PAL["g1"], PAL["g2"], PAL["g3"], PAL["g4"]])
    ti = np.minimum((id1 * 5).astype(np.int32), 4)
    green = tones[ti]
    green = mix(green, tones[np.minimum((id2 * 5).astype(np.int32), 4)], 0.35)
    green = mix(green, PAL["g3"], sstep(0.2, 0.7, nb.fbm("vegsun", x, y, z, 60.0, 2)) * 0.35)
    crev = 1.0 - np.clip(0.65 * c1 + 0.45 * c2, 0, 1)
    green = mix(green, PAL["crev"], sstep(0.35, 0.95, crev) * 0.75)
    col = mix(rock, green, veg)
    col = mix(col, PAL["sand"], sand)
    mask = np.stack([veg, sand, np.clip(dark, 0, 1), np.ones_like(z)], 1).astype(np.float32)
    return col.astype(np.float32), mask


def veg_above_distance(V, vegmask, cell=4.0):
    """For every vertex: vertical distance (m) to the nearest vegetated vertex above it, searching a
    horizontally dilated (±1 cell) column. Large if none."""
    lo = V.min(0)
    idx = np.floor((V - lo) / cell).astype(np.int32)
    dims = idx.max(0) + 3
    occ = np.zeros(dims, np.bool_)
    vi = idx[vegmask] + 1
    occ[vi[:, 0], vi[:, 1], vi[:, 2]] = True
    # horizontal dilation
    d = occ.copy()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            d |= np.roll(np.roll(occ, dx, 0), dy, 1)
    nzc = dims[2]
    INF = 10000
    dist = np.full(dims, INF, np.int32)
    run = np.full(dims[:2], INF, np.int32)
    for k in range(nzc - 1, -1, -1):
        run = np.where(d[:, :, k], 0, np.minimum(run + 1, INF))
        dist[:, :, k] = run
    i = idx + 1
    out = dist[i[:, 0], i[:, 1], i[:, 2]].astype(np.float32) * cell
    return out


def set_color_attr(me, name, arr):
    a = me.color_attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")
    rgba = np.ones((len(arr), 4), np.float32)
    rgba[:, :arr.shape[1]] = arr[:, :4]
    a.data.foreach_set("color", rgba.ravel())


# ----------------------------------------------------------------------------------------------
# scene helpers
# ----------------------------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    return sc


def setup_cycles(sc, samples=16):
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.refresh_devices()
    ok = False
    for d in prefs.devices:
        d.use = d.type == "METAL"
        ok |= d.use
    sc.cycles.device = "GPU" if ok else "CPU"
    sc.cycles.samples = samples
    sc.cycles.seed = 7
    log("cycles device:", sc.cycles.device, [d.name for d in prefs.devices if d.use])


def sky_world(sc, sun_el_deg=40.0, sun_az_deg=215.0, strength=1.0):
    w = bpy.data.worlds.new("Sky")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    items = [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items]
    for cand in ("NISHITA", "SINGLE_SCATTERING", "MULTIPLE_SCATTERING"):
        if cand in items:
            sky.sky_type = cand
            break
    sky.sun_elevation = math.radians(sun_el_deg)
    sky.sun_rotation = math.radians(sun_az_deg)
    for attr, val in (("altitude", 2.0), ("air_density", 1.0), ("dust_density", 0.6), ("ozone_density", 1.0),
                      ("sun_size", math.radians(0.545)), ("sun_intensity", 1.0)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    log("sky type", sky.sky_type)
    return sky


def haze_mix(nt, surf_out, sky_ref, dist_L=9000.0, max_haze=0.9):
    """Aerial perspective in the material: mix towards the sky radiance in the view direction."""
    N = nt.nodes
    geo = N.new("ShaderNodeNewGeometry")
    neg = N.new("ShaderNodeVectorMath"); neg.operation = "SCALE"; neg.inputs[3].default_value = -1.0
    nt.links.new(geo.outputs["Incoming"], neg.inputs[0])
    sky = N.new("ShaderNodeTexSky")
    for p in ("sky_type", "sun_elevation", "sun_rotation", "altitude", "air_density", "dust_density",
              "ozone_density", "sun_size", "sun_intensity", "sun_disc"):
        if hasattr(sky_ref, p):
            try:
                setattr(sky, p, getattr(sky_ref, p))
            except Exception:
                pass
    if hasattr(sky, "sun_disc"):
        sky.sun_disc = False
    nt.links.new(neg.outputs[0], sky.inputs["Vector"])
    em = N.new("ShaderNodeEmission")
    nt.links.new(sky.outputs[0], em.inputs[0])
    cam = N.new("ShaderNodeCameraData")
    m1 = N.new("ShaderNodeMath"); m1.operation = "DIVIDE"; m1.inputs[1].default_value = -dist_L
    nt.links.new(cam.outputs["View Distance"], m1.inputs[0])
    m2 = N.new("ShaderNodeMath"); m2.operation = "EXPONENT"
    nt.links.new(m1.outputs[0], m2.inputs[0])
    m3 = N.new("ShaderNodeMath"); m3.operation = "SUBTRACT"; m3.inputs[0].default_value = 1.0
    nt.links.new(m2.outputs[0], m3.inputs[1])
    m4 = N.new("ShaderNodeMath"); m4.operation = "MULTIPLY"; m4.inputs[1].default_value = max_haze
    nt.links.new(m3.outputs[0], m4.inputs[0])
    mx = N.new("ShaderNodeMixShader")
    nt.links.new(m4.outputs[0], mx.inputs[0])
    nt.links.new(surf_out, mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    return mx.outputs[0]


def sea_plane(sc, sky_ref, size=60000.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = "Sea"
    m = bpy.data.materials.new("Sea")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.0, 0.16, 0.20, 1)
    bs.inputs["Roughness"].default_value = 0.09
    bs.inputs["IOR"].default_value = 1.333
    # gentle wave normals
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.25, 0.6, 0.25)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0
    nz.inputs["Detail"].default_value = 6
    nt.links.new(mp.outputs[0], nz.inputs[0])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.2
    nt.links.new(nz.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], bs.inputs["Normal"])
    out = nt.nodes["Material Output"]
    hz = haze_mix(nt, bs.outputs[0], sky_ref, dist_L=14000.0, max_haze=0.8)
    nt.links.new(hz, out.inputs[0])
    ob.data.materials.append(m)
    return ob


def camera(sc, loc, look_at, fov_deg, name="Cam", res=(1600, 900)):
    cd = bpy.data.cameras.new(name)
    cd.lens_unit = "FOV"
    cd.sensor_fit = "HORIZONTAL"
    cd.angle = math.radians(fov_deg)
    cd.clip_start = 1.0
    cd.clip_end = 100000.0
    ob = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(ob)
    ob.location = loc
    from mathutils import Vector
    d = Vector(look_at) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = ob
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    return ob


def color_mgmt(sc, exposure=0.0):
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except Exception:
        pass
    sc.view_settings.exposure = exposure


def render_to(sc, path):
    sc.render.image_settings.file_format = "JPEG" if path.endswith(".jpg") else "PNG"
    if path.endswith(".jpg"):
        sc.render.image_settings.quality = 90
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    log("rendered", os.path.basename(path), "%.1fs" % (time.time() - t))
    return time.time() - t


# preview layout (Blender metres, camera at origin looking +Y): name -> (x, y, rotZ)
LAYOUT = {
    "Karst_00": (-420.0, 1500.0, 0.25),
    "Karst_01": (260.0, 1180.0, 0.9),
    "Karst_02": (780.0, 2150.0, -0.15),
    "Karst_03": (-1150.0, 2400.0, 0.5),
    "Karst_04": (-40.0, 850.0, 0.3),
    "Karst_05": (40.0, 2500.0, 2.6),
    "Karst_Ridge_0": (-600.0, 4300.0, 0.08),
    "Karst_Ridge_1": (1300.0, 3700.0, -0.12),
}


# ----------------------------------------------------------------------------------------------
# dev stage: highs with vertex colours rendered directly (fast iteration on shapes + colours)
# ----------------------------------------------------------------------------------------------
def stage_dev(args):
    sc = reset_scene()
    setup_cycles(sc, 24)
    sky = sky_world(sc)
    sea_plane(sc, sky)
    color_mgmt(sc, args.exposure)
    isl = make_islands(fast=args.fast)
    only = [s for s in args.only.split(",") if s]
    mat = bpy.data.materials.new("vc")
    mat.use_nodes = True
    nt = mat.node_tree
    bs = nt.nodes["Principled BSDF"]
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "Col"
    nt.links.new(at.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.85
    hz = haze_mix(nt, bs.outputs[0], sky)
    nt.links.new(hz, nt.nodes["Material Output"].inputs[0])
    for I in isl:
        if only and I.name not in only:
            continue
        V, Q, T = build_high(I)
        me = mesh_from_np(I.name, V, Q, T)
        me.shade_smooth()
        Nrm = np.empty(len(V) * 3, np.float32)
        me.vertex_normals.foreach_get("vector", Nrm)
        col, mask = vertex_albedo(I, V, Nrm.reshape(-1, 3))
        set_color_attr(me, "Col", col)
        ob = link_obj(I.name, me)
        ob.data.materials.append(mat)
        x, y, r = LAYOUT[I.name]
        ob.location = (x, y, 0)
        ob.rotation_euler = (0, 0, r)
    os.makedirs(args.scratch, exist_ok=True)
    res = tuple(int(v) for v in args.res.split("x"))
    camera(sc, (0, 0, 2.0), (0, 1500, 120), 40.0, res=res)
    render_to(sc, os.path.join(args.scratch, "dev_wide.jpg"))
    camera(sc, (0, 0, 2.0), (LAYOUT["Karst_00"][0], LAYOUT["Karst_00"][1], 170), 15.0, name="CamTele", res=res)
    render_to(sc, os.path.join(args.scratch, "dev_tele.jpg"))




# ==============================================================================================
# production stages (resumable: every stage skips when its output already exists)
# ==============================================================================================
TRI_TARGET = {"Karst_00": 5800, "Karst_01": 5000, "Karst_02": 5600, "Karst_03": 4600, "Karst_04": 3000,
              "Karst_05": 5400, "Karst_Ridge_0": 3800, "Karst_Ridge_1": 3800}
OUT = {"fbx": os.path.join(HERE, "KarstIslands.fbx"), "albedo": os.path.join(HERE, "Karst_Albedo.png"),
       "normal": os.path.join(HERE, "Karst_Normal.png"), "stats": os.path.join(HERE, "stats.json")}


def scr(args, name):
    return os.path.join(args.scratch, name)


def save_npz(path, **kw):
    tmp = path + ".tmp.npz"
    np.savez(tmp, **kw)
    os.replace(tmp, path)


# ---------------- stage 1: high-res source per island --------------------------------------------
def stage_high(args, I):
    path = scr(args, "high_%s.npz" % I.name)
    if os.path.exists(path):
        return
    t = time.time()
    V, Q, _ = build_high(I)
    me = mesh_from_np(I.name + "_hi", V, Q, np.zeros((0, 3), np.int32))
    Nrm = np.empty(len(V) * 3, np.float32)
    me.vertex_normals.foreach_get("vector", Nrm)
    bpy.data.meshes.remove(me)
    col = np.zeros((len(V), 3), np.float32)
    mask = np.zeros((len(V), 4), np.float32)
    col, mask = vertex_albedo(I, V, Nrm.reshape(-1, 3))
    save_npz(path, V=V, Q=Q, col=col.astype(np.float16), mask=mask.astype(np.float16))
    log("%s: high saved (%d tris) %.1fs" % (I.name, len(Q) * 2, time.time() - t))


def load_high(args, name):
    d = np.load(scr(args, "high_%s.npz" % name))
    return d["V"], d["Q"], d["col"].astype(np.float32), d["mask"].astype(np.float32)


# ---------------- stage 2: decimated game mesh ---------------------------------------------------
def bm_to_np(bm):
    bm.verts.index_update()
    V = np.array([v.co[:] for v in bm.verts], np.float32)
    F = np.array([[v.index for v in f.verts] for f in bm.faces], np.int32)
    return V, F


def stage_low(args, I):
    path = scr(args, "low_%s.npz" % I.name)
    if os.path.exists(path):
        return
    t = time.time()
    reset_scene()
    V, Q, _, _ = load_high(args, I.name)
    me = mesh_from_np(I.name + "_hi", V, Q, np.zeros((0, 3), np.int32))
    ob = link_obj(I.name + "_hi", me)
    target = TRI_TARGET[I.name]
    ratio = target * 1.05 / (2.0 * len(Q))
    best = None
    for it in range(5):
        mod = ob.modifiers.new("dec", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        dg = bpy.context.evaluated_depsgraph_get()
        mlo = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.remove(mod)
        bm = bmesh.new()
        bm.from_mesh(mlo)
        bpy.data.meshes.remove(mlo)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, -5.0), plane_no=(0, 0, 1), clear_inner=True)
        bmesh.ops.dissolve_degenerate(bm, dist=0.02, edges=bm.edges[:])
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        n = len(bm.faces)
        Vl, Fl = bm_to_np(bm)
        bm.free()
        best = (Vl, Fl)
        log("%s: decimate ratio %.5f -> %d tris (target %d)" % (I.name, ratio, n, target))
        if abs(n - target) <= 0.04 * target:
            break
        ratio *= target / max(n, 1)
    Vl, Fl = best
    Vl[:, 2] = np.maximum(Vl[:, 2], -5.0)
    # deviation high -> low (for the bake cage and the report)
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromPolygons([tuple(v) for v in Vl], [tuple(f) for f in Fl])
    rng = np.random.default_rng(1)
    sel = rng.choice(len(V), min(40000, len(V)), replace=False)
    dev = []
    for i in sel:
        if V[i, 2] < -4.0:
            continue
        hit = bvh.find_nearest(tuple(V[i]))
        if hit[0] is not None:
            dev.append(hit[3])
    dev = np.array(dev)
    stats = {"mean": float(dev.mean()), "p95": float(np.percentile(dev, 95)), "p99": float(np.percentile(dev, 99)),
             "max": float(dev.max())}
    save_npz(path, V=Vl, F=Fl, dev=np.array([stats["mean"], stats["p95"], stats["p99"], stats["max"]]))
    log("%s: low %d tris, deviation high->low mean %.2f p95 %.2f p99 %.2f max %.2f m (%.1fs)" %
        (I.name, len(Fl), stats["mean"], stats["p95"], stats["p99"], stats["max"], time.time() - t))


# ---------------- stage 3: shared atlas UVs ------------------------------------------------------
def make_low_obj(name, V, F, UV=None):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", (np.arange(len(F)) * 3).astype(np.int32))
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    if UV is not None:
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", UV.reshape(-1).astype(np.float32))
    me.shade_smooth()
    return link_obj(name, me)


def get_uv(me):
    a = np.empty(len(me.loops) * 2, np.float32)
    me.uv_layers.active.data.foreach_get("uv", a)
    return a.reshape(-1, 3, 2)


def tri_areas3(V, F):
    p = V[F]
    return 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)


def tri_areas2(T):
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]
    return 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])


def stage_uv(args, islands):
    """Each object gets one 1024x1024 slot of the 4096x2048 atlas (4 x 2 slots, 8 objects); inside its slot
    its own smart-projected islands are packed by Blender (pack within the 0..1 tile, then mapped into the
    slot). No cross-object packing (the multi-object packer misbehaves headless in 5.2)."""
    path = scr(args, "uv.npz")
    if os.path.exists(path):
        return
    reset_scene()
    out = {}
    for k, I in enumerate(islands):
        d = np.load(scr(args, "low_%s.npz" % I.name))
        ob = make_low_obj(I.name, d["V"], d["F"])
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(64), island_margin=0.012, area_weight=0.0,
                                 correct_aspect=False, scale_to_bounds=True)
        bpy.ops.uv.select_all(action="SELECT")
        kw = dict(udim_source="CLOSEST_UDIM", rotate=True, scale=True, merge_overlap=False,
                  margin_method="FRACTION", margin=0.004, shape_method="CONCAVE")
        try:
            bpy.ops.uv.pack_islands(**kw)
        except TypeError:
            kw.pop("shape_method"); bpy.ops.uv.pack_islands(**kw)
        bpy.ops.object.mode_set(mode="OBJECT")
        UV = get_uv(ob.data).astype(np.float64)
        lo, hi = UV.reshape(-1, 2).min(0), UV.reshape(-1, 2).max(0)
        UV = (UV - lo) / max((hi - lo).max(), 1e-9)                 # fill the slot, keep aspect
        col, row = k % 4, k // 4
        pad = 8.0 / 1024
        UV = UV * (1 - 2 * pad) + pad
        UV[..., 0] = (UV[..., 0] + col) / 4.0
        UV[..., 1] = (UV[..., 1] + row) / 2.0
        V, F = d["V"], d["F"]
        out[I.name + "__V"] = V; out[I.name + "__F"] = F; out[I.name + "__UV"] = UV.astype(np.float32)
        px = UV.copy(); px[..., 0] *= ATLAS_W; px[..., 1] *= ATLAS_H
        dens = math.sqrt(tri_areas2(px).sum() / tri_areas3(V, F).sum())
        log("%s: slot (%d,%d) UV u[%.4f,%.4f] v[%.4f,%.4f] texel density %.3f px/m" %
            (I.name, col, row, UV[..., 0].min(), UV[..., 0].max(), UV[..., 1].min(), UV[..., 1].max(), dens))
        bpy.data.objects.remove(ob)
    save_npz(path, **out)


def raster_coverage(islands, uvd):
    """objid map (H,W) int8 (-1 empty) from UV triangles (texel centres), plus overlap count."""
    obj = np.full((ATLAS_H, ATLAS_W), -1, np.int8)
    cnt = np.zeros((ATLAS_H, ATLAS_W), np.uint8)
    for oi, I in enumerate(islands):
        UV = uvd[I.name + "__UV"].astype(np.float64)
        P = UV * np.array([ATLAS_W, ATLAS_H]) - 0.5
        for t in P:
            x0 = max(int(np.floor(t[:, 0].min())), 0); x1 = min(int(np.ceil(t[:, 0].max())), ATLAS_W - 1)
            y0 = max(int(np.floor(t[:, 1].min())), 0); y1 = min(int(np.ceil(t[:, 1].max())), ATLAS_H - 1)
            if x1 < x0 or y1 < y0:
                continue
            xs = np.arange(x0, x1 + 1); ys = np.arange(y0, y1 + 1)
            X, Y = np.meshgrid(xs, ys)
            (ax, ay), (bx, by), (cx, cy) = t
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-12:
                continue
            l1 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
            l2 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
            l3 = 1 - l1 - l2
            ins = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
            if ins.any():
                yy, xx = Y[ins], X[ins]
                cnt[yy, xx] += 1
                obj[yy, xx] = oi
    return obj, cnt


# ---------------- stage 4: Cycles bakes per island -----------------------------------------------
def high_bake_material():
    m = bpy.data.materials.new("HiBake")
    m.use_nodes = True
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    col = N.new("ShaderNodeAttribute"); col.attribute_name = "Col"
    msk = N.new("ShaderNodeAttribute"); msk.attribute_name = "Mask"
    sep = N.new("ShaderNodeSeparateColor"); Lk.new(msk.outputs["Color"], sep.inputs[0])
    tc = N.new("ShaderNodeTexCoord")
    # fine rock streaks (vertical) and leaf speckle, object space metres
    mpr = N.new("ShaderNodeMapping"); mpr.inputs["Scale"].default_value = (1 / 1.7, 1 / 1.7, 1 / 16.0)
    Lk.new(tc.outputs["Object"], mpr.inputs[0])
    nr = N.new("ShaderNodeTexNoise"); nr.inputs["Scale"].default_value = 1.0; nr.inputs["Detail"].default_value = 4
    Lk.new(mpr.outputs[0], nr.inputs["Vector"])
    mpv = N.new("ShaderNodeMapping"); mpv.inputs["Scale"].default_value = (1 / 1.3, 1 / 1.3, 1 / 1.3)
    Lk.new(tc.outputs["Object"], mpv.inputs[0])
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1.0
    Lk.new(mpv.outputs[0], vor.inputs["Vector"])
    # factor: rock -> 0.80..1.10 ; veg -> 0.72..1.12 (darker gaps between leaf clumps)
    rr = N.new("ShaderNodeMapRange"); rr.inputs[1].default_value = 0.3; rr.inputs[2].default_value = 0.7
    rr.inputs[3].default_value = 0.80; rr.inputs[4].default_value = 1.10
    Lk.new(nr.outputs["Fac"], rr.inputs[0])
    vr = N.new("ShaderNodeMapRange"); vr.inputs[1].default_value = 0.0; vr.inputs[2].default_value = 0.6
    vr.inputs[3].default_value = 1.12; vr.inputs[4].default_value = 0.72
    Lk.new(vor.outputs["Distance"], vr.inputs[0])
    mixf = N.new("ShaderNodeMix"); mixf.data_type = "FLOAT"
    Lk.new(sep.outputs[0], mixf.inputs["Factor"])
    Lk.new(rr.outputs[0], mixf.inputs["A"]); Lk.new(vr.outputs[0], mixf.inputs["B"])
    mul = N.new("ShaderNodeVectorMath"); mul.operation = "SCALE"
    Lk.new(col.outputs["Color"], mul.inputs[0]); Lk.new(mixf.outputs["Result"], mul.inputs["Scale"])
    em_alb = N.new("ShaderNodeEmission"); Lk.new(mul.outputs[0], em_alb.inputs["Color"])
    ao = N.new("ShaderNodeAmbientOcclusion"); ao.only_local = True; ao.samples = 16
    ao.inputs["Distance"].default_value = 30.0
    em_ao = N.new("ShaderNodeEmission"); Lk.new(ao.outputs["AO"], em_ao.inputs["Color"])
    # bump for the normal pass: rock streaks + leaf clumps
    hb = N.new("ShaderNodeMix"); hb.data_type = "FLOAT"
    Lk.new(sep.outputs[0], hb.inputs["Factor"])
    Lk.new(nr.outputs["Fac"], hb.inputs["A"])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    Lk.new(vor.outputs["Distance"], inv.inputs[1]); Lk.new(inv.outputs[0], hb.inputs["B"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.6
    Lk.new(hb.outputs["Result"], bump.inputs["Height"])
    dif = N.new("ShaderNodeBsdfDiffuse"); Lk.new(bump.outputs[0], dif.inputs["Normal"])
    return m, out, {"albedo": em_alb, "ao": em_ao, "normal": dif}


def stage_bake(args, I, uvd, objid):
    path = scr(args, "bake_%s.npz" % I.name)
    if os.path.exists(path):
        return
    t0 = time.time()
    sc = reset_scene()
    setup_cycles(sc, 1)
    sc.cycles.use_denoising = False
    V, Q, col, mask = load_high(args, I.name)
    me = mesh_from_np(I.name + "_hi", V, Q, np.zeros((0, 3), np.int32))
    me.shade_smooth()
    set_color_attr(me, "Col", col)
    set_color_attr(me, "Mask", mask)
    hi = link_obj(I.name + "_hi", me)
    hm, hout, shaders = high_bake_material()
    me.materials.append(hm)
    lo = make_low_obj(I.name, uvd[I.name + "__V"], uvd[I.name + "__F"], uvd[I.name + "__UV"])
    img = bpy.data.images.new("bake", ATLAS_W, ATLAS_H, alpha=True, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    lm = bpy.data.materials.new("LoBake")
    lm.use_nodes = True
    tn = lm.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img
    lm.node_tree.nodes.active = tn
    lo.data.materials.append(lm)
    bpy.ops.object.select_all(action="DESELECT")
    hi.select_set(True); lo.select_set(True)
    bpy.context.view_layer.objects.active = lo
    dev = np.load(scr(args, "low_%s.npz" % I.name))["dev"]
    ext = float(np.clip(dev[2] * 1.3 + 2.0, 6.0, 18.0))     # cage extrusion from the p99 deviation
    ray = ext * 3.0
    zeros = np.zeros(ATLAS_W * ATLAS_H * 4, np.float32)
    mine = np.flatnonzero((objid == list(OBJ_ORDER).index(I.name)).ravel())
    res = {"ext": np.array([ext, ray])}
    buf = np.empty(ATLAS_W * ATLAS_H * 4, np.float32)
    for pas, typ, smp in (("albedo", "EMIT", 1), ("ao", "EMIT", 24), ("normal", "NORMAL", 1)):
        img.pixels.foreach_set(zeros)
        hm.node_tree.links.new(shaders[pas].outputs[0], hout.inputs["Surface"])
        sc.cycles.samples = smp
        t = time.time()
        kw = dict(type=typ, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray, margin=0,
                  use_clear=False, target="IMAGE_TEXTURES")
        if typ == "NORMAL":
            kw.update(normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        bpy.ops.object.bake(**kw)
        img.pixels.foreach_get(buf)
        px = buf.reshape(-1, 4)
        hit = np.flatnonzero(px[:, 3] > 0.5)
        res[pas + "_idx"] = hit.astype(np.int32)
        res[pas + "_val"] = px[hit, :3].astype(np.float16)
        miss = np.setdiff1d(mine, hit, assume_unique=False).size
        log("%s: bake %-6s %.1fs  hit %d px, coverage %d px, unhit-in-coverage %d" %
            (I.name, pas, time.time() - t, len(hit), len(mine), miss))
    save_npz(path, **res)
    log("%s: bakes done %.1fs (cage %.1f m, ray %.1f m)" % (I.name, time.time() - t0, ext, ray))


OBJ_ORDER = ["Karst_00", "Karst_01", "Karst_02", "Karst_03", "Karst_04", "Karst_05", "Karst_Ridge_0", "Karst_Ridge_1"]


# ---------------- stage 5: compose, check, dilate, write PNGs ------------------------------------
def pushpull_fill(img, valid):
    """Fill invalid texels from valid neighbours (pyramid push-pull). img (H,W,C) float32."""
    levels = []
    cur, w = img * valid[..., None], valid.astype(np.float32)
    while min(cur.shape[0], cur.shape[1]) > 1:
        levels.append((cur, w))
        H, W = cur.shape[0] // 2, cur.shape[1] // 2
        c = cur[:H * 2, :W * 2].reshape(H, 2, W, 2, -1).sum((1, 3))
        ww = w[:H * 2, :W * 2].reshape(H, 2, W, 2).sum((1, 3))
        cur, w = c, ww
    filled = np.where(w[..., None] > 0, cur / np.maximum(w[..., None], 1e-8), 0)
    for c, ww in reversed(levels):
        up = np.repeat(np.repeat(filled, 2, 0), 2, 1)
        H, W = c.shape[:2]
        up = np.pad(up, ((0, max(0, H - up.shape[0])), (0, max(0, W - up.shape[1])), (0, 0)), mode="edge")[:H, :W]
        avg = np.where(ww[..., None] > 0, c / np.maximum(ww[..., None], 1e-8), 0)
        a = np.clip(ww, 0, 1)[..., None]
        filled = avg * a + up * (1 - a)
    return filled.astype(np.float32)


def dilate_extend(img, valid, iters=6):
    """A few rings of exact edge-texel extension before the smooth push-pull fill."""
    img = img.copy(); valid = valid.copy()
    for _ in range(iters):
        acc = np.zeros_like(img); n = np.zeros(valid.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sv = np.roll(np.roll(valid, dy, 0), dx, 1)
            si = np.roll(np.roll(img, dy, 0), dx, 1)
            acc += si * sv[..., None]; n += sv
        new = (~valid) & (n > 0)
        img[new] = acc[new] / n[new][:, None]
        valid = valid | new
    return img, valid


def write_png(path, arr):
    """arr (H,W,C) uint8, row 0 = TOP of the image. Minimal PNG writer (Sub filter + zlib)."""
    import zlib, struct
    H, W, C = arr.shape
    ctype = {3: 2, 4: 6}[C]
    a = arr.astype(np.int16)
    sub = a.copy()
    sub[:, 1:] = (a[:, 1:] - a[:, :-1]) % 256
    raw = np.concatenate([np.ones((H, 1), np.uint8), sub.astype(np.uint8).reshape(H, W * C)], 1)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, ctype, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw.tobytes(), 9)) + chunk(b"IEND", b"")
    with open(path + ".tmp", "wb") as f:
        f.write(data)
    os.replace(path + ".tmp", path)


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def stage_compose(args, islands, uvd, objid, overl):
    if os.path.exists(OUT["albedo"]) and os.path.exists(OUT["normal"]) and os.path.exists(scr(args, "checks.json")):
        return
    HW = ATLAS_H * ATLAS_W
    alb = np.zeros((HW, 3), np.float32); ao = np.zeros((HW, 1), np.float32); nor = np.zeros((HW, 3), np.float32)
    hit_a = np.zeros(HW, bool); hit_o = np.zeros(HW, bool); hit_n = np.zeros(HW, bool)
    for I in islands:
        d = np.load(scr(args, "bake_%s.npz" % I.name))
        oi = OBJ_ORDER.index(I.name)
        own = (objid.ravel() == oi)
        for key, dst, hm, ch in (("albedo", alb, hit_a, 3), ("ao", ao, hit_o, 1), ("normal", nor, hit_n, 3)):
            idx = d[key + "_idx"]; val = d[key + "_val"].astype(np.float32)
            keep = own[idx]          # only texels that belong to this object's UV triangles
            dst[idx[keep]] = val[keep, :ch]
            hm[idx[keep]] = True
    cov = objid.ravel() >= 0
    checks = {"coverage_px": int(cov.sum()), "uv_overlap_px": int((overl > 1).sum())}
    for nm, hm in (("albedo", hit_a), ("ao", hit_o), ("normal", hit_n)):
        checks["holes_" + nm] = int((cov & ~hm).sum())
    # hits whose values are suspicious
    nz = nor[hit_n, 2]
    checks["normal_backfacing_px"] = int((nz < 0.5).sum())        # encoded z < 0.5 => normal pointing inward
    checks["albedo_black_px_in_hits"] = int((alb[hit_a].max(1) < 0.01).sum())
    log("checks before fill:", checks)
    H, W = ATLAS_H, ATLAS_W
    out = {}
    for nm, arr, hm in (("albedo", alb, hit_a), ("ao", ao, hit_o), ("normal", nor, hit_n)):
        img = arr.reshape(H, W, -1); v = hm.reshape(H, W)
        img, v2 = dilate_extend(img, v, 8)
        img = np.where(v2[..., None], img, pushpull_fill(img, v2))
        out[nm] = img
    # renormalise tangent normals
    n = out["normal"] * 2 - 1
    n /= np.linalg.norm(n, axis=2, keepdims=True) + 1e-8
    out["normal"] = n * 0.5 + 0.5
    checks["after_fill_black_albedo_px"] = int((out["albedo"].max(2) < 0.01).sum())
    checks["after_fill_nan"] = int(sum(np.isnan(v).sum() for v in out.values()))
    rgba = np.concatenate([lin2srgb(out["albedo"]), np.clip(out["ao"], 0, 1)], 2)
    write_png(OUT["albedo"], np.round(rgba[::-1] * 255).astype(np.uint8))
    write_png(OUT["normal"], np.round(np.clip(out["normal"][::-1], 0, 1) * 255).astype(np.uint8))
    # seam check: mean abs difference across island borders in the final normal map (lower = cleaner)
    ao_cov = out["ao"][..., 0][objid >= 0]
    checks["ao_mean"] = float(ao_cov.mean()); checks["ao_p5"] = float(np.percentile(ao_cov, 5))
    with open(scr(args, "checks.json"), "w") as f:
        json.dump(checks, f, indent=1)
    log("checks:", checks)


# ---------------- stage 6: FBX + stats -----------------------------------------------------------
def stage_fbx(args, islands, uvd):
    if os.path.exists(OUT["fbx"]) and os.path.exists(OUT["stats"]):
        return
    reset_scene()
    mat = bpy.data.materials.new("KarstIslands")
    mat.use_nodes = True
    nt = mat.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ia = nt.nodes.new("ShaderNodeTexImage"); ia.image = bpy.data.images.load(OUT["albedo"])
    nt.links.new(ia.outputs["Color"], bs.inputs["Base Color"])
    inn = nt.nodes.new("ShaderNodeTexImage"); inn.image = bpy.data.images.load(OUT["normal"])
    inn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(inn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.85
    stats = {"units": "metres", "unity_axes": "Unity = (-x_blender, z_blender, -y_blender); origin = island centre at sea level",
             "atlas": {"albedo": os.path.basename(OUT["albedo"]), "normal": os.path.basename(OUT["normal"]),
                       "size": [ATLAS_W, ATLAS_H]}, "objects": {}}
    total = 0
    for I in islands:
        V, F, UV = uvd[I.name + "__V"], uvd[I.name + "__F"], uvd[I.name + "__UV"]
        ob = make_low_obj(I.name, V, F, UV)
        ob.data.materials.append(mat)
        uu = np.stack([-V[:, 0], V[:, 2], -V[:, 1]], 1)
        px = UV.copy(); px[..., 0] *= ATLAS_W; px[..., 1] *= ATLAS_H
        dens = math.sqrt(tri_areas2(px).sum() / tri_areas3(V, F).sum())
        # unique (vertex, uv) pairs ~ vertex count after the engine splits UV seams
        key = np.concatenate([F.reshape(-1, 1).astype(np.float64), np.round(UV.reshape(-1, 2) * 65536)], 1)
        uverts = len(np.unique(key, axis=0))
        hi = np.load(scr(args, "high_%s.npz" % I.name), mmap_mode=None)
        dv = np.load(scr(args, "low_%s.npz" % I.name))["dev"]
        stats["objects"][I.name] = {
            "tris": int(len(F)), "verts": int(len(V)), "verts_after_uv_split": int(uverts),
            "bounds_unity_min": [round(float(v), 2) for v in uu.min(0)],
            "bounds_unity_max": [round(float(v), 2) for v in uu.max(0)],
            "height_m": round(float(V[:, 2].max()), 1),
            "footprint_m": [round(float(np.ptp(V[:, 0])), 1), round(float(np.ptp(V[:, 1])), 1)],
            "atlas_uv_rect": [round(float(UV[..., 0].min()), 5), round(float(UV[..., 1].min()), 5),
                              round(float(UV[..., 0].max()), 5), round(float(UV[..., 1].max()), 5)],
            "atlas_uv_rect_note": "[uMin, vMin, uMax, vMax]; islands of all objects are interleaved in the shared atlas",
            "texel_density_px_per_m": round(dens, 3),
            "highres_source_tris": int(len(hi["Q"]) * 2),
            "deviation_high_to_low_m": {"mean": round(float(dv[0]), 2), "p95": round(float(dv[1]), 2),
                                        "p99": round(float(dv[2]), 2), "max": round(float(dv[3]), 2)},
            "preview_position_blender": list(LAYOUT[I.name]),
        }
        total += len(F)
    stats["total_tris"] = int(total)
    try:
        stats["bake_checks"] = json.load(open(scr(args, "checks.json")))
    except Exception:
        pass
    bpy.ops.object.select_all(action="SELECT")
    tmp = OUT["fbx"] + ".tmp.fbx"
    bpy.ops.export_scene.fbx(filepath=tmp, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_ALL", global_scale=1.0, axis_forward="-Z", axis_up="Y",
                             bake_space_transform=True, use_mesh_modifiers=True, mesh_smooth_type="OFF",
                             use_tspace=True, use_custom_props=False, add_leaf_bones=False, path_mode="STRIP",
                             embed_textures=False, bake_anim=False)
    os.replace(tmp, OUT["fbx"])
    with open(OUT["stats"], "w") as f:
        json.dump(stats, f, indent=1)
    log("FBX + stats written, total tris", total)


# ---------------- stage 7: previews from the exported game asset only -----------------------------
def game_material(sky, haze=True):
    m = bpy.data.materials.new("KarstGame")
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ia = nt.nodes.new("ShaderNodeTexImage"); ia.image = bpy.data.images.load(OUT["albedo"])
    ia.image.alpha_mode = "CHANNEL_PACKED"
    # AO (alpha) darkens the albedo gently (stand-in for ambient-only occlusion in the game shader)
    aom = nt.nodes.new("ShaderNodeMapRange"); aom.inputs[3].default_value = 0.35; aom.inputs[4].default_value = 1.0
    nt.links.new(ia.outputs["Alpha"], aom.inputs[0])
    mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = "SCALE"
    nt.links.new(ia.outputs["Color"], mul.inputs[0]); nt.links.new(aom.outputs[0], mul.inputs["Scale"])
    nt.links.new(mul.outputs[0], bs.inputs["Base Color"])
    inn = nt.nodes.new("ShaderNodeTexImage"); inn.image = bpy.data.images.load(OUT["normal"])
    inn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(inn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.85
    for k in ("Specular IOR Level", "Specular"):
        if k in bs.inputs:
            bs.inputs[k].default_value = 0.25
    if haze:
        nt.links.new(haze_mix(nt, bs.outputs[0], sky, dist_L=11000.0, max_haze=0.85),
                     nt.nodes["Material Output"].inputs[0])
    return m


def import_islands():
    bpy.ops.import_scene.fbx(filepath=OUT["fbx"], axis_forward="-Z", axis_up="Y")
    obs = {o.name.split(".")[0]: o for o in bpy.context.scene.objects if o.type == "MESH"}
    return obs


def stage_preview(args):
    paths = [os.path.join(HERE, n) for n in ("preview_wide.jpg", "preview_tele.jpg", "preview_wire_sheet.jpg")]
    if all(os.path.exists(p) for p in paths) and not args.force_preview:
        return
    sc = reset_scene()
    setup_cycles(sc, args.preview_samples)
    sc.cycles.use_denoising = True
    sky = sky_world(sc, sun_el_deg=40.0, sun_az_deg=args.sun_az)
    sea_plane(sc, sky)
    color_mgmt(sc, args.exposure)
    obs = import_islands()
    gm = game_material(sky)
    for n, ob in obs.items():
        ob.data.materials.clear(); ob.data.materials.append(gm)
        x, y, r = LAYOUT[n]
        ob.location = (x, y, 0); ob.rotation_euler = (0, 0, r)
        zmin = min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
        assert zmin > -5.05, (n, zmin)
    camera(sc, (0, 0, 2.0), (0, 1200, 95), 40.0)
    render_to(sc, paths[0])
    x, y, _ = LAYOUT[args.tele]
    camera(sc, (0, 0, 2.0), (x, y, 140), 15.0, name="CamTele")
    render_to(sc, paths[1])
    # wire / silhouette sheet: low-poly game meshes in a row, wireframe over flat shading, white backdrop
    sc = reset_scene()
    setup_cycles(sc, 16)
    sc.cycles.use_denoising = False
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.view_settings.view_transform = "Standard"
    obs = import_islands()
    m = bpy.data.materials.new("Wire"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes
    for n_ in list(N):
        if n_.type != "OUTPUT_MATERIAL":
            N.remove(n_)
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.3
    base = N.new("ShaderNodeMapRange"); base.inputs[3].default_value = 0.42; base.inputs[4].default_value = 0.78
    nt.links.new(lw.outputs["Facing"], base.inputs[0])
    wf = N.new("ShaderNodeWireframe"); wf.use_pixel_size = True; wf.inputs[0].default_value = 0.9
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    nt.links.new(wf.outputs[0], mx.inputs["Factor"])
    cr = N.new("ShaderNodeCombineColor")
    nt.links.new(base.outputs[0], cr.inputs[0]); nt.links.new(base.outputs[0], cr.inputs[1]); nt.links.new(base.outputs[0], cr.inputs[2])
    nt.links.new(cr.outputs[0], mx.inputs["A"])
    mx.inputs["B"].default_value = (0.05, 0.12, 0.35, 1)
    em = N.new("ShaderNodeEmission"); nt.links.new(mx.outputs["Result"], em.inputs[0])
    nt.links.new(em.outputs[0], N["Material Output"].inputs[0])
    order = OBJ_ORDER
    xcur = 0.0
    rows = [order[:6], order[6:]]
    zrow = [0.0, -520.0]
    span = 0
    for ri, row in enumerate(rows):
        xcur = 0.0
        for n in row:
            ob = obs[n]
            ob.data.materials.clear(); ob.data.materials.append(m)
            xs = [v.co.x for v in ob.data.vertices]
            ob.location = (xcur - min(xs), 0, zrow[ri])
            xcur += (max(xs) - min(xs)) + 60
        span = max(span, xcur)
    cd = bpy.data.cameras.new("O"); cd.type = "ORTHO"; cd.ortho_scale = span * 1.02
    co = bpy.data.objects.new("O", cd); sc.collection.objects.link(co)
    co.location = (span / 2 - 30, -5000, -60); co.rotation_euler = (math.radians(90), 0, 0)
    cd.clip_end = 20000
    sc.camera = co
    sc.render.resolution_x, sc.render.resolution_y = 1600, int(1600 * 1000 / (span * 1.02)) + 40
    sc.render.resolution_y = min(max(sc.render.resolution_y, 500), 1000)
    render_to(sc, paths[2])


# ---------------- driver -------------------------------------------------------------------------
def write_readme():
    pass


def main():
    args = parse_args()
    if args.stage == "dev":
        return stage_dev(args)
    os.makedirs(args.scratch, exist_ok=True)
    islands = make_islands()
    if args.stage in ("all", "build"):
        for I in islands:
            stage_high(args, I)
        for I in islands:
            stage_low(args, I)
        stage_uv(args, islands)
        uvd = dict(np.load(scr(args, "uv.npz")))
        cov_path = scr(args, "coverage.npz")
        if not os.path.exists(cov_path):
            objid, overl = raster_coverage(islands, uvd)
            save_npz(cov_path, objid=objid, overl=overl)
        c = np.load(cov_path); objid, overl = c["objid"], c["overl"]
        log("coverage %.1f%% of atlas, overlapping texels %d" % (100.0 * (objid >= 0).mean(), int((overl > 1).sum())))
        for I in islands:
            stage_bake(args, I, uvd, objid)
        stage_compose(args, islands, uvd, objid, overl)
        stage_fbx(args, islands, uvd)
    if args.stage in ("all", "preview"):
        stage_preview(args)
    log("done")


if __name__ == "__main__":
    main()
