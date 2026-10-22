# Contact sheet: sheet.py out.jpg cols tile_w "label=path" ...
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = [a.split('=', 1) for a in sys.argv[4:]]
th = tw * 9 // 16; lab = 34
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * (th + lab)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
try: f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
except Exception: f = ImageFont.load_default()
for i, (l, p) in enumerate(items):
    x, y = (i % cols) * tw, (i // cols) * (th + lab)
    try:
        im = Image.open(p).convert('RGB'); im.thumbnail((tw, th)); sheet.paste(im, (x, y + lab))
    except Exception as e:
        d.text((x + 10, y + lab + 10), 'MISSING', fill=(255, 80, 80), font=f)
    d.text((x + 8, y + 5), l, fill=(240, 240, 240), font=f)
sheet.save(out, quality=85)
