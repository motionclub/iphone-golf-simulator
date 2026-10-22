import sys, os, importlib.util, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
B = os.path.join(HERE, '..', 'before')
def same(name, arr):
    a = g.read_png(os.path.join(B, name)); return bool(np.array_equal(a, arr))
# smoke
g.SMOKE_P.update(g.SMOKE_P_V6)
r = g.mat_smoke(); S = np.concatenate([g.enc(r['C']), np.clip(np.round(r['A'] * 255), 0, 255).astype(np.uint8)[..., None]], -1)
print('Smoke_C v6 rollback byte-identical:', same('Smoke_C.png', S))
# lava
g.LAVA_AA = g.LAVA_AA_V6; g.LAVA_P.update(tdf_k=0, fine_a=0.0, fil_a=0.0)
g.LAVA_ENC['lut'] = (0.0, 0.1, 0.293, 0.323, 0.364, 0.390, 0.428, 0.451, 0.518, 0.553, 0.735)
r = g.mat_lava(); C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
print('Lava C/E/N v6 rollback byte-identical:', same('Lava_C.png', C), same('Lava_E.png', E), same('Lava_N.png', N))
# basalt
g.BASALT_P.update(fork2_p=0.0, wide=0.0)
res = None
for n, fn, kind, size, tu, tv in g.MATS:
    if n == 'Basalt':
        res = g.generate(n, fn, kind, size)
print('Basalt C/E/N v6 rollback byte-identical:', all(same(k, v) for k, v in res.items()), {k: same(k, v) for k, v in res.items()})
