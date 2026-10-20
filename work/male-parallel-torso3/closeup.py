"""Close-up comparison: plate | mesh tags (Unity-like skin render + clay relief), region crops at high zoom.
PYTHONPATH=pylib python3.13 closeup.py <region> <out.png> <tag> [<tag> ...]   region: chest|mid|glute|torsoF|torsoB ; tags need r/<tag>/<view>.png (skin) and r/<tag>c/<view>.png (clay)"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
from relcorr import blur, PL as PLG, CAM
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
F2 = font(20)
def label(im, t, pos=(8, 6)):
    im = im.convert('RGB'); d = ImageDraw.Draw(im); w = d.textlength(t, font=F2); d.rectangle((pos[0] - 4, pos[1] - 3, pos[0] + w + 6, pos[1] + 24), fill=(0, 0, 0)); d.text(pos, t, font=F2, fill=(255, 255, 255)); return im
def relief(im, k=5, s=10):
    g = np.asarray(im.convert('L')).astype('float32'); d = np.clip((g - blur(g, s)) * k + 128, 0, 255).astype('uint8'); return Image.fromarray(d).convert('RGB')
REG = {'chest': ('front', 1.08, 1.36, 0.20), 'mid': ('front', 0.84, 1.20, 0.20), 'glute': ('back', 0.74, 1.04, 0.19), 'torsoF': ('front', 0.78, 1.38, 0.24), 'torsoB': ('back', 0.78, 1.38, 0.24), 'backup': ('back', 1.08, 1.38, 0.22)}
reg = sys.argv[1]; out = sys.argv[2]; tags = sys.argv[3:]; view, z0, z1, xh = REG[reg]
c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; box = (int(c['centre_x'] - xh / mpp), int(c['sole_y'] - z1 / mpp), int(c['centre_x'] + xh / mpp), int(c['sole_y'] - z0 / mpp))
PL = PLG.convert('RGB'); PLR = relief(PL)
Z = max(2, int(round(520 / (box[3] - box[1]))))
def crop(im): im = im.crop(box); return im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
cols = [label(crop(PL), f'plate {reg}'), label(crop(PLR), 'plate relief')]
for t in tags:
    sk = Image.open(f'r/{t}/{view}.png').convert('RGB'); cl = Image.open(f'r/{t}c/{view}.png').convert('RGB')
    cols.append(label(crop(sk), f'{t} skin')); cols.append(label(crop(relief(cl)), f'{t} clay relief'))
rows = [cols[i:i + 2] for i in range(0, len(cols), 2)]
W = max(sum(i.width for i in r) + 6 * (len(r) - 1) for r in rows); H = sum(r[0].height for r in rows) + 6 * (len(rows) - 1); s = Image.new('RGB', (W, H)); y = 0
for r in rows:
    x = 0
    for i in r: s.paste(i, (x, y)); x += i.width + 6
    y += r[0].height + 6
s.save(out); print(out, s.size)
