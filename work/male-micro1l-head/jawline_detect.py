"""Visible jaw-line detection in the FRONT view: per image column, the strongest light->dark luminance step (going down) in z 1.438..1.505, plus its contrast.
python3.13 jawline_detect.py <tag:dir> ...   -> prints z_edge(x) (mm) and edge contrast (luminance drop across +-8 mm, 0..255) for the plate and renders"""
import sys, json; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
from PIL import ImageFilter
items = [a.split(':') for a in sys.argv[1:]]
box = BOXES['front']
def lum(im): return np.asarray(im.convert('L')).astype(float)
def zhi_of(xm):
    """search window top (m): below the lips at the lateral columns (the lower lip border is a light->dark step too), up to 1.505 at |x| >= 60"""
    return float(np.interp(abs(xm), [0, 30, 60], [1.480, 1.480, 1.505]))


def edge(L, up, xs_mm, zlo=1.438, zhi=None, sig=2.0, flank=8.0):
    ez, con = [], []
    for xm in xs_mm:
        zh = zhi if zhi is not None else zhi_of(xm)
        c = int(round((CX + xm / 1000.0 / K - box[0]) * up))
        col = L[:, max(c - up, 0):c + up].mean(axis=1)
        r0 = int(round((rowz(zh) - box[1]) * up)); r1 = int(round((rowz(zlo) - box[1]) * up))
        seg = col[r0:r1]
        k = np.exp(-0.5 * (np.arange(-8, 9) / (sig * up / 2)) ** 2); k /= k.sum()
        sm = np.convolve(np.pad(seg, 8, mode='edge'), k, mode='valid'); g = np.gradient(sm); i = int(np.argmin(g))
        fl = int(round(flank / 1000.0 / K * up)); a = sm[max(i - fl, 0):max(i - 2, 1)].mean(); b = sm[min(i + 2, len(sm) - 1):min(i + fl, len(sm))].mean()
        ez.append(zrow((r0 + i) / up + box[1])); con.append(a - b)
    return np.array(ez), np.array(con)
xs = np.arange(-70, 71, 10)
rows = {}
pl = PLATE.crop(box); rows['PLATE'] = edge(lum(pl.filter(ImageFilter.GaussianBlur(1.0))), 1, xs)
for tag, d_ in items:
    im = Image.open(Path(d_) / 'plate_front.png').convert('RGB').filter(ImageFilter.GaussianBlur(1.5)); rows[tag] = edge(lum(im), 2, xs)
print('x(mm):   ' + ' '.join(f'{x:6d}' for x in xs))
for k, (z, c) in rows.items(): print(f'{k:8s} z ' + ' '.join(f'{v * 1000:6.1f}' for v in z))
for k, (z, c) in rows.items(): print(f'{k:8s} c ' + ' '.join(f'{v:6.1f}' for v in c))

if __import__('os').environ.get('JL_JSON'):
    json.dump({'x_mm': [int(v) for v in xs], 'rows': {k: {'jaw_line_z_mm': [round(float(v) * 1000, 1) for v in z], 'edge_contrast_lum': [round(float(v), 1) for v in c]} for k, (z, c) in rows.items()}}, open(__import__('os').environ['JL_JSON'], 'w'), indent=1)
