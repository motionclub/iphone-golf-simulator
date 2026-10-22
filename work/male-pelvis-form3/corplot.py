"""Coronal rear-surface y(x) at several heights z for candidate tags.  python3 corplot.py out.png tag[,tag2] z1,z2,...   (env XR=0.2 half range, YLO, YHI mm)"""
import sys, os, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
import common
from common import section_segments
out = sys.argv[1]; tags = sys.argv[2].split(','); zl = [float(v) for v in sys.argv[3].split(',')]
XR = float(os.environ.get('XR', 0.2)); YLO = float(os.environ.get('YLO', 0.0)); YHI = float(os.environ.get('YHI', 0.115)); S = float(os.environ.get('SC', 5000))
def load(t): return common.V0 if t == 'start' else np.load(f'data/V_{t}.npy')
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
Fs = font(14)
Wd = int(2 * XR * S) + 120; Hd = int((YHI - YLO) * S) + 80
im = Image.new('RGB', (Wd, Hd), (22, 22, 26)); d = ImageDraw.Draw(im)
X = lambda x: 60 + (x + XR) * S; Y = lambda y: 40 + (YHI - y) * S
for x in np.arange(-XR, XR + 1e-9, 0.05):
    d.line([(X(x), 30), (X(x), Hd - 30)], fill=(50, 50, 70)); d.text((X(x) - 14, Hd - 26), f'{x*1000:.0f}', fill=(130, 130, 170), font=Fs)
for y in np.arange(0, YHI + 1e-9, 0.02):
    d.line([(55, Y(y)), (Wd - 20, Y(y))], fill=(50, 50, 70)); d.text((4, Y(y) - 8), f'{y*1000:.0f}', fill=(130, 130, 170), font=Fs)
PAL = [(110, 190, 255), (110, 255, 150), (255, 120, 120), (230, 120, 255), (120, 255, 255), (255, 255, 120), (255, 170, 80), (200, 200, 200)]
xs = np.arange(-XR, XR + 1e-9, 0.002)
for ti, t in enumerate(tags):
    V = load(t)
    for zi, z in enumerate(zl):
        S_ = section_segments(V, z); ys = np.full(len(xs), np.nan)
        for (p, q) in S_:
            lo, hi = sorted([p[0], q[0]])
            if hi - lo < 1e-9: continue
            m = (xs >= lo) & (xs <= hi); t_ = (xs[m] - p[0]) / (q[0] - p[0]); yy = p[1] + t_ * (q[1] - p[1]); ys[m] = np.fmax(ys[m], yy)
        col = PAL[zi % len(PAL)]; w = 2 if ti == 0 else 1
        pts = [(X(x), Y(y)) for x, y in zip(xs, ys) if np.isfinite(y)]
        if len(pts) > 1: d.line(pts, fill=col, width=w)
        if ti == 0: d.text((Wd - 100, 40 + 18 * zi), f'z={z:.2f}', fill=col, font=Fs)
im.save(out); print(out, im.size)
