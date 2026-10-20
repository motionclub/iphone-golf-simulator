"""Jaw definition check: [plate | start | variant] at the plate framing, plain + local-contrast-boosted rows.
python3.13 jawcmp.py <out.png> <variant_tag> [view=left|right|q3L|q3R]    (needs r/ul_start/plate_<view>.png and r/ul_<tag>/plate_<view>.png)"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from j_lib import *
from PIL import ImageFilter
out = sys.argv[1]; tag = sys.argv[2]; view = sys.argv[3] if len(sys.argv) > 3 else 'left'
zlo, zhi = 1.43, 1.565
box = BOXES[view]
if view in ('q3L', 'q3R'): r0 = int(397 + (TOP - zhi) / K); r1 = int(397 + (TOP - zlo) / K)
else: r0 = int(rowz(zhi)); r1 = int(rowz(zlo))
if view in ('left', 'right'):
    c0 = int(prof_col(-0.15, view)); c1 = int(prof_col(0.02, view))
else:
    c0, c1 = (60, 300) if view == 'q3L' else ((470, 710) if view == 'q3R' else (box[0], box[2]))
up = 3.0
def boost(im, k=4.0, sig=12):
    g = np.asarray(im.convert('L')).astype(float); b = np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(sig))).astype(float)
    return Image.fromarray(np.clip(128 + (g - b) * k, 0, 255).astype(np.uint8)).convert('RGB')
tiles = []
pl = PLATE.crop((c0, r0, c1, r1)); pl = pl.resize((int(pl.width * up), int(pl.height * up)), Image.LANCZOS); tiles.append(pl)
for d_ in ('r/ul_start', f'r/ul_{tag}'):
    rn = Image.open(W / d_ / f'plate_{view}.png').convert('RGB')
    cr = rn.crop(((c0 - box[0]) * 2, (r0 - box[1]) * 2, (c1 - box[0]) * 2, (r1 - box[1]) * 2)).resize(pl.size, Image.LANCZOS); tiles.append(cr)
rows = [tiles, [boost(t, 3.2 if i == 0 else 4.5) for i, t in enumerate(tiles)]]
sheet = Image.new('RGB', (pl.width * 3 + 12, pl.height * 2 + 6))
for r, row in enumerate(rows):
    for i, t in enumerate(row):
        ImageDraw.Draw(t).text((6, 4), ['PLATE', 'START', tag][i], fill=(255, 255, 0)); sheet.paste(t, (i * (pl.width + 6), r * (pl.height + 6)))
sheet.save(out); print(out, sheet.size)
