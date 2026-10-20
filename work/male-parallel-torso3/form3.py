"""FORM3 builder: FORM2 mesh -> (gain-driven photometric RBF refit) + (structural features) -> extreme clamp -> deficit guard.  positions-only, y-only, torso zone only.
python3.13 form3.py <tag> [json cfg]      -> data/V_<tag>.npy, data/params_<tag>.json
cfg keys: order ('rbf_first'|'struct_first'), rbf: {gF,gB,lamF,lamB,lam,hmax,iters,tol,zfloor}, struct: {feature:{param:val}}, only_struct: [features kept], clamp_tol (mm), guard_sigma, guard_n"""
import sys, json, time, copy
import numpy as np
sys.path.insert(0, '.')
import struct3
from pmo3 import *
from parfit3 import make_gain

DEF = dict(order='rbf_first',
           rbf=dict(gF=[3.5, 2.6, 2.2], gB=[2.2, 2.0, 3.5], lamF=[0.25, 0.5, 1.0], lamB=[0.2, 0.5, 0.5], lam=0.1, hmax=14.0, iters=12, tol=0.4, zfloor=[0.782, 0.03], sp=0.012, sg=0.009, hp=3, skip=False),
           struct=dict(), only_struct=['pec_lift', 'sternum', 'cleft2', 'lobes'], clamp_tol=0.4, allow_back=None, guard_sigma=0.008, guard_n=3, guard_zhi=1.318)
Z_RAMPS_F = [(1.12, 1.135, 1.265, 1.285), (0.90, 0.92, 1.10, 1.13), (0.78, 0.80, 0.89, 0.915)]
Z_RAMPS_B = [(1.12, 1.14, 1.30, 1.33), (0.90, 0.93, 1.10, 1.13), (0.77, 0.79, 0.90, 0.935)]

def rbf_from_coef(Vs, R):
    """apply a frozen RBF coefficient asset (data/c_<name>.npz) to Vs: positions = Vs + BF cF + BB cB (same basis/taper as the solve)."""
    T = Torso3(Vs, xtaper=tuple(R.get('xtaper', (0.125, 0.075)))); T.make_basis(R.get('sp', 0.012), R.get('sg', 0.009)); d = np.load(R['coef_file'])
    assert np.allclose(d['C'], T.C), 'basis mismatch'
    cF = d['cF'] * R.get('coef_scale_F', R.get('coef_scale', 1.0)); cB = d['cB'] * R.get('coef_scale_B', R.get('coef_scale', 1.0))
    return T.positions(T.dy_mm(cF, cB)), (cF, cB, T.C)

def rbf_stage(Vs, T0, R, ext_ref):
    """gain-driven RBF refit starting at Vs (bounds: |dy|<=hmax and the extremes of ext_ref)."""
    if R.get('coef_file'): return rbf_from_coef(Vs, R)
    T = Torso3(Vs, gain_fn=make_gain(R['gF'], R['gB']), zfloor=tuple(R['zfloor']), hp_iters=R['hp'], xtaper=tuple(R.get('xtaper', (0.125, 0.075))), xtap=tuple(R.get('xtap', (0.14, 0.06)))); T.make_basis(R['sp'], R['sg']); zc = T.C[:, 1]
    def lam_region(mult, zr):
        out = np.ones(T.m)
        for mi, (a, b, c, d) in zip(mult, zr): out = out * (1 + (mi - 1.0) * ramp(zc, a, b, c, d))
        return out
    lamF = lam_region(R['lamF'], Z_RAMPS_F); lamB = lam_region(R['lamB'], Z_RAMPS_B)
    lo, hi = extreme_bounds_ref(T, ext_ref, R['hmax'], tol_mm=R['tol'])
    z0 = np.zeros(T.m); lamv = np.concatenate([lamF, lamB])
    # independent solves (front view -> cF, back view -> cB): damping/convergence of one side cannot disturb the other
    sides = R.get('sides', ['front', 'back']); cF = z0.copy(); cB = z0.copy()
    if R.get('joint', True) and 'front' in sides and 'back' in sides:       # the joint solve (shared damping) is the one validated against the gate; independent solves stall on the back
        T.active = None; cF, cB = solve_lm3(T, z0, z0, lam=R['lam'], lam_vec=lamv, lo=lo, hi=hi, iters=R['iters'], mu0=R.get('mu0', 0.5), verbose=False, tol_rel=R.get('tol_rel', 1.5e-3)); sides = []
    if 'front' in sides:
        T.active = ('front',); cF, _ = solve_lm3(T, z0, z0, lam=R['lam'], lam_vec=lamv, lo=lo, hi=hi, iters=R['iters'], verbose=False, tol_rel=R.get('tol_rel', 1.5e-3))
    if 'back' in sides:
        T.active = ('back',); _, cB = solve_lm3(T, z0, z0, lam=R['lam'], lam_vec=lamv, lo=lo, hi=hi, iters=R['iters'], verbose=False, tol_rel=R.get('tol_rel', 1.5e-3))
    T.active = None
    return T.positions(T.dy_mm(cF, cB)), (cF, cB, T.C)

