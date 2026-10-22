"""Progress sheet: PLATE | START | CURRENT for profile (left) and 3/4 (q3L) head+neck.  python3.13 progress_sheet.py <tag> <out.png> <caption>"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head')
from j_lib import *
tag = sys.argv[1]; out = sys.argv[2]; cap = sys.argv[3] if len(sys.argv) > 3 else tag
def crop_spec(view):
    if view == 'left': return int(rowz(1.72)), int(rowz(1.36)), int(prof_col(-0.17, 'left')), int(prof_col(0.11, 'left'))
    return int(397 + (TOP - 1.72) / K), int(397 + (TOP - 1.36) / K), 60, 300
H_OUT = 640
rows = []
for view in ('left', 'q3L'):
    r0, r1, c0, c1 = crop_spec(view); box = BOXES[view]
    tiles = [PLATE.crop((c0, r0, c1, r1))]
    for t in ('start', tag):
        rn = Image.open(W / f'r/ul_{t}/plate_{view}.png').convert('RGB')
        tiles.append(rn.crop(((c0 - box[0]) * 2, (r0 - box[1]) * 2, (c1 - box[0]) * 2, (r1 - box[1]) * 2)))
    tiles = [t.resize((int(t.width * H_OUT / t.height), H_OUT), Image.LANCZOS) for t in tiles]
    for lab, t in zip(('PLATE (face_lock)', 'START (Micro1i)', f'NOW ({tag})'), tiles): ImageDraw.Draw(t).text((8, 6), lab, fill=(255, 255, 0))
    rows.append(tiles)
Wd = max(sum(t.width for t in r) + 8 * (len(r) - 1) for r in rows)
sheet = Image.new('RGB', (Wd, H_OUT * len(rows) + 8 * (len(rows) - 1) + 28), (16, 16, 18)); y = 0
ImageDraw.Draw(sheet).text((8, 8), cap, fill=(255, 255, 255)); y = 28
for r in rows:
    x = 0
    for t in r: sheet.paste(t, (x, y)); x += t.width + 8
    y += H_OUT + 8
sheet.save(out); print(out, sheet.size)
