import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo, cage
d = np.load(fl.W / 'data/ring.npz'); ring_pos = d['pos']
H = geo.Head(); C = geo.C
cg = cage.build_cage(ring_pos, C, H=H)
oK = cg['collar_order']
k = 10; R = ring_pos[oK[k]]; print('R', R)
zs = np.linspace(R[2] + 0.001, 1.50, 200)
pw = H.neck_wall_point(R, zs); dw = pw - C; rw = np.linalg.norm(dw, axis=1); uw = dw / rw[:, None]
rh = H.r_head(uw); rn = H.r_neck(uw); rb = H.r_base(uw)
P = H.phi(uw)
for i in range(0, 200, 8): print(round(zs[i], 4), 'rw %.4f rhead %.4f rneck %.4f rbase %.4f' % (rw[i], rh[i], rn[i], rb[i]), 'phi z %.4f y %.4f' % (P[i, 2], P[i, 1]), 'wall y %.4f' % pw[i, 1])
