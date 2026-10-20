"""Plate | mesh | overlay(+silhouette edge) sheet, absolute alignment (no bbox shifting).  system python3 + Pillow.
usage: python3 compose.py <tag> [out.png] [panels=front,left,q3L,q3R]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = R / 'work/male-micro1h'
tag = sys.argv[1]
out = Path(sys.argv[2]) if len(sys.argv) > 2 else W / f'r/{tag}/sheet.png'
names = sys.argv[3].split(',') if len(sys.argv) > 3 else ['front', 'left', 'q3L', 'q3R']
BOX = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
plate = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
f = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
BG = (56, 56, 60)
rows = []
for n in names:
    p = plate.crop(BOX[n]); p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
    m = Image.open(W / f'r/{tag}/{n}.png').convert('RGBA').resize(p.size, Image.LANCZOS)
    bg = Image.new('RGBA', p.size, BG + (255,)); mm = Image.alpha_composite(bg, m).convert('RGB')
    # overlay: 50% blend of plate and mesh (mesh only where alpha), plus red silhouette edge of the mesh on the plate
    a = m.split()[3].point(lambda v: 255 if v > 127 else 0)
    edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)), a.filter(ImageFilter.MinFilter(3)))
    ov = Image.composite(Image.blend(p, mm, 0.5), p, a)
    ov2 = ov.copy(); ov2.paste((255, 40, 40), mask=edge)
    row = Image.new('RGB', (p.width * 3 + 20, p.height), (0, 0, 0))
    for i, t in enumerate((p, mm, ov2)): row.paste(t, (i * (p.width + 10), 0))
    d = ImageDraw.Draw(row); d.rectangle((0, 0, 120, 26), fill=(14, 14, 18)); d.text((8, 4), n, font=f(18), fill=(240, 240, 240))
    rows.append(row)
Wd = max(r.width for r in rows); H = sum(r.height for r in rows) + 50
S = Image.new('RGB', (Wd, H), (30, 31, 35)); d = ImageDraw.Draw(S)
d.text((12, 10), f'{tag} · plate | mesh | overlay + silhouette edge (absolute alignment)', font=f(24), fill=(240, 240, 240))
y = 44
for r in rows: S.paste(r, (0, y)); y += r.height
S = S.resize((S.width // 2, S.height // 2), Image.LANCZOS)
S.save(out); print(out, S.size)
