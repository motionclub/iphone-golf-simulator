import json, numpy as np, itertools
import fit_f, asm_f, metrics_f
x = json.load(open('data/fit_best_s2.json'))['params']
x.update(out_deg=3.8, psi_deg=0.0, lean_deg=0.0)
base = dict()
def run(extra):
    res, _ = metrics_f.compute(x, extra_par=extra)
    T = res['R']['thumb']
    return T['max_dihedral_root_deg'], T['n_edges_gt60'], res['thenar_mound_mm']
print('base', run({}))
for sm_R, iters, wk, wamp, tf in [(0.07, 45, 0.020, 0.9, 0.004), (0.07, 90, 0.020, 0.9, 0.004), (0.07, 90, 0.026, 1.2, 0.004), (0.07, 90, 0.026, 1.2, 0.009), (0.09, 120, 0.030, 1.4, 0.009), (0.09, 120, 0.030, 1.4, 0.014)]:
    e = dict(sm_thumb_R=sm_R, sm_iters=iters, web_k=wk, web_amp=wamp, thumb_first=tf)
    print(e, run(e))
