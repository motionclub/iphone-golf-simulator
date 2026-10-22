"""Clip runner (inside Blender): solve a clip frame by frame, preview sheets, or bake actions.

  blender -b <rig.blend> --python anim_run.py -- <male|female> sheet <Clip> <out_prefix> [times: keys | every:N | t1,t2,...]
  blender -b <rig.blend> --python anim_run.py -- <male|female> bake  <Clip|all> <out.blend>
"""
import importlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Quaternion, Vector

from common import *
import kin
import pose as PS
import clipkit
import preview as PV


def get_clip(tag, solver, name):
    import clips
    importlib.reload(clips)
    d = clips.build(name, solver)
    clip = clipkit.Clip(d, solver.ready)
    clip.track(solver)
    return clip, clip.d


def solve_clip(solver, clip):
    frames = clip.frame_times()
    out = []
    solver.reset()
    prev = None
    for t in frames:
        P = clip.params(t)
        basis, hips, info = solver.solve(P)
        out.append((t, basis, hips, info))
    return out


def clip_summary(solver, clip, frames, d):
    infos = [f[3] for f in frames]
    s = {}
    for k in ('lf_short', 'rf_short', 'L_arm_short', 'R_arm_short', 'racket_shift'):
        vals = [i.get(k, 0.0) for i in infos]
        s[k + '_max'] = float(np.max(vals))
    s['elbow_R_flex_max'] = float(max(i.get('R_elbow_flex_deg', 0) for i in infos))
    s['knee_flex_max'] = float(max(max(i.get('lf_knee_flex_deg', 0), i.get('rf_knee_flex_deg', 0)) for i in infos))
    s['knee_flex_min'] = float(min(min(i.get('lf_knee_flex_deg', 99), i.get('rf_knee_flex_deg', 99)) for i in infos))
    return s


