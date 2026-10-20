"""Photometric mesh optimisation (PMO): per-vertex displacement h_i along fixed directions d_i so that the Lambert shading of the mesh under the
plate-fitted light matches the plate luminance in several views.  Pure numpy.  Jacobian by footprint-coloured finite differences."""
import sys, math, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i')
from edlib import *

PLATE_L = np.asarray(PLATE.convert('L')).astype(np.float64)       # (720,1280) full plate luminance


def gauss_blur(a, s):
    k = int(max(1, round(3 * s))); xs = np.arange(-k, k + 1); w = np.exp(-0.5 * (xs / s) ** 2); w /= w.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 1, a)


def bilinear(img, col, row):
    h, w = img.shape
    c = np.clip(col, 0, w - 1.001); r = np.clip(row, 0, h - 1.001)
    c0 = np.floor(c).astype(int); r0 = np.floor(r).astype(int); fc = c - c0; fr = r - r0
    return (img[r0, c0] * (1 - fc) * (1 - fr) + img[r0, c0 + 1] * fc * (1 - fr) + img[r0 + 1, c0] * (1 - fc) * fr + img[r0 + 1, c0 + 1] * fc * fr)


def light_world(right, up, toward, az, el):
    a = math.radians(az); e = math.radians(el)
    return right * math.sin(a) * math.cos(e) + up * math.sin(e) + toward * math.cos(a) * math.cos(e)


class View:
    """orthographic plate view.  fold=True: use mirrored (|x|) vertices (all non-front plates show the +x side)."""
    def __init__(self, name, az, kind, pm=None, light=(0.0, 40.0, 95.0, 95.0), fold=True, plate_sigma=1.3):
        self.name = name; self.kind = kind; self.az = az; self.pm = pm; self.fold = fold
        a = math.radians(az)
        self.right = np.array([math.cos(a), math.sin(a), 0.0]); self.up = np.array([0, 0, 1.0]); self.toward = np.array([math.sin(a), -math.cos(a), 0.0])
        self.set_light(*light)
        self.img = gauss_blur(PLATE_L, plate_sigma)

    def set_light(self, az_l, el_l, a, b):
        self.light = (az_l, el_l, a, b)
        self.l = light_world(self.right, self.up, self.toward, az_l, el_l); self.a = a; self.b = b

    def project(self, P):
        if self.kind == 'front':
            return colx(P[:, 0]), rowz(P[:, 2])
        if self.kind == 'left':
            return 712.0 + (P[:, 1] - 0.065) / K, 76.0 + (TOP - P[:, 2]) / K
        if self.kind == 'right':
            return 1123.0 + (P[:, 1] - 0.065) / K, 76.0 + (TOP - P[:, 2]) / K
        a = math.radians(self.az); u = P[:, 0] * math.cos(a) + (P[:, 1] + 0.1254) * math.sin(a)
        return self.pm + u / K, 397.0 + (TOP - P[:, 2]) / K

    def depth(self, P): return P @ self.toward


VIEWS_DEF = {
    'front': dict(az=0.0, kind='front', pm=None, fold=False, light=(4.0, 40.0, 100.0, 93.4)),
    'q3L': dict(az=41.0, kind='q3', pm=176.5, fold=True, light=(-4.0, 40.0, 90.0, 99.6)),
    'q3R': dict(az=36.0, kind='q3', pm=589.5, fold=True, light=(-4.0, 40.0, 97.2, 92.2)),
    'left': dict(az=90.0, kind='left', pm=None, fold=True, light=(0.0, 40.0, 94.2, 94.9)),
}


def make_views(names=('front', 'q3L', 'q3R', 'left')):
    return [View(n, **VIEWS_DEF[n]) for n in names]


def fold_pts(P, N, fold):
    if not fold: return P, N
    s = np.where(P[:, 0] < 0, -1.0, 1.0)
    Q = P.copy(); Q[:, 0] = np.abs(P[:, 0]); M = N.copy(); M[:, 0] = N[:, 0] * s
    return Q, M


def zbuffer(view, P, mask_v, res=2.0, rad=2):
    """nearest-depth buffer (plate px * res) from all vertices flagged in mask_v, max-filtered to fill the splat gaps"""
    col, row = view.project(P[mask_v]); dep = view.depth(P[mask_v])
    H, W = int(720 * res), int(1280 * res)
    zb = np.full((H, W), -1e9)
    ci = np.clip(np.round(col * res).astype(int), 0, W - 1); ri = np.clip(np.round(row * res).astype(int), 0, H - 1)
    np.maximum.at(zb, (ri, ci), dep)
    out = zb.copy()
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            out = np.maximum(out, np.roll(np.roll(zb, dy, 0), dx, 1))
    return out, res


