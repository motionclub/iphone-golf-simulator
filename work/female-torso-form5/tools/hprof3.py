"""horizontal brightness profiles (plate vs renders) along rows at given model z.  python3-import: plot_h(roi,out,zs,xlo,xhi,files,labels)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from viz3 import *
from ncc3 import roi_pix
from PIL import ImageDraw
def hprofile(img, roi, z, xlo, xhi, half=0.004):
    a = np.asarray(img.convert('L'), float)
    x0, y0, x1, y1 = roi_pix(roi, xlo, xhi, z - half, z + half)
    seg = a[y0:y1 + 1, min(x0, x1):max(x0, x1) + 1].mean(0)
    xs = np.linspace(xlo, xhi, len(seg)) if roi in ('chest', 'chestW', 'torso_front') else np.linspace(xhi, xlo, len(seg))
    o = np.argsort(xs)
    return xs[o], seg[o]
def plot_h(roi, out, zs, xlo, xhi, files, labels, W=900, H=300):
    cols = ['#ffffff', '#ffb040', '#40d0ff', '#60ff80']
    im = Image.new('RGB', (W, H * len(zs)), (20, 20, 24)); d = ImageDraw.Draw(im)
    plate = plate_crop(roi, 1.0)
    for k, z in enumerate(zs):
        oy = k * H
        d.rectangle([0, oy, W - 1, oy + H - 1], outline=(60, 60, 70))
        d.text((6, oy + 4), f'z={z:.3f} brightness vs x (each curve minus its own mean)', fill=(255, 255, 255), font=font(13, False))
        for xm in np.arange(np.ceil(xlo * 25) / 25, xhi, 0.04):
            u = (xm - xlo) / (xhi - xlo) * W; d.line([(u, oy), (u, oy + H)], fill=(45, 45, 55)); d.text((u + 2, oy + H - 16), f'{xm*100:+.0f}', fill=(120, 120, 130), font=font(12, False))
        for i, (img, lab) in enumerate([(plate, 'PLATE')] + [(bgcomp(f), l) for f, l in zip(files, labels)]):
            xs, v = hprofile(img, roi, z, xlo, xhi)
            v = v - v.mean()
            pts = [((x - xlo) / (xhi - xlo) * W, oy + H / 2 - vv * 3.0) for x, vv in zip(xs, v)]
            d.line(pts, fill=cols[i % len(cols)], width=2); d.text((W - 90, oy + 6 + 15 * i), lab, fill=cols[i % len(cols)], font=font(13))
    im.save(out); print(out)
