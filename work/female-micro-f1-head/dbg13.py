import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl
d = np.load(fl.W / 'data/b3_patch.npz'); P = d['P']; F = d['F']; off = d['Foff']
Fl = [F[off[i]:off[i+1]] for i in range(len(off)-1)]
for z0 in np.arange(1.42, 1.50, 0.01):
    L = []; nq = 0; nt = 0
    for f in Fl:
        c = P[f].mean(0)
        if abs(c[0]) < 0.03 and c[1] < -0.08 and z0 <= c[2] < z0 + 0.01:
            nq += len(f) == 4; nt += len(f) == 3
            for i in range(len(f)): L.append(np.linalg.norm(P[f[i]] - P[f[(i+1) % len(f)]]))
    if L: print(f'z {z0:.3f}: faces quad {nq} tri {nt}  edge mm mean {np.mean(L)*1000:.1f} max {np.max(L)*1000:.1f}')
