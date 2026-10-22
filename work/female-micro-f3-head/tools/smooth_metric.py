"""interior shading smoothness of the lower face: RMS of the high-pass luminance (gaussian sigma 6 px at 3x) inside the lower-face skin region (eroded 14 px from the outline),
plate vs renders.  Lower = smoother.   python3 smooth_metric.py name=dir:tag ..."""
import sys, json
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import fl
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
UP = 3
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PAN = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'right': (830, 55, 1195, 342), 'q3L': (85, 385, 430, 656), 'q3R': (440, 385, 800, 656)}
# lower-face window: from just below the mouth (lip bottom) to just above the collar, central columns
def win(v, box):
    if v in ('front', 'left', 'right'): return float(fl.rowz(1.452)) - box[1], float(fl.rowz(1.4255 - 0.003)) - box[1]
    return (535 - box[1], 560 - box[1]) if v == 'q3R' else (535 - box[1], 560 - box[1])
def erode(m, k):
    o = m.copy()
    for _ in range(k):
        p = o.copy(); p[1:] &= o[:-1]; p[:-1] &= o[1:]; p[:, 1:] &= o[:, :-1]; p[:, :-1] &= o[:, 1:]; o = p
    return o
def skin_mask(a):
    R, G, B_ = a[..., 0], a[..., 1], a[..., 2]
    return (R - B_ > 18) & (R > G + 4) & (G > B_) & (R > 110)
S1, S2 = 5.0, 14.0           # band-pass (at 3x): features ~2-5 plate px wide (3-8 mm): crease / ridge scale
def hp_energy(img_rgb, mask):
    L = Image.fromarray(img_rgb).convert('L'); a = np.asarray(L.filter(ImageFilter.GaussianBlur(S1))).astype(float); b = np.asarray(L.filter(ImageFilter.GaussianBlur(S2))).astype(float)
    d = (a - b)[mask]
    # normalise by the local mean level so that exposure differences (plate vs render) do not matter
    lv = float(np.asarray(L).astype(float)[mask].mean()) if mask.sum() > 50 else 1.0
    return float(np.sqrt((d ** 2).mean()) / lv * 100.0) if mask.sum() > 50 else float('nan')
items = [a.split('=', 1) for a in sys.argv[1:]]
print('view   plate   ' + '   '.join(f'{n:>8s}' for n, _ in items))
res = {}
for v in ('front', 'q3L', 'q3R', 'left'):
    box = PAN[v]; pl = src.crop(box); w, h = pl.size; big = (w * UP, h * UP)
    pa = np.asarray(pl.resize(big, Image.LANCZOS)).astype(np.uint8)
    r0, r1 = win(v, box); R0, R1 = int(r0 * UP), int(r1 * UP)
    pm = skin_mask(pa.astype(float)); pm = erode(pm, 24)
    wm = np.zeros_like(pm); wm[R0:R1] = True
    out = [hp_energy(pa, pm & wm)]
    for n, spec in items:
        d, t = spec.split(':')
        r = Image.open(f'{d}/{t}_{v}.png').convert('RGBA').resize(big, Image.LANCZOS)
        al = np.asarray(r)[..., 3] > 127; rgb = np.asarray(r.convert('RGB'))
        m = None
        # evaluate on the same pixels as the plate region intersected with the render skin
        mm = erode(al, 24) & wm
        out.append(hp_energy(rgb, mm & pm))
    res[v] = out
    print(f'{v:6s} {out[0]:6.2f}  ' + '   '.join(f'{x:8.2f}' for x in out[1:]))
