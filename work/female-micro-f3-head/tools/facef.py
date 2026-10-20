"""Face_F: paint + eyeball layers built on the analytic skin surface (never volume).  Each builder returns (V list, F list, mat list)."""
import numpy as np
import fl, feat_f, geo
from fl import MM, K, zrow

MATS = ['Brow', 'BrowSoft', 'Sclera', 'IrisIn', 'Iris', 'Limbal', 'Pupil', 'Catch', 'LidLine', 'LidLower', 'Lip', 'LipUp', 'Seam', 'Nostril']


class Layer:
    def __init__(self): self.V = []; self.F = []; self.M = []; self.name = []; self.lift = []
    def add(self, V, F, mat, tag='', lift=None):
        """lift: None -> vertices keep their analytic positions;  float -> project onto the final skin mesh and lift by this much along its normal"""
        base = len(self.V); self.V += [tuple(v) for v in np.asarray(V, float)]; self.lift += [lift] * len(V)
        for f in F: self.F.append([base + int(i) for i in f]); self.M.append(MATS.index(mat)); self.name.append(tag)


class Skin:
    """skin frame at (x, z) front-projected coordinates: point + outward normal (finite differences of the analytic surface)"""
    def __init__(self, H): self.H = H
    def pt(self, x, z):
        x = np.atleast_1d(np.asarray(x, float)); z = np.atleast_1d(np.asarray(z, float))
        a = self.H.L.at(z)['a']; x = np.sign(x) * np.minimum(np.abs(x), 0.985 * a)       # never leave the surface laterally
        P, _ = self.H.surf_xz(x, z)
        h = 0.0007
        Px, _ = self.H.surf_xz(x + h, z); Pm, _ = self.H.surf_xz(x - h, z); Pz, _ = self.H.surf_xz(x, z + h); Pzm, _ = self.H.surf_xz(x, z - h)
        n = np.cross(Px - Pm, Pz - Pzm)                  # dx x dz points toward -y for a front-facing surface ... fix sign below
        n /= np.linalg.norm(n, axis=1, keepdims=True)
        flip = np.sum(n * (P - geo.C[None, :]), axis=1) < 0      # outward = away from the head centre
        n[flip] *= -1
        return P, n


def ribbon(sk, xa, za, xb, zb, m=3, lift=0.0003, flip=False):
    """strip between two (x,z) polylines of equal length n: rows j=0..m interpolated; returns V (n*(m+1),3), faces"""
    n = len(xa); V = []; 
    for j in range(m + 1):
        t = j / m
        x = (1 - t) * np.asarray(xa) + t * np.asarray(xb); z = (1 - t) * np.asarray(za) + t * np.asarray(zb)
        P, N = sk.pt(x, z); V.append(P + lift * N)
    V = np.concatenate(V)
    F = []
    for j in range(m):
        for i in range(n - 1):
            a = j * n + i; b = a + 1; c = (j + 1) * n + i + 1; d = (j + 1) * n + i
            F.append([a, b, c, d] if not flip else [d, c, b, a])
    return V, F


def orient_outward(V, F, ref=None):
    """make face normals point away from the head centre (geo.C) -- ribbons/shells hug the skin so this is robust"""
    V = np.asarray(V); out = []
    for f in F:
        p = V[f]; c = p.mean(0); nrm = np.cross(p[1] - p[0], p[2] - p[0])
        out.append(f if np.dot(nrm, c - geo.C) > 0 else f[::-1])
    return out


# ------------------------------------------------------------------------------------------------------------------------ brows
def brows(H, L, sk):
    up, lo = feat_f.brow_edges(40)
    for side in (-1, +1):
        xa = side * up[:, 0]; za = up[:, 1]; xb = side * lo[:, 0]; zb = lo[:, 1]
        V, F = ribbon(sk, xa, za, xb, zb, m=3, lift=0.0)
        L.add(V, orient_outward(V, F), 'Brow', 'brow' + ('L' if side < 0 else 'R'), lift=0.00055)
        # soft fringe: slightly larger ribbon, lower lift, lighter colour
        cz = 0.5 * (za + zb); ex = 0.0011; ez = 0.0010
        xa2 = xa + side * ex * np.sign(np.abs(xa) - np.abs(xa).mean()); za2 = za + ez; zb2 = zb - ez
        V2, F2 = ribbon(sk, xa2, za2, xb + 0 * xb, zb2, m=3, lift=0.0)
        L.add(V2, orient_outward(V2, F2), 'BrowSoft', 'browsoft' + ('L' if side < 0 else 'R'), lift=0.00030)


