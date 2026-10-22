import sys, pickle
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, loft as L, proxy as PX, sculpt as S, stage2 as S2, topo as T, wire
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
Vcc, Fcc = PX.build_proxy(3)
phi = S2.Phi(); phi.attach_cc(Vcc, Fcc)
Vn, Fn, info = S2.build_final(V, F, phi, eps=0.0004, max_level=3, min_face_level=1, verbose=False)
P1 = phi.stage1(Vn)
cen = np.array([P1[f].mean(axis=0) for f in Fn]); depth = np.array(info['depth'])
col = {0: (90, 90, 255), 1: (80, 220, 80), 2: (255, 200, 40), 3: (255, 60, 60)}
colors = np.array([col[min(int(d), 3)] for d in depth], np.uint8)
front = cen[:, 1] < -0.03
for name, sel, ax, b in (('front', front, (0, 2), (-0.11, 0.11, 1.43, 1.70)), ('side', cen[:, 0] > 0.0, (1, 2), (-0.12, 0.08, 1.43, 1.70))):
    wire.scatter(cen[sel][:, list(ax)], colors[sel], b, 900, str(H.W / f'r/depth_{name}.png'), r=2)
for d in range(4): print('depth', d, int((depth == d).sum()))
