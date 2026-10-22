"""GARMENT PIPELINE: worst-pose BEFORE vs AFTER proof. The N worst poses of the BEFORE suite, each from its worst BEFORE view:
top = today's garments + today's cover, bottom = the fitted run (red = through cloth). 1080x1350 tiles.
Blender -b --factory-startup --python gp/compare.py -- <hero> <before_suite_dir> <run_dir> <out.png> [N]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig, scene, evaluate as EV, render as RD, overlay as OV, stress as ST, candidate as CA

a = sys.argv[sys.argv.index('--') + 1:]
hid, bdir, run, out = a[0], a[1], a[2], a[3]; N = int(a[4]) if len(a) > 4 else 6
h = rig.Hero(hid); R = scene.Rig(h); lib = ST.Library(hid)
before = scene.items_from_dump(h)
cand = CA.load_dir(os.path.join(run, hid), h)
after = [cand.get(i.tag, i) for i in before]
if 'body' in cand: after[0] = cand['body']
sets = []
for items in (before, after):
    bits = EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', hid))
    sets.append((items, EV.Stress(R, items, bits)))
rows = json.load(open(os.path.join(bdir, 'suite.json')))['rows']
worst = sorted(rows, key=lambda r: -(r['tear'] + r['layer']))[:N]
Rh = OV.hi_renderer(); tiles = [[], []]; labels = []
for r in worst:
    i = r['i']
    view = None
    for k, (items, S) in enumerate(sets):
        sw = CA.shape_weights(items, {t: lib.sw[t][i] for t in lib.sw}, lib.mats[i], h, R)
        Ps = S.posed(lib.mats[i], sw)
        rr = S.frame(Ps, keep_masks=True)
        if view is None: view = int(np.argmax(rr['views']))
        tiles[k].append(OV.shot(S, Ps, S.views[view], rr['masks'][view][0], R=Rh))
        if k == 1: labels.append((r['clip'].split('__')[-1], r['frame'], r['tear'] + r['layer'], rr['tear'] + rr['layer']))
img = np.concatenate([np.concatenate(t, 1) for t in tiles], 0)
RD.write_png(out, img)
json.dump(labels, open(out + '.json', 'w'))
print('COMPARE', out, labels)
