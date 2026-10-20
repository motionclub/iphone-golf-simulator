"""Sub-pixel plate side contour, BACK edge (glute), from the multi-angle sheet profile panels (same anchoring as plate_side4.py).  -> data/plate_back_fine4.npy (z, y_back), calibrated on z .60-.78 to the old table"""
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from plate_side4 import im, S2, V0, PAN, gblur1
from targets import curves
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def back_edge(r, lo, hi):
    row = im[int(np.floor(r)), lo:hi] * (1 - (r - np.floor(r))) + im[int(np.floor(r)) + 1, lo:hi] * (r - np.floor(r))
    row = gblur1(row, 0.8); g = np.gradient(row)
    thr = max(2.5, 0.35 * np.abs(g).max())
    for i in range(len(g) - 3, 2, -1):             # scan from the right (outside) for the first strong positive gradient (body dark -> background light)
        if g[i] > thr:
            j = i - 3 + np.argmax(g[i - 3:i + 1])
            a, b, c = g[j - 1], g[j], g[j + 1]
            d = (a - c) / (2 * (a - 2 * b + c) + 1e-12)
            return lo + j + d
    return np.nan
zs = np.arange(0.70, 1.20, 0.01)
res = {}
for side in 'LR':
    p = PAN[side]
    res[side] = np.array([(back_edge(V0 - z / S2, p['lo'] + 20, p['hi'] + 40) - p['X0']) * S2 for z in zs])
(bz, b), _ = (None, None), None
(_, _), (bz, b) = curves()
T = np.interp(zs, bz, b)
avg = np.nanmean(np.stack([res['L'], res['R']]), 0)
c = np.nanmean((avg - T)[(zs >= 0.60) & (zs <= 0.78)]) if (zs <= 0.78).any() else 0.0
print('calibration offset avg-table (mm) over z .70-.78:', round(float(np.nanmean((avg - T)[(zs <= 0.78)])) * 1000, 2))
c = float(np.nanmean((avg - T)[(zs <= 0.78)]))
P = avg - c
np.save(HERE + '/data/plate_back_fine4.npy', np.stack([zs, P]))
print(' z    L(mm)  R(mm)  cal(mm)  table(mm)')
for z, a, b_, p, t in zip(zs, res['L'], res['R'], P, T):
    print(f'{z:.2f} {1000*a:+7.1f} {1000*b_:+7.1f} {1000*p:+7.1f} {1000*t:+7.1f}')
