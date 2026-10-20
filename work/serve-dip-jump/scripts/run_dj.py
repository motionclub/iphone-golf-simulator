"""Solve the Serve (serve_dj.py) with the match-anim-set engine -> data/gen_serve_<hero>.npz   (python3.13 of Blender: numpy)

  python3.13 run_dj.py <male|female> [--table] [--out NAME]

Differences to the engine's usual run (work/serve-toss-arm/scripts/run_serve.py):
  * nothing is spliced from an older clip: the whole Serve is keyed in serve_dj.py;
  * the tossing palm between the stance and the trophy is not interpolated in chest coordinates (the chest folds and jumps now) but put on the path the game gives the ball:
        stance -> release   straight line in hero space, smoothstep over the wind-up, the palm 9 cm below the stance palm at the first wind-up frame (the game's 'under the ball' goal)
        release -> trophy   smoothstep over 0.2 s from the release palm to the trophy palm (TennisServeRoutine.TossPalm), then fixed in hero space
    the chest-relative l_hand of every such frame is computed from the solved chest (two or three passes, the palm offset of the hand is read back from the skeleton)."""
import copy
import json
import os
import sys
import time

import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-dip-jump'
sys.path.insert(0, W + '/scripts')
import loco
import kin
import pose as PS
import clipkit_dj as clipkit
import clips as CL
import serve_dj as SD

tag = sys.argv[1]
OUTNAME = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'serve'
t0 = time.time()
hero = loco.Hero(tag)
S = hero.S
S.ready['gaze'] = None
S.ready['r_hint'] = [0.0, 0.0, 0.0]
S.ready['r_hint_w'] = 0.0
S.ready['r_tw'] = 0.0
S.ready['r_tw_w'] = 0.0
rig = hero.rig
FPS = 30
IX = rig.idx
LMAX = S.A_arm + 0.45 * CL.RACKET_LEN - 0.012
if os.environ.get('TRK_LAM'):
    clipkit.Clip.TRK_LAM = float(os.environ['TRK_LAM'])
sm = lambda u: u * u * (3 - 2 * u)
# the tossing arm may tuck up to ~145 deg of elbow flexion while the trunk bows over the ball (the engine's usual floor for a wrist is 0.5 arm lengths = 121 deg)
LEFT_MIN_WRIST = float(os.environ.get('LEFT_MIN_WRIST', 0.30))
_arm_ik_orig = S._arm_ik


def _arm_ik_side(s, Sh, W, pole_v):
    old = S.min_wrist_r
    if s == 'L':
        S.min_wrist_r = LEFT_MIN_WRIST * S.A_arm
    try:
        return _arm_ik_orig(s, Sh, W, pole_v)
    finally:
        S.min_wrist_r = old


S._arm_ik = _arm_ik_side


def palm_of(basis, hl):
    Q, Pos = rig.fk(basis, hl)
    return 0.3 * Pos[IX['LeftHand']] + 0.7 * Pos[IX['LeftMiddleProximal']], Pos[IX['LeftHand']].copy(), Pos


def chest_frame(P):
    return PS.R_ypr(P['pel_rot']) @ PS.R_ypr(P['chest_rot'], 1.0)


def solve_one(P):
    return S.solve(P)


def l_hand_from_world(P, info, wrist_w):
    Rc = chest_frame(P)
    c = np.asarray(info['chest_center'], float)
    return list(kin.w2a(Rc.T @ (wrist_w - c)) / S.A_arm)


def solve_frames(d, ritual_fixed=None):
    clip = clipkit.Clip(d, S.ready)
    d_ = clip.d
    clip.track(S)
    frames = clip.frame_times()
    nF = len(frames)
    S.reset()
    # ---- the three ritual palms from the chest-relative keys
    ritual = {}
    st_save = copy.deepcopy(S.state)
    for name, tt in (('S', SD.T_S), ('R', SD.T_R), ('T', SD.T_T)):
        S.state = copy.deepcopy(st_save)
        P = clip.params(tt)
        b, h, info = S.solve(P)
        ritual[name] = palm_of(b, h)[0]
    if ritual_fixed is not None:
        ritual = dict(ritual_fixed)
    S.reset()

    def left_target(t):
        if t <= SD.T_S + 1e-9 or t > SD.T_T + 1e-9:
            return None
        if t <= SD.T_R + 1e-9:
            u = (t - SD.T_S) / (SD.T_R - SD.T_S)
            return (1 - sm(u)) * (ritual['S'] - np.array([0, 0, 0.09])) + sm(u) * ritual['R']
        k = sm(min(1.0, (t - SD.T_R) / 0.2))
        return (1 - k) * ritual['R'] + k * ritual['T']

    prev = None
    quats = np.zeros((nF, rig.n, 4))
    hips = np.zeros((nF, 3))
    infos, bases, tg, tdist, Ps = [], [], [], [], []
    for fi, t in enumerate(frames):
        P = clip.params(t)
        tgt = left_target(t)
        st0 = copy.deepcopy(S.state)
        if tgt is not None and not (abs(t - SD.T_R) < 1e-9 or abs(t - SD.T_T) < 1e-9):
            for it in range(4):
                S.state = copy.deepcopy(st0)
                b, h, info = S.solve(P)
                palm, wrist, _ = palm_of(b, h)
                err = tgt - palm
                if np.linalg.norm(err) < 0.002:
                    break
                P['l_hand'] = l_hand_from_world(P, info, wrist + err)
            S.state = copy.deepcopy(st0)
        basis, hl, info = S.solve(P)
        Ps.append({k: P[k] for k in ('pel_rot', 'chest_rot')})
        palm, wrist, _ = palm_of(basis, hl)
        tg.append((tgt if tgt is not None else palm) - palm)
        tdist.append(float(np.linalg.norm((tgt if tgt is not None else palm) - np.asarray(info['L_shoulder']))))
        for i in range(rig.n):
            q = kin.mat_to_quat(basis[i])
            if prev is not None and np.dot(q, prev[i]) < 0:
                q = -q
            quats[fi, i] = q
        prev = quats[fi]
        hips[fi] = hl
        infos.append(info)
        bases.append(basis)
    return clip, d_, frames, quats, hips, infos, bases, np.array(tg), ritual, np.array(tdist), Ps