def extreme_bounds_ref(T, ref, hmax_mm, tol_mm=0.4, half=0.006):
    """like extreme_bounds but the slab extremes come from `ref` (the installed FORM2 mesh) while the positions come from T.V0 (current stage start)."""
    zs = np.arange(0.775, 1.40, 0.0025); F, B = extremes(ref, T.Z, zs, half=half, xmax=0.20); ok = ~np.isnan(F)
    Fz = np.interp(T.V0[:, 2], zs[ok], F[ok]); Bz = np.interp(T.V0[:, 2], zs[ok], B[ok])
    hf = np.maximum((T.V0[:, 1] - Fz) * 1000 + tol_mm, 0); hb = np.maximum((Bz - T.V0[:, 1]) * 1000 + tol_mm, 0)
    return (-np.minimum(hmax_mm, hf))[T.zi], (np.minimum(hmax_mm, hb))[T.zi]

def clamp_extremes(V, ref, T, tol_mm, allow_back=None):
    """hard clamp of zone vertices into the slab extremes of ref (+tol): no silhouette overshoot (flat-tops a crest that would exceed it).
    allow_back: optional dict(A=mm, z=[a,b,c,d]) extra back-most allowance (glute band; the side plates are 6-12 mm deeper than the mesh at z 0.82-0.84)."""
    zs = np.arange(0.775, 1.40, 0.0025); F, B = extremes(ref, T.Z, zs, half=0.006, xmax=0.20); ok = ~np.isnan(F)
    Fz = np.interp(V[:, 2], zs[ok], F[ok]) - tol_mm * 1e-3; Bz = np.interp(V[:, 2], zs[ok], B[ok]) + tol_mm * 1e-3
    if allow_back: Bz = Bz + allow_back['A'] * 1e-3 * ramp(V[:, 2], *allow_back['z'])
    W = V.copy(); y = np.clip(V[:, 1], Fz, Bz); msk = T.Z & (np.abs(V[:, 0]) < 0.20); W[msk, 1] = y[msk]; return W

def struct_stage(V, T0, S, only):
    P = copy.deepcopy(struct3.P_)
    for f in ('pec_lift', 'shelf', 'sternum', 'linea', 'iliac', 'oblique', 'cleft', 'lobes'):
        if f not in only: P[f]['A'] = 0.0
    if 'cleft2' not in only:
        for i in range(8): P['cleft2']['a%d' % i] = 0.0
    for f, kv in S.items(): P[f].update(kv)
    hF, hB = struct3.fields(V, P); dy = (-T0.wf * hF + T0.wb * hB) * T0.taper * 1e-3
    W = V.copy(); W[:, 1] += dy; return W, P

def build(cfg, verbose=True):
    V0 = np.load('data/V_base.npy'); T0 = Torso3(V0); t0 = time.time(); info = {}
    R = cfg['rbf']; V = V0.copy()
    steps = ['rbf', 'struct'] if cfg['order'] == 'rbf_first' else ['struct', 'rbf']
    for st in steps:
        if st == 'rbf' and not R.get('skip'):
            V, coef = rbf_stage(V, T0, R, V0); info['rbf_coef'] = coef; V = clamp_extremes(V, V0, T0, cfg['clamp_tol'])
        elif st == 'struct':
            V, P = struct_stage(V, T0, cfg['struct'], cfg['only_struct']); info['struct_params'] = P; V = clamp_extremes(V, V0, T0, cfg['clamp_tol'], cfg.get('allow_back'))
        if verbose: print('  stage', st, 'done %.0fs' % (time.time() - t0), 'dy range [%.1f, %.1f] mm' % (((V - V0)[:, 1].min()) * 1000, ((V - V0)[:, 1].max()) * 1000))
    Vg, dF, dB = deficit_guard(V, V0, T0, sigma=cfg['guard_sigma'], n=cfg['guard_n'], zhi=cfg['guard_zhi'], zlo=cfg.get('guard_zlo', 0.80))
    info['guard_drift_mm'] = (float(np.nanmax(np.abs(dF)) * 1000), float(np.nanmax(np.abs(dB)) * 1000))
    return Vg, V0, T0, info

def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): merge(a[k], v)
        else: a[k] = v
    return a

if __name__ == '__main__':
    tag = sys.argv[1]; cfg = copy.deepcopy(DEF)
    if len(sys.argv) > 2: merge(cfg, json.loads(sys.argv[2]))
    Vg, V0, T0, info = build(cfg); np.save(f'data/V_{tag}.npy', Vg)
    json.dump(cfg, open(f'data/cfg_{tag}.json', 'w'), indent=1)
    if 'rbf_coef' in info: np.savez(f'data/c_{tag}.npz', cF=info['rbf_coef'][0], cB=info['rbf_coef'][1], C=info['rbf_coef'][2])
    d = (Vg[:, 1] - V0[:, 1]) * 1000
    print(tag, 'dy [%.1f, %.1f] mm  moved %d  guard drift front %.2f back %.2f mm' % (d.min(), d.max(), int(np.any(Vg != V0, axis=1).sum()), *info['guard_drift_mm']))
