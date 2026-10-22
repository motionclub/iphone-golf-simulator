"""Torso photometric mesh optimisation (PMO), y-displacements only (front/back outline cannot change), numpy only.
Model: dy_i = -wf_i * (G cF)_i + wb_i * (G cB)_i  (G = mirror-symmetric Gaussian RBFs in (x,z), tapered at the zone border),
shading = SH2(n_i) . c_view  (lighting fitted on the UNTOUCHED limbs), residual = sqrt(w) * H (plate_lum - shading), H = graph high-pass."""
import sys, math, time
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso2')
from plateview import View, PLATE, gblur, bilinear, vertex_normals, visible, F as FACES
from zone import zone_mask

def sstep(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def sh2s(N):
    x, y, z = N[:, 0], N[:, 1], N[:, 2]; return np.stack([np.ones_like(x), y, z, y * z, 3 * z * z - 1, x * x - y * y], 1)

class Torso:
    def __init__(self, V0, plate_sigma=2.5, hp_iters=3, fit_light_on='outside', top_taper=(1.33, 0.06)):
        self.V0 = V0.copy(); self.n = len(V0); self.Z = zone_mask(V0); self.zi = np.where(self.Z)[0]; self.nz = len(self.zi)
        self.zloc = -np.ones(self.n, int); self.zloc[self.zi] = np.arange(self.nz)
        # faces touching the zone, split tri/quad (global indices)
        fs = [f for f in FACES if any(self.Z[i] for i in f)]
        self.tri = np.array([f for f in fs if len(f) == 3], np.int64).reshape(-1, 3); self.quad = np.array([f for f in fs if len(f) == 4], np.int64).reshape(-1, 4)
        self.N0 = vertex_normals(V0)
        # front/back depth-fraction weights (same construction as the sculpt)
        x, y, z = V0[:, 0], V0[:, 1], V0[:, 2]
        zz = np.arange(0.76, 1.42, 0.005); yc = np.zeros(len(zz)); hd = np.zeros(len(zz))
        for i, zf in enumerate(zz):
            m = (np.abs(z - zf) < 0.008) & (np.abs(x) < 0.09); yc[i] = 0.5 * (y[m].min() + y[m].max()); hd[i] = 0.5 * (y[m].max() - y[m].min())
        k = np.ones(5) / 5; yc = np.convolve(np.pad(yc, 2, mode='edge'), k, 'valid'); hd = np.convolve(np.pad(hd, 2, mode='edge'), k, 'valid')
        u = (y - np.interp(z, zz, yc)) / np.interp(z, zz, hd)
        self.wf = sstep((-u - 0.12) / 0.55); self.wb = sstep((u - 0.12) / 0.55)
        ax = np.abs(x)
        self.taper = (1 - sstep((ax - 0.15) / 0.07)) * sstep((z - 0.775) / 0.04) * (1 - sstep((z - top_taper[0]) / top_taper[1])) * self.Z
        # views
        self.views = {}; self.plate_blur = gblur(PLATE, plate_sigma); self.hp_iters = hp_iters
        body = (V0[:, 2] < 1.40) & (np.abs(x) < 0.40)
        for name in ('front', 'back'):
            vw = View(name); vis = visible(vw, V0, self.N0, sel=V0[:, 2] < 1.40)
            col, row = vw.project(V0); I = bilinear(self.plate_blur, col, row)
            fit = vis & body & ~self.Z
            c, *_ = np.linalg.lstsq(sh2s(self.N0[fit]), I[fit], rcond=None)           # lighting from the untouched limbs only
            wdata = vis & self.Z & (np.abs(x) < 0.20) & (z > 0.795) & (z < 1.375)
            wgt = np.clip(self.N0 @ vw.toward, 0, 1) * (1 - sstep((ax - 0.14) / 0.06)) * sstep((z - 0.795) / 0.03) * (1 - sstep((z - 1.345) / 0.03))
            sel = np.where(wdata & (wgt > 0.02))[0]
            self.views[name] = dict(vw=vw, c=c, I=I[sel], sel=sel, w=np.sqrt(wgt[sel]), HP=self._hp(sel), basis=sh2s)
        self.m_res = sum(len(v['sel']) for v in self.views.values())
    def add_yaw_view(self, name, cal, blur=1.1, weight=1.0):
        """add a sheet 3/4 panel (camera-frame SH lighting fitted on the untouched limbs) to the FIT set"""
        from plateview import ViewYaw, SHEET, visible_gen, sh2c
        V0 = self.V0; x = V0[:, 0]; z = V0[:, 2]; ax = np.abs(x)
        vw = ViewYaw(name, cal['yaw'], cal['col0'], cal['mpp'], cal['sole_row']); vis = visible_gen(vw, V0, self.N0, sel=V0[:, 2] < 1.40, res=1.0, rad=1)
        col, row = vw.project(V0); I = bilinear(gblur(SHEET, blur), col, row); body = (V0[:, 2] < 1.40) & (np.abs(x) < 0.62)
        A = sh2c(self.N0, vw); fit = vis & body & ~self.Z; c, *_ = np.linalg.lstsq(A[fit], I[fit], rcond=None)
        wgt = np.clip(self.N0 @ vw.toward, 0, 1) * (1 - sstep((ax - 0.14) / 0.06)) * sstep((z - 0.795) / 0.03) * (1 - sstep((z - 1.345) / 0.03))
        sel = np.where(vis & self.Z & (wgt > 0.05))[0]
        self.views[name] = dict(vw=vw, c=c, I=I[sel], sel=sel, w=np.sqrt(wgt[sel]) * weight, HP=self._hp(sel), basis=(lambda N, vw=vw: sh2c(N, vw)))
        self.m_res = sum(len(v['sel']) for v in self.views.values())
    # ---- graph high-pass on the selected subgraph
    def _hp(self, sel):
        loc = -np.ones(self.n, int); loc[sel] = np.arange(len(sel))
        a = []; b = []
        for f in FACES:
            m = len(f)
            for k in range(m):
                i, j = f[k], f[(k + 1) % m]
                if loc[i] >= 0 and loc[j] >= 0: a.append(loc[i]); b.append(loc[j])
        a = np.array(a); b = np.array(b); ii = np.concatenate([a, b]); jj = np.concatenate([b, a])
        order = np.argsort(ii, kind='stable'); ii = ii[order]; jj = jj[order]
        deg = np.bincount(ii, minlength=len(sel)).astype(float)
        return dict(ii=ii, jj=jj, deg=np.maximum(deg, 1), n=len(sel), has=deg > 0)
    def hp(self, x, HP):
        y = x
        for _ in range(self.hp_iters):
            if y.ndim == 1: s = np.bincount(HP['ii'], weights=y[HP['jj']], minlength=HP['n'])
            else: s = np.stack([np.bincount(HP['ii'], weights=y[HP['jj'], c], minlength=HP['n']) for c in range(y.shape[1])], 1)
            avg = s / (HP['deg'] if y.ndim == 1 else HP['deg'][:, None]); avg = np.where((HP['has'] if y.ndim == 1 else HP['has'][:, None]), avg, y)
            y = 0.5 * y + 0.5 * avg
        return x - y
    # ---- basis
    def make_basis(self, spacing=0.012, sigma=0.009, spacing_z=None, sigma_z=None, cleft=False):
        spz = spacing if spacing_z is None else spacing_z; sgz = sigma if sigma_z is None else sigma_z
        cs = []
        for cz in np.arange(0.78, 1.395, spz):
            for cx in np.arange(0.0, 0.215, spacing): cs.append((cx, cz))
        C = np.array(cs); P = self.V0[self.zi]; G = np.zeros((self.nz, len(C)))
        for k, (cx, cz) in enumerate(C):
            g = np.exp(-0.5 * (((P[:, 0] - cx) / sigma) ** 2 + ((P[:, 2] - cz) / sgz) ** 2))
            if cx > 1e-6: g = g + np.exp(-0.5 * (((P[:, 0] + cx) / sigma) ** 2 + ((P[:, 2] - cz) / sgz) ** 2))
            G[:, k] = g
        keep = G.max(0) > 0.2; self.C = C[keep]; self.G = G[:, keep]; self.n_main = self.G.shape[1]
        if cleft:        # extra narrow midline basis (back group is the intended user; the front copies get a huge ridge)
            ez = np.arange(0.805, 0.905, 0.008); E = np.zeros((self.nz, len(ez)))
            for k, cz in enumerate(ez): E[:, k] = np.exp(-0.5 * (((P[:, 0]) / 0.006) ** 2 + ((P[:, 2] - cz) / 0.007) ** 2))
            self.C = np.concatenate([self.C, np.stack([np.zeros(len(ez)), ez], 1)]); self.G = np.concatenate([self.G, E], axis=1)
        self.m = self.G.shape[1]
        self.BF = -(self.wf[self.zi] * self.taper[self.zi])[:, None] * self.G          # dy per unit front-outward coefficient (mm -> applied *1e-3)
        self.BB = (self.wb[self.zi] * self.taper[self.zi])[:, None] * self.G
        return self.m
    def dy_mm(self, cF, cB): return self.BF @ cF + self.BB @ cB
    def positions(self, dy_mm):
        P = self.V0.copy(); P[self.zi, 1] += dy_mm * 1e-3; return P
    # ---- angle-weighted normals of the zone vertices
    def normals(self, P):
        n = np.zeros((self.n, 3))
        def acc(idx, vec, ang):
            for c in range(3): n[:, c] += np.bincount(idx, weights=vec[:, c] * ang, minlength=self.n)
        if len(self.tri):
            a, b, c = (P[self.tri[:, k]] for k in range(3)); fn = np.cross(b - a, c - a); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-18)
            def ang(p, q, r):
                u = q - p; v = r - p; return np.arccos(np.clip((u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-18), -1, 1))
            acc(self.tri[:, 0], fn, ang(a, b, c)); acc(self.tri[:, 1], fn, ang(b, c, a)); acc(self.tri[:, 2], fn, ang(c, a, b))
        if len(self.quad):
            a, b, c, d = (P[self.quad[:, k]] for k in range(4)); fn = np.cross(c - a, d - b); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-18)
            def ang(p, q, r):
                u = q - p; v = r - p; return np.arccos(np.clip((u * v).sum(1) / np.maximum(np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1), 1e-18), -1, 1))
            acc(self.quad[:, 0], fn, ang(a, b, d)); acc(self.quad[:, 1], fn, ang(b, c, a)); acc(self.quad[:, 2], fn, ang(c, d, b)); acc(self.quad[:, 3], fn, ang(d, a, c))
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18); return n
    def residual_parts(self, cF, cB, P=None):
        P = self.positions(self.dy_mm(cF, cB)) if P is None else P; N = self.normals(P); out = []
        for name, v in self.views.items():
            M = v['basis'](N[v['sel']]) @ v['c']; out.append(v['w'] * self.hp(v['I'] - M, v['HP']))
        return out
    def residual(self, cF, cB): return np.concatenate(self.residual_parts(cF, cB))
    def score(self, cF, cB):
        """plain (not high-passed) correlation of model shading with plate over the data set, per view"""
        P = self.positions(self.dy_mm(cF, cB)); N = self.normals(P); out = {}
        for name, v in self.views.items():
            M = v['basis'](N[v['sel']]) @ v['c']; a = self.hp(v['I'], v['HP']); b = self.hp(M, v['HP']); out[name] = float(np.corrcoef(a, b)[0, 1])
        return out

