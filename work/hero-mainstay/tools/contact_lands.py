#!/usr/bin/env python3
"""contact_lands.py proof/trace.csv : CONTACT_LANDS. For every swing in the rally trace, the first frame in which the actor's time-to-contact reaches
zero is compared with the clip's own contact time (data/clip_table.json): the clip time shown in that frame must be the clip's contact frame (within one frame)."""
import csv, json, collections, statistics, sys, os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
tab = json.load(open(os.path.join(root, 'data/clip_table.json')))
contact = {f"{h['sex']}_{c['name']}": c['contact'] for h in tab['heroes'] for c in h['clips']}
rows = list(csv.DictReader(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'proof/trace.csv'))))
by = collections.defaultdict(list)
for r in rows: by[(r['scenario'], r['role'])].append(r)
res = collections.defaultdict(list)
for k, rs in by.items():
    prev = None
    for r in rs:
        if prev is not None and r['swinging'] == 'True' and prev['swinging'] == 'True' and float(r['ttc']) <= 0 < float(prev['ttc']) and int(r['frame']) == int(prev['frame']) + 1:
            ct = contact.get(r['clip'])
            if ct is not None: res[r['clip']].append(((float(prev['clipTime']) - ct) * 1000, (float(r['clipTime']) - ct) * 1000))
        prev = r
out = []
out.append("CONTACT_LANDS: clip time minus the clip's own contact time (ms), in the first rendered frame where the actor's time-to-contact is <= 0 (one frame = 16.7 ms)")
out.append(f"{'clip':24s} {'swings':>6s} {'contact frame: mean':>20s} {'min':>7s} {'max':>7s} {'frame before: mean':>20s}")
allv = []
for clip, v in sorted(res.items()):
    a = [x[1] for x in v]; b = [x[0] for x in v]; allv += a
    out.append(f"{clip:24s} {len(v):6d} {statistics.mean(a):20.1f} {min(a):7.1f} {max(a):7.1f} {statistics.mean(b):20.1f}")
ok = all(-1 <= x <= 16.7 + 1 for x in allv)
out.append(f"ALL: {len(allv)} swings, mean {statistics.mean(allv):.1f} ms, min {min(allv):.1f}, max {max(allv):.1f}  ->  {'PASS: every contact frame lands within one frame of the clip contact' if ok else 'FAIL'}")
print("\n".join(out)); open(os.path.join(root, 'proof/contact_lands.txt'), 'w').write("\n".join(out) + "\n")
sys.exit(0 if ok else 1)
