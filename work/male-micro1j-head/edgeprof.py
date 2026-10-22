"""Luminance profile across the plate-measured jaw border (profile plates): mean L vs signed offset s (mm, + cheek side) for PLATE and renders.
python3.13 edgeprof.py <tag1> [tag2 ...]   (renders r/ul_<tag>/plate_left.png must exist; 'start' -> r/ul_start)"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head')
from j_lib import *
from j_jaw import POLY
tags = sys.argv[1:]
def lum(im): return np.asarray(im.convert('L')).astype(float)
panel = 'left'; box = BOXES[panel]
imgs = {'PLATE': (lum(PLATE.crop(box)), 1.0)}
for t in tags:
    imgs[t] = (lum(Image.open(W / f'r/ul_{t}/plate_{panel}.png')), 2.0)
seg = POLY[1:] - POLY[:-1]; slen = np.linalg.norm(seg, axis=1); cum = np.concatenate([[0], np.cumsum(slen)]); L = cum[-1]
offs = np.arange(-16, 17, 2.0)                     # mm
def sample(img, scale, y, z):
    col = (prof_col(y, panel) - box[0]) * scale; row = (rowz(z) - box[1]) * scale
    r0, c0 = int(np.floor(row)), int(np.floor(col))
    if r0 < 0 or c0 < 0 or r0 + 1 >= img.shape[0] or c0 + 1 >= img.shape[1]: return np.nan
    fr, fc = row - r0, col - c0
    return (img[r0, c0] * (1 - fr) * (1 - fc) + img[r0 + 1, c0] * fr * (1 - fc) + img[r0, c0 + 1] * (1 - fr) * fc + img[r0 + 1, c0 + 1] * fr * fc)
for lab, (t0, t1) in (('ramus+angle (t .62-.97)', (0.62, 0.97)), ('jaw body (t .30-.62)', (0.30, 0.62))):
    print('== ' + lab + '  mean luminance by offset s (mm; + = cheek side, - = behind/below the border)')
    print('  s     ' + ' '.join(f'{o:+4.0f}' for o in offs))
    for name, (img, sc) in imgs.items():
        row = []
        for o in offs:
            vals = []
            for tt in np.linspace(t0, t1, 14):
                d = tt * L; k = min(np.searchsorted(cum, d) - 1, len(seg) - 1); k = max(k, 0); u = (d - cum[k]) / slen[k]
                p = POLY[k] + seg[k] * u; n = np.array([-seg[k][1], seg[k][0]]) / slen[k]       # cheek-side normal in (y,z)
                q = p + n * (o / 1000.0); vals.append(sample(img, sc, q[0], q[1]))
            row.append(np.nanmean(vals))
        row = np.array(row); mean = np.nanmean(row)
        print(f'  {name:6s}' + ' '.join(f'{v - mean:+4.0f}' for v in row) + f'   | step(cheek -10..-3 vs below): {np.nanmean(row[(offs>=3)&(offs<=10)]) - np.nanmean(row[(offs<=-3)&(offs>=-10)]):+5.1f}')
