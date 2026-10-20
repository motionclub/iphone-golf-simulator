"""fit the lower-face loft half-width row a(z) (+ optional bowl / blend params) so that the analytic head's front-view jaw contour follows the plate's smooth silhouette (cubic fit)
python3 fit_contour.py [--smin 2] [--nf 1] [--free a,cxb,k1] -> data/fit_contour.json  (da knots, parameter deltas, residuals)"""
import sys, json, copy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, trial, contour as ct, fl, exp

ZK = np.arange(1.430, 1.5601, 0.010)                  # B-spline knots of the row correction
def bs3(t):
    t = np.abs(t); out = np.zeros_like(t)
    m1 = t < 1; m2 = (t >= 1) & (t < 2)
    out[m1] = 2 / 3 - t[m1] ** 2 + 0.5 * t[m1] ** 3
    out[m2] = (2 - t[m2]) ** 3 / 6
    return out
def basis(z):
    return np.stack([bs3((np.asarray(z) - zk) / 0.010) for zk in ZK], -1)          # (n, J)

def make(kw, coef=None, dpar=None):
    kw = dict(kw)
    for k, v in (dpar or {}).items(): kw[k] = v
    H, P = trial.make_H(**kw)
    if coef is not None:
        H.L.a = H.L.a + basis(H.L.zk) @ coef
    return H, P

if __name__ == '__main__':
    smin = 2; nf = 1
    kw0 = dict(nf_smooth=nf, smin=smin)
    zs = np.arange(1.447, 1.4911, 0.002); tg = ct.target_hw(zs)
    H0, P0 = make(kw0)
    base = P0['under']
    c0 = ct.contour_x(H0, zs)
    print('start: contour - target (mm): rms %.2f max %.2f' % (np.sqrt(np.mean((c0 - tg) ** 2)) * 1000, np.abs(c0 - tg).max() * 1000))
    J = len(ZK); free_par = [('cxb', base['cxb'], 0.3), ('k1', base['k1'], 0.004)]
    cols = []
    for j in range(J):
        c = np.zeros(J); c[j] = 0.002
        H, _ = make(kw0, coef=c); cols.append((ct.contour_x(H, zs) - c0) / 0.002)
    for name, v0, dv in free_par:
        H, _ = make(dict(kw0, **{name: v0 + dv})); cols.append((ct.contour_x(H, zs) - c0) / dv)
    Jm = np.stack(cols, 1)                              # (nz, J + npar)
    print('jacobian column peak response (contour mm per mm of a / per unit par):')
    for j in range(J): print('  a knot %.3f: peak %.2f at z=%.3f' % (ZK[j], np.abs(Jm[:, j]).max(), zs[np.argmax(np.abs(Jm[:, j]))]))
    for i, (name, _, _) in enumerate(free_par): print('  %s: peak %.3g' % (name, np.abs(Jm[:, J + i]).max()))
    np.savez('data/fit_contour_jac.npz', Jm=Jm, zs=zs, c0=c0, tg=tg)


def targets(H0, z_blend=(1.480, 1.505), z_hold=1.530):
    """jaw/cheek contour target: plate cubic fit below z_blend[0]; above it a monotone continuation whose slope decays from the cubic's to a constant chosen so that the contour meets
    the original skull contour at z_hold; original (ear-free) contour above z_hold and a weak hold below the plate range"""
    za, zb = z_blend
    zz = np.arange(za, z_hold + 1e-9, 0.0005)
    c = ct.target_coef(); s_a = np.polyval(np.polyder(c), za - 1.47); x_a = np.polyval(c, za - 1.47)
    o_hold = float(ct.contour_x(H0, [z_hold])[0])
    g = fl.sstep5(za, zb, zz)
    def integ(s_end):
        sl = s_a * (1 - g) + s_end * g
        return x_a + np.concatenate([[0.0], np.cumsum(0.5 * (sl[1:] + sl[:-1]) * np.diff(zz))])
    lo, hi = 0.0, 0.5
    for _ in range(50):                                   # bisection on s_end so that the integral hits the skull contour at z_hold
        mid = 0.5 * (lo + hi)
        if integ(mid)[-1] < o_hold: lo = mid
        else: hi = mid
    s_end = 0.5 * (lo + hi); xs = integ(s_end)
    zf = np.arange(1.447, za, 0.002); zc = np.arange(za, z_hold + 1e-9, 0.002)
    zh = np.arange(z_hold + 0.004, 1.5601, 0.004); zl = np.arange(1.432, 1.4461, 0.003)
    c_hi = ct.contour_x(H0, np.concatenate([zh, zl]))
    zs = np.concatenate([zf, zc, zh, zl]); tg = np.concatenate([ct.target_hw(zf), np.interp(zc, zz, xs), c_hi])
    wts = np.concatenate([np.ones(len(zf)), np.ones(len(zc)), np.ones(len(zh)), 0.5 * np.ones(len(zl))])
    print('target: slope at %.3f = %.3f -> end slope %.3f; skull contour at %.3f = %.1f mm' % (za, s_a, s_end, z_hold, o_hold * 1000))
    return zs, tg, wts


