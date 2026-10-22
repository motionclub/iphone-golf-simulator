import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
Cc = g.read_png(os.path.join(ROOT, 'Unity/Assets/Resources/Course/Look/Basalt_C.png')).astype(np.float32)
lin = g.s2l(Cc / 255.0).astype(np.float64)
tint = g.s2l(np.array([.56, .74, .90]))
target = np.array([30., 30., 30.]) / 255
L = np.array([1.0, 1.0, 1.0])
for _ in range(60):
    out = g.l2s(lin * tint[None, None, :] * L[None, None, :]).reshape(-1, 3).mean(0)
    L *= (target / out) ** 1.5
out = g.l2s(lin * tint[None, None, :] * L[None, None, :])
ml = g.lum(out) * 255
print('BASALT_GATE_LIGHT', np.round(L, 4), 'mean', np.round(out.reshape(-1, 3).mean(0) * 255, 1), 'median lum', float(np.median(ml)))
