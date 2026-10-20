"""plate-region zoom vs model render at identical framing (front panel).   python3.13 zoomcmp.py <blend> <out.png> [x0 y0 x1 y1 scale] [panel=front]"""
import sys, subprocess, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import fl
blend, out = sys.argv[1], sys.argv[2]
vals = [float(v) for v in sys.argv[3:8]] if len(sys.argv) >= 8 else [175, 60, 345, 270, 6.0]
x0, y0, x1, y1, S = vals
panel = sys.argv[8] if len(sys.argv) > 8 else 'front'
cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
w, h = x1 - x0, y1 - y0
side = int(round(max(w, h) * S)); scsq = max(w, h) * fl.K
if panel == 'front':
    tx, ty, az = float(fl.xcol(cxp)), 0.0, 0.0
else:
    tx, ty, az = 0.0, float(fl.ycolL(cxp)), 90.0
tz = float(fl.zrow(cyp))
view = f'c:{az:.1f}:0.0:{tx:.5f}:{ty:.5f}:{tz:.5f}:{scsq:.6f}:{side}'
tag = 'zc'
subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', str(fl.W / 'ul.py'), '--', blend, str(fl.W / 'renders'), view, tag], check=True, capture_output=True)
rp = fl.W / 'renders' / (f'{tag}_' + view.replace(':', '_') + '.png')
r = Image.open(rp).convert('RGBA')
# render covers a square of side `side`; the plate region is w x h centred in it
cx0 = (side - int(w * S)) // 2; cy0 = (side - int(h * S)) // 2
r = r.crop((cx0, cy0, cx0 + int(w * S), cy0 + int(h * S)))
bg = Image.new('RGBA', r.size, (60, 60, 64, 255)); bg.alpha_composite(r); r = bg.convert('RGB')
pl = Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB').crop((int(x0), int(y0), int(x1), int(y1))).resize(r.size, Image.LANCZOS)
ov = Image.blend(pl, r, 0.5)
Wd = r.width
S3 = Image.new('RGB', (Wd * 3, r.height)); S3.paste(pl, (0, 0)); S3.paste(r, (Wd, 0)); S3.paste(ov, (2 * Wd, 0))
d = ImageDraw.Draw(S3)
f = ImageFont.load_default()
for gx in range(int(x0 // 10 + 1) * 10, int(x1), 10):
    X = (gx - x0) * S
    for k in range(3): d.line([(X + k * Wd, 0), (X + k * Wd, 10 if gx % 50 else 24)], fill=(0, 120, 255), width=1)
    if gx % 50 == 0: d.text((X + 2, 12), str(gx), fill=(0, 90, 220), font=f)
for gy in range(int(y0 // 10 + 1) * 10, int(y1), 10):
    Y = (gy - y0) * S
    for k in range(3): d.line([(k * Wd, Y), (k * Wd + (10 if gy % 50 else 24), Y)], fill=(255, 60, 60), width=1)
    if gy % 50 == 0: d.text((2, Y + 2), str(gy), fill=(220, 0, 0), font=f)
S3.save(out); print('saved', out, S3.size)
