"""Band-pass maps (plate | tagA | tagB ...) in the main FRONT view groin box.  python3 diffmap_front.py out.png s1 s2 tag..."""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
import metric as MT
from metric import dog, zrow, xcol
W = MT.W
PL = MT.PL
s1, s2 = float(sys.argv[2]), float(sys.argv[3]); tags = sys.argv[4:]
x0, x1 = int(xcol('bald_front', -0.17)), int(xcol('bald_front', 0.17)); y0, y1 = int(zrow('bald_front', 0.95)), int(zrow('bald_front', 0.72))
def col(v, lim):
    t = np.clip(v / lim, -1, 1); r = np.where(t > 0, 255 * t, 0); b = np.where(t < 0, 255 * -t, 0); g = 255 * (1 - np.abs(t)) * 0.35
    return np.stack([r + 40, g + 40, b + 40], -1).clip(0, 255).astype(np.uint8)
A = dog(PL, s1, s2)[y0:y1, x0:x1]; lim = 2.2 * A.std()
panels = [('PLATE', A)]
for t in tags:
    MT.render(t); m = np.asarray(Image.open(W / f'r/{t}_m/front.png').convert('L')).astype('float32'); panels.append((t, dog(m, s1, s2)[y0:y1, x0:x1]))
S = 4; ims = [Image.fromarray(col(p, lim)).resize(((x1 - x0) * S, (y1 - y0) * S), Image.NEAREST) for _, p in panels]
Wd = sum(i.width for i in ims) + 10 * (len(ims) + 1); Hd = ims[0].height + 30
out = Image.new('RGB', (Wd, Hd), (16, 16, 16)); d = ImageDraw.Draw(out); F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18); x = 10
for (nm, p), im in zip(panels, ims):
    out.paste(im, (x, 26)); d.text((x + 4, 4), nm + ('' if nm == 'PLATE' else '  r=%.2f' % np.corrcoef(A.ravel(), p.ravel())[0, 1]), fill=(255, 200, 80), font=F); x += im.width + 10
out.save(sys.argv[1]); print(sys.argv[1], out.size)
