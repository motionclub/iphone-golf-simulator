"""Coronal (x-z) sections of the crotch gap at several y planes.  python3 gapplot.py out.png tag[,tag2] y1,y2,...   (env BOX x0,x1,z0,z1)"""
import sys, os, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
import common
from common import F
out = sys.argv[1]; tags = sys.argv[2].split(','); ys = [float(v) for v in sys.argv[3].split(',')]
x0, x1, z0, z1 = [float(v) for v in os.environ.get('BOX', '-0.09,0.09,0.70,0.84').split(',')]; S = float(os.environ.get('SC', 5000))
def load(t): return common.V0 if t == 'start' else np.load(f'data/V_{t}.npy')
def sect_y(V, y):
    segs = []
    for f in F:
        yy = V[list(f), 1]
        if yy.min() > y or yy.max() < y: continue
        pts = []
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]; ya, yb = V[a, 1], V[b, 1]
            if (ya - y) * (yb - y) < 0:
                t = (y - ya) / (yb - ya); p = V[a] + t * (V[b] - V[a]); pts.append((p[0], p[2]))
        if len(pts) == 2: segs.append(pts)
    return segs
Wd = int((x1 - x0) * S) + 100; Hd = int((z1 - z0) * S) + 60; n = len(ys)
im = Image.new('RGB', (Wd, Hd), (22, 22, 26)); d = ImageDraw.Draw(im); Ft = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttf' if os.path.exists('/System/Library/Fonts/Helvetica.ttf') else '/System/Library/Fonts/Helvetica.ttc', 13)
X = lambda x: 50 + (x - x0) * S; Y = lambda z: 30 + (z1 - z) * S
for z in np.arange(np.ceil(z0 * 100) / 100, z1 + 1e-9, 0.01): d.line([(45, Y(z)), (Wd - 10, Y(z))], fill=(50, 50, 70)); d.text((2, Y(z) - 7), f'{z:.2f}', fill=(130, 130, 170), font=Ft)
for x in np.arange(np.ceil(x0 * 50) / 50, x1 + 1e-9, 0.02): d.line([(X(x), 26), (X(x), Hd - 20)], fill=(44, 44, 62)); d.text((X(x) - 10, Hd - 18), f'{x*1000:.0f}', fill=(130, 130, 170), font=Ft)
PAL = [(110, 190, 255), (110, 255, 150), (255, 120, 120), (230, 120, 255), (255, 255, 120), (120, 255, 255), (255, 170, 80), (200, 200, 200)]
for ti, t in enumerate(tags):
    V = load(t)
    for yi, y in enumerate(ys):
        col = PAL[yi % len(PAL)] if len(tags) == 1 else PAL[ti % len(PAL)]
        for (p, q) in sect_y(V, y):
            if max(p[1], q[1]) < z0 or min(p[1], q[1]) > z1: continue
            d.line([(X(p[0]), Y(p[1])), (X(q[0]), Y(q[1]))], fill=col, width=2 if ti == 0 else 1)
        if ti == 0: d.text((Wd - 80, 30 + 16 * yi), f'y={y*1000:.0f}', fill=col, font=Ft)
if len(tags) > 1:
    for ti, t in enumerate(tags): d.text((Wd - 160, 30 + 16 * len(ys) + 16 * ti), t, fill=PAL[ti % len(PAL)], font=Ft)
im.save(out); print(out, im.size)
