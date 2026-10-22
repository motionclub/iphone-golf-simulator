import json
import fit_f, metrics_f
def show(tag, x):
    r = fit_f.evaluate(x)
    res, _ = metrics_f.compute(x)
    T = res['R']['thumb']
    print('%-26s ROI %.0f cost %.0f over %.1f dih %.0f clear %.1f | thumb diam %.1f mm  L/D %.2f' % (tag, r['total'], r['cost'], r['thumb_front_over_mm'], r['web_dihedral_deg'], r['thumb_min_clear_mm'], T['mean_diam_mm'], T['length_over_diam']))
c2 = json.load(open('data/params_c2.json'))['params']; s13 = json.load(open('data/fit_best_s13.json'))['params']
show('c2 (thumb 1.19)', c2)
show('c2 thumb 1.08', {**c2, 'thumb_r_scale': 1.08})
show('s13 (thumb 0.99)', s13)
show('s13 thumb 1.08', {**s13, 'thumb_r_scale': 1.08})
