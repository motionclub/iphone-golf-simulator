import numpy as np, sys
from femlib import *
M = np.load('data/plate_masks.npz')
m = Mesh.from_npz(W/'data/mesh_start.npz'); V = m.V.astype(np.float64); T = m.tris()
# whole-body mesh without hands/arms: use legs+torso only is hard; just rasterise everything
for view, anchor in (('sheet_left', 791.5), ('sheet_right', 1089.5)):
    PROF_Y0[view] = anchor
    roi = (700, 40, 1180, 345)
    mk = raster(V, T, view, roi, ss=2) 
    pl = M[view][40:345, 700:1180]
    print(view, 'anchor', anchor, 'xor %', round(100*(mk ^ pl).sum()/(mk | pl).sum(), 2))
    for z in (0.3, 0.5, 0.7, 0.9, 1.1, 1.3):
        r = int(round(338.5 - z/S_SHEET)) - 40
        xm = np.nonzero(mk[r])[0]; xp = np.nonzero(pl[r])[0]
        print('   z %.1f  model x %d..%d  plate %d..%d  -> front/back edge diff px (model-plate): %d / %d' % (z, xm.min()+700, xm.max()+700, xp.min()+700, xp.max()+700, xm.min()-xp.min(), xm.max()-xp.max()))
