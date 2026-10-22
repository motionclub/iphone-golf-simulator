import numpy as np
D = np.load('data/mesh_start.npz'); V = D['V'].astype(np.float64)
np.set_printoptions(precision=4, suppress=True, linewidth=160)
for side in (+1, -1):
    m = (side*V[:,0] > 0.19) & (V[:,2] > 0.84) & (V[:,2] < 1.05)
    idx = np.nonzero(m)[0]; zs = V[idx,2]
    levels = np.unique(np.round(zs, 4))
    rows = []
    for z in levels:
        sel = idx[np.abs(V[idx,2]-z) < 0.00055]
        if len(sel) < 10: continue
        P = V[sel]; c = P.mean(0)
        # robust semi-axes
        rows.append((z, len(sel), c[0], c[1], 0.5*(P[:,0].max()-P[:,0].min()), 0.5*(P[:,1].max()-P[:,1].min())))
    rows = np.array(rows)
    print('side', side); print(' z      n    cx      cy      semi_x  semi_y'); print(rows)
    # linear fit of the axis over z in [0.86, 0.98]
    sel = (rows[:,0] > 0.855) & (rows[:,0] < 0.99)
    for k, nm in ((2,'x'),(3,'y')):
        p = np.polyfit(rows[sel,0], rows[sel,k], 1); print('  axis', nm, 'slope d%s/dz = %.4f' % (nm, p[0]), 'intercept at z=.8456: %.4f' % np.polyval(p, 0.8456))
