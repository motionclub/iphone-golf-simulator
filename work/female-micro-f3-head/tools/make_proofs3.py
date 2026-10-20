"""MicroF3 proof images -> proof/.   python3 make_proofs3.py   (renders via Blender: F2 staged blend [old lip palette] and the F3 staged blend)"""
import sys, subprocess, json, os, shutil
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fl, contour as ct
W3 = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/'
B = '/Applications/Blender.app/Contents/MacOS/Blender'
F2B = W3 + 'start/F2_STAGED.blend'; F3B = W3 + 'export/HeroBase_Female_MicroF3_head_STAGED.blend'
P = W3 + 'proof/'
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 26)
except Exception: font = ImageFont.load_default()
def render(blend, outdir, views, tag, palette):
    env = dict(os.environ); env['FACE_PALETTE'] = palette
    os.makedirs(outdir, exist_ok=True)
    subprocess.run([B, '-b', '--factory-startup', '--python', W3 + 'tools/ul.py', '--', blend, outdir, views, tag], check=True, capture_output=True, env=env)
def on_grey(path):
    im = Image.open(path).convert('RGBA'); bg = Image.new('RGBA', im.size, (224, 224, 226, 255)); bg.alpha_composite(im); return bg.convert('RGB')
# ------------------------------------------------------------------------------------------------ 1. jaw close-ups: plate profile | F2 | F3
VIEWS = 'c:90:0:0:-0.03:1.49:0.13:1100,c:35:0:-0.015:-0.06:1.47:0.13:1100,c:-35:0:0.015:-0.06:1.47:0.13:1100'
NAMES = ['c_90_0_0_-0.03_1.49_0.13_1100', 'c_35_0_-0.015_-0.06_1.47_0.13_1100', 'c_-35_0_0.015_-0.06_1.47_0.13_1100']
RD = W3 + 'renders/proof3/'
render(F2B, RD, VIEWS, 'F2', 'old'); render(F3B, RD, VIEWS, 'F3', 'new')
src = Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB')
h = 0.065 / fl.K; r = float(fl.rowz(1.49)); c = 653 + (-0.03 - fl.Y0) / fl.K
plate = src.crop((int(c - h), int(r - h), int(c + h), int(r + h))).resize((1100, 1100), Image.LANCZOS)
S = 700
sh = Image.new('RGB', (S * 3, S * 3 + 44), (20, 20, 22)); d = ImageDraw.Draw(sh)
for k, lab in enumerate(('PLATE (profile; the plate has no 3/4 close-up of this area)', 'F2 (delivered earlier)', 'F3 (this build)')): d.text((k * S + 10, 8), lab, fill=(255, 255, 255), font=font)
sh.paste(plate.resize((S, S), Image.LANCZOS), (0, 44))
for j in range(3):
    for k, t in ((1, 'F2'), (2, 'F3')):
        sh.paste(on_grey(f'{RD}{t}_{NAMES[j]}.png').resize((S, S), Image.LANCZOS), (k * S, 44 + j * S))
sh.save(P + 'F3_jaw_closeups_plate_F2_F3.png'); print('1', sh.size)
# ------------------------------------------------------------------------------------------------ 2. high-pass shading F2 vs F3 (lower face, 4 views)
HV = ['c:0:0:0:-0.06:1.46:0.17:700', 'c:35:0:-0.01:-0.06:1.46:0.17:700', 'c:-35:0:0.01:-0.06:1.46:0.17:700', 'c:90:0:0:-0.05:1.46:0.17:700']
render(F2B, W3 + 'renders/proof3hp/', ','.join(HV), 'F2', 'old'); render(F3B, W3 + 'renders/proof3hp/', ','.join(HV), 'F3', 'new')
from PIL import ImageFilter
def hp(im, s=9, g=6):
    L = im.convert('L'); a = np.asarray(L).astype(float); b = np.asarray(L.filter(ImageFilter.GaussianBlur(s))).astype(float)
    return Image.fromarray(np.clip(128 + (a - b) * g, 0, 255).astype(np.uint8)).convert('RGB')
cols = []
for t in ('F2', 'F3'):
    col = []
    for v in HV:
        im = Image.open(W3 + 'renders/proof3hp/' + f'{t}_' + v.replace(':', '_') + '.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
        col.append((im, hp(im)))
    cols.append(col)
w, hh = cols[0][0][0].size
sh = Image.new('RGB', (w * 4, hh * 4 + 40), (20, 20, 22)); d = ImageDraw.Draw(sh)
for k, lab in enumerate(('F2 shaded', 'F2 high-pass (x6)', 'F3 shaded', 'F3 high-pass (x6)')): d.text((k * w + 10, 8), lab, fill=(255, 255, 255), font=font)
for vi in range(4):
    for ci in range(2):
        sh.paste(cols[ci][vi][0], ((ci * 2) * w, 40 + vi * hh)); sh.paste(cols[ci][vi][1], ((ci * 2 + 1) * w, 40 + vi * hh))
sh.save(P + 'F3_highpass_shading_F2_vs_F3.png'); print('2', sh.size)
# ------------------------------------------------------------------------------------------------ 3. lips close-ups (front + profile)
env = dict(os.environ)
for mode, out in (('front', 'F3_lips_front_plate_F2_F3.png'), ('profile', 'F3_lips_profile_plate_F2_F3.png')):
    env['LIPS_VIEW'] = mode
    subprocess.run(['python3', W3 + 'tools/lips_cmp.py', P + out, 'F2=start/F2_STAGED.blend', 'F3=export/HeroBase_Female_MicroF3_head_STAGED.blend'], check=True, capture_output=True, env=env)
print('3 lips')
# ------------------------------------------------------------------------------------------------ 4. BA sheet (plate | F2 | F3)
FV = 'front,q3L,q3R,left'
render(F2B, W3 + 'renders/proof3ba/', FV, 'F2', 'old'); render(F3B, W3 + 'renders/proof3ba/', FV, 'F3', 'new')
env = dict(os.environ); env['LABELS'] = 'PLATE|F2 (delivered earlier)|F3 (smoother jaw + fuller, more visible lips)'
subprocess.run(['python3', W3 + 'tools/ba_sheet.py', W3 + 'renders/proof3ba', W3 + 'renders/proof3ba', P + 'F3_lowerface_BA_plate_F2_F3.png', 'F2', 'F3'], check=True, capture_output=True, env=env)
print('4 BA')
