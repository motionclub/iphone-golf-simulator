"""Solve every frame of the six clips on one hero -> data/gen_<clip>_<hero>.npz  (python3.13 of Blender: numpy)

  python3.13 emo_solve_all.py <male|female> [clip ...]

Per clip: quats (nF, 53, 4) bone rotations in the rest frame of each bone (the same layout as work/match-anim-set bake), hips (nF, 3) Hips location, the racket's pose relative to the
Hand_Racket socket (rk_pos (nF,3), rk_quat (nF,4) w x y z; identity while it is on the hand), rk_off (nF,) = 1 where it is off the hand, and the world traces used by the verifier."""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import emo_hero as EH
import emo_clips as EC
import kin

CLIPS = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike', 'Intro_Wave', 'Intro_BringIt', 'Intro_Pushups']
tag = sys.argv[1]
names = sys.argv[2:] or CLIPS
H = EH.EmoHero(tag)
rig = H.rig
t0 = time.time()
for clip in names:
    C = EC.build(clip, H)
    nF = int(round(C.length * 30)) + 1
    quats = np.zeros((nF, rig.n, 4))
    hips = np.zeros((nF, 3))
    rk_pos = np.zeros((nF, 3))
    rk_quat = np.tile(np.array([1.0, 0, 0, 0]), (nF, 1))
    rk_off = np.zeros(nF)
    tr = dict(sock_pos=np.zeros((nF, 3)), sock_R=np.zeros((nF, 3, 3)), rk_world_pos=np.zeros((nF, 3)), rk_world_R=np.zeros((nF, 3, 3)))
    prev = None
    for f in range(nF):
        d = C.solve(f / 30.0)
        q = EH.quats_of(rig, d['basis'], prev)
        prev = q
        quats[f] = q
        hips[f] = d['hips']
        info = d['info']
        sp, sR = info['rk_origin'], info['rk_R']
        tr['sock_pos'][f], tr['sock_R'][f] = sp, sR
        rw = d['racket']
        if rw is not None:
            lp = sR.T @ (rw['pos'] - sp)
            lR = sR.T @ rw['R']
            rk_pos[f] = lp
            rk_quat[f] = kin.mat_to_quat(lR)
            rk_off[f] = 1.0
            tr['rk_world_pos'][f], tr['rk_world_R'][f] = rw['pos'], rw['R']
        else:
            tr['rk_world_pos'][f], tr['rk_world_R'][f] = sp, sR
    # quaternion sign continuity of the racket
    for f in range(1, nF):
        if np.dot(rk_quat[f], rk_quat[f - 1]) < 0:
            rk_quat[f] = -rk_quat[f]
    meta = dict(name=clip, frames=nF, length=C.length, fps=30, hero=tag, racket_detaches=bool(rk_off.any()), events={k: float(v) for k, v in getattr(C, 'events', {}).items()})
    for kk in ('tW', 'tS', 'tR', 'tSW', 'tF', 'tA', 'tC', 'tH', 'tE', 'tD'):
        if hasattr(C, kk):
            meta.setdefault('times', {})[kk] = float(getattr(C, kk))
    if hasattr(C, 't') and isinstance(C.t, dict):
        meta['times'] = {k: float(v) for k, v in C.t.items()}
    elif hasattr(C, 't'):
        meta['times_list'] = [float(v) for v in C.t]
    np.savez_compressed(f'{EH.DATA}/gen_{clip}_{tag}.npz', quats=quats, hips=hips, rk_pos=rk_pos, rk_quat=rk_quat, rk_off=rk_off, meta=json.dumps(meta), **tr)
    print('SOLVED', tag, clip, nF, 'frames; racket off the hand', int(rk_off.sum()), 'frames; %.0fs' % (time.time() - t0))
