"""Per-row silhouette contours (metres) from plate target masks vs renders (python3 + numpy via Blender python3.13 or system python3 with numpy if available).
python3.13(blender) contours.py <renderdir> [zlo zhi step]
Prints for each view: z, plate edge(s), now edge(s), diff in mm.  Profile views: rear/front y; front/back views: half-widths x."""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work')
M = R / 'male-silhouette'
CAM = {c['name']: c for c in json.load(open(M / 'reference-cameras.json'))['views']}
def mask(p):
    a = np.array(Image.open(p).convert('RGBA'))
    return (a[:, :, 3] > 127) if a[:, :, 3].min() < 250 else (a[:, :, 0] > 127)
def row_of_z(view, z):
    c = CAM[view]; return c['sole_y'] - z / c['metres_per_pixel']
def edges(m, view, z, x_lo=None, x_hi=None):
    """left/right extreme foreground columns on the row at height z, in metres relative to centre_x (image-right positive)"""
    c = CAM[view]; r = int(round(row_of_z(view, z)))
    xs = np.where(m[r])[0]
    if x_lo is not None: xs = xs[(xs >= c['roi'][0]) & (xs <= c['roi'][2])]
    if len(xs) == 0: return None
    return ((xs[0] - c['centre_x']) * c['metres_per_pixel'], (xs[-1] - c['centre_x']) * c['metres_per_pixel'])
def contour(m, view, zs):
    c = CAM[view]; out = []
    roi = c['roi']
    for z in zs:
        r = int(round(row_of_z(view, z))); xs = np.where(m[r, roi[0]:roi[2] + 1])[0] + roi[0]
        if len(xs) == 0: out.append((np.nan, np.nan)); continue
        out.append(((xs[0] - c['centre_x']) * c['metres_per_pixel'], (xs[-1] - c['centre_x']) * c['metres_per_pixel']))
    return np.array(out)
if __name__ == '__main__':
    d = Path(sys.argv[1]); zlo, zhi, st = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.70, 1.56, 0.02)
    zs = np.arange(zlo, zhi + 1e-9, st)
    for v in ('bald_front', 'bald_back', 'left', 'right'):
        t = contour(mask(M / f'{v}_target.png'), v, zs); n = contour(mask(d / f'{v}.png'), v, zs)
        print(f'== {v}  (cols: z | plate L R | now L R | diff L R mm)')
        for i, z in enumerate(zs):
            dl, dr = (n[i] - t[i]) * 1000
            print(f'{z:5.2f} | {t[i,0]*1000:7.1f} {t[i,1]*1000:7.1f} | {n[i,0]*1000:7.1f} {n[i,1]*1000:7.1f} | {dl:6.1f} {dr:6.1f}')
