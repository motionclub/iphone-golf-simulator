"""smoke_gen.py <out.png> key=val ... : writes Smoke_C.png with SMOKE_P overrides (Blender python)."""
import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
for kv in sys.argv[2:]:
    k, v = kv.split('='); g.SMOKE_P[k] = float(v)
r = g.mat_smoke()
img = np.concatenate([r['C'], r['A'][..., None]], -1)
g.write_png(sys.argv[1], g.enc(img))
