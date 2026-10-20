"""plate vs render mouth close-up (front).  python3 lips_cmp.py out.png name=src.blend|npz [name=src ...]   window 0.09 m wide centred on x=0, z=1.472"""
import sys, subprocess, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, fl
from PIL import Image, ImageDraw
W3 = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/'
B = '/Applications/Blender.app/Contents/MacOS/Blender'
out = sys.argv[1]; items = [a.split('=', 1) for a in sys.argv[2:]]
MODE = os.environ.get('LIPS_VIEW', 'front')
ZC, WIN, RES = 1.472, 0.07, 700
YC = -0.105
os.makedirs(W3 + 'renders/lips', exist_ok=True)
src = Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB')
r = float(fl.rowz(ZC)); h = (WIN / 2) / fl.K
if MODE == 'front':
    cx = fl.CXF
else:
    cx = 653 + (YC - fl.Y0) / fl.K            # left panel: plate column of world y
plate = src.crop((int(round(cx - h)), int(round(r - h)), int(round(cx + h)), int(round(r + h)))).resize((RES, RES), Image.LANCZOS)
cols = [('PLATE', plate)]
view = f'c:0:0:0:-0.06:{ZC}:{WIN}:{RES}' if MODE == 'front' else f'c:90:0:0:{YC}:{ZC}:{WIN}:{RES}'
for name, p in items:
    p_ = p if p.startswith('/') else W3 + p
    env = dict(os.environ)
    if name.startswith('F2'): env['FACE_PALETTE'] = 'old'
    subprocess.run([B, '-b', '--factory-startup', '--python', W3 + 'tools/ul.py', '--', p_, W3 + 'renders/lips', view, name], check=True, capture_output=True, env=env)
    im = Image.open(W3 + 'renders/lips/' + f'{name}_' + view.replace(':', '_') + '.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (224, 224, 226, 255)); bg.alpha_composite(im)
    cols.append((name, bg.convert('RGB')))
sh = Image.new('RGB', (RES * len(cols), RES + 30), (20, 20, 22)); d = ImageDraw.Draw(sh)
for k, (lab, im) in enumerate(cols):
    d.text((k * RES + 8, 8), lab, fill=(255, 255, 255)); sh.paste(im, (k * RES, 30))
sh.save(out); print(sh.size)
