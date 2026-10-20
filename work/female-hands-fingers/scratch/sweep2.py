import json, numpy as np
import fit_f, asm_f, metrics_f
x = json.load(open('data/fit_best_s2.json'))['params']
x.update(out_deg=3.8, psi_deg=0.0, lean_deg=0.0)
web = dict(sm_thumb_R=0.09, sm_iters=120, web_k=0.03, web_amp=1.4, thumb_first=0.014)
def run(extra):
    e = dict(web); e.update(extra)
    res, _ = metrics_f.compute(x, extra_par=e)
    F = res['R']['fingers']; T = res['R']['thumb']
    return dict(dih=round(T['max_dihedral_root_deg'], 1), n60=T['n_edges_gt60'], ipbend=round(T['ip_bend_deg'], 1), ipbump=round(T['ip_bump_mm'], 2),
                pip=[round(F[k]['bump_pip_mm'], 2) for k in F], dip=[round(F[k]['bump_dip_mm'], 2) for k in F], tipbase=round(max(F[k]['tip_base'] for k in F), 3))
print('web only', run({}))
for bp, bd in ((0.14, 0.12), (0.20, 0.17), (0.26, 0.22)):
    print('bump', bp, bd, run(dict(bump_pip=bp, bump_dip=bd)))
for tm in (3.5, 4.5):
    print('morph', tm, run(dict(thumb_morph=tm, thumb_first=0.014)))
