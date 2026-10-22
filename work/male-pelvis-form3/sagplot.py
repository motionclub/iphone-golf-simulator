"""Sagittal (y-z) sections of the mesh at given |x| columns, for several tags.  python3 sagplot.py out.png "tag1,tag2" "x1,x2,.." [ylo yhi zlo zhi]
(numpy+PIL only; draws every section segment, polyline)"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
import common
from common import F, V0
def sections(V, x):
    """segments (y,z)-(y,z) of the plane X=x"""
    out = []
    for f in F:
        xx = V[list(f), 0]
        if xx.min() > x or xx.max() < x: continue
        pts = []
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]; xa, xb = V[a, 0], V[b, 0]
            if (xa - x) * (xb - x) < 0:
                t = (x - xa) / (xb - xa); p = V[a] + t * (V[b] - V[a]); pts.append((p[1], p[2]))
        if len(pts) == 2: out.append(pts)
    return out
def plot(out, tags, xs, box=(-0.21, 0.13, 0.68, 0.90), sc=2600):
    ylo, yhi, zlo, zhi = box; w = int((yhi - ylo) * sc); h = int((zhi - zlo) * sc)
    cols = [(90, 170, 255), (90, 255, 140), (255, 190, 60), (255, 90, 90), (230, 120, 255), (160, 160, 160)]
    ims = []
    for x in xs:
        im = Image.new('RGB', (w, h + 22), (20, 20, 26)); d = ImageDraw.Draw(im)
        for zz in np.arange(np.ceil(zlo * 100) / 100, zhi, 0.01):
            yy = h - (zz - zlo) * sc; d.line([(0, yy), (w, yy)], fill=(45, 45, 56)); d.text((2, yy - 11), f'{zz:.2f}', fill=(120, 120, 140))
        for yy_ in np.arange(np.ceil(ylo * 20) / 20, yhi, 0.05):
            xx = (yy_ - ylo) * sc; d.line([(xx, 0), (xx, h)], fill=(45, 45, 56)); d.text((xx + 2, h - 10), f'{int(round(yy_ * 1000))}', fill=(120, 120, 140))
        for ti, t in enumerate(tags):
            V = V0 if t == 'start' else np.load(f'data/V_{t}.npy')
            for (p, q) in sections(V, x):
                d.line([((p[0] - ylo) * sc, h - (p[1] - zlo) * sc), ((q[0] - ylo) * sc, h - (q[1] - zlo) * sc)], fill=cols[ti % len(cols)], width=2)
            d.text((w - 150, 6 + 14 * ti), t, fill=cols[ti % len(cols)])
        d.text((6, h + 4), f'x = {x*1000:.1f} mm  (front y<0 left, rear y>0 right)', fill=(255, 200, 80)); ims.append(im)
    S = Image.new('RGB', (w, sum(i.height + 4 for i in ims)), (10, 10, 10)); y = 0
    for i in ims: S.paste(i, (0, y)); y += i.height + 4
    S.save(out); print(out, S.size)
if __name__ == '__main__':
    a = sys.argv[1:]; tags = a[1].split(','); xs = [float(v) for v in a[2].split(',')]
    box = tuple(float(v) for v in a[3:7]) if len(a) >= 7 else (-0.21, 0.13, 0.68, 0.90)
    plot(a[0], tags, xs, box)
