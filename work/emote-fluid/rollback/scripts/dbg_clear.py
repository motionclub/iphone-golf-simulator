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
S = clr.mats(info)
print('holding L:', clr.holding(info, 'L'))
names = list(H.rig.names)
names = list(H.rig.names)
tr_tris, layer_dom = {}, {}
for side in 'LR':
    pts, kind = clr.arm_samples(info, side, side == 'R', S)
    ex = C.grip_exempt(t)
    trees = clr.obstacles(info, side, False, True, ex)
    # rebuild the face lists exactly as obstacles() does, to name the owners
    other = 'L' if side == 'R' else 'R'
    grip = bool(clr.holding(info, 'L'))
    for name, pr in clr.layers.items():
        vm = clr.vm[name]
        if name == 'skin':
            keep = clr.exposed.copy()
            if not (grip or ex): keep |= clr.arm_all[other]
        elif name == 'shirt':
            keep = ~vm['sleeve'][side]
        else:
            keep = np.ones(len(pr.co), bool)
        tr_tris[name] = pr.tris[keep[pr.tris].all(1)]
        layer_dom[name] = pr.dom
    for name, tr in trees.items():
        res = []
        for i in range(len(pts)):
            p = Vector(pts[i]); loc, nor, idx, dist = tr.find_nearest(p, 0.10)
            if loc is None: continue
            sd = (p - loc).dot(nor)
            if dist > 0.004 and abs(sd) < 0.6 * dist: continue
            v = (clr.margin_racket if kind[i] == 1 else clr.margin[name]) - sd
            fv = tr_tris[name][idx]
            res.append((v, i, kind[i], dist, tuple(round(float(x), 3) for x in pts[i]), [names[layer_dom[name][x]] for x in fv], tuple(round(float(x), 3) for x in loc), tuple(round(float(x), 2) for x in nor)))
        res.sort(key=lambda r: -r[0])
        print(side, name, 'n>0:', sum(1 for r in res if r[0] > 0))
        for r in res[:2]:
            print('     ', 'rk' if r[2] else 'arm', 'v=%.3f d=%.3f at %s face-dom %s loc %s nrm %s' % (r[0], r[3], r[4], r[5], r[6], r[7]))
