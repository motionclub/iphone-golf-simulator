import sys, numpy as np
from femlib import *
tag = sys.argv[1]
M = Mesh.from_npz(W / f'data/cand_{tag}.npz'); V = M.V.astype(np.float64)
N0 = 22419
hv = np.zeros(len(V), bool)
for s in (1, -1): hv[np.load(W / f'data/start_hand_verts_{s}.npy')] = True
hv[N0:] = True
E = edges_of(M.polys); L = np.linalg.norm(V[E[:,0]] - V[E[:,1]], axis=1)
inh = hv[E[:,0]] & hv[E[:,1]]
print('hand edges', int(inh.sum()), 'max len mm', round(L[inh].max()*1000, 1), ' mean', round(L[inh].mean()*1000, 2))
sel = np.nonzero(inh & (L > 0.02))[0]
for i in sel[:20]:
    a, b = E[i]; print(int(a), int(b), np.round(V[a]*1000, 1), np.round(V[b]*1000, 1), 'len mm', round(L[i]*1000, 1))
# vertices with no face
used = np.zeros(len(V), bool)
for p in M.polys: used[list(p)] = True
print('unused verts overall', int((~used).sum()), ' unused in hand sets', int((~used & hv).sum()))
