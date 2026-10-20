import json, numpy as np
import fit_f, asm_f
from femlib import *
x = json.load(open('data/fit_best_s2.json'))['params']
par, pose = fit_f.split({**fit_f.DEFAULT, **x})
Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
s = si[1]; mp = s['mapping']; info = s['info']
newfaces = polys[-len(s['faces']) * 2:]  # approximate: the last faces (both sides) -- recompute below
# normals of all polys
FN = face_normals(Vn, polys)
# thumb faces: those with all verts in thumb rows + tip
tv = set(mp[v] for row in info['thumb_rows'] for v in row) | {mp[info['thumb_tip']]}
cent = {}
dense, cum = info['thumb_axis']
# axis centre per row from info
rows = info['thumb_rows']; centers = info['thumb_centers']
vrow = {}
for j, row in enumerate(rows):
    for v in row: vrow[mp[v]] = j
bad = 0; tot = 0; badlist = []
for fi, p in enumerate(polys):
    if all(v in tv for v in p):
        tot += 1
        js = [vrow.get(v, len(rows)-1) for v in p]
        j = int(np.mean(js)); c = FN[fi]
        # centre of the axis in global coords: approximate by mean of that row's verts
        rowv = [mp[v] for v in rows[min(j, len(rows)-1)]]
        axc = Vn[rowv].mean(0)
        fc = Vn[list(p)].mean(0)
        d = np.dot(c, fc - axc)
        if d < 0: bad += 1; badlist.append((fi, j, round(float(d)*1000, 3)))
print('thumb faces', tot, 'inward facing', bad, badlist[:10])
# area of faces near tip
Ct = mp[info['thumb_tip']]
print('Ct', np.round(Vn[Ct]*1000, 1))
nb = [fi for fi, p in enumerate(polys) if Ct in p]
for fi in nb:
    p = polys[fi]; P = Vn[list(p)]*1000
    area = 0.5*np.linalg.norm(np.cross(P[1]-P[0], P[2]-P[0])) + (0.5*np.linalg.norm(np.cross(P[2]-P[0], P[3]-P[0])) if len(p) == 4 else 0)
    print(' face', fi, 'verts', len(p), 'area mm2 %.3f' % area, 'normal', np.round(FN[fi], 2))
