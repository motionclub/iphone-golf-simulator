import sys, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
Vn, polys, si = asm3.assemble({}, verbose=True)
V0 = asm3.V0.astype(np.float32); N0 = asm3.N0
print('rebuilt verts', len(Vn), 'orig', N0)
d = np.linalg.norm(Vn[:N0].astype(np.float32) - V0, axis=1) * 1000
print('max displacement vs installed FORM2 mesh (mm): %.4f ; moved verts (>1e-4 mm): %d' % (d.max(), int((d > 1e-4).sum())))
M0 = asm3.POLYS0
def canon(p):
    p = list(p); k = p.index(min(p)); return tuple(p[k:] + p[:k])
from collections import Counter
print('polys multiset equal to installed:', Counter(canon(p) for p in polys) == Counter(canon(p) for p in M0))
