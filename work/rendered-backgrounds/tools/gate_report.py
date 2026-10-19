#!/usr/bin/env python3
"""Summarise proof/<venue>/gates.json (+ proof/golf/holeNN_gates.json) into the per-venue gate lines for GATE_RESULTS.md.
   tools/gate_report.py > proof/gates_summary.md"""
import json, os, glob
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def line(name, g):
    out = []
    for k in ('NO_PAINT', 'SUN_MATCH', 'PARALLAX', 'LONG_LENS', 'PERF', 'CHAR_SAME'):
        v = g[k]; ok = 'PASS' if v['pass_'] else 'FAIL'
        d = v['detail']
        if k == 'PARALLAX':
            rows = d.get('crane_60m', []) + d.get('dolly_2m', [])
            good = sum(1 for r in rows if r['err_px'] <= max(1.0, .1 * abs(r['predicted_dx'])))
            d = f"{good}/{len(rows)} landmarks within tolerance; " + '; '.join(f"{r['move']} {r['landmark']} pred {r['predicted_dx']} meas {r['measured_dx']}" for r in rows[:4])
        elif k == 'LONG_LENS':
            d = ', '.join(f"{s}: {x['before']}→{x['after']}" for s, x in d['edge_p99_upper_half'].items())
        elif k == 'PERF':
            d = '; '.join(d)
        out.append(f'- GATE: {k} {ok} — {d}')
    return f'### {name}\n' + '\n'.join(out) + '\n'

for v in ('resort', 'skyscraper', 'volcano', 'hub'):
    p = f'proof/{v}/gates.json'
    if os.path.exists(p): print(line(v, json.load(open(p))))
for p in sorted(glob.glob('proof/golf/hole*_gates.json')):
    print(line(os.path.basename(p).split('_')[0], json.load(open(p))))
