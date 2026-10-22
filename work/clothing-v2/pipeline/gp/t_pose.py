import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, scene, render as RD, overlay as OV, stress as ST, candidate as CA
a = sys.argv[sys.argv.index('--') + 1:]
h = rig.Hero(a[0]); R = scene.Rig(h); items = scene.items_from_dump(h)
cand = CA.load_dir(a[1], h); items = [cand.get(i.tag, i) for i in items]
lib = ST.Library(h.id); meta = lib.meta
i = next(k for k, m in enumerate(meta) if m['clip'].endswith(a[2]) and m['frame'] == int(a[3]))
sw = CA.shape_weights(items, {t: lib.sw[t][i] for t in lib.sw}, lib.mats[i], h, R)
if len(a) > 5 and a[5] == 'nocorr': sw = {k: (None if any(it.tag == k and it.corr is not None for it in items) else v) for k, v in sw.items()}
Ps = [R.posem(it, lib.mats[i], sw.get(it.tag)) for it in items]
class S_: pass
S = S_(); S.items = items
c = Ps[0][[j for j, t in enumerate(items) if t.tag == 'body'][0]].mean(0) if False else None
foot = lib.mats[i][h.bidx[a[6] if len(a) > 6 else 'LeftFoot']][:3, 3]
Rr = RD.Renderer(1080, 1080, .30)
tiles = [OV.shot(S, Ps, v, R=Rr, centre=foot) for v in [(1.57, .1), (0.6, .3), (3.14, .1), (-0.6, -.3)]]
RD.write_png(a[4], np.concatenate(tiles, 1)); print('POSE', a[4])
