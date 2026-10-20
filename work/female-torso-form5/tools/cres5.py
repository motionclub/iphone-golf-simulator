"""cres5.py: crescent (lowest-luminance z) + dip depth per x column, plate vs model, front view, plate-fit light x gain.  import cres5; cres5.stats(co)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import photo3 as ph
from fplate import BALD, S, FRONT_CX, SOLE

XS = (0.03, 0.06, 0.085, 0.11)
ZS = np.arange(1.10, 1.32, 0.002)
_box = ph.roi_box('front', -0.16, 0.16, 1.08, 1.34)


def plate_prof(x, hw=1):
    col = FRONT_CX + x / S
    out = []
    for z in ZS:
        r = SOLE - z / S
        r0, c0 = int(round(r)), int(round(col))
        out.append(BALD[r0 - 1:r0 + 2, c0 - hw:c0 + hw + 1].mean())
    return np.array(out)


def model_prof(co, x, gain=2.5):
    L = np.array(ph.LIGHT, dtype=float).copy(); L[1:] *= gain
    N = ph.vertex_normals(co, ph.TRI)
    sh = ph.shade_vertices(co, N, 'front', L)
    img, mask = ph.raster_shaded(co, sh, 'front', _box)
    c0, r0, c1, r1 = _box
    col = int(round(FRONT_CX + x / S)) - c0
    return np.array([img[int(round(SOLE - z / S)) - r0 - 1:int(round(SOLE - z / S)) - r0 + 2, col - 1:col + 2].mean() for z in ZS])


def feat(v):
    i0 = int(np.argmin(np.abs(ZS - 1.13)))
    base = v[max(i0 - 4, 0):i0 + 4].mean()
    lo = int(np.argmin(np.abs(ZS - 1.15))); hi = int(np.argmin(np.abs(ZS - 1.25)))
    j = lo + int(np.argmin(v[lo:hi]))
    return float(ZS[j]), float(v[j] - base)


def stats(co, gain=2.5):
    out = {}
    for x in XS:
        pz, pd = feat(plate_prof(x))
        mz, md = feat(model_prof(co, x, gain))
        out[x] = (pz, pd, mz, md)
    return out


def line(co, gain=2.5):
    s = stats(co, gain)
    return ' | '.join(f'x{x:.3f}: z {mz:.3f}({pz:.3f}) dip {md:+.0f}({pd:+.0f})' for x, (pz, pd, mz, md) in s.items())

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p.split('/')[-1], line(np.load(p).astype(np.float64)))
