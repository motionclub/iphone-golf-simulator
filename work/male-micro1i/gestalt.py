"""plate | unity-like mesh render side by side at the plate framing.  python3.13 gestalt.py <ul_dir> <out.png> [views comma]"""
import sys; sys.path.insert(0, '.')
from m1i_lib import *
d = sys.argv[1]; out = sys.argv[2]; views = (sys.argv[3] if len(sys.argv) > 3 else 'front,q3L,q3R,left').split(',')
BOX = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'right': (834, 62, 1271, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
CROP = {'front': (150, 40, 700, 580), 'left': (100, 40, 700, 580), 'right': (100, 40, 700, 580), 'q3L': (100, 20, 740, 540), 'q3R': (100, 20, 740, 540)}
rows = []
for v in views:
    p = PLATE.crop(BOX[v]); p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
    m = Image.open(f'{d}/plate_{v}.png').convert('RGB').resize(p.size, Image.LANCZOS)
    c = CROP[v]; p = p.crop(c); m = m.crop(c)
    row = Image.new('RGB', (p.width * 2 + 10, p.height)); row.paste(p, (0, 0)); row.paste(m, (p.width + 10, 0)); rows.append(row)
W = max(r.width for r in rows); H_ = sum(r.height for r in rows) + 10 * (len(rows) - 1)
sheet = Image.new('RGB', (W, H_), (0, 0, 0)); y = 0
for r in rows: sheet.paste(r, (0, y)); y += r.height + 10
sheet.save(out); print(out, sheet.size)