d = SD.serve(S, hero)
d = CL.limit_reach(d, S)


def resolve_chest_oris(d):
    """racket keys written in the chest frame ('ori_c' = (shaft, face) directions from the chest's forward) -> stance-frame shaft / face at the key time"""
    body = [k for k in d['keys'] if any(c in k['ch'] for c in ('pel', 'pel_rot', 'chest_rot'))]
    tmp = clipkit.Clip(dict(d, keys=body), S.ready)
    for k in d['keys']:
        oc = k.get('ori_c')
        if oc:
            P = tmp.params(k['t'])
            Rc = chest_frame(P)
            k['ori'] = (kin.w2a(Rc @ kin.a2w(np.asarray(oc[0], float))), kin.w2a(Rc @ kin.a2w(np.asarray(oc[1], float))))


resolve_chest_oris(d)
for attempt in range(5):
    clip, d_c, frames, quats, hips, infos, bases, tg, ritual, tdist, Pframes = solve_frames(d)
    for _pass in range(2):
        real = {nm: palm_of(bases[int(round(tt * FPS))], hips[int(round(tt * FPS))])[0] for nm, tt in (('S', SD.T_S), ('R', SD.T_R), ('T', SD.T_T))}
        drift = max(float(np.linalg.norm(real[k] - ritual[k])) for k in 'SRT')
        print('  ritual palm drift (mm) pass', _pass, round(drift * 1000, 1))
        if drift < 0.003:
            break
        clip, d_c, frames, quats, hips, infos, bases, tg, ritual, tdist, Pframes = solve_frames(d, ritual_fixed=real)
    ci = int(round(d_c['contact'] * FPS))
    sweet = np.asarray(infos[ci]['sweet'])
    Q, Pos = rig.fk(bases[ci], hips[ci])
    shoulder = Pos[IX['RightUpperArm']]
    dist = float(np.linalg.norm(sweet - shoulder))
    print('attempt', attempt, 'contact reach %.3f limit %.3f' % (dist, LMAX), 'time %.0fs' % (time.time() - t0))
    if dist <= LMAX:
        break
    for k in d['keys']:
        if k['ch'].get('rk_abs') == 1.0 and k['ch'].get('rk_sweet') is not None:
            sw = np.asarray(k['ch']['rk_sweet'], float)
            k['ch']['rk_sweet'] = list(sw + kin.w2a((shoulder - sweet) / dist) * (dist - LMAX + 0.004))
nF = len(frames)
kf = np.array([[i['lf_knee_flex_deg'], i['rf_knee_flex_deg']] for i in infos])
short = np.array([[i['lf_short'], i['rf_short'], i.get('R_arm_short', 0), i.get('L_arm_short', 0), i.get('L_arm_near', 0), i.get('racket_shift', 0)] for i in infos])
wr = np.array([[i.get('R_wrist_swing_deg', 0), i.get('R_wrist_clamp_deg', 0), abs(i.get('R_wrist_twist_deg', 0))] for i in infos])
drop = np.array([i.get('pelvis_auto_drop', 0.0) for i in infos])
step = np.array([np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(quats[k + 1] * quats[k], axis=1)), 0, 1))).max() for k in range(nF - 1)])
hh = np.array([[hero.foot_h(bases[k], hips[k])['L'], hero.foot_h(bases[k], hips[k])['R']] for k in range(nF)])
print('SERVE', tag, 'frames', nF, 'contact', d_c['contact'], 'time %.0fs' % (time.time() - t0))
print(' knee flex max L/R', kf.max(0).round(1), ' leg short max mm', (short[:, :2].max() * 1000).round(2), ' arm short R/L mm', (short[:, 2:4].max(0) * 1000).round(2), ' L arm near max mm', (short[:, 4].max() * 1000).round(2),
      ' racket shift max mm', (short[:, 5].max() * 1000).round(1))