class Problem:
    def __init__(self, V0, F, views, free, d, wmask, rho=None, smooth_iters=3, ring=None, wlap=1.0):
        """V0: base vertices.  free: bool mask of vertices allowed to move (others fixed).  d: (n,3) unit directions.
        wmask: (n,) data weight per vertex (0 = excluded from the data term).  rho: (n,) albedo factor."""
        self.V0 = V0.copy(); self.F = F; self.views = views; self.n = len(V0)
        self.M = Mesh(V0, F)
        self.free = np.asarray(free, bool); self.idx = np.where(self.free)[0]; self.d = d
        self.wmask = np.asarray(wmask, float); self.rho = np.ones(self.n) if rho is None else rho
        self.smooth_iters = smooth_iters
        self.ring = np.zeros(self.n, bool) if ring is None else ring
        # head subset for normal computation (fast): all vertices with z > 1.40
        self.head = V0[:, 2] > 1.40
        hv = np.where(self.head)[0]; self.hv = hv
        rem = -np.ones(self.n, int); rem[hv] = np.arange(len(hv)); self.rem = rem
        Fh = [f for f in F if all(self.head[i] for i in f)]
        self.Fh = [[int(rem[i]) for i in f] for f in Fh]
        self.Mh = Mesh(V0[hv], self.Fh)
        self.tri = np.array([f for f in self.Fh if len(f) == 3], np.int64).reshape(-1, 3)
        self.quad = np.array([f for f in self.Fh if len(f) == 4], np.int64).reshape(-1, 4)
        # vertices whose normals are smoothed (head, not ring)
        self.sm = ~self.ring[hv]
        self.vis = None
        self.contours = []; self.contour_sel = {}; self.vmap = {v.name: v for v in views}

    def positions(self, h):
        P = self.V0.copy(); P[self.idx] += self.d[self.idx] * (h[:, None] * 1e-3); return P      # h in millimetres

    def normals(self, P):
        Ph = P[self.hv]; n = np.zeros_like(Ph)
        if len(self.tri):
            a, b, c = (Ph[self.tri[:, k]] for k in range(3)); fn = np.cross(b - a, c - a)
            for k in range(3): np.add.at(n, self.tri[:, k], fn)
        if len(self.quad):
            a, b, c, d_ = (Ph[self.quad[:, k]] for k in range(4)); fn = np.cross(c - a, d_ - b)
            for k in range(4): np.add.at(n, self.quad[:, k], fn)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        w = self.sm[:, None].astype(float)
        for _ in range(self.smooth_iters):
            m = self.Mh.nbr_mean(n); t = 0.5 * n + 0.5 * m; t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
            n = np.where(w > 0, t, n)
        N = np.zeros((self.n, 3)); N[self.hv] = n
        return N

    def setup_visibility(self, P, N, face_min_cos=0.15, tol=0.004):
        self.vis = {}
        Nraw = N
        for v in self.views:
            Q, Nq = fold_pts(P, Nraw, v.fold)
            zb, res = zbuffer(v, Q, self.head)
            col, row = v.project(Q); dep = v.depth(Q)
            ci = np.clip(np.round(col * res).astype(int), 0, zb.shape[1] - 1); ri = np.clip(np.round(row * res).astype(int), 0, zb.shape[0] - 1)
            vis = (dep >= zb[ri, ci] - tol) & ((Nq @ v.toward) > face_min_cos) & self.head
            self.vis[v.name] = vis

    def residuals(self, h, return_parts=False):
        P = self.positions(h); N = self.normals(P)
        out = []
        for v in self.views:
            Q, Nq = fold_pts(P, N, v.fold)
            col, row = v.project(Q)
            I = bilinear(v.img, col, row)
            s = v.a + v.b * np.clip(Nq @ v.l, 0.0, None)
            w = self.wmask * self.vis[v.name] * np.clip(Nq @ v.toward, 0.0, 1.0)
            sel = np.where(self.wmask * self.vis[v.name] > 0)[0]
            out.append((sel, np.sqrt(w[sel]) * (I[sel] - self.rho[sel] * s[sel])))
        if self.contours:
            for (vname, kind, rows_arr, lo_cols, hi_cols, w_s, tol_mm) in self.contours:
                v = self.vmap[vname]
                col, row = v.project(P)           # contours use the true (unfolded) positions: the far side forms the left silhouette
                lo = np.interp(row, rows_arr, lo_cols, left=np.nan, right=np.nan); hi = np.interp(row, rows_arr, hi_cols, left=np.nan, right=np.nan)
                ex_lo = np.nan_to_num((lo - col) * K * 1000 - tol_mm, nan=0.0); ex_hi = np.nan_to_num((col - hi) * K * 1000 - tol_mm, nan=0.0)
                r = w_s * (np.maximum(ex_lo, 0.0) + np.maximum(ex_hi, 0.0))
                sel = self.contour_sel[vname]
                out.append((sel, r[sel]))
        if return_parts: return out
        return np.concatenate([o[1] for o in out])


