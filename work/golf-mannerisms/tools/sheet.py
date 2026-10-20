# sheet.py <film dir> <out.jpg> <cols> <title> <crop:0|1> idx[:label] ...  -> contact sheet; crop=1 zooms on the golfer box from trace.csv
import sys, csv
from PIL import Image, ImageDraw
d, out, cols, title, crop = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5] == '1'
items = [a.split(':', 1) + [''] for a in sys.argv[6:]]
box = {}
for r in csv.DictReader(open(f'{d}/trace.csv')):
    if int(r['saved']) >= 0: box[int(r['saved'])] = [float(r[k]) for k in ('gx0', 'gy0', 'gx1', 'gy1')]
w, h = (300, 400) if crop else (480, 270)
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h + 24), (0, 0, 0))
dr = ImageDraw.Draw(sheet); dr.text((6, 5), title, fill=(255, 255, 0))
for i, it in enumerate(items):
    idx, label = int(it[0]), it[1]
    im = Image.open(f'{d}/f_{idx:05d}.jpg')
    if crop and idx in box:
        W, H = im.size; x0, y0, x1, y1 = box[idx]
        cx, cy = (x0 + x1) / 2 * W, (1 - (y0 + y1) / 2) * H
        ch = max((y1 - y0) * H * 1.15, 200); cw = ch * w / h
        im = im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
    im = im.resize((w, h))
    x, y = (i % cols) * w, 24 + (i // cols) * h
    sheet.paste(im, (x, y))
    dr.rectangle((x, y, x + 200, y + 16), fill=(0, 0, 0)); dr.text((x + 4, y + 3), f'#{idx} {label}', fill=(255, 255, 0))
sheet.save(out, quality=85)
