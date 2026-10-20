"""3/4 contour errors vs plate (mesh - plate, mm) at the jaw/cheek rows for START and variants.  python3.13 q3rows.py tag ..."""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_edit import *
import contours as C
ctx = Ctx(); V0 = ctx.V0; E = ctx.E
rows = list(range(470, 596, 6))
P = {'START': C.report_q3(V0, E, rows=rows, verbose=False)}
for t in sys.argv[1:]: P[t] = C.report_q3(np.load(W / f'data/V_{t}.npy'), E, rows=rows, verbose=False)
print('row  z      ' + ' || '.join(f'{k:^25s}' for k in P)); print('              [q3L: L R | q3R: L R]')
for r in rows:
    if all(r in P[k]['q3L'] and r in P[k]['q3R'] for k in P):
        print('%3d %.3f  ' % (r, 1.7046599 - (r - 397) * 0.0013043874) + ' || '.join('%5.1f %5.1f | %5.1f %5.1f' % (*P[k]['q3L'][r], *P[k]['q3R'][r]) for k in P))
