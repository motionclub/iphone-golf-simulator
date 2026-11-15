"""ua_mask2.py <out.npy> [r_full m] [r_fade m]: 0..1 mask over his polo around each armpit (11-14 polo underarm).
Armpit = the lowest part of today's chest/upper-arm weight transition on each side; full inside r_full, fading to 0 at r_fade."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, rig, scene, graph as GR
h = rig.Hero('MatchHero_Male'); it = [i for i in scene.items_from_dump(h) if i.tag == 'Kit_Top'][0]
r0 = float(sys.argv[2]) if len(sys.argv) > 2 else .10; r1 = float(sys.argv[3]) if len(sys.argv) > 3 else .17
gt = it.gidx[it.bi]; P = it.P
m = np.zeros(len(P))
for side, ua in ((-1, 'LeftUpperArm'), (1, 'RightUpperArm')):
    a = (it.bw * (gt == h.bidx[ua])).sum(1)
    sel = (a > .3) & (a < .7) & (P[:, 0] * side > .1)
    ys = P[sel, 1]; low = sel & (P[:, 1] < np.percentile(ys, 10))
    A = P[low].mean(0); print(ua, 'armpit at', A.round(3), int(low.sum()))
    d = np.linalg.norm(P - A, axis=1)
    t = np.clip((r1 - d) / (r1 - r0), 0, 1); m = np.maximum(m, t * t * (3 - 2 * t))
m = GR.Graph(P, it.tri).smooth(m[:, None], 4)[:, 0]
np.save(sys.argv[1], m.astype(np.float32)); print('mask: %d of %d vertices > .5, %d > .05' % ((m > .5).sum(), len(m), (m > .05).sum()))
