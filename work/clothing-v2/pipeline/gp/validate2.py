import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rig, scene
for hid in rig.HEROES:
    h = rig.Hero(hid); R = scene.Rig(h); items = scene.items_from_dump(h)
    c = h.clips[3]['file']; mats, sw = h.frames(c); f = len(mats)//2
    D = R.deltas(mats[f]); res = {}
    for it in items:
        p = h.part[it.tag]
        a = R.posem(it, mats[f], sw[it.tag][f]); b = rig.pose(p, mats[f], sw[it.tag][f])
        res[it.tag] = round(np.abs(a-b).max()*1000, 4)
    print(hid, c, res, 'drawn body tris', items[0].drawn.sum(), '/', len(items[0].drawn), 'r2root', np.round(h.body.r2root,3).tolist())
