"""explore feasible racket shaft directions for the crossed-forearm hit (python3.13): min wrist clamp over roll for shaft directions in the pelvis frame"""
import sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
import pose as PS
from kin import a2w, w2a, unit
tag = sys.argv[1]; t = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
H = EH.EmoHero(tag)
C = EC.build('Emote_Thrust', H)
P0 = C.P(t)
b, h, info0 = H.solve(P0)
Rp = C.pelvis_R(info0)
pos = np.asarray(P0['r_rk_pos'], float)
print('grip', np.round(pos, 3), 'shoulder-short', round(info0['R_arm_short'], 3))
best = {}
rows = []
for az in range(-180, 180, 20):          # azimuth in the pelvis frame: 0 = forward, +90 = right
    for el in range(-80, 81, 20):
        a, e = math.radians(az), math.radians(el)
        d_p = np.array([math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)])      # (r,f,u) in the pelvis frame
        sh = w2a(Rp @ a2w(d_p))
        mn = (1e9, None)
        for roll in range(0, 360, 30):
            g0 = unit(np.cross(sh, [0, 0, 1.0])) if abs(sh[2]) < 0.95 else np.array([1.0, 0, 0])
            ar = math.radians(roll)
            g1 = unit(np.cross(sh, g0))
            face = math.cos(ar) * g0 + math.sin(ar) * g1
            Pt = dict(P0); Pt['r_rk_shaft'] = sh; Pt['r_rk_face'] = face
            bb, hh, ii = H.solve(Pt)
            sc = ii['R_wrist_clamp_deg'] + 300 * ii['R_arm_short']
            if sc < mn[0]:
                mn = (sc, roll)
        rows.append((az, el, mn[0], mn[1]))

tab = {(r[0], r[1]): r for r in rows}
print('feasible map (score < 3 -> "o", < 12 -> "+", else "."): columns az -180..160 step 20; rows el 80..-80')
print('       ' + ''.join('%5d' % az for az in range(-180, 180, 20)))
for el in range(80, -81, -20):
    line = ''
    for az in range(-180, 180, 20):
        sc = tab[(az, el)][2]
        line += '    ' + ('o' if sc < 3 else '+' if sc < 12 else '.')
    print('el%4d ' % el + line)
