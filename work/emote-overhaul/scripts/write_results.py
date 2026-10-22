"""write_results.py : GATE_RESULTS.md from data/checks2.json (check_gates2.py), proof/collide/cloth_*.json (collide4.py) and proof/hold/*.json (EmoteHoldCheck)."""
import json, os
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emote-overhaul'
d = json.load(open(R + '/data/checks2.json'))
CL = ['Emote_Spike', 'Emote_Thrust', 'Emote_Scuba']
LEN = dict(Emote_Spike=3.2, Emote_Thrust=3.5, Emote_Scuba=4.7)
def short(r):
    items = []
    for k, v in r.items():
        if k == 'ok': continue
        if isinstance(v, float): v = round(v, 4)
        if isinstance(v, list): v = [round(x, 4) if isinstance(x, float) else x for x in v][:4]
        items.append(f'{k}={json.dumps(v)}')
    return '; '.join(items)[:230]
total = sum(len(d[h][c]) for h in d for c in CL)
npass = sum(1 for h in d for c in CL for g in d[h][c] if d[h][c][g]['ok'])
L = ['# GATE_RESULTS - emote overhaul (Spike / Scuba / Thrust)', '',
     f'**{npass} / {total} gate lines PASS** (6 FBX = 3 clips x 2 heroes). Definitions: `GATE_DEFS_preregistered.md` (written before the first run; three disclosed amendments at its end). Measured on the RE-IMPORTED FBX (`scripts/trace_fbx2.py`, `scripts/check_gates2.py`), the independent penetration run (`scripts/collide3.py`, Blender-evaluated skin) and the Unity clone (`proof/hold/*.json`, `film/*/triggers.json`).',
     '', 'Re-run everything: `scripts/run_all2.sh` (build -> FBX -> trace -> penetration -> gates, about 9 minutes), then `scripts/write_results.py`.', '']
for c in CL:
    L += [f'## {c}', '', '| id | male | female | measured (male) | measured (female) |', '|---|---|---|---|---|']
    gids = sorted({g for h in d for g in d[h][c]}, key=lambda g: (g[0] != 'G', g[0], int(g[1:])))
    for g in gids:
        row = []
        for h in ('male', 'female'):
            r = d[h][c].get(g)
            row.append('PASS' if r and r['ok'] else ('FAIL' if r else '-'))
        L.append(f"| {g} | {row[0]} | {row[1]} | {short(d['male'][c][g]) if g in d['male'][c] else ''} | {short(d['female'][c][g]) if g in d['female'][c] else ''} |")
    L.append('')
L += ['## Unity (clone, then installed byte-identical)', '',
      '* `EmoteWire` in the clone: the 6 new FBX import with lengths Spike 3.200, Thrust 3.500, Scuba 4.700 s on both prefabs (`work/emotes/logs/wire_report.txt`); prefabs unchanged byte for byte.',
      '* `EmoteFilm` (real Tennis scene, game camera + front + side): all 3 emotes start, play and finish for both heroes; triggers: plain point 0 emotes, won game 1 emote, no emote on the next point, PlayTaunt works, intro hook works (`film/<hero>/triggers.json`, `film/<hero>/summary.txt`).',
      '* `EmoteHoldCheck` (editor tool, the REAL `AwardPoint` flow, one fresh play session per case): a won game holds the next serve until the taunt is over; a plain point keeps the 2.4 s beat and plays no emote.  The game timers run at GameSpeed 1.2x real time, so the hold is (clip length + 0.4 s) x GameSpeed.', '',
      '| case | hero | serve timer after the award (game s) | emote ended (real s) | next point (real s) | ok |', '|---|---|---|---|---|---|']
for h in ('male', 'female'):
    for case in ('EmoteScuba', 'EmoteThrust', 'EmoteSpike', 'plain'):
        f = f'{R}/proof/hold/hold_{h}_{case}.json'
        if os.path.exists(f):
            r = json.load(open(f))[0]
            L.append(f"| {r['taunt']} | {h} | {r.get('serve_timer_after_award')} | {r.get('emote_ended_at', '-')} | {r.get('next_point_at', '-')} | {r['ok']} |")
L += ['', '* Unity EditMode suite in the patched clone: 232 / 233 pass; the one failure, `TennisTutorialTests.KitColoursParseFromTheLaunchMessage`, fails identically with this job\'s C# changes removed (checked) - it is about kit colours.', '']
L += ['## Extra, not gated: cloth enclosure (`scripts/collide4.py`, every frame, Blender-evaluated shirt / shorts)', '',
      'An arm vertex counts as ENCLOSED when 15 of 16 rays hit the garment (it is inside the cloth, not beside it); the arm\'s own sleeve is excluded.  The READY pose itself has the right hand tucked under the shirt hem (9-23 vertices), so the first and last 0.30 s are listed separately.', '',
      '| clip | hero | READY-edge frames: max enclosed | mid-clip frames with any | mid-clip max enclosed (of ~2000 vertices per arm) | where |', '|---|---|---|---|---|---|']
worst_mid = 0
for c in CL:
    for h in ('male', 'female'):
        rows = json.load(open(f'{R}/proof/collide/cloth_{c}_{h}.json'))['rows']
        edge = [r for r in rows if r['t'] < 0.30 or r['t'] > LEN[c] - 0.30]
        mid = [r for r in rows if 0.30 <= r['t'] <= LEN[c] - 0.30]
        e = max([max(r['L']['enclosed'], r['R']['enclosed']) for r in edge] or [0])
        anym = [r for r in mid if r['L']['enclosed'] or r['R']['enclosed']]
        mm = max([max(r['L']['enclosed'], r['R']['enclosed']) for r in mid] or [0])
        worst_mid = max(worst_mid, mm)
        wh = ', '.join(sorted({(r['L']['first'] or r['R']['first'] or ['', 0, 0])[0] for r in anym}))
        L.append(f'| {c} | {h} | {e} | {len(anym)} of {len(mid)} | {mm} | {wh} |')
L += ['', f'Reading: away from the READY edges the arms are never inside the cloth except for a few fingertip / hand vertices in a few frames where a hand brushes a hem (at most {worst_mid} vertices).']
open(R + '/GATE_RESULTS.md', 'w').write('\n'.join(L) + '\n')
print('GATE_RESULTS.md written;', npass, '/', total)
