"""Solve the new Serve with the match-anim-set engine (same tracker, same reach rule as work/match-anim-set/scripts/bake.py) -> data/gen_serve_<hero>.npz

  python3.13 run_serve.py <male|female>"""
import json
import sys
import time

import numpy as np

sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/scripts')
import loco
import kin
import clipkit
import clips as CL
import serve_new

tag = sys.argv[1]
t0 = time.time()
hero = loco.Hero(tag)
S = hero.S
S.ready['gaze'] = None                       # no READY gaze: the Clip anchors a channel with no READY value to its first / last key
rig = hero.rig
FPS = 30
d = serve_new.serve(S, hero)
d = CL.limit_reach(d, S)
LMAX = S.A_arm + 0.45 * CL.RACKET_LEN - 0.012


def solve_frames(d):
    clip = clipkit.Clip(d, S.ready)
    d_ = clip.d
    clip.track(S)
    frames = clip.frame_times()
    S.reset()
    prev = None
    quats = np.zeros((len(frames), rig.n, 4))
    hips = np.zeros((len(frames), 3))
    infos, bases = [], []
    for fi, t in enumerate(frames):
        P = clip.params(t)
        basis, hl, info = S.solve(P)
        for i in range(rig.n):
            q = kin.mat_to_quat(basis[i])
            if prev is not None and np.dot(q, prev[i]) < 0:
                q = -q
            quats[fi, i] = q
        prev = quats[fi]
        hips[fi] = hl
        infos.append(info)
        bases.append(basis)
    return clip, d_, frames, quats, hips, infos, bases


for attempt in range(5):
    clip, d_c, frames, quats, hips, infos, bases = solve_frames(d)
    ci = int(round(d_c['contact'] * FPS))
    sh = np.asarray(infos[ci]['R_shoulder'] if 'R_shoulder' in infos[ci] else infos[ci].get('R_shoulder'))
    sweet = np.asarray(infos[ci]['sweet'])
    Q, Pos = rig.fk(bases[ci], hips[ci])
    shoulder = Pos[rig.idx['RightUpperArm']]
    dist = float(np.linalg.norm(sweet - shoulder))
    print('attempt', attempt, 'contact reach %.3f limit %.3f' % (dist, LMAX), 'time %.0fs' % (time.time() - t0))
    if dist <= LMAX:
        break
    for k in d['keys']:
        if k['ch'].get('rk_abs') == 1.0 and k['ch'].get('rk_sweet') is not None:
            sw = np.asarray(k['ch']['rk_sweet'], float)
            k['ch']['rk_sweet'] = list(sw + kin.w2a((shoulder - sweet) / dist) * (dist - LMAX + 0.004))
nF = len(frames)
# diagnostics
kf = np.array([[i['lf_knee_flex_deg'], i['rf_knee_flex_deg']] for i in infos])
short = np.array([[i['lf_short'], i['rf_short'], i.get('R_arm_short', 0), i.get('L_arm_short', 0), i.get('racket_shift', 0)] for i in infos])
wr = np.array([[i.get('R_wrist_swing_deg', 0), i.get('R_wrist_clamp_deg', 0), abs(i.get('R_wrist_twist_deg', 0))] for i in infos])
drop = np.array([i.get('pelvis_auto_drop', 0.0) for i in infos])
step = np.array([np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(quats[k + 1] * quats[k], axis=1)), 0, 1))).max() for k in range(nF - 1)])
hh = np.array([[hero.foot_h(bases[k], hips[k])['L'], hero.foot_h(bases[k], hips[k])['R']] for k in range(nF)])
print('SERVE', tag, 'frames', nF, 'contact', d_c['contact'], 'time %.0fs' % (time.time() - t0))
print(' knee flex max L/R', kf.max(0).round(1), ' leg short max mm', (short[:, :2].max() * 1000).round(2), ' arm short R/L mm', (short[:, 2:4].max(0) * 1000).round(2), ' racket shift max mm', (short[:, 4].max() * 1000).round(1))
print(' R wrist swing max', wr[:, 0].max().round(1), ' clamp max', wr[:, 1].max().round(1), ' twist max', wr[:, 2].max().round(1), ' pelvis auto drop max mm', (drop.max() * 1000).round(1))
print(' max bone step deg/frame', step.max().round(1), 'at', int(step.argmax()), ' foot height min mm (L,R)', (hh.min(0) * 1000).round(1), ' max mm', (hh.max(0) * 1000).round(1))
ci = int(round(d_c['contact'] * FPS))
print(' contact: sweet', np.round(kin.w2a(infos[ci]['sweet'] - hero.O), 3), ' shaft err %.1f face err %.1f' % (infos[ci]['shaft_err_deg'], infos[ci]['face_err_deg']))
meta = dict(name='Serve', frames=nF, loop=False, contact=d_c['contact'], contact_frame=ci, stance=serve_new.T_S, release=serve_new.T_R, trophy=serve_new.T_T, deepest=serve_new.T_D,
            takeoff=serve_new.T_OFF, landing=serve_new.T_LAND, markers=[['Contact', ci]], thin=True, thin_why=d_c['thin_why'], url=d_c['url'], kind='serve',
            src='rxo1uEdLouY t=178-181 (WATCH.md section 3)')
if '--table' in sys.argv:
    print(' f    t    pelYaw chestYaw  kneeL kneeR  drop  hL   hR   Rsw  Rtw  maxstep(bone)')
    for k in range(nF):
        Q, Pos = rig.fk(bases[k], hips[k])
        def yaw(name):
            fwd = Q[rig.idx[name]] @ rig.Rrest[rig.idx[name]].T @ np.array([0, -1.0, 0])      # bone frame -> world forward of the rest pose (hero faces -Y)
            a = kin.w2a(fwd)
            return np.degrees(np.arctan2(a[0], a[1]))
        stp = ''
        if k > 0:
            ang = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(quats[k] * quats[k - 1], axis=1)), 0, 1)))
            j = int(ang.argmax()); stp = '%5.1f %s' % (ang[j], rig.names[j])
        print('%2d %5.2f  %6.1f  %6.1f   %5.1f %5.1f  %4.0f %4.0f %4.0f  %4.0f %5.0f  %s' % (k, k / FPS, yaw('Hips'), yaw('Chest'), kf[k, 0], kf[k, 1], drop[k] * 1000, hh[k, 0] * 1000, hh[k, 1] * 1000, wr[k, 0], infos[k].get('R_wrist_twist_deg', 0), stp))
np.savez_compressed(f'{loco.DATA}/gen_serve_{tag}.npz', quats=quats, hips=hips, heights=hh, knee=kf, meta=json.dumps(meta, default=float))
