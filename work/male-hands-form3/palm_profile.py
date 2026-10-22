"""Print the palm ring profile (a' extent, n extent, centre, ring w) of a candidate / the current mesh.  py.sh palm_profile.py [tag]"""
import sys, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
tag = sys.argv[1] if len(sys.argv) > 1 else None
import json
params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
Vn, polys, si = asm3.assemble(params, verbose=False)
side = +1
m = si[side]['mapping']; info = si[side]['info']; P = info['P']
def Lp(vid): return to_local(Vn[[m[vid]]], side)[0]
print('knuckle w', P['w_knuckle'], 'tips', [round(x, 4) for x in P['f_tip']])
print(' row   w(mm)  a_min  a_max  width | n_min  n_max  depth  centre_n | a_ctr')
for r, ids in sorted(info['ring'].items()):
    pts = np.array([Lp(v) for v in ids if v in m])
    a = pts[:, 0] * 1000; n = pts[:, 1] * 1000; w = pts[:, 2].mean() * 1000
    print(' %3d  %6.1f  %6.1f %6.1f %6.1f | %6.1f %6.1f %6.1f  %6.1f | %6.1f' % (r, w, a.min(), a.max(), a.max() - a.min(), n.min(), n.max(), n.max() - n.min(), 0.5 * (n.max() + n.min()), 0.5 * (a.max() + a.min())))
# weld ring
ro = info['ring_o']; pts = np.array([Lp(v) if v >= asm3.N0 else to_local(Vn[[v]], side)[0] for v in ro])
a = pts[:, 0] * 1000; n = pts[:, 1] * 1000
print(' weld %6.1f  %6.1f %6.1f %6.1f | %6.1f %6.1f %6.1f  %6.1f | %6.1f' % (pts[:, 2].mean() * 1000, a.min(), a.max(), a.max() - a.min(), n.min(), n.max(), n.max() - n.min(), 0.5 * (n.max() + n.min()), 0.5 * (a.max() + a.min())))
# finger roots
for k, (rows, C) in info['fin_rows'].items():
    pts = np.array([Lp(v) for v in rows[0]]); tip = Lp(C)
    print(' finger', k, 'first ring w %.1f  tip pole w %.1f  length from knuckle ring %.1f mm; a_ctr first ring %.1f' % (pts[:, 2].mean() * 1000, tip[2] * 1000, (tip[2] - P['w_knuckle']) * 1000, pts[:, 0].mean() * 1000))
