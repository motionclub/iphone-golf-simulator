"""Compile GATE_RESULTS.md and checks.json from data/checks_anim.json, data/checks_repo.json, data/supplement.json.  python3"""
import json, os, time
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emotes'
A = json.load(open(W + '/data/checks_anim.json'))
Rp = json.load(open(W + '/data/checks_repo.json'))
Su = json.load(open(W + '/data/supplement.json'))
NAMES = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike', 'Intro_Wave', 'Intro_BringIt', 'Intro_Pushups']
per = dict(Emote_Scuba=['S1', 'S2', 'S3', 'S4'], Emote_Thrust=['T1', 'T2', 'T3', 'T4'], Emote_Spike=['K1', 'K2', 'K3', 'K4', 'K5'], Intro_Wave=['W1', 'W2'], Intro_BringIt=['C1', 'C2', 'C3'], Intro_Pushups=['U1', 'U2', 'U3', 'U4'])
common = ['L1', 'P1', 'B1', 'R1', 'F1']
rows, fails = [], []
def add(gid, clip, ok, note=''):
    rows.append((gid, clip, ok, note))
    if not ok:
        fails.append((gid, clip, note))
for c in NAMES:
    for g in common + per[c]:
        m, f = A['male'][c][g], A['female'][c][g]
        ok = m['ok'] and f['ok']
        note = ''
        if not ok:
            bad = [t for t, x in (('male', m), ('female', f)) if not x['ok']]
            note = 'fails on ' + '+'.join(bad) + ': ' + json.dumps({t: {k: v for k, v in x.items() if k != 'ok'} for t, x in (('male', m), ('female', f)) if not x['ok']}, default=str)[:420]
        add(g, c, ok, note)
    add('same timing (L1)', c, A['same_timing'][c]['ok'], '')
for g in ('N1', 'N2', 'G1', 'G2', 'G3', 'X1', 'X2'):
    x = Rp[g]
    note = '' if x['ok'] else json.dumps({k: v for k, v in x.items() if k not in ('ok', 'detail')}, default=str)[:420]
    add(g, 'all', x['ok'], note)
verdict = 'PASS' if not fails else 'FAIL'
T = {g: '' for g in ()}
md = ['# GATE_RESULTS - EMOTES (2026-10-04)', '', f'## GATE: EMOTES {verdict}', '',
      'Definitions: `GATE_DEFS_preregistered.md` (written before the first run; one correction before it, listed in that file). Measured: the 12 exported FBX re-imported in Blender (`data/trace_*.npz`, `data/checks_anim.json`), the project files / Unity import log / in-game film traces (`data/checks_repo.json`), `data/protected_verify.json`. Every line is both heroes.', '']
md += ['| line | clip | result | note |', '|---|---|---|---|']
for gid, c, ok, note in rows:
    md.append(f'| {gid} | {c} | {"PASS" if ok else "**FAIL**"} | {note.replace("|", "/")} |')
