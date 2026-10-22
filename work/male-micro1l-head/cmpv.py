"""General plate-framed comparison: [PLATE | variants] for a view; plain (+ optional boosted) rows.
python3.13 cmpv.py <out.png> <view=front|left|right|q3L|q3R> <zlo> <zhi> [--boost=0|1] [--up=3] [--wide=1.0] <tag:dir> ...
dir holds plate_<view>.png from unity_like_j.py"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
from PIL import ImageFilter
out = sys.argv[1]; view = sys.argv[2]; zlo = float(sys.argv[3]); zhi = float(sys.argv[4])
opts = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[5:] if a.startswith('--')}
items = [a.split(':') for a in sys.argv[5:] if not a.startswith('--')]
RS = float(opts.get('--rs', 2)); up = float(opts.get('--up', 3)); boostrow = int(opts.get('--boost', 1)); wide = float(opts.get('--wide', 1.0))
box = BOXES[view]
if view in ('q3L', 'q3R'):
    r0 = int(397 + (TOP - zhi) / K); r1 = int(397 + (TOP - zlo) / K); c0, c1 = (60, 300) if view == 'q3L' else (470, 710)
    cm = 0.5 * (c0 + c1); hw = 0.5 * (c1 - c0) * wide; c0 = int(cm - hw); c1 = int(cm + hw)
elif view == 'front':
    r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(CX - 0.105 / K * wide); c1 = int(CX + 0.105 / K * wide)
else:
    y0 = float(opts.get('--y0', -0.15 * wide)); y1 = float(opts.get('--y1', 0.03))
    r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(prof_col(y0, view)); c1 = int(prof_col(y1, view))
def boost(im, k=4.0, sig=12):
    g = np.asarray(im.convert('L')).astype(float); b = np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(sig))).astype(float)
    return Image.fromarray(np.clip(128 + (g - b) * k, 0, 255).astype(np.uint8)).convert('RGB')
pl = PLATE.crop((c0, r0, c1, r1)); pl = pl.resize((int(pl.width * up), int(pl.height * up)), Image.LANCZOS); tiles = [('PLATE', pl)]
for tag, d_ in items:
    rn = Image.open(Path(d_) / f'plate_{view}.png').convert('RGB')
    tiles.append((tag, rn.crop((int((c0 - box[0]) * RS), int((r0 - box[1]) * RS), int((c1 - box[0]) * RS), int((r1 - box[1]) * RS))).resize(pl.size, Image.LANCZOS)))
rows = 2 if boostrow else 1
sheet = Image.new('RGB', (pl.width * len(tiles) + 6 * (len(tiles) - 1), pl.height * rows + 6 * (rows - 1)))
for i, (lab, t) in enumerate(tiles):
    ims = [t] + ([boost(t, 3.0 if i == 0 else 4.5)] if boostrow else [])
    for r, im in enumerate(ims):
        im = im.copy(); ImageDraw.Draw(im).text((6, 4), lab, fill=(255, 255, 0)); sheet.paste(im, (i * (pl.width + 6), r * (pl.height + 6)))
sheet.save(out); print(out, sheet.size)
