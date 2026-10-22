"""montage.py out.png scale name1:dirA name2:dirB ... -- shot [shot...]  : rows = shots, columns = dirs, each at `scale` of 900x1600 (labels drawn)"""
import sys
from PIL import Image, ImageDraw
a = sys.argv[1:]; out = a[0]; sc = float(a[1]); i = a.index('--'); cols = [x.split(':', 1) for x in a[2:i]]; shots = a[i + 1:]
w, h = int(900 * sc), int(1600 * sc)
im = Image.new('RGB', (len(cols) * (w + 6), len(shots) * (h + 6)), (24, 24, 24)); d = ImageDraw.Draw(im)
for r, s in enumerate(shots):
    for c, (lab, dr) in enumerate(cols):
        t = Image.open('%s/%s.png' % (dr, s)).convert('RGB').resize((w, h), Image.LANCZOS)
        im.paste(t, (c * (w + 6), r * (h + 6))); d.text((c * (w + 6) + 6, r * (h + 6) + 6), lab + ' ' + s, fill=(255, 255, 0))
im.save(out)
