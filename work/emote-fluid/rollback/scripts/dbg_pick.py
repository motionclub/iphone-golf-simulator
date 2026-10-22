import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
from kin import w2a
a_ = sys.argv[sys.argv.index('--') + 1:]
H = EH.EmoHero(a_[0]); C = EC.build('Emote_Scuba', H)
print('rk_land', C.rk_land, 'hover', C.hover, 'grasp wrist', C.grasp[0])
for t in (3.9, 4.0, 4.067, 4.1):
    P = C.P(t); b, h, info = H.solve(P)
    S_now = C.shoulder(info, 'R')
    print('t=%.3f S_now %s S_grasp %s | wrist cmd %s | rk_origin(auth) %s | target rk_land+hover %s | Rshort %.3f clamp %.1f' % (t, np.round(S_now, 3), np.round(C.S_grasp, 3), np.round(P['r_wrist'], 3), np.round(w2a(info['rk_origin'] - H.O), 3), np.round(C.rk_land + np.array([0, 0, C.hover]), 3), info['R_arm_short'], info['R_wrist_clamp_deg']))
# the pick-up fit posture vs the actual
x = C.pk_body
Pp = C.pickup_P(x); b, h, info = H.solve(Pp)
print('pickup_P: rk_origin(auth)', np.round(w2a(info['rk_origin'] - H.O), 3), 'short', info['R_arm_short'], 'clamp', info['R_wrist_clamp_deg'], 'x', np.round(x, 3))
