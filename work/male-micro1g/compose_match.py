"""Plate vs mesh vs 50% overlay sheet for the six head-detail panels.  python3 compose_match.py <tag> [out.png]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1g')
ROOT = W.parents[1]
tag = sys.argv[1]
out = Path(sys.argv[2]) if len(sys.argv) > 2 else W / f'r/{tag}_match.png'
title = sys.argv[3] if len(sys.argv) > 3 else f'{tag} · plate | mesh | 50% overlay'
im = Image.open(ROOT / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
PANELS = {'01_front': (5, 62, 433, 352), '02_left': (433, 62, 834, 352), '03_right': (834, 62, 1271, 352),
          '04_q3L': (5, 390, 433, 668), '05_q3R': (433, 390, 834, 668), '06_top': (834, 390, 1272, 668)}
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
def bbox_head(img, mask_fn):
    px = img.load(); W_, H_ = img.size
    xs = []; ys = []
    for yy in range(0, H_, 2):
        for xx in range(0, W_, 2):
            if mask_fn(px[xx, yy]): xs.append(xx); ys.append(yy)
    if not ys: return None
    top = min(ys); limit = top + int(0.42 * (max(ys) - top + 1))
    hx = [x_ for x_, y_ in zip(xs, ys) if y_ <= limit]
    return top, (min(hx) + max(hx)) / 2


def align(plate, mesh):
    """shift the mesh render so its head bbox (top row, centre column of the upper 42%) matches the plate's"""
    sk = lambda p: (p[0] - p[1] > 8) and (p[1] - p[2] > 4) and p[0] > 55
    bg = mesh.getpixel((2, 2))
    mk = lambda p: abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 40
    a = bbox_head(plate, sk); b = bbox_head(mesh, mk)
    if a is None or b is None: return mesh
    dx = int(round(a[1] - b[1])); dy = int(round(a[0] - b[0]))
    out = Image.new('RGB', mesh.size, bg); out.paste(mesh, (dx, dy)); return out


rows = []
for name, box in PANELS.items():
    p = im.crop(box); p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
    m = Image.open(W / f'r/{tag}_{name}.png').convert('RGB').resize(p.size)
    if name == '03_right': m = m.transpose(Image.FLIP_LEFT_RIGHT)   # plate 03 also faces left
    m = align(p, m)
    ov = Image.blend(p, m, 0.5)
    row = Image.new('RGB', (p.width * 3 + 20, p.height), (0, 0, 0))
    for i, t in enumerate((p, m, ov)): row.paste(t, (i * (p.width + 10), 0))
    d = ImageDraw.Draw(row); d.rectangle((0, 0, 170, 30), fill=(14, 14, 18)); d.text((8, 6), name, font=f(20), fill=(240, 240, 240))
    rows.append(row)
Wd = max(r.width for r in rows); H = sum(r.height for r in rows) + 60
S = Image.new('RGB', (Wd, H), (30, 31, 35)); d = ImageDraw.Draw(S)
d.text((16, 14), title, font=f(30), fill=(240, 240, 240))
y = 60
for r in rows: S.paste(r, (0, y)); y += r.height
S = S.resize((S.width // 2, S.height // 2), Image.LANCZOS)
S.save(out); print(out, S.size)
