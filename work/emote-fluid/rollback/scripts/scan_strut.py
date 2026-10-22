import sys, os, itertools, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
H = EH.EmoHero(tag)
def evaluate(Lst, Rst, fd=None, sh=None):
    EC.Thrust2.L_ST = tuple(Lst); EC.Thrust2.R_ST = tuple(Rst)
    if fd is not None: EC.Thrust2.FD_ST = tuple(fd)
    if sh is not None: EC.Thrust2.SH_ST = tuple(sh)
    C = EC.build('Emote_Thrust', H)
    out = []
    for t in (2.85, 3.0):
        P = C.P(t); b, h, info = H.solve(P)
        row = [info['R_arm_short'], info['L_arm_short'], info['R_wrist_clamp_deg']]
        for side in 'LR':
            trees = C.clr.obstacles(info, side, False, True, False)
            pts, kind = C.clr.arm_samples(info, side, side == 'R')
            viol, nrm = C.clr.violations(pts, kind, trees)
            row.append(float(viol.max()))
        out.append(row)
    return np.array(out)
res = []
for (r_, f_, u_), fd, sh in itertools.product(itertools.product((0.27, 0.31, 0.35), (0.04, 0.10), (0.08, 0.14)), ((0.30, 0.60, -0.74), (0.15, 0.80, -0.58), (0.05, 0.93, -0.35)), ((0.15, 0.55, 0.82), (0.30, 0.35, 0.89))):
    o = evaluate((-r_, f_, u_), (r_, f_ + 0.03, u_ + 0.01), fd, sh)
    worst = max(o[:, 3].max(), o[:, 4].max()); reach = max(o[:, 0].max(), o[:, 1].max())
    res.append((worst + 3 * reach + 0.0004 * o[:, 2].max(), worst, reach, o[:, 2].max(), r_, f_, u_, fd, sh))
res.sort(key=lambda r: r[0])
for r in res[:12]:
    print('score %.3f worst %.3f short %.3f clamp %.1f  r %.2f f %.2f u %.2f fd %s sh %s' % r)
