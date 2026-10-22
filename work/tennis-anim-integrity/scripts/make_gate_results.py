"""Write GATE_RESULTS.md from gates_before.json / gates_after.json (gates.py) plus the REF_MATCH table (ref_match.json).
usage: python3 make_gate_results.py <films dir> <out GATE_RESULTS.md>"""
import json, os, sys

F, OUT = sys.argv[1], sys.argv[2]
before = json.load(open(os.path.join(F, 'gates_before.json')))
after = json.load(open(os.path.join(F, 'gates_after.json')))
ref = json.load(open(os.path.join(os.path.dirname(OUT), 'ref_match.json')))

def pf(b): return 'PASS' if b else ('FAIL' if b is not None else 'n/a')

L = ['# Tennis animation integrity — GATE_RESULTS (chat 4, 2026-10-17)', '',
     'Binary gates from the brief (work/delegation-2026-10-17/04_tennis_animation_integrity.md). Numbers come from `scripts/gates.py` on',
     'the clip dump (every clip sampled at 120 Hz on the real prefabs) and on real AutoPlay matches filmed in the chat-4 Unity clone',
     '(telemetry of both heroes every frame). BEFORE = the project as found on 10-17, AFTER = chat-4 changes installed in the clone.', '']

# ---- per clip x hero
L += ['## Per clip × hero (clip dump)', '', '| hero | clip | RATE | APPROVED (hands / racket tip vs approved 30 Hz at shared frames) | before → after |', '|---|---|---|---|---|']
bc = {(r['sex'], r['clip']): r for r in before['clips']}
for r in after['clips']:
    if any(x in r['clip'] for x in ('Emote', 'Intro')): continue
    b = bc.get((r['sex'], r['clip']), {})
    L.append(f"| {r['sex']} | {r['clip']} | {pf(r['RATE'])} ({r['rate']}) | {pf(r.get('APPROVED'))} {r.get('approved', '')} | RATE {pf(b.get('RATE'))}→{pf(r['RATE'])}, APPROVED {pf(b.get('APPROVED'))}→{pf(r.get('APPROVED'))} ({b.get('approved', '')}) |")
L.append('')

# ---- live
L += ['## Live matches', '', '| run | hero | CONTACT | SERVE (visible swing rate) | FEET slide | FEET dip | NO_POP |', '|---|---|---|---|---|---|---|']
for tag, g in (('BEFORE', before), ('AFTER', after)):
    for run, heroes in g.items():
        if run == 'clips': continue
        for h, x in heroes.items():
            L.append(f"| {tag} {run} | {h} | {pf(x['CONTACT'])} {x['contact']} | {pf(x['SERVE_LIVE'])} {x['serve'][:120]} | {pf(x['FEET_SLIDE'])} {x['feet']} | {pf(x['FEET_DIP'])} {x['dip']} | {pf(x['NO_POP'])} {x['pops']} |")
L.append('')

# ---- REF_MATCH
L += ['## REF_MATCH (REFERENCES.md; clips cited by id + timestamp only)', '', '| clip / behaviour | reference ids + timestamps | check | result |', '|---|---|---|---|']
for r in ref:
    L.append(f"| {r['clip']} | {r['refs']} | {r['check']} | {r['result']} |")
L.append('')
open(OUT, 'w').write('\n'.join(L) + '\n')
print('wrote', OUT)
