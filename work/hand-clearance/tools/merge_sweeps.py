#!/usr/bin/env python3
"""Merge sweep folders into one: later folders replace earlier ones clip by clip (ctx + clip).
usage: merge_sweeps.py <out_dir> <sweep_dir> [<sweep_dir> ...]
Writes sweep.csv, clips.json and summary.json (gate totals, solver-cost percentiles from every AFTER row kept)."""
import csv, json, os, sys
out, dirs = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
clips, rows, header, worst = {}, {}, None, []
for d in dirs:
    if not os.path.exists(os.path.join(d, 'clips.json')): continue
    for c in json.load(open(os.path.join(d, 'clips.json'))): clips[(c['ctx'], c['clip'])] = c
    with open(os.path.join(d, 'sweep.csv')) as fh:
        r = csv.DictReader(fh); header = header or r.fieldnames
        per = {}
        for row in r: per.setdefault((row['ctx'], row['clip']), []).append(row)
        rows.update(per)
    s = json.load(open(os.path.join(d, 'summary.json')))
    worst += [dict(w, dir=d) for w in s.get('worst', [])]
with open(os.path.join(out, 'sweep.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=header); w.writeheader()
    for k in rows:
        for row in rows[k]: w.writerow({f: row.get(f, '') for f in header})
cl = list(clips.values())
json.dump(cl, open(os.path.join(out, 'clips.json'), 'w'), indent=0)
ms = sorted(float(r['solverMs']) for k in rows for r in rows[k] if r.get('frame') not in ('0', None) and r.get('solverMs'))
P = lambda q: ms[min(len(ms) - 1, int(q * (len(ms) - 1)))] if ms else 0
summ = {'clips': len(cl), 'frames': sum(c['frames'] for c in cl),
        'bodyFailFramesBefore': sum(c['bodyFailBefore'] for c in cl), 'bodyFailFramesAfter': sum(c['bodyFailAfter'] for c in cl),
        'clothFailFramesBefore': sum(c['clothFailBefore'] for c in cl), 'clothFailFramesAfter': sum(c['clothFailAfter'] for c in cl),
        'maxContactDrift': max([c['contactDrift'] for c in cl] or [0]), 'popFrames': sum(c['popFrames'] for c in cl), 'flips': sum(c['flips'] for c in cl),
        'solverMsMean': sum(ms) / len(ms) if ms else 0, 'solverMsP50': P(.5), 'solverMsP95': P(.95), 'solverMsP99': P(.99), 'solverMsMax': P(1), 'worst': worst}
json.dump(summ, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
print({k: v for k, v in summ.items() if k != 'worst'})
