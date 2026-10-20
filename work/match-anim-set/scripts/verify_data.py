"""Gate measurements that need only the baked traces (numpy; run with Blender's python):  verify_data.py <male|female>
Writes data/verify_data_<hero>.json.  Definitions are the ones in GATE_DEFS_preregistered.md (written before the build)."""
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *  # noqa

tag = sys.argv[1]
A = np.load(f'{DATA}/anim_{tag}.npz')
B = json.load(open(f'{DATA}/bake_{tag}.json'))
rig = json.load(open(f'{DATA}/rig_{tag}.json'))
names = [b['name'] for b in rig['bones']]
ix = {n: i for i, n in enumerate(names)}
measures = rig['measures']
A_arm = float(np.linalg.norm(np.array(rig['joints']['wrist_L']) - np.array(rig['joints']['shoulder_L'])))
RACKET_LEN = 0.68
FPS_ = float(FPS)

YAW_REQ = dict(Forehand=60, ForehandWide=60, Backhand=60, BackhandWide=60, SliceApproach=60, Return=60, ForehandShort=40, ForehandOpen=40,
               Serve=70, Overhead=70, VolleyForehand=20, VolleyBackhand=20)
HIT = ['Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort', 'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand',
       'VolleyBackhand', 'Overhead']
MOVE = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter']


def qang(a, b):
    d = np.abs(np.sum(a * b, axis=-1)).clip(0, 1)
    return np.degrees(2 * np.arccos(d))


res = dict(tag=tag, clips={}, gates={})
R0q = A['ReadyIdle/quats'][0]
R0 = {k: A['ReadyIdle/' + k][0] for k in ('hips', 'ankle_L', 'ankle_R', 'ball_L', 'ball_R', 'sweet', 'pelvis')}
root = np.array(rig.get('root_origin', [0, 0, 0]), float) if 'root_origin' in rig else None

