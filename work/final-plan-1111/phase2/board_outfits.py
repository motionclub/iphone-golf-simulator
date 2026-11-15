#!/usr/bin/env python3
"""board_outfits.py <renders dir> <out.jpg>: the male head to toe in the tennis, golf and bowling outfits, four sides each."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
R, OUT = sys.argv[1], sys.argv[2]
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
CW, CH, GAP, PAD = 300, 564, 12, 18
BOX = (190, 170, 570, 884)
def cell(p): return Image.open(os.path.join(R, p)).convert("RGB").crop(BOX).resize((CW, CH), Image.LANCZOS)
rows = [("Tennis", "tennisfit"), ("Golf", "golffit"), ("Bowling", "bowlfit")]; views = [("fullfront", "front"), ("full3q", "three-quarter"), ("fullside", "side"), ("fullback", "back")]
W = PAD * 2 + 4 * CW + 3 * GAP; H = 64 + len(rows) * (34 + CH + 34) + 40
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "The male in each outfit  (Blender studio renders, flat colours, not in game yet)", font=font(24, True), fill="#0b0b0b")
y = 64
for title, k in rows:
    d.text((PAD, y), title, font=font(20, True), fill="#0b0b0b"); y += 34
    for i, (v, label) in enumerate(views):
        x = PAD + i * (CW + GAP); im.paste(cell(f"{k}_down_dressed_{v}.png"), (x, y)); d.text((x + 2, y + CH + 6), label, font=font(17), fill="#0b0b0b")
    y += CH + 34
d.text((PAD, y + 4), "Body: the whole-body version with the rebuilt chest. Tops are refitted; shorts, trousers, shoes, cap and gloves are as tailored.", font=font(15), fill="#52514e")
im.save(OUT, quality=90); print(OUT, im.size)
