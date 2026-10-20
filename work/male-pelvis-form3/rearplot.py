"""Rear-most surface depth y(z) at several x offsets (|x|) for 1+ candidates vs the plate's extreme side contour.
python3 rearplot.py out.png zlo zhi ylo yhi tag...   env XS comma list (m)"""
import sys, os, json, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
import common
from common import rear_curve
out, zlo, zhi, ylo, yhi = sys.argv[1], *map(float, sys.argv[2:6]); tags = sys.argv[6:]
XS = [float(v) for v in os.environ.get('XS', '0.0,0.02,0.04,0.06,0.08,0.10,0.12,0.15').split(',')]
S = float(os.environ.get('SC', 4600))
def load(t): return common.V0 if t == 'start' else np.load(f'data/V_{t}.npy')
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
Fs = font(14)
W_ = int((yhi - ylo) * S) + 160; H_ = int((zhi - zlo) * S) + 60
im = Image.new('RGB', (W_, H_), (22, 22, 26)); d = ImageDraw.Draw(im)
X = lambda y: 60 + (y - ylo) * S; Y = lambda z: 30 + (zhi - z) * S
for z in np.arange(np.ceil(zlo * 50) / 50, zhi + 1e-9, 0.02):
    d.line([(55, Y(z)), (W_ - 100, Y(z))], fill=(50, 50, 70)); d.text((4, Y(z) - 8), f'{z:.2f}', fill=(130, 130, 170), font=Fs)
for y in np.arange(np.ceil(ylo * 100) / 100, yhi, 0.01):
    d.line([(X(y), 26), (X(y), H_ - 20)], fill=(44, 44, 62)); d.text((X(y) - 12, H_ - 18), f'{y*1000:.0f}', fill=(130, 130, 170), font=Fs)
pl = json.load(open('data/plate_rear_subpx.json')); zs = np.array(pl['z'])
for side, col in (('left', (255, 205, 70)), ('right', (255, 130, 40))):
    pts = [(X(v), Y(z)) for z, v in zip(zs, pl[side]) if v is not None and zlo <= z <= zhi]
    if len(pts) > 1: d.line(pts, fill=col, width=4)
d.text((W_ - 150, 10), 'plate L/R side', fill=(255, 205, 70), font=Fs)
PAL = [(110, 190, 255), (110, 255, 150), (255, 120, 120), (230, 120, 255), (120, 255, 255), (255, 255, 120), (200, 200, 200), (255, 170, 80)]
zz = np.arange(zlo, zhi + 1e-9, 0.002)
for ti, t in enumerate(tags):
    V = load(t)
    for xi, x in enumerate(XS):
        a = rear_curve(V, x + 1e-6, zz); b = rear_curve(V, -x - 1e-6, zz); c = np.nanmean(np.stack([a, b]), axis=0)
        col = PAL[xi % len(PAL)]; w = 2 if ti == 0 else 1
        pts = [(X(v), Y(z)) for z, v in zip(zz, c) if np.isfinite(v)]
        # split at jumps
        seg = []
        for p in pts:
            if seg and abs(p[1] - seg[-1][1]) > 6 * (S * 0.002): d.line(seg, fill=col, width=w); seg = []
            seg.append(p)
        if len(seg) > 1: d.line(seg, fill=col, width=w)
        if ti == 0: d.text((W_ - 90, 30 + 18 * xi), f'x={x*1000:.0f}', fill=col, font=Fs)
    if len(tags) > 1: d.text((W_ - 150, 190 + 18 * ti), ('solid' if ti == 0 else 'thin') + ' ' + t, fill=(220, 220, 220), font=Fs)
im.save(out); print(out, im.size)
