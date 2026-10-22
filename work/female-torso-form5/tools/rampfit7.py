"""rampfit7.py: round-5 underbutt search.  Targets the HIGH-PASS fold line (what the eye / the critics trace in the rendered soft panel) instead of the deficit centroid.
cost = fold-line z error (cm rms, |x| .045-.135) + hp depth ratio + lower-edge onset + envelope (<= 3 mm) + dihedral caps.
python3 tools/rampfit7.py NAME iters seed [start.json]   -> data/PP5_NAME.json"""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rampfit6 as rf
import foldx5 as fx
import bandtrace5 as bt
import pelvis5 as pv, benv5
from fplate import BALD

HERE = fx.HERE; FB = fx.FB
XS = (0.045, 0.06, 0.075, 0.09, 0.105, 0.12, 0.135)
ENV_CAP = float(os.environ.get('ENV_CAP', '3.0'))
ZG2 = np.arange(0.70, 0.881, 0.02)      # same z grid as the envelope gate (a single-z glitch of the envelope function at z .73 is not a target)
box = fx.BOX; c0, r0, c1, r1 = box
PLATE = np.asarray(BALD[r0:r1, c0:c1], dtype=np.float32)
TP = bt.trace(PLATE, box, XS)
PZ = np.array([t[0] for t in TP]); PD = np.array([t[1] for t in TP])
PLO = [fx.fold_stats(fx.profile_plate(x))['onset'] for x in (0.03, 0.06, 0.09, 0.12)]
SPACE = dict(rf.SPACE)
SPACE.update({'rza_x': (-0.03, 0.06, 0.004), 'rzf_x': (-0.02, 0.05, 0.004), 'rx0': (0.02, 0.09, 0.006), 'rx1': (0.09, 0.17, 0.008), 'R0': (0.006, 0.016, 0.0008), 'rz2': (0.76, 0.80, 0.004), 'rz3': (0.82, 0.88, 0.005)})
SPACE['rza'] = (0.82, 0.92, 0.006); SPACE['rzf'] = (0.74, 0.80, 0.004)
SPACE.pop('rl0', None); SPACE.pop('rl1', None)      # frozen at .075/.20: the round-4 outer-thigh stripe-patch fix (mirror-stripe test) must not be undone

def cost(PP, gain=1.5):
    co = pv.build_pelvis(rf.CO_MIX, PP)
    e = 1000 * (benv5.env(co, ZG2) - np.interp(ZG2, FB[0], FB[1]))
    img, _ = fx.render(co, gain, box); img = np.asarray(img, dtype=np.float32)
    t = bt.trace(img, box, XS)
    mz = np.array([v[0] for v in t]); md = np.array([v[1] for v in t])
    ez = 100.0 * (mz - PZ)                                  # cm
    rd = np.clip(md / np.maximum(PD, 1.0) - 1.0, -1.0, 2.0)
    img2, _ = fx.render(co, 2.0, box)
    ons = [fx.fold_stats(fx.profile_model(img2, x))['onset'] for x in (0.03, 0.06, 0.09, 0.12)]
    eo = 100.0 * (np.array(ons) - np.array(PLO))
    dm, di, du = rf.dih_stats(co)
    J = (12.0 * np.sqrt((ez ** 2).mean()) + 6.0 * np.sqrt((rd[:5] ** 2).mean()) + 3.0 * np.sqrt((eo ** 2).mean())
         + 0.4 * np.sqrt((e ** 2).mean()) + 4.0 * max(0.0, np.abs(e).max() - ENV_CAP)
         + 3.0 * max(0.0, dm - 29.5) + 3.0 * max(0.0, di - 24.8) + 2.0 * max(0.0, du - 26.0))
    return J, dict(e=e, ez=ez, rd=rd, eo=eo, dm=dm, di=di, du=du, mz=mz, md=md)

if __name__ == '__main__':
    name, iters, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    rng = np.random.default_rng(seed)
    PP = json.load(open(sys.argv[4] if len(sys.argv) > 4 else HERE + '/data/PP5_final.json'))
    bestJ, info = cost(PP)
    print('start J %.2f | ez rms %.2f cm | env max %.2f | dep ratio %s' % (bestJ, np.sqrt((info['ez'] ** 2).mean()), np.abs(info['e']).max(), np.round(info['rd'], 2)), flush=True)
    keys = list(SPACE)
    for it in range(iters):
        Q = copy.deepcopy(PP)
        for k in rng.choice(keys, int(rng.integers(1, 4)), replace=False):
            lo, hi, st = SPACE[k]
            Q[k] = float(np.clip(Q.get(k, 0.5 * (lo + hi)) + rng.normal() * st * (1 if rng.random() < .7 else 2.5), lo, hi))
        if (Q.get('c_x1', 0.07) <= Q.get('c_x0', 0.03) + 0.01 or Q.get('ds_x1', 0.12) <= Q.get('ds_x0', 0.07) + 0.02 or Q.get('rl1', 0.16) <= Q.get('rl0', 0.11) + 0.02
                or Q.get('rx1', 0.13) <= Q.get('rx0', 0.06) + 0.03 or Q.get('rz3', 0.84) <= Q.get('rz2', 0.78) + 0.03):
            continue
        J, inf = cost(Q)
        if J < bestJ - 1e-4:
            bestJ, PP, info = J, Q, inf
            print('it %4d J %.2f | ez rms %.2f cm (%s) | env %.2f | rd %s | onset rms %.2f | dih %.1f/%.1f/%.1f' % (it, J, np.sqrt((inf['ez'] ** 2).mean()), np.round(inf['ez'], 1), np.abs(inf['e']).max(), np.round(inf['rd'][:5], 2), np.sqrt((inf['eo'] ** 2).mean()), inf['dm'], inf['di'], inf['du']), flush=True)
            json.dump(PP, open(HERE + f'/data/PP5_{name}.json', 'w'), indent=1)
    json.dump(PP, open(HERE + f'/data/PP5_{name}.json', 'w'), indent=1)
    print('done', name, 'J', bestJ); print(json.dumps({k: round(PP.get(k, 0), 4) for k in SPACE}))
