"""topo3.py: topographic map (iso-lines of the absolute front/back surface y) for coordinate files, side by side.
python3 tools/topo3.py front|back out.png tag=coords.npy ..."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
from torso2 import *
from footprint import grid_surface
import viz3

def topo(side, co, xs, zs, step=0.004, sc=4):
    G = grid_surface(co, side, xs, zs)          # (len(zs), len(xs)) y (m)
    if side == 'front':
        H = -G                                   # forward = bigger
    else:
        H = G
    H = np.nan_to_num(H, nan=np.nanmin(H))
    lo, hi = np.floor(H.min() / step) * step, np.ceil(H.max() / step) * step
    img = np.zeros((len(zs), len(xs), 3), np.uint8)
    t = (H - lo) / (hi - lo)
    img[..., 0] = (255 * np.clip(1.5 * t, 0, 1)); img[..., 1] = (255 * np.clip(1.5 * (1 - abs(t - 0.5) * 2), 0, 1)); img[..., 2] = (255 * np.clip(1.5 * (1 - t), 0, 1))
    im = Image.fromarray(img).resize((len(xs) * sc, len(zs) * sc), Image.BILINEAR)
    A = np.asarray(im).copy()
    Hs = np.asarray(Image.fromarray(H.astype(np.float32)).resize((len(xs) * sc, len(zs) * sc), Image.BILINEAR))
    for lv in np.arange(lo, hi + 1e-9, step):
        w = 0.0009
        m = np.abs(Hs - lv) < w
        A[m] = (0, 0, 0) if abs((lv / (5 * step)) - round(lv / (5 * step))) > 1e-6 else (255, 255, 255)
    im = Image.fromarray(A); d = ImageDraw.Draw(im)
    for xm in np.arange(np.ceil(xs[0] * 25) / 25, xs[-1], 0.04):
        u = (xm - xs[0]) / (xs[1] - xs[0]) * sc; d.line([(u, 0), (u, 6)], fill=(0, 0, 0)); d.text((u + 2, 2), f'{xm*100:+.0f}', fill=(0, 0, 0))
    for zm in np.arange(np.ceil(zs[0] * 50) / 50, zs[-1], 0.02):
        v = (zm - zs[0]) / (zs[1] - zs[0]) * sc; d.line([(0, v), (6, v)], fill=(0, 0, 0)); d.text((8, v - 5), f'{zm:.2f}', fill=(0, 0, 0))
    return im

if __name__ == '__main__':
    side, out = sys.argv[1], sys.argv[2]
    items = [a.split('=', 1) for a in sys.argv[3:]]
    if side == 'front':
        xs = np.arange(-0.12, 0.1201, 0.002); zs = np.arange(1.10, 1.32, 0.002)
    else:
        xs = np.arange(-0.17, 0.1701, 0.002); zs = np.arange(0.80, 1.04, 0.002)
    ims = []
    for lab, f in items:
        co = np.load(f)
        ims.append(viz3.label(topo(side, co, xs, zs).convert('RGB'), lab))
    W = Image.new('RGB', (sum(i.width for i in ims), ims[0].height))
    x = 0
    for i in ims:
        W.paste(i, (x, 0)); x += i.width
    W.save(out); print(out, W.size)