# ------------------------------------------------------------------------------------------------------------------------ eyes
def _ray_poly(poly, c, phi):
    """distance from c along direction phi to the closed polygon (2D)"""
    d = np.array([np.cos(phi), np.sin(phi)]); best = 1e9
    n = len(poly)
    for i in range(n):
        a = poly[i] - c; b = poly[(i + 1) % n] - c; e = b - a
        den = d[0] * (-e[1]) - d[1] * (-e[0])                     # solve t*d = a + s*e
        M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
        if abs(np.linalg.det(M)) < 1e-14: continue
        t, s = np.linalg.solve(M, a)
        if t > 0 and 0 <= s <= 1: best = min(best, t)
    return best


EYE = dict(e_m=0.0022, e_c=0.0008, lid_t=0.0016, ring_mm=[0.0, 4.9, 9.8, 12.0, 14.6, 16.2], nphi=40, ntrans=5, outer=1.10, hidden_extra=0.0032)


def eye_shell(H, L, sk, side, poly=None):
    """eyeball surface following the skin inside the aperture (inset), full iris circle (the part above the aperture hides behind the upper lid)"""
    poly = feat_f.eye_poly(6) if poly is None else poly
    I = feat_f.IRIS
    c = np.array([I['cx'], I['cz']])
    nphi = EYE['nphi']; phis = np.linspace(0, 2 * np.pi, nphi, endpoint=False)
    Rp = np.array([_ray_poly(poly, c, ph) for ph in phis])
    rr = [r * MM for r in EYE['ring_mm']]
    dirs = np.stack([np.cos(phis), np.sin(phis)], 1)
    rings = []
    for r in rr:
        if r == 0.0: rings.append(np.repeat(c[None, :], nphi, 0))
        else: rings.append(c[None, :] + r * dirs)
    Rout = np.maximum(EYE['outer'] * Rp, rr[-1] + 0.0026)
    for k in range(1, EYE['ntrans'] + 1):
        t = k / EYE['ntrans']
        rk = (1 - t) * rr[-1] + t * Rout
        rings.append(c[None, :] + rk[:, None] * dirs)
    nR = len(rings)
    V = []
    for k, ring in enumerate(rings):
        P, N = sk.pt(side * ring[:, 0], ring[:, 1])
        dp = feat_f.poly_signed_dist(ring[:, 0], ring[:, 1], poly)                    # +inside
        rho = np.linalg.norm(ring - c[None, :], axis=1) / np.maximum(Rp, 1e-6)
        e = EYE['e_m'] - (EYE['e_m'] - EYE['e_c']) * (1 - np.clip(rho, 0, 1) ** 2)
        e = e + EYE['hidden_extra'] * fl.sstep(0.0, 0.004, -dp)
        V.append(P - e[:, None] * N)
    V = np.concatenate(V)
    def vid(k, i): return k * nphi + (i % nphi)
    lab = {1: 'Pupil', 2: 'IrisIn', 3: 'Iris', 4: 'Limbal'}
    F2 = []; M2 = []
    for i in range(nphi): F2.append([vid(0, i), vid(1, i), vid(1, i + 1)]); M2.append('Pupil')
    for k in range(1, nR - 1):
        m = lab.get(k, 'Sclera')
        for i in range(nphi): F2.append([vid(k, i), vid(k + 1, i), vid(k + 1, i + 1), vid(k, i + 1)]); M2.append(m)
    Fo = orient_outward(V, F2)
    base = len(L.V); L.V += [tuple(v) for v in V]; L.lift += [None] * len(V)
    for f, m in zip(Fo, M2): L.F.append([base + i for i in f]); L.M.append(MATS.index(m)); L.name.append('eye' + ('L' if side < 0 else 'R'))
    # catch light disc just in front of the shell
    hx, hz, hr = I['hi']
    cc = np.array([I['cx'] + (1.0 if side > 0 else -1.0) * hx, I['cz'] + hz])
    th = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    pts = np.vstack([cc[None, :], cc[None, :] + hr * np.stack([np.cos(th), np.sin(th)], 1)])
    P, N = sk.pt(side * pts[:, 0], pts[:, 1])
    rho = np.linalg.norm(pts - c[None, :], axis=1) / 0.010
    e = EYE['e_m'] - (EYE['e_m'] - EYE['e_c']) * (1 - np.clip(rho, 0, 1) ** 2)
    Vc = P - (e - 0.00045)[:, None] * N
    Fc = [[0, 1 + i, 1 + (i + 1) % 16] for i in range(16)]
    L.add(Vc, orient_outward(Vc, Fc), 'Catch', 'catch' + ('L' if side < 0 else 'R'))
    return rings


