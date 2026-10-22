"""Sagittal sections near the groin: all section segments at several |x|, y from -0.22..0.12, z 0.70..0.95.  python3 frontplot.py out.png tag [xs]"""
import sys, os, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
import common
from common import section_x
out, tag = sys.argv[1], sys.argv[2]; XS = [float(v) for v in (sys.argv[3] if len(sys.argv) > 3 else '0.004,0.02,0.04,0.06,0.09').split(',')]
ylo, yhi, zlo, zhi = [float(v) for v in os.environ.get('BOX', '-0.22,0.12,0.70,0.95').split(',')]; S = float(os.environ.get('SC', 3000))
V = common.V0 if tag == 'start' else np.load(f'data/V_{tag}.npy')
Wd = int((yhi - ylo) * S) + 120; Hd = int((zhi - zlo) * S) + 60
im = Image.new('RGB', (Wd, Hd), (22, 22, 26)); d = ImageDraw.Draw(im); F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
X = lambda y: 60 + (y - ylo) * S; Y = lambda z: 30 + (zhi - z) * S
for z in np.arange(np.ceil(zlo * 50) / 50, zhi + 1e-9, 0.02): d.line([(55, Y(z)), (Wd - 10, Y(z))], fill=(50, 50, 70)); d.text((4, Y(z) - 8), f'{z:.2f}', fill=(130, 130, 170), font=F)
for y in np.arange(np.ceil(ylo * 50) / 50, yhi, 0.02): d.line([(X(y), 26), (X(y), Hd - 20)], fill=(44, 44, 62)); d.text((X(y) - 12, Hd - 18), f'{y*1000:.0f}', fill=(130, 130, 170), font=F)
PAL = [(110, 190, 255), (110, 255, 150), (255, 120, 120), (230, 120, 255), (255, 255, 120), (120, 255, 255)]
for xi, x in enumerate(XS):
    for (p, q) in section_x(V, x):
        if max(p[1], q[1]) < zlo or min(p[1], q[1]) > zhi: continue
        d.line([(X(p[0]), Y(p[1])), (X(q[0]), Y(q[1]))], fill=PAL[xi % len(PAL)], width=2)
    d.text((Wd - 90, 30 + 18 * xi), f'|x|={x*1000:.0f}', fill=PAL[xi % len(PAL)], font=F)
d.text((70, 8), 'FRONT (-y) <---------------------------> REAR (+y)', fill=(200, 200, 200), font=F)
im.save(out); print(out, im.size)
