"""lprof5.py: vertical luminance profiles (plate vs models, plate-fit light x gain) at several x columns of the front view.
python3 tools/lprof5.py out.png [--gain 2.5] [--xs 0.03,0.06,0.085,0.11] tag=coords.npy ...
Plot: x axis z (m), y axis luminance (grey), plate in black; models in colour.  Also prints the z of the profile minimum (crescent) per column."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import photo3 as ph
from fplate import BALD, S, FRONT_CX, SOLE

def prof_plate(x, zs, hw=1):
    col = FRONT_CX + x / S
    out = []
    for z in zs:
        r = SOLE - z / S
        r0, c0 = int(round(r)), int(round(col))
        out.append(BALD[r0 - 1:r0 + 2, c0 - hw:c0 + hw + 1].mean())
    return np.array(out)

def run(out, items, xs, gain=2.5, zr=(1.10, 1.32)):
    L = np.array(ph.LIGHT, dtype=float).copy(); L[1:] *= gain
    box = ph.roi_box('front', -0.16, 0.16, zr[0] - 0.02, zr[1] + 0.02)
    zs = np.arange(zr[0], zr[1], 0.002)
    cols = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e']
    W, H = 440, 300
    im = Image.new('RGB', (W * len(xs), H), (255, 255, 255)); d = ImageDraw.Draw(im)
    res = {}
    imgs = []
    for tag, path in items:
        co = np.load(path).astype(np.float64)
        N = ph.vertex_normals(co, ph.TRI)
        sh = ph.shade_vertices(co, N, 'front', L)
        img, mask = ph.raster_shaded(co, sh, 'front', box)
        imgs.append((tag, img, mask))
    c0, r0, c1, r1 = box
    for k, x in enumerate(xs):
        pp = prof_plate(x, zs)
        allv = [pp]
        mp = []
        for tag, img, mask in imgs:
            col = int(round(FRONT_CX + x / S)) - c0
            v = []
            for z in zs:
                r = int(round(SOLE - z / S)) - r0
                v.append(img[r - 1:r + 2, col - 1:col + 2].mean())
            mp.append(np.array(v)); allv.append(mp[-1])
        lo = min(a.min() for a in allv); hi = max(a.max() for a in allv)
        # normalise each curve to its own value at z=1.11 for shape comparison
        ox = k * W
        d.rectangle([ox + 5, 5, ox + W - 5, H - 5], outline=(150, 150, 150))
        d.text((ox + 10, 8), f'x={x:+.3f}  (black plate, rel. to z=1.11)', fill=(0, 0, 0))
        def pl(v, color):
            v0 = v[:5].mean()
            r = v - v0
            pts = [(ox + 10 + (W - 20) * i / (len(zs) - 1), H / 2 - 4 * r[i]) for i in range(len(zs))]
            d.line(pts, fill=color, width=2)
            return zs[int(np.argmin(r[10:]))+10] if True else None
        zmin = {'plate': pl(pp, (0, 0, 0))}
        for (tag, _, _), v, c in zip(imgs, mp, cols):
            zmin[tag] = pl(v, c)
        for i, z in enumerate(np.arange(zr[0], zr[1] + 0.001, 0.04)):
            xx = ox + 10 + (W - 20) * (z - zr[0]) / (zs[-1] - zr[0]); d.line([(xx, H - 22), (xx, H - 12)], fill=(0, 0, 0)); d.text((xx - 12, H - 12), f'{z:.2f}', fill=(0, 0, 0))
        res[x] = {k2: round(float(v), 3) for k2, v in zmin.items()}
    for i, (tag, _, _) in enumerate(imgs):
        d.text((8, 24 + 12 * i), tag, fill=ImageDraw.ImageColor.getrgb(cols[i % len(cols)]))
    im.save(out); print(out); print('z of lowest luminance (crescent):'); [print(' ', x, r) for x, r in res.items()]

if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[0]; a = a[1:]
    xs = (0.03, 0.06, 0.085, 0.11); gain = 2.5
    while a and a[0].startswith('--'):
        if a[0] == '--gain': gain = float(a[1])
        if a[0] == '--xs': xs = tuple(float(v) for v in a[1].split(','))
        a = a[2:]
    run(out, [x.split('=', 1) for x in a], xs, gain)
