"""GARMENT PIPELINE: run the stress suite for one hero (Blender headless).
Blender -b --factory-startup --python gp/suite.py -- <hero> <out_dir> [--cand <dir with <Piece>.npz>] [--frames all|stress] [--views 24]
Writes <out_dir>/<hero>/suite.json (per pose tear / layer pixels, totals) and worst_NN.png (shaded worst view, red = flagged)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig, scene, evaluate as EV, render as RD, overlay as OV, stress as ST, candidate as CA

argv = sys.argv[sys.argv.index('--') + 1:]
hid, out = argv[0], argv[1]
opt = {argv[i][2:]: argv[i + 1] for i in range(2, len(argv) - 1, 2) if argv[i].startswith('--')}
h = rig.Hero(hid); R = scene.Rig(h)
items = scene.items_from_dump(h)
cd_ = os.path.join(opt['cand'], hid) if 'cand' in opt and os.path.isdir(os.path.join(opt['cand'], hid)) else opt.get('cand')
cand = CA.load_dir(cd_, h) if cd_ else {}
print('SUITE candidates:', sorted(cand), flush=True)
items = [cand.get(i.tag, i) for i in items]
have = {i.tag for i in items}; items += [v for k, v in sorted(cand.items()) if k not in have and k != 'body']   # brand-new pieces (not in the dump) join the worn set
if 'body' in cand: items[0] = cand['body']
bits = EV.limb_filter(items, EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', hid)), h.bones)
S = EV.Stress(R, items, bits)
if 'views' in opt and int(opt['views']) != 24:
    S.views = RD.view_dirs(int(opt['views']) // 3)
lib = ST.Library(hid)
od = os.path.join(out, hid); os.makedirs(od, exist_ok=True)
rows = []; t0 = time.time()
# GP_ORACLE="<Tag>=<ckpt dir>[,...]": that garment gets each stress pose's OWN solved corrective field instead of the compressed
# shapes + RBF (the best correctives could ever do: tells compression loss from what the solver itself cannot fix)
ORC = dict(kv.split('=', 1) for kv in os.environ.get('GP_ORACLE', '').split(',') if '=' in kv)
def oracle(i):
    out = {}
    for k, it in enumerate(items):
        if it.tag in ORC:
            f = np.load(os.path.join(ORC[it.tag], 'p%03d.npy' % i)).astype(float); m = np.linalg.norm(f, axis=1)
            f *= np.minimum(1, .025 / np.maximum(m, 1e-9))[:, None]
            out[it.tag] = R.posem(it, lib.mats[i], None, base=it.P + f)
    return out or None
import hashlib
ck = os.path.join(od, 'rows_%s.jsonl' % hashlib.sha1(('limb2h3' + os.environ.get('GP_ORACLE', '') + ''.join(EV.pose_key(i) + str(int(i.drawn.sum())) for i in items) + str(len(lib))).encode()).hexdigest()[:10])
done = {}
if os.path.exists(ck):
    for line in open(ck):
        try: r = json.loads(line); done[r['i']] = r
        except Exception: pass
ckf = open(ck, 'a')
CHUNK = int(os.environ.get('GP_SUITE_CHUNK', 70)); new = 0
SUB = set(json.load(open(os.environ['GP_SUITE_SUBSET']))) if os.environ.get('GP_SUITE_SUBSET') else None
for i in range(len(lib)):
    if SUB is not None and i not in SUB: continue
    if i in done: rows.append(done[i]); continue
    if new >= CHUNK or (new > 0 and RD.footprint_gb() > RD.MEM_LIMIT_GB):   # GPU work is never freed in background Blender: stop, the caller relaunches
        print('SUITE chunk done at', i, flush=True); sys.stdout.flush(); os._exit(3)
    new += 1
    sw = {t: lib.sw[t][i] for t in lib.sw}
    Ps = S.posed(lib.mats[i], CA.shape_weights(items, sw, lib.mats[i], h, R), oracle(i))
    r = S.frame(Ps)
    rows.append({'i': i, 'clip': lib.meta[i]['clip'], 'frame': lib.meta[i]['frame'], 'why': sorted(set(lib.meta[i]['why'])),
                 'tear': r['tear'], 'layer': r['layer'], 'holes': r['holes'], 'holes_bg': r.get('holes_bg', 0), 'holes_inner': r.get('holes_inner', 0), 'holes_deep': r.get('holes_deep', 0), 'by': r['by'], 'pair': r.get('pair', {})})
    ckf.write(json.dumps(rows[-1]) + '\n'); ckf.flush()
    if i % 20 == 0: print('SUITE progress %d/%d %.0f s' % (i, len(lib), time.time() - t0), flush=True)
tot = {'tear': sum(r['tear'] for r in rows), 'layer': sum(r['layer'] for r in rows),
       'poses_with_tear': sum(r['tear'] > 0 for r in rows), 'poses_with_layer': sum(r['layer'] > 0 for r in rows),
       'holes': sum(r['holes'] for r in rows), 'poses_with_holes': sum(r['holes'] > 0 for r in rows),
       'by': {}}
for r in rows:
    for k, v in r['by'].items(): tot['by'][k] = tot['by'].get(k, 0) + v
    for k, v in r.get('pair', {}).items(): tot.setdefault('pair', {})[k] = tot.get('pair', {}).get(k, 0) + v
worst = sorted(rows, key=lambda r: -(r['tear'] + r['layer']))[:12]
for n, r in enumerate(worst):
    i = r['i']; sw = {t: lib.sw[t][i] for t in lib.sw}
    Ps = S.posed(lib.mats[i], CA.shape_weights(items, sw, lib.mats[i], h, R), oracle(i))
    rr = S.frame(Ps, keep_masks=True)
    vi = int(np.argmax(rr['views'])) if max(rr['views']) > 0 else 0
    RD.write_png(os.path.join(od, f'worst_{n:02d}.png'), OV.shot(S, Ps, S.views[vi], rr['masks'][vi][0]))
    r['view'] = vi
json.dump({'hero': hid, 'cand': opt.get('cand'), 'poses': len(rows), 'seconds': round(time.time() - t0, 1), 'total': tot, 'worst': worst, 'rows': rows},
          open(os.path.join(od, 'suite.json'), 'w'), indent=1)
print('SUITE', hid, json.dumps(tot), 'in %.0f s' % (time.time() - t0))
