import json, numpy as np
import fit_f, asm_f, metrics_f
x = json.load(open('data/fit_best_s7_ckpt.json'))['params']
def run(extra, tag=None):
    res, (Vn, polys, si) = metrics_f.compute(x, extra_par=extra)
    T = res['R']['thumb']
    r = dict(dih=round(T['max_dihedral_root_deg'], 1), n60=T['n_edges_gt60'], ipbend=round(T['ip_bend_deg'], 1), thenar=round(res['thenar_mound_mm'], 2), L=round(T['length_mm'], 1), minr=round(T['min_shaft_radius_mm'], 1))
    if tag:
        par, pose = fit_f.split({**fit_f.DEFAULT, **x}); par.update(extra); V, p, s, rem = asm_f.assemble(par, pose, verbose=False); asm_f.save(asm_f.W / f'data/cand_{tag}.npz', V, p, rem)
    return r
print('base', run({}))
for lift, first in ((0.008, 0.008), (0.012, 0.008), (0.012, 0.012), (0.016, 0.010)):
    print(lift, first, run(dict(root_lift=lift, thumb_first=first), tag=f'rl{int(lift*1000)}_{int(first*1000)}'))
