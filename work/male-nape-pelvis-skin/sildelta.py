"""Plate-vs-render rear-contour delta from the side silhouettes (left R edge, right -L edge), averaged, smoothed.
python3.13 sildelta.py <render sil dir> <out.json> [zlo zhi]   -> D(z) in metres: (plate - render), positive = plate is further back"""
import sys, json
sys.path.insert(0, '.')
import numpy as np
from contours import *
d = Path(sys.argv[1]); zlo = float(sys.argv[3]) if len(sys.argv) > 3 else 0.70; zhi = float(sys.argv[4]) if len(sys.argv) > 4 else 1.56
zs = np.arange(zlo, zhi + 1e-9, 0.002)
res = {}
for v, col in (('left', 1), ('right', 0)):
    t = contour(mask(M / f'{v}_target.png'), v, zs); n = contour(mask(d / f'{v}.png'), v, zs)
    sgn = 1 if v == 'left' else -1               # rear edge: left view -> max column, right view -> min column (negated)
    res[v] = sgn * (t[:, col] - n[:, col])
D = 0.5 * (res['left'] + res['right'])
def smooth(x, s):
    k = int(3 * s / 0.002); w = np.exp(-0.5 * (np.arange(-k, k + 1) * 0.002 / s) ** 2); w /= w.sum()
    m = np.isfinite(x); xi = np.interp(np.arange(len(x)), np.where(m)[0], x[m]); return np.convolve(np.pad(xi, k, mode='edge'), w, mode='valid')
Ds = smooth(D, 0.010)
json.dump(dict(z=zs.tolist(), D_raw=np.nan_to_num(D).tolist(), D=Ds.tolist(), left=np.nan_to_num(res['left']).tolist(), right=np.nan_to_num(res['right']).tolist()), open(sys.argv[2], 'w'))
for z in np.arange(0.72, 1.12, 0.02):
    i = int(round((z - zlo) / 0.002)); print(f'z {z:.2f}  left {res["left"][i]*1000:6.1f}  right {res["right"][i]*1000:6.1f}  mean-smooth {Ds[i]*1000:6.1f} mm  (plate - now)')