for name in CLIPS:
    c = B['clips'][name]
    q = A[name + '/quats']
    nF = len(q)
    L = (nF - 1) / FPS_
    sweet = A[name + '/sweet']
    pel = A[name + '/pelvis']
    hips = A[name + '/hips']
    ball_L, ball_R = A[name + '/ball_L'], A[name + '/ball_R']
    lift_L, lift_R = A[name + '/lift_L'], A[name + '/lift_R']
    heel_L, heel_R = A[name + '/heel_L'], A[name + '/heel_R']
    d = dict(length_s=L, frames=nF, section=c['section'], contact_s=c['contact_s'], thin=c['thin'])
    # ---- IN_PLACE (data part)
    d['hips_first_last_m'] = float(np.linalg.norm((pel[-1] - pel[0])[:2]))
    d['pelvis_excursion_m'] = float(np.linalg.norm((pel - pel[0])[:, :2], axis=1).max())
    skate = 0.0
    nplanted = 0
    for ball, lift, heel in ((ball_L, lift_L, heel_L), (ball_R, lift_R, heel_R)):
        for i in range(1, nF):
            if lift[i] <= 1e-6 and lift[i - 1] <= 1e-6 and heel[i] <= 1e-6 and heel[i - 1] <= 1e-6:
                nplanted += 1
                skate = max(skate, float(np.linalg.norm((ball[i] - ball[i - 1])[:2])))
    d['planted_frames'] = nplanted
    d['max_planted_foot_step_m'] = skate
    # ---- CONTACT_NAMED (data part)
    if c['contact_s'] is not None:
        ci = int(round(c['contact_s'] * FPS_))
        v = np.linalg.norm(np.diff(sweet, axis=0), axis=1) * FPS_
        vpk = float(v.max())
        w0, w1 = max(ci - int(math.ceil(0.12 * FPS_)), 0), min(ci + int(math.ceil(0.12 * FPS_)), len(v))
        vwin = float(v[w0:w1].max())
        reach = float(np.linalg.norm(sweet[ci] - A[name + '/R_shoulder'][ci]))
        fwd = float(pel[ci][1] - sweet[ci][1])          # the hero faces -Y
        d.update(contact_frame=ci, in_range=bool(0.15 * L < c['contact_s'] < 0.92 * L), reach_m=reach, reach_limit_m=A_arm + 0.45 * RACKET_LEN,
                 sweet_forward_of_pelvis_m=fwd, speed_in_window=vwin, speed_peak=vpk, speed_ratio=vwin / vpk)
    else:
        d['contact_frame'] = None
    # ---- READS_FROM_BEHIND (data part): shoulder-line yaw, held finish
    sh = A[name + '/R_shoulder'] - A[name + '/L_shoulder']
    sh0 = A['ReadyIdle/R_shoulder'][0] - A['ReadyIdle/L_shoulder'][0]
    yaw0 = math.atan2(sh0[1], sh0[0])
    yaws = np.degrees(np.arctan2(sh[:, 1], sh[:, 0]) - yaw0)
    yaws = (yaws + 180.0) % 360.0 - 180.0
    d['peak_shoulder_yaw_deg'] = float(np.abs(yaws).max())
    d['yaw_required_deg'] = YAW_REQ.get(name)
    if c['contact_s'] is not None:
        v = np.linalg.norm(np.diff(sweet, axis=0), axis=1) * FPS_
        ipk = int(v.argmax())
        vpk = float(v.max())
        # the held finish = the FIRST run of slow steps (<= 12 % of the peak racket-head speed) after the peak, i.e. before the recovery to READY
        run, first, start = 0, None, None
        for k in range(ipk + 1, len(v)):
            if v[k] <= 0.12 * vpk:
                if run == 0:
                    start = k
                run += 1
            else:
                if run:
                    first = (start, run)
                    break
                run = 0
        if first is None and run:
            first = (start, run)
        d['finish_hold_frames'] = first[1] if first else 0
        d['finish_hold_start_frame'] = first[0] if first else None
    # ---- READY_LOOP
    d['start_max_deg'] = float(qang(q[0], R0q).max())
    d['end_max_deg'] = float(qang(q[-1], R0q).max())
    d['end_hips_m'] = float(np.linalg.norm(pel[-1] - R0['pelvis']))
    d['end_ball_m'] = float(max(np.linalg.norm(ball_L[-1] - R0['ball_L']), np.linalg.norm(ball_R[-1] - R0['ball_R'])))
    d['end_racket_head_m'] = float(np.linalg.norm(sweet[-1] - R0['sweet']))
    d['start_hips_m'] = float(np.linalg.norm(pel[0] - R0['pelvis']))
    d['start_ball_m'] = float(max(np.linalg.norm(ball_L[0] - R0['ball_L']), np.linalg.norm(ball_R[0] - R0['ball_R'])))
    d['start_racket_head_m'] = float(np.linalg.norm(sweet[0] - R0['sweet']))
    if name == 'ReadyIdle':
        step = qang(q[1:], q[:-1]).max(axis=1)
        d['loop_last_vs_first_deg'] = float(qang(q[-1], q[0]).max())
        d['loop_last_vs_first_hips_m'] = float(np.abs(hips[-1] - hips[0]).max())
        d['seam_step_deg'] = float(step[-1])
        d['median_step_deg'] = float(np.median(step))
    # per-frame step statistics (informational)
    dq = qang(q[1:], q[:-1])
    d['max_bone_step_deg'] = float(dq.max())
    arm_idx = [ix[n] for n in ('RightUpperArm', 'RightLowerArm', 'RightHand', 'LeftUpperArm', 'LeftLowerArm', 'LeftHand')]
    d['arm_steps_over_100deg'] = int((dq[:, arm_idx] > 100).sum())
    d['racket_shift_max_m'] = float(A[name + '/racket_shift'].max())
    d['right_arm_shortfall_max_m'] = float(A[name + '/R_short'].max())
    d['left_arm_shortfall_max_m'] = float(A[name + '/L_short'].max())
    res['clips'][name] = d

# ---- gate rollups
g = res['gates']
ip_fail = []
for n, d in res['clips'].items():
    if d['hips_first_last_m'] > 0.03:
        ip_fail.append(f'{n}: first-last hips {d["hips_first_last_m"]*100:.1f} cm')
    if d['pelvis_excursion_m'] > 0.55:
        ip_fail.append(f'{n}: pelvis excursion {d["pelvis_excursion_m"]*100:.0f} cm')
    if d['max_planted_foot_step_m'] > 0.005:
        ip_fail.append(f'{n}: planted foot moves {d["max_planted_foot_step_m"]*1000:.1f} mm/frame')
g['IN_PLACE_data'] = ip_fail
cn_fail = []
for n in HIT:
    d = res['clips'][n]
    if not d['in_range']:
        cn_fail.append(f'{n}: contact {d["contact_s"]} not in (0.15L, 0.92L)')
    if d['reach_m'] > d['reach_limit_m']:
        cn_fail.append(f'{n}: sweet spot {d["reach_m"]:.2f} m from the shoulder > {d["reach_limit_m"]:.2f}')
    if d['sweet_forward_of_pelvis_m'] < 0.05:
        cn_fail.append(f'{n}: sweet spot only {d["sweet_forward_of_pelvis_m"]*100:.1f} cm in front of the pelvis')
    if d['speed_ratio'] < 0.60:
        cn_fail.append(f'{n}: racket speed in +-0.12 s is {d["speed_ratio"]*100:.0f} % of peak')
for n in MOVE:
    if res['clips'][n]['contact_frame'] is not None:
        cn_fail.append(f'{n}: has a contact time')
