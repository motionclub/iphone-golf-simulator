"""scan_cross.py <tag> : grid scan of the Thrust cross targets with the nominal channels (no correction): worst penetration (beyond the 8 mm allowance) per arm at the three hits."""
import sys, os, itertools, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
H = EH.EmoHero(tag)
def evaluate(Lcr, Rcr, shaft=None):
    EC.Thrust2.L_CR = tuple(Lcr); EC.Thrust2.R_CR = tuple(Rcr)
    if shaft is not None: EC.Thrust2.CROSS_SHAFT = tuple(shaft)
    C = EC.build('Emote_Thrust', H)
    out = []
    for t in (0.6, 1.1667, 1.8333):
        P = C.P(t); b, h, info = H.solve(P)
        row = [info['R_arm_short'], info['L_arm_short'], info['R_wrist_clamp_deg']]
        for side in 'LR':
            trees = C.clr.obstacles(info, side, False, True, False)
            rk_obs = (info['rk_origin'] + (C.clr.rko @ info['rk_R'].T)) if side == 'L' else None
            pts, kind = C.clr.arm_samples(info, side, side == 'R')
            viol, nrm = C.clr.violations(pts, kind, trees, rk_obs=rk_obs)
            row.append(float(viol.max()))
        out.append(row)
    return np.array(out)   # rows: hit; cols: Rshort, Lshort, Rclamp, vL, vR
import os
if a_[0] == 'female':
    base_L, base_R = (0.10, 0.28, 0.09), (-0.12, 0.43, 0.27)
else:
    base_L, base_R = tuple(float(x) for x in os.environ.get('SL', '0.10,0.31,0.09').split(',')), tuple(float(x) for x in os.environ.get('SR', '-0.12,0.37,0.27').split(','))
r = evaluate(base_L, base_R)
print('base: vL', np.round(r[:, 3], 3), 'vR', np.round(r[:, 4], 3), 'short R', np.round(r[:, 0], 3), 'L', np.round(r[:, 1], 3))
print('done: base only')
