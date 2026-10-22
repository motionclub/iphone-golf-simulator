import json
import metrics_f
x = json.load(open('data/params_final.json'))['params']
for tb in (0.08, 0.16, 0.24, 0.32, 0.40):
    res, _ = metrics_f.compute(x, extra_par=dict(thumb_bump=tb))
    T = res['R']['thumb']
    print('thumb_bump %.2f  IP bump %.2f mm  tip ratio %.2f  min r %.1f  dih %.1f  bend %.1f' % (tb, T['ip_bump_mm'], T['tip_ratio'], T['min_shaft_radius_mm'], T['max_dihedral_root_deg'], T['ip_bend_deg']))
