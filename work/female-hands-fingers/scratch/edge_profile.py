import numpy as np
from femlib import *
M = np.load('data/plate_masks.npz')
S = S_BALD
print(' z     | front +x: lat  med | front -x: lat  med | back +x lat med | back -x lat med   (|x| in mm of lateral/medial hand edges)')
rows = []
for z in np.arange(0.88, 0.66, -0.02):
    r = int(round(Z0_BALD - z/S))
    out = []
    for view, side, (x0, x1) in (('bald_front', +1, (500, 575)), ('bald_front', -1, (305, 380)), ('bald_back', +1, (715, 790)), ('bald_back', -1, (905, 980))):
        row = M[view][r, x0:x1]; xs = np.nonzero(row)[0] + x0
        if len(xs) == 0: out += [np.nan, np.nan]; continue
        # contiguous run containing the arm/hand: take the run with the largest |x| extent from the body centre
        segs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
        seg = max(segs, key=lambda s: len(s)) if False else segs[-1] if (view == 'bald_front' and side > 0) or (view == 'bald_back' and side < 0) else segs[0]
        if view == 'bald_front': xa = (seg.min() - 0.5 - 440) * S; xb = (seg.max() + 0.5 - 440) * S
        else: xa = (847 - (seg.max() + 0.5)) * S; xb = (847 - (seg.min() - 0.5)) * S
        lo, hi = min(xa, xb), max(xa, xb)
        if side > 0: lat, med = hi, lo
        else: lat, med = -lo, -hi
        out += [lat*1000, med*1000]
    rows.append((z, out))
    print('%.2f | %6.1f %6.1f | %6.1f %6.1f | %6.1f %6.1f | %6.1f %6.1f' % (z, *out))
arr = np.array([r[1] for r in rows]); z = np.array([r[0] for r in rows])
lat = np.nanmean(arr[:, [0, 2, 4, 6]], axis=1); med = np.nanmean(arr[:, [1, 3, 5, 7]], axis=1)
print('mean lateral edge |x| mm:', np.round(lat, 1)); print('mean medial edge |x| mm:', np.round(med, 1))
np.save('data/plate_edge_profile.npy', np.stack([z, lat, med], 1))
