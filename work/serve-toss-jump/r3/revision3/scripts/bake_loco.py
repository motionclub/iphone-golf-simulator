"""Bake generated clips (data/gen_<clip>_<hero>.npz) into actions of the working copy of the hero blend.

  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/bake_loco.py -- <male|female> <Clip>[=<gen name>] ...

Same action layout as work/match-anim-set/scripts/bake.py (LINEAR keys on rotation_quaternion of every non-Root bone, Hips location, 30 fps, frame 0..N).  An existing action
of the same name is renamed '<name>_old' (kept in the copy, never exported).  Saves the copy in place; the source blend in work/match-anim-set is never touched."""
import json
import os
import sys

import numpy as np
import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/serve-toss-jump'
sys.path.insert(0, WORK + '/scripts')
import loco

a = sys.argv[sys.argv.index('--') + 1:]
tag = a[0]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
names = json.load(open(f'{loco.MA}/data/rig_{tag}.json'))
names = [b['name'] for b in names['bones']]
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.context.preferences.filepaths.save_version = 0
for spec in a[1:]:
    clip, _, gen = spec.partition('=')
    gen = gen or clip.lower()
    z = np.load(f'{loco.DATA}/gen_{gen}_{tag}.npz', allow_pickle=True)
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
    act['clip'] = clip
    act['hero'] = tag
    act['length_s'] = (nF - 1) / 30.0
    act['fps'] = 30
    act['loop'] = bool(meta.get('loop', False))
    act['gen'] = json.dumps(meta)
    for mk in meta.get('markers', []):
        m = act.pose_markers.new(mk[0])
        m.frame = int(mk[1])
    print('BAKED', clip, nF, 'frames')
sc.frame_start = 0
rig_o.animation_data.action = bpy.data.actions[a[1].partition('=')[0]]
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('BAKE_DONE', tag)
