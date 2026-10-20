import json, numpy as np
import fit_f
x = json.load(open('data/fit_best.json'))['params']
def show(tag, **kw):
    y = dict(x); y.update(kw); r = fit_f.evaluate(y)
    print('%-28s roi %.0f shelfP %.3f shelfD %.3f dih %.0f clear %.1f cost %.0f' % (tag, r['total'], r['shelf_slope_palmar'], r['shelf_slope_dorsal'], r['web_dihedral_deg'], r['thumb_min_clear_mm'], r['cost']))
show('current')
for sp in (0.06, 0.08, 0.095): show(f'span {sp}', span=sp)
for nc in (0.0, 0.2, 0.6): show(f'NC_gain {nc}', NC_gain=nc)
for bg in (0.9, 1.2): show(f'B_gain {bg}', B_gain=bg)
show('span .08 NC .2', span=0.08, NC_gain=0.2)
show('span .08 B 1.2', span=0.08, B_gain=1.2)
