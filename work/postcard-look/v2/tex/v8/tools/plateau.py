"""plateau.py <dir with Lava_C/E/N.png> ... : structural metrics of the shader-model heat of a lava map set (Blender python)."""
import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
sp = g.lava_spec()
for d in sys.argv[1:]:
    C, E, N = (g.read_png(os.path.join(d, 'Lava_%s.png' % k)) for k in 'CEN')
    h, rgb = g.lava_shader_model(C, E, N, sp)
    out = {}
    for thr in (0.6, 0.75):
        m = (h > thr).astype(np.float32)
        for k in (9, 15, 25):
            op = g._maxf(-g._maxf(-m, k), k) if False else None
            er = -g._maxf(-m, k); op = g._maxf(er, k)        # opening with a k x k square
            out['bright>%.2f_open%d' % (thr, k)] = round(float(op.mean()), 4)
        out['share>%.2f' % thr] = round(float(m.mean()), 4)
    # thin veins: top-hat of heat
    er = -g._maxf(-h.astype(np.float32), 9); op = g._maxf(er, 9); th = h - op
    out['vein_h>.15'] = round(float((th > .15).mean()), 4)
    out['vein_h>.25'] = round(float((th > .25).mean()), 4)
    # gradient energy (texel scale)
    gx = np.abs(np.roll(h, -1, 1) - h); gy = np.abs(np.roll(h, -1, 0) - h)
    out['grad_mean'] = round(float(np.maximum(gx, gy).mean()), 4)
    # edge sharpness: share of texels whose heat step to neighbour > .1
    out['step>.1'] = round(float((np.maximum(gx, gy) > .1).mean()), 4)
    print(d, out)
