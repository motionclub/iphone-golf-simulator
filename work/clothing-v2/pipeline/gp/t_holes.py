import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, scene, evaluate as EV, render as RD, overlay as OV, stress as ST, candidate as CA
h = rig.Hero(sys.argv[-2]); R = scene.Rig(h); items = scene.items_from_dump(h)
S = EV.Stress(R, items, EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', h.id)))
lib = ST.Library(h.id); i = int(sys.argv[-1])
Ps = S.posed(lib.mats[i], {t: lib.sw[t][i] for t in lib.sw})
r = S.frame(Ps, keep_masks=True)
hm = r['hole_masks']; vi = int(np.argmax([m.sum() for m in hm]))
print('HOLES', r['holes'], [int(m.sum()) for m in hm], 'view', S.views[vi])
RD.write_png(os.path.join(rig.PIPE, 'scratch', 'holes.png'), OV.shot(S, Ps, S.views[vi], hm[vi]))
