"""Axial (x-y) sections at given z for several tags, plan view (front y<0 at the BOTTOM of the image).
python3 axplot.py out.png "tag1,tag2" "z1,z2,.." [xlo xhi ylo yhi] [sc]"""
import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '.')
from common import F, V0, section_segments
def plot(out, tags, zs, box=(-0.13, 0.13, -0.22, 0.12), sc=2200):
    xlo, xhi, ylo, yhi = box; w = int((xhi - xlo) * sc); h = int((yhi - ylo) * sc)
    cols = [(90, 170, 255), (90, 255, 140), (255, 190, 60), (255, 90, 90), (230, 120, 255), (160, 160, 160)]
    ims = []
    for z in zs:
        im = Image.new('RGB', (w, h + 22), (20, 20, 26)); d = ImageDraw.Draw(im)
        for xx_ in np.arange(np.ceil(xlo * 20) / 20, xhi, 0.05):
            px = (xx_ - xlo) * sc; d.line([(px, 0), (px, h)], fill=(45, 45, 56)); d.text((px + 2, h - 10), f'{int(round(xx_ * 1000))}', fill=(120, 120, 140))
        for yy_ in np.arange(np.ceil(ylo * 20) / 20, yhi, 0.05):
            py = (yy_ - ylo) * sc; d.line([(0, py), (w, py)], fill=(45, 45, 56)); d.text((2, py - 11), f'{int(round(yy_ * 1000))}', fill=(120, 120, 140))
        for ti, t in enumerate(tags):
            V = V0 if t == 'start' else np.load(f'data/V_{t}.npy')
            S = section_segments(V, z)
            for s in S:
                d.line([((s[0][0] - xlo) * sc, (s[0][1] - ylo) * sc), ((s[1][0] - xlo) * sc, (s[1][1] - ylo) * sc)], fill=cols[ti % len(cols)], width=2)
            d.text((w - 150, 6 + 14 * ti), t, fill=cols[ti % len(cols)])
        d.text((6, h + 4), f'z = {z:.3f}  (front y<0 at top, x right)', fill=(255, 200, 80)); ims.append(im)
    n = len(ims); S = Image.new('RGB', (w * n + 4 * (n - 1), ims[0].height), (10, 10, 10)); x = 0
    for i in ims: S.paste(i, (x, 0)); x += w + 4
    S.save(out); print(out, S.size)
if __name__ == '__main__':
    a = sys.argv[1:]; tags = a[1].split(','); zs = [float(v) for v in a[2].split(',')]
    box = tuple(float(v) for v in a[3:7]) if len(a) >= 7 else (-0.13, 0.13, -0.22, 0.12); sc = float(a[7]) if len(a) > 7 else 2200
    plot(a[0], tags, zs, box, sc)
