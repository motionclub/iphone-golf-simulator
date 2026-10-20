"""vertical luminance profiles across the lower-pec region: plate vs plate-lit renders (avg of columns at |x| in .06-.13)"""
import sys; sys.path.insert(0, '.')
from relcorr import *
from PIL import Image
import numpy as np
c = CAM['bald_front']; mpp = c['metres_per_pixel']
def prof(img, xs):
    a = np.asarray(img.convert('L')).astype('float32'); out = []
    for z in np.arange(1.10, 1.34, 0.005):
        row = int(round(c['sole_y'] - z / mpp)); vals = []
        for x in xs: vals.append(a[row - 1:row + 2, int(round(c['centre_x'] + x / mpp)) - 1:int(round(c['centre_x'] + x / mpp)) + 2].mean())
        out.append(np.mean(vals))
    return np.array(out)
zs = np.arange(1.10, 1.34, 0.005); xs = [-0.13, -0.11, -0.09, -0.07, 0.07, 0.09, 0.11, 0.13]
P0 = prof(PL, xs); res = {'plate': P0}
for t in sys.argv[1:]: res[t] = prof(Image.open(f'r/{t}sh/front.png'), xs)
print('z      ' + '  '.join(f'{k:>7s}' for k in res))
for i, z in enumerate(zs):
    if i % 2 == 0: print(f'{z:.3f}  ' + '  '.join(f'{v[i]:7.1f}' for v in res.values()))
for k, v in res.items():
    # crease depth = (mean of the 3 brightest-above values at z>1.20 near the pec crest) - minimum below
    up = v[(zs > 1.21) & (zs < 1.30)].max(); lo = v[(zs > 1.12) & (zs < 1.22)].min(); print(f'{k:8s} pec crest-to-crease drop {up - lo:5.1f} lum  (crease at z={zs[(zs>1.12)&(zs<1.22)][np.argmin(v[(zs>1.12)&(zs<1.22)])]:.3f}, crest at z={zs[(zs>1.21)&(zs<1.30)][np.argmax(v[(zs>1.21)&(zs<1.30)])]:.3f})')
