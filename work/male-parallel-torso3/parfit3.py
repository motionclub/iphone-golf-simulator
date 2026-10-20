"""Parametric feature fit: the struct3 anatomical fields (pec lift, shelf, sternum, linea, iliac V, oblique, cleft, lobes) with their position/width/amplitude
parameters fitted to the plate-lit shading (same residual as the RBF solve, with relief gain).  Bounded damped Gauss-Newton, FD Jacobian (few parameters).
python3.13 parfit3.py <tag> [json: {"gF":..,"gB":..,"free":[feature names],"hp":3,"fix":{...}}]  -> data/V_<tag>.npy , data/params_<tag>.json"""
import sys, json, time, copy
import numpy as np
sys.path.insert(0, '.')
import struct3
from pmo3 import *

# parameter table: (feature, key, lo, hi)
SPEC = {
    'pec_lift': [('A', 0, 9), ('x0', .05, .14), ('sx', .018, .06), ('z0', 1.19, 1.28), ('sz', .015, .05)],
    'shelf':    [('A', 0, 8), ('zc0', 1.14, 1.21), ('zc_curve', 0.0, .10), ('sz', .008, .022), ('xc', 0.0, 1.0)],
    'sternum':  [('A', 0, 5)],
    'linea':    [('A', 0, 4)],
    'iliac':    [('A', 0, 7), ('s', .006, .02), ('x1', .12, .19), ('z1', .90, 1.02), ('x2', .0, .06), ('z2', .83, .93)],
    'oblique':  [('A', 0, 5), ('s', .006, .02), ('x0', .08, .17)],
    'cleft':    [('A', 0, 14), ('z_pk0', .80, .86), ('z_pk1', .83, .92), ('z_hi', .90, 1.0), ('s_lo', .005, .02), ('s_hi', .008, .03)],
    'cleft2':   [('a%d' % i, 0, 18) for i in range(8)] + [('s_top', .004, .012), ('s_bot', .006, .022)],
    'lobes':    [('A', 0, 8), ('x0', .04, .11), ('sx', .02, .06), ('z0', .82, .91), ('sz', .02, .06)],
}
def flat(P, free):
    names, x0, lo, hi = [], [], [], []
    for f in free:
        for k, a, b in SPEC[f]: names.append((f, k)); x0.append(P[f][k]); lo.append(a); hi.append(b)
    return names, np.array(x0, float), np.array(lo, float), np.array(hi, float)
def unflat(P, names, x):
    Q = copy.deepcopy(P)
    for (f, k), v in zip(names, x): Q[f][k] = float(v)
    return Q

def make_gain(gF, gB):
    def gfn(name, x, z):
        g = gF if name == 'front' else gB
        zr = [(1.12, 1.135, 1.265, 1.285), (0.90, 0.92, 1.10, 1.13), (0.78, 0.80, 0.89, 0.915)] if name == 'front' else [(1.12, 1.14, 1.30, 1.33), (0.90, 0.93, 1.10, 1.13), (0.77, 0.79, 0.90, 0.935)]
        out = np.ones_like(z)
        for gi, (a, b, c, d) in zip(g, zr): out = out + (gi - 1.0) * ramp(z, a, b, c, d)
        return out
    return gfn

def build(V, P, T, lo_b=None, hi_b=None):
    hF, hB = struct3.fields(V, P); dy = (-T.wf * hF + T.wb * hB) * T.taper * 1e-3
    if lo_b is not None:           # clamp into the silhouette-extreme bounds (mm) on zone vertices
        d = dy[T.zi] * 1000; d = np.clip(d, lo_b, hi_b); dy = dy.copy(); dy[T.zi] = d * 1e-3
    Vn = V.copy(); Vn[:, 1] += dy; return Vn

