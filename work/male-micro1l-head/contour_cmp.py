"""3/4 + front contour comparison of variants vs start: python3.13 contour_cmp.py <tag> [<tag> ...]"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *
sys.path.insert(0, str(I1)); import contours as C
ctx = LCtx(with_dist=False); V0 = ctx.V0; E = ctx.E
vs = {'start': V0}; vs.update({t: np.load(W / f'data/V_{t}.npy') for t in sys.argv[1:]})
rows = list(range(470, 596, 6)); Q = {k: C.report_q3(v, E, rows=rows, verbose=False) for k, v in vs.items()}; P = {k: C.report_profile(v, E, rows=range(200, 270, 4), verbose=False) for k, v in vs.items()}
jr = [r for r in rows if 494 <= r <= 578 and r in Q['start']['q3L']]
for k in vs:
    allv = [v for q in ('q3L', 'q3R') for r in jr for v in Q[k][q][r]]
    cheek = [v for q in ('q3L', 'q3R') for r in jr if 500 <= r <= 560 for v in Q[k][q][r]]
    low = [v for q in ('q3L', 'q3R') for r in jr if 566 <= r <= 578 for v in Q[k][q][r][:1]]
    print(f'{k:8s} 3/4 jaw+cheek rows: within3mm {sum(1 for v in allv if abs(v) <= 3)}/{len(allv)}  mean|err| {np.mean(np.abs(allv)):.2f} | cheek rows 500-560 mean|err| {np.mean(np.abs(cheek)):.2f} | jaw-bottom rows 566-578 L-edge mean|err| {np.mean(np.abs(low)):.2f} | front half-width jaw rows max|err| {max(abs(P[k][r][2]) for r in P[k] if 228 <= r <= 264):.2f}')
