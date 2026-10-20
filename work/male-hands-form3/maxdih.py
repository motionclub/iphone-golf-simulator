"""py.sh maxdih.py base.json 'name={overrides}' ... -> max dihedral (all new faces / thumb-root faces within 25 mm of C_loop), ROI xor"""
import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3, evalp
from hlib import *
import metrics3
base = json.load(open(sys.argv[1]))
def run(name, p):
    Vn, polys, si = asm3.assemble(p, verbose=False)
    nnew = sum(len(si[s]['faces']) for s in (+1, -1)); idx = list(range(len(polys) - nnew, len(polys)))
    st = metrics3.dihedral_stats(Vn.astype(np.float64), polys, idx)
    # near thumb root: faces whose centroid is within 25 mm of C_loop (R hand)
    info = si[+1]['info']; C = to_global(np.array([info['C_loop']]), +1)[0]
    Fn = face_normals(Vn.astype(np.float64), polys); ef = edge_faces(polys)
    cent = lambda f: Vn[list(polys[f])].mean(0)
    mx = 0; m25 = 0; n60 = 0
    for (a, b), fs in ef.items():
        if len(fs) == 2 and fs[0] >= idx[0] and fs[1] >= idx[0]:
            dd = np.linalg.norm(0.5 * (Vn[a] + Vn[b]) - C); ang = np.degrees(np.arccos(np.clip((Fn[fs[0]] * Fn[fs[1]]).sum(), -1, 1)))
            if dd < 0.060: mx = max(mx, ang)
            if dd < 0.025:
                m25 = max(m25, ang); n60 += int(ang > 60)
    r = evalp.evaluate(p)
    print('%-22s max all %5.1f gt60 %2d gt90 %d | root25mm max %5.1f (>60: %d) | 60mm %5.1f | roi %d bf %.3f bb %.3f' % (name, st['max'], st['gt60'], st['gt90'], m25, n60, mx, r['roi_total'], r['full']['bald_front'], r['full']['bald_back']))
run('base', base)
for a in sys.argv[2:]:
    n, js = a.split('=', 1); p = dict(base); p.update(json.loads(js)); run(n, p)
