"""near_sim.py: Laplacian sd of the bilinear-magnified luminance of Fairway_C (x3.8 = the tee's last rows; x1 = mid field, x0.5 = far), current vs a candidate extra 'grain' layer. Blender python."""
import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
def magnify(c, mag, size=380):
    ys = (np.arange(size) + .5) / mag - .5; xs = (np.arange(size) + .5) / mag - .5
    yi = np.floor(ys).astype(int); xi = np.floor(xs).astype(int); fy = (ys - yi)[:, None]; fx = (xs - xi)[None, :]
    h, w = c.shape
    y0 = yi % h; x0 = xi % w; y1 = (yi + 1) % h; x1 = (xi + 1) % w
    return (c[y0][:, x0] * (1 - fx) + c[y0][:, x1] * fx) * (1 - fy) + (c[y1][:, x0] * (1 - fx) + c[y1][:, x1] * fx) * fy
def lap_sd(L):
    l = (-4 * L[1:-1, 1:-1] + L[:-2, 1:-1] + L[2:, 1:-1] + L[1:-1, :-2] + L[1:-1, 2:]); return float(l.std())
def measure(L255, tag):
    out = []
    for mag in (3.8, 2.4, 1.0):
        v = []
        for (y0, x0) in ((0, 0), (300, 500), (700, 200), (150, 800)):
            c = L255[y0:y0 + 120, x0:x0 + 120]
            size = int(120 * mag) if mag >= 1 else 120
            v.append(lap_sd(magnify(c, mag, min(size, 380))))
        out.append('x%.1f lap sd %.2f' % (mag, np.mean(v)))
    print(tag, ' | '.join(out))
C = g.read_png(os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'Unity/Assets/Resources/Course/Look', 'Fairway_C.png')).astype(np.float32) / 255
L = g.lum(C) * 255
measure(L, 'installed Fairway_C')
