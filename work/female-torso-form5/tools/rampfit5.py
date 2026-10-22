"""rampfit5.py: coordinate/random search of the ramp parameters so the back ENVELOPE (silhouette column) tracks the sub-pixel plate contour tightly (z .76-.88) -> fold timing like the plate;
reports luminance zmin/onset per column.  python3 tools/rampfit5.py NAME iters seed"""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import foldx5 as fx, benv5, pelvis5 as pv
HERE = fx.HERE
FB = fx.FB
ZE = np.arange(0.76, 0.881, 0.01)
CO_MIX = np.load(HERE + '/data/co_FORM5_mix.npy').astype(np.float64)
SPACE = {'rzf': (0.755, 0.80, 0.004), 'rza': (0.85, 0.92, 0.005), 'ra': (1.0, 3.5, 0.2), 'rc': (1.5, 7.0, 0.4), 'dshift': (0.0, 0.04, 0.004), 'ds_x0': (0.03, 0.09, 0.006), 'ds_x1': (0.09, 0.16, 0.008)}


def env_err(co):
    e = 1000 * (benv5.env(co, ZE) - np.interp(ZE, FB[0], FB[1]))
    return e


def evaluate(PP):
    co = pv.build_pelvis(CO_MIX, PP)
    e = env_err(co)
    img, _ = fx.render(co)
    zm = [fx.fold_stats(fx.profile_model(img, x))['zmin'] for x in fx.FX]
    on = [fx.fold_stats(fx.profile_model(img, x))['onset'] for x in fx.FX]
    pz = [fx.fold_stats(fx.profile_plate(x)) for x in fx.FX]
    pzm = [p['zmin'] for p in pz]; pon = [p['onset'] for p in pz]
    return e, zm, on, pzm, pon, co


def cost(PP):
    e, zm, on, pzm, pon, co = evaluate(PP)
    J = float(np.sqrt((e ** 2).mean())) + 120.0 * float(np.sqrt(np.mean((np.array(zm) - np.array(pzm)) ** 2))) + 60.0 * float(np.sqrt(np.mean((np.array(on) - np.array(pon)) ** 2)))
    J += 3.0 * max(0.0, float(np.abs(e).max()) - 3.0)
    return J, (e, zm, on, pzm, pon)


if __name__ == '__main__':
    name, iters, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    rng = np.random.default_rng(seed)
    PP = json.load(open(HERE + '/data/PP5_final.json'))
    bestJ, info = cost(PP)
    print('start J %.2f' % bestJ, 'env rms %.2f max %.2f' % (np.sqrt((info[0] ** 2).mean()), np.abs(info[0]).max()), 'zmin', [round(v, 3) for v in info[1]], 'plate', [round(v, 3) for v in info[3]], flush=True)
    keys = list(SPACE)
    for it in range(iters):
        Q = copy.deepcopy(PP)
        for k in rng.choice(keys, int(rng.integers(1, 4)), replace=False):
            lo, hi, st = SPACE[k]
            Q[k] = float(np.clip(Q.get(k, 0.5 * (lo + hi)) + rng.normal() * st * (1 if rng.random() < .7 else 2.5), lo, hi))
        J, inf = cost(Q)
        if J < bestJ - 1e-4:
            bestJ, PP, info = J, Q, inf
            print('it %4d J %.2f env rms %.2f max %.2f | zmin %s onset %s' % (it, J, np.sqrt((inf[0] ** 2).mean()), np.abs(inf[0]).max(), [round(v, 3) for v in inf[1]], [round(v, 3) for v in inf[2]]), flush=True)
    json.dump(PP, open(HERE + f'/data/PP5_{name}.json', 'w'), indent=1)
    print('done', name, 'plate zmin', [round(v, 3) for v in info[3]], 'onset', [round(v, 3) for v in info[4]])
    print(json.dumps({k: round(PP[k], 4) for k in SPACE}))
