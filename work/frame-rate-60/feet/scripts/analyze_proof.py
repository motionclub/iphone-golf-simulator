"""Play-mode gate measurements from proof/trace.csv and proof/audit.txt (the Unity proof of ServeAndFeetProof).  python3.13 scripts/analyze_proof.py  -> data/proof_metrics.json + prints
Definitions: GATE_DEFS_preregistered.md (gates 3, 4, 5, 6, 7, 9)."""
import csv
import json
import math
import re
import statistics
import sys
from collections import defaultdict

import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet'
P = W + '/proof'
import gzip, os
rows = list(csv.DictReader(open(P + '/trace.csv') if os.path.exists(P + '/trace.csv') else gzip.open(P + '/trace.csv.gz', 'rt')))
audit = open(P + '/audit.txt').read()
tab = json.load(open(W + '/data/clip_table_new.json'))
SERVE = tab['serve']
V_WALK, V_RUN = tab['walkSpeed'], tab['runSpeed']
FPS_PROOF = 60.0
R = {}


def f(x, d=float('nan')):
    try:
        return float(x)
    except Exception:
        return d


def weights(s):
    out = {}
    for tok in s.split(' '):
        if '=' in tok and not tok.startswith('upper'):
            k, v = tok.split('=')
            try:
                out[k] = float(v)
            except Exception:
                pass
    return out


for r in rows:
    r['_w'] = weights(r['weights'])
    r['_speed'] = f(r['speedMag'])
    r['_frame'] = int(r['frame'])
by_hero = defaultdict(list)
for r in rows:
    by_hero[(r['scenario'], r['role'])].append(r)

# ------------------------------------------------------------------ SERVE_HIPS in Unity (hips yaw against the clip time of the Serve played at weight >= 0.9)
hips = {}
for (sc, role), rs in by_hero.items():
    xs = [(f(r['clipTime']), f(r['hipsYaw']), f(r['chestYaw'])) for r in rs if r['clip'].endswith('_Serve') and f(r['actionWeight']) > 0.9]
    if not xs:
        continue
    sex = rs[0]['sex']

    def avg(lo, hi):
        v = [y for t, y, c in xs if lo <= t <= hi]
        return (sum(v) / len(v)) if v else None
    key = f'{sc}/{role}/{sex}'
    hips[key] = dict(n=len(xs), stance=avg(SERVE['stance'] - .05, SERVE['stance'] + .05), release=avg(SERVE['release'] - .03, SERVE['release'] + .03), trophy=avg(SERVE['trophy'] - .03, SERVE['trophy'] + .03),
                     deepest=avg(SERVE['deepest'] - .03, SERVE['deepest'] + .03), contact=avg(SERVE['contact'] - .04, SERVE['contact'] + .02))
    h = hips[key]
    h['load'] = (h['deepest'] - h['stance']) if h['deepest'] is not None and h['stance'] is not None else None
    h['unwind'] = (h['deepest'] - h['contact']) if h['deepest'] is not None and h['contact'] is not None else None
R['serve_hips_unity'] = hips

# ------------------------------------------------------------------ SERVE_CONTACT from the serve log
sv = audit.split('-- serves --')[-1].strip().splitlines()
serves = []
for line in sv:
    p = line.split(',')
    if len(p) >= 9:
        serves.append(dict(role=p[0], sex=p[1], clipTime=float(p[2]), contact=float(p[3]), delta=float(p[4]), gap=float(p[5]), frame=int(p[6]), acc=float(p[7]), mode=p[8],
                           gap0=float(p[9]) if len(p) > 9 else float(p[5]), gapmin=float(p[10]) if len(p) > 10 else float(p[5])))
R['serves_total'] = len(serves)
for mode in ('perfect', 'perfect-showcase', 'auto'):
    for role in ('PLAYER', 'RIVAL'):
        ss = [s for s in serves if s['mode'] == mode and s['role'] == role]
        if not ss:
            continue
        gaps = np.array([s['gap0'] for s in ss])          # strings-to-ball at the instant the game's time-to-contact reaches 0 (the gate)
        raw = np.array([s['gap'] for s in ss])            # the same on the frame the log fires on (ball may already be off the strings)
        d = np.array([s['delta'] for s in ss])
        R[f'serve_contact/{mode}/{role}'] = dict(n=len(ss), sexes=sorted(set(s['sex'] for s in ss)), delta_ms_minmax=[float(d.min() * 1000), float(d.max() * 1000)], within_1_frame=bool(np.all(np.abs(d) <= 1 / 30 + 1e-6)),
                                                 gap_median_m=float(np.median(gaps)), gap_max_m=float(gaps.max()), frac_gap_le_12cm=float((gaps <= .12).mean()), frac_gap_le_20cm=float((gaps <= .20).mean()),
                                                 closest_approach_max_m=float(max(s['gapmin'] for s in ss)), frame_gap_max_m=float(raw.max()), frame_gap_frac_le_12cm=float((raw <= .12).mean()))
