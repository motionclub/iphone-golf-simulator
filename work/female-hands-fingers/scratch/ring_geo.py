import numpy as np
D = np.load('data/mesh_start.npz'); V = D['V'].astype(np.float64)
cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
polys = [tuple(int(x) for x in cv[s:s+t]) for s, t in zip(ls, lt)]
np.set_printoptions(precision=4, suppress=True, linewidth=160)
for side in (+1, -1):
    ring = np.load(f'data/start_hand_ring_{side}.npy'); P = V[ring]
    c = P.mean(0)
    # order by angle in xy about the centre
    ang = np.arctan2(P[:,1]-c[1], P[:,0]-c[0]); o = np.argsort(ang); P = P[o]; ring = ring[o]
    print('side', side, 'centre', c, 'z min/max', P[:,2].min(), P[:,2].max())
    ex = P[:,0].max()-P[:,0].min(); ey = P[:,1].max()-P[:,1].min()
    print('  extent x %.4f y %.4f  -> semi a %.4f b %.4f' % (ex, ey, ex/2, ey/2))
    d = np.linalg.norm(np.roll(P,-1,0)-P, axis=1); print('  edge lengths mm', np.round(d*1000,1), 'perimeter mm', d.sum()*1000)
    # neighbors up the arm: the arm-side verts adjacent to the ring
    rs = set(ring.tolist()); nb = set()
    for p in polys:
        if any(v in rs for v in p):
            for v in p:
                if v not in rs: nb.add(v)
    nb = np.array(sorted(nb)); hv = np.load(f'data/start_hand_verts_{side}.npy')
    arm_nb = [v for v in nb if V[v,2] > c[2]-1e-4]
    print('  adjacent non-ring verts', len(nb), 'on arm side (z>ring)', len(arm_nb), 'on hand side', len(set(nb.tolist()) & set(hv.tolist())))
    Pa = V[arm_nb]; print('  arm-side nbr z range', Pa[:,2].min(), Pa[:,2].max())
    # hand extents
    H = V[hv]; print('  hand verts bbox min', H.min(0), 'max', H.max(0))
