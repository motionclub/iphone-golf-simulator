"""rung.py: glute variants on top of a fixed bust (n3-like).  run_g(k, params) -> data/co_glu_<k>.npy"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form3/tools')
from torso3 import *

A = dict(xc=0.064, zc=1.232, sxm=0.042, sxl=0.036, szd=0.038, szu=0.055, H=0.012, p=1.0)
B = dict(xc=0.080, zc=1.208, sxm=0.038, sxl=0.036, szd=0.026, szu=0.040, H=0.026, p=1.2, tdn=0.2, tup=0.3, gd=0.004, gr=1.15, gw=0.2)
BUST = dict(pf_A=0.0, b_rec=0.016, bm_list=[A, B], bm_scale=0.98, bm_dz=-0.0105)

def run_g(k, Pg, bust=None, prefix='glu', iters=4):
    Q = {**DEFAULT3, **(bust or BUST), **Pg}
    dF, dB = fit_walls(Q, iters=iters, verbose=False, zlo=0.82, zhi=1.30, fz=(0.82, 1.12), bz=(0.82, 1.30))
    co = build3(Q, dF, dB)
    np.save(f'{WD}/data/co_{prefix}_{k}.npy', co)
    json.dump(Q, open(f'{WD}/data/P_{prefix}_{k}.json', 'w'), default=float)
    np.save(f'{WD}/data/dFB_{prefix}_{k}.npy', np.stack([dF, dB]))
    ef, eb, m = sil_err(co, 0.82, 1.0)
    print(f'{k}: back sil rms 0.82-1.0 {1000*np.sqrt((eb[m]**2).mean()):.2f} mm; at z=.82: {1000*eb[int(round((0.82-0.8)/0.002))]:+.1f}')
    return Q
