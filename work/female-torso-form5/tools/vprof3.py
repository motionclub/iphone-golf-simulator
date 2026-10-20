"""vertical brightness profiles (plate vs renders) along columns at given model x; plots to PNG.
python3 tools/vprof3.py roi out.png zlo zhi x1,x2,.. label=render.png ..."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from viz3 import *
from ncc3 import roi_pix
from PIL import ImageDraw

def profile(img, roi, x, zlo, zhi, half=0.006):
    a = np.asarray(img.convert('L'), float)
    x0, _, x1, _ = roi_pix(roi, x - half, x + half, zlo, zhi)
    _, y0, _, y1 = roi_pix(roi, x, x, zlo, zhi)
    col = a[y0:y1, min(x0, x1):max(x0, x1) + 1].mean(1)
    zs = np.linspace(zhi, zlo, len(col))
    return zs, col

def plot(roi, out, zlo, zhi, xs, files, labels, W=520, H=640):
    cols = ['#ffffff', '#ffb040', '#40d0ff', '#60ff80', '#ff70c0']
    im = Image.new('RGB', (W * len(xs), H), (20, 20, 24)); d = ImageDraw.Draw(im)
    plate = plate_crop(roi, 1.0)
    for k, x in enumerate(xs):
        ox = k * W
        d.rectangle([ox, 0, ox + W - 1, H - 1], outline=(60, 60, 70))
        d.text((ox + 6, 4), f'x={x:+.3f}  brightness vs z (each curve normalised to its own mean over the window)', fill=(255, 255, 255), font=font(13, False))
        for zz in np.arange(np.ceil(zlo * 50) / 50, zhi, 0.02):
            yy = H - 30 - (zz - zlo) / (zhi - zlo) * (H - 60)
            d.line([(ox, yy), (ox + W, yy)], fill=(40, 40, 50)); d.text((ox + 3, yy - 13), f'{zz:.2f}', fill=(120, 120, 130), font=font(12, False))
        for i, (img, lab) in enumerate([(plate, 'PLATE')] + [(Image.open(f).convert('RGBA') if False else bgcomp(f), l) for f, l in zip(files, labels)]):
            zs, v = profile(img, roi, x, zlo, zhi)
            v = (v - v.mean()) / 255.0
            pts = [(ox + W / 2 + vv * 2.6 * W * 0.5 * 2 / 2, H - 30 - (z - zlo) / (zhi - zlo) * (H - 60)) for z, vv in zip(zs, v)]
            d.line(pts, fill=cols[i % len(cols)], width=2)
            d.text((ox + 8, 22 + 16 * i), lab, fill=cols[i % len(cols)], font=font(13))
    im.save(out); print(out)

if __name__ == '__main__':
    roi, out, zlo, zhi = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    xs = [float(v) for v in sys.argv[5].split(',')]
    pairs = [a.split('=', 1) for a in sys.argv[6:]]
    plot(roi, out, zlo, zhi, xs, [p[1] for p in pairs], [p[0] for p in pairs])
