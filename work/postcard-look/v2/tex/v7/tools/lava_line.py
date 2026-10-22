import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
F0 = g.lava_fields()
ss = 2
hhd, crd, sed = g.lava_design(F0)          # ss-res design
hh, crust, seam = [g.ssdown(a_, ss) for a_ in (hhd, crd, sed)]
raw_hh = g.ssdown(F0['hh'], ss); raw_cr = g.ssdown(F0['crust'], ss)
r = g.lava_encode(F0, g.LAVA_ENC['alpha'], list(g.LAVA_ENC['lut']))
C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
sp = g.lava_spec(); h_, rgb = g.lava_shader_model(C, E, N, sp)
Jt = g.map_jump(F0['pu'], F0['pv']) * F0['pu'].shape[0]
J = g.ssdown(Jt, ss)
col = 415
print('profile across the line at column %d, rows 585..600 (texel row: raw_hh raw_crust | design hh crust seam | J (pattern texels per texel) | shader heat, rgb)' % col)
for row in range(584, 602):
    print(row, '%.2f %.2f | %.2f %.2f %.2f | %5.1f | %.2f' % (raw_hh[row, col], raw_cr[row, col], hh[row, col], crust[row, col], seam[row, col], J[row, col], h_[row, col]), rgb[row, col].astype(int))
