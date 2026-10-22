import numpy as np, sys, json, time
sys.path.insert(0, '.')
import fair as FA, quality as Q
from common import V0
tin, tout, tau = sys.argv[1], sys.argv[2], float(sys.argv[3])
box = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
V = np.load(f'data/V_{tin}.npy'); g = FA.box_mask(V0, **box)
t = time.time(); Vf, info = FA.fair(V, g, tau=tau, return_info=True); print(info, round(time.time() - t, 1), 's')
np.save(f'data/V_{tout}.npy', Vf)
q = Q.stats(Vf); d = np.linalg.norm(Vf - V0, axis=1) * 1000
print(f'{tout}: moved {int((d > 1e-4).sum())} max {d.max():.1f} mm  dihedral p99 {q["p99"]:.1f} max {q["max"]:.1f} new_sharp {q["new_sharp"]}')
dd = Q.dihedral(Vf); idx = np.argsort(-(dd * Q.ZONE_E))[:4]
print([('%.0f' % dd[i], '(x%.0f y%.0f z%.0f)' % tuple((Vf[Q._ev[i][0]] + Vf[Q._ev[i][1]]) / 2 * 1000)) for i in idx])
