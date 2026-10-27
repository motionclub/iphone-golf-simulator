#!/usr/bin/env python3
"""Before | after sheets of the menu shots: sheet.py <before run> <after run> <out dir> [shots...]
Each sheet is both full 1920x1080 frames side by side (scaled to 1280 wide each), labelled, as JPEG."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
b, a, out = sys.argv[1:4]
shots = sys.argv[4:] or ["low", "close", "mid", "solo", "arrival"]
os.makedirs(out, exist_ok=True)
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
except Exception: font = ImageFont.load_default()
for s in shots:
    pa, pb = os.path.join(b, f"shot_{s}.png"), os.path.join(a, f"shot_{s}.png")
    if not (os.path.exists(pa) and os.path.exists(pb)): continue
    ims = [Image.open(p).convert("RGB").resize((1280, 720), Image.LANCZOS) for p in (pa, pb)]
    W = Image.new("RGB", (2560 + 16, 720), "white")
    for i, (im, lab) in enumerate(zip(ims, ("BEFORE (origin/main)", "AFTER"))):
        d = ImageDraw.Draw(im); d.rectangle((0, 0, 420, 52), fill=(11, 40, 120)); d.text((14, 8), f"{lab}  {s}", fill=(241, 177, 32), font=font)
        W.paste(im, (i * (1280 + 16), 0))
    W.save(os.path.join(out, f"before_after_{s}.jpg"), quality=90)
    print("wrote", s)
