"""bp5.py: band-pass shading maps (plate vs models) at a chosen scale with the calibrated light gain.  python3 tools/bp5.py out.png [--s 1.6,9] [--gain 2.5] [--vmax 40] [--view front|back] [--box x0,x1,z0,z1] tag=coords.npy ..."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import photo3 as ph
from bpmap4 import to_img

def run(out, items, view='front', box_m=(-0.15, 0.15, 1.08, 1.34), s1=1.6, s2=9.0, vmax=40.0, gain=2.5, scale=4):
    box = ph.roi_box(view, *box_m)
    pb = ph.plate_bp(view, box, s1, s2)
    cols = [('PLATE', to_img(pb, vmax, scale))]
    L = np.array(ph.LIGHT, dtype=float).copy()
    L[1:] *= gain
    for tag, path in items:
        co = np.load(path).astype(np.float64)
        mb, mask, img = ph.model_bp(co, view, box, s1, s2, light=L)
        cols.append((tag, to_img(mb, vmax, scale)))
    W = sum(c[1].width for c in cols); H = cols[0][1].height
    im = Image.new('RGB', (W, H + 20), (255, 255, 255)); d = ImageDraw.Draw(im); x = 0
    for t, c in cols:
        im.paste(c, (x, 20)); d.text((x + 4, 4), t + f' s=({s1},{s2}) gain {gain}  red=brighter, blue=darker (+-{vmax:.0f})', fill=(0, 0, 0)); x += c.width
    im.save(out); print(out, im.size)

if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[0]; a = a[1:]
    kw = {}
    while a and a[0].startswith('--'):
        k = a[0]
        if k == '--s': s = a[1].split(','); kw['s1'], kw['s2'] = float(s[0]), float(s[1])
        elif k == '--gain': kw['gain'] = float(a[1])
        elif k == '--vmax': kw['vmax'] = float(a[1])
        elif k == '--view': kw['view'] = a[1]
        elif k == '--box': kw['box_m'] = tuple(float(v) for v in a[1].split(','))
        a = a[2:]
    run(out, [x.split('=', 1) for x in a], **kw)
