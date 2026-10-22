"""Sub-pixel plate side contour (front edge) from the multi-angle sheet profile panels, anchored like targets.py (knee-centre X0, V0 sole row).
python3 tools/plate_side4.py  -> data/plate_side_contour4.json  (z, y_front_L, y_front_R, y_back_L, y_back_R in metres, negative = forward)"""
import sys, json, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = HERE.rsplit('/work/', 1)[0]
im = np.asarray(Image.open(ROOT + '/ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('L')).astype(float)
S2 = 1.7039 / 288.5; V0 = 338.5
PAN = {'L': dict(X0=791.5, lo=745, hi=860), 'R': dict(X0=1095.0, lo=1050, hi=1165)}

def gblur1(a, s):
    k = np.arange(-int(4 * s) - 1, int(4 * s) + 2); w = np.exp(-0.5 * (k / s) ** 2); w /= w.sum()
    return np.convolve(np.pad(a, (len(k) // 2,) * 2, mode='edge'), w, mode='valid')

def edges_row(r, lo, hi, front=True):
    """subpixel x of the steepest bright->dark (front) or dark->bright (back) transition scanning from outside"""
    row = im[int(np.floor(r)), lo:hi] * (1 - (r - np.floor(r))) + im[int(np.floor(r)) + 1, lo:hi] * (r - np.floor(r))
    row = gblur1(row, 0.8)
    g = np.gradient(row)
    if front:
        # scan from the left (outside) for the first strong negative gradient (background light -> body dark)
        thr = -max(2.5, 0.35 * np.abs(g).max())
        for i in range(2, len(g) - 2):
            if g[i] < thr:
                j = i + np.argmin(g[i:i + 4])
                a, b, c = g[j - 1], g[j], g[j + 1]
                d = (a - c) / (2 * (a - 2 * b + c) + 1e-12)
                return lo + j + d
    return np.nan

def contour(side, zs):
    p = PAN[side]
    out = []
    for z in zs:
        r = V0 - z / S2
        x = edges_row(r, p['lo'], p['hi'], True)
        out.append((x - p['X0']) * S2 if np.isfinite(x) else np.nan)
    return np.array(out)

if __name__ == '__main__':
    zs = np.arange(0.95, 1.43, 0.01)
    fl, fr = contour('L', zs), contour('R', zs)
    from targets import curves
    (fz, f), _ = curves()
    ft = np.interp(zs, fz, f)
    res = {'z': zs.tolist(), 'front_L': fl.tolist(), 'front_R': fr.tolist(), 'table': ft.tolist()}
    json.dump(res, open(HERE + '/data/plate_side_contour4.json', 'w'), indent=0)
    print(' z     L(mm)   R(mm)  table(mm)')
    for z, a, b, t in zip(zs, fl, fr, ft):
        print(f'{z:.2f}  {1000*a:+7.1f} {1000*b:+7.1f}  {1000*t:+7.1f}')
