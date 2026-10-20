"""Supplementary numbers (NOT replacements for any pre-registered line): T4 limited to the thrust window, R1 against the FBX noise floor of shipped clips, the in-game racket distance.  python3.13"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_gates as CG
out = {}
for tag in ('male', 'female'):
    h = CG.Hero(tag)
    c = 'Emote_Thrust'
    hp = h.P(c, 'Hips')
    fwd = -(hp[:, 1] - hp[0, 1])
    idx = np.where(fwd >= fwd.min() + 0.4 * (fwd.max() - fwd.min()))[0]
    sl = slice(int(idx[0]), int(idx[-1]) + 1)
    d_win = min(float(np.linalg.norm(h.P(c, S + 'Hand')[sl] - hp[sl], axis=1).min()) for S in ('Left', 'Right'))
    d_all = min(float(np.linalg.norm(h.P(c, S + 'Hand') - hp, axis=1).min()) for S in ('Left', 'Right'))
    d_ready = min(float(np.linalg.norm(h.P('ReadyIdle', S + 'Hand') - h.P('ReadyIdle', 'Hips'), axis=1).min()) for S in ('Left', 'Right'))
    out[tag] = dict(T4_thrust_window_frames=[sl.start, sl.stop - 1], T4_min_wrist_to_hips_in_window_m=d_win, T4_min_over_all_frames_m=d_all, T4_min_in_the_ReadyIdle_clip_itself_m=d_ready)
out['R1_noise_floor_shipped_clips'] = json.load(open(CG.DATA + '/r1_noise_floor.json'))
rp = json.load(open(CG.DATA + '/checks_repo.json'))
out['R1_in_game_max_grip_hand_distance_m'] = {k: v['max_grip_hand_distance_m'] for k, v in rp['G2']['detail'].items() if 'max_grip_hand_distance_m' in v}
json.dump(out, open(CG.DATA + '/supplement.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
