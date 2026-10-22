"""proof/03_unity_f.png : Unity captures of the female head at the plate angles (plate | Unity), then the arm's-length and close-up captures.
python3.13 proof03.py <unity_dir> <out.png>"""
import sys, os, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from PIL import Image, ImageDraw, ImageFont
import fl
udir, out = sys.argv[1], sys.argv[2]
FL = fl.PLATES / 'face_lock_f'
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
except Exception: font = ImageFont.load_default()
PAIRS = [('head_front', '01_front_face.png'), ('head_left', '02_left_profile.png'), ('head_right', '03_right_profile.png'), ('head_q3L', '04_threequarter_front_left.png'),
         ('head_q3R', '05_threequarter_front_right.png'), ('head_top', '06_top_cranial.png'), ('head_back', '08_body_back_head.png')]
CLOSE = ['face_front', 'face_q3', 'face_profile', 'eye_front', 'eye_q3', 'mouth_front', 'ear_side', 'ear_back']
H = 420
def fit(im, h):
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
pairs = []
for u, p in PAIRS:
    up = fit(Image.open(os.path.join(udir, u + '.png')).convert('RGB'), H); pl = fit(Image.open(FL / p).convert('RGB'), H)
    row = Image.new('RGB', (pl.width + up.width + 6, H), (20, 20, 22)); row.paste(pl, (0, 0)); row.paste(up, (pl.width + 6, 0))
    d = ImageDraw.Draw(row); d.rectangle([0, 0, 420, 28], fill=(0, 0, 0)); d.text((6, 3), f'{p[:-4]}   |   Unity {u}', fill=(255, 255, 255), font=font)
    pairs.append(row)
cl = [fit(Image.open(os.path.join(udir, c + '.png')).convert('RGB'), 360) for c in CLOSE]
for im, c in zip(cl, CLOSE): ImageDraw.Draw(im).text((6, 3), c, fill=(255, 255, 255), font=font)
W2 = max(r.width for r in pairs)
colw = W2 * 2 + 12
rows = [pairs[i:i + 2] for i in range(0, len(pairs), 2)]
parts = []
for r in rows:
    im = Image.new('RGB', (colw, H), (20, 20, 22)); x = 0
    for p in r: im.paste(p, (x, 0)); x += W2 + 12
    parts.append(im)
# close-up grid
cw = max(c.width for c in cl); per = max(1, colw // (cw + 8))
grid_rows = [cl[i:i + per] for i in range(0, len(cl), per)]
for r in grid_rows:
    im = Image.new('RGB', (colw, 360), (20, 20, 22)); x = 0
    for c in r: im.paste(c, (x, 0)); x += cw + 8
    parts.append(im)
Hh = sum(p.height for p in parts) + 8 * len(parts) + 44
S = Image.new('RGB', (colw, Hh), (20, 20, 22)); d = ImageDraw.Draw(S)
d.text((10, 10), 'FEMALE HEAD MicroF1 - Unity 6000.3.24f1 (URP Lit, studio rig) vs face_lock_f plates;  lower rows: arm\'s-length / close-up captures', fill=(255, 255, 255), font=font)
y = 44
for p in parts: S.paste(p, (0, y)); y += p.height + 8
S.save(out); print('saved', out, S.size)
