"""relief3b.py : glute relief table (back view, plate-pixel grid, fitted light x2.0):
  vertical profiles at x=+-0.045/+-0.07/+-0.095 : crescent dip (mean z .90-.94 - min z .805-.845) and rise (max z .85-.90 - min)
  horizontal profiles at z=.85/.88/.91          : cleft depth = mean(|x| in .045..075) - mean(|x|<.007)  (grey levels)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from photo3 import *
LB = np.array(LIGHT); LB[1:] *= 2.0
BOXB = roi_box('back', -0.15, 0.15, 0.76, 1.02)
PLATEB = plate_gray('back', BOXB).astype(float)
XSV = (0.045, 0.07, 0.095)
ZSH = (0.85, 0.88, 0.91)


def _col(x):
    c0, r0, c1, r1 = BOXB
    return BACK_CX - x / S - c0


def vprof(img, x, half=0.004):
    c0, r0, c1, r1 = BOXB
    col = _col(x)
    p = img[:, int(round(col - half / S)):int(round(col + half / S)) + 1].mean(1)
    zs = (SOLE - (np.arange(r0, r1) + 0.5)) * S
    return p, zs


def hprof(img, z, half=0.004):
    c0, r0, c1, r1 = BOXB
    row = SOLE - z / S - r0
    p = img[int(round(row - half / S)):int(round(row + half / S)) + 1, :].mean(0)
    xs = (BACK_CX - (np.arange(c0, c1) + 0.5)) / 1.0
    xs = (BACK_CX - (np.arange(c0, c1) + 0.5)) * S
    return p, xs


def measures(img):
    out = {}
    for x in XSV:
        for sg in (1, -1):
            p, zs = vprof(img, sg * x)
            mn = p[(zs > 0.805) & (zs < 0.845)].min()
            out[f'v{sg*x:+.3f}'] = (float(p[(zs > 0.90) & (zs < 0.94)].mean() - mn), float(p[(zs > 0.85) & (zs < 0.90)].max() - mn))
    for z in ZSH:
        p, xs = hprof(img, z)
        c = p[np.abs(xs) < 0.007].mean()
        out[f'h{z:.2f}'] = float(0.5 * (p[(xs > 0.045) & (xs < 0.075)].mean() + p[(xs < -0.045) & (xs > -0.075)].mean()) - c)
    return out


def model_img(co, normals=None):
    N = vertex_normals(co, TRI) if normals is None else normals
    sh = shade_vertices(co, N, 'back', LB)
    img, mask = raster_shaded(co, sh, 'back', BOXB)
    if mask.any():
        img = np.where(mask, img, img[mask].mean())
    return img


PM = measures(PLATEB)


def score(co, verbose=False):
    m = measures(model_img(co))
    errs = []
    for k, v in PM.items():
        a, b = (np.array(v, float).ravel(), np.array(m[k], float).ravel())
        for pa, pb in zip(a, b):
            errs.append(np.log(max(pb, 0.5) / max(pa, 0.5)))
    if verbose:
        for k in PM:
            print(f'  {k:8s} plate {np.round(PM[k],1)}  model {np.round(m[k],1)}')
    return float(np.mean(np.abs(errs))), m


if __name__ == '__main__':
    for f in sys.argv[1:]:
        s_, m = score(np.load(f), verbose=True)
        print(f, 'mean |log ratio|', round(s_, 3))
