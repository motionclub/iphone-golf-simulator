"""Palmar / dorsal contour of the palm at fixed a' stations vs w (rows), R hand, for several param sets.
py.sh sagittal.py name1 '<json>' name2 '<json>' ...   prints n_palmar(a'=-20,0,+20) and n_dorsal(a'=0) per row"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
for i in range(1, len(sys.argv), 2):
    name, prm = sys.argv[i], json.loads(sys.argv[i + 1])
    Vn, polys, si = asm3.assemble(prm, verbose=False)
    m = si[+1]['mapping']; info = si[+1]['info']
    Lp = lambda vid: to_local(Vn[[m[vid]]], +1)[0] * 1000
    print('===', name, ' (n palmar side at a\'=-25 / 0 / +20 ; dorsal n at a\'=0 ; mm)')
    for r, ids in sorted(info['ring'].items()):
        pts = np.array([Lp(v) for v in ids if v in m])
        def band(a0, sel):
            q = pts[np.abs(pts[:, 0] - a0) < 7.0]
            return (q[:, 1].max() if sel == 'p' else q[:, 1].min()) if len(q) else float('nan')
        print('  row %2d w=%6.1f   palmar n: %6.1f %6.1f %6.1f   dorsal n(0): %6.1f   thickness(0): %5.1f' % (r, pts[:, 2].mean(), band(-25, 'p'), band(0, 'p'), band(20, 'p'), band(0, 'd'), band(0, 'p') - band(0, 'd')))
