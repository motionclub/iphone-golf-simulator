"""dbg_clear2.py <tag> <clip> <t> : what the offset-body engine sees for each arm at nominal channels: violating samples, their signed distance, the nearest face's dominant bone, the cloth offset there."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
import emo_clear as CL
from mathutils import Vector
a_ = sys.argv[sys.argv.index('--') + 1:]
tag, clip, t = a_[0], a_[1], float(a_[2])
H = EH.EmoHero(tag)
C = EC.build(clip, H)
clr = C.clr
P = C.P(t)
b, h, info = H.solve(P)
names = list(H.rig.names)
S = clr.mats(info); Rd = clr.rdelta(info)
for side in 'LR':
    ex = C.grip_exempt(t)
    trees = clr.obstacles(info, side, False, True, ex)
    tr = trees['skin']
    pts, kind = clr.arm_samples(info, side, side == 'R')
    keep = ~clr.arm_all[side]
    if ex: keep &= ~clr.arm_all['R' if side == 'L' else 'L']
    tris = clr.body.tris[keep[clr.body.tris].all(1)]
    res = []
    for i in range(len(pts)):
        p = Vector(pts[i]); loc, nor, idx, dist = tr.find_nearest(p, 0.10)
        if loc is None: continue
        sd = (p - loc).dot(nor)
        if dist > 0.004 and abs(sd) < 0.8 * dist: continue
        v = clr.margin['skin'] - sd
        vi = tris[idx]
        res.append((v, sd, dist, 'rk' if kind[i] else 'arm', [names[clr.body.dom[x]] for x in vi][0], float(np.mean(clr.body_off[vi])), tuple(round(float(x), 3) for x in pts[i])))
    res.sort(key=lambda r: -r[0])
    print(side, 'exempt', ex, 'violators', sum(1 for r in res if r[0] > 0), 'of', len(pts))
    for r in res[:5]:
        print('    v=%.3f sd=%.3f dist=%.3f %s nearest-face dom=%s mean offset=%.3f at %s' % r)
