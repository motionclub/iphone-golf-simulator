"""cnweight5.py: per-vertex weight (0..1) of the authored custom-normal offsets to cancel: vertices whose position moved vs the ORIGINAL ArtDir mesh (smoothstep of the displacement, then 2 graph-diffusion
passes), border / floor-ring vertices forced to 0.   python3 tools/cnweight5.py coords.npy out.npy [d0_mm d1_mm]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from torso2 import CO0, EA, EB, BORDER, N, sstep
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def cn_weight(co, d0=0.002, d1=0.010, passes=2):
    d = np.linalg.norm(co.astype(np.float64) - CO0, axis=1)
    w = sstep((d - d0) / (d1 - d0))
    deg = np.bincount(np.r_[EA, EB], minlength=N).astype(float)
    for _ in range(passes):
        sm = np.zeros(N); np.add.at(sm, EA, w[EB]); np.add.at(sm, EB, w[EA])
        w = 0.5 * w + 0.5 * np.where(deg > 0, sm / np.maximum(deg, 1), w)
    z5 = np.load(HERE + '/data/zone5.npz')
    w[z5['border5']] = 0.0
    w[~np.asarray(z5['torso'], bool)] = 0.0
    return w

if __name__ == '__main__':
    co = np.load(sys.argv[1]); d0 = float(sys.argv[3]) / 1000 if len(sys.argv) > 3 else 0.002; d1 = float(sys.argv[4]) / 1000 if len(sys.argv) > 4 else 0.010
    w = cn_weight(co, d0, d1); np.save(sys.argv[2], w)
    print('weights saved', sys.argv[2], 'vertices w>0.05:', int((w > 0.05).sum()), 'w>0.95:', int((w > 0.95).sum()), 'mean over moved:', float(w[w > 0].mean()))
