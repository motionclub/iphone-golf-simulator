"""plate vs mesh ear: side + both 3/4 + front.  python3.13 ear_views.py <tag...>  (needs r/<tag>/ul/plate_*.png)"""
import sys; sys.path.insert(0, '.')
from m1i_lib import *
from PIL import ImageFont
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
def crop_pair(view, pl_box, zoom, tag):
    x0, y0, x1, y1 = pl_box
    p = PLATE.crop(pl_box).resize(((x1 - x0) * zoom, (y1 - y0) * zoom), Image.LANCZOS)
    b0 = {'front': (5, 62), 'q3L': (5, 390), 'left': (433, 62), 'q3R': (433, 390)}[view]
    m = Image.open(f'r/{tag}/ul/plate_{view}.png').convert('RGB')
    mb = ((x0 - b0[0]) * 2, (y0 - b0[1]) * 2, (x1 - b0[0]) * 2, (y1 - b0[1]) * 2)
    return p, m.crop(mb).resize(((x1 - x0) * zoom, (y1 - y0) * zoom), Image.LANCZOS)
tags = sys.argv[2:]; out = sys.argv[1]
views = [('left', (625, 145, 705, 225), 4), ('q3L', (235, 440, 305, 540), 4), ('q3R', (640, 440, 740, 540), 4), ('front', (290, 140, 350, 230), 4)]
tiles = []
for v, box, z in views:
    p, _ = crop_pair(v, box, z, tags[0]); tiles.append((f'PLATE {v}', p))
    for t in tags: tiles.append((f'{t} {v}', crop_pair(v, box, z, t)[1]))
H_ = max(t.height for _, t in tiles); W = sum(t.width for _, t in tiles) + 8 * len(tiles)
# wrap into rows of 2 views each
rows = []; cur = []; cw = 0
per = 1 + len(tags)
for i in range(0, len(tiles), per):
    grp = tiles[i:i + per]; rows.append(grp)
RW = max(sum(t.width for _, t in g) + 8 * len(g) for g in rows)
sh = Image.new('RGB', (RW, sum(max(t.height for _, t in g) + 28 for g in rows)), (20, 20, 24)); d = ImageDraw.Draw(sh); y = 0
for g in rows:
    x = 0
    for lab, im in g: sh.paste(im, (x, y + 28)); d.text((x + 4, y + 4), lab, font=f(20), fill=(240, 240, 240)); x += im.width + 8
    y += max(t.height for _, t in g) + 28
sh.save(out); print(out, sh.size)
