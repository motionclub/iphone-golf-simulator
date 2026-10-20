"""test: fair the whole ear region of the b5 patch (both sides) with several lam; writes data/fe_<lam>.npz.   python3 fairtest_ear.py lam [frozen_loops 0/1]"""
import sys, json
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import fair, feat_f
lam = float(sys.argv[1]); frz = int(sys.argv[2]) if len(sys.argv) > 2 else 0
pd = np.load('data/b9_patch.npz'); P = pd['P'].copy(); off = pd['Foff']; flat = pd['F']; pj = json.load(open('data/b9_patch.json'))
F = [np.asarray(flat[off[i]:off[i + 1]]) for i in range(len(off) - 1)]
adj = fair.vertex_adj(F, len(P))
ef = feat_f.EarField()
dE = feat_f.poly_signed_dist(P[:, 1], P[:, 2], ef.poly)
for side, sn in ((-1, 'L'), (+1, 'R')):
    frozen = set(pj['loops'][f'ear_attach_{sn}']) | set(pj['loops'][f'helix_{sn}']) | set(pj['loops'][f'concha_{sn}']) if frz else set()
    reg = np.where((np.sign(P[:, 0]) == side) & (np.abs(P[:, 0]) > 0.060) & (dE > -0.010) & (P[:, 1] > -0.03) & (P[:, 1] < 0.07) & (P[:, 2] > 1.46) & (P[:, 2] < 1.62))[0]
    print(sn, 'free', len(reg), 'frozen', len(frozen), 'max move mm %.2f' % (fair.fair(P, adj, reg, frozen=frozen, lam=lam) * 1000))
np.savez(f'data/fe_{lam}_{frz}.npz', V=P, F=flat, Foff=off)
