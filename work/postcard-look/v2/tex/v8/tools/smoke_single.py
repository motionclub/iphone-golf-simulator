import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
outs = sys.argv[1]; tiles = []
for cfg in sys.argv[2:]:
    for k in list(g.SMOKE_P): pass
    P0 = dict(g.SMOKE_P)
    for kv in cfg.split(','):
        if not kv: continue
        k, v = kv.split('='); g.SMOKE_P[k] = float(v)
    r = g.mat_smoke(); g.SMOKE_P.clear(); g.SMOKE_P.update(P0)
    al = np.clip(r['A'] * 1.35, 0, 1)[..., None]
    bg = np.array([0.10, 0.07, 0.07], np.float32)[None, None]
    tiles.append(r['C'] * al + bg * (1 - al))
g.write_png(outs, g.enc(np.concatenate(tiles, 1)))
