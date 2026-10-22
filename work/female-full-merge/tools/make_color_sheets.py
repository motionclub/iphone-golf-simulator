"""Compose the colour sheets from color/raw (transparent Unity-like renders) over a plate-like grey.  ./py.sh tools/make_color_sheets.py"""
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
def font(sz, bold=False):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        try: return ImageFont.truetype(p, sz, index=1 if (bold and p.endswith('.ttc')) else 0)
        except Exception: pass
    return ImageFont.load_default()
F18, F22, F26, F30 = font(18), font(22), font(26, True), font(30, True)
BG = (24, 24, 28); FG = (235, 235, 235); WARN = (255, 200, 120)
def grad(size, top=(205, 205, 208), bot=(232, 232, 234)):
    w, h = size; a = np.linspace(0, 1, h)[:, None, None]; arr = (np.array(top)[None, None, :] * (1 - a) + np.array(bot)[None, None, :] * a) * np.ones((1, w, 1)); return Image.fromarray(arr.astype(np.uint8), 'RGB')
def comp(name, size=None):
    m = Image.open(f'color/raw/col_{name}.png').convert('RGBA'); b = grad(m.size).convert('RGBA'); return Image.alpha_composite(b, m).convert('RGB')
def fit(im, w=None, h=None):
    r = min((w or 10**9) / im.width, (h or 10**9) / im.height); return im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
def panel(sheet, im, x, y, label):
    sheet.paste(im, (x, y)); d = ImageDraw.Draw(sheet); d.rectangle([x, y, x + im.width, y + 32], fill=(0, 0, 0)); d.text((x + 8, y + 4), label, font=F22, fill=FG)
P = json.load(open('color/female_palette.json'))
LIT = 'Unity-like lit rig (4 suns + trilight ambient, F3 ul.py rig), EEVEE, orthographic. Palette values = project Unity female palette. Not a Unity capture.'
# ---------------------------------------------------------------- full figure
names = [('b_0_0_0_0_0.86_1.95_900_1300', 'front'), ('b_35_3_0_0_0.86_1.95_900_1300', '3/4 front (her left)'), ('b_90_0_0_0_0.86_1.95_900_1300', 'left'), ('b_180_0_0_0_0.86_1.95_900_1300', 'back'), ('b_-90_0_0_0_0.86_1.95_900_1300', 'right')]
pw, ph = 440, 636; sheet = Image.new('RGB', (pw * 5 + 48, ph + 190), BG); d = ImageDraw.Draw(sheet)
d.text((24, 14), 'FEMALE FULL staged - colour pass: skin, eyes, brows, lips', font=F30, fill=FG); d.text((24, 56), LIT, font=F18, fill=WARN)
for i, (n, lab) in enumerate(names): panel(sheet, fit(comp(n), pw, ph), 24 + i * pw, 90, lab)
sk = P['skin']; d.text((24, ph + 104), f"skin {sk['hex']} (sRGB {sk['srgb']}, smoothness {sk['smoothness']}) on the whole body: head, neck, torso, arms, hands, legs, feet.  Geometry is the staged merge, untouched.  Hair_F stays hidden/optional.", font=F18, fill=FG)
d.text((24, ph + 134), 'Not a form pass; body shapes are the staged merge (open FORM5 fails still visible: bust side fill, underbutt crease; neck weld NECK_STEP_MM 7.92).', font=F18, fill=FG)
sheet.save('color/COLOR_SHEET_full.png'); print('saved COLOR_SHEET_full', sheet.size)
# ---------------------------------------------------------------- face / details
W = 2200; sheet = Image.new('RGB', (W, 1800), BG); d = ImageDraw.Draw(sheet)
d.text((24, 14), 'FEMALE FULL staged - colour pass: face and details', font=F30, fill=FG); d.text((24, 56), LIT, font=F18, fill=WARN)
a = fit(comp('b_0_0_0_-0.115_1.553_0.17_1100_560'), 1060); panel(sheet, a, 24, 96, 'eyes front')
b = fit(comp('b_32_0_0_-0.115_1.553_0.17_1100_560'), 1060); panel(sheet, b, 24 + 1100, 96, 'eyes 3/4')
y = 96 + max(a.height, b.height) + 16
c = fit(comp('b_0_0_0_-0.12_1.475_0.11_800_600'), 520, 420); panel(sheet, c, 24, y, 'lips + nostrils')
e = fit(comp('front'), 560, 480); panel(sheet, e, 24 + 540, y, 'head front')
f = fit(comp('q3L'), 560, 480); panel(sheet, f, 24 + 1120, y, 'head 3/4')
g = fit(comp('left'), 440, 480); panel(sheet, g, 24 + 1700, y, 'head left')
y += 500
h = fit(comp('b_0_0_0_0_0.82_0.80_1000_800'), 1060, 560); panel(sheet, h, 24, y, 'hands / hips (skin continuity)')
k = fit(comp('b_25_0_0_-0.03_0.10_0.50_1000_600'), 1060, 560); panel(sheet, k, 24 + 1100, y, 'feet')
y += max(h.height, k.height) + 14
d.text((24, y), 'face palette (sRGB 0-1, smoothness): ' + '   '.join(f"{k_.replace('Face_', '')} {v['hex']}" for k_, v in P['face'].items()), font=F18, fill=FG)
sheet = sheet.crop((0, 0, W, y + 40)); sheet.save('color/COLOR_SHEET_face.png'); print('saved COLOR_SHEET_face', sheet.size)
