"""fieldmap3.py: image of the analytic front/back feature fields for a param json.  python3 tools/fieldmap3.py P.json out.png"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
from torso3 import *
import viz3

def field_front(P, xs, zs):
    X, Z = np.meshgrid(xs, zs)
    return -(bust_amp(X, Z, P) + fill_amp(X, Z, P) - sternum_amp(X, Z, P) - moat_amp(X, Z, P))   # + = backward, - = forward (as displacement y)

def cmap(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    r = np.where(t < 0.5, 40 + 430 * t, 255)
    g = np.where(t < 0.5, 40 + 430 * t, 255 - 430 * (t - 0.5))
    b = np.where(t < 0.5, 255, 255 - 430 * (t - 0.5))
    return np.stack([r, g, b], -1).clip(0, 255).astype(np.uint8)

def render(P, out, sc=3000):
    xs = np.arange(-0.13, 0.1301, 0.001); zs = np.arange(1.34, 1.10, -0.001)
    D = 1000 * field_front(P, xs, zs)          # mm, + backward
    # absolute front surface: wall table + D  (relative to F(z)) is not needed; show D itself with iso-lines every 4 mm
    img = Image.fromarray(cmap(D, -35, 35)).resize((len(xs) * 3, len(zs) * 3), Image.BILINEAR)
    d = ImageDraw.Draw(img)
    for lv in range(-32, 33, 4):
        pass
    # draw iso-lines by thresholding
    A = np.asarray(img.convert('RGB')).astype(float)
    Dm = np.kron(D, np.ones((3, 3)))
    for lv in range(-36, 37, 6):
        m = (np.abs(Dm - lv) < 0.45)
        A[m] = (0, 0, 0)
    img = Image.fromarray(A.astype(np.uint8)); d = ImageDraw.Draw(img)
    for xm in np.arange(-0.12, 0.121, 0.04):
        u = (xm + 0.13) / 0.001 * 3; d.line([(u, 0), (u, img.height)], fill=(90, 90, 90)); d.text((u + 2, 2), f'{xm*100:+.0f}', fill=(0, 0, 0))
    for zm in np.arange(1.12, 1.34, 0.04):
        v = (1.34 - zm) / 0.001 * 3; d.line([(0, v), (img.width, v)], fill=(90, 90, 90)); d.text((2, v + 1), f'{zm:.2f}', fill=(0, 0, 0))
    img.save(out); print(out, img.size, 'D range mm', D.min(), D.max())

if __name__ == '__main__':
    P = {**DEFAULT3, **json.load(open(sys.argv[1]))}
    render(P, sys.argv[2])
