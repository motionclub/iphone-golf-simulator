"""FORM5 final build: chest (torso5 arc mounds + soft wall corner + front wall fit) + FORM4's own glute build (unchanged parameters) blended over z .99-1.06 exactly like torso4.build_final,
then the underbutt / LEG-TOP stage (pelvis5) on top.  python3 tools/build5.py [P5_final.json] [P_glute4.json] [PP5_final.json]  -> data/co_FORM5_final.npy"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torso5 as t5
import torso4 as t4
import pelvis5 as pv
from torso4 import CO0, T, sstep

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_final5(PC, PG, PP, z0=0.99, z1=1.06, iters=4, return_parts=False):
    coC, dFc, dBc = t5.build_chest(PC)                      # sets t4.TT for the chest build
    t4.TT = t5._TT_ORIG.copy()                              # FORM4's glute build uses the ORIGINAL ring parameter
    dFg, dBg = t4.fit_walls(PG, iters=iters, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    coG = t4.build3(PG, dFg, dBg)
    w = sstep((CO0[:, 2] - z0) / (z1 - z0))
    co_mix = np.where(T[:, None], coG + w[:, None] * (coC - coG), CO0)
    co = pv.build_pelvis(co_mix, PP)
    if return_parts:
        return co, dict(co_mix=co_mix, coC=coC, coG=coG, dFc=dFc, dBc=dBc, dFg=dFg, dBg=dBg)
    return co


if __name__ == '__main__':
    pc = sys.argv[1] if len(sys.argv) > 1 else HERE + '/data/P5_final.json'
    pg = sys.argv[2] if len(sys.argv) > 2 else HERE + '/data/P_glute4.json'
    pp = sys.argv[3] if len(sys.argv) > 3 else HERE + '/data/PP5_final.json'
    PC, PG, PP = json.load(open(pc)), json.load(open(pg)), json.load(open(pp))
    co, parts = build_final5(PC, PG, PP, return_parts=True)
    assert np.isfinite(co).all()
    np.save(HERE + '/data/co_FORM5_final.npy', co)
    np.save(HERE + '/data/co_FORM5_mix.npy', parts['co_mix'])
    np.save(HERE + '/export/form5_wall_corrections.npy', np.stack([parts['dFc'], parts['dBc'], parts['dFg'], parts['dBg']]))
    co4 = np.load(HERE + '/data/co_FORM4_final.npy').astype(np.float64)
    d = np.linalg.norm(co - co4, axis=1)
    z5 = np.load(HERE + '/data/zone5.npz')
    print('saved data/co_FORM5_final.npy; moved vs FORM4:', int((d > 1e-9).sum()), ' max mm', round(1000 * d.max(), 2), ' outside T5 moved:', int(((d > 1e-12) & ~z5['torso']).sum()),
          ' border5 moved:', int(((d > 1e-12) & z5['border5']).sum()))
    # glute (z<.99) of the mix equals FORM4 exactly?
    dm = np.linalg.norm(parts['co_mix'] - co4, axis=1)
    print('mix vs FORM4 at z<0.99 (max mm):', round(1000 * dm[CO0[:, 2] < 0.99].max(), 6))
