import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo, cage, loftf
d = np.load(fl.W / 'data/ring.npz'); ring_pos = d['pos']
H = geo.Head()
cg = cage.build_cage(ring_pos, geo.C, H=H)
U = cg['u']; P = H.phi(U)
for v, p in cg['pinned'].items(): P[v] = p
rows = cg['rows']
for k in (0, 3, 5, 8, 10, 13, 15, 20, 25):
    print('col', k, [round(float(P[rows[j][k], 2]), 3) for j in range(len(rows))])
loftf.save_npz(str(fl.W / 'data/cage_L0.npz'), P, cg['faces'])
