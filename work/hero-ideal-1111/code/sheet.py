#!/usr/bin/env python3
"""sheet.py out.jpg cols cellw img[:label] ...  -> labelled contact sheet."""
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols, cw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = [a.rsplit('::', 1) if '::' in a else [a, a.split('/')[-1]] for a in sys.argv[4:]]
try: font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 15)
except Exception: font = ImageFont.load_default()
cells = []
for p, lab in items:
    box = None
    if '@' in p: p, b = p.split('@'); box = tuple(int(x) for x in b.split(','))
    im = Image.open(p).convert('RGB')
    if box: im = im.crop(box)
    h = round(im.height * cw / im.width); im = im.resize((cw, h), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.rectangle([0, 0, d.textlength(lab, font=font) + 10, 21], fill=(0, 0, 0)); d.text((5, 3), lab, fill=(255, 255, 255), font=font)
    cells.append(im)
rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
H = sum(max(c.height for c in r) for r in rows); W = cw * cols
sheet = Image.new('RGB', (W, H), (24, 24, 24)); y = 0
for r in rows:
    for i, c in enumerate(r): sheet.paste(c, (i * cw, y))
    y += max(c.height for c in r)
sheet.save(out, quality=88); print(out, sheet.size)
