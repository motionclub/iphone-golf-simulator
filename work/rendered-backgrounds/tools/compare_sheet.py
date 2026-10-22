#!/usr/bin/env python3
"""Before | after sheet per camera for one venue.
   tools/compare_sheet.py <venue> <before_dir> <after_dir> <out.jpg> [shot ...]"""
import sys, os
from PIL import Image, ImageDraw
venue, before, after, out = sys.argv[1:5]
shots = sys.argv[5:] or ['01_gameplay', '03_elevated', '04_stare_rival', '06_stare_player', '07_drone00', '07_drone35', '08_ring000', '08_ring180', '09_longlens']
W, H, T = 800, 450, 24
rows = [s for s in shots if os.path.exists(os.path.join(after, f'{venue}_{s}.png'))]
sheet = Image.new('RGB', (W * 2, (H + T) * len(rows)), 'black'); d = ImageDraw.Draw(sheet)
for r, s in enumerate(rows):
    for c, (lab, src) in enumerate((('BEFORE painted', before), ('AFTER rendered', after))):
        p = os.path.join(src, f'{venue}_{s}.png')
        y = r * (H + T)
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS), (c * W, y + T))
        d.text((c * W + 6, y + 6), f'{venue} {s} — {lab}', fill=(255, 230, 0))
sheet.save(out, quality=85)
print(out, len(rows), 'rows')
