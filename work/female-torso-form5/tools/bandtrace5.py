"""bandtrace5.py: trace the dark under-butt fold-band centre line (z of the high-passed luminance minimum) per column x, in the numpy plate-lit domain, for the plate and for coordinate files.
usage: python3 tools/bandtrace5.py [--gain 1.5] NAME=data/co_xxx.npy ...   (prints z of the band centre in cm above the sole for |x| = .03 .. .15 and the rise vs the plate)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import photo3 as ph
import foldx5 as fx
from fplate import BALD, BACK_CX, SOLE, S

def hp_img(a, s=6.0):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); b = np.asarray(im.filter(ImageFilter.GaussianBlur(s)), dtype=np.float32)
    return np.asarray(im, dtype=np.float32) - b

def trace(img, box, xs, zlo=0.74, zhi=0.90, s=6.0):
    c0, r0, c1, r1 = box
    h = hp_img(img, s)
    out = []
    for x in xs:
        col = int(round(BACK_CX - x / S)) - c0
        prof = h[:, max(col - 2, 0):col + 3].mean(axis=1)
        zs = SOLE * S - (np.arange(r0, r1)) * S           # z of each row (row index r -> z = (SOLE - r)*S)
        zs = (SOLE - np.arange(r0, r1)) * S
        m = (zs >= zlo) & (zs <= zhi)
        pz = prof[m]; z = zs[m]
        k = int(np.argmin(pz)); half = pz[k] * 0.5
        w = np.clip(half - pz, 0, None); c = float((w * z).sum() / max(w.sum(), 1e-9))
        out.append((c, float(-pz[k]), float(z[k])))
    return out

if __name__ == '__main__':
    gain = 1.5
    args = sys.argv[1:]
    if '--gain' in args:
        i = args.index('--gain'); gain = float(args[i + 1]); del args[i:i + 2]
    xs = (0.03, 0.045, 0.06, 0.075, 0.09, 0.105, 0.12, 0.135, 0.15)
    box = fx.BOX
    c0, r0, c1, r1 = box
    plate = np.asarray(BALD[r0:r1, c0:c1], dtype=np.float32)
    tp = trace(plate, box, xs)
    print('|x|          ' + ' '.join(f'{x:6.3f}' for x in xs))
    print('PLATE  z(cm) ' + ' '.join(f'{100*t[0]:6.1f}' for t in tp))
    for a in args:
        name, path = a.split('=')
        co = np.load(path).astype(np.float64)
        img, mask = fx.render(co, gain, box)
        img = np.asarray(img, dtype=np.float32)
        t = trace(img, box, xs)
        # average of the two sides is not possible (x>0 only sampled) -> also mirror
        print(f'{name:6s} z(cm) ' + ' '.join(f'{100*v[0]:6.1f}' for v in t) + f'   rise(.045->.12) {100*(t[6][0]-t[1][0]):+.1f} cm (plate {100*(tp[6][0]-tp[1][0]):+.1f})')
        print(f'{"":6s} depth  ' + ' '.join(f'{v[1]:6.1f}' for v in t))
    print('plate depth  ' + ' '.join(f'{t[1]:6.1f}' for t in tp))
