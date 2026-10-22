"""ring5.py: closed-ring / bullseye detector on the SOFT render (same pixel grid as the plate crop).
For each mound (centre xc, zc) and radius r: luminance L(theta) around the circle vs the centre value L0; closed rim = darker than L0 - thr for most of the circle (angular fraction f_dark).
An open under-bust crescent darkens only the lower part (f_dark <= ~0.5, upper half bright).  returns dict r -> (f_dark, f_dark_upper_half, f_dark_lower_half)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image
from viz3 import plate_crop, ROIS, S, FC, SOLE
box = ROIS['chest']['box']; sc = ROIS['chest']['scale']

def lum(img, x, z, hw=2):
    col = (FC + x / S - box[0]) * sc; row = (SOLE - z / S - box[1]) * sc
    a = np.asarray(img.convert('L'), dtype=float)
    r0, c0 = int(round(row)), int(round(col))
    return a[r0 - hw:r0 + hw + 1, c0 - hw:c0 + hw + 1].mean()

def bgcomp(p):
    m = Image.open(p).convert('RGBA'); bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m); return bg.convert('RGB')

def ring_stats(img, centres=((0.07, 1.225), (-0.07, 1.225)), radii=(0.035, 0.045, 0.055, 0.065), thr=6.0, n=72):
    out = {}
    for r in radii:
        fd = []; fu = []; fl = []
        for xc, zc in centres:
            L0 = np.mean([lum(img, xc + 0.012 * np.cos(t), zc + 0.012 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)])
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            L = np.array([lum(img, xc + r * np.cos(t), zc + r * np.sin(t)) for t in th])
            dark = L < L0 - thr
            up = (th > np.radians(15)) & (th < np.radians(165)); lo = (th > np.radians(195)) & (th < np.radians(345))
            fd.append(dark.mean()); fu.append(dark[up].mean()); fl.append(dark[lo].mean())
        out[r] = (float(np.mean(fd)), float(np.mean(fu)), float(np.mean(fl)))
    return out

if __name__ == '__main__':
    H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ims = {'plate': plate_crop('chest', 1.0)}
    for t in sys.argv[1:]:
        ims[t] = bgcomp(f'{H}/scratch/r/bd_chest_{t}_soft_front.png')
    for k, im in ims.items():
        st = ring_stats(im)
        print(f'{k:10s}', ' | '.join(f'r={r*100:.1f}cm: all {a:.2f} up {b:.2f} lo {c:.2f}' for r, (a, b, c) in st.items()))
