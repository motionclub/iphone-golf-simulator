"""FORM3 photometric torso optimiser (extends FORM2's pmo_t).  y-displacements only, numpy only (run with Blender's python3.13).
Differences to FORM2:
  * start mesh = installed FORM2 mesh (V0), unknowns = additional mirror-symmetric Gaussian-RBF y-fields
  * plate target high-pass is multiplied by a per-region RELIEF GAIN (stronger masses, same feature layout as the plate)
  * per-vertex bounds lo<=dy<=hi: |dy|<=hmax AND the silhouette extremes (front-most / back-most y per height slab of the start mesh) cannot be exceeded
    (inequality inside the solve -> the pec crest may rise to the extreme, no whole-slab shifting that flattens relief)
  * optional extra linear least-squares rows (feature priors) and per-coefficient ridge multipliers
"""
import sys, math, time
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3')
from pmo_t import *          # Torso, sstep, sh2s, fd_jacobian, color_classes_2d ...
from slab import extremes

class Torso3(Torso):
    def __init__(self, V0, gain_fn=None, plate_sigma=2.5, hp_iters=3, top_taper=(1.325, 0.025), zfloor=(0.782, 0.03), views_gain=None, xtaper=(0.125, 0.075), xtap=(0.14, 0.06), gain_mode='all', fine_iters=1):
        super().__init__(V0, plate_sigma=plate_sigma, hp_iters=hp_iters, top_taper=top_taper)
        x = V0[:, 0]; z = V0[:, 2]; ax = np.abs(x)
        # FORM3 moves only |x| < 0.20 (the hands/arm chat owns the shoulder-ball overlap |x| >= 0.215): own x-taper
        self.taper = (1 - sstep((ax - xtaper[0]) / xtaper[1])) * sstep((z - 0.775) / 0.04) * (1 - sstep((z - top_taper[0]) / top_taper[1])) * self.Z
        # re-select the data set with a lower floor ramp (glute band) - otherwise identical to Torso.__init__
        for name, v in list(self.views.items()):
            vw = v['vw']; N0 = self.N0
            from plateview import visible, bilinear
            vis = visible(vw, V0, N0, sel=V0[:, 2] < 1.40)
            wdata = vis & self.Z & (ax < 0.20) & (z > zfloor[0]) & (z < 1.375)
            wgt = np.clip(N0 @ vw.toward, 0, 1) * (1 - sstep((ax - xtap[0]) / xtap[1])) * sstep((z - zfloor[0]) / zfloor[1]) * (1 - sstep((z - 1.345) / 0.03))
            col, row = vw.project(V0); I = bilinear(self.plate_blur, col, row)
            sel = np.where(wdata & (wgt > 0.02))[0]
            self.views[name] = dict(vw=vw, c=v['c'], I=I[sel], sel=sel, w=np.sqrt(wgt[sel]), HP=self._hp(sel), basis=sh2s)
        self.m_res = sum(len(v['sel']) for v in self.views.values())
        self.gain_fn = gain_fn
        for name, v in self.views.items():
            g = np.ones(len(v['sel'])) if gain_fn is None else gain_fn(name, V0[v['sel'], 0], V0[v['sel'], 2])
            v['gain'] = g
            if gain_mode == 'mid':        # amplify only the mid band (HP_full - HP_fine); the fine band (noise-prone, <~10 mm) stays at 1x
                hf = self.hp(v['I'], v['HP'], iters=fine_iters); hfull = self.hp(v['I'], v['HP']); v['HPI'] = hf + g * (hfull - hf)
            else: v['HPI'] = g * self.hp(v['I'], v['HP'])
    active = None
    def residual_parts(self, cF, cB, P=None):
        P = self.positions(self.dy_mm(cF, cB)) if P is None else P; N = self.normals(P); out = []
        for name, v in self.views.items():
            if self.active is not None and name not in self.active: continue
            M = v['basis'](N[v['sel']]) @ v['c']; out.append(v['w'] * (v['HPI'] - self.hp(M, v['HP'])))
        return out
    def score_hp(self, P=None, regions=None):
        """high-passed shading correlation (plate vs model) per view, optionally per z-region"""
        P = self.V0 if P is None else P; N = self.normals(P); out = {}
        for name, v in self.views.items():
            M = v['basis'](N[v['sel']]) @ v['c']; a = self.hp(v['I'], v['HP']); b = self.hp(M, v['HP']); out[name] = float(np.corrcoef(a, b)[0, 1])
            zz = self.V0[v['sel'], 2]
            for rn, (z0, z1) in (regions or {}).items():
                m = (zz >= z0) & (zz < z1) & (np.abs(self.V0[v['sel'], 0]) < 0.12)
                out[f'{name}_{rn}'] = float(np.corrcoef(a[m], b[m])[0, 1]); out[f'{name}_{rn}_amp'] = float(np.std(b[m]) / max(np.std(a[m]), 1e-9))
        return out

