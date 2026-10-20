"""noise5.py: mesh-scale noise (rms of y - Taubin(y)) by z band, back half of T5, for coord files; prints and returns."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from torso2 import EA, EB, CO0
N = len(CO0)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = np.load(HERE + '/data/zone5.npz'); T5 = Z['torso']

def taubin_y(c, mask, k=10, lam=.5, mu=-.53):
    yy = c[:, 1].copy(); m_e = mask[EA] & mask[EB]; ea, eb = EA[m_e], EB[m_e]
    deg = np.bincount(np.r_[ea, eb], minlength=N).astype(float)
    for _ in range(k):
        for l in (lam, mu):
            sm = np.zeros(N); np.add.at(sm, ea, yy[eb]); np.add.at(sm, eb, yy[ea])
            nb = np.where(deg > 0, sm / np.maximum(deg, 1), yy); yy = yy + l * np.where(mask, 1, 0) * (nb - yy)
    return yy

def bands(c, bands=((0.62, 0.70), (0.70, 0.78), (0.78, 0.86), (0.86, 0.94)), k=10):
    reg = T5 & (c[:, 1] > 0.0); r = 1000 * (c[:, 1] - taubin_y(c, reg, k)); out = []
    for z0, z1 in bands:
        m = reg & (c[:, 2] >= z0) & (c[:, 2] < z1) & (np.abs(c[:, 0]) < 0.2) & (np.abs(c[:, 0]) > 0.012)
        out.append((z0, z1, float(np.sqrt((r[m] ** 2).mean())), float(np.percentile(np.abs(r[m]), 95))))
    return out

if __name__ == '__main__':
    for a in sys.argv[1:]:
        c = np.load(a).astype(np.float64)
        print(os.path.basename(a), ' '.join(f'[{z0:.2f}-{z1:.2f}: rms {r:.2f} p95 {p:.2f}]' for z0, z1, r, p in bands(c)))
