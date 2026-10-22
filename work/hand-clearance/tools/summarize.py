#!/usr/bin/env python3
"""Gate numbers from a sweep folder (AnimationSafetyAudit.Sweep output).
usage: summarize.py <sweep_dir> <proof_dir> [--label final]
Writes <proof_dir>/<label>-summary.json (gate numbers), <label>-clips.csv (per clip), <label>-locked.csv (frames over
3 mm while the wrists were locked at contact), and prints a short report."""
import csv, json, os, sys, collections

args = sys.argv[1:]
label = 'final'
if '--label' in args:
    i = args.index('--label'); label = args[i + 1]; del args[i:i + 2]
src, out = args[0], args[1]
os.makedirs(out, exist_ok=True)
rows = list(csv.DictReader(open(os.path.join(src, 'sweep.csv'))))
clips = json.load(open(os.path.join(src, 'clips.json')))
summ = json.load(open(os.path.join(src, 'summary.json')))
F = 3.0

def f(r, k):
    try: return float(r.get(k) or 0)
    except ValueError: return 0.0

tot = collections.Counter()
locked = []
per = collections.defaultdict(collections.Counter)
for r in rows:
    key = (r['ctx'], r['clip'])
    b_b, b_a, c_b, c_a = f(r, 'bodyBefore'), f(r, 'bodyAfter'), f(r, 'clothBefore'), f(r, 'clothAfter')
    lk = 'travel' in r and f(r, 'travel') < .05
    tot['frames'] += 1
    for name, v in (('bodyBefore', b_b), ('bodyAfter', b_a), ('clothBefore', c_b), ('clothAfter', c_a)):
        if v > F: tot[name] += 1; per[key][name] += 1
    if lk: tot['lockedFrames'] += 1
    if lk and (b_a > F or c_a > F):
        tot['lockedFail'] += 1
        locked.append([r['ctx'], r['clip'], r['frame'], r['t'], b_a, r['whereBodyAfter'], c_a, r['whereClothAfter']])
    if not lk:
        if b_a > F: tot['bodyAfterFree'] += 1
        if c_a > F: tot['clothAfterFree'] += 1
    per[key]['frames'] += 1

with open(os.path.join(out, f'{label}-locked.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['ctx', 'clip', 'frame', 't', 'bodyMm', 'bodyWhere', 'clothMm', 'clothWhere']); w.writerows(locked)
with open(os.path.join(out, f'{label}-clips.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['ctx', 'clip', 'frames', 'bodyFailBefore', 'bodyFailAfter', 'clothFailBefore', 'clothFailAfter', 'bodyMaxBefore', 'bodyMaxAfter', 'clothMaxBefore', 'clothMaxAfter', 'whereAfter', 'contactDriftMm', 'popRatio', 'popAt', 'flips'])
    for c in clips:
        w.writerow([c['ctx'], c['clip'], c['frames'], c['bodyFailBefore'], c['bodyFailAfter'], c['clothFailBefore'], c['clothFailAfter'], c['bodyBefore'], c['bodyAfter'], c['clothBefore'], c['clothAfter'], c['whereAfter'], c['contactDrift'], c['popRatio'], c.get('popAt', ''), c['flips']])

pop_clips = [c for c in clips if c['popFrames'] > 0]
pop_static = [c for c in pop_clips if max(c['rawPeakShoulder'], c['rawPeakElbow']) < 30]
drift = [c['contactDrift'] for c in clips if c['contactDrift'] >= 0]
g = {
    'frames': tot['frames'], 'clips': len(clips),
    'bodyFailFramesBefore': tot['bodyBefore'], 'bodyFailFramesAfter': tot['bodyAfter'],
    'clothFailFramesBefore': tot['clothBefore'], 'clothFailFramesAfter': tot['clothAfter'],
    'lockedFrames': tot['lockedFrames'], 'failFramesWhileLocked': tot['lockedFail'],
    'bodyFailFramesAfterFree': tot['bodyAfterFree'], 'clothFailFramesAfterFree': tot['clothAfterFree'],
    'clipsWithBodyFailAfter': sum(1 for c in clips if c['bodyFailAfter'] > 0), 'clipsWithClothFailAfter': sum(1 for c in clips if c['clothFailAfter'] > 0),
    'maxContactDriftMm': max(drift) if drift else None, 'contactClips': len(drift),
    'popFrames': sum(c['popFrames'] for c in clips), 'clipsWithPops': len(pop_clips), 'clipsWithPopsStaticClip': len(pop_static),
    'flips': sum(c['flips'] for c in clips),
    'solverMs': {k: summ.get(k) for k in ('solverMsMean', 'solverMsP50', 'solverMsP95', 'solverMsP99', 'solverMsMax')},
}
json.dump(g, open(os.path.join(out, f'{label}-summary.json'), 'w'), indent=1)
print(json.dumps(g, indent=1))
for ctx in sorted(set(c['ctx'] for c in clips)):
    cc = [c for c in clips if c['ctx'] == ctx]
    print(ctx, 'frames', sum(c['frames'] for c in cc), 'body', sum(c['bodyFailBefore'] for c in cc), '->', sum(c['bodyFailAfter'] for c in cc),
          'cloth', sum(c['clothFailBefore'] for c in cc), '->', sum(c['clothFailAfter'] for c in cc), 'pops', sum(c['popFrames'] for c in cc), 'flips', sum(c['flips'] for c in cc))
