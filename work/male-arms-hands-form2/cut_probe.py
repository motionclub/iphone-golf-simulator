import numpy as np, sys
sys.path.insert(0,'.')
from hlib import *
M = Mesh.from_npz('data/mesh_start.npz'); V = M.V.astype(np.float64); polys = M.polys
print('verts', len(V), 'polys', len(polys))
for side in (+1,-1):
    L = to_local(V, side)
    gx = side*V[:,0]
    for w0 in (-0.07,-0.06,-0.055,-0.05):
        Hs = (gx>0.30)&(V[:,2]<1.10)&(L[:,2]>=w0)
        rem = np.array([Hs[list(p)].any() for p in polys])
        kept = ~rem
        used = np.zeros(len(V),bool)
        for fi in np.nonzero(kept)[0]: used[list(polys[fi])] = True
        free = (~used)&((gx>0.20)|True)
        # boundary of kept faces
        ec = defaultdict(int)
        for fi in np.nonzero(kept)[0]:
            p=polys[fi]
            for k in range(len(p)):
                a,b=p[k],p[(k+1)%len(p)]; ec[(min(a,b),max(a,b))]+=1
        bnd=[e for e,c in ec.items() if c==1]
        bv=set(v for e in bnd for v in e)
        # only boundary edges near this hand
        bnd_hand=[e for e in bnd if gx[e[0]]>0.2 and gx[e[1]]>0.2]
        print(side,w0,'removed faces',int(rem.sum()),'free verts',int(free.sum()),'boundary edges (hand side)',len(bnd_hand), 'free x range', V[free][:,0].min() if free.any() else None)
