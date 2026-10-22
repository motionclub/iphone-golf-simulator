"""chestprof6.py: vertical plate-lit luminance profiles of the front (numpy domain, same light as the proofs' soft look) for the plate and coordinate files, to see the neck-base dark band.
usage: python3 tools/chestprof6.py [--gain 1.5] NAME=data/co_xxx.npy ...   columns: centre |x|<.03, side .05-.09 (mean of both sides)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import photo3 as ph
from fplate import BALD, FRONT_CX, SOLE, S

ZR = np.arange(1.20, 1.4001, 0.01)
BOXF = ph.roi_box('front', -0.16, 0.16, 1.10, 1.43)

def render_front(co, gain=1.5):
    L = np.array(ph.LIGHT, dtype=float).copy(); L[1:] *= gain
    N = ph.vertex_normals(co, ph.TRI); sh = ph.shade_vertices(co, N, 'front', L)
    img, mask = ph.raster_shaded(co, sh, 'front', BOXF)
    return np.asarray(img, dtype=float), np.asarray(mask)

def col_prof(img, xa, xb, box=BOXF):
    c0, r0, c1, r1 = box
    ca, cb = sorted((int(round(FRONT_CX + xa / S)) - c0, int(round(FRONT_CX + xb / S)) - c0))
    out = []
    for z in ZR:
        r = int(round(SOLE - z / S)) - r0
        out.append(img[r - 1:r + 2, ca:cb + 1].mean())
    return np.array(out)

def groups(img):
    cen = col_prof(img, -0.03, 0.03)
    sd = 0.5 * (col_prof(img, 0.05, 0.09) + col_prof(img, -0.09, -0.05))
    return cen, sd

def dip(p):
    """depth of the neck-base dark band: how far below the straight line between z 1.26 and z 1.38 the profile goes in z 1.29-1.36 (grey levels, positive = dark band)"""
    i0 = int(round((1.26 - 1.20) / 0.01)); i1 = int(round((1.38 - 1.20) / 0.01))
    line = np.interp(ZR, [ZR[i0], ZR[i1]], [p[i0], p[i1]])
    seg = slice(int(round((1.29 - 1.20) / 0.01)), int(round((1.36 - 1.20) / 0.01)) + 1)
    return float((line - p)[seg].max())

if __name__ == '__main__':
    args = sys.argv[1:]; gain = 1.5
    if '--gain' in args:
        i = args.index('--gain'); gain = float(args[i + 1]); del args[i:i + 2]
    plate = np.asarray(BALD[BOXF[1]:BOXF[3], BOXF[0]:BOXF[2]], dtype=float)
    pc, ps = groups(plate)
    print('z          ' + ' '.join(f'{z:6.2f}' for z in ZR))
    print('PLATE cen  ' + ' '.join(f'{v:6.1f}' for v in pc) + f'   dip {dip(pc):5.1f}')
    print('PLATE side ' + ' '.join(f'{v:6.1f}' for v in ps) + f'   dip {dip(ps):5.1f}')
    for a in args:
        name, path = a.split('=')
        co = np.load(path).astype(np.float64)
        img, _ = render_front(co, gain)
        c, s_ = groups(img)
        print(f'{name:5s} cen   ' + ' '.join(f'{v:6.1f}' for v in c) + f'   dip {dip(c):5.1f}')
        print(f'{name:5s} side  ' + ' '.join(f'{v:6.1f}' for v in s_) + f'   dip {dip(s_):5.1f}')
