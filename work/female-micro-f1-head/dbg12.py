import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl
d = np.load(fl.W / 'data/b3_patch.npz'); P = d['P']
sel = np.where((np.abs(P[:, 0]) < 0.0025) & (P[:, 1] < -0.04) & (P[:, 2] < 1.50) & (P[:, 2] > 1.415))[0]
o = sel[np.argsort(-P[sel, 2])]
prev = None
for i in o:
    p = P[i]; print(round(p[2], 4), round(p[1], 4), round(p[0], 4), '' if prev is None else round(np.linalg.norm(p - prev) * 1000, 1)); prev = p
