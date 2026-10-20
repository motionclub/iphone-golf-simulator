"""runvar.py: build chest variants (fit + walls) -> data/co_chest_<k>.npy"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form3/tools')
from torso3 import *

def run(k, P, fit=True, prefix='chest'):
    Q = {**DEFAULT3, **P}
    if fit:
        sc, dz = fit_bust(Q, verbose=False)
        Q['bm_scale'], Q['bm_dz'] = sc, dz
    dF, dB = fit_walls(Q, iters=3, verbose=False)
    co = build3(Q, dF, dB)
    np.save(f'{WD}/data/co_{prefix}_{k}.npy', co)
    json.dump(Q, open(f'{WD}/data/P_{prefix}_{k}.json', 'w'), default=float)
    ef, eb, m = sil_err(co, 1.12, 1.30)
    print(f'{k}: scale={Q.get("bm_scale",1):.2f} dz={Q.get("bm_dz",0)*1000:+.1f}mm  front sil rms {1000*np.sqrt((ef[m]**2).mean()):.2f} mm')
    return Q
