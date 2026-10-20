"""plate | render side by side, torso crops.  python3.13 cmp.py <renderdir> <out.png> [views front,back] [zoom]"""
import sys
from pathlib import Path
from PIL import Image
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
PL = Image.open(R / 'ArtDir/hero/base_lock/male_body_plain.jpg').convert('RGB')
d = sys.argv[1]; out = sys.argv[2]; views = (sys.argv[3] if len(sys.argv) > 3 else 'front,back').split(','); Z = float(sys.argv[4]) if len(sys.argv) > 4 else 2.6
CROP = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440), 'front_low': (235, 280, 475, 520), 'back_low': (790, 280, 1050, 520), 'front_up': (235, 130, 475, 300)}
rows = []
for v in views:
    c = CROP[v]; base = v.split('_')[0]
    p = PL.crop(c); m = Image.open(f'{d}/{base}.png').convert('RGB').crop(c)
    sz = (int(p.width * Z), int(p.height * Z)); p = p.resize(sz, Image.LANCZOS); m = m.resize(sz, Image.LANCZOS)
    row = Image.new('RGB', (sz[0] * 2 + 10, sz[1]), (0, 0, 0)); row.paste(p, (0, 0)); row.paste(m, (sz[0] + 10, 0)); rows.append(row)
Wd = max(r.width for r in rows); sheet = Image.new('RGB', (Wd, sum(r.height for r in rows) + 10 * (len(rows) - 1)))
y = 0
for r in rows: sheet.paste(r, (0, y)); y += r.height + 10
sheet.save(out); print(out, sheet.size)
