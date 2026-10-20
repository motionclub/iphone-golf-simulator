"""Before/after from the REAL Unity captures: before (baseline/unity_captures_before = Micro1k + later chats) | after (unity_captures_l = Micro1l) | authority plate.  python3.13 compose_ba_l.py <out.png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-micro1l-head'
B = W / 'baseline/unity_captures_before'; A = W / 'unity_captures_l'; FL = R / 'ArtDir/hero/base_lock/face_lock'
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
def cc(im, w, h, cx=None, cy=None):
    cx = im.width // 2 if cx is None else cx; cy = im.height // 2 if cy is None else cy
    return im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
S = 560
rows = [('front  (jaw all around, cheeks, lips)', 'face_front', '01_front_face.png'), ('three-quarter  (mandible edge, cheek, lips)', 'face_threequarter', '04_threequarter_front_left.png'), ('profile  (mandible, upper lip)', 'face_profile', '02_left_profile.png'), ('3/4 back  (jaw / ramus fade)', 'face_threequarter_back', '15_ma_threequarter_back_left.png'), ('chin 3/4 (under-jaw plane)', 'chin_threequarter', '04_threequarter_front_left.png')]
img = Image.new('RGB', (S * 3 + 40, 36 + len(rows) * (S + 36)), (30, 31, 35)); d = ImageDraw.Draw(img)
d.text((12, 6), 'Micro1l - before (Micro1k, left) | after (Micro1l, middle) | authority plate (right) - real Unity captures, locked studio', font=f(22), fill=(240, 240, 240))
y = 36
for lab, v, plate in rows:
    d.text((12, y + 4), lab, font=f(20), fill=(200, 200, 205)); y += 30
    ims = []
    for base in (B, A):
        im = Image.open(base / f'{v}.png').convert('RGB'); im = cc(im, 760, 760); ims.append(im.resize((S, S), Image.LANCZOS))
    pl = Image.open(FL / plate).convert('RGB'); s = min(S / pl.width, S / pl.height); pl = pl.resize((int(pl.width * s), int(pl.height * s)), Image.LANCZOS); pn = Image.new('RGB', (S, S), (40, 40, 44)); pn.paste(pl, ((S - pl.width) // 2, (S - pl.height) // 2)); ims.append(pn)
    for i, im in enumerate(ims): img.paste(im, (i * (S + 10), y))
    y += S + 6
img.save(sys.argv[1]); print(sys.argv[1], img.size)
