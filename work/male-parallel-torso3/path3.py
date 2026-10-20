"""LM path recorder: python3.13 path3.py <side front|back> <tag> [json rbf overrides] -> data/path_<tag>.npz (cF/cB per iterate) and V_<tag>_i<k>.npy for each iterate (no structure)."""
import sys, json, copy
import numpy as np
sys.path.insert(0, '.')
import form3
from form3 import *
side = sys.argv[1]; tag = sys.argv[2]; R = copy.deepcopy(DEF['rbf'])
if len(sys.argv) > 3: R.update(json.loads(sys.argv[3]))
V0 = np.load('data/V_base.npy'); T0 = Torso3(V0)
T = Torso3(V0, gain_fn=make_gain(R['gF'], R['gB']), zfloor=tuple(R['zfloor']), hp_iters=R['hp'], xtaper=tuple(R.get('xtaper', (0.125, 0.075))), xtap=tuple(R.get('xtap', (0.14, 0.06))), gain_mode=R.get('gain_mode', 'all'), fine_iters=R.get('fine_iters', 1)); T.make_basis(R['sp'], R['sg']); zc = T.C[:, 1]
def lam_region(mult, zr):
    out = np.ones(T.m)
    for mi, (a, b, c, d) in zip(mult, zr): out = out * (1 + (mi - 1.0) * ramp(zc, a, b, c, d))
    return out
lamv = np.concatenate([lam_region(R['lamF'], Z_RAMPS_F), lam_region(R['lamB'], Z_RAMPS_B)]); lo, hi = extreme_bounds_ref(T, V0, R['hmax'], tol_mm=R['tol']); z0 = np.zeros(T.m)
T.active = None if side == 'both' else (side,); path = []
solve_lm3(T, z0, z0, lam=R['lam'], lam_vec=lamv, lo=lo, hi=hi, iters=R['iters'], mu0=R.get('mu0', 0.5), verbose=False, tol_rel=0.0, callback=lambda it, c: path.append(c))
for k, c in enumerate(path):
    cF, cB = (c[:T.m], c[T.m:]); V = T.positions(T.dy_mm(cF, cB)); V = clamp_extremes(V, V0, T0, 0.4)
    Vg, dF, dB = deficit_guard(V, V0, T0, sigma=0.008, n=3, zhi=1.318); np.save(f'data/V_{tag}_i{k}.npy', Vg); np.savez(f'data/c_{tag}_i{k}.npz', cF=cF, cB=cB, C=T.C)
print(tag, side, 'iterates', len(path))
