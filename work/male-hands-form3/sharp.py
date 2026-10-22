"""list edges of the new hand shell with dihedral > thr (default 70 deg) and their local positions.  py.sh sharp.py '<params json>' [thr]"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
prm = json.loads(sys.argv[1]); thr = float(sys.argv[2]) if len(sys.argv) > 2 else 70
Vn, polys, si = asm3.assemble(prm, verbose=False)
nnew = sum(len(si[s]['faces']) for s in (+1, -1)); idx = set(range(len(polys) - nnew, len(polys)))
ef = edge_faces(polys); Fn = face_normals(Vn.astype(np.float64), polys)
inv = {}
for s in (+1, -1):
    for b, v in si[s]['mapping'].items(): inv[v] = (s, b)
for (a, b), fs in ef.items():
    if len(fs) == 2 and fs[0] in idx and fs[1] in idx:
        ang = np.degrees(np.arccos(np.clip((Fn[fs[0]] * Fn[fs[1]]).sum(), -1, 1)))
        if ang > thr:
            side = +1 if Vn[a][0] > 0 else -1
            L = to_local(Vn[[a, b]].astype(float), side) * 1000
            print('%.1f deg  side %+d  mid local (a,n,w) = (%.1f, %.1f, %.1f) mm  verts %s %s' % (ang, side, *L.mean(0), inv.get(a), inv.get(b)))