def extreme_bounds(T, hmax_mm, tol_mm=0.4, half=0.006, smooth_z=0.0, zs=None):
    """per zone vertex lower/upper bounds (mm) on dy: |dy|<=hmax and y stays within the start mesh's slab extremes (+tol)."""
    V0 = T.V0; Z = T.Z; zs = np.arange(0.775, 1.40, 0.0025) if zs is None else zs
    F, B = extremes(V0, Z, zs, half=half, xmax=0.20)
    ok = ~np.isnan(F)
    Fz = np.interp(V0[:, 2], zs[ok], F[ok]); Bz = np.interp(V0[:, 2], zs[ok], B[ok])
    hf = (V0[:, 1] - Fz) * 1000 + tol_mm       # how far FORWARD (-y) the vertex may still move
    hb = (Bz - V0[:, 1]) * 1000 + tol_mm       # how far BACKWARD (+y)
    hf = np.maximum(hf, 0); hb = np.maximum(hb, 0)
    lo = -np.minimum(hmax_mm, hf); hi = np.minimum(hmax_mm, hb)
    return lo[T.zi], hi[T.zi]

def solve_lm3(T, cF0, cB0, lam=0.1, lam_vec=None, lo=None, hi=None, kappa=3000.0, iters=10, mu0=0.5, delta=0.25, D=0.12, verbose=True, extra=None, tol_rel=1.5e-3, callback=None):
    """extra: optional (A, b, w): w*(A@[cF;cB] - b) appended as residual rows (dense A, rows x 2m)"""
    m = T.m; c = np.concatenate([cF0, cB0]); lv = np.ones(2 * m) if lam_vec is None else (np.asarray(lam_vec) if len(lam_vec) == 2 * m else np.concatenate([lam_vec, lam_vec])); mu = mu0
    Bfull = np.concatenate([T.BF, T.BB], axis=1)
    def split(cc): return cc[:m], cc[m:]
    def over_of(cc):
        dy = Bfull @ cc
        up = np.maximum(dy - hi, 0) if hi is not None else 0 * dy; dn = np.maximum(lo - dy, 0) if lo is not None else 0 * dy
        return up, dn
    def extra_res(cc):
        if extra is None: return np.zeros(0)
        A, b, w = extra; return w * (A @ cc - b)
    def energy(cc):
        cF, cB = split(cc); r = T.residual(cF, cB); up, dn = over_of(cc); er = extra_res(cc)
        return 0.5 * float(r @ r) + 0.5 * float(er @ er) + 0.5 * lam * float((lv * cc * cc).sum()) + 0.5 * kappa * float(up @ up + dn @ dn), float(r @ r)
    E0, rr0 = energy(c)
    if verbose: print('  start: E %.5g data %.5g (rms %.3f)' % (E0, rr0, math.sqrt(rr0 / T.m_res)))
    for it in range(iters):
        cF, cB = split(c); t0 = time.time(); J, r0 = fd_jacobian(T, cF, cB, delta=delta, D=D)
        up, dn = over_of(c); act = (up > 0) | (dn > 0); sgn = up - dn
        A0 = J.T @ J + lam * np.diag(lv) + kappa * (Bfull[act].T @ Bfull[act]); g = J.T @ r0 + lam * lv * c + kappa * (Bfull.T @ sgn)
        if extra is not None:
            A, b, w = extra; A0 = A0 + (w * w) * (A.T @ A) if np.isscalar(w) else A0 + A.T @ ((w * w)[:, None] * A); g = g + (w * w) * (A.T @ (A @ c - b)) if np.isscalar(w) else g + A.T @ ((w * w) * (A @ c - b))
        acc = False
        for tr in range(8):
            dc = np.linalg.solve(A0 + mu * np.diag(np.diag(A0) + 1e-9), -g); cn = c + dc; En, rrn = energy(cn)
            if En < E0: acc = True; break
            mu *= 6.0
        if not acc:
            if verbose: print('  iter %d: no decrease (mu %.3g)' % (it, mu))
            break
        dyn = Bfull @ cn
        if verbose: print('  iter %d: %.1fs mu %.3g |dc|max %.2f  dy[%.1f,%.1f] mm  E %.5g -> %.5g  data rms %.3f' % (it, time.time() - t0, mu, np.abs(dc).max(), dyn.min(), dyn.max(), E0, En, math.sqrt(rrn / T.m_res)))
        rel = (E0 - En) / abs(E0); c = cn; E0 = En; mu = max(mu / 4, 1e-3)
        if callback is not None: callback(it, c.copy())
        if rel < tol_rel: break
    return split(c)

