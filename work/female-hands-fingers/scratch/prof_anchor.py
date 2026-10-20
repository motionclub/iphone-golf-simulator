import numpy as np
M = np.load('data/plate_masks.npz'); S2 = 1.7039/288.5
for nm in ('sheet_left', 'sheet_right'):
    m = M[nm]
    print(nm)
    for z in (0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.95, 1.10):
        r = int(round(338.5 - z/S2)); xs = np.nonzero(m[r])[0]
        if len(xs): print('  z %.2f row %d  x_range %d..%d  centre %.1f  width_cm %.1f' % (z, r, xs.min(), xs.max(), 0.5*(xs.min()+xs.max()), (xs.max()-xs.min())*S2*100))
# sole row check: lowest mask row
for nm in ('sheet_front','sheet_back','sheet_left','sheet_right'):
    ys, xs = np.nonzero(M[nm]); print(nm, 'lowest row', ys.max(), 'head top row', ys.min())
