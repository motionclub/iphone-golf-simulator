"""test: fair the lower-head sides/back (jaw angle, behind the ear, nape top) of the b7 patch.   python3 jawtest2.py <lam>"""
import sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import fair
lam = float(sys.argv[1])
pd = np.load('data/b7_patch.npz'); P = pd['P'].copy(); off = pd['Foff']; flat = pd['F']
F = [np.asarray(flat[off[i]:off[i + 1]]) for i in range(len(off) - 1)]
adj = fair.vertex_adj(F, len(P))
ear = (np.abs(P[:, 0]) > 0.065) & (P[:, 1] > -0.03) & (P[:, 1] < 0.07) & (P[:, 2] > 1.455)
zone = np.where((P[:, 2] > 1.4125) & (P[:, 2] < 1.52) & (P[:, 1] > -0.075) & (~ear))[0]
print('zone', len(zone))
mv = fair.fair(P, adj, zone, lam=lam, rings=2)
print('max move mm %.2f' % (mv * 1000))
np.savez(f'data/jt2_{lam}.npz', V=P, F=flat, Foff=off)