def deficit_guard(Vnew, Vref, T, sigma=0.008, n=3, mode='deficit', zlo=0.80, zhi=1.318, tol_mm=0.0):
    """restore slab extremes that RECEDED (mode 'deficit': only shifts toward the reference extreme, never pulls an overshoot back) - smoothed slab-wide shift of front/back weighted vertices."""
    Z = T.Z; zs = np.arange(0.775, 1.40, 0.0025); V = Vnew.copy(); wf, wb = T.wf, T.wb
    F0, B0 = extremes(Vref, Z, zs)
    k = int(3 * sigma / 0.0025); xs = np.arange(-k, k + 1) * 0.0025; wk = np.exp(-0.5 * (xs / sigma) ** 2); wk /= wk.sum()
    def sm(a): a = np.where(np.isnan(a), 0.0, a); return np.convolve(np.pad(a, k, mode='edge'), wk, 'valid')
    for _ in range(n):
        F1, B1 = extremes(V, Z, zs)
        dF = F0 - F1; dB = B0 - B1                       # dF<0: front receded (needs -y shift); dB>0: back receded (needs +y shift)
        if mode == 'deficit': dF = np.minimum(dF, 0); dB = np.maximum(dB, 0)
        dF = np.where(np.abs(dF) < tol_mm * 1e-3, 0, dF); dB = np.where(np.abs(dB) < tol_mm * 1e-3, 0, dB)
        dF = sm(dF); dB = sm(dB); z = V[:, 2]; ax = np.abs(V[:, 0])
        tz = sstep((z - zlo) / 0.03) * (1 - sstep((z - zhi) / 0.03)); tx = 1 - sstep((ax - 0.13) / 0.07)          # zero at |x| = 0.20: the shoulder-ball overlap (|x| >= 0.215) belongs to the arms chat
        V[:, 1] += (wf * np.interp(z, zs, dF) + wb * np.interp(z, zs, dB)) * tz * tx * Z * (ax < 0.2)
    F1, B1 = extremes(V, Z, zs); return V, F1 - F0, B1 - B0

def ramp(z, a, b, c, d):
    """0 below a, rises to 1 at b, 1 until c, falls to 0 at d"""
    return sstep((z - a) / max(b - a, 1e-9)) * (1 - sstep((z - c) / max(d - c, 1e-9)))
