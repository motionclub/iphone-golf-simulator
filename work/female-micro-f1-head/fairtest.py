"""quick test: fair the chin underside of the b3 patch and write data/fairtest.npz for ul.py.   python3 fairtest.py <lam> [xmax ymin ymax zmin zmax]"""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import fair
lam = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
box = [float(v) for v in sys.argv[2:7]] if len(sys.argv) >= 7 else [0.050, -0.140, -0.050, 1.412, 1.455]
pd = np.load('data/b3_patch.npz'); P = pd['P'].copy(); off = pd['Foff']; flat = pd['F']
F = [np.asarray(flat[off[i]:off[i + 1]]) for i in range(len(off) - 1)]
adj = fair.vertex_adj(F, len(P))
xmax, ymin, ymax, zmin, zmax = box
free = np.where((np.abs(P[:, 0]) < xmax) & (P[:, 1] > ymin) & (P[:, 1] < ymax) & (P[:, 2] > zmin) & (P[:, 2] < zmax))[0]
print('free', len(free))
d = fair.fair(P, adj, free, lam=lam, rings=1)
print('max displacement mm', d * 1000)
np.savez('data/fairtest.npz', V=P, F=flat, Foff=off)
