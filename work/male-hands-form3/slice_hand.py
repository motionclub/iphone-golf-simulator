"""cross-section extents of the arm+hand along the hand axis w (local frame) on the current mesh, both hands. py.sh slice_hand.py [npz]"""
import sys, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
from hlib import *
npz = sys.argv[1] if len(sys.argv) > 1 else str(W / 'data/mesh_cur.npz')
M = Mesh.from_npz(npz); V = M.V.astype(np.float64); polys = M.polys
for side in (+1, -1):
    L = to_local(V, side); gx = side * V[:, 0]
    sel = (gx > 0.30) & (V[:, 2] < 1.10)
    print('side', side, 'verts', int(sel.sum()))
    print('   w(mm)   a_min  a_max  width |  n_min  n_max  depth   (mm; a\'=across (+thumb side/front), n=palm normal)')
    for w0 in np.arange(-0.20, 0.200, 0.01):
        m = sel & (L[:, 2] >= w0) & (L[:, 2] < w0 + 0.01)
        if m.sum() < 4: continue
        a = L[m, 0] * 1000; n = L[m, 1] * 1000
        print('  %6.0f  %6.1f %6.1f %6.1f | %6.1f %6.1f %6.1f' % ((w0 + 0.005) * 1000, a.min(), a.max(), a.max() - a.min(), n.min(), n.max(), n.max() - n.min()))
    break