def eye_lines(H, L, sk, side, poly=None):
    poly = feat_f.eye_poly(6) if poly is None else poly
    I = feat_f.IRIS; c = np.array([I['cx'], I['cz']])
    iu = feat_f.EYE_OUTER * 6                                         # index of the outer corner in the smoothed polygon
    upper = poly[0:iu + 1]; lower = np.vstack([poly[iu:], poly[:1]])
    def outward(curve):
        t = np.gradient(curve, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True)
        nrm = np.stack([-t[:, 1], t[:, 0]], 1); sgn = np.sign(np.sum(nrm * (curve - c[None, :]), axis=1)); sgn[sgn == 0] = 1
        return nrm * sgn[:, None]
    # upper lash band (inner -> outer corner): thick black band above the lid margin
    sarc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(upper, axis=0), axis=1))]); sarc /= sarc[-1]
    w = np.interp(sarc, [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0], [1.8, 4.0, 6.3, 7.0, 6.8, 5.0, 3.2]) * MM
    no = outward(upper); outer_edge = upper + no * w[:, None]
    V, F = ribbon(sk, side * upper[:, 0], upper[:, 1], side * outer_edge[:, 0], outer_edge[:, 1], m=3, lift=0.0)
    L.add(V, orient_outward(V, F), 'LidLine', 'lash' + ('L' if side < 0 else 'R'), lift=0.00045)
    # wing: tapered flick from the outer corner, pointing out and slightly up
    O = upper[-1]; dirw = np.array([1.0, 0.30]); dirw /= np.linalg.norm(dirw)
    Lw = 4.4 * MM; k = 8; t = np.linspace(0, 1, k)
    base_lo = O[None, :] + np.outer(t, dirw) * Lw
    base_hi = outer_edge[-1][None, :] + np.outer(t, dirw) * Lw
    base_hi = base_lo + (base_hi - base_lo) * (1 - t)[:, None] ** 0.85
    base_lo[:, 0] = np.minimum(base_lo[:, 0], 0.0925); base_hi[:, 0] = np.minimum(base_hi[:, 0], 0.0925)
    V, F = ribbon(sk, side * base_lo[:, 0], base_lo[:, 1], side * base_hi[:, 0], base_hi[:, 1], m=2, lift=0.0)
    L.add(V, orient_outward(V, F), 'LidLine', 'wing' + ('L' if side < 0 else 'R'), lift=0.00045)
    # soft double-lid crease: thin tapered line above the lash band (plate: faint brown crease)
    s0, s1 = 0.16, 0.90; sel = (sarc >= s0) & (sarc <= s1)
    base = upper[sel] + no[sel] * (w[sel] + 3.4 * MM)[:, None]
    tt = (sarc[sel] - s0) / (s1 - s0); wc = 0.60 * MM * np.sin(np.pi * tt) ** 0.7 + 0.06 * MM
    top = base + no[sel] * wc[:, None]
    V, F = ribbon(sk, side * base[:, 0], base[:, 1], side * top[:, 0], top[:, 1], m=1, lift=0.0)
    L.add(V, orient_outward(V, F), 'BrowSoft', 'crease' + ('L' if side < 0 else 'R'), lift=('ray', 0.00045))
    # lower lid line
    nl = outward(lower); wl = np.interp(np.linspace(0, 1, len(lower)), [0, 0.5, 1], [0.8, 1.2, 0.8]) * MM
    out2 = lower + nl * wl[:, None]
    V, F = ribbon(sk, side * lower[:, 0], lower[:, 1], side * out2[:, 0], out2[:, 1], m=1, lift=0.0)
    L.add(V, orient_outward(V, F), 'LidLower', 'lower' + ('L' if side < 0 else 'R'), lift=0.00045)


