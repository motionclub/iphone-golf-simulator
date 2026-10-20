"""relief3.py : 1-D crescent/highlight relief table, plate vs model, at the plate pixel grid with the fitted light (no Blender).
dip  = mean(z 1.13..1.15) - min(z 1.165..1.205)   (underbust crescent depth, grey levels)
rise = max(z 1.23..1.29) - min(z 1.165..1.205)    (crescent -> upper highlight)
table(co) -> {x: (dip, rise)} ; compare(co) -> score + table vs plate"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from photo3 import *

XS = (-0.105, -0.09, -0.075, 0.075, 0.09, 0.105)
LF = np.array(LIGHT); LF[1:] *= 2.5
BOX = roi_box('front', -0.13, 0.13, 1.10, 1.32)
PLATE = plate_gray('front', BOX).astype(float)
_N0 = None


def _prof(img, x, half=0.005):
    c0, r0, c1, r1 = BOX
    col = FRONT_CX + x / S - c0
    cs = slice(int(round(col - half / S)), int(round(col + half / S)) + 1)
    p = img[:, cs].mean(1)
    zs = (SOLE - (np.arange(r0, r1) + 0.5)) * S
    return p, zs


def _dr(img, x):
    p, zs = _prof(img, x)
    base = p[(zs > 1.13) & (zs < 1.15)].mean()
    mn = p[(zs > 1.165) & (zs < 1.205)].min()
    return float(base - mn), float(p[(zs > 1.23) & (zs < 1.29)].max() - mn)


def model_img(co, light=None, normals=None):
    N = vertex_normals(co, TRI) if normals is None else normals
    sh = shade_vertices(co, N, 'front', LF if light is None else light)
    img, mask = raster_shaded(co, sh, 'front', BOX)
    if mask.any():
        img = np.where(mask, img, img[mask].mean())
    return img


def table(co):
    im = model_img(co)
    return {x: _dr(im, x) for x in XS}


PT = {x: _dr(PLATE, x) for x in XS}


def score(co, verbose=False):
    t = table(co)
    errs = []
    for x in XS:
        for k in (0, 1):
            errs.append(np.log(max(t[x][k], 0.5) / max(PT[x][k], 0.5)))
    if verbose:
        for x in XS:
            print(f'  x {x:+.3f}  plate dip/rise {PT[x][0]:5.1f}/{PT[x][1]:5.1f}   model {t[x][0]:5.1f}/{t[x][1]:5.1f}')
    return float(np.mean(np.abs(errs))), t


if __name__ == '__main__':
    for f in sys.argv[1:]:
        s_, t = score(np.load(f), verbose=True)
        print(f, 'mean |log ratio|', round(s_, 3))
