"""OVERHAUL copy (3 clips -> work/emote-overhaul/data): re-import the exported FBX files and record what they actually contain (Blender, headless).

  blender -b --factory-startup --python trace_fbx.py -- <male|female> [fbx_dir]

For every clip (+ the ReadyIdle FBX of work/match-anim-set as the READY reference) writes data/trace_<hero>_<clip>.npz: the world matrices of all 53 pose bones per frame, of Hand_Racket and
Racket_Classic, the RightHand bone, the armature object; the object names and the bone parents."""
import json
import os
import sys

import numpy as np
import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = REPO + '/work/emotes'
CLIPS = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike']
a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
fbx_dir = a_[1] if len(a_) > 1 else W + '/export/fbx'
label = 'Male' if tag == 'male' else 'Female'
names = [b['name'] for b in json.load(open(f'{REPO}/work/match-anim-set/data/rig_{tag}.json'))['bones']]
todo = [(c, f'{fbx_dir}/{label}_{c}.fbx') for c in CLIPS] + [('ReadyIdle', f'{REPO}/work/match-anim-set/export/fbx/{label}_ReadyIdle.fbx'), ('RunForward', f'{REPO}/work/match-anim-set/export/fbx/{label}_ReadyIdle.fbx'.replace('match-anim-set/export/fbx/' + label + '_ReadyIdle', 'serve-and-feet/export/fbx/' + label + '_RunForward'))]
for clip, path in todo:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, axis_forward='-Z', axis_up='Y')
    sc = bpy.context.scene
    arms = [o for o in sc.objects if o.type == 'ARMATURE']
    arm = arms[0]
    act = arm.animation_data.action
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    objs = sorted(o.name for o in sc.objects)
    hr = bpy.data.objects.get('Hand_Racket')
    rc = bpy.data.objects.get('Racket_Classic')
    nF = f1 - f0 + 1
    M = np.zeros((nF, len(names), 4, 4), np.float64)
    HR = np.tile(np.eye(4), (nF, 1, 1))
    RC = np.tile(np.eye(4), (nF, 1, 1))
    ARM = np.tile(np.eye(4), (nF, 1, 1))
    ROOT = np.zeros((nF, 7))
    pbs = [arm.pose.bones[n] for n in names]
    racket_pts = None
    for k, f in enumerate(range(f0, f1 + 1)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        mw = arm.matrix_world
        ARM[k] = np.array(mw)
        for i, pb in enumerate(pbs):
            M[k, i] = np.array(mw @ pb.matrix)
        if hr is not None:
            HR[k] = np.array(hr.matrix_world)
        if rc is not None:
            RC[k] = np.array(rc.matrix_world)
        rb = arm.pose.bones['Root']
        ROOT[k, :3] = np.array(rb.location)
        ROOT[k, 3:] = np.array(rb.rotation_quaternion)
    parents = [(b.name, b.parent.name if b.parent else None) for b in arm.data.bones]
    meshes = sorted(o.name for o in sc.objects if o.type == 'MESH')
    empties = sorted(o.name for o in sc.objects if o.type == 'EMPTY')
    rc_parent = rc.parent.name if rc is not None and rc.parent else None
    hr_parent = (hr.parent.name, hr.parent_type, hr.parent_bone) if hr is not None and hr.parent else None
    np.savez_compressed(f'{REPO}/work/emote-overhaul/data/trace_{tag}_{clip}.npz', M=M, HR=HR, RC=RC, ARM=ARM, ROOT=ROOT, frames=nF,
                        meta=json.dumps(dict(clip=clip, objects=objs, meshes=meshes, empties=empties, armatures=len(arms), parents=parents, bones=names,
                                             rc_parent=rc_parent, hr_parent=hr_parent, frame_range=[f0, f1], path=path)))
    print('TRACE', tag, clip, nF, 'frames', len(objs), 'objects')
