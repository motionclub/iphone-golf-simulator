"""Skin/lip/eye patch colours: reference sheet 07 front vs a Unity front render; CIEDE2000 + CIE76. python3 tools/patches.py <unity front.png>"""
import sys, json, numpy as np
from PIL import Image
SHEET = '../../ArtDir/style/alive/neutral-reference-pack-2026-10-15/sheets/07-head-skin-neutral.png'
# name: (ref box in sheet px, ours box in 1080 front render px)
P = {'forehead': ((262, 140, 298, 168), (515, 240, 565, 280)), 'cheek_L': ((213, 268, 238, 288), (380, 655, 410, 685)),
     'cheek_R': ((320, 268, 345, 288), (675, 655, 705, 685)), 'chin': ((270, 350, 290, 364), (525, 850, 555, 870)),
     'upper_lip': ((272, 311, 288, 316), (530, 768, 550, 776)), 'lower_lip': ((268, 325, 292, 331), (525, 792, 555, 802)),
     'neck': ((265, 400, 295, 420), (525, 965, 555, 995))}
EYE_WIN = ((200, 212, 258, 262), (330, 480, 520, 640))   # left eye windows: sheet / 1080 front render
def iris_disk(im, box):
    a = np.asarray(im.crop(box)).astype(float); L = (a / 255) @ [.2126, .7152, .0722]
    m = L < .33; ys, xs = np.nonzero(m); cy, cx = ys.mean(), xs.mean(); r = np.sqrt(m.sum() / np.pi)
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]; d = np.hypot(yy - cy, xx - cx) < r * .92
    return a[d & (L < .8)].mean(0), (box[0] + cx, box[1] + cy, r)
def lab(rgb):
    c = np.asarray(rgb, float) / 255; c = np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]); xyz = M @ c / np.array([.95047, 1, 1.08883])
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])
def de2000(a, b):
    L1, a1, b1 = a; L2, a2, b2 = b
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2); Cm = (C1 + C2) / 2; G = .5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2; C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1, h2 = np.degrees(np.arctan2(b1, a1p)) % 360, np.degrees(np.arctan2(b2, a2p)) % 360
    dL, dC = L2 - L1, C2p - C1p; dh = h2 - h1
    dh = dh - 360 if dh > 180 else dh + 360 if dh < -180 else dh
    dH = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2)); Lm = (L1 + L2) / 2; Cpm = (C1p + C2p) / 2
    hm = (h1 + h2) / 2 if abs(h1 - h2) <= 180 else (h1 + h2 + 360) / 2
    T = 1 - .17 * np.cos(np.radians(hm - 30)) + .24 * np.cos(np.radians(2 * hm)) + .32 * np.cos(np.radians(3 * hm + 6)) - .2 * np.cos(np.radians(4 * hm - 63))
    SL = 1 + .015 * (Lm - 50) ** 2 / np.sqrt(20 + (Lm - 50) ** 2); SC = 1 + .045 * Cpm; SH = 1 + .015 * Cpm * T
    RT = -2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7)) * np.sin(np.radians(60 * np.exp(-((hm - 275) / 25) ** 2)))
    return float(np.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH)))
def mean(im, b): return np.asarray(im.crop(b)).reshape(-1, 3).mean(0)
if __name__ == '__main__':
    ref = Image.open(SHEET).convert('RGB'); ours = Image.open(sys.argv[1]).convert('RGB')
    rows = {}
    items = [(k, mean(ref, rb), mean(ours, ob)) for k, (rb, ob) in P.items()]
    items.append(('iris_disk', iris_disk(ref, EYE_WIN[0])[0], iris_disk(ours, EYE_WIN[1])[0]))
    for k, r, o in items:
        lr, lo = lab(r), lab(o)
        rows[k] = dict(ref='#%02X%02X%02X' % tuple(r.astype(int)), ours='#%02X%02X%02X' % tuple(o.astype(int)), dE00=round(de2000(lr, lo), 1),
                       dL=round(lo[0] - lr[0], 1), da=round(lo[1] - lr[1], 1), db=round(lo[2] - lr[2], 1))
        print(f"{k:10s} ref {rows[k]['ref']} ours {rows[k]['ours']} dE00 {rows[k]['dE00']:5.1f}  dL {rows[k]['dL']:6.1f} da {rows[k]['da']:6.1f} db {rows[k]['db']:6.1f}")
    if len(sys.argv) > 2: json.dump(rows, open(sys.argv[2], 'w'), indent=1)
