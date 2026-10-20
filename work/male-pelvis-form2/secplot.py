"""Sagittal-section plot of Body_M candidates vs the plate's sub-pixel rear contour.
python3 secplot.py out.png zlo zhi ylo yhi  tag[:colorname] ...   (tag = 'start' or data/V_<tag>.npy); x offsets from env XS (comma list, metres)"""
import sys, os, json, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
import common
from common import F, section_x
out, zlo, zhi, ylo, yhi = sys.argv[1], *map(float, sys.argv[2:6])
tags = sys.argv[6:]
XS = [float(v) for v in os.environ.get('XS', '0.0,0.03,0.06,0.09,0.12,0.15').split(',')]
S = float(os.environ.get('SC', 3800))
def load(t):
    return common.V0 if t == 'start' else np.load(f'data/V_{t}.npy')
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
Fs = font(14)
W_ = int((yhi - ylo) * S) + 100; H_ = int((zhi - zlo) * S) + 60
im = Image.new('RGB', (W_, H_), (22, 22, 26)); d = ImageDraw.Draw(im)
X = lambda y: 60 + (y - ylo) * S
Y = lambda z: 30 + (zhi - z) * S
for z in np.arange(np.ceil(zlo * 50) / 50, zhi + 1e-9, 0.02):
    d.line([(55, Y(z)), (W_ - 10, Y(z))], fill=(50, 50, 70)); d.text((4, Y(z) - 8), f'{z:.2f}', fill=(130, 130, 170), font=Fs)
for y in np.arange(np.ceil(ylo * 50) / 50, yhi, 0.02):
    d.line([(X(y), 26), (X(y), H_ - 20)], fill=(44, 44, 62)); d.text((X(y) - 12, H_ - 18), f'{y*1000:.0f}', fill=(130, 130, 170), font=Fs)
pl = json.load(open('data/plate_rear_subpx.json')); zs = np.array(pl['z'])
for side, col in (('left', (255, 205, 70)), ('right', (255, 130, 40))):
    pts = [(X(v), Y(z)) for z, v in zip(zs, pl[side]) if v is not None and zlo <= z <= zhi]
    if len(pts) > 1: d.line(pts, fill=col, width=3)
PAL = [(110, 190, 255), (110, 255, 150), (255, 120, 120), (230, 120, 255), (120, 255, 255), (255, 255, 120), (200, 200, 200), (255, 170, 80)]
for ti, t in enumerate(tags):
    V = load(t.split(':')[0])
    for xi, x in enumerate(XS):
        S_ = section_x(V, x + 1e-6) if x >= 0 else section_x(V, x - 1e-6)
        col = PAL[xi % len(PAL)] if len(tags) == 1 else PAL[ti % len(PAL)]
        for (p, q) in S_:
            if max(p[1], q[1]) < zlo or min(p[1], q[1]) > zhi: continue
            d.line([(X(p[0]), Y(p[1])), (X(q[0]), Y(q[1]))], fill=col, width=1)
        if len(tags) == 1: d.text((W_ - 90, 30 + 18 * xi), f'x={x*1000:.0f}', fill=col, font=Fs)
if len(tags) > 1:
    for ti, t in enumerate(tags): d.text((W_ - 140, 30 + 18 * ti), t, fill=PAL[ti % len(PAL)], font=Fs)
im.save(out); print(out, im.size)
