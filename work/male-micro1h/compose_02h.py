"""02_match_m_head.png: six head-detail panels, plate | mesh (Eevee, alpha) | 50% overlay with silhouette edge.
python3 compose_02h.py <panels_dir> <out.png> [title]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
pdir = Path(sys.argv[1]); out = Path(sys.argv[2]); title = sys.argv[3] if len(sys.argv) > 3 else 'Micro1h male head'
plate = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
BOX = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'right': (834, 62, 1271, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668), 'top': (834, 390, 1272, 668)}
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
BG = (56, 56, 60)


def align_top(pl, m):
    """top view: scale the head-only mesh render so ear-to-ear width matches the plate, align centres and the back edge"""
    px = pl.load(); W, H = pl.size
    xs = []; ys = []
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            r, g, b = px[x, y]
            if r - b > 30 and r > 120 and r - g > 10: xs.append(x); ys.append(y)
    a = np.array(m.split()[3]) > 127
    cols = np.where(a.any(axis=0))[0]; rows = np.where(a.any(axis=1))[0]
    Wp = max(xs) - min(xs) + 1; Wm = cols[-1] - cols[0] + 1
    s = Wp / Wm
    mm = m.resize((int(m.width * s), int(m.height * s)), Image.LANCZOS)
    dx = int(round((min(xs) + max(xs)) / 2 - (cols[0] + cols[-1]) / 2 * s)); dy = int(round(min(ys) - rows[0] * s))
    outm = Image.new('RGBA', pl.size, (0, 0, 0, 0)); outm.paste(mm, (dx, dy), mm)
    return outm


rows = []
for n, box in BOX.items():
    p = plate.crop(box); p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
    m = Image.open(pdir / f'{n}.png').convert('RGBA')
    if n == 'top':
        m = align_top(p, m)
    else:
        m = m.resize(p.size, Image.LANCZOS)
    bg = Image.new('RGBA', p.size, BG + (255,)); mm_ = Image.alpha_composite(bg, m).convert('RGB')
    a = m.split()[3].point(lambda v: 255 if v > 127 else 0)
    edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)), a.filter(ImageFilter.MinFilter(3)))
    ov = Image.composite(Image.blend(p, mm_, 0.5), p, a); ov.paste((255, 40, 40), mask=edge)
    row = Image.new('RGB', (p.width * 3 + 20, p.height), (0, 0, 0))
    for i, t in enumerate((p, mm_, ov)): row.paste(t, (i * (p.width + 10), 0))
    d = ImageDraw.Draw(row); d.rectangle((0, 0, 190, 30), fill=(14, 14, 18)); d.text((8, 5), {'front': '01 front', 'left': '02 left profile', 'right': '03 right profile', 'q3L': '04 3/4 front left', 'q3R': '05 3/4 front right', 'top': '06 top (approx. fit)'}[n], font=f(20), fill=(240, 240, 240))
    rows.append(row)
Wd = max(r.width for r in rows); Ht = sum(r.height for r in rows) + 60
S = Image.new('RGB', (Wd, Ht), (30, 31, 35)); d = ImageDraw.Draw(S)
d.text((16, 14), f'{title} · plate | mesh (Blender Eevee, plate-aligned) | 50% overlay + red silhouette edge', font=f(30), fill=(240, 240, 240))
y = 60
for r in rows: S.paste(r, (0, y)); y += r.height
S = S.resize((S.width // 2, S.height // 2), Image.LANCZOS); S.save(out); print(out, S.size)
