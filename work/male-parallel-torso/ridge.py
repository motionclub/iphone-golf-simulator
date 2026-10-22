import sys, numpy as np
from zone import *
tag = sys.argv[1]; V = np.load(f'data/V_{tag}.npy')
back = V0[:, 1] > -0.04
print('rings near z=1.31 (back, |x|<0.2): unique z (mm):', np.unique(np.round(V0[back & (np.abs(V0[:,0])<0.2) & (V0[:,2]>1.27) & (V0[:,2]<1.36), 2]*1000)).astype(int))
for xc in (0.0, 0.04, 0.08, 0.12, 0.16, 0.20):
    sel = back & (np.abs(np.abs(V0[:, 0]) - xc) < 0.012) & (V0[:, 2] > 1.26) & (V0[:, 2] < 1.37)
    o = np.argsort(V0[sel, 2]); zz = V0[sel, 2][o] * 1000; yy = V[sel, 1][o] * 1000; y0 = V0[sel, 1][o] * 1000
    # local second difference of y over z bins
    bins = np.arange(1260, 1370, 5); out = []
    for b in bins:
        m = (zz >= b) & (zz < b + 5)
        out.append(f'{yy[m].mean():6.1f}' if m.any() else '   -- ')
    print(f'x~{xc:.2f} ' + ' '.join(out))
print('z bins  ', ' '.join(f'{b:6d}' for b in np.arange(1260, 1370, 5)))