g['CONTACT_NAMED_data'] = cn_fail
rd_fail = []
for n in HIT:
    d = res['clips'][n]
    if d['peak_shoulder_yaw_deg'] < d['yaw_required_deg']:
        rd_fail.append(f'{n}: peak shoulder yaw {d["peak_shoulder_yaw_deg"]:.0f} deg < {d["yaw_required_deg"]}')
    if d['finish_hold_frames'] < 3:
        rd_fail.append(f'{n}: finish held only {d["finish_hold_frames"]} frames')
g['READS_FROM_BEHIND_data'] = rd_fail
rl_fail = []
ri = res['clips']['ReadyIdle']
if not (2.0 <= ri['length_s'] <= 2.4):
    rl_fail.append(f'ReadyIdle length {ri["length_s"]:.2f}')
if ri['loop_last_vs_first_deg'] > 0.05 or ri['loop_last_vs_first_hips_m'] > 1e-4:
    rl_fail.append(f'ReadyIdle last != first ({ri["loop_last_vs_first_deg"]:.3f} deg, {ri["loop_last_vs_first_hips_m"]*1000:.3f} mm)')
if ri['seam_step_deg'] > 2 * ri['median_step_deg'] + 1e-9:
    rl_fail.append(f'ReadyIdle seam step {ri["seam_step_deg"]:.2f} > 2 x median {ri["median_step_deg"]:.2f}')
for n, d in res['clips'].items():
    for k, lim, u in (('start_max_deg', 25.0, 'deg'), ('end_max_deg', 25.0, 'deg'), ('start_hips_m', 0.05, 'm'), ('end_hips_m', 0.05, 'm'), ('start_ball_m', 0.10, 'm'),
                      ('end_ball_m', 0.10, 'm'), ('start_racket_head_m', 0.30, 'm'), ('end_racket_head_m', 0.30, 'm')):
        if d[k] > lim:
            rl_fail.append(f'{n}: {k} {d[k]:.3f} {u} > {lim}')
    if d['length_s'] > CAPS[n] + 1e-6:
        rl_fail.append(f'{n}: length {d["length_s"]:.3f} > cap {CAPS[n]}')
g['READY_LOOP_data'] = rl_fail

# ---- FROM_WATCH / SHORT_IS_18 / SLICE_IS_17 (text part)
watch = open(f'{WORK}/WATCH.md').read()
heads = {int(m.group(1)): m.group(2) for m in re.finditer(r'^## (\d+)\.\s*(.*)$', watch, re.M)}
BORROW = {6: [5]}                 # the only borrowing GATE_DEFS_preregistered.md allows: S6 (ForehandOpen) takes its take-back from S5, as S6 itself instructs
fw = []
for n in CLIPS:
    c = B['clips'][n]
    s = c['section']
    if s not in heads or n.lower() not in heads[s].lower().replace(' ', ''):
        # headings carry the clip name as the first word
        if s not in heads or n.lower() not in heads[s].lower():
            fw.append(f'{n}: section {s} heading "{heads.get(s)}" does not name the clip')
    ok_secs = {s} | set(BORROW.get(s, []))
    for tok in c['src_tokens']:
        t = tok.strip()
        if not t:
            continue
        if t in ('READY', 'LOCK'):
            continue
        m = re.match(r'S(\d+)\.', t)
        if not m or int(m.group(1)) not in ok_secs:
            fw.append(f'{n}: key source "{t}" is not section {s} (allowed {sorted(ok_secs)}) / READY / LOCK')
g['FROM_WATCH_text'] = fw
c18 = B['clips']['ForehandShort']
c17 = B['clips']['SliceApproach']
g['SHORT_IS_18_data'] = [] if (c18['section'] == 18 and 'WBfw9nFojHc' in c18['url'] and not any(t.startswith('S8') for t in c18['src_tokens'])) else ['ForehandShort section/url/src']
g['SLICE_IS_17_data'] = [] if (c17['section'] == 17 and 'ebS3Lf25hZ0' in c17['url'] and c17['thin']) else ['SliceApproach section/url/thin']
json.dump(res, open(f'{DATA}/verify_data_{tag}.json', 'w'), indent=1)
print(json.dumps(res['gates'], indent=1))
for n, d in res['clips'].items():
    print('%-15s L=%.2f yaw %3.0f/%s hold %s reach %s fwd %s ratio %s skate %.1fmm excursion %.0fcm steps>100 %d' % (
        n, d['length_s'], d['peak_shoulder_yaw_deg'], d['yaw_required_deg'], d.get('finish_hold_frames'),
        '%.2f' % d['reach_m'] if 'reach_m' in d else '-', '%.2f' % d['sweet_forward_of_pelvis_m'] if 'sweet_forward_of_pelvis_m' in d else '-',
        '%.2f' % d['speed_ratio'] if 'speed_ratio' in d else '-', d['max_planted_foot_step_m'] * 1000, d['pelvis_excursion_m'] * 100, d['arm_steps_over_100deg']))
