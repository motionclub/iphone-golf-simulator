"""Stage 2: solve every clip frame by frame and bake it into one Blender action per clip on the hero's rig.

  blender -b export/_stage/<Hero>_rig.blend --python bake.py -- <male|female>

Writes  export/HeroBase_<Hero>_MatchAnims.blend  (the stage blend + 16 actions, active action ReadyIdle),
        data/anim_<hero>.npz  (per clip: bone quaternions, hips location, planted-foot / racket / hand traces used by the gates),
        data/bake_<hero>.json (per clip: length, frames, contact, section, THIN, resolved wrist data, solver diagnostics)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Quaternion

from common import *
import kin
import clipkit
import clips as CL
import preview as PV


def unit_(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


tag = args_after_dashes()[0]
H = HERO[tag]
NAME = H['label']
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
rig, solver = PV.load_all(tag)
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.render.fps = FPS
bpy.context.scene.render.fps_base = 1.0

summary = {}
trace = {}
actions = {}
def solve_frames(d, name):
    """track + solve a clip; returns (clip, d_clip, frames, quats, hips, tr, infos)."""
    clip = clipkit.Clip(d, solver.ready)
    d_ = clip.d                                       # the clip's own copy carries the warped contact / hold times
    clip.track(solver)
    frames = clip.frame_times()
    if FPS != clipkit.FPS:                            # MA_FPS=60 with the approved 30 Hz tracking (see clipkit.FPS): sample the clip's continuous curves at the output rate;
        frames = [i / FPS for i in range(int(round(clip.length * FPS)) + 1)]   # the even frames are the approved 30 Hz frames exactly
    solver.reset()
    prev_q = None
    quats = np.zeros((len(frames), rig.n, 4))
    hips = np.zeros((len(frames), 3))
    tr = {k: [] for k in ('ball_L', 'ball_R', 'ankle_L', 'ankle_R', 'lift_L', 'lift_R', 'heel_L', 'heel_R', 'rk_origin', 'sweet', 'shaft', 'face', 'R_wrist', 'L_wrist',
                          'R_shoulder', 'L_shoulder', 'R_elbow', 'L_elbow', 'l_attach', 'l_grip', 'knee_L', 'knee_R', 'racket_shift', 'R_short', 'L_short', 'pelvis')}
    infos = []
    for fi, t in enumerate(frames):
        P = clip.params(t)
        basis, hl, info = solver.solve(P)
        Q, Pos = rig.fk(basis, hl)
        for i, nm in enumerate(rig.names):
            q = kin.mat_to_quat(basis[i])
            if prev_q is not None and np.dot(q, prev_q[i]) < 0:
                q = -q
            quats[fi, i] = q
        prev_q = quats[fi]
        hips[fi] = hl
        tr['ball_L'].append(info['lf_ball']); tr['ball_R'].append(info['rf_ball'])
        tr['ankle_L'].append(info['lf_ankle']); tr['ankle_R'].append(info['rf_ankle'])
        tr['lift_L'].append(P.get('lf_lift', 0.0)); tr['lift_R'].append(P.get('rf_lift', 0.0))
        tr['heel_L'].append(P.get('lf_heel', 0.0)); tr['heel_R'].append(P.get('rf_heel', 0.0))
        tr['rk_origin'].append(info['rk_origin']); tr['sweet'].append(info['sweet'])
        tr['shaft'].append(info['shaft_a']); tr['face'].append(info['face_a'])
        tr['R_wrist'].append(Pos[rig.idx['RightHand']]); tr['L_wrist'].append(Pos[rig.idx['LeftHand']])
        tr['R_shoulder'].append(Pos[rig.idx['RightUpperArm']]); tr['L_shoulder'].append(Pos[rig.idx['LeftUpperArm']])
        tr['R_elbow'].append(Pos[rig.idx['RightLowerArm']]); tr['L_elbow'].append(Pos[rig.idx['LeftLowerArm']])
        tr['l_attach'].append(P.get('l_attach', 1.0)); tr['l_grip'].append(P.get('l_grip', 0.0))
        tr['knee_L'].append(info['lf_knee_flex_deg']); tr['knee_R'].append(info['rf_knee_flex_deg'])
        tr['racket_shift'].append(info.get('racket_shift', 0.0)); tr['R_short'].append(info.get('R_arm_short', 0.0)); tr['L_short'].append(info.get('L_arm_short', 0.0))
        tr['pelvis'].append(Pos[rig.idx['Hips']])
        infos.append({k: (float(v) if np.isscalar(v) else None) for k, v in info.items() if np.isscalar(v)})
    return clip, d_, frames, quats, hips, tr, infos


LMAX = solver.A_arm + 0.45 * CL.RACKET_LEN - 0.012           # CONTACT_NAMED reach test with a 12 mm margin
for name in (os.environ.get('MA_CLIPS', '').split(',') if os.environ.get('MA_CLIPS') else CLIPS):
    d = CL.build(name, solver)
    for attempt in range(5):
        clip, d_c, frames, quats, hips, tr, infos = solve_frames(d, name)
        if d_c['contact'] is None:
            break
        ci = int(round(d_c['contact'] * FPS))
        S_ = np.asarray(tr['R_shoulder'][ci]); X_ = np.asarray(tr['sweet'][ci])
        dist = float(np.linalg.norm(X_ - S_))
        if dist <= LMAX:
            break
        # the tracked pose reaches further than the probe did: pull the pinned sweet-spot target in by the excess (a few mm) and solve again
        pulled = False
        for k in d['keys']:
            if k['ch'].get('rk_abs') == 1.0 and k['ch'].get('rk_sweet') is not None:
                sw = np.asarray(k['ch']['rk_sweet'], float)
                k['ch']['rk_sweet'] = list(sw + kin.w2a(unit_(S_ - X_)) * (dist - LMAX + 0.004))
                pulled = True
        if not pulled:
            break
        print('REACH_PULL', name, 'attempt', attempt, 'dist %.3f -> limit %.3f' % (dist, LMAX))
    d = d_c
    nF = len(frames)
    # loop clip: make the last frame equal the first exactly (the closing key repeats the opening pose)
    if d.get('loop'):
        quats[-1] = quats[0]
        hips[-1] = hips[0]
    # ---- action
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig_o.animation_data_create()
    rig_o.animation_data.action = act
    for i, nm in enumerate(rig.names):
        if nm == 'Root':
            continue
        for comp in range(4):
            fc = act.fcurve_ensure_for_datablock(rig_o, f'pose.bones["{nm}"].rotation_quaternion', index=comp, group_name=nm)
            fc.keyframe_points.add(nF)
            co = np.empty(nF * 2)
            co[0::2] = np.arange(nF)
            co[1::2] = quats[:, i, comp]
            fc.keyframe_points.foreach_set('co', co)
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.update()
        if nm == 'Hips':
            for comp in range(3):
                fc = act.fcurve_ensure_for_datablock(rig_o, 'pose.bones["Hips"].location', index=comp, group_name='Hips')
                fc.keyframe_points.add(nF)
                co = np.empty(nF * 2)
                co[0::2] = np.arange(nF)
                co[1::2] = hips[:, comp]
                fc.keyframe_points.foreach_set('co', co)
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
                fc.update()
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = nF - 1
    if d['contact'] is not None:
        mk = act.pose_markers.new('Contact')
        mk.frame = int(round(d['contact'] * FPS))
    # events
    events = {}
    if name in ('Backhand', 'BackhandWide', 'Return', 'VolleyBackhand'):
        att = np.array(tr['l_attach'])
        # first frame after the contact at which the left hand is no longer on the racket
        fc_ = int(round(d['contact'] * FPS))
        off = [i for i in range(fc_, nF) if att[i] < 0.5]
        if off:
            events['left_release_s'] = off[0] / FPS
            mk = act.pose_markers.new('LeftRelease')
            mk.frame = off[0]
    if name == 'SliceApproach':
        att = np.array(tr['l_attach'])
        off = [i for i in range(nF) if att[i] < 0.5 and i > 0.3 * FPS]
        events['left_release_s'] = off[0] / FPS if off else None
        if off:
            mk = act.pose_markers.new('LeftRelease')
            mk.frame = off[0]
    act['clip'] = name
    act['hero'] = tag
    act['watch_section'] = int(d['section'])
    act['watch_source'] = d['url']
    act['length_s'] = nF / FPS - 1.0 / FPS
    act['fps'] = FPS
    if d['contact'] is not None:                       # the four movement clips carry no contact time at all
        act['contact_time_s'] = float(d['contact'])
    act['thin'] = bool(d['thin'])
    act['thin_why'] = json.dumps(d['thin_why'])
    act['loop'] = bool(d.get('loop', False))
    actions[name] = act
    for k in tr:
        trace[f'{name}/{k}'] = np.array(tr[k], float)
    trace[f'{name}/quats'] = quats
    trace[f'{name}/hips'] = hips
    keysrc = sorted(set(s for k in d['keys'] for s in k['src'].replace(',', '/').split('/')))
    cw_ = d.get('contact_window')
    if cw_ is not None and d.get('warp'):
        xs_, ys_ = [a for a, b in d['warp']], [b for a, b in d['warp']]
        cw_ = (float(np.interp(cw_[0], xs_, ys_)), float(np.interp(cw_[1], xs_, ys_)))
    cwin = [] if d['contact'] is None else [dict(t=round(k['t'], 4), src=k['src'], has_racket_orientation=k['ori'] is not None) for k in d['keys']
                                            if (cw_ is not None and cw_[0] - 1e-6 <= k['t'] <= cw_[1] + 1e-6) or (cw_ is None and abs(k['t'] - d['contact']) <= 0.07)]
    cerr = None
    if d['contact'] is not None:
        ci_ = int(round(d['contact'] * FPS))
        ish, ifc = clip.intent(d['contact'])
        e_s = float(np.degrees(np.arccos(np.clip(np.dot(tr['shaft'][ci_], ish), -1, 1))))
        e_f = float(np.degrees(np.arccos(np.clip(np.dot(tr['face'][ci_], ifc), -1, 1))))
        cerr = dict(shaft_deg=e_s, face_deg=e_f, authored_shaft_az_el=None)
    summary[name] = dict(contact_orientation_error=cerr, keys_near_contact=cwin, frames=nF, length_s=(nF - 1) / FPS, cap_s=CAPS[name], contact_s=d['contact'], section=d['section'], url=d['url'], thin=bool(d['thin']),
                         thin_why=d['thin_why'], loop=bool(d.get('loop', False)), events=events, src_tokens=keysrc, n_keys=len(d['keys']),
                         resolved=getattr(clip, 'resolved', None),
                         diag=dict(R_arm_short_max=max(i.get('R_arm_short', 0) for i in infos), L_arm_short_max=max(i.get('L_arm_short', 0) for i in infos),
                                   racket_shift_max=max(i.get('racket_shift', 0) for i in infos), knee_flex_max=max(max(i.get('lf_knee_flex_deg', 0), i.get('rf_knee_flex_deg', 0)) for i in infos),
                                   wrist_swing_max=max(i.get('R_wrist_swing_deg', 0) for i in infos), wrist_twist_max=max(abs(i.get('R_wrist_twist_deg', 0)) for i in infos),
                                   pelvis_auto_drop_max=max(i.get('pelvis_auto_drop', 0) for i in infos)))
    print('BAKED', name, nF, 'frames', 'contact', d['contact'])

# the rest pose for the active scene: ReadyIdle frame 0
rig_o.animation_data.action = actions.get('ReadyIdle') or list(actions.values())[0]   # (a MA_CLIPS subset may lack ReadyIdle)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 0, int(round(CL.LENGTH['ReadyIdle'] * FPS))
sc.frame_set(0)
rig_o['match_anims'] = 'work/match-anim-set/WATCH.md sections 1-18; see checks.json'
os.makedirs(EXPORT, exist_ok=True)
OUT = H['blend']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
np.savez_compressed(f'{DATA}/anim_{tag}.npz', **trace)
json.dump(dict(tag=tag, blend=OUT, blend_sha256=sha256_file(OUT), clips=summary), open(f'{DATA}/bake_{tag}.json', 'w'), indent=1)
print('BAKE_DONE', tag, OUT)
