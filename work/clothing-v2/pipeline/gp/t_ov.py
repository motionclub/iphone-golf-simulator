import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, scene, evaluate as EV, render as RD, overlay as OV
h = rig.Hero(os.environ.get('HERO','MatchHero_Male')); R = scene.Rig(h); items = scene.items_from_dump(h)
bits = EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', h.id))
S = EV.Stress(R, items, bits)
out = os.path.join(rig.PIPE, 'scratch'); os.makedirs(out, exist_ok=True)
for clip, f in [(sys.argv[-2], int(sys.argv[-1]))]:
    mats, sw = h.frames(clip)
    Ps = S.posed(mats[f], {k: v[f] for k, v in sw.items()})
    r = S.frame(Ps, keep_masks=True)
    print(clip, f, r['tear'], r['layer'], r['by'], r['views'])
    top = np.argsort(r['views'])[::-1][:4]
    RD.write_png(os.path.join(out, f'ov_{clip}_{f}.png'), np.concatenate([OV.shot(S, Ps, S.views[vi], r['masks'][vi][0]) for vi in top], 1))
