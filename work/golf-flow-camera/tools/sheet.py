# sheet.py <film dir> <out.jpg> <cols> <title> idx[:label] ...  -> contact sheet of saved frames f_#####.jpg
import sys
from PIL import Image, ImageDraw
d, out, cols, title = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
items = [a.split(':', 1) + [''] for a in sys.argv[5:]]
w, h = 480, 270
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * h + 24), (0, 0, 0))
dr = ImageDraw.Draw(sheet); dr.text((6, 5), title, fill=(255, 255, 0))
for i, it in enumerate(items):
    idx, label = int(it[0]), it[1]
    im = Image.open(f'{d}/f_{idx:05d}.jpg').resize((w, h))
    x, y = (i % cols) * w, 24 + (i // cols) * h
    sheet.paste(im, (x, y))
    dr.rectangle((x, y, x + 300, y + 16), fill=(0, 0, 0)); dr.text((x + 4, y + 3), f'#{idx} {label}', fill=(255, 255, 0))
sheet.save(out, quality=85)
