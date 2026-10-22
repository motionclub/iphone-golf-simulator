"""Compose a labelled contact sheet from Unity proof frames: python3 sheet_unity.py <out.png> <cols> <cell_px> <file1> <file2> ...  (label = file stem)"""
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
try: font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 12)
except Exception: font = ImageFont.load_default()
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cell, rows * (cell + 16)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB'); im.thumbnail((cell, cell))
    x, y = (i % cols) * cell, (i // cols) * (cell + 16)
    sheet.paste(im, (x, y + 16))
    d.text((x + 3, y + 2), f.split('/')[-1].rsplit('.', 1)[0][-34:], fill=(255, 220, 120), font=font)
sheet.save(out); print('saved', out, sheet.size)
