"""Write an npz holding only the faces of one finger / the thumb of the R hand (for isolated close-ups).
py.sh fingeriso.py <out.npz> '<params json>' <k|thumb>"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
out = sys.argv[1]; params = json.loads(sys.argv[2]); which = sys.argv[3]
Vn, polys, si = asm3.assemble(params, verbose=False)
m = si[+1]['mapping']; info = si[+1]['info']
if which == 'thumb':
    ids = set(m[v] for r in info['thumb_rows'] for v in r) | {m[info['thumb_tip']]}
else:
    rows, C = info['fin_rows'][int(which)]
    ids = set(m[v] for r in rows for v in r) | {m[C]}
sel = [p for p in polys if all(v in ids for v in p)]
M = Mesh(Vn.astype(np.float32), sel); cv, ls, lt = M.arrays()
np.savez(out, V=M.V, corner_verts=cv, loop_start=ls, loop_total=lt)
print(out, len(sel), 'faces')
