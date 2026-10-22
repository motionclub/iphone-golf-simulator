# course_sheet.py <render_dir> <out_prefix>: one sheet per course, each hole = a render row over its target row,
# columns = that hole's reference views (refs/holes/hNN_<view>.jpg).
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd, prefix = sys.argv[1], sys.argv[2]
COURSES = {'cliffside': [7, 8, 9, 12, 15], 'wildisles': [13, 14, 17, 18, 19, 20], 'magma': [10, 16, 21, 22, 23]}
ORDER = ['tee', 'mid', 'approach', 'offL', 'offR', 'flyOpen', 'greenBack']
tw, th, lab = 360, 202, 22
try: f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
except Exception: f = ImageFont.load_default()
for course, holes in COURSES.items():
    rows = []
    for h in holes:
        views = [v for v in ORDER if os.path.exists(os.path.join(D, f'refs/holes/h{h:02d}_{v}.jpg'))]
        rows.append((h, views))
    cols = max(len(v) for _, v in rows)
    sheet = Image.new('RGB', (cols * tw, len(rows) * 2 * (th + lab)), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    for ri, (h, views) in enumerate(rows):
        for ci, v in enumerate(views):
            for k, (tag, p) in enumerate([('now', os.path.join(rd, f'h{h:02d}_{v}.jpg')), ('target', os.path.join(D, f'refs/holes/h{h:02d}_{v}.jpg'))]):
                x, y = ci * tw, (ri * 2 + k) * (th + lab)
                try: im = Image.open(p).convert('RGB'); im.thumbnail((tw, th)); sheet.paste(im, (x, y + lab))
                except Exception: d.text((x + 8, y + lab + 8), 'MISSING', fill=(255, 80, 80), font=f)
                d.text((x + 6, y + 3), f'h{h:02d} {v} {tag}', fill=(240, 240, 240) if tag == 'now' else (150, 200, 255), font=f)
    out = f'{prefix}_{course}.jpg'; sheet.save(out, quality=82); print(out, sheet.size)
