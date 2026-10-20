import sys, pickle
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2')
import numpy as np
from ff_common import *

Vb, Fb = load_base()
Vf = np.load(W + '/tmp/V_f1.npy')
Vo = np.load(ROOT + '/work/male-parallel-legs/data/V_start_orig.npy')
wall = np.zeros(len(Vb), bool)
wall[:len(Vo)] = (np.abs(Vo[:, 0]) >= XMAX) & (Vo[:, 2] < 0.15)
print('wall verts', wall.sum(), ' left', (wall & (Vb[:, 0] > 0)).sum())
# region around the flap on the left foot
sel = (Vf[:, 0] > 0.24) & (Vf[:, 0] < 0.31) & (Vf[:, 1] > 0.035) & (Vf[:, 1] < 0.095) & (Vf[:, 2] < 0.075)
idx = np.where(sel)[0]
print('verts in region', len(idx), ' wall among them', wall[idx].sum())
d = np.linalg.norm(Vf[idx] - Vb[idx], axis=1) * 1000
order = idx[np.argsort(-d)]
print('idx   wall   base(x,y,z mm)              new(x,y,z mm)               disp mm')
for i in order[:40]:
    print(i, int(wall[i]), np.round(Vb[i] * 1000, 1), np.round(Vf[i] * 1000, 1), round(float(np.linalg.norm(Vf[i] - Vb[i]) * 1000), 2))
# wall strip: how thin are its faces in base and new
from collections import defaultdict
E = edges_of(Fb)
wl = [(a, b) for a, b in E if wall[a] and wall[b]]
lb = np.array([np.linalg.norm(Vb[a] - Vb[b]) for a, b in wl]) * 1000
lf = np.array([np.linalg.norm(Vf[a] - Vf[b]) for a, b in wl]) * 1000
print('wall-wall edges', len(wl), 'len mm base min/mean/max', lb.min().round(2), lb.mean().round(2), lb.max().round(2), ' new', lf.min().round(2), lf.mean().round(2), lf.max().round(2))
# wall <-> non-wall edges
wn = [(a, b) if wall[a] else (b, a) for a, b in E if wall[a] != wall[b]]
lb2 = np.array([np.linalg.norm(Vb[a] - Vb[b]) for a, b in wn]) * 1000
lf2 = np.array([np.linalg.norm(Vf[a] - Vf[b]) for a, b in wn]) * 1000
print('wall-nonwall edges', len(wn), 'len mm base min/mean/max', lb2.min().round(2), lb2.mean().round(2), lb2.max().round(2), ' new', lf2.min().round(2), lf2.mean().round(2), lf2.max().round(2))
# the displacement of wall verts vs. their non-wall neighbours
nb = defaultdict(list)
for a, b in E:
    nb[a].append(b); nb[b].append(a)
rel = []
for i in np.where(wall & (Vb[:, 0] > 0))[0]:
    nn = [j for j in nb[i] if not wall[j]]
    if not nn: continue
    dm = np.mean([np.linalg.norm((Vf[j] - Vb[j])) for j in nn]) * 1000
    di = np.linalg.norm(Vf[i] - Vb[i]) * 1000
    rel.append((i, di, dm))
rel = np.array(rel)
print('wall verts (left): own disp mm mean/max', rel[:, 1].mean().round(2), rel[:, 1].max().round(2), ' neighbour disp mean', rel[:, 2].mean().round(2), rel[:, 2].max().round(2))