def color_classes_2d(C, D):
    """class id per centre so that members of one class are >= D apart (one member per cell, 4 cell-parity classes)"""
    ci = np.floor(C[:, 0] / D).astype(int); cj = np.floor(C[:, 1] / D).astype(int); par = (ci & 1) + 2 * (cj & 1)
    key = (ci - ci.min()) * 1000 + (cj - cj.min()); order = np.lexsort((np.arange(len(C)), key)); k = np.zeros(len(C), int); ks = key[order]
    start = np.r_[0, np.where(np.diff(ks) != 0)[0] + 1]
    for a, b in zip(start, np.r_[start[1:], len(C)]): k[order[a:b]] = np.arange(b - a)
    return par * (k.max() + 1) + k
def fd_jacobian(T, cF, cB, delta=0.25, D=0.12):
    """J (n_res x 2m) dense: perturb one coefficient per cell per class, attribute each changed row to the nearest perturbed centre (mirrored distance)."""
    r0 = T.residual(cF, cB); m = T.m; J = np.zeros((len(r0), 2 * m))
    pos = np.concatenate([T.V0[v['sel']][:, [0, 2]] for v in T.views.values()])
    cls = color_classes_2d(T.C, D)
    for grp in (0, 1):
        for c in np.unique(cls):
            mem = np.where(cls == c)[0]
            cF2, cB2 = cF.copy(), cB.copy(); (cF2 if grp == 0 else cB2)[mem] += delta
            r1 = T.residual(cF2, cB2); dr = (r1 - r0) / delta; nz = np.where(np.abs(dr) > 1e-9)[0]
            if len(nz) == 0: continue
            Cm = T.C[mem]; d1 = ((pos[nz, None, :] - Cm[None, :, :]) ** 2).sum(2); d2 = ((pos[nz, None, :] - (Cm * np.array([-1.0, 1.0]))[None, :, :]) ** 2).sum(2)
            j = np.argmin(np.minimum(d1, d2), axis=1); J[nz, grp * m + mem[j]] = dr[nz]
    return J, r0

