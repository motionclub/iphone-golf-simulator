"""front half-width / back-y / front-y errors vs plate at the jaw rows for START and variants.  python3.13 jawrows.py tag1 tag2 ..."""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_edit import *
import contours as C
ctx = Ctx(); V0 = ctx.V0; E = ctx.E
tags = sys.argv[1:]
rows = range(200, 266, 4)
P = {'START': C.report_profile(V0, E, rows=rows, verbose=False)}
for t in tags: P[t] = C.report_profile(np.load(W / f'data/V_{t}.npy'), E, rows=rows, verbose=False)
print('row(z)  ' + ' | '.join(f'{k:>20s}' for k in P))
print('   [front_y_err, back_y_err, half_width_err]')
for r in rows:
    if r < 228: continue
    print('%3d z=%.3f ' % (r, float(zrow(r))) + ' | '.join('%6.1f %6.1f %6.1f' % tuple(P[k][r][:3]) for k in P))
