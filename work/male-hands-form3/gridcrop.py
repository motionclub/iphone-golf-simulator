"""gridcrop.py <image> x0 y0 x1 y1 scale out.png [step] : crop + upscale + labelled grid in ORIGINAL pixel coordinates"""
import sys
from PIL import Image, ImageDraw, ImageFont
img, x0, y0, x1, y1, s, out = sys.argv[1], *map(int, sys.argv[2:6]), int(sys.argv[6]), sys.argv[7]
step = int(sys.argv[8]) if len(sys.argv) > 8 else 5
im = Image.open(img).convert('RGB').crop((x0, y0, x1, y1)); im = im.resize((im.width * s, im.height * s), Image.BICUBIC)
d = ImageDraw.Draw(im)
try: f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 13)
except Exception: f = ImageFont.load_default()
for x in range((x0 // step + 1) * step, x1, step):
    X = (x - x0) * s; d.line([(X, 0), (X, im.height)], fill=(255, 200, 40) if x % (step * 2) == 0 else (120, 100, 40), width=1); d.text((X + 2, 2), str(x), fill=(255, 230, 120), font=f)
for y in range((y0 // step + 1) * step, y1, step):
    Y = (y - y0) * s; d.line([(0, Y), (im.width, Y)], fill=(255, 200, 40) if y % (step * 2) == 0 else (120, 100, 40), width=1); d.text((2, Y + 2), str(y), fill=(255, 230, 120), font=f)
im.save(out); print(out, im.size)
