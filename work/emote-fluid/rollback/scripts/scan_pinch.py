"""scan_pinch.py <tag> : pole direction of the pinch (left) arm of the Scuba dance, chest frame: penetration of the nominal pose over the dance cycle"""
import sys, os, itertools, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
from kin import unit
a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
H = EH.EmoHero(tag)
C = EC.build('Emote_Scuba', H)
res = []
poles = [(-0.35, -0.65, -0.65)] + [(x, y, z) for x in (-0.9, -0.6, -0.3, 0.0) for y in (-0.5, 0.0, 0.5) for z in (-0.7, -0.2, 0.4)]
for pole in poles:
    C.l_pole_hold = unit(np.array(pole, float))
    worst = -9; sh = 0
    for t in (1.0, 1.25, 1.5, 1.8, 2.2):
        P = C.P(t); b, h, info = H.solve(P)
        ca = C.clr
        trees = ca.obstacles(info, 'L', True, False, False)           # head ignored (the pad is on the nose)
        pts, kind = ca.arm_samples(info, 'L', False)
        viol, nrm = ca.violations(pts, kind, trees)
        worst = max(worst, float(viol.max()))
        sh = max(sh, info['L_arm_short'])
    res.append((worst, sh, pole))
res.sort(key=lambda r: r[0])
print('baseline pole (-0.35,-0.65,-0.65):', [r for r in res if r[2] == (-0.35, -0.65, -0.65)])
for r in res[:10]:
    print('worst viol %.3f short %.3f pole %s' % r)
