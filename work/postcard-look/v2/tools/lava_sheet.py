import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lab
gl = lab.gl
out = sys.argv[1]; mult = float(sys.argv[2]) if len(sys.argv) > 2 else 1.2
d = lab.gen('Lava')
C, E, N = d['Lava_C.png'], d['Lava_E.png'], d['Lava_N.png']
game = lab.lava_game(C, E, (mult,) * 3)
tile3 = lab.fit(lab.tile(game, 3), 768)
one = lab.fit(game, 768)
p, hit = lab.persp(lab.tile(game, 2), 24 * 2, size=(1280, 420), cam_h=8.0, pitch_deg=-8.0)
Ef = lab.fit(lab.f01(E), 384); Cf = lab.fit(lab.f01(C), 384)
top = lab.hstack([lab.label(one, 'LAVA GAME-LIT 1X (EMISSION X%.1f)' % mult), lab.label(tile3, 'LAVA 3X3 TILED')])
mid = lab.hstack([lab.label(Cf, 'ALBEDO'), lab.label(Ef, 'EMISSION')])
sheet = lab.vstack([top, lab.label(p, 'PERSPECTIVE (CAM 8 M UP, -8 DEG PITCH, 24 M TILE)'), mid])
lab.write(out, sheet)
print('wrote', out, sheet.shape)
st = lab.lava_stats(game)
print('GAME  ', {k: (v if not isinstance(v, float) else round(v, 3)) for k, v in st.items()})
print('STILL ', lab.STILL_LAVA)
