#!/usr/bin/env python3
"""Worst-N before/after contact sheet from one or more sweep folders.
usage: sheet.py <out.jpg> <sweep_dir> [<sweep_dir> ...] [--n 20]
Each sweep dir holds summary.json (worst list) and <tag>_before.png / <tag>_after.png."""
import json, sys, os
from PIL import Image, ImageDraw, ImageFont

args = [a for a in sys.argv[1:]]
n = 20
if '--n' in args:
    i = args.index('--n'); n = int(args[i + 1]); del args[i:i + 2]
out, dirs = args[0], args[1:]
items = []
for d in dirs:
    s = json.load(open(os.path.join(d, 'summary.json')))
    for w in s['worst']:
        w['dir'] = d; items.append(w)
items.sort(key=lambda w: -w['before'])
items = [w for w in items if os.path.exists(os.path.join(w['dir'], w['tag'] + '_before.png'))][:n]
try:
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
    small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 12)
except Exception:
    font = small = ImageFont.load_default()
T = 260; cols = 4  # 4 pairs per row
W = cols * (2 * T + 14); rows = (len(items) + cols - 1) // cols; H = rows * (T + 46) + 10
sheet = Image.new('RGB', (W, H), (24, 26, 30)); dr = ImageDraw.Draw(sheet)
for k, w in enumerate(items):
    x = (k % cols) * (2 * T + 14) + 4; y = (k // cols) * (T + 46) + 4
    for j, tag in enumerate(['before', 'after']):
        im = Image.open(os.path.join(w['dir'], w['tag'] + '_' + tag + '.png')).convert('RGB')
        if im.width != im.height:  # 1920x1080 proof frames: the centred square around the deepest point
            s0 = min(im.size); l = (im.width - s0) // 2; t0 = (im.height - s0) // 2; im = im.crop((l, t0, l + s0, t0 + s0))
        im = im.resize((T, T))
        sheet.paste(im, (x + j * (T + 4), y + 30))
        val = w[tag]; col = (255, 110, 100) if val > 3 else (120, 230, 140)
        dr.text((x + j * (T + 4) + 4, y + 34), f"{tag.upper()} {val:.1f} mm", fill=col, font=font)
        where = w[tag + 'Where'] if val > 0 else 'clear'
        dr.text((x + j * (T + 4) + 4, y + T + 12), where[:40], fill=(200, 200, 200), font=small)
    dr.text((x, y + 6), f"#{k + 1} {w['ctx']} {w['clip']} f{w['frame']}"[:70], fill=(240, 240, 240), font=font)
sheet.save(out, quality=88)
print(out, len(items))
