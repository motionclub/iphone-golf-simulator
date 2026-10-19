import json, sys, glob, collections
for d in sys.argv[1:]:
    import os; f_ = max(glob.glob(d + '/rows_*.jsonl'), key=os.path.getmtime); rows = [json.loads(l) for l in open(f_)]
    agg = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        c = r['clip'].split('__')[-1].replace('Male_', '')
        a = agg[c]; a['poses'] += 1; a['tear'] += r['tear']; a['layer'] += r['layer']
        for k, v in r.get('pair', {}).items(): a[k] += v
    print('==', d, len(rows), 'poses')
    for c in sorted(agg, key=lambda c: -agg[c]['tear']):
        a = agg[c]; pairs = {k: v for k, v in a.items() if '<' in k and v > 0}
        print('%-22s poses %3d tear %7d layer %6d  %s' % (c, a['poses'], a['tear'], a['layer'], dict(sorted(pairs.items(), key=lambda kv: -kv[1])[:4])))
