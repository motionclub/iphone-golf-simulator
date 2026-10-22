"""Edit e7: fairing of the nose-side / alar zone (removes the speckled crinkles of the carved alar chains) -- loops keep their vertices."""
import sys; sys.path.insert(0, '.')
from edlib import *


def e7_nose_fair(V, M, iters=6, strength=0.85):
    ax = np.abs(V[:, 0]) * 1000; z = V[:, 2]; y = V[:, 1]
    w = sstep(10.0, 15.0, ax) * (1 - sstep(34.0, 40.0, ax)) * sstep(1.524, 1.531, z) * (1 - sstep(1.566, 1.576, z)) * sstep(-0.10, -0.125, y) * strength
    return M.taubin(V, w, iters=iters)