def solve_lm(T, cF0, cB0, lam=60.0, lam_vec=None, hmax=6.0, kappa=3000.0, iters=8, mu0=0.5, delta=0.25, D=0.12, verbose=True):
    m = T.m; c = np.concatenate([cF0, cB0]); lv = np.ones(2 * m) if lam_vec is None else (np.asarray(lam_vec) if len(lam_vec) == 2 * m else np.concatenate([lam_vec, lam_vec])); mu = mu0
    def split(cc): return cc[:m], cc[m:]
    def energy(cc):
        cF, cB = split(cc); r = T.residual(cF, cB); dy = T.dy_mm(cF, cB); over = np.maximum(np.abs(dy) - hmax, 0)
        return 0.5 * float(r @ r) + 0.5 * lam * float((lv * cc * cc).sum()) + 0.5 * kappa * float(over @ over), float(r @ r)
    E0, rr0 = energy(c)
    if verbose: print('  start: E %.5g data %.5g (rms %.3f) ' % (E0, rr0, math.sqrt(rr0 / T.m_res)))
    for it in range(iters):
        cF, cB = split(c); t0 = time.time(); J, r0 = fd_jacobian(T, cF, cB, delta=delta, D=D)
        dy = T.dy_mm(cF, cB); act = (np.abs(dy) > hmax); sgn = np.sign(dy) * np.maximum(np.abs(dy) - hmax, 0)
        BF, BB = T.BF, T.BB; Bfull = np.concatenate([BF, BB], axis=1)
        A0 = J.T @ J + lam * np.diag(lv) + kappa * (Bfull[act].T @ Bfull[act]); g = J.T @ r0 + lam * lv * c + kappa * (Bfull.T @ sgn)
        acc = False
        for tr in range(8):
            dc = np.linalg.solve(A0 + mu * np.diag(np.diag(A0) + 1e-9), -g); cn = c + dc; En, rrn = energy(cn)
            if En < E0: acc = True; break
            mu *= 6.0
        if not acc:
            if verbose: print('  iter %d: no decrease (mu %.3g)' % (it, mu))
            break
        if verbose: print('  iter %d: %.1fs mu %.3g |dc|max %.2f  max|dy| %.2f mm  E %.5g -> %.5g  data rms %.3f' % (it, time.time() - t0, mu, np.abs(dc).max(), np.abs(T.dy_mm(*split(cn))).max(), E0, En, math.sqrt(rrn / T.m_res)))
        rel = (E0 - En) / abs(E0); c = cn; E0 = En; mu = max(mu / 4, 1e-3)
        if rel < 1.5e-3: break
    return split(c)
