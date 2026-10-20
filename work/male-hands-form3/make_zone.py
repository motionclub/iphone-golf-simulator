"""zone_R/L (arm zone + hand shell) for the 31,628-vertex current mesh, plus hand-only masks.  py.sh make_zone.py"""
import sys, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
from hlib import *
M = Mesh.from_npz(W / 'data/mesh_cur.npz'); V = M.V.astype(np.float64); n = len(V)
F2 = W.parent / 'male-arms-hands-form2'
for side, nm in ((+1, 'R'), (-1, 'L')):
    z0 = np.load(F2 / f'data/zone_{nm}.npy'); z = np.zeros(n, bool); z[:len(z0)] = z0
    sh = np.load(W / f'data/shellv_{side}.npy'); z[sh] = True
    np.save(W / f'data/zone_{nm}.npy', z)
    print(nm, 'zone', int(z.sum()), 'shell', len(sh), 'shell subset of zone', bool(z[sh].all()))
