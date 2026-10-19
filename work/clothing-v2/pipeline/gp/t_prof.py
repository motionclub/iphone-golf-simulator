import sys, os, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, scene, evaluate as EV, render as RD
h = rig.Hero('MatchHero_Male'); R = scene.Rig(h); items = scene.items_from_dump(h)
bits = EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', h.id))
S = EV.Stress(R, items, bits); print('groups', [[items[g].tag for g in grp] for grp in S.groups])
mats, sw = h.frames('tennis__Male_Serve'); f = 20
t=time.time(); Ps = S.posed(mats[f], {k: v[f] for k, v in sw.items()}); print('pose', time.time()-t)
t=time.time(); b = S._batch(Ps, list(range(len(items)))); print('batch', time.time()-t)
V = RD.view_matrix(Ps[0].mean(0), 0, 0)
t=time.time(); ids, dep = S.R.draw(b, V); print('draw', time.time()-t)
t=time.time(); ids, dep = S.R.draw(b, V); print('draw2', time.time()-t)
t=time.time(); r = S.frame(Ps); print('frame', time.time()-t, r['tear'], r['layer'], r['by'])