# ----------------------------------------------------------------------------------------------------------------------------------
# Jacobian by footprint-coloured finite differences, Gauss-Newton / CG solver
# ----------------------------------------------------------------------------------------------------------------------------------
def color_classes(P, idx, D=0.040):
    c = np.floor(P[idx] / D).astype(np.int64)
    par = (c[:, 0] & 1) | ((c[:, 1] & 1) << 1) | ((c[:, 2] & 1) << 2)
    key = (c[:, 0] - c[:, 0].min()) * 100000 + (c[:, 1] - c[:, 1].min()) * 1000 + (c[:, 2] - c[:, 2].min())
    order = np.lexsort((np.arange(len(idx)), key))
    k = np.zeros(len(idx), np.int64)
    ks = key[order]
    start = np.r_[0, np.where(np.diff(ks) != 0)[0] + 1]
    for s, e in zip(start, np.r_[start[1:], len(idx)]):
        k[order[s:e]] = np.arange(e - s)
    maxk = k.max() + 1
    return par * maxk + k            # class id per free vertex (position in idx)


def build_jacobian(pb, h, delta=0.2, D=0.040, verbose=False):
    """returns (rows, cols, vals, r0): J as COO over (residual row, free-vertex index in pb.idx)"""
    P0 = pb.positions(h)
    parts0 = pb.residuals(h, return_parts=True)
    r0 = np.concatenate([p[1] for p in parts0])
    # row -> (vertex, view) bookkeeping
    row_vert = np.concatenate([p[0] for p in parts0])
    cls = color_classes(pb.V0, pb.idx, D)
    ncls = cls.max() + 1
    rows_all = []; cols_all = []; vals_all = []
    t0 = time.time()
    members = [[] for _ in range(ncls)]
    for j, c in enumerate(cls): members[c].append(j)
    Pv = pb.V0                                     # distances from the base geometry
    for c in range(ncls):
        mem = np.array(members[c], np.int64)
        if len(mem) == 0: continue
        h2 = h.copy(); h2[mem] += delta
        r1 = pb.residuals(h2)
        dr = (r1 - r0) / delta
        nz = np.where(np.abs(dr) > 1e-9)[0]
        if len(nz) == 0: continue
        # attribute each changed row to the nearest perturbed member (3D distance between the row's vertex and the member vertex)
        rv = Pv[row_vert[nz]]; mv = Pv[pb.idx[mem]]
        d2 = ((rv[:, None, :] - mv[None, :, :]) ** 2).sum(axis=2)
        j_near = mem[np.argmin(d2, axis=1)]
        rows_all.append(nz); cols_all.append(j_near); vals_all.append(dr[nz])
    rows = np.concatenate(rows_all); cols = np.concatenate(cols_all); vals = np.concatenate(vals_all)
    if verbose: print('  jacobian: %d classes, nnz %d, %.1fs' % (ncls, len(vals), time.time() - t0))
    return rows, cols, vals, r0


class Sparse:
    def __init__(self, rows, cols, vals, nr, nc):
        self.rows, self.cols, self.vals, self.nr, self.nc = rows, cols, vals, nr, nc

    def dot(self, x): return np.bincount(self.rows, weights=self.vals * x[self.cols], minlength=self.nr)
    def tdot(self, y): return np.bincount(self.cols, weights=self.vals * y[self.rows], minlength=self.nc)


def lap_apply(pb, H):
    """umbrella Laplacian (I - A) on the full-length vector (head subset), returns full-length"""
    Hh = H[pb.hv]
    m = pb.Mh.nbr_mean(Hh[:, None])[:, 0]
    out = np.zeros(pb.n); out[pb.hv] = Hh - m
    return out


def lap_t_apply(pb, Y):
    """(I - A)^T applied; A is the row-stochastic neighbour average: A^T y = scatter y_i/deg_i to neighbours"""
    Yh = Y[pb.hv]; deg = np.maximum(pb.Mh.deg, 1)
    s = np.zeros_like(Yh); E = pb.Mh.E
    np.add.at(s, E[:, 0], Yh[E[:, 1]] / deg[E[:, 1]]); np.add.at(s, E[:, 1], Yh[E[:, 0]] / deg[E[:, 0]])
    out = np.zeros(pb.n); out[pb.hv] = Yh - s
    return out


