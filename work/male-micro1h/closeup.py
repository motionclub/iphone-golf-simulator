"""Plate crop vs mesh close-up at identical framing (absolute).  python3 closeup.py <tag> [views=front,q3L,q3R,side] [zc=1.55] [scale=0.16] [out]
Mesh renders must be 'face_<view>.png' made with target (0,-0.1,zc) and the matching az (front 0, q3L 32.5, q3R 30, side 90)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-micro1h'
import math
K = 0.0013043874429196725; TOP = 1.7046599388122559
tag = sys.argv[1]
import os
PREFIX = os.environ.get('PFX', 'face')
YT = float(os.environ.get('YT', '-0.1'))
views = sys.argv[2].split(',') if len(sys.argv) > 2 else ['front', 'q3L', 'q3R', 'side']
zc = float(sys.argv[3]) if len(sys.argv) > 3 else 1.55
sc = float(sys.argv[4]) if len(sys.argv) > 4 else 0.16
out = Path(sys.argv[5]) if len(sys.argv) > 5 else W / f'r/{tag}/face_cmp.png'
plate = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
n = sc / K          # plate px across the crop
def crop_center(view):
    row = 76 + (TOP - zc) / K
    if view == 'front':
        return 227.6 + (0.0 - 0.0) / K, row                      # target x=0 -> face centre col
    if view == 'side':
        return 712 - (0.065 - YT) / K, row
    psi = math.radians(32.5 if view == 'q3L' else 30.0)
    cx = 219.0 if view == 'q3L' else (433 + 834) / 2
    row = 397 + (TOP - zc) / K
    return cx + ((YT * math.sin(psi)) - (-0.040 * math.sin(psi))) / K, row
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
S = 520
sheet = Image.new('RGB', (S * 2 * len(views) // 2 + 0, 1), (0, 0, 0))
cells = []
for v in views:
    cx, cy = crop_center(v)
    pc = plate.crop((int(round(cx - n / 2)), int(round(cy - n / 2)), int(round(cx + n / 2)), int(round(cy + n / 2)))).resize((S, S), Image.LANCZOS)
    m = Image.open(W / f'r/{tag}/{PREFIX}_{v}.png').convert('RGBA').resize((S, S), Image.LANCZOS)
    bg = Image.new('RGBA', (S, S), (56, 56, 60, 255)); mm = Image.alpha_composite(bg, m).convert('RGB')
    cells.append((v, pc, mm))
ncol = 2
rows = (len(cells) + 1) // 2
Wd = ncol * (2 * S + 10) + 10
Sh = Image.new('RGB', (Wd, rows * (S + 8) + 36), (30, 31, 35)); d = ImageDraw.Draw(Sh)
d.text((10, 6), f'{tag} · close-up plate | mesh (absolute framing, zc={zc}, scale={sc})', font=f(22), fill=(240, 240, 240))
for i, (v, pc, mm) in enumerate(cells):
    r, c = divmod(i, ncol)
    x0 = 10 + c * (2 * S + 10); y0 = 36 + r * (S + 8)
    Sh.paste(pc, (x0, y0)); Sh.paste(mm, (x0 + S + 4, y0))
    d.rectangle((x0, y0, x0 + 90, y0 + 22), fill=(14, 14, 18)); d.text((x0 + 6, y0 + 2), v, font=f(16), fill=(240, 240, 240))
Sh = Sh.resize((Sh.width * 3 // 4, Sh.height * 3 // 4), Image.LANCZOS)
Sh.save(out); print(out, Sh.size)
