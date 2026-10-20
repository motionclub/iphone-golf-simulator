import json, numpy as np
import fit_f, asm_f, fhand
from femlib import *
x = json.load(open('data/fit_best_s2.json'))['params']
par, pose = fit_f.split({**fit_f.DEFAULT, **x})
Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
info = si[1]['info']; P = info['P']
print('thumb_pts (local):'); 
for p in P['thumb_pts']: print('  ', np.round(p, 4))
dense, cum = info['thumb_axis']
tot = cum[-1]; print('axis length mm', round(tot*1000, 1))
def tang(u):
    k = int(np.searchsorted(cum, u*tot)); k = min(max(k, 2), len(dense)-3); t = dense[k+2]-dense[k-2]; return t/np.linalg.norm(t)
for u in (0.1, 0.3, 0.5, 0.7, 0.85): print('u', u, 'tangent', np.round(tang(u), 3))
ang = lambda a, b: np.degrees(np.arccos(np.clip(np.dot(a, b), -1, 1)))
print('angle t(0.3)-t(0.8): %.1f' % ang(tang(0.3), tang(0.8)), ' t(0.1)-t(0.85): %.1f' % ang(tang(0.1), tang(0.85)))
cen = np.array(info['thumb_centers']); print('centers rows', len(cen)); 
print('center row n_shaft path deg: ', [round(ang(cen[i+1]-cen[i], cen[i+2]-cen[i+1]), 1) for i in range(0, 8)])
