import sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
from kin import w2a
a_ = sys.argv[sys.argv.index('--') + 1:]
H = EH.EmoHero(a_[0]); C = EC.build('Emote_Spike', H)
ix = H.rig.idx
print('fold_d', C.fold_d)
for t in (0.0, 0.9, 1.2, 1.5, 1.7, 1.967, 2.2, 3.2):
    P = C.P(t); b, h, info = H.solve(P)
    v = info['Pos'][ix['Neck']] - info['Pos'][ix['Hips']]
    ang = math.degrees(math.acos(v[2] / np.linalg.norm(v)))
    print('t=%.3f trunk-from-vertical %.1f  Rshort %.3f clamp %.1f  knees %.0f/%.0f  rkMinZ %.3f pelDrop %.3f' % (t, ang, info['R_arm_short'], info['R_wrist_clamp_deg'], info['lf_knee_flex_deg'], info['rf_knee_flex_deg'], EC.racket_min_z(info['rk_origin'], info['rk_R']), info.get('pelvis_auto_drop', 0)))