def solve(kw0, iters=4, lam2=0.02, lam0=0.004, lamp=(0.15, 0.15), free=('cxb', 'k1'), verbose=True, zs=None, tg=None, wts=None):
    """Gauss-Newton on (a-row B-spline coefficients, free parameters)"""
    H0, P0 = make(kw0); base = P0['under']
    if zs is None: zs, tg, wts = targets(H0)
    if wts is None: wts = np.ones(len(zs))
    J = len(ZK); coef = np.zeros(J); par = {k: base[k] for k in free}; scale = {'cxb': 1.0, 'k1': 0.010, 'cx': 1.0, 'kx': 0.02}
    D2 = np.zeros((J - 2, J))
    for i in range(J - 2): D2[i, i:i + 3] = (1, -2, 1)
    hist = []
    for it in range(iters):
        H, _ = make(kw0, coef=coef, dpar=par); c0 = ct.contour_x(H, zs); r0 = (c0 - tg) * wts
        hist.append(float(np.sqrt(np.mean(r0 ** 2)) * 1000))
        if verbose: print('iter %d: contour err rms %.2f mm max %.2f   cxb %.3f k1 %.4f   |da| max %.2f mm' % (it, hist[-1], np.abs(r0).max() * 1000, par.get('cxb', 0), par.get('k1', 0), np.abs(basis(H.L.zk) @ coef).max() * 1000))
        cols = []
        for j in range(J):
            c = coef.copy(); c[j] += 0.002
            Hj, _ = make(kw0, coef=c, dpar=par); cols.append((ct.contour_x(Hj, zs) - c0) * wts / 0.002)
        for k in free:
            dv = scale[k] * 0.05
            Hj, _ = make(kw0, coef=coef, dpar=dict(par, **{k: par[k] + dv})); cols.append((ct.contour_x(Hj, zs) - c0) * wts / dv)
        Jm = np.stack(cols, 1) * 1000.0                        # mm of contour per unit (m of a, unit of par)
        npar = len(free)
        # unknown increments: dcoef (m), dpar ; residual in mm
        A = [Jm]; b = [-r0 * 1000.0]
        A.append(np.sqrt(lam2) * 1000.0 * np.hstack([D2, np.zeros((J - 2, npar))])); b.append(-np.sqrt(lam2) * 1000.0 * (D2 @ coef))
        A.append(np.sqrt(lam0) * 1000.0 * np.hstack([np.eye(J), np.zeros((J, npar))])); b.append(-np.sqrt(lam0) * 1000.0 * coef)
        for i, k in enumerate(free):
            row = np.zeros((1, J + npar)); row[0, J + i] = np.sqrt(lamp[i]) / scale[k]
            A.append(row); b.append(np.array([-np.sqrt(lamp[i]) / scale[k] * (par[k] - base[k])]))
        A = np.vstack(A); b = np.concatenate(b)
        dx = np.linalg.lstsq(A, b, rcond=None)[0]
        coef = coef + 0.8 * dx[:J]
        for i, k in enumerate(free): par[k] = par[k] + 0.8 * dx[J + i]
    H, _ = make(kw0, coef=coef, dpar=par); c0 = ct.contour_x(H, zs); r0 = (c0 - tg) * wts
    if verbose: print('final: contour err rms %.2f mm max %.2f' % (np.sqrt(np.mean(r0 ** 2)) * 1000, np.abs(r0).max() * 1000))
    return coef, par, r0, H

if __name__ == '__main__' and '--solve' in sys.argv:
    kw0 = dict(nf_smooth=1, smin=2)
    coef, par, r0, H = solve(kw0)
    print('coef (mm):', np.round(coef * 1000, 2)); print('par', par)
    json.dump(dict(ZK=ZK.tolist(), coef=coef.tolist(), par=par), open('data/fit_contour.json', 'w'), indent=1)
