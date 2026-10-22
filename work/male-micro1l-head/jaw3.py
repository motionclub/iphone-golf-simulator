"""Jaw close-up: [PLATE | MICRO1J | variant] at the plate framing; plain + boosted rows.  python3.13 jaw3.py <out.png> <view=left|q3L|q3R> <tagA:dirA> <tagB:dirB> ..."""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
from PIL import ImageFilter
out = sys.argv[1]; view = sys.argv[2]; items = [a.split(':') for a in sys.argv[3:]]
zlo, zhi = 1.42, 1.56; box = BOXES[view]
if view in ('q3L', 'q3R'): r0 = int(397 + (TOP - zhi) / K); r1 = int(397 + (TOP - zlo) / K); c0, c1 = (60, 300) if view == 'q3L' else (470, 710)
else: r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(prof_col(-0.15, view)); c1 = int(prof_col(0.03, view))
up = 3.0
def boost(im, k=4.0, sig=12):
    g = np.asarray(im.convert('L')).astype(float); b = np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(sig))).astype(float)
    return Image.fromarray(np.clip(128 + (g - b) * k, 0, 255).astype(np.uint8)).convert('RGB')
pl = PLATE.crop((c0, r0, c1, r1)); pl = pl.resize((int(pl.width * up), int(pl.height * up)), Image.LANCZOS); tiles = [('PLATE', pl)]
for tag, d_ in items:
    rn = Image.open(Path(d_) / f'plate_{view}.png').convert('RGB')
    tiles.append((tag, rn.crop(((c0 - box[0]) * 2, (r0 - box[1]) * 2, (c1 - box[0]) * 2, (r1 - box[1]) * 2)).resize(pl.size, Image.LANCZOS)))
sheet = Image.new('RGB', (pl.width * len(tiles) + 6 * (len(tiles) - 1), pl.height * 2 + 6))
for i, (lab, t) in enumerate(tiles):
    for r, im in enumerate((t, boost(t, 3.0 if i == 0 else 4.5))):
        im = im.copy(); ImageDraw.Draw(im).text((6, 4), lab, fill=(255, 255, 0)); sheet.paste(im, (i * (pl.width + 6), r * (pl.height + 6)))
sheet.save(out); print(out, sheet.size)
