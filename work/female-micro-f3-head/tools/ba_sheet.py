"""plate | F1 | F2 lower-face before/after sheet at the plate cameras.  python3 ba_sheet.py <f1_dir> <f2_dir> <out.png> [tagF1 tagF2]"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
d1, d2, out = sys.argv[1], sys.argv[2], sys.argv[3]
t1 = sys.argv[4] if len(sys.argv) > 4 else 'F1'; t2 = sys.argv[5] if len(sys.argv) > 5 else 'F2'
UP = 3
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PAN = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'right': (830, 55, 1195, 342), 'q3L': (85, 385, 430, 656), 'q3R': (440, 385, 800, 656)}
WIN = {'front': (0.10, 0.36, 0.90, 0.84), 'left': (0.05, 0.30, 0.82, 0.84), 'right': (0.18, 0.30, 0.95, 0.84), 'q3L': (0.08, 0.34, 0.92, 0.90), 'q3R': (0.05, 0.34, 0.92, 0.90)}
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
except Exception: font = ImageFont.load_default()
rows = []
views = [v for v in ('front', 'q3L', 'q3R', 'left') if True]
for v in views:
    box = PAN[v]; pl = src.crop(box); w, h = pl.size; big = (w * UP, h * UP)
    f0, f1, f2, f3 = WIN[v]; c = (int(f0 * big[0]), int(f1 * big[1]), int(f2 * big[0]), int(f3 * big[1]))
    tiles = [pl.resize(big, Image.LANCZOS).crop(c)]
    for d, t in ((d1, t1), (d2, t2)):
        r = Image.open(f'{d}/{t}_{v}.png').convert('RGBA').resize(big, Image.LANCZOS)
        af = (np.asarray(r)[..., 3] / 255.0)[..., None]; rgb = np.asarray(r.convert('RGB')).astype(float)
        im = Image.fromarray((rgb * af + np.array([224., 224., 226.]) * (1 - af)).astype(np.uint8)).crop(c); tiles.append(im)
    TW = 760
    tiles = [t.resize((TW, int(t.height * TW / t.width)), Image.LANCZOS) for t in tiles]
    row = Image.new('RGB', (TW * 3, tiles[0].height))
    for k, t in enumerate(tiles): row.paste(t, (k * TW, 0))
    rows.append(row)
sheet = Image.new('RGB', (rows[0].width, sum(r.height for r in rows) + 40), (20, 20, 22)); y = 40
for r in rows: sheet.paste(r, (0, y)); y += r.height
d = ImageDraw.Draw(sheet); W3 = rows[0].width // 3
import os
LAB = os.environ.get('LABELS', 'PLATE|F1 (MicroF1 staged)|F2 (this build)').split('|')
for k, lab in enumerate(LAB): d.text((k * W3 + 12, 8), lab, fill=(255, 255, 255), font=font)
sheet.save(out); print(sheet.size)
