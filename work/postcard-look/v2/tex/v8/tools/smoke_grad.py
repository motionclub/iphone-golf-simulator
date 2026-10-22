import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
base = dict(g.SMOKE_P)
def stats(cfg):
    g.SMOKE_P.clear(); g.SMOKE_P.update(base)
    for kv in cfg.split(','):
        if kv:
            k, v = kv.split('='); g.SMOKE_P[k] = tuple(float(x) for x in v.split(':')) if ':' in v else float(v)
    r = g.mat_smoke(); a = np.power(np.clip(r['A'] * 1.1, 0, 1), 1.5)
    gx = np.abs(np.roll(a, -1, 1) - np.roll(a, 1, 1)) / 2; gy = np.abs(np.roll(a, -1, 0) - np.roll(a, 1, 0)) / 2
    gm = np.maximum(gx, gy); m = a > 0.005
    return 'p99 grad %.4f max %.4f  area(a>.005) %.3f  mean a in area %.3f' % (np.percentile(gm[m], 99), gm.max(), m.mean(), a[m].mean())
for cfg in sys.argv[1:]:
    print('%-60s %s' % (cfg or '(current)', stats(cfg)))
