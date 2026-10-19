"""Per-height comparison in the crown+chin frame (mm): profile front edge (ours vs ref) and front half-width (ours vs ref).
python3 tools/table.py <tag> [zmin zmax step]"""
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import align2 as A
from PIL import Image
tag = sys.argv[1]
z0, z1, st = (float(v) for v in (sys.argv[2:5] if len(sys.argv) > 4 else (1.42, 1.56, .004)))
def edge_table(tag):
    out = {}
    for view in ('front', 'side'):
        A.render('crownchin', view, [tag], A.W + f'eval/ov2_crownchin_{view}_{tag}.png')
        img = np.asarray(Image.open(A.W + f'eval/ov2_crownchin_{view}_{tag}.png').convert('RGB'))
        refm = (img[..., 1] == 200) & (img[..., 0] == 0)   # green outline pixels
        om = np.load(A.W + f'eval/{tag}_{view}_mask.npy')
        out[view] = (refm, om)
    return out
T = edge_table(tag)
print(' z     | prof ours  ref   d(+=ours fwd) | half ours  ref   d')
rows = []
for z in np.arange(z1, z0 - 1e-9, -st):
    r = int(round((A.C[2] + A.H - z) / A.MPP))
    rs, os_ = T['side']; rf, of = T['front']
    def first(m): c = np.nonzero(m[r])[0]; return c.min() if len(c) else None
    pso = first(os_); psr = first(rs)
    po = None if pso is None else (A.C[1] - A.H + pso * A.MPP) * 1000
    pr = None if psr is None else (A.C[1] - A.H + psr * A.MPP) * 1000
    co = np.nonzero(of[r])[0]; cr = np.nonzero(rf[r])[0]
    ho = (co.max() - co.min()) / 2 * A.MPP * 1000 if len(co) else None
    hr = (cr.max() - cr.min()) / 2 * A.MPP * 1000 if len(cr) > 1 else None
    f = lambda v: '  -   ' if v is None else f'{v:6.1f}'
    d1 = None if po is None or pr is None else pr - po
    d2 = None if ho is None or hr is None else ho - hr
    print(f'{z:.3f} | {f(po)} {f(pr)} {f(d1)} | {f(ho)} {f(hr)} {f(d2)}')
