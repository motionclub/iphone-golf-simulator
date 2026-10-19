"""check_game_gates.py <film dir> [label] : gates 1-3 of GATE_DEFS_preregistered.md on one in-game trace (ServeTossFilm trace.csv).  Prints the numbers and PASS / FAIL per gate; writes <dir>/gates.json."""
import json, sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/serve/scripts')
from read_trace import load
d = sys.argv[1]; label = sys.argv[2] if len(sys.argv) > 2 else d
rows = load(d + '/trace.csv')
A = lambda r, k: np.array(r[k])
def flex(sh, el, wr):
    u, v = A(sh, 0) if False else sh - el, wr - el
    return 180.0 - np.degrees(np.arccos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
# the first serve: from the first row with prepare > 0 (wind-up) back to the hold, up to the contact
i_w = next(i for i, r in enumerate(rows) if r['prep'] > 0.0005 and r['flow'] != 'Rally')
i_rel = next(i for i, r in enumerate(rows) if r['flow'] == 'PlayerServeToss')
i_end = next((i for i, r in enumerate(rows) if i > i_rel and r['sw'] == 'True'), min(len(rows) - 1, i_rel + 90))
def F(i):
    r = rows[i]; return flex(np.array(r['Ls']), np.array(r['Lel']), np.array(r['Lh']))
def elev(i):
    r = rows[i]; ax = np.array(r['strings']) - np.array(r['Rh']); return float(np.degrees(np.arcsin(ax[1] / np.linalg.norm(ax))))   # y up
# T_H: the ball reaches the head bone's height
i_h = next(i for i in range(i_w, i_end) if rows[i]['ball'][1] >= rows[i]['head'][1])
dt = 1 / 60.0
r = rows[i_h]; k10 = int(round(0.10 / dt)); k15 = int(round(0.15 / dt))
out = dict(label=label, frame_windup_start=rows[i_w]['frame'], frame_release=rows[i_rel]['frame'], frame_T_H=r['frame'], t_H_after_windup_start=(i_h - i_w) * dt)
Lh, Ls, head, Rh, Rs = A(r, 'Lh'), A(r, 'Ls'), A(r, 'head'), A(r, 'Rh'), A(r, 'Rs')
g1a = Lh[1] >= head[1] - 0.15; g1b = F(i_h) <= 70; g1c = F(i_h) <= F(i_h - k10) - 15; g1d = Rh[1] >= Rs[1] - 0.30
rr = rows[min(i_h + k15, len(rows) - 1)]
g1e = F(i_h + k15) <= 25 and rr['Lh'][1] >= rr['head'][1] + 0.10
out['g1'] = dict(lwrist_minus_head_y=float(Lh[1] - head[1]), flexL_TH=float(F(i_h)), flexL_TH_minus_0p1=float(F(i_h - k10)), rwrist_minus_rshoulder_y=float(Rh[1] - Rs[1]),
                 flexL_TH_plus_0p15=float(F(i_h + k15)), lwrist_minus_head_y_plus_0p15=float(rr['Lh'][1] - rr['head'][1]), parts=[bool(g1a), bool(g1b), bool(g1c), bool(g1d), bool(g1e)])
g1 = all(out['g1']['parts'])
# gate 2
g2a = elev(i_h) >= 45
cand = [i for i in range(i_w, i_end) if F(i) <= 25 and rows[i]['Lh'][1] > rows[i]['head'][1]]
if cand:
    j = cand[0]; rj = rows[j]; hoop = A(rj, 'strings'); hd = A(rj, 'head')
    g2b = elev(j) >= 60 and hoop[1] >= hd[1] + 0.15 and np.hypot(hoop[0] - hd[0], hoop[2] - hd[2]) <= 0.70
    out['g2b'] = dict(frame=rj['frame'], elev=elev(j), hoop_minus_head_y=float(hoop[1] - hd[1]), hoop_head_horiz=float(np.hypot(hoop[0] - hd[0], hoop[2] - hd[2])))
else:
    g2b = False; out['g2b'] = 'no frame with the left arm straight and above the head'
run = best = 0
for i in range(i_w, i_h + 1):
    r_ = rows[i]
    if abs(elev(i)) <= 15 and r_['Rh'][1] < r_['Rs'][1] - 0.20: run += 1; best = max(best, run)
    else: run = 0
g2c = best <= 8
out['g2'] = dict(elev_TH=elev(i_h), longest_sideways_at_waist_run_frames=best, parts=[bool(g2a), bool(g2b), bool(g2c)])
g2 = g2a and g2b and g2c
# gate 3
dist = [float(np.linalg.norm(A(rows[i], 'ball') - A(rows[i], 'Lh'))) for i in range(i_w, i_rel)]
g3 = max(dist) <= 0.22
out['g3'] = dict(max_ball_to_left_wrist=max(dist), at_frame=int(np.argmax(dist)))
out['pass'] = dict(g1=bool(g1), g2=bool(g2), g3=bool(g3))
json.dump(out, open(d + '/gates.json', 'w'), indent=1)
print(label, 'T_H frame', r['frame'], '(%.2f s into the wind-up)' % ((i_h - i_w) * dt))
print(' G1 LEFT_ARM_RISES_WITH_BALL', 'PASS' if g1 else 'FAIL', json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in out['g1'].items()}))
print(' G2 RACKET_TURNS_WITH_THE_ARM', 'PASS' if g2 else 'FAIL', json.dumps(out['g2']), json.dumps(out['g2b']))
print(' G3 BALL_STAYS_IN_THE_HAND', 'PASS' if g3 else 'FAIL', json.dumps(out['g3']))
