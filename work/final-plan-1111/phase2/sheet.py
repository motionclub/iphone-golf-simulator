#!/usr/bin/env python3
"""sheet.py out.jpg cellw img:label ... [--cols n]: labelled contact sheet."""
import sys
from PIL import Image, ImageDraw, ImageFont
args = sys.argv[1:]; cols = None
if "--cols" in args: i = args.index("--cols"); cols = int(args[i + 1]); del args[i:i + 2]
out, cw, items = args[0], int(args[1]), [a.split(":", 1) for a in args[2:]]
cols = cols or len(items)
def font(n):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n)
    except Exception: return ImageFont.load_default()
ims = []
for path, label in items:
    im = Image.open(path).convert("RGB"); im = im.resize((cw, round(im.height * cw / im.width)), Image.LANCZOS); ims.append((im, label))
ch = max(im.height for im, _ in ims); rows = -(-len(ims) // cols)
sheet = Image.new("RGB", (cols * cw, rows * (ch + 34)), "#fcfcfb"); d = ImageDraw.Draw(sheet)
for k, (im, label) in enumerate(ims):
    x, y = (k % cols) * cw, (k // cols) * (ch + 34); sheet.paste(im, (x, y)); d.text((x + 8, y + ch + 6), label, font=font(20), fill="#0b0b0b")
sheet.save(out, quality=88); print(out, sheet.size)
