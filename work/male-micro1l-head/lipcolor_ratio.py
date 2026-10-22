"""Lip colour ratios (upper / lower lip vs cheek) in the plate and in plate-framed renders, sampled inside the traced lip regions.
python3.13 lipcolor_ratio.py <tag:dir> ...   (dir holds plate_front.png at 2x)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
C = json.load(open(W / 'r2_analysis/lip_curves_v0.json'))
cv = lambda k: (lambda p: (lambda x: np.interp(abs(x), p[:, 0], p[:, 1])))(np.array(C[k], float))
seam, up, lo = cv('seam'), cv('up'), cv('lo'); box = BOXES['front']
def sample(img, RS, f_lo, f_hi, x0, x1, plate=False):
    a = np.asarray(img).astype(float); vals = []
    for xm in np.arange(x0, x1, 0.5):
        for sgn in (1, -1):
            x = sgn * xm
            for zz in np.arange(f_lo(x), f_hi(x), 0.3):
                if plate: r = int(round(rowz(zz / 1000.0) - 0.5)); c = int(round(CX + x / 1000 / K))
                else: r = int(round((rowz(zz / 1000.0) - box[1]) * RS - 0.5)); c = int(round((CX + x / 1000 / K - box[0]) * RS))
                vals.append(a[r, c])
    return np.array(vals).mean(axis=0)
def box_mean(img, RS, xa, xb, za, zb, plate=False):
    a = np.asarray(img).astype(float)
    if plate: c0 = int(round(CX + xa / 1000 / K)); c1 = int(round(CX + xb / 1000 / K)); r0 = int(rowz(zb / 1000)); r1 = int(rowz(za / 1000))
    else: c0 = int(round((CX + xa / 1000 / K - box[0]) * RS)); c1 = int(round((CX + xb / 1000 / K - box[0]) * RS)); r0 = int((rowz(zb / 1000) - box[1]) * RS); r1 = int((rowz(za / 1000) - box[1]) * RS)
    return a[r0:r1, c0:c1].reshape(-1, 3).mean(axis=0)
ts = 1.9
def report(name, img, RS, plate):
    u = sample(img, RS, lambda x: seam(x) + ts + 0.5, lambda x: up(x) - 0.5, 0, 18, plate); l = sample(img, RS, lambda x: lo(x) + 0.5, lambda x: seam(x) - ts - 0.5, 0, 18, plate)
    ch = box_mean(img, RS, 30, 45, 1520, 1540, plate); sm = []
    a = np.asarray(img).astype(float)
    print(f'{name:12s} upper {np.round(u).astype(int)} lower {np.round(l).astype(int)} cheek {np.round(ch).astype(int)} | upper/cheek {np.round(u / ch, 2)} lower/cheek {np.round(l / ch, 2)} | lower/upper {np.round(l / u, 2)}')
report('PLATE', PLATE.convert('RGB'), 1, True)
for a in sys.argv[1:]:
    tag, d = a.split(':'); report(tag, Image.open(d + '/plate_front.png').convert('RGB'), 2, False)
