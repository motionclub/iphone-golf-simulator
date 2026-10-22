import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
for kv in sys.argv[1:]:
    k, v = kv.split('=')
    g.SMOKE_P[k] = tuple(float(x) for x in v.split(',')) if ',' in v else float(v)
r = g.mat_smoke(); a = np.clip(r['A'] * 1.35, 0, 1)
def shift(x, dx, dy, mir):
    if mir: x = x[:, ::-1]
    return np.roll(np.roll(x, int(dx * x.shape[1]), 1), int(dy * x.shape[0]), 0)
best = 0
res = []
for sp in (0.0, 0.05, 0.10, 0.15):
    for sc in (1.0, 0.9):
        b = shift(a, sp, 0.02, True)
        c = shift(a, -sp, 0.04, False)
        two = 1 - (1 - a) * (1 - b); three = 1 - (1 - a) * (1 - b) * (1 - c)
        res.append((sp, sc, float(two.max()), float(three.max()), float((three >= .30).mean()), float((three >= .85).mean())))
print('single max %.3f; stack of 2 (mirrored, shift) max / 3 cards max / share>=.30 / share>=.85:' % a.max())
for r_ in res[::2]: print('  shift %.2f: 2-card max %.3f, 3-card max %.3f, share>=.30 %.3f, share>=.85 %.4f' % (r_[0], r_[2], r_[3], r_[4], r_[5]))