if __name__ == '__main__':
    a = args_after_dashes()
    tag, mode, clipname, outp = a[:4]
    rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    rig, solver = PV.load_all(tag)
    clip, d = get_clip(tag, solver, clipname)
    frames = solve_clip(solver, clip)
    print('CLIP', clipname, 'length', clip.length, 'frames', len(frames), json.dumps(clip_summary(solver, clip, frames, d)))
    if mode == 'issues':
        thr = dict(short=0.012, shift=0.02, knee=78.0, swing=105.0, twist=105.0, elbow_hyper=3.0)
        n_bad = 0
        for (t, basis, hips, i) in frames:
            msgs = []
            for k in ('R_arm_short', 'L_arm_short', 'lf_short', 'rf_short'):
                if i.get(k, 0) > thr['short']:
                    msgs.append('%s %.1fcm' % (k, i[k] * 100))
            if i.get('racket_shift', 0) > thr['shift']:
                msgs.append('racket_shift %.1fcm' % (i['racket_shift'] * 100))
            for k in ('lf_knee_flex_deg', 'rf_knee_flex_deg'):
                if i.get(k, 0) > thr['knee']:
                    msgs.append('%s %.0f' % (k, i[k]))
            if i.get('R_wrist_swing_deg', 0) > thr['swing']:
                msgs.append('R_wrist_swing %.0f' % i['R_wrist_swing_deg'])
            if abs(i.get('R_wrist_twist_deg', 0)) > thr['twist']:
                msgs.append('R_wrist_twist %.0f' % i['R_wrist_twist_deg'])
            if i.get('pelvis_auto_drop', 0) > 0.03:
                msgs.append('pelvis_auto_drop %.0fcm' % (i['pelvis_auto_drop'] * 100))
            if msgs:
                n_bad += 1
                print('  t=%.2f  %s' % (t, '; '.join(msgs)))
        print('ISSUES', clipname, 'frames with issues:', n_bad, 'of', len(frames))
    if mode == 'report':
        spec = a[4] if len(a) > 4 else 'keys'
        if spec == 'keys':
            times = sorted(set(round(k['t'] * 30) / 30 for k in clip.keys))
        else:
            times = [round(float(x) * 30) / 30 for x in spec.split(',')]
        by_t = {round(f[0] * 30): f for f in frames}
        print('%5s %-26s %-18s %-18s %-8s %-8s %-9s %-9s %-6s' % ('t', 'sweet(r,f,u)', 'shaft(cmd)', 'face(cmd)', 'shErr', 'fcErr', 'wr pre/post', 'tw', 'elb'))
        for t in times:
            f = by_t[int(round(t * 30))]
            i = f[3]
            ish, ifc = clip.intent(t)
            i = dict(i)
            i['shaft_err_deg'] = float(np.degrees(np.arccos(np.clip(np.dot(i['shaft_a'], ish), -1, 1))))
            i['face_err_deg'] = float(np.degrees(np.arccos(np.clip(np.dot(i['face_a'], ifc), -1, 1))))
            i['shaft_cmd_a'] = ish; i['face_cmd_a'] = ifc
            print('%5.2f %-26s %-18s %-18s %-8.0f %-8.0f %4.0f/%-4.0f  %-9.0f %-6.0f short %.1f/%.1fcm kn %.0f/%.0f shift %.1f' % (
                t, np.round(i['sweet_a'], 2), np.round(i['shaft_cmd_a'], 2), np.round(i['face_cmd_a'], 2), i['shaft_err_deg'], i['face_err_deg'],
                i['R_wrist_swing_pre_deg'], i['R_wrist_swing_deg'], i['R_wrist_twist_deg'], i['R_elbow_flex_deg'], i['R_arm_short'] * 100, i['L_arm_short'] * 100,
                i['lf_knee_flex_deg'], i['rf_knee_flex_deg'], i['racket_shift'] * 100))
    if mode == 'sheet':
        spec = a[4] if len(a) > 4 else 'keys'
        if spec == 'keys':
            times = sorted(set(round(k['t'] * 30) / 30 for k in clip.keys))
        elif spec.startswith('every:'):
            n = int(spec.split(':')[1])
            times = [t for i, t in enumerate(clip.frame_times()) if i % n == 0]
        else:
            times = [round(float(x) * 30) / 30 for x in spec.split(',')]
        cam = PV.setup_scene(rig_o)
        cells = []
        prev_q = None
        by_t = {round(f[0] * 30): f for f in frames}
        for t in times:
            f = by_t[int(round(t * 30))]
            prev_q = PV.apply_pose(rig_o, rig, f[1], f[2], prev_q)
            bpy.context.view_layer.update()
            row = []
            vws = (a[5].split(',') if len(a) > 5 else ['behind', 'side'])
            for v in vws:
                p = f'{outp}_t{int(round(t * 1000)):04d}_{v}.png'
                PV.render(cam, v, rig.root_origin, p, res=(360, 480))
                row.append(p)
            info = f[3]
            sweet = info['sweet']
            dg = {k: (round(float(info[k]), 2) if np.isscalar(info.get(k)) else None) for k in
                  ('R_wrist_swing_deg', 'R_wrist_twist_deg', 'R_wrist_clamp_deg', 'L_wrist_swing_deg', 'L_wrist_twist_deg', 'R_elbow_flex_deg', 'R_arm_short', 'L_arm_short', 'racket_shift',
                   'lf_knee_flex_deg', 'rf_knee_flex_deg', 'lf_short', 'rf_short', 'pelvis_auto_drop') if k in info}
            cells.append(dict(t=t, files=row, src=[k['src'] for k in clip.keys if abs(k['t'] - t) < 1e-3], diag=dg,
                              sweet=[round(float(x), 3) for x in info['sweet_a']], grip=[round(float(x), 3) for x in info['grip_a']]))
        json.dump(dict(clip=clipname, tag=tag, cells=cells, contact=d.get('contact')), open(outp + '_sheet.json', 'w'), indent=1)
        print('SHEET_DONE', len(cells))
