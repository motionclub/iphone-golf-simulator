import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo, cage
d = np.load(fl.W / 'data/ring.npz'); ring_pos = d['pos']
H = geo.Head(); cg = cage.build_cage(ring_pos, geo.C, H=H)
U = cg['u']; P = H.phi(U)
for v, p in cg['pinned'].items(): P[v] = p
rows = cg['rows']; B = cg['B']; s = cg['shift']; nB = len(B)
Bs = [B[(c + s) % nB] for c in range(nB)]
th = np.arctan2(U[Bs, 1], U[Bs, 0])
for c in np.argsort(np.abs(th + np.pi / 2))[:3].tolist() + np.argsort(np.abs(th - np.pi / 2))[:1].tolist():
    print('col', c, 'azimuth deg %.0f' % np.degrees(th[c]))
    print('  B   ', np.round(P[Bs[c]], 4))
    for j, r in enumerate(rows):
        v = r[c]; print('  row', j, 'pinned' if v in cg['pinned'] else '      ', np.round(P[v], 4))
