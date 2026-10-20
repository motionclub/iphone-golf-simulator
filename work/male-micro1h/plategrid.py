"""Labeled-grid zooms of the head-detail plate (system python3 + Pillow).
usage: python3 plategrid.py <name> <x0> <y0> <x1> <y1> <scale> [step=10]
Draws plate-pixel gridlines (rows/cols in full-plate coordinates) so landmarks can be read exactly.
z(row) = 1.70466 - (row-76)*0.0013044 ; x(col) = (col-227.5)*0.0013044  (front panel)"""
import sys
from PIL import Image, ImageDraw, ImageFont
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
name, x0, y0, x1, y1, sc = sys.argv[1], *map(int, sys.argv[2:6]), int(sys.argv[6])
step = int(sys.argv[7]) if len(sys.argv) > 7 else 10
src = sys.argv[8] if len(sys.argv) > 8 else R + '/ArtDir/hero/base_lock/male_head_detail.jpg'
im = Image.open(src).convert('RGB')
c = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.LANCZOS)
d = ImageDraw.Draw(c, 'RGBA')
f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 13)
for r in range((y0 // step) * step, y1 + 1, step):
    if r < y0: continue
    Y = (r - y0) * sc
    major = (r % (step * 5) == 0)
    d.line((0, Y, c.width, Y), fill=(0, 255, 255, 110 if major else 55), width=1)
    d.text((2, Y + 1), str(r), font=f, fill=(255, 255, 0, 255))
for k in range((x0 // step) * step, x1 + 1, step):
    if k < x0: continue
    X = (k - x0) * sc
    major = (k % (step * 5) == 0)
    d.line((X, 0, X, c.height), fill=(255, 0, 255, 110 if major else 55), width=1)
    d.text((X + 2, 2), str(k), font=f, fill=(255, 200, 0, 255))
c.save(f'{R}/work/male-micro1h/plates/{name}.png'); print(c.size)
