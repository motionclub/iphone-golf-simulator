import numpy as np
from zone import *
from sculpt import sstep
import sculpt3 as S
zm = zone_mask(); z = V0[:, 2]
w = sstep((z - 0.776) / 0.012) * (1 - sstep((z - 0.86) / 0.04)) * zm
print('weights>0.5:', int((w > 0.5).sum()))
L = S.lap(V0); print('lap norm stats (mm) in band', np.round(np.linalg.norm(L[w > 0.5], axis=1).mean() * 1000, 2), 'max', np.round(np.linalg.norm(L[w>0.5], axis=1).max()*1000, 1))
for it in (1, 10, 60, 200):
    Vt = S.taubin(V0, w, it=it); d = np.linalg.norm(Vt - V0, axis=1) * 1000; print(it, 'max disp', round(d.max(), 2), 'mean(band)', round(d[w > 0.5].mean(), 2))
# probe a flank vertex pair at x~0.185 z .79/.80 front
for zf in (0.79, 0.80):
    m = (np.abs(z - zf) < 0.0055) & (np.abs(np.abs(V0[:, 0]) - 0.185) < 0.004) & (V0[:, 1] < -0.04)
    print(zf, 'verts', m.sum(), 'w', np.round(w[m][:4], 2), 'lap mm', np.round(np.linalg.norm(L[m], axis=1)[:4] * 1000, 1))
