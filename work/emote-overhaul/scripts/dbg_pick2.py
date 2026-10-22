import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
from kin import w2a
a_ = sys.argv[sys.argv.index('--') + 1:]
H = EH.EmoHero(a_[0]); C = EC.build('Emote_Scuba', H)
t = 4.0
P, d, env, s, c, pk = C.body_P(t)
info = C.body_info(P)
print('pk', pk, 'S_R', np.round(C.shoulder(info, 'R'), 4), 'S_grasp', np.round(C.S_grasp, 4))
P2 = C.P(t)
print('P r_wrist', np.round(P2['r_wrist'], 4), ' grasp', np.round(C.grasp[0], 4))
print('keys', [k for k in P2.keys() if k.startswith('r_')])
