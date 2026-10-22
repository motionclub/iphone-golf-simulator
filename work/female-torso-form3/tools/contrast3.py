"""relief-contrast energy: std of the band-pass (DoG) luminance inside a model-space box, plate vs renders (same matcap frame as the plate crop).
python3 tools/contrast3.py chest|pelvis  tag=coords.npy ..."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from rr import *
from ncc3 import roi_pix
import viz3

BOX = {'chest': (-0.115, 0.115, 1.14, 1.30), 'pelvis': (-0.14, 0.14, 0.80, 0.97)}
def energy(img, roi, s1=2.5, s2=14.0):
    sc = ROIS[roi]['scale']
    b = np.asarray(viz3.bandpass(img, sc, s1, s2, 1.0).convert('L'), float) - 128.0
    x0, y0, x1, y1 = roi_pix(roi, *BOX[roi])
    sub = b[y0:y1, x0:x1]
    return float(sub.std()), sub
def run(roi, items, look='matcap:soft'):
    out = {}
    pl = plate_crop(roi, 1.0)
    out['PLATE'] = energy(pl, roi)[0]
    for t, c in items:
        p = render([roi], c if c.startswith('/') else HERE + '/' + c, 'ct_' + t, look)[0]
        out[t] = energy(bgcomp(p), roi)[0]
    return out
if __name__ == '__main__':
    roi = sys.argv[1]; items = [a.split('=', 1) for a in sys.argv[2:]]
    r = run(roi, items)
    base = r['PLATE']
    for k, v in r.items():
        print(f'{k:12s} bandpass std {v:6.3f}   ratio to plate {v/base:5.2f}')
