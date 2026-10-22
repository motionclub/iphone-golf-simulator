"""rampfit6.py: search the smile parameters (ramp + centre dip) against the plate's fold LINE (luminance zmin per column x .02-.135) with an envelope constraint.
python3 tools/rampfit6.py NAME iters seed [start.json]"""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import foldx5 as fx, benv5, pelvis5 as pv, foldtab5 as ft, seam
from torso4 import CO0, T, BORDER
HERE = fx.HERE; FB = fx.FB
ZE = np.arange(0.70, 0.881, 0.01)
CO_MIX = np.load(HERE + '/data/co_FORM5_mix.npy').astype(np.float64)
PL = [fx.band_stats(fx.profile_plate(x)) for x in ft.XS]
_zp = T[seam.PAIR_E[:, 0]] & T[seam.PAIR_E[:, 1]]
_a0 = seam.dihedral(CO0)
_nb = ~(BORDER[seam.PAIR_E[:, 0]] | BORDER[seam.PAIR_E[:, 1]]) & (_a0 <= 15.0)
def dih_stats(co):
    a1 = seam.dihedral(co); mid = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
    reg = _zp & _nb & (mid[:, 2] >= 0.80) & (mid[:, 2] <= 1.02) & (np.abs(mid[:, 0]) <= 0.15) & (mid[:, 1] > 0)
    reg2 = _zp & (mid[:, 2] >= 0.70) & (mid[:, 2] <= 0.90) & (mid[:, 1] > 0.02) & (np.abs(mid[:, 0]) >= 0.035) & (np.abs(mid[:, 0]) <= 0.17)
    return float(a1[reg].max()), float((a1 - _a0)[reg].max()), float(a1[reg2].max())
SPACE = {'rzf': (0.76, 0.80, 0.004), 'rza': (0.85, 0.92, 0.006), 'ra': (0.7, 3.0, 0.2), 'rc': (1.5, 6.0, 0.4), 'dshift': (0.0, 0.045, 0.004), 'ds_x0': (0.03, 0.09, 0.006), 'ds_x1': (0.09, 0.17, 0.008),
         'cdz': (0.0, 0.03, 0.003), 'c_x0': (0.01, 0.05, 0.005), 'c_x1': (0.05, 0.11, 0.006), 'rl0': (0.09, 0.14, 0.006), 'rl1': (0.14, 0.2, 0.008)}


def cost(PP, wenv=1.0):
    co = pv.build_pelvis(CO_MIX, PP)
    e = 1000 * (benv5.env(co, ZE) - np.interp(ZE, FB[0], FB[1]))
    img, _ = fx.render(co)
    md = [fx.band_stats(fx.profile_model(img, x)) for x in ft.XS]
    ez = np.array([m['centroid'] - p['centroid'] for m, p in zip(md, PL)]); eo = np.array([m['lower'] - p['lower'] for m, p in zip(md, PL)]); ed = np.array([m['depth'] - p['depth'] for m, p in zip(md, PL)])
    dm, di, du = dih_stats(co)
    J = 100.0 * np.sqrt((ez ** 2).mean()) + 40.0 * np.sqrt((eo ** 2).mean()) + 0.03 * np.sqrt((ed ** 2).mean()) + wenv * (0.4 * np.sqrt((e ** 2).mean()) + 2.0 * max(0.0, np.abs(e).max() - 3.5)) + 3.0 * max(0.0, dm - 29.5) + 3.0 * max(0.0, di - 24.8) + 1.0 * max(0.0, du - 31.0) + 8.0 * max(0.0, abs(float(ez[1]) if False else 0.0)) + 40.0 * max(0.0, abs(float(eo[1])) - 0.010)
    return J, (e, ez, eo, ed, dm, di, du)


if __name__ == '__main__':
    name, iters, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    rng = np.random.default_rng(seed)
    PP = json.load(open(sys.argv[4] if len(sys.argv) > 4 else HERE + '/data/PP5_final.json'))
    bestJ, info = cost(PP)
    print('start J %.2f env max %.2f zmin rms %.2f cm' % (bestJ, np.abs(info[0]).max(), 100 * np.sqrt((info[1] ** 2).mean())), flush=True)
    keys = list(SPACE)
    for it in range(iters):
        Q = copy.deepcopy(PP)
        for k in rng.choice(keys, int(rng.integers(1, 4)), replace=False):
            lo, hi, st = SPACE[k]
            Q[k] = float(np.clip(Q.get(k, 0.5 * (lo + hi)) + rng.normal() * st * (1 if rng.random() < .7 else 2.5), lo, hi))
        if Q.get('c_x1', 0.07) <= Q.get('c_x0', 0.03) + 0.01 or Q.get('ds_x1', 0.12) <= Q.get('ds_x0', 0.07) + 0.02 or Q.get('rl1', 0.16) <= Q.get('rl0', 0.11) + 0.02:
            continue
        J, inf = cost(Q)
        if J < bestJ - 1e-4:
            bestJ, PP, info = J, Q, inf
            print('it %4d J %.2f env max %.2f rms %.2f | zmin rms %.2f cm onset rms %.2f cm depth rms %.1f | dih %.1f inc %.1f und %.1f | onset@.03 %+.2f cm' % (it, J, np.abs(inf[0]).max(), np.sqrt((inf[0] ** 2).mean()), 100 * np.sqrt((inf[1] ** 2).mean()), 100 * np.sqrt((inf[2] ** 2).mean()), np.sqrt((inf[3] ** 2).mean()), inf[4], inf[5], inf[6], 100 * inf[2][1]), flush=True)
    json.dump(PP, open(HERE + f'/data/PP5_{name}.json', 'w'), indent=1)
    print('done', name); print(json.dumps({k: round(PP.get(k, 0), 4) for k in SPACE}))
