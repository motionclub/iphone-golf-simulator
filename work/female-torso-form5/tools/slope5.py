"""slope5.py: max underside slope (deg from vertical) along the lower lobe flank at |x| .045/.065/.09 (sagittal vertex profiles, smoothed)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from torso4 import gauss1d

def prof(c, xc, zr=np.arange(0.66, 0.92, 0.01)):
    ys = []
    for z in zr:
        m = (np.abs(c[:, 2] - z) < 0.0056) & (np.abs(np.abs(c[:, 0]) - xc) < 0.012) & (c[:, 1] > 0.0)
        ys.append(c[m, 1].max() if m.any() else np.nan)
    return zr, np.array(ys)

def max_slope(c):
    out = []
    for xc in (0.045, 0.065, 0.09):
        zr, y = prof(c, xc); g = np.isfinite(y)
        yy = np.interp(zr, zr[g], y[g]); zz = np.arange(0.66, 0.92, 0.002)
        yy = gauss1d(np.interp(zz, zr, yy), 0.008, step=0.002)
        ang = np.degrees(np.arctan(np.gradient(yy, 0.002)))
        m = (zz >= 0.74) & (zz <= 0.88)
        out.append(round(float(ang[m].max()), 1))
    return out

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(os.path.basename(p), max_slope(np.load(p).astype(np.float64)))