md += ['', f'**{sum(1 for r in rows if r[2])} / {len(rows)} lines PASS.**', '']
if fails:
    md += ['## The failed lines, as measured', '']
    for gid, c, note in fails:
        md.append(f'* **{gid} {c}** - {note}')
    md += ['',
           '## What the failed lines are (evidence, not a re-grade - the lines above keep their FAIL)', '',
           '* **R1 (Scuba, Thrust, Wave, BringIt): racket vs Hand_Racket <= 0.01 deg in the re-imported FBX.** The positions agree to 2.5e-7 m; the rotation differs by 0.05 - 0.13 deg. That is the noise floor of this FBX pipeline: Blender bakes the bone-parented racket nodes (Hand_Racket, Racket_Classic, Grip, ButtCap, StringBed carry baked curves in every clip FBX, also in clips this job did not write). The same measure on shipped clips: Male_Forehand 0.079 deg, Male_ReadyIdle 0.074 deg, Female_Forehand 0.137 deg, Female_ReadyIdle 0.134 deg (`data/r1_noise_floor.json`), so no clip can meet 0.01 deg through this exporter (`export_emotes.py` clears the racket animation data in the four clips, which changed nothing). In the game the racket is exactly on the hand: in-game grip-to-hand distance 0.0000 m for all eight emote clips x heroes (G2 PASS). I did not change the line.',
           '* **T4 (Thrust): each wrist >= 0.22 m from the Hips head in EVERY frame.** The READY pose the clip starts and ends on has its racket wrist 0.187 m (male) / 0.189 m (female) from the Hips head (the ReadyIdle clip itself), so frame 0 can never pass. Inside the thrust window (frames 11-47) the minimum is 0.418 m (male) / 0.406 m (female): no hand comes near the pelvis. I did not change the line.',
           '* **X2 (untouched): a protected file was written inside one of my run windows.** Another session is working on the golf look: `Unity/Assets/Scripts/Course/GolfLook.cs` and `Unity/Assets/Editor/GolfLookSmoke.cs` changed during this job (GolfLook.cs 15:31:47, then again later; GolfLookSmoke.cs 15:28 and later). At the last verify the file inside a run window of mine is `GolfLookSmoke.cs` (the verifier reports whichever protected file has an mtime in a window). Every Unity run of this job ran in an APFS CLONE of the project (`scratchpad/UnityClone`), never in the shared project; the clone\'s copy of GolfLook.cs is byte-identical to the job-start baseline (sha256 cf456807...) while the real file differs and changed again while this job ran, so the changes were not made by this job. No protected file is on this job\'s write list. The line is FAIL by its own wording and stays FAIL.', '']
else:
    md += ['All lines pass.', '']
md += ['## Numbers worth reading', '']
for tag in ('male', 'female'):
    a = A[tag]
    md.append(f'* {tag}: Scuba pinch {a["Emote_Scuba"]["S1"]["pinch_seconds"]:.2f} s, knee maxima {a["Emote_Scuba"]["S3"]["knee_maxima"]}; Thrust hips p-p {a["Emote_Thrust"]["T1"]["hips_forward_p2p_m"]:.3f} m (run: {a["Emote_Thrust"]["T2"]["run_hips_p2p_m"]:.3f} m), pitch swing {a["Emote_Thrust"]["T2"]["pitch_swing_deg"]:.0f} deg; Spike peak wrist {a["Emote_Spike"]["K2"]["peak_wrist_speed_mps"]:.1f} m/s (down {a["Emote_Spike"]["K2"]["peak_down_mps"]:.1f}), fold {a["Emote_Spike"]["K2"]["pelvis_pitch_max_deg"]:.0f} deg, racket off the hand {a["Emote_Spike"]["K3"]["off_seconds"]:.2f} s, hands on hips {a["Emote_Spike"]["K5"]["on_hips_seconds"]:.2f} s, head shake {a["Emote_Spike"]["K5"]["head_yaw_p2p_deg"]:.0f} deg; Wave crossings {a["Intro_Wave"]["W1"]["crossings"]}, p-p {a["Intro_Wave"]["W1"]["lateral_p2p_deg"]:.0f} deg; BringIt tuck peaks {a["Intro_BringIt"]["C1"]["tuck_peaks"]}, racket head max {a["Intro_BringIt"]["C1"]["racket_head_max_mps"]:.2f} m/s; Pushups floor {a["Intro_Pushups"]["U1"]["floor_seconds"]:.2f} s, racket off the hand {a["Intro_Pushups"]["U4"]["off_seconds"]:.2f} s.')
md += ['', 'Reply contract: `GATE: EMOTES ' + verdict + '`' + (' - failed lines: ' + ', '.join(f'{g} {c}' for g, c, _ in fails) if fails else ''), '']
open(W + '/GATE_RESULTS.md', 'w').write('\n'.join(md))
json.dump(dict(verdict=verdict, lines=[dict(id=g, clip=c, ok=ok) for g, c, ok, _ in rows], failed=[dict(id=g, clip=c) for g, c, _ in fails], supplement=Su, finished=time.strftime('%Y-%m-%d %H:%M:%S')), open(W + '/checks.json', 'w'), indent=1)
print('GATE: EMOTES', verdict, [f'{g} {c}' for g, c, _ in fails])
