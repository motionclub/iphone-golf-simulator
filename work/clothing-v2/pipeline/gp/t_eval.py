import sys, os, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gpu
import rig, scene, evaluate as EV
hid = os.environ.get('HERO', 'MatchHero_Male')
h = rig.Hero(hid); R = scene.Rig(h); items = scene.items_from_dump(h)
t = time.time(); bits = EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', hid)); print('coverage s', round(time.time()-t,1))
for it, b in zip(items, bits): print(' ', it.tag, 'tris', len(b), 'covered', int((b != 0).sum()))
S = EV.Stress(R, items, bits)
for clip in ['tennis__Male_Serve', 'tennis__Male_Emote_Scuba', 'tennis__Male_Overhead']:
    mats, sw = h.frames(clip)
    t = time.time(); tot = []
    for f in range(0, len(mats), 4):
        r = S.frame(S.posed(mats[f], {k: v[f] for k, v in sw.items()}))
        tot.append((f, r['tear'], r['layer'], r['by']))
    print(clip, 'per frame s', round((time.time()-t)/len(tot), 3))
    for x in tot: print('   ', x)
