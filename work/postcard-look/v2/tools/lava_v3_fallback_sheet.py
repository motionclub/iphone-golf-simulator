"""lava_v3_fallback_sheet.py <look_dir> <out.png>: the raw Lava maps and the URP Lit FALLBACK (shader missing) with the shipped tint, a white tint and emission only."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lab
gl = lab.gl
d, out = sys.argv[1:3]
C, E = gl.read_png(os.path.join(d, 'Lava_C.png')), gl.read_png(os.path.join(d, 'Lava_E.png'))
sp = gl.lava_spec(); m = sp['emission']
def lit(tint, c=C): return gl.lava_game(c, E, m, tint) / 255.0
cells = [lab.label(lab.fit(lab.f01(C), 400), 'LAVA_C (ALBEDO)', 1), lab.label(lab.fit(lab.f01(E), 400), 'LAVA_E (GLOW)', 1),
         lab.label(lab.fit(lit(sp['tint']), 400), 'LIT FALLBACK, SHIPPED TINT %.2f' % sp['tint'], 1),
         lab.label(lab.fit(lit(1.0), 400), 'LIT FALLBACK, TINT WHITE', 1),
         lab.label(lab.fit(lit(1.0, np.zeros_like(C)), 400), 'EMISSION ALONE (ALBEDO OFF)', 1)]
lab.write(out, lab.hstack(cells)); print('wrote', out)
