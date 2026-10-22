"""Blender -b --factory-startup --python tear_shots.py -- <hero> <cand dir (has <hero>/Piece.npz)> <out prefix> <subset.json>
Shaded shot of the view with the most flagged pixels (red) for each listed stress-suite pose index, plus the pixel count per pair.
Uses the pipeline's own evaluator (gp/suite.py logic) so the pixels are the suite's."""
import sys, os, json
GP = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline/gp'
sys.path.insert(0, GP); os.chdir(os.path.dirname(GP))
import numpy as np
import rig, scene, candidate as CA, evaluate as EV, stress as ST, render as RD, overlay as OV
a = sys.argv[sys.argv.index('--') + 1:]
hid, cdir, pre, sub = a[0], a[1], a[2], json.load(open(a[3]))
h = rig.Hero(hid); R = scene.Rig(h); items = scene.items_from_dump(h)
cand = CA.load_dir(os.path.join(cdir, hid), h); items = [cand.get(i.tag, i) for i in items]
if 'body' in cand: items[0] = cand['body']
bits = EV.limb_filter(items, EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', hid)), h.bones)
S = EV.Stress(R, items, bits); lib = ST.Library(hid)
for i in sub:
    sw = {t: lib.sw[t][i] for t in lib.sw}
    Ps = S.posed(lib.mats[i], CA.shape_weights(items, sw, lib.mats[i], h, R))
    rr = S.frame(Ps, keep_masks=True)
    vi = int(np.argmax(rr['views'])) if max(rr['views']) > 0 else 0
    RD.write_png('%s_%03d.png' % (pre, i), OV.shot(S, Ps, S.views[vi], rr['masks'][vi][0]))
    print('TEARSHOT', i, lib.meta[i]['clip'], lib.meta[i]['frame'], 'view', vi, json.dumps(rr.get('pair', {})), flush=True)
