"""basalt_try.py <outdir> [key=value ...] : v7 basalt experiments (Blender's python3.13). Overrides BASALT_P, generates Basalt_C/N/E, writes the PNGs + a sheet, runs the basalt gates."""
import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for kv in sys.argv[2:]:
    k, v = kv.split('=')
    g.BASALT_P[k] = tuple(float(x) for x in v.split(',')) if ',' in v else float(v)
res = g.generate('Basalt', g.mat_basalt, 'colour', 1024) if False else None
for n, fn, kind, size, tu, tv in g.MATS:
    if n == 'Basalt':
        res = g.generate(n, fn, kind, size)
for fname, arr in res.items():
    g.write_png(os.path.join(out, fname), arr)
imgs = {k: g.read_png(os.path.join(out, k)) for k in res}
def gate(what, ok, detail): print('GATE: %s %s (%s)' % (what[:90], 'PASS' if ok else 'FAIL', detail[:700]))
g.basalt_gates(imgs, gate)
C = imgs['Basalt_C.png'].astype(np.float32); E = imgs['Basalt_E.png']; N = imgs['Basalt_N.png']
sheet = np.concatenate([np.clip(C * 3.2, 0, 255).astype(np.uint8)[::2, ::2], E[::2, ::2], N[::2, ::2]], 1)
g.write_png(os.path.join(out, 'sheet.png'), sheet)
print('wrote', out)
