import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
v8 = dict(g.SMOKE_P)
g.SMOKE_P.update(g.SMOKE_P_V7); a7 = g.mat_smoke()['A']
g.SMOKE_P.clear(); g.SMOKE_P.update(v8); a8 = g.mat_smoke()['A']
for nm, a in (('v7', a7), ('v8', a8)):
    for gain, pw in ((1.35, 1.0), (1.10, 1.5)):
        ae = np.power(np.clip(a * gain, 0, 1), pw)
        print(nm, 'gain %.2f pow %.1f: peak %.3f  share eff>=.07 %.4f  >=.12 %.4f  >=.20 %.4f  >=.30 %.4f' % (gain, pw, ae.max(), (ae >= .07).mean(), (ae >= .12).mean(), (ae >= .20).mean(), (ae >= .30).mean()))
