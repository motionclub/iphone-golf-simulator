"""Before/after from the REAL Unity captures: Micro1i (baseline/unity_captures_micro1i) vs Micro1j (ArtDir proof/male_form_d/unity).  python3.13 compose_ba.py <out.png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-micro1j-head'
B = W / 'baseline/unity_captures_micro1i'; A = R / 'ArtDir/hero/base_lock/proof/male_form_d/unity'; FL = R / 'ArtDir/hero/base_lock/face_lock'
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
def cc(im, w, h, cx=None, cy=None):
    cx = im.width // 2 if cx is None else cx; cy = im.height // 2 if cy is None else cy
    return im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
S = 560
rows = [('profile  (jawline, Adam apple, nape)', 'face_profile', None), ('three-quarter  (jaw border, throat)', 'face_threequarter', None), ('head side  (nape lump)', 'head_side', (720, 720))]
plates = {'face_profile': '02_left_profile.png', 'face_threequarter': '04_threequarter_front_left.png', 'head_side': '02_left_profile.png'}
img = Image.new('RGB', (S * 3 + 40, 36 + 3 * (S + 36)), (30, 31, 35)); d = ImageDraw.Draw(img)
d.text((12, 6), 'Micro1j - before (Micro1i, left) | after (Micro1j, middle) | authority plate (right) - real Unity captures', font=f(22), fill=(240, 240, 240))
y = 36
for lab, v, crop in rows:
    d.text((12, y + 4), lab, font=f(20), fill=(200, 200, 205)); y += 30
    ims = []
    for base in (B, A):
        im = Image.open(base / f'{v}.png').convert('RGB'); im = cc(im, 760, 760) if crop is None else cc(im, *crop); ims.append(im.resize((S, S), Image.LANCZOS))
    pl = Image.open(FL / plates[v]).convert('RGB'); s = min(S / pl.width, S / pl.height); pl = pl.resize((int(pl.width * s), int(pl.height * s)), Image.LANCZOS); pn = Image.new('RGB', (S, S), (40, 40, 44)); pn.paste(pl, ((S - pl.width) // 2, (S - pl.height) // 2)); ims.append(pn)
    for i, im in enumerate(ims): img.paste(im, (i * (S + 10), y))
    y += S + 6
img.save(sys.argv[1]); print(sys.argv[1], img.size)
