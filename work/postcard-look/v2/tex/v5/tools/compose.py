"""compose.py <out.png> <cols> <cell_w> <cell_h> <label=path[@x0,y0,x1,y1]> ... : contact sheet from JPG/PNG files (Pillow, system python3)."""
import sys
from PIL import Image, ImageDraw
out, cols, cw, ch = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
items = sys.argv[5:]
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (cw + 6) + 6, rows * (ch + 24) + 6), (24, 22, 24))
d = ImageDraw.Draw(sheet)
for i, it in enumerate(items):
    lab, rest = it.split('=', 1)
    box = None
    if '@' in rest:
        rest, b = rest.rsplit('@', 1); box = tuple(int(x) for x in b.split(','))
    im = Image.open(rest).convert('RGB')
    if box: im = im.crop(box)
    im.thumbnail((cw, ch), Image.LANCZOS)
    x = 6 + (i % cols) * (cw + 6); y = 6 + (i // cols) * (ch + 24)
    sheet.paste(im, (x, y + 18)); d.text((x + 2, y + 2), lab, fill=(255, 240, 200))
sheet.save(out); print('wrote', out, sheet.size)
