"""lower-face silhouette IoU / XOR (mm^2) plate vs render, 5 views.  python3 lowiou.py name=render_dir tag ... (e.g. F1=renders/f1pl:F1 F2=renders/n11b:F2)"""
import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import fl
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
UP = 3
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PAN = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'right': (830, 55, 1195, 342), 'q3L': (85, 385, 430, 656), 'q3R': (440, 385, 800, 656)}
def skin_mask(a):
    R, G, B_ = a[..., 0], a[..., 1], a[..., 2]
    return (R - B_ > 18) & (R > G + 4) & (G > B_) & (R > 110)
def rows(v, box):
    if v in ('front', 'left', 'right'): return float(fl.rowz(1.500)) - box[1], float(fl.rowz(1.4255 - 0.004)) - box[1] + 8
    if v == 'q3L': return 515 - box[1], 563 + 6 - box[1]
    return 515 - box[1], 562 + 6 - box[1]
items = [a.split('=', 1) for a in sys.argv[1:]]
print('view   ' + '   '.join(f'{n:>22s}' for n, _ in items))
res = {n: {} for n, _ in items}
for v in ('front', 'left', 'right', 'q3L', 'q3R'):
    box = PAN[v]; pl = src.crop(box); w, h = pl.size; big = (w * UP, h * UP)
    pm = skin_mask(np.asarray(pl.resize(big, Image.LANCZOS)).astype(float))
    r0, r1 = rows(v, box); R0, R1 = int(r0 * UP), int(r1 * UP)
    out = []
    for n, spec in items:
        d, t = spec.split(':')
        r = Image.open(f'{d}/{t}_{v}.png').convert('RGBA').resize(big, Image.LANCZOS)
        rm = np.asarray(r)[..., 3] > 127
        a, b = rm[R0:R1], pm[R0:R1]
        iou = (a & b).sum() / max((a | b).sum(), 1); xor = (a ^ b).sum() * (fl.K / UP * 1000) ** 2
        out.append((iou, xor)); res[n][v] = (float(iou), float(xor))
    print(f'{v:6s} ' + '   '.join(f'IoU {i:.3f} xor {x:7.0f}mm2' for i, x in out))
json.dump(res, open(ROOT + 'work/female-micro-f2-head/data/lowiou_last.json', 'w'), indent=1)
