"""python3 hv.py out.png side views scale center tag1 tag2 ...   -> stacked rows (one per tag) of hand views; tag 'base' = current ArtDir mesh"""
import sys, subprocess, os
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
sys.path.insert(0, W)
from sheetlib import font
out, side, views, scale, center = sys.argv[1:6]; tags = sys.argv[6:]
procs = [subprocess.Popen(['python3', W + '/rv2.py', t, side, views, scale, center], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for t in tags]
for p in procs: p.wait()
rows = []
for t in tags:
    im = Image.open(f'{W}/proof/it/{t}_zoom' + ('_wire' if os.environ.get('WIRE') else '') + f'_{side}.png').convert('RGB')
    d = ImageDraw.Draw(im); d.rectangle((0, 0, im.width, 30), fill=(15, 15, 17)); d.text((8, 5), f'{t}  - {side} hand', fill=(255, 230, 120), font=font(18)); rows.append(im)
S = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)))
y = 0
for r in rows: S.paste(r, (0, y)); y += r.height
fac = float(os.environ.get('FAC', '0.6')); S = S.resize((int(S.width * fac), int(S.height * fac)), Image.LANCZOS); S.save(out); print(out, S.size)
