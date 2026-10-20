"""Silhouette tools: hand-ROI XOR vs the frozen plate masks + full-body XOR/union per locked view (numpy rasteriser)."""
import numpy as np, sys
from pathlib import Path
from PIL import Image
W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
import lockcam as L
from hlib import Mesh
PL = W.parent / 'male-silhouette'
ROIS = {
 'bald_front': [('L', (100, 300, 205, 395)), ('R', (500, 300, 605, 395))],
 'bald_back': [('L', (670, 300, 775, 395)), ('R', (1060, 300, 1165, 395))],
 'sheet_front': [('L', (45, 160, 125, 225)), ('R', (250, 160, 330, 225))],
 'sheet_back': [('L', (355, 160, 435, 225)), ('R', (545, 160, 625, 225))],
}
_pl = {}
def plate(v):
    if v not in _pl: _pl[v] = np.array(Image.open(PL / f'{v}_target.png').convert('L')) > 127
    return _pl[v]
def tris_for(V, polys, arm_only=True):
    T = Mesh(V, polys).tris()
    return T
def roi_xor(V, T, sel=None, verbose=False):
    res = {}
    for v, rois in ROIS.items():
        for nm, (x0, y0, x1, y1) in rois:
            m = L.raster(V, T, v, sel=sel, roi=(x0, y0, x1, y1), ss=2)
            p = plate(v)[y0:y1, x0:x1]
            res[(v, nm)] = (int((m ^ p).sum()), int((m & ~p).sum()), int((p & ~m).sum()), int(p.sum()), int(m.sum()))
    tot = sum(r[0] for r in res.values())
    if verbose:
        for k, r in res.items(): print(k, 'xor', r[0], 'mesh-only', r[1], 'plate-only', r[2], 'plate', r[3], 'mesh', r[4])
    return tot, res
def full_sil(V, T, views=('bald_front', 'bald_back', 'left', 'right', 'sheet_front', 'sheet_back')):
    out = {}
    for v in views:
        m = L.raster(V, T, v, ss=2); p = plate(v)
        x = int((m ^ p).sum()); u = int((m | p).sum())
        out[v] = dict(xor=x, union=u, pct=round(100.0 * x / u, 3), plate_only=int((p & ~m).sum()), mesh_only=int((m & ~p).sum()))
    return out
def mesh_from(npz):
    M = Mesh.from_npz(npz); return M.V.astype(np.float64), M.polys, M.tris()
if __name__ == '__main__':
    import json
    for nm in sys.argv[1:]:
        path = W / 'data/mesh_cur.npz' if nm == 'base' else (W / 'data/mesh_start.npz' if nm == 'base0' else W / f'data/cand_{nm}.npz')
        V, polys, T = mesh_from(path)
        arm = (np.abs(V[:, 0]) > 0.2) & (V[:, 2] > 0.78) & (V[:, 2] < 1.40); sel = arm[T].all(1)
        tot, res = roi_xor(V, T, sel)
        fs = full_sil(V, T, ('bald_front', 'bald_back'))
        print(nm, 'hand ROI xor total', tot, {f'{k[0]}_{k[1]}': v[0] for k, v in res.items()}, 'full', {k: v['pct'] for k, v in fs.items()})
