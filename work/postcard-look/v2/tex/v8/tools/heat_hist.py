import sys, os, json, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
kv = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
for k, v in kv.items():
    g.LAVA_P[k] = tuple(tuple(x) if isinstance(x, list) else x for x in v) if isinstance(v, list) else v
F0 = g.lava_fields()
hh, crust, seam = g.lava_design(F0)
hh = g.ssdown(hh, 2); crust = g.ssdown(crust, 2)
mol = crust < 0.03
h = hh[mol]
print('molten share', mol.mean())
for q in (5, 10, 25, 50, 75, 90, 95, 99):
    print('p%d %.3f' % (q, np.percentile(h, q)), end='  ')
print()
print('frac >0.98:', (h > .98).mean(), ' >0.9', (h > .9).mean(), '>0.7', (h > .7).mean(), '<0.2', (h < .2).mean())
hist, _ = np.histogram(h, bins=20, range=(0, 1)); print(np.round(hist / hist.sum(), 3))
