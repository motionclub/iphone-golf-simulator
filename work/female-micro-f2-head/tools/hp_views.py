"""render variants (npz or blend) with ul.py at lower-face close-up views and build a high-pass sheet (rows = views, cols = variants).
python3 hp_views.py <out.png> <name=src> [name=src ...]    (src: .npz or .blend)"""
import sys, subprocess, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/'
B = '/Applications/Blender.app/Contents/MacOS/Blender'
out = sys.argv[1]; items = [a.split('=', 1) for a in sys.argv[2:]]
VIEWS = ['c:0:0:0:-0.06:1.46:0.17:700', 'c:35:0:-0.01:-0.06:1.46:0.17:700', 'c:-35:0:0.01:-0.06:1.46:0.17:700', 'c:90:0:0:-0.05:1.46:0.17:700']
os.makedirs(ROOT + 'renders/hp', exist_ok=True)
def hp(img, s=9, g=6):
    L = img.convert('L'); a = np.asarray(L).astype(float); b = np.asarray(L.filter(ImageFilter.GaussianBlur(s))).astype(float)
    return Image.fromarray(np.clip(128 + (a - b) * g, 0, 255).astype(np.uint8)).convert('RGB')
cols = []
for name, src in items:
    subprocess.run([B, '-b', '--factory-startup', '--python', ROOT + 'tools/ul.py', '--', ROOT + src if not src.startswith('/') else src, ROOT + 'renders/hp', ','.join(VIEWS), name], check=True, capture_output=True)
    col = []
    for v in VIEWS:
        p = ROOT + 'renders/hp/' + f'{name}_' + v.replace(':', '_') + '.png'
        im = Image.open(p).convert('RGBA'); bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
        col.append((im, hp(im)))
    cols.append((name, col))
w, h = cols[0][1][0][0].size
sheet = Image.new('RGB', (w * len(cols) * 2, h * len(VIEWS)), (20, 20, 22))
for ci, (name, col) in enumerate(cols):
    for vi, (im, hh) in enumerate(col):
        sheet.paste(im, ((ci * 2) * w, vi * h)); sheet.paste(hh, ((ci * 2 + 1) * w, vi * h))
    ImageDraw.Draw(sheet).text((ci * 2 * w + 8, 6), name, fill=(255, 255, 0))
sheet.save(out); print(sheet.size)
