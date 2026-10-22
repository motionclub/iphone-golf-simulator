import numpy as np, sys
sys.path.insert(0,'.')
from hlib import *
M = Mesh.from_npz('data/mesh_start.npz'); V = M.V.astype(np.float64); polys = M.polys
used = np.zeros(len(V),bool)
for p in polys: used[list(p)] = True
orph = np.nonzero(~used)[0]
print('orphans', len(orph), V[orph].min(0) if len(orph) else None, V[orph].max(0) if len(orph) else None)
print(orph[:20], V[orph[:5]])
# polygon-vertex connectivity components restricted to the hand region
for side in (+1,-1):
    L = to_local(V, side); gx = side*V[:,0]
    for w0 in (-0.055,):
        Hs = (gx>0.30)&(V[:,2]<1.10)&(L[:,2]>=w0)
        rem = np.array([Hs[list(p)].any() for p in polys]); kept=~rem
        usedk = np.zeros(len(V),bool)
        for fi in np.nonzero(kept)[0]: usedk[list(polys[fi])] = True
        free = (~usedk)&used    # only verts that were used by some face
        print('side',side,'free (used by faces, only removed)',int(free.sum()),'Hs verts',int(Hs.sum()),'free subset of Hs?', bool((free&~Hs).sum()==0), (free&~Hs).sum())
        fv = np.nonzero(free)[0]
        Lf = L[fv]
        print('  free local w range', Lf[:,2].min(), Lf[:,2].max(), 'a range', Lf[:,0].min(), Lf[:,0].max())
