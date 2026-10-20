"""structure-correlation score: NCC of band-pass maps (plate vs render) inside a model-space box, same processing for both"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from viz3 import *

def roi_pix(roi, x0, x1, z0, z1):
    """model-space box -> pixel box in the upsampled ROI image (same frame as the plate crop / render)"""
    r = ROIS[roi]; sh = roi_shot('t', roi)
    W, H = sh['res']; xc, zc, w = sh['xc'], sh['zc'], sh['w']
    pxm = W / w                         # px per metre
    if roi in ('chest', 'chestW', 'torso_front'):
        cols = [(x - xc) * pxm + W / 2 for x in (x0, x1)]
    else:                               # back view: image right = -x
        cols = [(-(x - xc)) * pxm + W / 2 for x in (x0, x1)]
    rows = [H / 2 - (z - zc) * pxm for z in (z1, z0)]
    return int(min(cols)), int(min(rows)), int(max(cols)), int(max(rows))

def ncc(roi, render_png, box, s1=1.2, s2=9.0, gain=4.0):
    sc = ROIS[roi]['scale']
    a = np.asarray(bandpass(plate_crop(roi, 1.0), sc, s1, s2, gain).convert('L'), float)
    b = np.asarray(bandpass(bgcomp(render_png), sc, s1, s2, gain).convert('L'), float)
    x0, y0, x1, y1 = roi_pix(roi, *box)
    a, b = a[y0:y1, x0:x1], b[y0:y1, x0:x1]
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))

if __name__ == '__main__':
    roi = sys.argv[1]
    box = {'chest': (-0.12, 0.12, 1.14, 1.32), 'pelvis': (-0.15, 0.15, 0.80, 0.97)}[roi]
    for f in sys.argv[2:]:
        print(f'{os.path.basename(f):40s} NCC {ncc(roi, f, box):+.3f}')
