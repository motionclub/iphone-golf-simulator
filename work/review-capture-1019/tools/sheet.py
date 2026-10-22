#!/usr/bin/env python3
"""sheet.py <out.jpg> <title> <tileH> <row label>=<glob> ... : one labelled row per glob (sorted), each tile captioned with its file's angle."""
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
out, title, th = sys.argv[1], sys.argv[2], int(sys.argv[3])
rows = [a.split('=', 1) for a in sys.argv[4:]]
def font(sz):
    for f in ['/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Helvetica.ttc']:
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()
F, FT, FR = font(max(14, th // 28)), font(max(22, th // 14)), font(max(16, th // 20))
data = []
for label, g in rows:
    files = sorted(glob.glob(g)); ims = []
    for f in files:
        im = Image.open(f).convert('RGB'); w = int(im.width * th / im.height); ims.append((os.path.splitext(os.path.basename(f))[0], im.resize((w, th), Image.LANCZOS)))
    data.append((label, ims))
lw = int(th * .55); pad = 8; top = int(th * .16)
W = lw + max(sum(i.width + pad for _, i in ims) for _, ims in data) + pad
H = top + len(data) * (th + pad + int(th * .07)) + pad
sheet = Image.new('RGB', (W, H), (24, 26, 30)); d = ImageDraw.Draw(sheet)
d.text((pad * 2, top // 4), title, font=FT, fill=(255, 255, 255))
y = top
for label, ims in data:
    d.text((pad * 2, y + th // 2 - 20), label.replace('\\n', '\n'), font=FR, fill=(230, 230, 120))
    x = lw
    for name, im in ims:
        sheet.paste(im, (x, y)); cap = name.split('_', 2)[-1] if name.count('_') >= 2 else name
        cap = '_'.join(name.split('_')[-2:]) if name.split('_')[-2].isdigit() else cap
        d.text((x + 4, y + th + 2), cap, font=F, fill=(220, 220, 220)); x += im.width + pad
    y += th + pad + int(th * .07)
sheet.save(out, quality=90); print(out, sheet.size)
