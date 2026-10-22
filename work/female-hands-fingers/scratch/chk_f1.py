import json, numpy as np
import fit_f, asm_f
from femlib import *
x = json.load(open('data/fit_best_s1.json'))['params']
r = fit_f.evaluate(x)
print({k: v for k, v in r.items() if k != 'per'})
par, pose = fit_f.split({**fit_f.DEFAULT, **x})
Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
for side in (1,):
    s = si[side]; mp = s['mapping']; info = s['info']
    thumb_ids = [mp[v] for row in info['thumb_rows'] for v in row]
    idx_ids = [mp[v] for row in info['fin_rows'][0][0] for v in row]
    print('thumb y range mm', Vn[thumb_ids,1].min()*1000, Vn[thumb_ids,1].max()*1000, ' x range', Vn[thumb_ids,0].min()*1000, Vn[thumb_ids,0].max()*1000)
    print('index y range mm', Vn[idx_ids,1].min()*1000, Vn[idx_ids,1].max()*1000)
    for k in range(4):
        ids = [mp[v] for row in info['fin_rows'][k][0] for v in row]
        C = mp[info['fin_rows'][k][1]]
        print('finger', k, 'tip pole xyz mm', np.round(Vn[C]*1000, 1), ' z min', round(Vn[ids,2].min()*1000,1))
    print('thumb tip', np.round(Vn[mp[info['thumb_tip']]]*1000, 1))
