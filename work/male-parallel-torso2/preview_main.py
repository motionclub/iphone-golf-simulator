import sys; sys.path.insert(0, '.')
from relcorr import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
tag = sys.argv[1]; out = sys.argv[2]
def font(sz):
    for p in ('/System/Library/Fonts/Helvetica.ttc',):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F2_ = font(22)
def label(im, t):
    d = ImageDraw.Draw(im); w = d.textlength(t, font=F2_); d.rectangle((4, 4, 14 + w, 36), fill=(0, 0, 0)); d.text((10, 8), t, font=F2_, fill=(255, 255, 255)); return im
BOX = {'front': (225, 140, 485, 440), 'back': (790, 140, 1050, 440)}
def relief(im, k=5, s=14):
    g = np.asarray(im.convert('L')).astype('float32'); d = np.clip((g - blur(g, s)) * k + 128, 0, 255).astype('uint8'); return Image.fromarray(d).convert('RGB')
rows = []
for v in ('front', 'back'):
    box = BOX[v]; Z = 1.5
    ims = [PL.convert('RGB').crop(box), Image.open(f'r/base/{v}.png').convert('RGB').crop(box), Image.open(f'r/{tag}/{v}.png').convert('RGB').crop(box),
           relief(PL).crop(box), relief(Image.open(f'r/basec/{v}.png').convert('RGB')).crop(box), relief(Image.open(f'r/{tag}c/{v}.png').convert('RGB')).crop(box)]
    names = [f'{v} plate', 'PASS (before)', 'FORM2', 'plate relief', 'PASS relief', 'FORM2 relief']
    ims = [label(i.resize((int(i.width * Z), int(i.height * Z)), Image.LANCZOS), n) for i, n in zip(ims, names)]
    rows.append(ims)
Wd = sum(i.width for i in rows[0]) + 5 * 6; s = Image.new('RGB', (Wd, rows[0][0].height * 2 + 6))
for r, ims in enumerate(rows):
    x = 0
    for i in ims: s.paste(i, (x, r * (ims[0].height + 6))); x += i.width + 6
s.save(out); print(out, s.size)
