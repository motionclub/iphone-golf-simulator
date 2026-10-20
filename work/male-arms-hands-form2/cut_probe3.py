import numpy as np, sys
sys.path.insert(0,'.')
from hlib import *
M = Mesh.from_npz('data/mesh_start.npz'); V = M.V.astype(np.float64); polys = M.polys
for side in (+1,-1):
    c = extract_cut(V, polys, side, -0.055)
    L = c['L']; ring = c['ring']
    print('side',side,'ring',len(ring),'removed faces',int(c['removed'].sum()),'free',int(c['free'].sum()))
    Lr = L[ring]
    print('  ring local w: min %.4f max %.4f  a: %.4f..%.4f  n: %.4f..%.4f'%(Lr[:,2].min(),Lr[:,2].max(),Lr[:,0].min(),Lr[:,0].max(),Lr[:,1].min(),Lr[:,1].max()))
    rf = [len(polys[i]) for i in np.nonzero(c['removed'])[0]]
    import collections; print('  removed face sizes', collections.Counter(rf))
    np.save(f'data/ring_{side}.npy', np.array(ring))
    np.save(f'data/free_{side}.npy', np.nonzero(c['free'])[0])
    np.save(f'data/removed_{side}.npy', np.nonzero(c['removed'])[0])