auto = [s for s in serves if s['mode'] == 'auto' and s['role'] == 'PLAYER']
if auto:
    for lo, hi in ((0.0, 0.7), (0.7, 0.9), (0.9, 1.01)):
        ss = [s for s in auto if lo <= s['acc'] < hi]
        if ss:
            R[f'serve_contact/auto/PLAYER/toss_acc_{lo}-{hi}'] = dict(n=len(ss), gap_median_m=float(np.median([s['gap0'] for s in ss])), gap_max_m=float(max(s['gap0'] for s in ss)))

# ------------------------------------------------------------------ foot height series helpers
def series(rs, key):
    return [(r['_frame'], f(r[key])) for r in rs]


def peaks(vals, thr):
    """indices of local maxima >= thr (plateaus count once)"""
    out = []
    for i in range(1, len(vals) - 1):
        if vals[i] >= thr and vals[i] >= vals[i - 1] and vals[i] > vals[i + 1]:
            out.append(i)
    return out


# ------------------------------------------------------------------ WALK in Unity: the serve walk-in of every scenario (frames < 150, the player); walking frames = commanded ground speed >= 1.05 m/s (the base layer is fully off
# ReadyIdle there: runW = 1), counted from 0.2 s after the walk starts (the blend-in)
walk = {}
for (sc, role), rs in by_hero.items():
    if role != 'PLAYER':
        continue
    start, win = None, []
    for r in rs:
        if r['_frame'] >= 150:
            break
        if r['_speed'] >= 1.05:
            if start is None:
                start = r['_frame']
            if r['_frame'] - start >= 12:
                win.append(r)
    if len(win) < 30:
        continue
    sex = win[0]['sex']
    fl = np.array([f(r['footL_mm']) for r in win]); fr = np.array([f(r['footR_mm']) for r in win])
    ok = ~(np.isnan(fl) | np.isnan(fr))
    sk = np.array([f(r['footSkate']) for r in win])
    walk[f'{sc}/{sex}'] = dict(frames=len(win), speed_mean=float(np.mean([r['_speed'] for r in win])), walk_weight_min=float(min(r['_w'].get('Walk', 0) for r in win)), ready_weight_max=float(max(r['_w'].get('Ready', 0) for r in win)),
                               foot_skate_median=float(np.median(sk)), foot_skate_p90=float(np.percentile(sk, 90)), share_over_0_15=float((sk > .15).mean()),
                               L=dict(planted_frac=float((fl[ok] <= 10).mean()), clear40_frac=float((fl[ok] >= 40).mean()), peak_mm=float(fl[ok].max())),
                               R=dict(planted_frac=float((fr[ok] <= 10).mean()), clear40_frac=float((fr[ok] >= 40).mean()), peak_mm=float(fr[ok].max())))
R['walk_unity'] = walk

# ------------------------------------------------------------------ RUN in Unity: windows of >= 0.6 s at >= 2.5 m/s on the run clips
windows = []
for (sc, role), rs in by_hero.items():
    cur = []
    for r in rs:
        rw = sum(v for k, v in r['_w'].items() if k.startswith('Run'))
        good = r['_speed'] >= 2.5 and r['state'] == 'Run' and rw >= .9 and not math.isnan(f(r['footL_mm'], float('nan')))
        if good and (not cur or r['_frame'] == cur[-1]['_frame'] + 1):
            cur.append(r)
        else:
            if len(cur) >= 36:
                windows.append((sc, role, cur))
            cur = [r] if good else []
    if len(cur) >= 36:
        windows.append((sc, role, cur))
run_res = []
for sc, role, w in windows:
    sex = w[0]['sex']
    fl = [f(r['footL_mm']) for r in w]; fr = [f(r['footR_mm']) for r in w]
    rate = np.mean([min(1.6, max(.25, r['_speed'] / V_RUN)) for r in w])
    T = (17 / 30.0) / rate
    dur = len(w) / FPS_PROOF
    res = dict(scenario=sc, role=role, sex=sex, frames=len(w), duration_s=dur, rate=float(rate), cycle_s=float(T), clip=max(('RunForward', 'RunLeft', 'RunRight'), key=lambda k: np.mean([r['_w'].get(k, 0) for r in w])))
    ok = True
    for name, vals in (('L', fl), ('R', fr)):
        pk = peaks(vals, 60.0)
        gaps = np.diff([0] + pk + [len(vals) - 1]) / FPS_PROOF
        res[name] = dict(peaks=len(pk), peak_mm=float(max(vals)), min_peak_mm=float(min([vals[i] for i in pk])) if pk else None, max_gap_s=float(gaps.max()), planted_frac=float((np.array(vals) <= 10).mean()))
        if dur >= 1.2 * T and (not pk or gaps.max() > 1.6 * T):
            ok = False
        if dur < 1.2 * T and not pk:
            ok = False
    res['pass'] = ok
    run_res.append(res)
