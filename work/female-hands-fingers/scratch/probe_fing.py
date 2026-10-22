import json
import fit_f, metrics_f
x = json.load(open('data/params_final.json'))['params']
for fs, ag, tr in ((0.986, 0.881, 0.994), (1.06, 0.881, 0.994), (1.10, 0.881, 0.994), (1.14, 0.881, 0.994), (1.10, 0.95, 1.05), (1.14, 1.0, 1.10)):
    y = dict(x, fing_scale=fs, A_gain=ag, thumb_r_scale=tr)
    r = fit_f.evaluate(y); res, _ = metrics_f.compute(y)
    F = res['R']['fingers']; T = res['R']['thumb']
    print('fing %.3f A %.2f thumb %.2f | ROI %.0f cost %.0f band %s  clear %.1f dih %.0f | finger base %.1f mm tip/base %.2f  thumb diam %.1f' % (fs, ag, tr, r['total'], r['cost'], r['band_back_front_mm'], r['thumb_min_clear_mm'], r['web_dihedral_deg'], F[1]['width_base_mm'], F[1]['tip_base'], T['mean_diam_mm']))
