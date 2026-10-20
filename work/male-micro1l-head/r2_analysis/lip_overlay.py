"""Overlay candidate lip curves (mm) on the plate mouth crop.  python3.13 lip_overlay.py <curves.json> <out.png> [raw]
curves.json: {"seam":[[x,z],...], "up":[[x,z],...], "lo":[[x,z],...], "seam_t":[[x,t],...]}  (right half; mirrored)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_lib import *
from PIL import ImageDraw, ImageFont
F = lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', s)
up = 10; zlo, zhi = 1.486, 1.526; xm = 44
r0 = int(rowz(zhi)); r1 = int(rowz(zlo)); c0 = int(CX - xm / 1000 / K); c1 = int(CX + xm / 1000 / K)
C = json.load(open(sys.argv[1])); out = sys.argv[2]; raw = len(sys.argv) > 3
a = np.asarray(PLATE.crop((c0, r0, c1, r1))).astype(float)
im = Image.fromarray(np.clip((a - a.mean(axis=(0, 1))) * (1.0 if raw else 1.6) + a.mean(axis=(0, 1)), 0, 255).astype(np.uint8)).resize(((c1 - c0) * up, (r1 - r0) * up), Image.BICUBIC)
d = ImageDraw.Draw(im); X = lambda x: (CX + x / 1000 / K - c0) * up; Z = lambda z: (rowz(z / 1000) - r0) * up
for x in range(-40, 41, 10): d.line((X(x), 0, X(x), im.height), fill=(0, 255, 255) if x % 20 == 0 else (0, 140, 140), width=1); d.text((X(x) + 3, 2), f'{x}', font=F(16), fill=(0, 255, 255))
for z in range(1490, 1526, 5): d.line((0, Z(z), im.width, Z(z)), fill=(255, 255, 0), width=1); d.text((3, Z(z) - 16), f'{z}', font=F(16), fill=(255, 255, 0))
col = dict(seam=(255, 40, 40), up=(60, 255, 60), lo=(255, 120, 255))
for key in ('seam', 'up', 'lo'):
    pts = np.array(C[key], float); xs = np.linspace(0, pts[-1, 0], 80); zs = np.interp(xs, pts[:, 0], pts[:, 1])
    for sgn in (1, -1):
        d.line([(X(sgn * x), Z(z)) for x, z in zip(xs, zs)], fill=col[key], width=2)
im.save(out); print(out, im.size)
