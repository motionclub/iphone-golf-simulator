"""tile the cells written by emo_render.py (system python + Pillow).  python3 emo_tile.py <cells.json> <out.png> [cols] [cell_w cell_h]"""
import json, sys
from PIL import Image, ImageDraw, ImageFont
js = json.load(open(sys.argv[1])); out = sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
cells = js['cells']
views = js.get('views') or ['v']
try:
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
except Exception:
    font = ImageFont.load_default()
im0 = Image.open(cells[0]['files'][0]); w, h = im0.size
if len(sys.argv) > 5:
    w, h = int(sys.argv[4]), int(sys.argv[5])
nr = (len(cells) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, nr * (h * len(views) + 20)), (30, 30, 34)); d = ImageDraw.Draw(sheet)
for i, c in enumerate(cells):
    cx, cy = (i % cols) * w, (i // cols) * (h * len(views) + 20)
    d.text((cx + 4, cy + 3), f"{js['clip']} {js['tag']} f{c['frame']} t={c['t']:.2f}", fill=(255, 220, 120), font=font)
    for j, f in enumerate(c['files']):
        sheet.paste(Image.open(f).convert('RGB').resize((w, h)), (cx, cy + 20 + j * h))
sheet.save(out); print('saved', out, sheet.size)
