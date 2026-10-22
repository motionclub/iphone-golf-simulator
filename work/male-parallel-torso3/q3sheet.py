"""3/4 view sheet: plate sheet panel | tag1 | tag2 ... for the 4 torso 3/4 views (needs r/<tag>/yaw*.png from rt.py).  PYTHONPATH=pylib python3.13 q3sheet.py out.png tag [tag...]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
F2 = font(20)
def label(im, t, pos=(8, 6)):
    im = im.convert('RGB'); d = ImageDraw.Draw(im); w = d.textlength(t, font=F2); d.rectangle((pos[0] - 4, pos[1] - 3, pos[0] + w + 6, pos[1] + 24), fill=(0, 0, 0)); d.text(pos, t, font=F2, fill=(255, 255, 255)); return im
def hstack(ims, gap=6):
    h = max(i.height for i in ims); s = Image.new('RGB', (sum(i.width for i in ims) + gap * (len(ims) - 1), h)); x = 0
    for i in ims: s.paste(i, (x, 0)); x += i.width + gap
    return s
def vstack(ims, gap=6):
    w = max(i.width for i in ims); s = Image.new('RGB', (w, sum(i.height for i in ims) + gap * (len(ims) - 1))); y = 0
    for i in ims: s.paste(i, (0, y)); y += i.height + gap
    return s
SH = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
import os
K = 0.00582; ZT, ZB = float(os.environ.get('ZT', 1.42)), float(os.environ.get('ZB', 0.74)); WH = int(os.environ.get('WH', 62)); HH = int(os.environ.get('HH', 520)); SEL = os.environ.get('VIEWS', '0123')
ITEMS = [('3/4 front L', 183, 672, 'yaw38_2.0_0.95'), ('3/4 front R', 480, 672, 'yaw-38_2.0_0.95'), ('3/4 back L', 788, 672, 'yaw142_2.0_0.95'), ('3/4 back R', 1090, 672, 'yaw-142_2.0_0.95')]
out = sys.argv[1]; tags = sys.argv[2:]; cols = []; H = HH; ITEMS = [it for i, it in enumerate(ITEMS) if str(i) in SEL]
for lab, cx, sole, fn in ITEMS:
    y0 = int(sole - ZT / K); y1 = int(sole - ZB / K); p = SH.crop((cx - WH, y0, cx + WH, y1)); p = p.resize((int(p.width * H / p.height), H), Image.LANCZOS); col = [label(p, f'plate {lab}')]
    for t in tags:
        m = Image.open(f'r/{t}/{fn}.png').convert('RGB'); py = lambda z: 500 - (z - 0.95) / 0.002
        mm = m.crop((int(500 - WH * K / 0.002), int(py(ZT)), int(500 + WH * K / 0.002), int(py(ZB)))); mm = mm.resize((int(mm.width * H / mm.height), H), Image.LANCZOS); col.append(label(mm, t))
    cols.append(col)
if os.environ.get('TRANSPOSE'):
    rows = [hstack([c[i] for c in cols]) for i in range(len(cols[0]))]; sheet = vstack(rows)
else: sheet = vstack([hstack(c) for c in cols])
sheet.save(out); print(out, sheet.size)
