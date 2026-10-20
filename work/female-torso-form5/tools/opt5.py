"""opt5.py: constrained random hill-climb of the chest parameters against the plate (front band-pass at the plate-matched gain) with geometric safety penalties.
python3 tools/opt5.py START.json OUT_NAME iters seed   -> data/P5_<OUT>.json, data/co5_<OUT>.npy, log"""
import sys, os, json, time, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import chestx5, costb5, seam
import torso5 as t5, torso4 as t4
from torso4 import section_extents, fillnan, ZG, T, BORDER
HERE = chestx5.HERE; FF = chestx5.FF
CONC = {"mode": "land", "zs": 1.262, "ze": 1.355}
# name: (lo, hi, step)   'b5.x' keys go to P['b5']
SPACE = {
    'b5.H': (0.014, 0.032, 0.002), 'b5.sxm': (0.028, 0.065, 0.004), 'b5.sxl': (0.05, 0.11, 0.006), 'b5.xcr': (0.06, 0.10, 0.004),
    'b5.Ll': (0.028, 0.06, 0.004), 'b5.Lu': (0.035, 0.09, 0.005), 'b5.zlow': (1.150, 1.195, 0.004), 'b5.xarc': (0.07, 0.11, 0.004),
    'b5.Rarc': (0.07, 0.14, 0.008), 'b5.Rarc_l': (0.05, 0.13, 0.008), 'b5.a': (1.6, 3.6, 0.2), 'b5.fw': (0.03, 0.09, 0.006),
    'b5.sv': (0.0, 0.008, 0.001), 'b5.ssx': (0.014, 0.036, 0.003), 'b5.tr': (0.0, 0.03, 0.003), 'b5.qx': (1.6, 3.2, 0.2),
    'wl_y': (-0.125, -0.105, 0.003), 'wc_s': (0.5, 0.95, 0.05),
}
FAST_ENV_Z = np.arange(1.14, 1.285, 0.01)


def evaluate(P, gain=1.5):
    t4.TT = t5.make_TT(P)
    try:
        co, dF, dB = t5.build_chest(P)
    except Exception as e:
        return 1e9, {}
    if not np.isfinite(co).all():
        return 1e9, {}
    m = costb5.metrics(co, gain)
    fe, be = section_extents(co); fe = fillnan(fe)
    env = 1000 * (np.interp(FAST_ENV_Z, ZG, fe) - np.interp(FAST_ENV_Z, FF[0], FF[1]))
    env_rms = float(np.sqrt((env ** 2).mean()))
    bs = seam.border_steps(co)[0]
    a1 = seam.dihedral(co)
    mid = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
    reg = (mid[:, 2] >= 1.14) & (mid[:, 2] <= 1.32) & (np.abs(mid[:, 0]) <= 0.115) & (mid[:, 1] < 0) & T[seam.PAIR_E[:, 0]] & T[seam.PAIR_E[:, 1]] & ~(BORDER[seam.PAIR_E[:, 0]] | BORDER[seam.PAIR_E[:, 1]])
    dmax = float(a1[reg].max())
    cen = (mid[:, 2] >= 1.15) & (mid[:, 2] <= 1.30) & (np.abs(mid[:, 0]) < 0.022) & (mid[:, 1] < 0) & T[seam.PAIR_E[:, 0]] & T[seam.PAIR_E[:, 1]]
    dcen = float(a1[cen].max())
    img, _ = costb5.render_front(co, gain)
    ru, ra = costb5.ring_fracs(img)
    J = 10.0 * (1.0 - m['ncc']) + 3.0 * abs(np.log(max(m['model_std'], 1e-6) / m['plate_std'])) + 0.15 * env_rms + 8.0 * max(0.0, ru - 0.30)
    J += 2.0 * max(0.0, bs['arm']['max_mm'] - 10.0) + 6.0 * max(0.0, bs['top']['max_mm'] - 1.0)
    J += 0.15 * max(0.0, dmax - 26.0) + 0.15 * max(0.0, dcen - 17.0)
    info = dict(J=J, rms=m['rms'], ncc=m['ncc'], sd=m['model_std'], ring_up=ru, ring_all=ra, env_rms=env_rms, arm=bs['arm']['max_mm'], top=bs['top']['max_mm'], dmax=dmax, dcen=dcen)
    return J, info


def main(start, name, iters, seed):
    rng = np.random.default_rng(seed)
    P = {**t4.DEFAULT3, **json.load(open(start))}
    P['conc_post'] = CONC
    best_J, best_info = evaluate(P)
    print('start', json.dumps({k: round(v, 3) for k, v in best_info.items()}), flush=True)
    keys = list(SPACE)
    t0 = time.time(); acc = 0
    for it in range(iters):
        Q = copy.deepcopy(P)
        n = int(rng.integers(1, 4))
        for k in rng.choice(keys, n, replace=False):
            lo, hi, st = SPACE[k]
            cur = Q['b5'].get(k[3:], None) if k.startswith('b5.') else Q.get(k, None)
            if cur is None:
                cur = 0.5 * (lo + hi)
            v = float(np.clip(cur + rng.normal() * st * (1.0 if rng.random() < 0.7 else 2.5), lo, hi))
            if k.startswith('b5.'):
                Q['b5'][k[3:]] = v
            else:
                Q[k] = v
        J, info = evaluate(Q)
        if J < best_J - 1e-4:
            best_J, best_info, P = J, info, Q; acc += 1
            print(f'it {it:4d} J {J:.3f}  ' + ' '.join(f'{k}={v:.2f}' for k, v in info.items() if k != 'J') + f'  t {time.time()-t0:.0f}s', flush=True)
    json.dump(P, open(f'{HERE}/data/P5_{name}.json', 'w'), indent=1)
    co, dF, dB = t5.build_chest(P) if True else None
    t4.TT = t5.make_TT(P); co, dF, dB = t5.build_chest(P)
    np.save(f'{HERE}/data/co5_{name}.npy', co)
    print('done', name, json.dumps({k: round(v, 3) for k, v in best_info.items()}))
    print('b5:', json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in P['b5'].items()}))
    print('wl_y', P.get('wl_y'), 'wc_s', P.get('wc_s'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
