"""Plate | model side-by-side at identical cameras (F3's calibrated panels).  ./py.sh tools/compare_plate.py <tag> <out.png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
tag, out = sys.argv[1], sys.argv[2]
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
plate = Image.open(f'{ROOT}/ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PANEL = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'q3L': (85, 385, 430, 656)}
def font(sz):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Supplemental/Arial.ttf'):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F = font(26)
rows = []
for v in ('front', 'left', 'q3L'):
    x0, y0, x1, y1 = PANEL[v]; pc = plate.crop((x0, y0, x1, y1)); w, h = pc.size
    pc = pc.resize((w * 3, h * 3), Image.LANCZOS)
    bg = tuple(int(c) for c in np.asarray(plate.crop((x0, y0, x0 + 12, y0 + 12))).reshape(-1, 3).mean(0))
    m = Image.open(f'color/raw/{tag}_{v}.png').convert('RGBA'); base = Image.new('RGBA', m.size, bg + (255,)); m = Image.alpha_composite(base, m).convert('RGB')
    assert m.size == pc.size, (m.size, pc.size)
    rows.append((v, pc, m))
W = rows[0][1].width * 2 + 30; H = sum(r[1].height + 44 for r in rows) + 60
sheet = Image.new('RGB', (W, H), (24, 24, 28)); d = ImageDraw.Draw(sheet)
d.text((16, 12), 'FEMALE colour pass: plate (left)  vs  model, same camera, Unity-like rig (right)', font=font(30), fill=(235, 235, 235))
y = 60
for v, pc, m in rows:
    d.text((16, y + 6), f'{v}: plate', font=F, fill=(255, 200, 120)); d.text((pc.width + 46, y + 6), f'{v}: model (colored)', font=F, fill=(255, 200, 120)); y += 44
    sheet.paste(pc, (10, y)); sheet.paste(m, (pc.width + 30, y)); y += pc.height
sheet.save(out); print('saved', out, sheet.size)
