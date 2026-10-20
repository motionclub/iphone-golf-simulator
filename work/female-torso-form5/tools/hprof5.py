"""hprof5.py: horizontal luminance profiles (plate vs models; plate-fit light x gain) at several z rows of the front view.
python3 tools/hprof5.py out.png [--gain 2.5] [--zs 1.17,1.20,1.23,1.26,1.29] tag=coords.npy ...   (x from -0.15 to +0.15; +x = viewer right)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import photo3 as ph
from fplate import BALD, S, FRONT_CX, SOLE

def run(out, items, zs, gain=2.5, xr=0.15):
    L = np.array(ph.LIGHT, dtype=float).copy(); L[1:] *= gain
    box = ph.roi_box('front', -xr - 0.02, xr + 0.02, 1.10, 1.34)
    xs = np.arange(-xr, xr, 0.002)
    c0, r0, c1, r1 = box
    imgs = []
    for tag, path in items:
        co = np.load(path).astype(np.float64)
        N = ph.vertex_normals(co, ph.TRI)
        sh = ph.shade_vertices(co, N, 'front', L)
        img, mask = ph.raster_shaded(co, sh, 'front', box)
        imgs.append((tag, img))
    cols = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e']
    W, H = 760, 220
    im = Image.new('RGB', (W, H * len(zs)), (255, 255, 255)); d = ImageDraw.Draw(im)
    for k, z in enumerate(zs):
        oy = k * H
        row = int(round(SOLE - z / S))
        pp = np.array([BALD[row - 1:row + 2, int(round(FRONT_CX + x / S)) - 1:int(round(FRONT_CX + x / S)) + 2].mean() for x in xs])
        allp = [pp]
        for tag, img in imgs:
            allp.append(np.array([img[row - r0 - 1:row - r0 + 2, int(round(FRONT_CX + x / S)) - c0 - 1:int(round(FRONT_CX + x / S)) - c0 + 2].mean() for x in xs]))
        d.rectangle([5, oy + 5, W - 5, oy + H - 5], outline=(160, 160, 160))
        d.text((10, oy + 8), f'z={z:.2f}  (black=plate, absolute grey; models coloured)', fill=(0, 0, 0))
        lo, hi = 90, 250
        def pl(v, color, w=2):
            pts = [(10 + (W - 20) * i / (len(xs) - 1), oy + H - 12 - (H - 30) * (np.clip(v[i], lo, hi) - lo) / (hi - lo)) for i in range(len(xs))]
            d.line(pts, fill=color, width=w)
        pl(allp[0], (0, 0, 0), 3)
        for a, c in zip(allp[1:], cols):
            pl(a, c)
        for xt in (-0.1, -0.05, 0, 0.05, 0.1):
            xx = 10 + (W - 20) * (xt + xr) / (2 * xr); d.line([(xx, oy + H - 12), (xx, oy + H - 22)], fill=(0, 0, 0)); d.text((xx - 10, oy + H - 22), f'{xt:+.2f}', fill=(0, 0, 0))
    for i, (tag, _) in enumerate(imgs):
        d.text((W - 80, 8 + 12 * i), tag, fill=ImageDraw.ImageColor.getrgb(cols[i % len(cols)]))
    im.save(out); print(out)

if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[0]; a = a[1:]
    zs = (1.17, 1.20, 1.23, 1.26, 1.29); gain = 2.5
    while a and a[0].startswith('--'):
        if a[0] == '--gain': gain = float(a[1])
        if a[0] == '--zs': zs = tuple(float(v) for v in a[1].split(','))
        a = a[2:]
    run(out, [x.split('=', 1) for x in a], zs, gain)