def solve_gn(pb, h0, lam_lap=40.0, lam_mag=0.5, freeze_w=None, iters=6, hmax=8.0, cg_iters=150, mu=1e-3, verbose=True, symmetrize=None, delta=0.2, D=0.040):
    nf = len(pb.idx)
    h = h0.copy()
    fz = np.zeros(nf) if freeze_w is None else freeze_w[pb.idx]

    def energy(hh, parts_r=None):
        r = pb.residuals(hh) if parts_r is None else parts_r
        H = np.zeros(pb.n); H[pb.idx] = hh
        Lh = lap_apply(pb, H)
        return 0.5 * float(r @ r) + 0.5 * lam_lap * float(Lh @ Lh) + 0.5 * lam_mag * float(hh @ hh) + 0.5 * float((fz * hh * hh).sum()), float(r @ r)
    E0, rr0 = energy(h)
    if verbose: print('  start: E %.4g  data %.4g (rms %.3f)' % (E0, rr0, math.sqrt(rr0 / max(1, len(pb.residuals(h))))))
    for it in range(iters):
        rows, cols, vals, r0 = build_jacobian(pb, h, delta=delta, D=D, verbose=verbose)
        J = Sparse(rows, cols, vals, len(r0), nf)

        def Aop(x):
            H = np.zeros(pb.n); H[pb.idx] = x
            LtL = lap_t_apply(pb, lap_apply(pb, H))[pb.idx]
            return J.tdot(J.dot(x)) + lam_lap * LtL + (lam_mag + fz + mu) * x
        Hc = np.zeros(pb.n); Hc[pb.idx] = h
        grad = J.tdot(r0) + lam_lap * lap_t_apply(pb, lap_apply(pb, Hc))[pb.idx] + (lam_mag + fz) * h
        # CG
        x = np.zeros(nf); r_ = -grad - Aop(x); p_ = r_.copy(); rs = r_ @ r_
        for k in range(cg_iters):
            Ap = Aop(p_); alpha = rs / max(p_ @ Ap, 1e-30)
            x += alpha * p_; r_ -= alpha * Ap; rs_new = r_ @ r_
            if rs_new < 1e-14 * max(1.0, grad @ grad): break
            p_ = r_ + (rs_new / rs) * p_; rs = rs_new
        # line search
        best = None
        for a in (1.0, 0.6, 0.3, 0.15):
            hn = np.clip(h + a * x, -hmax, hmax)
            if symmetrize is not None: hn = symmetrize(hn)
            En, rrn = energy(hn)
            if best is None or En < best[0]: best = (En, a, hn, rrn)
            if En < E0: break
        En, a, hn, rrn = best
        if verbose: print('  iter %d: |step| max %.2f mm, alpha %.2f, E %.4g -> %.4g (data %.4g)' % (it, np.abs(x).max(), a, E0, En, rrn))
        if En >= E0 - 1e-9 * abs(E0):
            if verbose: print('  no further decrease'); 
            break
        h = hn; E0 = En
    return h


# ----------------------------------------------------------------------------------------------------------------------------------
# smooth, mirror-symmetric RBF basis:  h = Phi c
# ----------------------------------------------------------------------------------------------------------------------------------
def make_basis(P, spacing=0.006, sigma=0.007):
    """P: (nf,3) free vertex positions.  Gaussian RBFs, centres by farthest-point sampling on the x>=0 half, mirrored pairs share one coefficient."""
    half = np.where(P[:, 0] >= -0.0005)[0]
    Q = P[half]
    centers = [Q[np.argmin(np.linalg.norm(Q - Q.mean(axis=0), axis=1))]]
    dmin = np.linalg.norm(Q - centers[0], axis=1)
    while dmin.max() > spacing:
        j = int(np.argmax(dmin)); centers.append(Q[j])
        dmin = np.minimum(dmin, np.linalg.norm(Q - Q[j], axis=1))
    C = np.array(centers)
    Phi = np.zeros((len(P), len(C)))
    for k, c in enumerate(C):
        g = np.exp(-0.5 * (((P - c) ** 2).sum(axis=1)) / sigma ** 2)
        if c[0] > 0.002:
            cm = c.copy(); cm[0] *= -1
            g = g + np.exp(-0.5 * (((P - cm) ** 2).sum(axis=1)) / sigma ** 2)
        Phi[:, k] = g
    return Phi, C


