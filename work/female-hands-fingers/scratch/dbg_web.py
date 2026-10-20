import json, numpy as np
import fit_f, asm_f, fhand
from femlib import *
x = json.load(open('data/fit_best_s7_ckpt.json'))['params']
par, pose = fit_f.split({**fit_f.DEFAULT, **x})
Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
s = si[1]; mp = s['mapping']; info = s['info']
inv = {v: k for k, v in mp.items()}
loop = [mp[v] for v in info['thumb_loop']]; c0 = Vn[loop].mean(0)
ef = edge_faces(polys); FN = face_normals(Vn, polys)
FR = asm_f.make_frame_for(asm_f.POSE0)
rows = []
for e, fl in ef.items():
    if len(fl) == 2:
        m = 0.5*(Vn[e[0]] + Vn[e[1]])
        if np.linalg.norm(m - c0) < 0.025:
            a = np.degrees(np.arccos(np.clip(np.dot(FN[fl[0]], FN[fl[1]]), -1, 1)))
            if a > 60: rows.append((a, e, m))
rows.sort(key=lambda r: -r[0])
# classify each end vertex by role
role = {}
for r, ids in info['ring'].items():
    for i, v in enumerate(ids):
        if v in mp: role[mp[v]] = f'palm r{r} c{i}'
for j, ids in enumerate(info['thumb_rows']):
    for i, v in enumerate(ids): role[mp[v]] = f'thumb row{j} k{i}'
for a, e, m in rows[:14]:
    print('%.1f deg  edge %s - %s   at %s' % (a, role.get(e[0], '?'), role.get(e[1], '?'), np.round(m*1000, 1)))
print('loop centroid mm', np.round(c0*1000, 1))
print('hole', info['hole'], 'w_rows', np.round(info['w_rows'], 4).tolist())
