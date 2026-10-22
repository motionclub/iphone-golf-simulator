"""strip of several images side by side (RGBA over grey).  python3.13 cmpstrip.py out.png px img1 img2 ..."""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from PIL import Image, ImageDraw
out, px = sys.argv[1], int(sys.argv[2]); names = sys.argv[3:]
bg = Image.new('RGB', (px * len(names), px), (70, 70, 74))
for k, n in enumerate(names):
    im = Image.open(n).convert('RGBA').resize((px, px), Image.LANCZOS); bg.paste(im, (k * px, 0), im)
bg.save(out); print('ok', out)
