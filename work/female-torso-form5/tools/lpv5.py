"""lpv5.py: general vertical luminance profiles, plate vs models, for view front|back.
python3 tools/lpv5.py out.png --view back --gain 2.0 --zr 0.66,1.0 --xs 0.03,0.06,0.09,0.12 tag=coords.npy ...
(column x is in MODEL coordinates; for the back view +x appears on the viewer's LEFT.)  Curves are shown relative to their own value at the bottom of the z-range."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import photo3 as ph
from fplate import BALD, S, FRONT_CX, BACK_CX, SOLE

def run(out, items, view, gain, zr, xs, ysc=4.0):
    L = np.array(ph.LIGHT, dtype=float).copy(); L[1:] *= gain
    cx = FRONT_CX if view == 'front' else BACK_CX
    sg = 1.0 if view == 'front' else -1.0
    box = ph.roi_box(view, -0.20, 0.20, zr[0] - 0.03, zr[1] + 0.03)
    c0, r0, c1, r1 = box
    zs = np.arange(zr[0], zr[1], 0.002)
    imgs = []
    for tag, path in items:
        co = np.load(path).astype(np.float64)
        N = ph.vertex_normals(co, ph.TRI)
        sh = ph.shade_vertices(co, N, view, L)
        img, mask = ph.raster_shaded(co, sh, view, box)
        imgs.append((tag, img))
    cols = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e']
    W, H = 460, 330
    im = Image.new('RGB', (W * len(xs), H), (255, 255, 255)); d = ImageDraw.Draw(im)
    for k, x in enumerate(xs):
        col = int(round(cx + sg * x / S))
        pp = np.array([BALD[int(round(SOLE - z / S)) - 1:int(round(SOLE - z / S)) + 2, col - 1:col + 2].mean() for z in zs])
        mp = [np.array([img[int(round(SOLE - z / S)) - r0 - 1:int(round(SOLE - z / S)) - r0 + 2, col - c0 - 1:col - c0 + 2].mean() for z in zs]) for _, img in imgs]
        ox = k * W
        d.rectangle([ox + 5, 5, ox + W - 5, H - 5], outline=(150, 150, 150))
        d.text((ox + 10, 8), f'{view} x={x:+.3f} rel. to z={zr[0]:.2f} (black=plate)', fill=(0, 0, 0))
        def pl(v, color, w=2):
            r = v - v[:5].mean()
            pts = [(ox + 10 + (W - 20) * i / (len(zs) - 1), H / 2 - ysc * r[i]) for i in range(len(zs))]
            d.line(pts, fill=color, width=w)
        pl(pp, (0, 0, 0), 3)
        for v, c in zip(mp, cols):
            pl(v, c)
        for z in np.arange(zr[0], zr[1] + 0.001, 0.05):
            xx = ox + 10 + (W - 20) * (z - zr[0]) / (zs[-1] - zr[0]); d.line([(xx, H - 22), (xx, H - 12)], fill=(0, 0, 0)); d.text((xx - 12, H - 12), f'{z:.2f}', fill=(0, 0, 0))
    for i, (tag, _) in enumerate(imgs):
        d.text((8, 24 + 12 * i), tag, fill=ImageDraw.ImageColor.getrgb(cols[i % len(cols)]))
    im.save(out); print(out)

if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[0]; a = a[1:]
    view = 'back'; gain = 2.0; zr = (0.66, 1.0); xs = (0.03, 0.06, 0.09, 0.12)
    while a and a[0].startswith('--'):
        if a[0] == '--view': view = a[1]
        if a[0] == '--gain': gain = float(a[1])
        if a[0] == '--zr': zr = tuple(float(v) for v in a[1].split(','))
        if a[0] == '--xs': xs = tuple(float(v) for v in a[1].split(','))
        a = a[2:]
    run(out, [x.split('=', 1) for x in a], view, gain, zr, xs)