def solve_gn_rbf(pb, Phi, c0, lam_c=50.0, fz=None, iters=8, hmax=6.0, mu0=1.0, delta=0.2, D=0.040, verbose=True):
    """Levenberg-Marquardt in the RBF coefficient space.  hmax is a soft bound (quadratic barrier beyond hmax)."""
    nf, m = Phi.shape
    fzv = np.zeros(nf) if fz is None else fz[pb.idx]
    c = c0.copy(); mu = mu0

    def energy(cc):
        h = Phi @ cc; r = pb.residuals(h)
        over = np.maximum(np.abs(h) - hmax, 0.0)
        return 0.5 * float(r @ r) + 0.5 * lam_c * float(cc @ cc) + 0.5 * float((fzv * h * h).sum()) + 0.5 * 5000.0 * float(over @ over), float(r @ r)
    E0, rr0 = energy(c)
    if verbose: print('  start: E %.4g  data %.4g' % (E0, rr0))
    for it in range(iters):
        h = Phi @ c
        rows, cols, vals, r0 = build_jacobian(pb, h, delta=delta, D=D, verbose=verbose)
        J = Sparse(rows, cols, vals, len(r0), nf)
        Jc = np.empty((len(r0), m))
        for k in range(m): Jc[:, k] = J.dot(Phi[:, k])
        A0 = Jc.T @ Jc + lam_c * np.eye(m) + (Phi * fzv[:, None]).T @ Phi
        over = np.sign(h) * np.maximum(np.abs(h) - hmax, 0.0)
        g = Jc.T @ r0 + lam_c * c + Phi.T @ (fzv * h) + 5000.0 * (Phi.T @ over)
        accepted = False
        for tr in range(8):
            dc = np.linalg.solve(A0 + mu * np.diag(np.diag(A0) + 1e-6), -g)
            cn = c + dc; En, rrn = energy(cn)
            if En < E0:
                accepted = True; break
            mu *= 8.0
        if not accepted:
            if verbose: print('  iter %d: no decrease even with mu=%.3g' % (it, mu))
            break
        if verbose: print('  iter %d: mu %.3g, max|h| %.2f mm, E %.4g -> %.4g (data rms %.2f)' % (it, mu, np.abs(Phi @ cn).max(), E0, En, math.sqrt(rrn / len(r0))))
        rel = (E0 - En) / abs(E0)
        c = cn; E0 = En; mu = max(mu / 4.0, 1e-3)
        if rel < 2e-3: break
    return c


def add_contour_constraints(pb, V0, w_s=6.0, tol_mm=1.0, z_range=(1.452, 1.62), names=('q3L', 'q3R')):
    """hinge penalties that stop free vertices from leaving the plate silhouette (3/4 plates: both sides).  Plate extents from the skin masks, outliers removed."""
    import contours as C
    for name in names:
        rows = np.arange(C.BOXES[name][1] + 2, C.BOXES[name][3] - 2)
        pe = C.plate_extent(name, rows)
        rr = np.array(sorted(pe)); lo = np.array([pe[r][0] for r in rr], float); hi = np.array([pe[r][1] for r in rr], float)

        def runmed(a, k=7):
            pad = np.pad(a, k // 2, mode='edge'); return np.array([np.median(pad[i:i + k]) for i in range(len(a))])
        bad = (np.abs(lo - runmed(lo)) > 3) | (np.abs(hi - runmed(hi)) > 3)
        if name in ('q3L', 'q3R'): bad |= (rr >= 462) & (rr <= 492)
        if name == 'front': bad |= (rr >= 330)
        # the lowest rows (chin underside / neck) are not clean silhouettes in the skin masks
        bad |= (rr >= 584) if name in ('q3L', 'q3R') else (rr >= 262)
        lo[bad] = np.nan; hi[bad] = np.nan
        # z-tolerant extents: min/max over a +-3 row window (a vertex may sit a mm above/below the row it is compared with)
        lo_d = lo.copy(); hi_d = hi.copy()
        for i in range(len(rr)):
            w = [j for j in range(max(0, i - 3), min(len(rr), i + 4)) if not np.isnan(lo[j]) and abs(rr[j] - rr[i]) <= 3]
            if w: lo_d[i] = min(lo[j] for j in w); hi_d[i] = max(hi[j] for j in w)
        lo, hi = lo_d, hi_d
        ok = ~np.isnan(lo)
        rows_arr = rr[ok].astype(float); lo_c = lo[ok]; hi_c = hi[ok]
        sel = np.where(pb.free & (V0[:, 2] > z_range[0]) & (V0[:, 2] < z_range[1]))[0]
        pb.contours.append((name, 'q3', rows_arr, lo_c, hi_c, w_s, tol_mm)); pb.contour_sel[name] = sel