print(' R wrist swing max', wr[:, 0].max().round(1), ' clamp max', wr[:, 1].max().round(1), ' twist max', wr[:, 2].max().round(1), ' pelvis auto drop max mm', (drop.max() * 1000).round(1))
print(' max bone step deg/frame', step.max().round(1), 'at', int(step.argmax()), ' foot height min mm (L,R)', (hh.min(0) * 1000).round(1), ' max mm', (hh.max(0) * 1000).round(1))
print(' left palm vs game path (mm) max over the ritual frames', (np.linalg.norm(tg, axis=1).max() * 1000).round(1))
meta = dict(name='Serve', frames=nF, loop=False, contact=d_c['contact'], contact_frame=ci, stance=SD.T_S, release=SD.T_R, trophy=SD.T_T, deepest=SD.T_D,
            takeoff=SD.T_OFF, landing=SD.T_LAND, markers=[['Contact', ci]], thin=True, thin_why=d_c['thin_why'], url=d_c['url'], kind='serve',
            src='rxo1uEdLouY t=178-181 (WATCH.md section 3) + the pre-toss fold and hop (Adnan 2026-10-03)')
if '--table' in sys.argv:
    print(' f    t    kneeL kneeR  drop  hL   hR  | Lshort Lnear palmErr Ldist Lelb | Rsw  Rtw shaftE faceE | maxstep(bone)')
    for k in range(nF):
        stp = ''
        if k > 0:
            ang = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(quats[k] * quats[k - 1], axis=1)), 0, 1)))
            j = int(ang.argmax()); stp = '%5.1f %s' % (ang[j], rig.names[j])
        print('%2d %5.2f  %5.1f %5.1f  %4.0f %4.0f %4.0f | %5.0f %5.0f %6.0f %5.0f %4.0f | %4.0f %5.0f %5.0f %5.0f | %s' % (k, k / FPS, kf[k, 0], kf[k, 1], drop[k] * 1000, hh[k, 0] * 1000, hh[k, 1] * 1000, short[k, 3] * 1000, short[k, 4] * 1000,
                                                                                         np.linalg.norm(tg[k]) * 1000, tdist[k] * 1000, infos[k].get('L_elbow_flex_deg', 0), wr[k, 0], infos[k].get('R_wrist_twist_deg', 0), infos[k].get('shaft_err_deg', 0), infos[k].get('face_err_deg', 0), stp))
if '--elbow' in sys.argv:
    print(' f    t   | R elbow rel. R shoulder, chest frame (r f u) m | hand(wrist) rel. R shoulder (r f u) | chest yaw  | ')
    for k in range(nF):
        Rc = chest_frame(Pframes[k])
        Q, Pos = rig.fk(bases[k], hips[k])
        sh = Pos[IX['RightUpperArm']]; el = Pos[IX['RightLowerArm']]; wr_ = Pos[IX['RightHand']]
        e = kin.w2a(Rc.T @ (el - sh)); w_ = kin.w2a(Rc.T @ (wr_ - sh))
        cy = Pframes[k]['pel_rot'][0] + Pframes[k]['chest_rot'][0]
        print('%2d %5.2f | %6.2f %6.2f %6.2f | %6.2f %6.2f %6.2f | %6.1f' % (k, k / FPS, *e, *w_, cy))
if '--wrist' in sys.argv:
    print(' f    t   | wrist flex dev twist | shaft achieved az el | commanded az el | err | swivel')
    clipw = None
    for k in range(nF):
        info = infos[k]
        fl, dv, tw = info.get('rk_fit_flex_dev_twist', [0, 0, 0])
        sh = np.asarray(info['shaft_a']); cm = np.asarray(info['shaft_cmd_a'])
        az = lambda v: np.degrees(np.arctan2(v[0], v[1])); el = lambda v: np.degrees(np.arcsin(np.clip(v[2] / np.linalg.norm(v), -1, 1)))
        print('%2d %5.2f | %6.0f %5.0f %6.0f | %6.0f %5.0f | %6.0f %5.0f | %4.0f | %5.0f' % (k, k / FPS, fl, dv, tw, az(sh), el(sh), az(cm), el(cm), info.get('shaft_err_deg', 0), info.get('rk_swivel_deg', 0)))
np.savez_compressed(f'{loco.DATA}/gen_{OUTNAME}_{tag}.npz', quats=quats, hips=hips, heights=hh, knee=kf, meta=json.dumps(meta, default=float),
                    ritual=np.array([ritual['S'], ritual['R'], ritual['T']]), palm_err=tg,
                    chest_yaw=np.array([Pframes[k]['pel_rot'][0] + Pframes[k]['chest_rot'][0] for k in range(nF)]), pel_yaw=np.array([Pframes[k]['pel_rot'][0] for k in range(nF)]))
print('saved', f'{loco.DATA}/gen_{OUTNAME}_{tag}.npz')
