"""quick evaluation of a parameter set: python evalp.py '<json>'  -> ROI xor + full sil"""
import sys, json, time
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3, sil3
from hlib import *
def evaluate(params, full=True):
    t = time.time()
    Vn, polys, si = asm3.assemble(params, verbose=False)
    M = Mesh(Vn.astype(np.float32), polys); T = M.tris()
    N0 = asm3.N0
    zone = np.load(W / 'data/zone_R.npy') | np.load(W / 'data/zone_L.npy')
    flag = np.r_[zone, np.ones(len(Vn) - N0, bool)]
    sel = flag[T].all(1)
    tot, res = sil3.roi_xor(Vn.astype(np.float64), T, sel)
    out = dict(roi_total=tot, roi={f'{k[0]}_{k[1]}': v[0] for k, v in res.items()})
    if full:
        fs = sil3.full_sil(Vn.astype(np.float64), T, ('bald_front', 'bald_back'))
        out['full'] = {k: v['pct'] for k, v in fs.items()}
    out['sec'] = round(time.time() - t, 1)
    return out
if __name__ == '__main__':
    p = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(evaluate(p)))
