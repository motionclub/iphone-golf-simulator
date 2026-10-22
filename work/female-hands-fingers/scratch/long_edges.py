import sys, numpy as np
from femlib import *
tag = sys.argv[1]
M = Mesh.from_npz(W / f'data/cand_{tag}.npz'); V = M.V.astype(np.float64)
E = edges_of(M.polys)
L = np.linalg.norm(V[E[:,0]] - V[E[:,1]], axis=1)
sel = np.nonzero(L > 0.03)[0]
print('edges', len(E), 'long (>30mm):', len(sel))
# compare with base
B0 = Mesh.from_npz(W / 'data/mesh_start.npz'); E0 = edges_of(B0.polys); L0 = np.linalg.norm(B0.V[E0[:,0]].astype(float) - B0.V[E0[:,1]].astype(float), axis=1)
print('base long edges (>30mm):', int((L0 > 0.03).sum()), ' max base edge mm', L0.max()*1000)
for i in sel[:20]:
    a, b = E[i]; print(int(a), int(b), np.round(V[a]*1000, 1), np.round(V[b]*1000, 1), 'len mm', round(L[i]*1000, 1))
