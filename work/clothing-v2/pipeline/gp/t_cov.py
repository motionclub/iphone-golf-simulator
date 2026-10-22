import sys, os, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, scene, evaluate as EV
h = rig.Hero(sys.argv[-1]); items = scene.items_from_dump(h)
t = time.time(); tb, vb = EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', h.id), vertices=True); print('COV s', round(time.time()-t, 1))
for it, b in zip(items, tb): print('COV', it.tag, 'tris', len(b), 'covered', int((b != 0).sum()), 'drawn&covered', int(((b != 0) & it.drawn).sum()))
