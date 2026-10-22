"""test: soften the jaw crease (loft/under blend zone) of the b7 patch.   python3 jawtest.py <lam> <band>   -> data/jt_<lam>.npz"""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import fair, geo
lam = float(sys.argv[1]); band = float(sys.argv[2])
pd = np.load('data/b17_patch.npz'); P = pd['P'].copy(); off = pd['Foff']; flat = pd['F']
F = [np.asarray(flat[off[i]:off[i + 1]]) for i in range(len(off) - 1)]
adj = fair.vertex_adj(F, len(P))
H = geo.Head()
u = P - geo.C[None, :]; u /= np.linalg.norm(u, axis=1, keepdims=True)
sel0 = (P[:, 2] > 1.405) & (P[:, 2] < 1.52) & (P[:, 1] < 0.05)
idx = np.where(sel0)[0]
rl = H.r_loft(u[idx]); ru = H.r_under(u[idx])
d = np.abs(rl - ru)
zone = idx[(d < band) & (ru < 5)]
# keep the chin centre and the mouth/lip area out; keep z<1.495
zone = np.array([v for v in zone if P[v, 2] < 1.495 and abs(P[v, 0]) > 0.012])
print('zone', len(zone), 'x range', P[zone, 0].min(), P[zone, 0].max(), 'z', P[zone, 2].min(), P[zone, 2].max())
mv = fair.fair(P, adj, zone, lam=lam, rings=2)
print('max move mm %.2f' % (mv * 1000))
np.savez(f'data/jt_{lam}.npz', V=P, F=flat, Foff=off)
