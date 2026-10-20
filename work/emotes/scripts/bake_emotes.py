"""Bake the solved emote clips into actions of a working copy of the hero blend (Blender, headless).

  blender -b export/blend/HeroBase_<Hero>_Emotes.blend --python bake_emotes.py -- <male|female>

Same action layout as work/match-anim-set bake: LINEAR keys on rotation_quaternion of every non-Root bone + Hips location, 30 fps, frames 0..N.  For a clip in which the racket leaves the hand the
Racket_Classic object (child of the Hand_Racket socket) gets its own action with location / rotation_quaternion keys (identity while attached); clips without detach have no racket action."""
import json
import os
import sys

import numpy as np
import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = REPO + '/work/emotes'
MA = REPO + '/work/match-anim-set'
CLIPS = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike', 'Intro_Wave', 'Intro_BringIt', 'Intro_Pushups']
tag = sys.argv[sys.argv.index('--') + 1]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
rk = bpy.data.objects['Racket_Classic']
names = [b['name'] for b in json.load(open(f'{MA}/data/rig_{tag}.json'))['bones']]
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.context.preferences.filepaths.save_version = 0
rk.rotation_mode = 'QUATERNION'


def put(act, owner, path, idx, group, vals):
    fc = act.fcurve_ensure_for_datablock(owner, path, index=idx, group_name=group)
    n = len(vals)
    fc.keyframe_points.add(n)
    co = np.empty(n * 2)
    co[0::2] = np.arange(n)
    co[1::2] = vals
    fc.keyframe_points.foreach_set('co', co)
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
    fc.update()


for clip in CLIPS:
    z = np.load(f'{W}/data/gen_{clip}_{tag}.npz', allow_pickle=True)
    quats, hips = z['quats'], z['hips']
    meta = json.loads(str(z['meta']))
    nF = len(quats)
    old = bpy.data.actions.get(clip)
    if old is not None:
        old.name = clip + '_old'
    act = bpy.data.actions.new(clip)
    act.use_fake_user = True
    rig_o.animation_data_create()
    rig_o.animation_data.action = act
    for i, nm in enumerate(names):
        if nm == 'Root':
            continue
        for comp in range(4):
            put(act, rig_o, f'pose.bones["{nm}"].rotation_quaternion', comp, nm, quats[:, i, comp])
        if nm == 'Hips':
            for comp in range(3):
                put(act, rig_o, 'pose.bones["Hips"].location', comp, 'Hips', hips[:, comp])
    act.use_frame_range = True
    act.frame_start = 0
    act.frame_end = nF - 1
    act['clip'] = clip
    act['hero'] = tag
    act['length_s'] = (nF - 1) / 30.0
    act['fps'] = 30
    act['loop'] = False
    act['gen'] = json.dumps(meta)
    # racket action
    if meta.get('racket_detaches'):
        ract = bpy.data.actions.get(clip + '_Racket')
        if ract is not None:
            ract.name = clip + '_Racket_old'
        ract = bpy.data.actions.new(clip + '_Racket')
        ract.use_fake_user = True
        rk.animation_data_create()
        rk.animation_data.action = ract
        for comp in range(3):
            put(ract, rk, 'location', comp, 'Racket', z['rk_pos'][:, comp])
        for comp in range(4):
            put(ract, rk, 'rotation_quaternion', comp, 'Racket', z['rk_quat'][:, comp])
        ract.use_frame_range = True
        ract.frame_start = 0
        ract.frame_end = nF - 1
        rk.animation_data.action = None
    print('BAKED', clip, nF, 'frames', 'racket action' if meta.get('racket_detaches') else '')
sc.frame_start = 0
rig_o.animation_data.action = bpy.data.actions[CLIPS[0]]
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('BAKE_DONE', tag)