def lm_param(T, V, P0, free, lo_b, hi_b, iters=12, lam_prior=0.0, verbose=True, step_rel=0.02, prior_rows=None):
    names, x, lo, hi = flat(P0, free); span = hi - lo
    def res(xv):
        P = unflat(P0, names, np.clip(xv, lo, hi)); Vn = build(V, P, T, lo_b, hi_b); r = np.concatenate(T.residual_parts(None, None, P=Vn))
        if prior_rows is not None: r = np.concatenate([r, prior_rows(P)])
        return r
    r0 = res(x); E0 = float(r0 @ r0); mu = 1.0
    if verbose: print('  param LM start: %d params, E %.4g' % (len(x), E0))
    for it in range(iters):
        t0 = time.time(); J = np.zeros((len(r0), len(x)))
        for j in range(len(x)):
            h = step_rel * span[j]; xp = x.copy(); xp[j] = min(x[j] + h, hi[j]);
            if xp[j] == x[j]: xp[j] = x[j] - h
            J[:, j] = (res(xp) - r0) / (xp[j] - x[j])
        A = J.T @ J; g = J.T @ r0; acc = False
        for tr in range(8):
            dx = -np.linalg.solve(A + mu * np.diag(np.diag(A) + 1e-12), g); xn = np.clip(x + dx, lo, hi); rn = res(xn); En = float(rn @ rn)
            if En < E0: acc = True; break
            mu *= 5.0
        if not acc:
            if verbose: print('  iter %d: no decrease' % it)
            break
        if verbose: print('  iter %d: %.1fs mu %.3g E %.5g -> %.5g' % (it, time.time() - t0, mu, E0, En))
        rel = (E0 - En) / E0; x = xn; r0 = rn; E0 = En; mu = max(mu / 3, 1e-4)
        if rel < 2e-3: break
    return unflat(P0, names, x), x, names

if __name__ == '__main__':
    tag = sys.argv[1]; cfg = dict(base='base', gF=[1.0, 1.0, 1.0], gB=[1.0, 1.0, 1.0], free=['pec_lift', 'shelf', 'iliac', 'oblique', 'cleft', 'lobes'], hp=3, hmax=14.0, iters=12, init=None, fix={})
    if len(sys.argv) > 2: cfg.update(json.loads(sys.argv[2]))
    P0 = copy.deepcopy(struct3.P_)
    if cfg['init']: P0 = json.load(open(cfg['init']))
    for f in ('pec_lift', 'shelf', 'sternum', 'linea', 'iliac', 'oblique', 'cleft', 'lobes'):
        if f not in cfg['free'] and f not in cfg.get('keep', []): P0[f]['A'] = 0.0
    for f, kv in cfg['fix'].items(): P0[f].update(kv)
    V = np.load('data/V_%s.npy' % cfg.get('base', 'base')); T = Torso3(V, gain_fn=make_gain(cfg['gF'], cfg['gB']), hp_iters=cfg['hp'], xtaper=tuple(cfg.get('xtaper', (0.125, 0.075))))
    lo_b, hi_b = extreme_bounds(T, cfg['hmax'], tol_mm=0.4)
    t0 = time.time(); P, x, names = lm_param(T, V, P0, cfg['free'], lo_b, hi_b, iters=cfg['iters'])
    Vn = build(V, P, T, lo_b, hi_b); Pg, dF, dB = deficit_guard(Vn, V, T, sigma=0.008, n=3)
    np.save(f'data/V_{tag}.npy', Pg); json.dump(P, open(f'data/params_{tag}.json', 'w'), indent=1); json.dump(cfg, open(f'data/cfg_{tag}.json', 'w'), indent=1)
    d = (Pg[:, 1] - V[:, 1]) * 1000
    print(tag, 'time %.0fs dy [%.1f, %.1f] mm moved %d' % (time.time() - t0, d.min(), d.max(), int(np.any(Pg != V, axis=1).sum())))
    for f in cfg['free']: print('  ', f, {k: round(P[f][k], 4) for k, _, _ in SPEC[f]})
    print(tag, 'plate-lit HP corr:', {k: round(v, 3) for k, v in T.score_hp(Pg, {'chest': (1.15, 1.32), 'abd': (0.90, 1.15), 'pel': (0.80, 0.90)}).items() if 'amp' not in k})