# ------------------------------------------------------------------------------------------------------------------------ mouth
def mouth(H, L, sk):
    mo = feat_f.MOUTH; hw = mo['hw']
    xs = np.linspace(-hw, hw, 81)
    zs = H.seam_z(xs)
    # lips first (analytic skin surface + lift: the lip surface is smooth, no BVH needed), then the seam on top
    zu = mo['ztop'] + (mo['ztop_k'] - mo['ztop']) * (np.abs(xs) / hw) ** 3.0
    V, F = ribbon(sk, xs, zu, xs, zs, m=5, lift=0.00060)
    L.add(V, orient_outward(V, F), 'LipUp', 'lipup', lift=('ray', 0.00055))
    hl = 0.0262; xl = np.linspace(-hl, hl, 53); zsl = H.seam_z(xl)
    zl = zsl - (zsl - 1.4634) * np.sqrt(np.clip(1 - (xl / hl) ** 2, 0, 1)) ** 1.0
    V, F = ribbon(sk, xl, zsl, xl, zl, m=6, lift=0.00060)
    L.add(V, orient_outward(V, F), 'Lip', 'liplo', lift=('ray', 0.00055))
    w = 0.00080 * (1 - (np.abs(xs) / hw) ** 3) + 0.00030
    V, F = ribbon(sk, xs, zs + w * 0.5, xs, zs - w * 0.5, m=1, lift=0.00095)
    L.add(V, orient_outward(V, F), 'Seam', 'seam', lift=('ray', 0.00085))


# ------------------------------------------------------------------------------------------------------------------------ nostril cups (dark pockets behind the carved holes)
def nostril_cup(H, L, sk, P, loop, depth=0.0032):
    pts = P[loop]; c = pts.mean(axis=0)
    _, N = sk.pt(pts[:, 0], pts[:, 2]); nm = N.mean(axis=0); nm /= np.linalg.norm(nm)
    ring2 = c[None, :] + 0.62 * (pts - c[None, :]) - nm[None, :] * depth * 0.75
    apex = c - nm * depth * 1.25
    V = np.vstack([pts, ring2, apex[None, :]]); n = len(pts)
    F = []
    for i in range(n):
        j = (i + 1) % n
        F.append([i, j, n + j, n + i]); F.append([n + i, n + j, 2 * n])
    out = []
    for f in F:
        p = V[f]; fc = p.mean(0); nrm = np.cross(p[1] - p[0], p[2] - p[0])
        out.append(f if np.dot(nrm, (c + nm * 0.01) - fc) > 0 else f[::-1])
    L.add(V, out, 'Nostril', 'nostril', lift=None)


def nostrils(H, L, sk):
    nz = feat_f.NOSTRIL
    for side in (-1, 1):
        th = np.linspace(0, 2 * np.pi, 18, endpoint=False)
        pts = np.vstack([[nz['cx'], nz['cz']], np.column_stack([nz['cx'] + 0.85 * nz['rx'] * np.cos(th), nz['cz'] + 0.60 * nz['rz'] * np.sin(th)])])
        P, N = sk.pt(side * pts[:, 0], pts[:, 1])
        F = [[0, 1 + i, 1 + (i + 1) % 18] for i in range(18)]
        L.add(P, orient_outward(P, F), 'Nostril', 'nostril' + ('L' if side < 0 else 'R'), lift=('ray', 0.00060))
