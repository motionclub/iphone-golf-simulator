"""compose a sheet: python3 tile_sheet.py <cells.json> <out.png> [cols] [label]   (system python + Pillow)"""
import json, sys
from PIL import Image, ImageDraw, ImageFont
js = json.load(open(sys.argv[1])); out = sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
label = sys.argv[4] if len(sys.argv) > 4 else js['clip']
cells = js['cells']
nv = len(cells[0]['files'])
im0 = Image.open(cells[0]['files'][0]); w, h = im0.size
try:
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
except Exception:
    font = ImageFont.load_default()
nrows = (len(cells) + cols - 1) // cols
cell_h = h * nv + 20
sheet = Image.new('RGB', (cols * w, nrows * cell_h), (30, 30, 34))
d = ImageDraw.Draw(sheet)
for i, c in enumerate(cells):
    cx, cy = (i % cols) * w, (i // cols) * cell_h
    for j, f in enumerate(c['files']):
        sheet.paste(Image.open(f).convert('RGB'), (cx, cy + 20 + j * h))
    d.text((cx + 4, cy + 3), f"{label} f{c['frame']}  t={c['frame']/30:.2f}", fill=(255, 220, 120), font=font)
sheet.save(out)
print('saved', out, sheet.size)
