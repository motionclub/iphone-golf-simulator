"""Mid-frequency relief map: signed normal distance of the surface to a Taubin-smoothed copy (mm), splatted in back/front view coordinates.
python3 reliefmap.py out.png view(back|front) tag iters [range_mm]"""
import sys, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
import common
from sculpt import taubin
out, view, tag, iters = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]); rng = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
V = common.V0 if tag == 'start' else np.load(f'data/V_{tag}.npy')
N = common.vnormals(V); w = np.ones(len(V))
Vs = taubin(V, w, iters=iters, lam=0.5, mu=-0.53)
rel = ((V - Vs) * N).sum(1) * 1000        # >0 : bump (convex relative to smoothed), <0 : groove
sgn = 1 if view == 'back' else -1
sel = (sgn * N[:, 1] > 0.2) & (np.abs(V[:, 0]) < 0.24) & (V[:, 2] > 0.70) & (V[:, 2] < 1.12)
S = 3600; x0, x1, z0, z1 = -0.24, 0.24, 0.70, 1.12
Wd, Hd = int((x1 - x0) * S), int((z1 - z0) * S); img = np.zeros((Hd, Wd, 3), np.float32); wt = np.zeros((Hd, Wd), np.float32)
px = ((-V[:, 0] * sgn if view == 'back' else V[:, 0]) - x0) * S; py = (z1 - V[:, 2]) * S
for i in np.where(sel)[0]:
    cx, cy = int(px[i]), int(py[i]); r = 7
    ys, xs = np.ogrid[-r:r + 1, -r:r + 1]; k = np.exp(-(xs ** 2 + ys ** 2) / (2 * 3.5 ** 2))
    ya, yb, xa, xb = max(cy - r, 0), min(cy + r + 1, Hd), max(cx - r, 0), min(cx + r + 1, Wd)
    if ya >= yb or xa >= xb: continue
    kk = k[ya - (cy - r):yb - (cy - r), xa - (cx - r):xb - (cx - r)]
    img[ya:yb, xa:xb, 0] += kk * rel[i]; wt[ya:yb, xa:xb] += kk
val = np.where(wt > 0.05, img[..., 0] / np.maximum(wt, 1e-6), np.nan)
t = np.clip(val / rng, -1, 1); rgb = np.zeros((Hd, Wd, 3), np.uint8) + 25
pos = np.nan_to_num(np.clip(t, 0, 1)); neg = np.nan_to_num(np.clip(-t, 0, 1)); has = np.isfinite(val)
rgb[..., 0] = np.where(has, 128 + 127 * pos - 100 * neg, 25); rgb[..., 1] = np.where(has, 128 - 90 * pos - 90 * neg, 25); rgb[..., 2] = np.where(has, 128 - 100 * pos + 127 * neg, 25)
im = Image.fromarray(rgb.astype(np.uint8)); d = ImageDraw.Draw(im)
try: F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
except Exception: F = ImageFont.load_default()
for z in np.arange(0.70, 1.121, 0.02):
    yy = int((z1 - z) * S); d.line([(0, yy), (Wd, yy)], fill=(70, 70, 70) if round(z * 100) % 10 else (140, 140, 140)); d.text((4, yy - 14), f'{z:.2f}', fill=(255, 255, 255), font=F)
for x in np.arange(-0.2, 0.2001, 0.05):
    xx = int((x - x0) * S); d.line([(xx, 0), (xx, Hd)], fill=(90, 90, 90)); d.text((xx + 3, Hd - 18), f'{x*1000:.0f}', fill=(255, 255, 255), font=F)
im.save(out); print(out, im.size, 'range +-', rng, 'mm')