R['run_unity'] = dict(windows=len(run_res), passing=sum(1 for x in run_res if x['pass']), failing=[x for x in run_res if not x['pass']][:12], by_clip={k: sum(1 for x in run_res if x['clip'] == k) for k in ('RunForward', 'RunLeft', 'RunRight')},
                      by_sex={k: sum(1 for x in run_res if x['sex'] == k) for k in ('M', 'F')}, sample=run_res[:6])

# ------------------------------------------------------------------ NO_SLIDE_SUBSTITUTE in Unity
seg_ok, seg_tot = 0, 0
for (sc, role), rs in by_hero.items():
    run_len = 0
    for r in rs:
        rw = sum(v for k, v in r['_w'].items() if k.startswith('Run'))
        if r['_speed'] > 2.5 and r['state'] == 'Run':
            run_len += 1
            if run_len > 12:
                seg_tot += 1
                if rw >= .9 and r['_w'].get('Ready', 0) < .1:
                    seg_ok += 1
        else:
            run_len = 0
mov = [r for (sc, role), rs in by_hero.items() if role == 'PLAYER' for r in rs if r['_speed'] > 1.0]
skate = [f(r['footSkate']) for r in mov]
R['no_slide_unity'] = dict(run_frames_after_blend=seg_tot, run_frames_on_run_clips=seg_ok, share_run_clip_frames=(seg_ok / seg_tot if seg_tot else None),
                           player_moving_frames=len(mov), share_moving_frames_toe_slide_over_0_15=float(np.mean(np.array(skate) > .15)) if skate else None,
                           median_toe_slide=float(np.median(skate)) if skate else None)
# the same statistic on moving frames that are not inside a swing action
mov2 = [r for r in mov if r['swinging'] != 'True' and r['actionWeight'] and f(r['actionWeight']) < .05]
R['no_slide_unity']['share_toe_slide_over_0_15_no_action'] = float(np.mean(np.array([f(r['footSkate']) for r in mov2]) > .15)) if mov2 else None
R['no_slide_unity']['frames_no_action'] = len(mov2)
# what is playing on the moving frames (the player's frames at > 1 m/s)
br = defaultdict(list)
for r in mov:
    w = r['_w']; aw = f(r['actionWeight'], 0.0) if r['actionWeight'] else 0.0
    runw = sum(v for k, v in w.items() if k.startswith('Run'))
    if aw > .05 or r['swinging'] == 'True':
        c = 'action layer (stroke / serve clip of the other 15 + Serve)'
    elif w.get('Walk', 0) >= .9:
        c = 'Walk >= 0.9'
    elif runw >= .9:
        c = 'Run clips >= 0.9'
    else:
        c = 'blending (no clip >= 0.9)'
    br[c].append(f(r['footSkate']))
R['no_slide_unity']['by_what_plays'] = {c: dict(frames=len(v), share_of_moving_frames=len(v) / max(1, len(mov)), share_slide_over_0_15=float((np.array(v) > .15).mean()), median=float(np.median(v))) for c, v in br.items()}

# ------------------------------------------------------------------ NO_OLD_HERO in Play
clips_played = defaultdict(int)
for r in rows:
    if r['clip']:
        clips_played[r['clip']] += 1
R['clips_played'] = dict(clips_played)
R['clips_not_match_hero'] = [c for c in clips_played if not (c.startswith('Male_') or c.startswith('Female_'))]
R['legacy_look_lines'] = len(re.findall(r'legacy look=True', audit))
R['matchlook_lines'] = len(re.findall(r'legacy look=False matchLook=True', audit))
R['slot_assets_outside_matchheroes'] = [l for l in audit.splitlines() if 'asset=' in l and 'Assets/Characters/MatchHeroes/' not in l]
R['foot_probe_lines'] = [l.strip() for l in audit.splitlines() if 'foot probe' in l]
json.dump(R, open(W + '/data/proof_metrics.json', 'w'), indent=1, default=float)
print(json.dumps(R, indent=1, default=float)[:9000])
