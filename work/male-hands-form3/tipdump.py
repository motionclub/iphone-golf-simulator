"""Print tip geometry per finger: last rings (a/n/w extents), pole.  py.sh tipdump.py '<params json>'"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
Vn, polys, si = asm3.assemble(params, verbose=False)
side = +1; m = si[side]['mapping']; info = si[side]['info']; P = info['P']
Lp = lambda vid: to_local(Vn[[m[vid]]], side)[0]
for k, (rows, C) in info['fin_rows'].items():
    pole = Lp(C)
    print('finger', k, 'pole local (a,n,w) mm = (%.1f, %.1f, %.1f)' % tuple(pole * 1000))
    ncap = len(P['cap_angles'])
    for j in range(len(rows) - ncap - 2, len(rows)):
        pts = np.array([Lp(v) for v in rows[j]]); c = pts.mean(0)
        print('   ring %2d  w=%.1f  a-width %.1f  n-extent %.1f (n %.1f..%.1f)' % (j, pts[:, 2].mean() * 1000, (pts[:, 0].max() - pts[:, 0].min()) * 1000, (pts[:, 1].max() - pts[:, 1].min()) * 1000, pts[:, 1].min() * 1000, pts[:, 1].max() * 1000))
    if k == 1: break
