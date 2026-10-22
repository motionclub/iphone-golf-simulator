import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, geo, facef, feat_f
H = geo.Head(); sk = facef.Skin(H)
xs = np.array([0.0, 0.02, 0.04, 0.06, 0.07, 0.08, 0.09, 0.095]); zs = np.full(len(xs), 1.5556)
P, N = sk.pt(xs, zs)
for x, p, n in zip(xs, P, N): print(x, np.round(p, 4), np.round(n, 3))
poly = feat_f.eye_poly(6); print('poly x range', poly[:, 0].min(), poly[:, 0].max(), 'z', poly[:, 1].min(), poly[:, 1].max())
print('a at z', H.L.at(np.array([1.5556]))['a'], 'nf', H.L.at(np.array([1.5556]))['nf'])
